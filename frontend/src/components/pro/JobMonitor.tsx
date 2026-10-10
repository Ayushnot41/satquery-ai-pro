"use client";
import {useCallback, useEffect, useState} from 'react';
import {ChevronDown, LoaderCircle, RefreshCw} from 'lucide-react';
import {cancelJob, listJobs, readJob, type InvestigationJob} from '../../lib/jobs';
import type {InvestigationResponse} from '../../types/investigation';

export function JobMonitor({onOpen}: {onOpen: (result: InvestigationResponse) => void}) {
  const [jobs, setJobs] = useState<InvestigationJob[]>([]);
  const [error, setError] = useState('');
  const [expanded, setExpanded] = useState(false);
  const [busy, setBusy] = useState<string | null>(null);
  const refresh = useCallback(async () => {
    try {setJobs(await listJobs()); setError('');}
    catch (e) {setError((e as Error).message);}
  }, []);
  useEffect(() => {void refresh(); const timer = setInterval(refresh, 5000); return () => clearInterval(timer);}, [refresh]);
  const active = jobs.filter(job => job.status === 'queued' || job.status === 'running');
  async function act(job: InvestigationJob) {
    setBusy(job.id);
    try {
      if (job.status === 'queued' || job.status === 'running') await cancelJob(job.id);
      else {const saved = await readJob(job.id); if (saved.result) onOpen(saved.result);}
      await refresh();
    } catch (e) {setError((e as Error).message);} finally {setBusy(null);}
  }
  if (!jobs.length && !error) return null;
  return <section className="pro-job-monitor" aria-label="Background investigations">
    <button className="pro-job-toggle" aria-expanded={expanded} onClick={() => setExpanded(!expanded)}>
      {active.length > 0 && <LoaderCircle size={15} className="animate-spin"/>}
      Background investigations <span>{active.length ? `${active.length} in progress` : `${jobs.length} saved`}</span><ChevronDown size={15}/>
    </button>
    {expanded && <div className="pro-job-list">
      <p>Jobs survive page reloads. Completed reports also appear in history. Cancellation may not stop a provider request already sent.</p>
      {error && <div role="alert" className="pro-alert">{error}<button onClick={refresh} aria-label="Retry loading jobs"><RefreshCw size={16}/></button></div>}
      {jobs.map(job => <div className="pro-job" key={job.id}><span><strong>{job.question || 'Imagery investigation'}</strong><small>{job.status} · {new Date(job.created_at * 1000).toLocaleString()}</small>{job.error && <small className="pro-job-error">{job.error}</small>}</span>
        <button className="pro-secondary" onClick={() => act(job)} disabled={busy === job.id || job.status === 'cancelled' || (job.status === 'error' && !job.result)}>{busy === job.id ? 'Working…' : job.status === 'queued' || job.status === 'running' ? 'Cancel' : job.status === 'cancelled' ? 'Cancelled' : 'Open report'}</button>
      </div>)}
    </div>}
  </section>;
}
