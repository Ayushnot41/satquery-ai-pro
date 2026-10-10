"use client";
import React,{useState,useEffect,useCallback,useRef} from 'react';
import dynamic from 'next/dynamic';
import {MotionConfig, motion, useReducedMotion} from 'framer-motion';
import {Globe2,LayoutDashboard,Plus,Map,MessagesSquare,FlaskConical,History,GitCompareArrows,Shield,ScanLine,Route,Orbit,Settings,Search,ChevronRight,LogOut,Menu,X,ArrowUpRight,LoaderCircle} from 'lucide-react';
import {AuthGatekeeper,AuthUser,identityRequest} from '../components/auth/AuthGatekeeper';
import {Dashboard} from '../components/pro/Dashboard';
import {IdentityPanel} from '../components/pro/IdentityPanel';
import {JobMonitor} from '../components/pro/JobMonitor';
import {CommandPalette} from '../components/pro/CommandPalette';
import {submitInvestigation,waitForInvestigation} from '../lib/jobs';
import {checkHealth,uploadImagery,runInvestigation,investigationResponseToAnalysisResult,investigationMode} from '../lib/api';
import type {AnalysisResult} from '../types/investigation';
import type {NewAnalysisState} from '../components/analysis/NewAnalysisView';
const loading=()=> <div className="pro-loading"><LoaderCircle className="animate-spin"/>Opening workspace…</div>;
const NewAnalysisView=dynamic(()=>import('../components/analysis/NewAnalysisView').then(m=>m.NewAnalysisView),{loading});
const AnalysisResultsView=dynamic(()=>import('../components/analysis/AnalysisResultsView').then(m=>m.AnalysisResultsView),{loading});
const StaticImageComparisonView=dynamic(()=>import('../components/screens/StaticImageComparisonView').then(m=>m.StaticImageComparisonView),{loading});
const InvestigationWorkspace=dynamic(()=>import('../components/screens/InvestigationWorkspace').then(m=>m.InvestigationWorkspace),{loading});
const AgentDebateView=dynamic(()=>import('../components/screens/AgentDebateView').then(m=>m.AgentDebateView),{loading});
const EvaluationView=dynamic(()=>import('../components/screens/EvaluationView').then(m=>m.EvaluationView),{loading});
const AnalysisHistoryView=dynamic(()=>import('../components/screens/AnalysisHistoryView').then(m=>m.AnalysisHistoryView),{loading});
const MissionView=dynamic(()=>import('../components/screens/MissionView').then(m=>m.MissionView),{loading,ssr:false});
const MissionHome=dynamic(()=>import('../components/screens/MissionHome').then(m=>m.MissionHome),{loading});
const DefenseIntelView=dynamic(()=>import('../components/screens/DefenseIntelView').then(m=>m.DefenseIntelView),{loading});
const SarReaderView=dynamic(()=>import('../components/screens/SarReaderView').then(m=>m.SarReaderView),{loading});
const DisasterRoutingView=dynamic(()=>import('../components/screens/DisasterRoutingView').then(m=>m.DisasterRoutingView),{loading});

const groups=[{label:'WORKSPACE',items:[['home','Overview',LayoutDashboard],['new_analysis','New investigation',Plus],['workspace','Map workspace',Map],['image_compare','Image comparison',GitCompareArrows],['history','Investigation history',History]]},{label:'EXPLORE',items:[['cockpit','3D Earth cockpit',Globe2],['mission_view','Mission control',Orbit],['sar_reader','SAR radar',ScanLine],['defense_ops','Defense simulation',Shield],['disaster_routing','Disaster scenarios',Route]]},{label:'INTELLIGENCE',items:[['debate','Agent council',MessagesSquare],['evaluation','Evaluation lab',FlaskConical],['advanced','Advanced consoles',Orbit],['original_home','Original mission hub',LayoutDashboard]]}];
const all=groups.flatMap(g=>g.items);

