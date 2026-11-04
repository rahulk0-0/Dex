export type Options={query:string,replace:string,caseSensitive:boolean,whole:boolean,regex:boolean};
export type Hit={from:number,to:number,text:string,replacement:string};
export function findHits(text:string,o:Options):Hit[]{
 if(!o.query)return [];
 const escaped=o.query.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
 const r=new RegExp(o.regex?o.query:escaped,`gu${o.caseSensitive?'':'i'}`);
 const out:Hit[]=[]; let m:RegExpExecArray|null;
 while((m=r.exec(text))!==null){
  if(out.length>=100000)throw new Error('More than 100,000 matches. Narrow your search.');
  const from=m.index,to=from+m[0].length;
  if(!o.whole||(!/[\p{L}\p{N}_]/u.test(text[from-1]||'')&&!/[\p{L}\p{N}_]/u.test(text[to]||''))){
   const replacement=o.regex?o.replace.replace(/\$(\$|&|`|'|\d{1,2}|<[^>]+>)/g,(raw,key)=>{
    if(key==='$')return '$';if(key==='&')return m![0];if(key==='`')return text.slice(0,from);if(key==="'")return text.slice(to);
    if(key.startsWith('<'))return m!.groups?.[key.slice(1,-1)]??raw;
    const n=Number(key);if(n>0&&n<m!.length)return m![n]??'';
    if(key.length===2&&Number(key[0])>0&&Number(key[0])<m!.length)return (m![Number(key[0])]??'')+key[1];return raw;
   }):o.replace;
   out.push({from,to,text:m[0],replacement});
  }
  if(m[0].length===0){const cp=text.codePointAt(r.lastIndex);r.lastIndex+=cp&&cp>65535?2:1;}
 }
 return out;
}
export function applyHits(text:string,hits:Hit[]):string{for(let i=hits.length-1;i>=0;i--){const h=hits[i];text=text.slice(0,h.from)+h.replacement+text.slice(h.to);}return text;}
