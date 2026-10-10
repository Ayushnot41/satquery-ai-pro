"""One-time browser findings repair. Source files stay in this project."""
from pathlib import Path
import ast
root = Path(__file__).resolve().parents[1]
def edit(name, changes):
    path = root / name
    text = path.read_text(encoding='utf-8')
    for old, new in changes:
        if old not in text:
            raise RuntimeError(f'Missing edit context in {name}: {old[:70]}')
        text = text.replace(old, new)
    path.write_text(text, encoding='utf-8')

edit('backend/app/agents/visual_grounding.py', [
    ('# Determine thematic tag from query context', '# Saliency indicates contrast, not semantic class or calibrated confidence.'),
])
p = root / 'backend/app/agents/visual_grounding.py'
t = p.read_text(encoding='utf-8')
start = t.index('            c_lower = context.lower()')
end = t.index('            # Sort components', start)
t = t[:start] + '            tag_prefix = "Salient region (unclassified)"\n\n' + t[end:]
start = t.index('            components = []')
end = t.index('            for idx, (area, comp)', start)
t = t[:start] + '''            counts = np.bincount(labeled.ravel())
            candidate_ids = np.argsort(counts[1:])[::-1] + 1
            components = [(int(counts[i]), labeled == i) for i in candidate_ids[:5] if counts[i] > 100]

''' + t[end:]
start = t.index('            # Fallback if no clean components')
end = t.index('            return regions', start)
t = t[:start] + t[end:]
t = t.replace('float(xs.max()) / w', 'float(xs.max() + 1) / w').replace('float(ys.max()) / h', 'float(ys.max() + 1) / h')
t = t.replace('change_type=f"{tag_prefix} {chr(65 + idx)}",', 'change_type=f"{tag_prefix} {chr(65 + idx)}",\n                    coordinate_space="normalized",')
t = t.replace('round(min(0.95, 0.75 + (area / (h * w)) * 2), 2)', 'round(area / (h * w), 4)')
p.write_text(t, encoding='utf-8')