export default function Home(){
 const runGeneration=useRef(0);
 const reduceMotion=useReducedMotion();
 const [tab,setTab]=useState('home'),[user,setUser]=useState<AuthUser|null>(null),[checking,setChecking]=useState(true),[health,setHealth]=useState('checking'),[menu,setMenu]=useState(false),[showSearch,setShowSearch]=useState(false);
 const [scenario,setScenario]=useState<string|undefined>(),[query,setQuery]=useState('Where has construction increased between these two dates?'),[result,setResult]=useState<AnalysisResult|null>(null),[error,setError]=useState('');
 const navigate=useCallback((next:string)=>{setTab(next);setMenu(false);setShowSearch(false);setError('');window.location.hash=next;},[]);
 const authenticate=useCallback((next:AuthUser)=>setUser(next),[]);
 useEffect(()=>{identityRequest('me').then(d=>setUser(d.user)).catch(()=>{}).finally(()=>setChecking(false));const sync=()=>{const next=window.location.hash.slice(1);if([...all.map(x=>x[0]),'settings','analysis_results'].includes(next))setTab(next);};sync();window.addEventListener('hashchange',sync);return()=>window.removeEventListener('hashchange',sync);},[]);
 useEffect(()=>{const update=()=>checkHealth().then(d=>setHealth(d.status));update();const timer=setInterval(update,30000);return()=>clearInterval(timer);},[]);
 useEffect(()=>{function keyboard(e:KeyboardEvent){if((e.ctrlKey||e.metaKey)&&e.key==='k'){e.preventDefault();setShowSearch(s=>!s);}if(e.key==='Escape'){setShowSearch(false);setMenu(false);}}window.addEventListener('keydown',keyboard);return()=>window.removeEventListener('keydown',keyboard);},[]);
 async function logout(){try{await identityRequest('logout',{});runGeneration.current++;setUser(null);setResult(null);navigate('home');}catch(e){setError((e as Error).message);}}
 function viewResult(r:AnalysisResult){runGeneration.current++;setResult(r);navigate('analysis_results');}
 async function run(state:NewAnalysisState){
   const urls=[state.slot1?.previewUrl,state.slot2?.previewUrl].filter(Boolean) as string[];
   const pending:AnalysisResult={run_id:`run-${Date.now()}`,created_at:new Date().toISOString(),mode:state.mode,mission_context:state.missionContext,question:state.question,input_ids:[],answer:'Processing imagery and gathering evidence…',status:'processing',confidence:null,metrics:{},evidence:{type:'bounding_box',regions:[]},limitations:[],trace:[],imageUrls:urls,previewUrl:urls[0]};
   viewResult(pending);
   const generation=runGeneration.current;
   try{const ids:string[]=[],previews:string[]=[];
     const selected=[state.slot1,state.slot2].filter(Boolean);
     if(selected.some(slot=>slot?.file) && selected.some(slot=>slot?.isDemo))throw Error('Use either uploaded images or demo scenes for both slots.');
     for(const slot of [state.slot1,state.slot2]){if(slot?.file){const upload=await uploadImagery(slot.file);ids.push(upload.id);previews.push(upload.preview_url);}else if(slot && !slot.isDemo){throw Error('Select an uploaded file or choose a demo scenario.');}}
     if(ids.length===0)ids.push(...(state.mode==='optical_sar'?['demo-flood-pre-optical','demo-flood-post-sar']:state.mode==='bi_temporal'?['demo-construction-before','demo-construction-after']:['demo-construction-before']));
     const jobId=await submitInvestigation(state.question,ids,state.mode==='bi_temporal'?'temporal':state.mode==='optical_sar'?'auto':'optical');
     const response=await waitForInvestigation(jobId,job=>{if(generation===runGeneration.current)setResult({...pending,run_id:jobId,answer:job.status==='queued'?'Investigation queued. Waiting for an available worker…':'The specialist pipeline is processing your imagery…'});},()=>generation!==runGeneration.current);
     if(generation===runGeneration.current)setResult(investigationResponseToAnalysisResult(response,state.mode,state.question,previews.length?previews:urls,state.missionContext));
   }catch(e){if(generation===runGeneration.current)setResult({...pending,status:'error',answer:(e as Error).message,limitations:['No analysis was completed. Correct the issue and retry.']});}
 }
 if(checking)return <div className="pro-loading min-h-screen"><LoaderCircle className="animate-spin"/>Connecting to your workspace…</div>;
 if(!user)return <AuthGatekeeper currentUser={null} onAuthenticated={authenticate}/>;
 const title=tab==='settings'?'Account & verification':tab==='analysis_results'?'Investigation report':(all.find(x=>x[0]===tab)?.[1] as string)||'Workspace';
 return <MotionConfig reducedMotion="user"><div className="pro-shell"><a className="pro-skip" href="#workspace-main">Skip to workspace</a>{menu&&<button className="pro-scrim" aria-label="Close navigation" onClick={()=>setMenu(false)}/>}
 <aside className={`pro-sidebar ${menu?'is-open':''}`}><button className="pro-brand" onClick={()=>navigate('home')}><Globe2 size={28}/><span>satquery<span className="pro-brand-ai"> / AI</span></span><small>PRO</small></button><div className="pro-workspace-label"><div className="pro-avatar">{user.name.charAt(0)}</div><span><strong>{user.guest?'Demo workspace':'Personal workspace'}</strong><small>{user.guest?'Explore the possibilities':user.name}</small></span><ChevronRight size={15}/></div>
 <nav aria-label="Main navigation">{groups.map(g=><div className="pro-nav-group" key={g.label}><span>{g.label}</span>{g.items.map(([id,label,Icon])=>{const I=Icon as typeof Globe2;return <button key={id as string} aria-current={tab===id?'page':undefined} onClick={()=>navigate(id as string)} className={tab===id?'active':''}><I size={17}/><span>{label as string}</span>{id==='new_analysis'&&<small>+</small>}</button>;})}</div>)}</nav>
 <div className="pro-sidebar-bottom"><button onClick={()=>navigate('settings')} className={tab==='settings'?'active':''}><Settings size={17}/>Account & verification</button><div className="pro-user-row"><div className="pro-avatar">{user.name.charAt(0)}</div><span><strong>{user.name}</strong><small>{user.email_verified?'Email verified':user.phone_verified?'Phone verified':user.guest?'Demo explorer':'Verification needed'}</small></span><button onClick={logout} aria-label="Sign out" title="Sign out"><LogOut size={17}/></button></div></div></aside>
 <div className="pro-workspace"><header className="pro-topbar"><div className="pro-row"><button className="pro-mobile-toggle" aria-label="Open navigation" onClick={()=>setMenu(true)}><Menu size={21}/></button><span className="pro-breadcrumb">Workspace</span><ChevronRight size={14}/><strong>{title}</strong></div><div className="pro-row"><button className="pro-search-button" onClick={()=>setShowSearch(true)}><Search size={16}/><span>Find a tool</span><kbd>⌘ K</kbd></button><span className={`pro-service ${health==='healthy'?'connected':''}`}><i/>{health==='healthy'?'Connected':'Service unavailable'}</span></div></header>
 <div className="pro-mode-banner"><span className="pro-pill pro-amber">{user.guest?'DEMO WORKSPACE':'UNVERIFIED ANALYSIS'}</span><span>Simulated consoles and sample results are illustrative. Uploaded imagery requires a configured vision provider.</span><button onClick={()=>navigate('settings')}>Workspace details<ArrowUpRight size={13}/></button></div>
 <JobMonitor onOpen={response=>viewResult(investigationResponseToAnalysisResult(response,investigationMode(response),response.question))}/>
 <motion.main key={tab} id="workspace-main" className="pro-main" tabIndex={-1} initial={reduceMotion?false:{opacity:0.7,y:5}} animate={{opacity:1,y:0}} transition={{duration:0.18,ease:'easeOut'}}>
 {error&&<div role="alert" className="pro-alert m-5">{error}</div>}
 {tab==='home'&&<Dashboard navigate={navigate} userName={user.name} health={health}/>}
 {tab==='settings'&&<IdentityPanel user={user} onUpdate={setUser}/>}
 {tab==='new_analysis'&&<NewAnalysisView onRunPipeline={run} onNavigateHome={()=>navigate('home')}/>}
 {tab==='analysis_results'&&(result?<AnalysisResultsView result={result} onBack={()=>navigate('new_analysis')}/>:<div className="pro-empty">No report selected. <button onClick={()=>navigate('history')}>Open history</button></div>)}
 {tab==='workspace'&&<InvestigationWorkspace initialScenarioId={scenario} initialQuery={query} onViewResults={viewResult}/>}
 {tab==='image_compare'&&<StaticImageComparisonView onViewDetailedResult={viewResult}/>}
 {tab==='debate'&&<AgentDebateView onTriggerInvestigation={(id,q)=>{setScenario(id);setQuery(q);navigate('workspace');}}/>}
 {tab==='evaluation'&&<EvaluationView/>}
 {tab==='history'&&<AnalysisHistoryView onSelectResult={viewResult} onNewAnalysis={()=>navigate('new_analysis')}/>}
 {tab==='mission_view'&&<MissionView onTriggerInvestigation={(_,q)=>{setQuery(q);navigate('workspace');}}/>}
 {tab==='original_home'&&<MissionHome onStartInvestigation={id=>{setScenario(id);navigate('workspace');}} onOpenMissionView={()=>navigate('mission_view')}/>}
 {tab==='defense_ops'&&<DefenseIntelView/>}{tab==='sar_reader'&&<SarReaderView/>}{tab==='disaster_routing'&&<DisasterRoutingView/>}
 {(tab==='cockpit'||tab==='advanced')&&<div className="pro-console"><div className="pro-console-heading"><div><span className="pro-eyebrow">ORIGINAL CAPABILITIES · ENHANCED CONSOLE</span><h1>{tab==='cockpit'?"3D Earth · God's Eye":"Advanced mission consoles"}</h1></div><a className="pro-secondary" href={`/console?screen=${tab==='cockpit'?'mission':'futuristic'}`} target="_blank" rel="noreferrer">Open full screen<ArrowUpRight size={16}/></a></div><iframe key={tab} title={tab==='cockpit'?'3D Earth cockpit':'Advanced mission consoles'} src={`/console?screen=${tab==='cockpit'?'mission':'futuristic'}&embed=1`} allow="fullscreen"/></div>}
 </motion.main></div>
 {showSearch&&<CommandPalette items={all.map(([id,label,Icon])=>({id:id as string,label:label as string,Icon:Icon as typeof Globe2}))} onSelect={navigate} onClose={()=>setShowSearch(false)}/>}
 </div></MotionConfig>;
}
