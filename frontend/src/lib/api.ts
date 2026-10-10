import { InvestigationResponse } from "../types/investigation";
export type { InvestigationResponse };

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "/api";

export async function checkHealth(): Promise<{ status: string; [key: string]: unknown }> {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error("Health check failed");
    return await res.json();
  } catch {
    return { status: "unavailable" };
  }
}

export async function runInvestigation(
  questionOrPayload: string | Record<string, unknown>,
  imageryIds?: string[],
  mode: string = "auto"
): Promise<InvestigationResponse> {
  const body =
    typeof questionOrPayload === "string"
      ? {
          question: questionOrPayload,
          imagery_ids: imageryIds || ["demo-construction-before", "demo-construction-after"],
          mode,
        }
      : questionOrPayload;

  const res = await fetch(`${API_BASE}/investigate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {const error=await res.json().catch(()=>({}));throw new Error(error.detail || `Investigation failed (${res.status})`);}
  return await res.json();
}

export async function fetchAgentDebate(scenario: string, location?: string): Promise<any> {
  try {
    const loc = location ? encodeURIComponent(location) : "Brahmaputra Valley, Assam";
    const sc = encodeURIComponent(scenario);
    const res = await fetch(`${API_BASE}/debate?scenario=${sc}&target_location=${loc}`);
    if (!res.ok) return null;
    return await res.json();
  } catch {
    return null;
  }
}

export async function analyzeSpectral(lat: number, lon: number, indexType: string = "ndvi"): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/investigate/spectral/analyze?lat=${lat}&lon=${lon}&index_type=${indexType}`);
    return await res.json();
  } catch {
    return { status: "error" };
  }
}

export async function measureGeodesicArea(coordinates: [number, number][] | Record<string, unknown>): Promise<any> {
  try {
    const body = Array.isArray(coordinates) ? { coordinates } : coordinates;
    const res = await fetch(`${API_BASE}/investigate/measure/area`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    return await res.json();
  } catch {
    return { status: "error" };
  }
}

export async function fetchTrafficFlow(lat: number, lon: number): Promise<any> {
  const res = await fetch(`${API_BASE}/traffic/flow?lat=${lat}&lon=${lon}`);
  return await res.json();
}

export async function exportInvestigationGeoJSON(investigationId: string): Promise<any> {
  const res = await fetch(`${API_BASE}/investigate/${investigationId}/geojson`);
  return checkedResponse(res);
}
export async function uploadImagery(file: File): Promise<{
  id: string;
  filename: string;
  preview_url: string;
  metadata?: any;
}> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/imagery/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || "Image upload failed");
  }
  return await res.json();
}

import type {
  AnalysisResult,
  AnalysisMode,
  EvidenceRegion,
  TraceStep,
} from "../types/investigation";

