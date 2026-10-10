"use client";
import {useEffect, useRef, useState} from 'react';
import {AuthUser, identityRequest} from './AuthGatekeeper';

export function GoogleSignIn({clientId, onAuthenticated}: {clientId:string; onAuthenticated:(user:AuthUser)=>void}) {
  const box = useRef<HTMLDivElement>(null);
  const complete = useRef(onAuthenticated);
  complete.current = onAuthenticated;
  const [error,setError] = useState('');
  const [attempt,setAttempt] = useState(0);
  useEffect(() => {
    let cancelled = false;
    let refresh:ReturnType<typeof setTimeout>;
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    setError('');
    async function initialize() {
      if(cancelled) return;
      try {
        const {nonce} = await identityRequest('google/nonce', {});
        if(cancelled) return;
        const google = (window as any).google;
        google.accounts.id.initialize({client_id:clientId, nonce, callback:async ({credential}:{credential:string}) => {
          clearTimeout(refresh);
          try {
            const data = await identityRequest('google', {credential});
            if(!cancelled) complete.current(data.user);
          } catch(e) {
            if(!cancelled) {setError((e as Error).message); if(box.current) box.current.replaceChildren();}
          }
        }});
        if(box.current) {
          box.current.replaceChildren();
          google.accounts.id.renderButton(box.current, {theme:'outline', size:'large', text:'continue_with', width:Math.min(320, box.current.clientWidth)});
        }
        refresh = setTimeout(() => {if(!cancelled) setAttempt(value => value + 1);}, 240000);
      } catch(e) {if(!cancelled) setError((e as Error).message);}
    }
    script.onload = initialize;
    script.onerror = () => {if(!cancelled) setError('Google sign-in could not load. Check your connection and retry.');};
    document.head.appendChild(script);
    return () => {cancelled = true; clearTimeout(refresh); script.remove();};
  }, [clientId, attempt]);
  return <div className="mt-4"><div ref={box}/>{error&&<div role="alert" className="pro-alert">{error}<button type="button" className="pro-text-button" onClick={()=>setAttempt(value=>value+1)}>Retry Google sign-in</button></div>}</div>;
}
