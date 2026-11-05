export type DexConnection={mode:'hosted'|'local';apiBase:string|null};
const KEY='dex-editor-connection-v1';
export const isLoopback=(host:string)=>['localhost','127.0.0.1','[::1]'].includes(host);
export function validateBase(value:string):string{const u=new URL(value);if(u.username||u.password||u.search||u.hash)throw new Error('Use a plain server URL without credentials, query, or fragment.');if(u.protocol!=='https:'&&!(u.protocol==='http:'&&isLoopback(u.hostname)))throw new Error('Hosted DEX servers require HTTPS. HTTP is only allowed for localhost.');return u.href.replace(/\/$/,'');}
let configPromise:Promise<DexConnection>|null=null;
export function getConnection():Promise<DexConnection>{
 if(configPromise)return configPromise;
 configPromise=(async()=>{
  try{const saved=localStorage.getItem(KEY);if(saved){const c=JSON.parse(saved);if(c.mode==='local')return {mode:'local',apiBase:'http://127.0.0.1:8787'} as DexConnection;if(c.apiBase)return {mode:'hosted',apiBase:validateBase(c.apiBase)} as DexConnection;}}catch{}
  if(isLoopback(location.hostname))return {mode:'local',apiBase:location.origin};
  try{const r=await fetch('/dex-config.json',{cache:'no-store',signal:AbortSignal.timeout(5000)});if(r.ok){const c=await r.json();if(c.apiBase!==null&&typeof c.apiBase==='string')return {mode:'hosted',apiBase:validateBase(c.apiBase||location.origin)};}}catch{}
  return {mode:'hosted',apiBase:null};
 })();return configPromise;
}
export function saveConnection(c:DexConnection){const safe={...c,apiBase:c.mode==='local'?'http://127.0.0.1:8787':c.apiBase?validateBase(c.apiBase):null};try{localStorage.setItem(KEY,JSON.stringify(safe));}catch{throw new Error('Cannot save the connection in this browser. Allow site storage and try again.');}configPromise=Promise.resolve(safe);return safe;}
export async function api(path:string,body?:unknown){
 const connection=await getConnection();if(!connection.apiBase)throw new Error('Hosted DEX processing is not deployed yet. Smali, TXT, XML, and ZIP work now. Open “DEX processing” to connect an HTTPS DEX server. Mobile does not use a local companion.');
 let r:Response;try{r=await fetch(connection.apiBase+path,{method:body?'POST':'GET',headers:body?{'Content-Type':'application/json'}:{},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(body?200000:60000),credentials:'omit'});}catch{throw new Error(connection.mode==='hosted'?'The hosted DEX server could not be reached. Check its URL in DEX processing and retry. A sleeping server may take a minute to start.':'The local PC companion could not be reached. Start server.py on this computer, or choose Hosted server in DEX processing. Mobile requires a hosted server.');}
 if([502,503,504].includes(r.status))throw new Error('The DEX server restarted or exceeded its processing capacity. Your original files are unchanged. Retry one file at a time or use the PC companion for large files.');
 if(r.status===413)throw new Error('The DEX server rejected this request because it exceeds its upload limit. Use a smaller file or a server with a larger limit.');
 let data;try{data=await r.json();}catch{throw new Error(`The DEX server returned an unexpected response (HTTP ${r.status}). Check the server URL and health endpoint.`);}
 if(!r.ok)throw new Error(data.error||`DEX processing failed (HTTP ${r.status})`);return data;
}

export async function disassembleFile(file:File,onProgress:(text:string)=>void){
 const connection=await getConnection();
 if(connection.mode==='local'){
  const bytes=new Uint8Array(await file.arrayBuffer());let raw='';for(let i=0;i<bytes.length;i+=32768)raw+=String.fromCharCode(...bytes.subarray(i,i+32768));
  return api('/disassemble',{data:btoa(raw)});
 }
 if(!connection.apiBase)throw new Error('No hosted DEX server is configured. Open DEX processing to select one.');
 if(file.size>32*1024*1024)throw new Error('This hosted server accepts DEX files up to 32 MiB. Split the app into its individual DEX files.');
 onProgress(`Disassembling ${file.name} on server…`);
 let response:Response;
 try{response=await fetch(connection.apiBase+'/disassemble-binary',{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file,credentials:'omit',signal:AbortSignal.timeout(200000)});}catch{throw new Error('The DEX server could not complete this request. Your original file is unchanged. Retry after the server recovers, or use the PC companion for large files.');}
 if(!response.ok){
  let message='';try{message=(await response.json()).error||'';}catch{}
  if([502,503,504].includes(response.status))throw new Error('The DEX server restarted or ran out of processing capacity. Your original file is unchanged. Retry with one DEX file at a time; large files may need more server memory.');
  throw new Error(message||`DEX import failed (HTTP ${response.status})`);
 }
 onProgress('Downloading compressed classes…');
 const {default:JSZip}=await import('jszip');const zipped=await JSZip.loadAsync(await response.arrayBuffer());
 const apiLevel=Number(await zipped.file('_dex_api.txt')?.async('string'))||28;
 const entries=Object.values(zipped.files).filter(f=>!f.dir&&f.name.endsWith('.smali'));const files:{name:string,text:string}[]=[];
 for(let i=0;i<entries.length;i++){
  files.push({name:entries[i].name,text:await entries[i].async('string')});
  if(i%32===0){onProgress(`Opening class ${i+1} of ${entries.length}…`);await new Promise(resolve=>setTimeout(resolve,0));}
 }
 return {files,api:apiLevel};
}
