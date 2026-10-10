"use client";

import React from "react";
import { ExecutionTrace } from "../../types/investigation";

interface AuditTraceModalProps {
  trace?: ExecutionTrace | null;
  isOpen: boolean;
  onClose: () => void;
}

export function AuditTraceModal({ trace, isOpen, onClose }: AuditTraceModalProps) {
  if (!isOpen || !trace) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 select-none">
      <div className="bg-[#0A0F1C] border border-[#1F2937] rounded-2xl w-full max-w-3xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden text-white">
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-[#1F2937] bg-[#111827]">
          <div>
            <h2 className="text-base font-bold tracking-tight text-white flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-blue-500" />
              Observable Execution Trace & Audit Log
            </h2>
            <p className="text-xs text-gray-400 mt-0.5 font-mono">
              Investigation ID: {trace.investigation_id} | Total Duration: {trace.total_duration_ms || 0}ms
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-4 font-mono text-xs">
          {/* Metadata Grid */}
          <div className="grid grid-cols-3 gap-3 bg-[#111827] p-3 rounded-xl border border-[#1F2937]">
            <div>
              <span className="text-[10px] uppercase text-gray-500 block">Agents Invoked</span>
              <span className="text-blue-400 font-bold text-xs">{trace.agents_invoked.length} Agents</span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-gray-500 block">Models Used</span>
              <span className="text-emerald-400 font-bold text-xs truncate block">
                {trace.models_used[0] || "None"}
              </span>
            </div>
            <div>
              <span className="text-[10px] uppercase text-gray-500 block">Warnings / Fallbacks</span>
              <span className="text-amber-400 font-bold text-xs">
                {trace.warnings.length} Warn / {trace.fallbacks_used.length} Fallbacks
              </span>
            </div>
          </div>

          {/* Timeline Events */}
          <div className="space-y-2">
            <span className="text-[11px] text-gray-400 uppercase tracking-wider block font-sans font-bold">
              Sequential Event Trace
            </span>
            <div className="space-y-2 border-l border-gray-800 ml-2 pl-4">
              {trace.events.map((evt, idx) => (
                <div key={idx} className="relative group">
                  <span className="absolute -left-[21px] top-1.5 w-2 h-2 rounded-full bg-blue-500 group-hover:scale-125 transition-transform" />
                  <div className="bg-[#111827] p-2.5 rounded-lg border border-[#1F2937] hover:border-gray-600 transition-colors">
                    <div className="flex items-center justify-between text-[10px] text-gray-400 mb-1">
                      <span className="font-bold text-blue-400">
                        [{evt.agent_id}] {evt.agent_name}
                      </span>
                      <span>{new Date(evt.timestamp).toLocaleTimeString()}</span>
                    </div>
                    <div className="text-gray-200 text-xs">{evt.message}</div>
                    {evt.duration_ms && (
                      <span className="text-[10px] text-gray-500 mt-1 block">
                        Duration: {Math.round(evt.duration_ms)}ms
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-[#1F2937] bg-[#111827] flex items-center justify-between text-xs text-gray-400 font-sans">
          <span>Official SIH26167 Auditable Compliance Record</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-[#3B82F6] hover:bg-blue-600 text-white rounded-lg font-medium transition-colors cursor-pointer"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  );
}
