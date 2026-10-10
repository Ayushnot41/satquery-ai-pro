"use client";

import React, { useState, useEffect, useRef } from "react";
import { LocationSearchBar, LocationItem } from "../shared/LocationSearchBar";

interface MissionViewProps {
  onTriggerInvestigation: (areaName: string, question: string) => void;
}

export function MissionView({ onTriggerInvestigation }: MissionViewProps) {
  const [selectedOptics, setSelectedOptics] = useState<"optical" | "sar" | "flir" | "nvg">("optical");
  const [selectedTarget, setSelectedTarget] = useState<string>("NCR Delhi Urban Fringe");
  const [crtEnabled, setCrtEnabled] = useState<boolean>(true);
  const [heading, setHeading] = useState<number>(14.2);

  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const animFrameRef = useRef<number | null>(null);

  // 3D Globe Interactive States
  const globeAngleRef = useRef<number>(0);
  const globePitchRef = useRef<number>(0.28);
  const isDraggingRef = useRef<boolean>(false);
  const lastMouseRef = useRef<{ x: number; y: number }>({ x: 0, y: 0 });
  const satellitePhaseRef = useRef<number>(0);

  const regions = [
    {
      id: "delhi",
      name: "NCR Delhi Urban Fringe",
      coords: "28.6139° N, 77.2090° E",
      lat: 28.6139,
      lon: 77.209,
      mgrs: "43R FK 2145 6789",
      bounds: "[77.10° E, 28.55° N, 77.35° E, 28.75° N]",
      defaultQuery: "Where has construction increased between these two dates?",
      elevation: "216 m MSL",
      radarReturn: "-8.2 dB (Double-Bounce)",
    },
    {
      id: "assam",
      name: "Brahmaputra Flood Plain",
      coords: "26.2006° N, 92.9376° E",
      lat: 26.2006,
      lon: 92.9376,
      mgrs: "46R ER 9210 0145",
      bounds: "[92.70° E, 26.05° N, 93.15° E, 26.35° N]",
      defaultQuery: "Where did flooding expand?",
      elevation: "86 m MSL",
      radarReturn: "-21.4 dB (Specular Water)",
    },
    {
      id: "ghats",
      name: "Western Ghats Forest Buffer",
      coords: "10.1632° N, 76.6413° E",
      lat: 10.1632,
      lon: 76.6413,
      mgrs: "43P FM 6120 2480",
      bounds: "[76.45° E, 10.00° N, 76.85° E, 10.30° N]",
      defaultQuery: "Where has vegetation changed?",
      elevation: "1,240 m MSL",
      radarReturn: "-12.6 dB (Volume Canopy)",
    },
  ];

  const [customTarget, setCustomTarget] = useState<any | null>(null);
  const currentRegion = customTarget || regions.find((r) => r.name === selectedTarget) || regions[0];

  const handleLocationSelect = (loc: LocationItem) => {
    setSelectedTarget(loc.name);
    // Smoothly turn the 3D globe to face the searched target
    globeAngleRef.current = -loc.lon;
    globePitchRef.current = Math.max(-0.85, Math.min(0.85, (loc.lat - 15) * (Math.PI / 180)));
    setCustomTarget({
      id: "custom",
      name: loc.name,
      coords: `${loc.lat.toFixed(4)}° N, ${loc.lon.toFixed(4)}° E`,
      lat: loc.lat,
      lon: loc.lon,
      mgrs: loc.mgrs || `43R FK ${Math.abs(Math.floor(loc.lon * 100))} ${Math.abs(Math.floor(loc.lat * 100))}`,
      bounds: `[${(loc.lon - 0.1).toFixed(2)}° E, ${(loc.lat - 0.1).toFixed(2)}° N, ${(loc.lon + 0.1).toFixed(2)}° E, ${(loc.lat + 0.1).toFixed(2)}° N]`,
      defaultQuery: `Investigate remote sensing change and features in ${loc.name}`,
      elevation: `${loc.elevation_m || 200} m MSL`,
      radarReturn: "-14.2 dB (Mixed Target)",
    });
  };

  // Azimuth compass tape auto-rotation
  useEffect(() => {
    const interval = setInterval(() => {
      setHeading((h) => (h + 0.1) % 360);
    }, 200);
    return () => clearInterval(interval);
  }, []);

  // 3D Canvas Projection Engine
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const handleResize = () => {
      if (!canvas) return;
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
    };
    handleResize();
    window.addEventListener("resize", handleResize);

    const project3D = (lat: number, lon: number, alt = 0, cx: number, cy: number, r: number) => {
      const phi = (90 - lat) * (Math.PI / 180);
      const theta = (lon + globeAngleRef.current) * (Math.PI / 180);
      const radius = r + alt;

      let x = radius * Math.sin(phi) * Math.cos(theta);
      let y = radius * Math.cos(phi);
      let z = radius * Math.sin(phi) * Math.sin(theta);

      // Pitch rotation
      const cosP = Math.cos(globePitchRef.current);
      const sinP = Math.sin(globePitchRef.current);
      const y2 = y * cosP - z * sinP;
      const z2 = y * sinP + z * cosP;

      return {
        x: cx + x,
        y: cy - y2,
        z: z2,
        visible: z2 > -r * 0.35,
      };
    };

    const render = () => {
      if (!canvas || !ctx) return;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      const cx = canvas.width / 2;
      const cy = canvas.height / 2;
      const globeRadius = Math.min(canvas.width, canvas.height) * 0.36;

      if (!isDraggingRef.current) {
        globeAngleRef.current += 0.12;
      }
      satellitePhaseRef.current += 0.015;

      // Outer Atmospheric Glow
      const glowGrad = ctx.createRadialGradient(cx, cy, globeRadius * 0.8, cx, cy, globeRadius * 1.35);
      if (selectedOptics === "sar") {
        glowGrad.addColorStop(0, "rgba(139, 92, 246, 0.16)");
        glowGrad.addColorStop(1, "transparent");
      } else if (selectedOptics === "flir") {
        glowGrad.addColorStop(0, "rgba(245, 158, 11, 0.16)");
        glowGrad.addColorStop(1, "transparent");
      } else if (selectedOptics === "nvg") {
        glowGrad.addColorStop(0, "rgba(16, 185, 129, 0.20)");
        glowGrad.addColorStop(1, "transparent");
      } else {
        glowGrad.addColorStop(0, "rgba(6, 182, 212, 0.18)");
        glowGrad.addColorStop(1, "transparent");
      }
      ctx.fillStyle = glowGrad;
      ctx.beginPath();
      ctx.arc(cx, cy, globeRadius * 1.35, 0, Math.PI * 2);
      ctx.fill();

      // Globe Base Body
      ctx.beginPath();
      ctx.arc(cx, cy, globeRadius, 0, Math.PI * 2);
      ctx.fillStyle = "#030816";
      ctx.fill();
      ctx.strokeStyle =
        selectedOptics === "sar"
          ? "rgba(139, 92, 246, 0.4)"
          : selectedOptics === "flir"
          ? "rgba(245, 158, 11, 0.4)"
          : selectedOptics === "nvg"
          ? "rgba(16, 185, 129, 0.45)"
          : "rgba(6, 182, 212, 0.35)";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // Latitude Parallels
      for (let lat = -60; lat <= 60; lat += 30) {
        ctx.beginPath();
        let first = true;
        for (let lon = 0; lon <= 360; lon += 8) {
          const pt = project3D(lat, lon, 0, cx, cy, globeRadius);
          if (pt.visible) {
            if (first) {
              ctx.moveTo(pt.x, pt.y);
              first = false;
            } else ctx.lineTo(pt.x, pt.y);
          } else {
            first = true;
          }
        }
        ctx.strokeStyle = "rgba(75, 85, 99, 0.25)";
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }

      // Longitude Meridians
      for (let lon = 0; lon < 360; lon += 30) {
        ctx.beginPath();
        let first = true;
        for (let lat = -80; lat <= 80; lat += 8) {
          const pt = project3D(lat, lon, 0, cx, cy, globeRadius);
          if (pt.visible) {
            if (first) {
              ctx.moveTo(pt.x, pt.y);
              first = false;
            } else ctx.lineTo(pt.x, pt.y);
          } else {
            first = true;
          }
        }
        ctx.strokeStyle = "rgba(75, 85, 99, 0.25)";
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }

      // Subcontinent Landmass Contour (India Perimeter)
      const subContinent = [
        { lat: 34, lon: 74 },
        { lat: 31, lon: 77 },
        { lat: 28, lon: 81 },
        { lat: 26, lon: 88 },
        { lat: 27, lon: 95 },
        { lat: 23, lon: 91 },
        { lat: 21, lon: 87 },
        { lat: 16, lon: 82 },
        { lat: 10, lon: 79 },
        { lat: 8, lon: 77.5 },
        { lat: 12, lon: 75 },
        { lat: 16, lon: 73.5 },
        { lat: 20, lon: 73 },
        { lat: 23, lon: 69 },
        { lat: 26, lon: 70 },
        { lat: 32, lon: 74 },
      ];
      ctx.beginPath();
      let firstCoast = true;
      subContinent.forEach((ptCoord) => {
        const pt = project3D(ptCoord.lat, ptCoord.lon, 0, cx, cy, globeRadius);
        if (pt.visible) {
          if (firstCoast) {
            ctx.moveTo(pt.x, pt.y);
            firstCoast = false;
          } else ctx.lineTo(pt.x, pt.y);
        }
      });
      ctx.closePath();
      ctx.fillStyle =
        selectedOptics === "sar"
          ? "rgba(139, 92, 246, 0.18)"
          : selectedOptics === "flir"
          ? "rgba(239, 68, 68, 0.22)"
          : selectedOptics === "nvg"
          ? "rgba(16, 185, 129, 0.25)"
          : "rgba(6, 182, 212, 0.16)";
      ctx.fill();
      ctx.strokeStyle =
        selectedOptics === "sar"
          ? "#a78bfa"
          : selectedOptics === "flir"
          ? "#f87171"
          : selectedOptics === "nvg"
          ? "#34d399"
          : "#38bdf8";
      ctx.lineWidth = 1.5;
      ctx.stroke();

      // 3D Extruded Architectural Wireframe Prisms over NCR Delhi
      const delhiBase = project3D(28.61, 77.2, 0, cx, cy, globeRadius);
      const delhiTop = project3D(28.61, 77.2, 38, cx, cy, globeRadius);
      if (delhiBase.visible) {
        ctx.strokeStyle = "#ef4444";
        ctx.fillStyle = "rgba(239, 68, 68, 0.35)";
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        ctx.moveTo(delhiBase.x - 14, delhiBase.y - 6);
        ctx.lineTo(delhiBase.x + 14, delhiBase.y - 6);
        ctx.lineTo(delhiTop.x + 14, delhiTop.y - 6);
        ctx.lineTo(delhiTop.x - 14, delhiTop.y - 6);
        ctx.closePath();
        ctx.fill();
        ctx.stroke();

        ctx.fillStyle = "#ef4444";
        ctx.beginPath();
        ctx.arc(delhiTop.x, delhiTop.y, 4.5, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#ffffff";
        ctx.font = "9px 'JetBrains Mono', monospace";
        ctx.fillText("NCR DELHI [EXTRUDED // 216M]", delhiTop.x + 10, delhiTop.y + 3);
      }

      // Hotspot Beacons for Assam & Western Ghats
      const assamPt = project3D(26.2, 92.93, 0, cx, cy, globeRadius);
      if (assamPt.visible) {
        ctx.fillStyle = "#06b6d4";
        ctx.beginPath();
        ctx.arc(assamPt.x, assamPt.y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#a5f3fc";
        ctx.font = "9px 'JetBrains Mono', monospace";
        ctx.fillText("BRAHMAPUTRA BASIN", assamPt.x + 8, assamPt.y + 3);
      }

      const ghatsPt = project3D(10.16, 76.64, 0, cx, cy, globeRadius);
      if (ghatsPt.visible) {
        ctx.fillStyle = "#10b981";
        ctx.beginPath();
        ctx.arc(ghatsPt.x, ghatsPt.y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.fillStyle = "#6ee7b7";
        ctx.font = "9px 'JetBrains Mono', monospace";
        ctx.fillText("WESTERN GHATS", ghatsPt.x + 8, ghatsPt.y + 3);
      }

      // Sentinel-1 SAR Orbit Ring (Violet Polar Orbit)
      ctx.beginPath();
      let firstS1 = true;
      for (let a = 0; a <= 360; a += 8) {
        const pLat = Math.sin((a * Math.PI) / 180) * 80;
        const pLon = a * 1.5;
        const pt = project3D(pLat, pLon, 45, cx, cy, globeRadius);
        if (pt.visible) {
          if (firstS1) {
            ctx.moveTo(pt.x, pt.y);
            firstS1 = false;
          } else ctx.lineTo(pt.x, pt.y);
        } else {
          firstS1 = true;
        }
      }
      ctx.strokeStyle = "rgba(139, 92, 246, 0.45)";
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Sentinel-1 Satellite Tracker Pod
      const s1Lat = Math.sin(satellitePhaseRef.current) * 80;
      const s1Lon = ((satellitePhaseRef.current * 180) / Math.PI) * 1.5;
      const s1Pt = project3D(s1Lat, s1Lon, 45, cx, cy, globeRadius);
      if (s1Pt.visible) {
        ctx.fillStyle = "#8b5cf6";
        ctx.beginPath();
        ctx.arc(s1Pt.x, s1Pt.y, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = "#c4b5fd";
        ctx.font = "10px 'JetBrains Mono', monospace";
        ctx.fillText("SENTINEL-1 (SAR C-BAND)", s1Pt.x + 8, s1Pt.y + 3);
      }

      // Sentinel-2 Optical Orbit Ring (Cyan Sun-Synchronous Orbit)
      ctx.beginPath();
      let firstS2 = true;
      for (let a = 0; a <= 360; a += 8) {
        const pLat = Math.cos((a * Math.PI) / 180) * 75;
        const pLon = a * 1.2 + 90;
        const pt = project3D(pLat, pLon, 55, cx, cy, globeRadius);
        if (pt.visible) {
          if (firstS2) {
            ctx.moveTo(pt.x, pt.y);
            firstS2 = false;
          } else ctx.lineTo(pt.x, pt.y);
        } else {
          firstS2 = true;
        }
      }
      ctx.strokeStyle = "rgba(6, 182, 212, 0.45)";
      ctx.setLineDash([4, 4]);
      ctx.stroke();
      ctx.setLineDash([]);

      // Sentinel-2 Satellite Tracker Pod
      const s2Lat = Math.cos(satellitePhaseRef.current * 0.8) * 75;
      const s2Lon = ((satellitePhaseRef.current * 0.8 * 180) / Math.PI) * 1.2 + 90;
      const s2Pt = project3D(s2Lat, s2Lon, 55, cx, cy, globeRadius);
      if (s2Pt.visible) {
        ctx.fillStyle = "#06b6d4";
        ctx.beginPath();
        ctx.arc(s2Pt.x, s2Pt.y, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.strokeStyle = "#ffffff";
        ctx.lineWidth = 1.5;
        ctx.stroke();
        ctx.fillStyle = "#a5f3fc";
        ctx.font = "10px 'JetBrains Mono', monospace";
        ctx.fillText("SENTINEL-2 (MSI 10M)", s2Pt.x + 8, s2Pt.y + 3);
      }

      animFrameRef.current = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
    };
  }, [selectedOptics]);

  // Mouse drag handlers for interactive 3D rotation
  const handleMouseDown = (e: React.MouseEvent<HTMLCanvasElement>) => {
    isDraggingRef.current = true;
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseMove = (e: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDraggingRef.current) return;
    const dx = e.clientX - lastMouseRef.current.x;
    const dy = e.clientY - lastMouseRef.current.y;
    globeAngleRef.current += dx * 0.45;
    globePitchRef.current = Math.max(-0.9, Math.min(0.9, globePitchRef.current + dy * 0.005));
    lastMouseRef.current = { x: e.clientX, y: e.clientY };
  };

  const handleMouseUp = () => {
    isDraggingRef.current = false;
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4 text-white select-none space-y-4">
      {/* ================= TOP TACTICAL HUD HEADER ================= */}
      <div className="flex items-center justify-between bg-[#070B14] border border-[#1F2937] p-4 rounded-xl shadow-2xl relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 pointer-events-none bg-[radial-gradient(#38bdf8_1px,transparent_1px)] [background-size:16px_16px]" />

        <div className="relative z-10 flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-300 shadow-[0_0_15px_rgba(6,182,212,0.3)]">
            <svg className="w-5 h-5 animate-pulse" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10" />
              <path d="M12 2a14.5 14.5 0 0 0 0 20 14.5 14.5 0 0 0 0-20" />
              <path d="M2 12h20" />
            </svg>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-sm font-bold font-mono tracking-wider text-white uppercase">
                God&apos;s Eye View // Spatial Telemetry &amp; Orbit HUD
              </h2>
              <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-cyan-950 text-cyan-300 border border-cyan-500/30 uppercase">
                ACTIVE RECON
              </span>
            </div>
            <p className="text-xs text-gray-400 mt-0.5 font-mono">
              3D Spherical Orbit Engine &bull; Co-registered Sentinel-1 SAR &amp; Sentinel-2 MSI &bull; SIH26167
            </p>
          </div>
        </div>

        {/* Real-Time Flight Telemetry */}
        <div className="relative z-10 flex items-center gap-6 font-mono text-xs text-gray-300">
          <div>
            <span className="text-[10px] text-gray-500 uppercase block">Orbital Alt</span>
            <span className="text-cyan-300 font-bold">786.4 km (LEO)</span>
          </div>
          <div>
            <span className="text-[10px] text-gray-500 uppercase block">Velocity</span>
            <span className="text-emerald-300 font-bold">7.56 km/s</span>
          </div>
          <div>
            <span className="text-[10px] text-gray-500 uppercase block">GSD</span>
            <span className="text-cyan-300 font-bold">10.0 m/px</span>
          </div>
          <div>
            <span className="text-[10px] text-gray-500 uppercase block">Sun Azimuth</span>
            <span className="text-amber-300 font-bold">142.8° / +54°</span>
          </div>
          <div>
            <span className="text-[10px] text-gray-500 uppercase block">Radar Return</span>
            <span className="text-purple-300 font-bold">{currentRegion.radarReturn}</span>
          </div>
        </div>
      </div>

      {/* ================= RECON TARGET LOCATION SEARCH ================= */}
      <div className="w-full bg-[#070B14] border border-[#1F2937] p-3 rounded-xl shadow-xl">
        <LocationSearchBar
          onSelectLocation={handleLocationSelect}
          selectedLocationName={currentRegion.name}
        />
      </div>

      {/* ================= COMPASS HEADING TAPE ================= */}
      <div className="w-full bg-[#050811] border border-[#1F2937] px-4 py-2 rounded-xl flex items-center justify-between font-mono text-xs text-gray-400 overflow-hidden shadow-inner">
        <span className="text-[10px] text-gray-500 uppercase tracking-wider shrink-0">BEARING // AZIMUTH</span>

        <div className="flex items-center gap-4 text-[11px] overflow-hidden tracking-widest text-cyan-400/70">
          <span>330°</span>
          <span className="text-gray-600">····</span>
          <span>345°</span>
          <span className="text-gray-600">····</span>
          <span className="text-white font-bold bg-cyan-950 px-2 py-0.5 rounded border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.3)]">
            [ N {heading.toFixed(1)}° ]
          </span>
          <span className="text-gray-600">····</span>
          <span>015°</span>
          <span className="text-gray-600">····</span>
          <span>030°</span>
          <span className="text-gray-600">····</span>
          <span>045° NE</span>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          <button
            onClick={() => setCrtEnabled(!crtEnabled)}
            className={`px-2 py-0.5 rounded text-[10px] font-mono cursor-pointer transition-colors ${
              crtEnabled ? "bg-emerald-950 text-emerald-300 border border-emerald-500/40" : "bg-gray-800 text-gray-400"
            }`}
          >
            CRT RASTER: {crtEnabled ? "ON" : "OFF"}
          </button>
          <span className="text-gray-500 text-[10px]">MGRS: {currentRegion.mgrs}</span>
        </div>
      </div>

      {/* ================= MAIN SPATIAL EARTH CANOPY VIEWPORT ================= */}
      <div className="relative w-full h-[600px] bg-[#030611] rounded-2xl border border-[#1F2937] overflow-hidden shadow-2xl flex flex-col justify-between p-6">
        {/* Background Cartesian Tactical Grid */}
        <div
          className="absolute inset-0 pointer-events-none opacity-40 transition-all duration-500"
          style={{
            backgroundImage: `
              radial-gradient(circle at 50% 50%, rgba(6, 182, 212, 0.15) 0%, rgba(3, 6, 17, 0.95) 85%),
              linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
              linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px)
            `,
            backgroundSize: "100% 100%, 60px 60px, 60px 60px",
          }}
        />

        {/* Interactive 3D Canvas Globe */}
        <canvas
          ref={canvasRef}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
          className="absolute inset-0 w-full h-full cursor-grab active:cursor-grabbing z-0"
        />

        {/* Optics Shader Emulation Filter */}
        <div
          className={`absolute inset-0 pointer-events-none transition-all duration-700 z-10 ${
            selectedOptics === "sar"
              ? "grayscale contrast-200 invert-0 mix-blend-screen bg-violet-950/20"
              : selectedOptics === "flir"
              ? "hue-rotate-180 saturate-200 contrast-150 bg-amber-950/20"
              : selectedOptics === "nvg"
              ? "sepia-[0.9] hue-rotate-[90deg] saturate-[3] contrast-[1.4] bg-emerald-950/30"
              : ""
          }`}
        />

        {/* CRT Scanline Overlay */}
        {crtEnabled && (
          <div
            className="absolute inset-0 pointer-events-none opacity-25 z-10"
            style={{
              backgroundImage:
                "repeating-linear-gradient(0deg, rgba(0, 0, 0, 0.2), rgba(0, 0, 0, 0.2) 1px, transparent 1px, transparent 3px)",
            }}
          />
        )}

        {/* Radar Sweep Animation */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[520px] h-[520px] rounded-full border border-cyan-500/20 pointer-events-none z-10">
          <div className="absolute inset-0 rounded-full border border-dashed border-cyan-500/15" />
          <div className="absolute inset-16 rounded-full border border-cyan-500/20" />
          <div className="absolute inset-32 rounded-full border border-cyan-500/25" />
          <div
            className="absolute top-1/2 left-1/2 w-[260px] h-[260px] -translate-x-full -translate-y-full origin-bottom-right pointer-events-none animate-spin"
            style={{
              animationDuration: "6s",
              background: "conic-gradient(from 0deg, rgba(6, 182, 212, 0.3) 0deg, transparent 60deg)",
            }}
          />
          <span className="absolute top-4 left-1/2 -translate-x-1/2 text-[9px] font-mono text-cyan-400/60 bg-black/60 px-1 rounded">
            50 KM
          </span>
          <span className="absolute top-20 left-1/2 -translate-x-1/2 text-[9px] font-mono text-cyan-400/60 bg-black/60 px-1 rounded">
            25 KM
          </span>
          <span className="absolute top-36 left-1/2 -translate-x-1/2 text-[9px] font-mono text-cyan-400/60 bg-black/60 px-1 rounded">
            10 KM
          </span>
        </div>

        {/* Four Corner Framing Reticles & Coordinates */}
        <div className="absolute inset-5 pointer-events-none z-20">
          <div className="absolute top-0 left-0">
            <div className="w-6 h-6 border-t-2 border-l-2 border-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
            <span className="text-[10px] font-mono text-cyan-300 bg-black/80 px-1.5 py-0.5 rounded mt-1 block">
              NW: 28.7500° N, 77.1000° E
            </span>
          </div>

          <div className="absolute top-0 right-0 text-right">
            <div className="w-6 h-6 border-t-2 border-r-2 border-cyan-400 ml-auto shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
            <span className="text-[10px] font-mono text-cyan-300 bg-black/80 px-1.5 py-0.5 rounded mt-1 block">
              NE: 28.7500° N, 77.3500° E
            </span>
          </div>

          <div className="absolute bottom-0 left-0">
            <span className="text-[10px] font-mono text-cyan-300 bg-black/80 px-1.5 py-0.5 rounded mb-1 block">
              SW: 28.5500° N, 77.1000° E
            </span>
            <div className="w-6 h-6 border-b-2 border-l-2 border-cyan-400 shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
          </div>

          <div className="absolute bottom-0 right-0 text-right">
            <span className="text-[10px] font-mono text-cyan-300 bg-black/80 px-1.5 py-0.5 rounded mb-1 block">
              SE: 28.5500° N, 77.3500° E
            </span>
            <div className="w-6 h-6 border-b-2 border-r-2 border-cyan-400 ml-auto shadow-[0_0_8px_rgba(6,182,212,0.8)]" />
          </div>
        </div>

        {/* Center Target Acquisition Crosshair */}
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-none z-20 text-center">
          <div className="w-80 h-64 border-2 border-cyan-400/80 rounded-lg relative shadow-[0_0_30px_rgba(6,182,212,0.25)]">
            <div className="absolute -top-3 -left-3 w-6 h-6 border-t-2 border-l-2 border-cyan-300" />
            <div className="absolute -top-3 -right-3 w-6 h-6 border-t-2 border-r-2 border-cyan-300" />
            <div className="absolute -bottom-3 -left-3 w-6 h-6 border-b-2 border-l-2 border-cyan-300" />
            <div className="absolute -bottom-3 -right-3 w-6 h-6 border-b-2 border-r-2 border-cyan-300" />

            <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-4 h-4">
              <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-cyan-400" />
              <div className="absolute left-1/2 top-0 bottom-0 w-0.5 bg-cyan-400" />
              <div className="absolute inset-0 rounded-full border border-cyan-300 animate-ping opacity-75" />
            </div>

            <div className="absolute -top-6 left-2 bg-black/85 px-2.5 py-0.5 rounded text-[10px] font-mono text-cyan-300 uppercase tracking-wider border border-cyan-500/40">
              AOI RECON TARGET: {currentRegion.name}
            </div>
            <div className="absolute -bottom-6 right-2 bg-black/85 px-2.5 py-0.5 rounded text-[10px] font-mono text-gray-300 border border-gray-700">
              ELEVATION: {currentRegion.elevation} &bull; BOUNDS: {currentRegion.bounds}
            </div>
          </div>
        </div>

        {/* ================= TOP CONTROLS: 4-CHANNEL SENSOR OPTICS ================= */}
        <div className="relative z-30 flex items-center justify-between pointer-events-none">
          <div className="flex items-center gap-1.5 bg-black/85 backdrop-blur-md p-1.5 rounded-xl border border-white/10 text-xs font-mono shadow-2xl pointer-events-auto">
            <span className="text-[11px] text-gray-400 px-2 uppercase font-semibold">SENSOR OPTICS:</span>

            <button
              onClick={() => setSelectedOptics("optical")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-all ${
                selectedOptics === "optical"
                  ? "bg-blue-600 text-white shadow-[0_0_12px_rgba(59,130,246,0.6)]"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Optical RGB (Sentinel-2)
            </button>

            <button
              onClick={() => setSelectedOptics("sar")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-all ${
                selectedOptics === "sar"
                  ? "bg-purple-600 text-white shadow-[0_0_12px_rgba(139,92,246,0.6)]"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              SAR Microwave (Sentinel-1)
            </button>

            <button
              onClick={() => setSelectedOptics("flir")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-all ${
                selectedOptics === "flir"
                  ? "bg-amber-600 text-white shadow-[0_0_12px_rgba(245,158,11,0.6)]"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              Thermal FLIR (Heatmap)
            </button>

            <button
              onClick={() => setSelectedOptics("nvg")}
              className={`px-3 py-1 rounded-lg text-xs font-semibold cursor-pointer transition-all ${
                selectedOptics === "nvg"
                  ? "bg-emerald-600 text-white shadow-[0_0_12px_rgba(16,185,129,0.6)]"
                  : "text-gray-400 hover:text-white"
              }`}
            >
              NVG Night Vision (Phosphor)
            </button>
          </div>

          {/* Target Region Quick Switcher */}
          <div className="flex items-center gap-1.5 bg-black/85 backdrop-blur-md p-1.5 rounded-xl border border-white/10 text-xs font-mono shadow-2xl pointer-events-auto">
            <span className="text-[11px] text-gray-400 px-2 uppercase">HOTSPOTS:</span>
            {regions.map((r) => (
              <button
                key={r.name}
                onClick={() => setSelectedTarget(r.name)}
                className={`px-2.5 py-1 rounded-lg text-xs cursor-pointer transition-all ${
                  selectedTarget === r.name
                    ? "bg-cyan-950 text-cyan-300 border border-cyan-500/50 shadow-[0_0_10px_rgba(6,182,212,0.3)]"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                {r.name.split(" ")[0]}
              </button>
            ))}
          </div>
        </div>

        {/* ================= BOTTOM ACTION BAR: SCENE-AWARE TRIGGER ================= */}
        <div className="relative z-30 flex items-center justify-between bg-black/90 backdrop-blur-md p-4 rounded-xl border border-white/15 shadow-2xl pointer-events-auto">
          <div>
            <div className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-cyan-400 animate-ping" />
              <span className="text-[10px] uppercase font-mono text-cyan-400 font-bold tracking-wider">
                ACTIVE SCENE GROUNDING CONTEXT
              </span>
            </div>
            <h3 className="text-sm font-bold text-white font-space mt-0.5">{currentRegion.name}</h3>
            <p className="text-xs text-gray-400 font-mono">
              Coordinates: {currentRegion.coords} &bull; MGRS: {currentRegion.mgrs} &bull; Dual Optical-SAR co-registration confirmed
            </p>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => onTriggerInvestigation(currentRegion.name, currentRegion.defaultQuery)}
              className="px-6 py-2.5 bg-gradient-to-r from-blue-600 via-cyan-600 to-indigo-600 hover:from-blue-500 hover:to-cyan-500 text-white font-bold text-xs rounded-xl shadow-[0_0_20px_rgba(6,182,212,0.4)] border border-cyan-400/50 transition-all cursor-pointer flex items-center gap-2 font-mono uppercase tracking-wider"
            >
              <svg className="w-4 h-4 text-cyan-200" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <polygon points="5 3 19 12 5 21 5 3" />
              </svg>
              <span>Launch AI Investigation &rarr;</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
