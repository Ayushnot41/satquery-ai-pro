"use client";
import {useEffect,useRef,useState} from 'react';
import {useReducedMotion} from 'framer-motion';
import {Pause,Play} from 'lucide-react';

/** The preserved SVG stays intact; native SMIL controls pause its animation. */
export function AnimatedEarth(){
 const object=useRef<HTMLObjectElement>(null);
 const reduced=useReducedMotion();
 const [paused,setPaused]=useState(false),[visible,setVisible]=useState(true),[loaded,setLoaded]=useState(false);
 useEffect(()=>{const node=object.current;if(!node)return;const observer=new IntersectionObserver(entries=>setVisible(entries[0].isIntersecting));observer.observe(node);const visibility=()=>setVisible(document.visibilityState==='visible');document.addEventListener('visibilitychange',visibility);return()=>{observer.disconnect();document.removeEventListener('visibilitychange',visibility);};},[]);
 useEffect(()=>{const svg=object.current?.contentDocument?.documentElement as unknown as SVGSVGElement|undefined;if(svg&&typeof svg.pauseAnimations==='function'){if(paused||reduced||!visible)svg.pauseAnimations();else svg.unpauseAnimations();}},[paused,reduced,visible,loaded]);
 return <div className="pro-animated-earth"><object ref={object} type="image/svg+xml" data="/assets/earth_3d_orbit_constellation.svg" aria-label="Illustrative Earth with satellite orbits" onLoad={()=>setLoaded(true)} tabIndex={-1}><span>Earth and orbital illustration</span></object><button type="button" className="pro-motion-toggle" aria-label={paused?'Play orbital animation':'Pause orbital animation'} aria-pressed={paused||Boolean(reduced)} onClick={()=>setPaused(!paused)} disabled={Boolean(reduced)}>{paused||reduced?<Play size={14}/>:<Pause size={14}/>}<span>{reduced?'Reduced motion':paused?'Play animation':'Pause animation'}</span></button></div>;
}
