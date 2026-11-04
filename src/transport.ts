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
 if(r.status===413)throw new Error('The DEX server rejected this request because it exceeds its upload limit. Use a smaller file or a server with a larger limit.');
 let data;try{data=await r.json();}catch{throw new Error(`The DEX server returned an unexpected response (HTTP ${r.status}). Check the server URL and health endpoint.`);}
 if(!r.ok)throw new Error(data.error||`DEX processing failed (HTTP ${r.status})`);return data;
}
