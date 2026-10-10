"use client";
import {AnimatedEarth} from "../pro/AnimatedEarth";
import React, { useState, useEffect, useRef } from 'react';
import { ArrowRight, Globe2, LockKeyhole, LoaderCircle } from 'lucide-react';

export interface AuthUser {
  id: string; name: string; email: string; organization: string; clearance_level: string;
  role?: string; token?: string; guest?: boolean; email_verified?: boolean; phone_verified?: boolean; phone?: string;
}
export function getStoredAuthUser(): AuthUser | null { return null; }
export function clearStoredAuthUser() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('satquery_auth_user'); localStorage.removeItem('satquery_auth_token');
  }
}
export async function identityRequest(path: string, body?: unknown) {
  const response = await fetch(`/api/auth/${path}`, {method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? {} : {'Content-Type':'application/json'}, credentials:'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body)});
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : 'The request could not be completed. Check your input and connection.');
  return data;
}

export function AuthGatekeeper({onAuthenticated, currentUser}: {onAuthenticated:(user:AuthUser)=>void;currentUser:AuthUser|null}) {
  const [mode,setMode] = useState<'login'|'register'|'forgot'|'reset'|'phone'|'phone-code'>('login');
  const [phone,setPhone] = useState('');
  const [config,setConfig] = useState<any>(null);
  const [error,setError] = useState(''); const [notice,setNotice] = useState('');
  const [busy,setBusy] = useState(false); const [email,setEmail] = useState(''); const [password,setPassword] = useState('');
  const [name,setName] = useState(''); const [code,setCode] = useState('');
  const googleBox = useRef<HTMLDivElement>(null);
  useEffect(() => { identityRequest('config').then(setConfig).catch(() => setError('The workspace service is unavailable. Start the backend and try again.')); clearStoredAuthUser(); }, []);
  useEffect(() => {
    if (!config?.google_client_id || currentUser) return;
    const script = document.createElement('script'); script.src='https://accounts.google.com/gsi/client'; script.async=true;
    script.onload = () => {
      const google = (window as any).google;
      google.accounts.id.initialize({client_id:config.google_client_id, callback:async ({credential}:any) => {
        try {const data=await identityRequest('google',{credential});onAuthenticated(data.user);} catch(e) {setError((e as Error).message);}
      }});
      if(googleBox.current) google.accounts.id.renderButton(googleBox.current,{theme:'outline',size:'large',width:320});
    };
    document.head.appendChild(script); return () => script.remove();
  },[config?.google_client_id,currentUser,onAuthenticated]);
  if(currentUser) return null;
  async function submit(event:React.FormEvent) {
    event.preventDefault();setBusy(true);setError('');setNotice('');
    try {
      if(mode==='phone') {const d=await identityRequest('otp/send',{phone,purpose:'login'});setNotice(d.development_code ? `Local development code: ${d.development_code}` : d.message);setCode('');setMode('phone-code');}
      else if(mode==='phone-code') {const d=await identityRequest('otp/verify',{phone,otp:code,purpose:'login'});onAuthenticated(d.user);}
      else if(mode==='forgot') {const d=await identityRequest('password/forgot',{email});setNotice(d.development_token ? `Local development code: ${d.development_token}` : d.message);setMode('reset');}
      else if(mode==='reset') {const d=await identityRequest('password/reset',{token:code,password});setMode('login');setPassword('');setNotice(d.message);}
      else {const d=await identityRequest(mode, mode==='register'?{name,email,password}:{email,password});onAuthenticated(d.user);}
    } catch(e) {setError((e as Error).message);} finally {setBusy(false);}
  }
  async function guest() {setBusy(true);setError('');try{const d=await identityRequest('guest-token',{});onAuthenticated(d.user);}catch(e){setError((e as Error).message);}finally{setBusy(false);}}
  return <main className="pro-auth">
    <section className="pro-auth-story"><a className="pro-brand" href="/"><Globe2 size={30}/><span>satquery<span className="pro-brand-ai"> / AI</span></span><small>PRO</small></a>
      <div className="pro-auth-art"><AnimatedEarth/><span className="pro-orbit-label">A NEW PERSPECTIVE ON OUR PLANET</span></div>
      <div><span className="pro-eyebrow">EARTH INTELLIGENCE WORKSPACE</span><h1>See the change.<br/><em>Understand the why.</em></h1><p>Bring imagery, geospatial context, and nine specialist agents into one focused workspace.</p></div>
      <footer><span>Optical + radar imagery</span><span>3D exploration</span><span>Traceable evidence</span></footer>
    </section>
    <section className="pro-auth-panel"><div className="pro-auth-form"><div className="pro-icon-tile"><LockKeyhole size={23}/></div><span className="pro-eyebrow">YOUR WORKSPACE, CONNECTED</span>
      <h2>{config?.public_preview?'Explore Satquery.':mode==='phone'?'Sign in by phone.':mode==='phone-code'?'Enter your SMS code.':mode==='login'?'Welcome back.':mode==='register'?'Start exploring.':mode==='forgot'?'Reset your password.':'Choose a new password.'}</h2>
      <p>{config?.public_preview?'Try sample imagery, investigations, and reports. This temporary preview does not accept accounts or uploads.':mode==='register'?'Create your private workspace. Verify your email in Account settings.':'Sign in to your imagery, investigations, and saved evidence.'}</p>
      {!config?.public_preview&&<form onSubmit={submit}>
        {mode==='register'&&<label>Full name<input autoComplete="name" value={name} onChange={e=>setName(e.target.value)} required minLength={2}/></label>}
        {(mode==='login'||mode==='register'||mode==='forgot')&&<label>Email address<input type="email" autoComplete="email" placeholder="you@organization.com" value={email} onChange={e=>setEmail(e.target.value)} required/></label>}
        {mode==='phone'&&<label>Verified phone number<input type="tel" autoComplete="tel" placeholder="+91…" value={phone} onChange={e=>setPhone(e.target.value)} pattern="\+[1-9][0-9]{7,14}" required/><small>Use a phone already verified in your account settings.</small></label>}
        {mode==='phone-code'&&<label>SMS code<input autoComplete="one-time-code" inputMode="numeric" pattern="[0-9]{6}" maxLength={6} value={code} onChange={e=>setCode(e.target.value)} required/></label>}
        {mode==='reset'&&<label>Reset code<input autoComplete="one-time-code" value={code} onChange={e=>setCode(e.target.value)} required/></label>}
        {(mode==='login'||mode==='register'||mode==='reset')&&<label>Password<input type="password" autoComplete={mode==='login'?'current-password':'new-password'} placeholder={mode==='login'?'Enter your password':'At least 12 characters'} value={password} minLength={mode==='login'?1:12} maxLength={256} onChange={e=>setPassword(e.target.value)} required/></label>}
        {mode==='login'&&<button type="button" className="pro-text-button pro-forgot" onClick={()=>{setMode('forgot');setError('');}}>Forgot password?</button>}
        {error&&<div role="alert" className="pro-alert">{error}</div>}{notice&&<div role="status" className="pro-notice break-all">{notice}</div>}
        <button className="pro-primary" disabled={busy}>{busy?<LoaderCircle className="animate-spin" size={17}/>:mode==='phone'?'Send SMS code':mode==='phone-code'?'Verify and sign in':mode==='login'?'Sign in':mode==='register'?'Create account':mode==='forgot'?'Send reset code':'Update password'}<ArrowRight size={17}/></button>
      </form>}
      {config?.public_preview&&error&&<div role="alert" className="pro-alert">{error}</div>}
      <div ref={googleBox} className="mt-4"/>
      {mode==='login'&&(config?.sms_delivery||config?.development_codes)&&<button className="pro-secondary w-full mt-3" disabled={busy} onClick={()=>{setMode('phone');setError('');setNotice('');}}>Sign in with a verified phone</button>}
      {!config?.public_preview&&<div className="pro-auth-switch">{mode==='login'?'New to Satquery?':'Already have an account?'} <button onClick={()=>{setMode(mode==='login'?'register':'login');setError('');setNotice('');}}>{mode==='login'?'Create an account':'Sign in'}</button></div>}
      {config?.demo_guest&&<><div className="pro-divider"><span>OR EXPLORE FIRST</span></div><button className="pro-secondary w-full" disabled={busy} onClick={guest}>Explore the demo workspace <ArrowRight size={16}/></button><p className="pro-auth-note">Synthetic scenarios. No live surveillance or verified geographic conclusions.</p></>}
    </div><div className="pro-auth-bottom">Satquery AI Pro <span>Built on BHUVISION · Team BANKAI</span></div></section>
  </main>;
}
