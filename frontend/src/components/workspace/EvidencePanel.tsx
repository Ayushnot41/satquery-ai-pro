"use client";

import React from "react";
import { FusedEvidence, SensorDecision } from "../../types/investigation";

interface EvidencePanelProps {
  fusedEvidence?: FusedEvidence | null;
  sensorDecision?: SensorDecision | null;
  answer?: string;
}

export function EvidencePanel({ fusedEvidence, sensorDecision, answer }: EvidencePanelProps) {
  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-5 text-white flex flex-col gap-4">
      {/* Primary Investigation Finding */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-blue-400">
            Synthesis Finding
          </span>
          {fusedEvidence && (
            <span
              className={`text-[10px] font-mono px-2 py-0.5 rounded uppercase font-bold border ${
                fusedEvidence.evidence_strength === "high"
                  ? "bg-emerald-950 text-emerald-300 border-emerald-500/40"
                  : "bg-amber-950 text-amber-300 border-amber-500/40"
              }`}
            >
              Strength: {fusedEvidence.evidence_strength}
            </span>
          )}
        </div>
        <p className="text-sm font-medium text-gray-100 leading-relaxed bg-[#0A0F1C] p-3.5 rounded-lg border border-[#1F2937]">
          {answer || "Submit an Earth inquiry or select a scenario to initiate investigation."}
        </p>
      </div>

      {/* Sensor Pathway Justification */}
      {sensorDecision && (
        <div className="bg-[#0A0F1C]/80 border border-[#1F2937] p-3 rounded-lg text-xs">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-semibold text-gray-300 uppercase font-mono text-[10px]">
              Sensor Pathway:
            </span>
            <span className="text-cyan-400 font-mono text-[11px] uppercase font-bold">
              {sensorDecision.decision.replace("_", " ")}
            </span>
          </div>
          <p className="text-gray-400 text-xs leading-relaxed">{sensorDecision.reason}</p>
        </div>
      )}

      {/* Corroborating Evidence Items */}
      {fusedEvidence && fusedEvidence.evidence_items.length > 0 && (
        <div>
          <span className="text-[11px] font-mono uppercase tracking-wider font-semibold text-gray-400 block mb-2">
            Corroborating Evidence Sources ({fusedEvidence.evidence_items.length})
          </span>
          <div className="flex flex-col gap-2">
            {fusedEvidence.evidence_items.map((item, idx) => (
              <div
                key={idx}
                className="bg-[#0A0F1C] border border-[#1F2937] p-2.5 rounded-lg flex items-start gap-2.5 text-xs"
              >
                <div className="w-5 h-5 rounded bg-blue-900/60 border border-blue-500/30 text-blue-300 flex items-center justify-center font-mono text-[10px] font-bold shrink-0">
                  {item.agent_id}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-0.5">
                    <span className="font-semibold text-gray-200 text-[11px]">{item.source_agent}</span>
                    <span className="text-[10px] font-mono text-gray-500 uppercase">{item.evidence_type}</span>
                  </div>
                  <p className="text-gray-300 text-[11px] leading-normal">{item.content}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Contradiction Warning if any */}
      {fusedEvidence && fusedEvidence.contradictions.length > 0 && (
        <div className="bg-amber-950/40 border border-amber-500/40 p-3 rounded-lg text-xs text-amber-200">
          <span className="font-bold block mb-1">Evidence Discrepancy Flagged:</span>
          <ul className="list-disc list-inside space-y-0.5 text-[11px]">
            {fusedEvidence.contradictions.map((c, i) => (
              <li key={i}>{c}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