export function investigationResponseToAnalysisResult(
  resp: InvestigationResponse,
  mode: AnalysisMode,
  question: string,
  imageUrls?: string[],
  missionContext: string = "General Change Analysis"
): AnalysisResult {
  if (!imageUrls?.length) {
    imageUrls = resp.provenance?.preview_urls as string[] | undefined;
    if (!imageUrls?.length && resp.provenance?.mode === 'simulation') {
      imageUrls = (resp.provenance.imagery_ids as string[] || []).filter(id=>/^demo-[a-zA-Z0-9_-]+$/.test(id)).map(id=>`/assets/${id}.png`);
    }
  }
  const dimensions = resp.provenance?.image_dimensions as {width:number;height:number}|undefined;
  const regions: EvidenceRegion[] = [];
  const sourceRegions = resp.grounding?.regions?.length ? resp.grounding.regions : resp.change_result?.change_regions || [];
  for (const [index, region] of sourceRegions.entries()) {
    if (!region.bbox || region.bbox.length !== 4 || !region.bbox.every(Number.isFinite)) continue;
    let [x1, y1, x2, y2] = region.bbox;
    if (region.coordinate_space === 'pixel' || (!region.coordinate_space && Math.max(...region.bbox) > 1)) {
      if (!dimensions || dimensions.width <= 0 || dimensions.height <= 0) continue;
      x1 /= dimensions.width; x2 /= dimensions.width;
      y1 /= dimensions.height; y2 /= dimensions.height;
    }
    if (!(0 <= x1 && x1 < x2 && x2 <= 1 && 0 <= y1 && y1 < y2 && y2 <= 1)) continue;
    regions.push({id: `region-${index + 1}`, label: region.change_type || 'Detected region',
      score: region.change_type?.startsWith('Salient region') ? null : region.change_magnitude ?? null,
      type: 'bounding_box', bbox: {x:x1, y:y1, width:x2-x1, height:y2-y1}});
  }
  mode = investigationMode(resp, mode);

  // Convert trace events
  const trace: TraceStep[] = (resp.trace?.events || []).map((ev, i) => ({
    step: ev.message || `Step ${i + 1}`,
    tool: `${ev.agent_name} (${ev.model_used || "Local Agent"})`,
    duration_ms: Math.round(ev.duration_ms ?? 0),
    status: ev.event_type.includes("error")
      ? "failed"
      : ev.event_type.includes("warning")
      ? "warning"
      : "success",
    detail: ev.message,
    timestamp_offset_ms: Math.max(0, Date.parse(ev.timestamp) - Date.parse(resp.trace?.started_at || ev.timestamp)),
  }));

  const confidenceScore = resp.confidence?.confidence_score == null ? null : Math.round(resp.confidence.confidence_score * 100);

  const metrics: Record<string, string | number> = {
    "Objects / Parcels": regions.length,
    "Sensors Evaluated": resp.sensor_decision?.decision || "Not reported",
    "Model Engine": resp.vqa_result?.model_name || "Not reported",
    "Total Pipeline Latency": resp.total_duration_ms == null ? "Not recorded" : `${resp.total_duration_ms.toFixed(0)} ms`,
  };

  if (resp.change_result?.has_change) {
    metrics["Change Percentage"] = `${resp.change_result.change_percentage}%`;
    metrics["Total Changed Pixels"] = resp.change_result.total_changed_pixels;
  }

  return {
    run_id: resp.investigation_id,
    provenance: resp.provenance,
    total_duration_ms: resp.total_duration_ms,
    created_at: resp.created_at || new Date().toISOString(),
    mode,
    mission_context: missionContext,
    question: question || resp.question,
    input_ids: (resp.provenance?.imagery_ids as string[] | undefined) || [],
    answer: resp.answer || resp.fused_evidence?.primary_answer || resp.vqa_result?.answer || "No answer was returned.",
    status: resp.status === "error" ? "error" : resp.status === "complete" ? "complete" : "processing",
    confidence: confidenceScore,
    metrics,
    evidence: {
      type: "bounding_box",
      regions,
    },
    limitations: [...(resp.provenance?.limitations as string[] || []), ...(resp.confidence?.uncertainties || []), 'Grounded regions and model interpretations require independent validation.'],
    trace,
    imageUrls: imageUrls || [],
    previewUrl: imageUrls && imageUrls.length > 0 ? imageUrls[0] : undefined,
  };
}


// â”€â”€â”€ Benchmark & History Protocol API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export interface BenchmarkMetric {
  id: string;
  name: string;
  dataset: string;
  value: string | null;
  numeric_value?: number;
  baseline?: string;
  evaluated: boolean;
  notes?: string;
}

export interface BenchmarkCategory {
  category_id: string;
  tag: string;
  title: string;
  metrics_count: number;
  metrics: BenchmarkMetric[];
}

export interface BenchmarkProtocolState {
  is_evaluated: boolean;
  last_run_at: string | null;
  categories: BenchmarkCategory[];
}

async function checkedResponse(response: Response): Promise<any> {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(typeof data.detail === 'string' ? data.detail : `Request failed (${response.status}). Please retry.`);
  return data;
}

export function investigationMode(response: InvestigationResponse, fallback: AnalysisMode = 'single_image'): AnalysisMode {
  const ids = response.provenance?.imagery_ids as string[] | undefined;
  if (response.provenance?.analysis_mode === 'sar' || ids?.some(id => id.includes('-sar'))) return 'optical_sar';
  if (response.provenance?.analysis_mode === 'temporal' || response.plan?.requires_temporal || (ids?.length || 0) > 1) return 'bi_temporal';
  return fallback;
}

export async function fetchInvestigationHistory(): Promise<InvestigationResponse[]> {
  return checkedResponse(await fetch(`${API_BASE}/investigate`, {cache:'no-store', signal:AbortSignal.timeout(20000)}));
}
export async function deleteInvestigation(id: string): Promise<boolean> {
  await checkedResponse(await fetch(`${API_BASE}/investigate/${encodeURIComponent(id)}`, {method:'DELETE'}));
  return true;
}
export async function clearInvestigationCache(): Promise<boolean> {
  await checkedResponse(await fetch(`${API_BASE}/investigate/clear-cache`, {method:'POST'}));
  return true;
}

