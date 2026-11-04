import {useEffect,useRef} from 'react';
import {EditorState} from '@codemirror/state';
import {EditorView,Decoration,keymap} from '@codemirror/view';
import {basicSetup} from 'codemirror';
import {oneDark} from '@codemirror/theme-one-dark';
import {StreamLanguage} from '@codemirror/language';
import {xml} from '@codemirror/lang-xml';
import {undo,redo,historyKeymap} from '@codemirror/commands';
import type {Hit} from './search';
export type Doc={id:string,name:string,text:string,original:string,group:string,api?:number};
const smali=StreamLanguage.define({token(s){if(s.eatSpace())return null;if(s.match(/^#.*/))return 'comment';if(s.match(/^"(?:[^"\\]|\\.)*"/))return 'string';if(s.match(/^\.[\w-]+/))return 'keyword';if(s.match(/^:[\w_]+/))return 'labelName';if(s.match(/^[vp]\d+\b/))return 'variableName';if(s.match(/^-?(?:0x[\da-f]+|\d+)(?:[tTsSlL])?/i))return 'number';if(s.match(/^L[^;\s]+;/))return 'typeName';if(s.match(/^[\w/-]+/))return 'operator';s.next();return null;}});
export function Editor({doc,dark,hits,onChange,onReady}:{doc:Doc,dark:boolean,hits:Hit[],onChange:(id:string,text:string)=>void,onReady:(v:EditorView|null)=>void}){
 const host=useRef<HTMLDivElement>(null),v=useRef<EditorView|null>(null),states=useRef(new Map<string,EditorState>()),current=useRef(''),change=useRef(onChange);change.current=onChange;
 useEffect(()=>{if(!host.current)return;
 const view=new EditorView({parent:host.current});v.current=view;onReady(view);
 return()=>{view.destroy();onReady(null);};},[]);
 useEffect(()=>{const view=v.current;if(!view)return;
 if(current.current)states.current.set(current.current,view.state);
 const previous=states.current.get(doc.id);const extensions=[basicSetup,keymap.of([...historyKeymap,{key:'Mod-y',run:redo},{key:'Mod-z',run:undo}]),doc.name.endsWith('.xml')?xml():smali,theme.of(dark?[oneDark]:[]),highlight.of([]),EditorView.updateListener.of(u=>{if(u.docChanged)change.current(current.current,u.state.doc.toString());}),EditorView.theme({'&':{height:'100%',fontSize:'13px'},'.cm-scroller':{fontFamily:'"SFMono-Regular",Consolas,"Liberation Mono",monospace',lineHeight:'1.9'},'.cm-content':{padding:'22px 0'},'.cm-gutters':{background:'transparent',border:'none',color:'#606876'},'.cm-lineNumbers .cm-gutterElement':{padding:'0 24px 0 18px'},'&.cm-focused':{outline:'none'},'.cm-searchMatch':{backgroundColor:'#b2913066'},'.cm-searchMatch-selected':{backgroundColor:'#80cdb177'}})];
 current.current=doc.id;
 const state=previous&&previous.doc.toString()===doc.text?previous:EditorState.create({doc:doc.text,extensions});
 // Recreate extensions when theme changes while retaining per-file histories.
 view.setState(state);view.dispatch({effects:theme.reconfigure(dark?[oneDark]:[])});
 },[doc.id,dark]);
 useEffect(()=>{const view=v.current;if(view&&view.state.doc.toString()!==doc.text)view.dispatch({changes:{from:0,to:view.state.doc.length,insert:doc.text},userEvent:'input.replace.all'});},[doc.text]);
 useEffect(()=>{const view=v.current;if(!view)return;const marks=Decoration.set(hits.filter(h=>h.to>h.from&&h.to<=view.state.doc.length).slice(0,10000).map(h=>Decoration.mark({class:'cm-searchMatch'}).range(h.from,h.to)),true);
 const ext=EditorView.decorations.of(marks); // compartment replacement avoids accumulating marks
 view.dispatch({effects:highlight.reconfigure(ext)});
 },[hits,doc.id,doc.text]);
 return <div className="editor-host" ref={host}/>;
}
import {Compartment} from '@codemirror/state';
const highlight=new Compartment();const theme=new Compartment();
