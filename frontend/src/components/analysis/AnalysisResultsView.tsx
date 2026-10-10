"use client";

import React, { useState } from "react";
import { AnalysisResult } from "../../types/investigation";
import { ALL_MOCK_RESULTS } from "../../lib/mock-results";
import { RunHeader } from "./RunHeader";
import { ImageryPanel } from "./ImageryPanel";
import { EvidenceOverlay } from "./EvidenceOverlay";
import { AnswerConfidencePanel } from "./AnswerConfidencePanel";
import { ExecutionTrace } from "./ExecutionTrace";
import { PdfReportTemplate } from "./PdfReportTemplate";

interface AnalysisResultsViewProps {
  result?: AnalysisResult | null;
  onBack?: () => void;
}

// ─── Processing / loading layout ──────────────────────────────────────────
function ProcessingState({message}: {message: string}) {
  const PIPELINE_STEPS = [
    "Input Inspection",
    "Compatibility Gate",
    "Task Classification",
    "Sensor Routing",
    "Specialist Dispatch",
    "Evidence Assembly",
    "Result Validation",
    "Confidence Assessment",
    "Audit & Trace",
  ];

  const activeStep = -1; // Individual agent completion is shown only in the returned trace.

  return (
    <div className="w-full max-w-7xl mx-auto p-6 space-y-6">
      {/* Animated status bar */}
      <div className="bg-[#090E1A] border border-blue-500/30 rounded-xl p-5 flex flex-col gap-4">
        <div className="flex items-center gap-3">
          <div className="w-4 h-4 rounded-full border-2 border-blue-400 border-t-transparent animate-spin" />
          <span className="font-mono font-bold text-blue-300 text-sm tracking-wider uppercase">
            {message}
          </span>
          <span className="ml-auto text-[10px] font-mono text-gray-500 animate-pulse">
            Pipeline stages · waiting for result
          </span>
        </div>

        {/* Mini pipeline stepper */}
        <div className="flex flex-wrap gap-2 mt-1">
          {PIPELINE_STEPS.map((step, i) => (
            <div
              key={step}
              className={`flex items-center gap-1.5 px-2.5 py-1 rounded-lg text-[10px] font-mono border transition-all ${
                i < activeStep
                  ? "bg-emerald-950/60 text-emerald-400 border-emerald-500/40"
                  : i === activeStep
                  ? "bg-blue-950/80 text-blue-300 border-blue-500/60 animate-pulse"
                  : "bg-[#111827] text-gray-600 border-[#1F2937]"
              }`}
            >
              {i < activeStep ? "✓" : i === activeStep ? "●" : `${i + 1}`}
              <span className="truncate max-w-[80px]">{step}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Skeleton layout */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">
        <div className="lg:col-span-1">
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl h-80 animate-pulse" />
        </div>
        <div className="lg:col-span-1">
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl h-80 animate-pulse" />
        </div>
        <div className="lg:col-span-1 flex flex-col gap-4">
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl h-36 animate-pulse" />
          <div className="bg-[#111827] border border-[#1F2937] rounded-xl h-36 animate-pulse" />
        </div>
      </div>
    </div>
  );
}

// ─── Error state ───────────────────────────────────────────────────────────
function ErrorState({ onBack, onRetry, message }: { onBack?: () => void; onRetry?: () => void; message: string }) {
  return (
    <div className="w-full max-w-7xl mx-auto p-6 flex flex-col items-center justify-center min-h-96 gap-6">
      <div className="bg-[#111827] border border-rose-500/50 rounded-xl p-8 flex flex-col items-center gap-4 max-w-md w-full text-center">
        <div className="w-14 h-14 rounded-xl bg-rose-950/60 border border-rose-500/50 flex items-center justify-center">
          <svg className="w-7 h-7 text-rose-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <div>
          <h2 className="text-base font-bold text-rose-300 font-mono uppercase tracking-wider">
            Pipeline Error
          </h2>
          <p className="text-sm text-gray-400 mt-2 leading-relaxed">
            {message}
          </p>
        </div>
        <div className="flex gap-3">
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-5 py-2 bg-gradient-to-r from-blue-700 to-blue-600 hover:from-blue-600 hover:to-blue-500 text-white text-sm font-semibold rounded-lg border border-blue-500/50 transition-all cursor-pointer flex items-center gap-2"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              Retry Pipeline
            </button>
          )}
          {onBack && (
            <button
              onClick={onBack}
              className="px-5 py-2 bg-[#1F2937] hover:bg-gray-700 text-gray-200 text-sm font-semibold rounded-lg border border-gray-600 transition-all cursor-pointer"
            >
              Back
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Mock mode switcher (for demo) ────────────────────────────────────────
function MockModeSwitcher({
  activeIdx,
  onChange,
}: {
  activeIdx: number;
  onChange: (i: number) => void;
}) {
  const labels = [
    { label: "Single Image", accent: "cyan" },
    { label: "Bi-Temporal", accent: "blue" },
    { label: "Optical + SAR", accent: "purple" },
  ];

  return (
    <div className="flex items-center gap-2 bg-[#111827] p-1 rounded-lg border border-[#1F2937]">
      <span className="text-[10px] font-mono text-gray-500 ml-1.5 uppercase shrink-0">
        Demo Mode:
      </span>
      {labels.map((l, i) => (
        <button
          key={i}
          onClick={() => onChange(i)}
          className={`px-2.5 py-1 rounded text-[10px] font-mono font-bold uppercase tracking-wider transition-all cursor-pointer border ${
            activeIdx === i
              ? l.accent === "cyan"
                ? "bg-cyan-950 text-cyan-300 border-cyan-500/60"
                : l.accent === "blue"
                ? "bg-blue-950 text-blue-300 border-blue-500/60"
                : "bg-purple-950 text-purple-300 border-purple-500/60"
              : "bg-transparent text-gray-500 border-transparent hover:border-gray-700"
          }`}
        >
          {l.label}
        </button>
      ))}
    </div>
  );
}

// ─── Main Results View ────────────────────────────────────────────────────
export function AnalysisResultsView({ result: propResult, onBack }: AnalysisResultsViewProps) {
  // Mock switcher for demo
  const [mockIdx, setMockIdx] = useState(0);
  const result = propResult ?? ALL_MOCK_RESULTS[mockIdx];
  const workspaceRef = React.useRef<HTMLDivElement>(null);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState('');

  const exportToPDF = async () => {
    if (!workspaceRef.current || exporting) return;
    setExporting(true);
    setExportError('');
    try {
      const [{default: html2canvas}, {default: jsPDF}] = await Promise.all([import('html2canvas'), import('jspdf')]);
      const canvas = await html2canvas(workspaceRef.current, {
        scale: 2,
        useCORS: true,
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({
        orientation: "portrait",
        unit: "mm",
        format: "a4",
      });

      const pdfWidth = pdf.internal.pageSize.getWidth();
      const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
      
      const pageHeight = pdf.internal.pageSize.getHeight();
      for (let offset = 0; offset < pdfHeight; offset += pageHeight) {
        if (offset > 0) pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, -offset, pdfWidth, pdfHeight);
      }
      pdf.save(`Satquery-Analysis-Report-${Date.now()}.pdf`);
    } catch (err) {
      setExportError('The report could not be exported. Please try again.');
    } finally { setExporting(false); }
  };

  if (result.status === "processing") {
    return <ProcessingState message={result.answer} />;
  }

  if (result.status === "error") {
    return <ErrorState onBack={onBack} message={result.answer} />;
  }

  const totalMs = result.total_duration_ms ?? result.trace.reduce((end, s) => Math.max(end, s.timestamp_offset_ms || 0), 0);

  // SAR metrics for the evidence overlay physics chip
  const sarMetrics =
    result.mode === "optical_sar"
      ? {
          "σ⁰ (VV)": result.metrics["Water Backscatter (VV)"] ?? result.metrics["Water σ⁰ (VV)"] ?? "Not reported",
          "VH/VV Ratio": result.metrics["VH/VV Ratio"] ?? "Not reported",
          "Lee Filter": result.metrics["Lee Filter Window"] ?? "Not reported",
          "Cloud Cover": result.metrics["Optical Cloud Cover"] ?? "Not reported",
        }
      : undefined;

  return (
    <>
      <PdfReportTemplate ref={workspaceRef} result={result} sarMetrics={sarMetrics as Record<string, string | number>} />
      
      <div className="w-full max-w-7xl mx-auto p-6 space-y-5 text-white select-none relative z-10">
        {/* ─── Export & Demo switcher ─────────────────────────────── */}
      <div className="flex items-center justify-end gap-3">
        {exportError && <p role="alert" className="text-sm text-rose-300">{exportError}</p>}
        <button
            onClick={exportToPDF}
            disabled={exporting}
            className="px-4 py-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white font-bold text-[10px] rounded border border-emerald-400/30 transition-all flex items-center gap-2 font-mono uppercase tracking-wider cursor-pointer"
          >
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
              <line x1="16" y1="13" x2="8" y2="13"></line>
              <line x1="16" y1="17" x2="8" y2="17"></line>
              <polyline points="10 9 9 9 8 9"></polyline>
            </svg>
            {exporting ? 'Preparing PDF…' : 'Export PDF Report'}
          </button>
        {!propResult && (
          <MockModeSwitcher activeIdx={mockIdx} onChange={setMockIdx} />
        )}
      </div>

      {/* ─── ZONE 1: Run Header ─────────────────────────────── */}
      <RunHeader result={result} onBack={onBack} />

      {/* ─── ZONES 2-4: Three-column grid ───────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* LEFT — Imagery Panel */}
        <div className="lg:col-span-1">
          <ImageryPanel
            mode={result.mode}
            imageUrls={result.imageUrls}
          />
        </div>

        {/* CENTER — Evidence Overlay */}
        <div className="lg:col-span-1">
          <EvidenceOverlay
            evidence={result.evidence}
            mode={result.mode}
            confidence={result.confidence}
            sarMetrics={sarMetrics as Record<string, string | number> | undefined}
            imageUrls={result.imageUrls}
          />
        </div>

        {/* RIGHT — Answer + Confidence */}
        <div className="lg:col-span-1">
          <AnswerConfidencePanel result={result} />
        </div>
      </div>

      {/* ─── ZONE 5: Execution Trace ─────────────────────────── */}
      <ExecutionTrace
        steps={result.trace}
        totalDurationMs={totalMs}
        defaultExpanded={true}
      />

      {/* ─── Footer strip ────────────────────────────────────── */}
      <div className="flex flex-wrap items-center justify-between gap-3 text-[10px] font-mono text-gray-600 px-1">
        <span>
          BHUVISION SIH26167 // Results Record — {result.run_id}
        </span>
        <div className="flex items-center gap-4">
          <span>9-agent architecture</span>
          <span>|</span>
          <span>Independent review required</span>
          <span>|</span>
          <span className="text-emerald-500">Execution trace available</span>
        </div>
      </div>
    </div>
    </>
  );
}