export async function fetchBenchmarkProtocol(): Promise<BenchmarkProtocolState> {
  try {
    const res = await fetch(`${API_BASE}/benchmark/protocol`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("fetchBenchmarkProtocol failed:", err);
    return { is_evaluated: false, last_run_at: null, categories: [] };
  }
}

export async function runBenchmarkSuite(): Promise<BenchmarkProtocolState> {
  try {
    const res = await fetch(`${API_BASE}/benchmark/run`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("runBenchmarkSuite failed:", err);
    throw err;
  }
}

export async function resetBenchmarkProtocol(): Promise<BenchmarkProtocolState> {
  try {
    const res = await fetch(`${API_BASE}/benchmark/reset`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("resetBenchmarkProtocol failed:", err);
    throw err;
  }
}

export async function fetchMetricDetail(metricId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/benchmark/metric/${metricId}`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("fetchMetricDetail failed:", err);
    return null;
  }
}

export async function testBenchmarkSample(metricId: string = "vqa_acc"): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/benchmark/test-sample?metric_id=${metricId}`, { method: "POST" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("testBenchmarkSample failed:", err);
    return null;
  }
}

// â”€â”€â”€ Indian Armed Forces Defense API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function fetchDefenseHotspots(branch?: string): Promise<any[]> {
  try {
    const url = branch ? `${API_BASE}/defense/hotspots?branch=${branch}` : `${API_BASE}/defense/hotspots`;
    const res = await fetch(url);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("fetchDefenseHotspots failed:", err);
    return [];
  }
}

export async function analyzeDefenseTarget(payload: {
  branch: string;
  hotspot_id?: string;
  lat?: number;
  lon?: number;
  tactical_query: string;
  sensor?: string;
  clearance_level?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/defense/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Defense analysis failed: ${res.statusText}`);
  return await res.json();
}

export async function fetchTacticalLayers(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/defense/tactical-layers`);
    if (!res.ok) return { layers: [] };
    return await res.json();
  } catch {
    return { layers: [] };
  }
}

// â”€â”€â”€ SAR Reader & Radar Physics API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function fetchSarPresets(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/sar-reader/presets`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error("fetchSarPresets failed:", err);
    return [];
  }
}

export async function processSarRadar(payload: {
  preset_id?: string;
  polarization?: string;
  apply_lee_filter?: boolean;
  filter_window_size?: number;
  water_threshold_db?: number;
  urban_threshold_db?: number;
  custom_center_lat?: number;
  custom_center_lon?: number;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/sar-reader/process`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`SAR processing failed: ${res.statusText}`);
  return await res.json();
}

// â”€â”€â”€ Disaster Assessment & Evacuation Routing API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function assessDisasterRisk(payload: {
  location_name?: string;
  lat: number;
  lon: number;
  disaster_type: string;
  past_image_url?: string;
  current_image_url?: string;
  weather_condition?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/traffic/disaster-assessment`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Disaster assessment failed: ${res.statusText}`);
  return await res.json();
}

export async function calculateEvacuationCorridor(payload: {
  origin_lat: number;
  origin_lon: number;
  dest_lat?: number;
  dest_lon?: number;
  disaster_type?: string;
  api_key?: string;
}): Promise<any> {
  const res = await fetch(`${API_BASE}/traffic/evacuation-corridor`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error(`Evacuation corridor calculation failed: ${res.statusText}`);
  return await res.json();
}

// â”€â”€â”€ Authentication & Security Clearance API â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

export async function loginApi(email: string, password: string): Promise<any> {
  const res = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Invalid credentials" }));
    throw new Error(err.detail || "Login failed");
  }
  return await res.json();
}

export async function registerApi(name: string, email: string, password: string, organization: string, role: string): Promise<any> {
  const res = await fetch(`${API_BASE}/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, email, password, organization, role }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Registration failed" }));
    throw new Error(err.detail || "Registration failed");
  }
  return await res.json();
}

export async function getGuestTokenApi(_clearanceLevel?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/auth/guest-token`, {method:'POST', headers:{'Content-Type':'application/json'},body:'{}'});
  if (!res.ok) throw new Error('Demo sessions are unavailable.');
  return res.json();
}
