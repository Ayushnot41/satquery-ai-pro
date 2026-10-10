import type {InvestigationResponse} from '../types/investigation';

export interface InvestigationJob {
  id: string;
  status: 'queued' | 'running' | 'complete' | 'error' | 'cancelled';
  result: InvestigationResponse | null;
  error: string | null;
  created_at: number;
  question?: string;
}

async function jobRequest(path: string, body?: unknown): Promise<any> {
  const response = await fetch(`/api/jobs${path}`, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'same-origin',
    headers: body === undefined ? {} : {'Content-Type': 'application/json'},
    body: body === undefined ? undefined : JSON.stringify(body), cache: 'no-store', signal: AbortSignal.timeout(20000),
  });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Investigation service unavailable (${response.status}).`);
  return data;
}
export const listJobs = (): Promise<InvestigationJob[]> => jobRequest('');
export const readJob = (id: string): Promise<InvestigationJob> => jobRequest(`/${encodeURIComponent(id)}`);
export const cancelJob = (id: string) => jobRequest(`/${encodeURIComponent(id)}/cancel`, {});
export async function submitInvestigation(question: string, imageryIds: string[], mode: string): Promise<string> {
  const job = await jobRequest('', {question, imagery_ids: imageryIds, mode});
  return job.id;
}
export async function waitForInvestigation(id: string, onProgress?: (job: InvestigationJob) => void, abandoned?: () => boolean): Promise<InvestigationResponse> {
  const deadline = Date.now() + 16 * 60 * 1000;
  while (Date.now() < deadline) {
    if(abandoned?.()) throw new Error('This report is no longer selected. The job remains saved.');
    const job = await readJob(id);
    onProgress?.(job);
    if (job.status === 'complete' && job.result) return job.result;
    if (job.status === 'cancelled') throw new Error('Investigation cancelled.');
    if (job.status === 'error') throw new Error(job.error || job.result?.answer || 'The investigation could not be completed.');
    await new Promise(resolve => setTimeout(resolve, 2000));
  }
  throw new Error('This investigation is taking longer than expected. Its saved job remains available in Background investigations.');
}
