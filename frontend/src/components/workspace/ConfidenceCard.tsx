"use client";

import React from "react";
import { ConfidenceReport } from "../../types/investigation";

interface ConfidenceCardProps {
  confidence?: ConfidenceReport | null;
  onOpenTrace?: () => void;
}

export function ConfidenceCard({ confidence, onOpenTrace }: ConfidenceCardProps) {
  if (!confidence) return null;

  const getBadgeStyle = (level: string) => {
    switch (level) {
      case "high":
        return "bg-emerald-950 text-emerald-300 border-emerald-500/50";
      case "moderate":
        return "bg-amber-950 text-amber-300 border-amber-500/50";
      default:
        return "bg-rose-950 text-rose-300 border-rose-500/50";
    }
  };

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 text-white flex flex-col gap-3">
      <div className="flex items-center justify-between pb-2 border-b border-[#1F2937]">
        <span className="text-xs uppercase font-bold tracking-wider text-gray-300">
          Empirical Confidence & Uncertainty
        </span>
        <div className="flex items-center gap-2">
          <span
            className={`text-xs font-mono uppercase font-bold px-2.5 py-0.5 rounded border ${getBadgeStyle(
              confidence.overall_confidence
            )}`}
          >
            {confidence.overall_confidence} Confidence
          </span>
          {confidence.confidence_score && (
            <span className="text-xs font-mono text-gray-400 bg-black/40 px-2 py-0.5 rounded">
              Score: {Math.round(confidence.confidence_score * 100)}%
            </span>
          )}
        </div>
      </div>

      <p className="text-xs text-gray-300 leading-relaxed bg-[#0A0F1C] p-3 rounded-lg border border-[#1F2937]">
        {confidence.explanation}
      </p>

      {/* Contributing Factors */}
      {confidence.factors.length > 0 && (
        <div className="text-xs">
          <span className="text-[11px] font-mono text-emerald-400 font-semibold uppercase block mb-1">
            Corroborating Factors:
          </span>
          <ul className="space-y-1 text-gray-300 text-[11px]">
            {confidence.factors.map((f, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-emerald-400 font-bold">+</span>
                <span>{f}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Explicit Uncertainties */}
      {confidence.uncertainties.length > 0 && (
        <div className="text-xs">
          <span className="text-[11px] font-mono text-amber-400 font-semibold uppercase block mb-1">
            Known Uncertainties:
          </span>
          <ul className="space-y-1 text-gray-300 text-[11px]">
            {confidence.uncertainties.map((u, i) => (
              <li key={i} className="flex items-start gap-1.5">
                <span className="text-amber-400 font-bold">!</span>
                <span>{u}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Audit Button */}
      {onOpenTrace && (
        <button
          onClick={onOpenTrace}
          className="mt-2 w-full py-2 bg-[#1F2937] hover:bg-gray-700 text-gray-200 rounded-lg text-xs font-medium transition-colors border border-gray-600/50 flex items-center justify-center gap-2 cursor-pointer"
        >
          <svg className="w-4 h-4 text-blue-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
          </svg>
          View Full Observable Execution Trace
        </button>
      )}
    </div>
  );
}
