"use client";

import React from "react";

interface MissionHomeProps {
  onStartInvestigation: (scenarioId?: string) => void;
  onOpenMissionView: () => void;
}

export function MissionHome({ onStartInvestigation, onOpenMissionView }: MissionHomeProps) {
  const scenarios = [
    {
      id: "scenario-construction-01",
      title: "Urban Construction Expansion",
      tag: "Bi-Temporal Optical",
      question: "Where has construction increased between these two dates?",
      type: "construction",
      color: "from-blue-600/20 to-indigo-600/20 border-blue-500/30",
    },
    {
      id: "scenario-flood-01",
      title: "Monsoon Inundation Delineation",
      tag: "Sentinel-1 SAR + Optical",
      question: "Where did flooding expand?",
      type: "flood",
      color: "from-cyan-600/20 to-blue-600/20 border-cyan-500/30",
    },
    {
      id: "scenario-vegetation-01",
      title: "Forest Canopy & Buffer Depletion",
      tag: "Multispectral NDVI",
      question: "Where has vegetation changed?",
      type: "vegetation",
      color: "from-emerald-600/20 to-teal-600/20 border-emerald-500/30",
    },
  ];

  return (
    <div className="w-full max-w-6xl mx-auto py-12 px-6 flex flex-col items-center text-center select-none">
      {/* Credential Badges */}
      <div className="flex items-center gap-2 mb-6">
        <span className="px-3 py-1 bg-blue-950/80 border border-blue-500/40 rounded-full text-blue-300 text-xs font-mono font-semibold tracking-wider">
          SMART INDIA HACKATHON // SIH26167
        </span>
        <span className="px-3 py-1 bg-amber-950/80 border border-amber-500/40 rounded-full text-amber-300 text-xs font-mono font-semibold tracking-wider">
          ORGANIZATION: ISRO
        </span>
      </div>

      {/* Main Tagline & Hero */}
      <h1 className="text-4xl sm:text-6xl font-extrabold text-white tracking-tight leading-tight max-w-4xl font-sans">
        Ask the Earth. <br />
        <span className="bg-gradient-to-r from-blue-400 via-cyan-300 to-emerald-400 bg-clip-text text-transparent">
          AI decides how to investigate it.
        </span>
      </h1>

      <p className="mt-6 text-base sm:text-lg text-gray-300 max-w-2xl font-light leading-relaxed">
        Not another satellite chatbot. A controlled 9-agent investigation system that validates imagery,
        routes between Optical and SAR radar, detects changes, highlights visual evidence, and reports empirical uncertainty.
      </p>

      {/* Action Buttons */}
      <div className="mt-8 flex items-center gap-4">
        <button
          onClick={() => onStartInvestigation()}
          className="px-6 py-3.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-semibold text-sm rounded-xl shadow-lg shadow-blue-500/25 border border-blue-400/30 transition-all cursor-pointer flex items-center gap-2"
        >
          <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <polygon points="5 3 19 12 5 21 5 3" />
          </svg>
          Start Investigation
        </button>
        <button
          onClick={onOpenMissionView}
          className="px-6 py-3.5 bg-[#111827] hover:bg-gray-800 text-gray-200 font-semibold text-sm rounded-xl border border-gray-700 transition-all cursor-pointer flex items-center gap-2"
        >
          <svg className="w-4 h-4 text-cyan-400" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <path d="m4.93 4.93 4.24 4.24" />
            <path d="m14.83 9.17 4.24-4.24" />
            <path d="m14.83 14.83 4.24 4.24" />
            <path d="m9.17 14.83-4.24 4.24" />
          </svg>
          God&apos;s Eye View (Spatial 3D)
        </button>
      </div>

      {/* Curated Judge Scenarios */}
      <div className="mt-16 w-full text-left">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xs uppercase font-bold tracking-wider text-gray-400 font-mono">
            Live Demo Scenarios // 2-3 Minute Judge Workflow
          </h2>
          <span className="text-[11px] text-gray-500 font-mono">Click to launch with pre-calibrated imagery</span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {scenarios.map((sc) => (
            <div
              key={sc.id}
              onClick={() => onStartInvestigation(sc.id)}
              className={`p-5 rounded-xl border bg-gradient-to-b ${sc.color} hover:border-gray-500 transition-all cursor-pointer group`}
            >
              <div className="flex items-center justify-between mb-3">
                <div className="w-8 h-8 rounded-lg bg-black/50 border border-white/10 flex items-center justify-center text-cyan-300">
                  {sc.type === "construction" ? (
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <rect x="2" y="7" width="20" height="14" rx="2" />
                      <path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
                    </svg>
                  ) : sc.type === "flood" ? (
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M2 12h20" />
                      <path d="M20 12v8H4v-8" />
                      <path d="m4 8 16-4" />
                      <path d="m4 4 16 4" />
                    </svg>
                  ) : (
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2v20" />
                      <path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6" />
                    </svg>
                  )}
                </div>
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-black/50 text-gray-300 uppercase font-semibold">
                  {sc.tag}
                </span>
              </div>
              <h3 className="text-sm font-bold text-white group-hover:text-cyan-300 transition-colors">
                {sc.title}
              </h3>
              <p className="text-xs text-gray-300 mt-2 italic font-mono">
                &ldquo;{sc.question}&rdquo;
              </p>
              <div className="mt-4 flex items-center gap-1.5 text-xs font-semibold text-blue-400 group-hover:translate-x-1 transition-transform">
                <span>Run Agent Investigation</span>
                <span>&rarr;</span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Core Architectural Pillars */}
      <div className="mt-16 grid grid-cols-1 md:grid-cols-4 gap-4 text-left w-full">
        <div className="bg-[#111827]/80 p-4 rounded-xl border border-[#1F2937]">
          <span className="text-xs font-mono text-blue-400 font-bold block mb-1">01 // NINE SPECIALISTS</span>
          <p className="text-xs text-gray-300 leading-normal">
            Controlled graph with explicit typed contracts. No single hallucinating chatbot.
          </p>
        </div>
        <div className="bg-[#111827]/80 p-4 rounded-xl border border-[#1F2937]">
          <span className="text-xs font-mono text-purple-400 font-bold block mb-1">02 // TRUE SAR RADAR</span>
          <p className="text-xs text-gray-300 leading-normal">
            Lee speckle filtering and calibrated backscatter dB for all-weather flood detection.
          </p>
        </div>
        <div className="bg-[#111827]/80 p-4 rounded-xl border border-[#1F2937]">
          <span className="text-xs font-mono text-emerald-400 font-bold block mb-1">03 // VISUAL EVIDENCE</span>
          <p className="text-xs text-gray-300 leading-normal">
            Every answer grounds back to pixel coordinates and highlighted bounding polygons.
          </p>
        </div>
        <div className="bg-[#111827]/80 p-4 rounded-xl border border-[#1F2937]">
          <span className="text-xs font-mono text-amber-400 font-bold block mb-1">04 // AUDITABLE TRACE</span>
          <p className="text-xs text-gray-300 leading-normal">
            Observable timeline with millisecond latency, model versions, and honest uncertainty.
          </p>
        </div>
      </div>
    </div>
  );
}