edit('frontend/src/types/investigation.ts', [
    ('export interface ChangeRegion {', "export interface ChangeRegion {\n  coordinate_space?: 'pixel' | 'normalized';"),
    ('export interface VisualOverlay {', "export interface VisualOverlay {\n  coordinate_space?: 'pixel' | 'normalized';"),
])
edit('frontend/src/lib/api.ts', [
    ('if (x1 > 1.0 || x2 > 1.0 || y1 > 1.0 || y2 > 1.0) {', "if (r.coordinate_space === 'pixel' || (!r.coordinate_space && (x1 > 1 || x2 > 1 || y1 > 1 || y2 > 1))) {"),
    ('score: r.change_magnitude ?? null,', "score: r.change_type?.startsWith('Salient region') ? null : r.change_magnitude ?? null,"),
    ('timestamp_offset_ms: i * 20,', 'timestamp_offset_ms: Math.max(0, Date.parse(ev.timestamp) - Date.parse(resp.trace?.started_at || ev.timestamp)),'),
])
edit('frontend/src/components/analysis/PdfReportTemplate.tsx', [
    ('ref={ref}', 'ref={ref}\n        aria-hidden="true"'),
    ('ISRO SIH26167 • TEAM BANKAI', 'SATQUERY AI PRO · INVESTIGATION REPORT'),
    ('{result.confidence}%', "{result.confidence == null ? 'N/A' : `${result.confidence}%`}"),
    ('Empirically Calibrated', 'Reported confidence'),
    ('All agent consensus thresholds met.', 'Not independently calibrated. Review limitations.'),
    ('{/* Mission Context & Question */}', '''<p style={{padding: '12px', backgroundColor:'#fff7ed', color:'#9a3412', fontSize:'12px'}}>
          {result.provenance?.mode === 'simulation' || result.answer.includes('SIMULATION') ? 'SIMULATION — illustrative sample.' : 'MODEL INTERPRETATION — independent review required.'} Scientific accuracy has not been validated.
        </p>
        {/* Mission Context & Question */}'''),
    ('Automated multi-agent generation • Do not distribute without classification review', 'SATQUERY AI PRO · MODEL-GENERATED REPORT · REVIEW BEFORE USE'),
])
edit('frontend/src/components/analysis/AnalysisResultsView.tsx', [
    ('function ProcessingState() {', 'function ProcessingState({message}: {message: string}) {'),
    ('const [activeStep] = useState(4); // Simulate mid-pipeline', 'const activeStep = -1; // Individual agent completion is shown only in the returned trace.'),
    ('SATQUERY PIPELINE EXECUTING', '{message}'),
    ('Agent council processing...', 'Pipeline stages · waiting for result'),
    ('function ErrorState({ onBack, onRetry }: { onBack?: () => void; onRetry?: () => void }) {', 'function ErrorState({ onBack, onRetry, message }: { onBack?: () => void; onRetry?: () => void; message: string }) {'),
    ('The 9-agent investigation pipeline encountered an unrecoverable error. The execution trace has been committed for audit.', '{message}'),
    ('return <ProcessingState />;', 'return <ProcessingState message={result.answer} />;'),
    ('return <ErrorState onBack={onBack} />;', 'return <ErrorState onBack={onBack} message={result.answer} />;'),
    ('const totalMs = result.trace.reduce((acc, s) => acc + s.duration_ms, 0);', 'const totalMs = result.trace.reduce((end, s) => Math.max(end, (s.timestamp_offset_ms || 0) + s.duration_ms), 0);'),
    ('pdf.addImage(imgData, "PNG", 0, 0, pdfWidth, pdfHeight);', '''const pageHeight = pdf.internal.pageSize.getHeight();
      for (let offset = 0; offset < pdfHeight; offset += pageHeight) {
        if (offset > 0) pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, -offset, pdfWidth, pdfHeight);
      }'''),
    ('ISRO-SatQuery-Intelligence-Report-', 'Satquery-Analysis-Report-'),
    ('?? "−22.4 dB"', '?? "Not reported"'), ('?? "0.31"', '?? "Not reported"'),
    ('?? "7×7 px"', '?? "Not reported"'), ('?? "100%"', '?? "Not reported"'),
    ('9 Agents Operational', '9-agent architecture'),
    ('Zero-Hallucination Protocol', 'Independent review required'),
    ('Audit Committed', 'Execution trace available'),
])
edit('frontend/src/components/analysis/AnswerConfidencePanel.tsx', [
    ('Pending', 'Not reported'), ('"PENDING"', '"NOT REPORTED"'),
    ('Empirical Calibration', 'Reported confidence'),
    ('All agent consensus thresholds met', 'High reported score; independent review required'),
    ('Score wired to Agent 8 empirical calibration. Never fabricated.', 'Model confidence is not a calibrated probability of correctness.'),
])
edit('frontend/src/components/analysis/ExecutionTrace.tsx', [
    ('VERIFIED:', 'RECORDED:'), ('SIH26167 Auditable Compliance Record', 'Recorded pipeline events'),
])
edit('frontend/src/components/analysis/ImageryPanel.tsx', [
    ('MGRS · 44RKQ 6139 7209', 'Image preview · coordinates not shown'),
    ('CARTOSAT-3', 'Not reported'), ('0.28 m/px', 'Not reported'), ('PAN+4xVNIR', 'Not reported'),
    ('2026-07-12', 'Not reported'), ('2026-07-19', 'Not reported'),
    ('SENTINEL-2 MSI', 'Not reported'), ('SENTINEL-1 C-BAND', 'Not reported'),
    ('SENTINEL-2', 'Not reported'), ('7 days', 'Not reported'),
    ('σ⁰(VV) = −22.4 dB', 'Backscatter value not reported'),
    ('100 / (wipePos / 100)', '100 / (Math.max(wipePos, 0.01) / 100)'),
    ('onMouseDown={onMouseDown} onTouchStart={onTouchStart}>', '''onMouseDown={onMouseDown} onTouchStart={onTouchStart}
      role="slider" tabIndex={0} aria-label="Before and after image comparison"
      aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(wipePos)}
      onKeyDown={event=>{if(['ArrowLeft','ArrowRight','Home','End'].includes(event.key)){event.preventDefault();setWipePos(value=>event.key==='Home'?0:event.key==='End'?100:Math.max(0,Math.min(100,value+(event.key==='ArrowRight'?5:-5))));}}}>'''),
])
print('Applied browser findings to source.')
