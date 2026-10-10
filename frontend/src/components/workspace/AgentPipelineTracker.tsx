"use client";

import React from "react";
import { InvestigationStatus, ExecutionTrace } from "../../types/investigation";

interface AgentPipelineTrackerProps {
  status: InvestigationStatus;
  trace?: ExecutionTrace | null;
}

const AGENTS = [
  { id: 1, name: "Query Planner", role: "Investigation Intent", code: "PLAN" },
  { id: 2, name: "Input Validation", role: "CRS, Bounds & Alignment", code: "VAL" },
  { id: 3, name: "Sensor Router", role: "Optical / SAR Dispatch", code: "ROUT" },
  { id: 4, name: "Remote-Sensing VQA", role: "Vision-Language Answering", code: "VQA" },
  { id: 5, name: "Bi-Temporal Change", role: "Pixel & Morphology Differencing", code: "DIFF" },
  { id: 6, name: "Visual Grounding", role: "Bounding Polygon Extraction", code: "GRND" },
  { id: 7, name: "Evidence Fusion", role: "Multi-Source Synthesis", code: "FUSE" },
  { id: 8, name: "Confidence & Uncertainty", role: "Empirical Reliability Assessment", code: "CONF" },
  { id: 9, name: "Audit & Trace", role: "Observable Execution Record", code: "TRAC" },
];

export function AgentPipelineTracker({ status, trace }: AgentPipelineTrackerProps) {
  const getAgentStatus = (agentId: number, agentName: string) => {
    if (status === "complete") return "completed";
    if (status === "error") return "error";

    // Check if agent is recorded in trace
    const invoked = trace?.agents_invoked || [];
    if (invoked.includes(agentName)) return "completed";

    // Map high-level status to active agent
    if (status === "planning" && agentId === 1) return "active";
    if (status === "validating" && agentId === 2) return "active";
    if (status === "routing" && agentId === 3) return "active";
    if (status === "analyzing" && (agentId === 4 || agentId === 5)) return "active";
    if (status === "grounding" && agentId === 6) return "active";
    if (status === "fusing" && agentId === 7) return "active";
    if (status === "assessing" && agentId === 8) return "active";

    return "idle";
  };

  return (
    <div className="bg-[#111827] border border-[#1F2937] rounded-xl p-4 text-white">
      <div className="flex items-center justify-between pb-3 border-b border-[#1F2937]">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-blue-500 animate-pulse" />
          <h3 className="text-xs uppercase font-bold tracking-wider text-gray-300">
            9-Agent Controlled Investigation Graph
          </h3>
        </div>
        <span className="text-[11px] font-mono text-gray-400">
          State: <span className="text-blue-400 uppercase font-semibold">{status}</span>
        </span>
      </div>

      <div className="grid grid-cols-3 gap-2.5 mt-3">
        {AGENTS.map((agent) => {
          const agentState = getAgentStatus(agent.id, agent.name);

          let badgeColor = "bg-gray-800/80 text-gray-400 border-gray-700/50";
          let statusText = "STANDBY";

          if (agentState === "active") {
            badgeColor = "bg-blue-950 text-blue-300 border-blue-500/80 ring-1 ring-blue-500/50";
            statusText = "EXECUTING";
          } else if (agentState === "completed") {
            badgeColor = "bg-emerald-950/60 text-emerald-300 border-emerald-500/40";
            statusText = "VERIFIED";
          }

          return (
            <div
              key={agent.id}
              className={`p-2.5 rounded-lg border transition-all duration-200 ${badgeColor}`}
            >
              <div className="flex items-center justify-between mb-1">
                <span className="font-mono text-[10px] font-bold opacity-70">
                  A{agent.id} // {agent.code}
                </span>
                <span className="text-[9px] font-mono uppercase px-1.5 py-0.2 rounded bg-black/40">
                  {statusText}
                </span>
              </div>
              <div className="text-xs font-semibold text-white truncate">{agent.name}</div>
              <div className="text-[11px] text-gray-400 truncate mt-0.5">{agent.role}</div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
