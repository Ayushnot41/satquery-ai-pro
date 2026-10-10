"""Preserve existing feature views while removing false success fallbacks."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
p=root/'frontend/src/lib/api.ts'
s=p.read_text(encoding='utf-8').replace('"http://127.0.0.1:8000/api"','"/api"').replace('return { status: "online" };','return { status: "unavailable" };')
s=s.replace('if (!res.ok) throw new Error(`Investigation failed: ${res.statusText}`);', '''if (!res.ok) {const error=await res.json().catch(()=>({}));throw new Error(error.detail || `Investigation failed (${res.status})`);}''')
a=s.index('  // Fallback if zero regions found');b=s.index('  // Convert trace events',a);s=s[:a]+s[b:]
a=s.index('  if (trace.length === 0)');b=s.index('  const metrics:',a)
s=s[:a]+'''  const confidenceScore = resp.confidence?.confidence_score == null ? null : Math.round(resp.confidence.confidence_score * 100);

'''+s[b:]
s=s.replace('resp.sensor_decision?.decision || "optical_primary"','resp.sensor_decision?.decision || "Not reported"').replace('resp.vqa_result?.model_name || "google/gemini-2.5-flash"','resp.vqa_result?.model_name || "Not reported"').replace('`${(resp.total_duration_ms || 1200).toFixed(0)} ms`','resp.total_duration_ms == null ? "Not recorded" : `${resp.total_duration_ms.toFixed(0)} ms`')
s=s.replace('resp.fused_evidence?.primary_answer || resp.vqa_result?.answer || resp.answer || "Analysis completed."','resp.answer || resp.fused_evidence?.primary_answer || resp.vqa_result?.answer || "No answer was returned."')
s=s.replace('status: resp.status === "error" ? "error" : "complete",','status: resp.status === "error" ? "error" : resp.status === "complete" ? "complete" : "processing",')
s=s.replace('run_id: `RUN-${resp.investigation_id.slice(-6)}`,','run_id: resp.investigation_id,')
s=s.replace('r.change_magnitude || 0.85','r.change_magnitude ?? null').replace('r.change_magnitude || 0.88','r.change_magnitude ?? null').replace('ev.duration_ms || 25','ev.duration_ms ?? 0')
s=s.replace('r.bbox || [0.1, 0.1, 0.5, 0.5]','r.bbox').replace('      let [x1, y1, x2, y2] = r.bbox;','      if (!r.bbox || r.bbox.length !== 4) return;\n      let [x1, y1, x2, y2] = r.bbox;')
s=s.replace('  // Extract evidence regions', '''  const dimensions = resp.provenance?.image_dimensions as {width:number;height:number}|undefined;
  // Extract only grounded evidence regions with known image dimensions.''')
s=s.replace('        x1 = Math.min', '        if (!dimensions) return;\n        x1 = Math.min').replace('x1 / 512','x1 / dimensions.width').replace('x2 / 512','x2 / dimensions.width').replace('y1 / 512','y1 / dimensions.height').replace('y2 / 512','y2 / dimensions.height')
s=s.replace('Math.max(0.04, Math.min(1.0 - x1, x2 - x1))','Math.max(0, Math.min(1.0 - x1, x2 - x1))').replace('Math.max(0.04, Math.min(1.0 - y1, y2 - y1))','Math.max(0, Math.min(1.0 - y1, y2 - y1))')
a=s.index('export async function getGuestTokenApi(')
s=s[:a]+'''export async function getGuestTokenApi(_clearanceLevel?: string): Promise<any> {
  const res = await fetch(`${API_BASE}/auth/guest-token`, {method:'POST', headers:{'Content-Type':'application/json'},body:'{}'});
  if (!res.ok) throw new Error('Demo sessions are unavailable.');
  return res.json();
}
'''
p.write_text(s,encoding='utf-8')
p=root/'frontend/src/types/investigation.ts';s=p.read_text(encoding='utf-8').replace('export interface InvestigationResponse {','export interface InvestigationResponse {\n  provenance?: Record<string, unknown>;');p.write_text(s,encoding='utf-8')
# Same-origin requests support secure cookies and a single deployment URL.
for p in (root/'frontend/src').rglob('*'):
 if p.suffix in {'.tsx','.ts'}:
  s=p.read_text(encoding='utf-8');s=s.replace('http://127.0.0.1:8000/api','/api').replace('http://localhost:8000/api','/api').replace('http://127.0.0.1:8000/static','/static').replace('http://localhost:8000/static','/static');p.write_text(s,encoding='utf-8')
p=root/'frontend/src/components/screens/StaticImageComparisonView.tsx';s=p.read_text(encoding='utf-8')
for slot,default in [('A','before'),('B','after')]:
 old=f'''        try {{
          const up{slot} = await uploadImagery(slot{slot}.file);
          imageryIds.push(up{slot}.id);
        }} catch {{
          imageryIds.push("demo-construction-{default}");
        }}'''
 assert old in s
 s=s.replace(old,f'''        const up{slot} = await uploadImagery(slot{slot}.file);
        imageryIds.push(up{slot}.id);''')
s=s.replace('runInvestigation(query, imageryIds, "bi_temporal")','runInvestigation(query, imageryIds, "temporal")')
a=s.index('    } catch (err) {',s.index('  const handleRunComparison'))
b=s.index('    } finally {',a)
s=s[:a]+'''    } catch (err) {
      setAnalysisOutput({run_id:'failed-comparison',created_at:new Date().toISOString(),mode:'bi_temporal',mission_context:'Comparison',question:query,status:'error',answer:(err as Error).message,confidence:null,metrics:{},evidence:{type:'bounding_box',regions:[]},limitations:['No comparison was completed.'],trace:[],imageUrls:[slotA.previewUrl,slotB.previewUrl]});
'''+s[b:]
s=s.replace('confidence_score: analysisOutput?.confidence ?? 89','confidence_score: analysisOutput?.confidence ?? null').replace('"Changed Surface Area": "18.4%"','"Analysis": "Not completed"').replace('"Confidence Level": "89% High"','"Confidence Level": "Not measured"').replace('analysisOutput?.answer || "Comparative baseline established."','analysisOutput?.answer || "No analysis has been run."')
p.write_text(s,encoding='utf-8')
# Label original synthetic science endpoints at the response boundary.
for filename in ['defense.py','sar_reader.py','futuristic.py','benchmark.py']:
 p=root/'backend/app/api'/filename;s=p.read_text(encoding='utf-8')
 s=s.replace('from fastapi import ', 'from ..core.provenance import SimulationRoute\nfrom fastapi import ',1)
 s=s.replace('APIRouter(', 'APIRouter(route_class=SimulationRoute, ')
 p.write_text(s,encoding='utf-8')
p=root/'backend/app/main.py';s=p.read_text(encoding='utf-8').replace('from .api.auth import router as auth_router','from .api.auth import router as auth_router\nfrom .api.jobs import router as jobs_router').replace('app.include_router(auth_router, prefix="/api")','app.include_router(auth_router, prefix="/api")\napp.include_router(jobs_router, prefix="/api")').replace('path=str(request.url),','path=request.url.path,');p.write_text(s,encoding='utf-8')
p=root/'backend/app/api/investigation.py';s=p.read_text(encoding='utf-8').replace("'imagery_ids': request.imagery_ids, 'scientifically_validated': False,", "'imagery_ids': request.imagery_ids, 'scientifically_validated': False,\n        'image_dimensions': {'width': imagery_inputs[0].metadata.geo.width, 'height': imagery_inputs[0].metadata.geo.height},")
a=s.index('    # Bound in-memory cache');b=s.index('    response.provenance',a);s=s[:a]+s[b:];p.write_text(s,encoding='utf-8')
print('Client correctness and simulation provenance updated.')
