import {findHits} from './search';
self.onmessage=({data})=>{try{self.postMessage({id:data.id,results:data.docs.map((d:any)=>({id:d.id,hits:findHits(d.text,data.options)}))});}catch(e){self.postMessage({id:data.id,error:String(e)});}};
