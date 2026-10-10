"use client";
import {useEffect,useRef,useState} from 'react';
import {Search,X,ArrowUpRight,type LucideIcon} from 'lucide-react';

export function CommandPalette({items,onSelect,onClose}:{items:{id:string;label:string;Icon:LucideIcon}[];onSelect:(id:string)=>void;onClose:()=>void}) {
 const dialog=useRef<HTMLDialogElement>(null);
 const [query,setQuery]=useState('');
 useEffect(()=>{const node=dialog.current;node?.showModal();return()=>node?.close();},[]);
 const results=items.filter(item=>item.label.toLowerCase().includes(query.toLowerCase()));
 return <dialog ref={dialog} className="pro-native-command" aria-labelledby="command-title" onCancel={event=>{event.preventDefault();onClose();}} onClick={event=>{if(event.target===dialog.current)onClose();}}>
  <section className="pro-command"><h2 id="command-title" className="sr-only">Find a workspace tool</h2><div className="pro-row"><Search size={20}/><label className="sr-only" htmlFor="command-query">Search tools</label><input id="command-query" autoFocus placeholder="Search maps, agents, radar…" value={query} onChange={event=>setQuery(event.target.value)}/><button aria-label="Close search" onClick={onClose}><X size={18}/></button></div>
  <div className="pro-command-results">{results.length?results.map(({id,label,Icon})=><button key={id} onClick={()=>onSelect(id)}><Icon size={18}/>{label}<ArrowUpRight size={16}/></button>):<p className="pro-empty" role="status">No tools match “{query}”. Try maps, radar, or history.</p>}</div></section>
 </dialog>;
}
