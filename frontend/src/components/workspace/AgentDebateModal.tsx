"use client";

import React from "react";
import { MessageSquare, X, ShieldCheck, Cpu, ArrowRight } from "lucide-react";

interface AgentDebateModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AgentDebateModal({ isOpen, onClose }: AgentDebateModalProps) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-md">
      <div className="bg-[#0B1120] border border-[#1F2937] rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-4 text-gray-200 font-sans">
        
        <div className="flex items-center justify-between pb-3 border-b border-[#1F2937]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-indigo-950 border border-indigo-500/40 flex items-center justify-center text-indigo-300">
              <MessageSquare className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono uppercase text-white tracking-wider">
                Graph-of-Thought (GoT) Agent Debate Protocol
              </h3>
              <p className="text-[10px] text-gray-400 font-mono">
                Autonomous Cross-Sensor Deliberation & Empirical Truth Discovery
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white p-1 rounded-lg hover:bg-gray-800 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        <div className="flex items-center justify-between p-2.5 rounded-xl bg-[#030611] border border-emerald-500/30 text-xs font-mono">
          <div className="flex items-center gap-2 text-emerald-300 font-bold">
            <ShieldCheck className="w-4 h-4 text-emerald-400" />
            <span>Multi-Agent Consensus Reached</span>
          </div>
          <span className="text-cyan-400">Calibrated Confidence: 94.2%</span>
        </div>

        {/* Live Debate Transcript Cards */}
        <div className="space-y-3 font-mono text-xs max-h-80 overflow-y-auto pr-1">
          <div className="p-3.5 bg-[#030611] border border-blue-500/40 rounded-xl">
            <div className="flex items-center justify-between text-blue-400 font-bold mb-1">
              <span>[AGENT 4: OPTICAL RS-VQA]</span>
              <span className="text-gray-500">T + 0.12s</span>
            </div>
            <p className="text-gray-300 font-sans leading-relaxed text-[12px]">
              &ldquo;Visual scene inspection flags high pixel obscurity over target AOI. Cloud cover exceeds 72%. Optical RGB spectrum cannot verify ground inundation without risking false alarm.&rdquo;
            </p>
          </div>

          <div className="p-3.5 bg-[#030611] border border-purple-500/40 rounded-xl">
            <div className="flex items-center justify-between text-purple-400 font-bold mb-1">
              <span>[AGENT 5: SAR CHANGE DETECTION ENGINE]</span>
              <span className="text-gray-500">T + 0.38s</span>
            </div>
            <p className="text-gray-300 font-sans leading-relaxed text-[12px]">
              &ldquo;Counter-argument submitted. Sentinel-1 C-Band (5.405 GHz) microwave pulses penetrate cloud ceiling unattenuated. Specular backscatter calibrated at -18.2 dB confirms standing water over 420 hectares in eastern floodplain.&rdquo;
            </p>
          </div>

          <div className="p-3.5 bg-[#030611] border border-emerald-500/40 rounded-xl bg-gradient-to-r from-emerald-950/20 to-transparent">
            <div className="flex items-center justify-between text-emerald-400 font-bold mb-1">
              <span>[AGENT 7: EVIDENCE FUSION RESOLUTION]</span>
              <span className="text-gray-500">T + 0.98s</span>
            </div>
            <p className="text-gray-200 font-sans leading-relaxed text-[12px] font-medium">
              &ldquo;Debate resolved in favor of SAR microwave evidence. Optical uncertainty overridden. Flood boundary polygon committed to GIS export with 94.2% verified empirical confidence.&rdquo;
            </p>
          </div>
        </div>

        <div className="pt-3 border-t border-[#1F2937] flex items-center justify-between text-xs font-mono text-gray-400">
          <span>Latency overhead: 48ms</span>
          <button
            onClick={onClose}
            className="px-4 py-1.5 bg-gray-800 hover:bg-gray-700 text-white rounded-lg transition-colors"
          >
            Close Inspector
          </button>
        </div>

      </div>
    </div>
  );
}
