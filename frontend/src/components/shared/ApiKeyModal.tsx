"use client";

import React, { useState } from "react";
import { Key, X, CheckCircle, ShieldAlert, Sparkles } from "lucide-react";

interface ApiKeyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave: (keys: { googleMaps?: string; mapbox?: string; sentinelHub?: string }) => void;
}

export function ApiKeyModal({ isOpen, onClose, onSave }: ApiKeyModalProps) {
  const [googleKey, setGoogleKey] = useState("");
  const [mapboxKey, setMapboxKey] = useState("");
  const [sentinelKey, setSentinelKey] = useState("");
  const [isSaved, setIsSaved] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    onSave({
      googleMaps: googleKey.trim() || undefined,
      mapbox: mapboxKey.trim() || undefined,
      sentinelHub: sentinelKey.trim() || undefined,
    });
    setIsSaved(true);
    setTimeout(() => {
      setIsSaved(false);
      onClose();
    }, 600);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
      <div className="bg-[#0B1120] border border-[#1F2937] rounded-2xl max-w-lg w-full p-6 shadow-2xl space-y-4 text-gray-200 font-sans">
        
        <div className="flex items-center justify-between pb-3 border-b border-[#1F2937]">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-cyan-950/80 border border-cyan-500/40 flex items-center justify-center text-cyan-400">
              <Key className="w-4 h-4" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono uppercase text-white tracking-wider">
                Geospatial & Vision API Keys
              </h3>
              <p className="text-[10px] text-gray-400 font-mono">
                Commercial Maps, Live Traffic & Foundation Sensor Connectors
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

        <div className="p-3 rounded-xl bg-[#030712] border border-[#1F2937] text-xs leading-relaxed text-gray-300">
          <div className="flex items-center gap-1.5 text-emerald-400 font-mono font-bold text-[11px] mb-1">
            <CheckCircle className="w-3.5 h-3.5" />
            <span>Zero-Key Architecture Active</span>
          </div>
          <p className="text-[11px] text-gray-400 font-sans">
            BHUVISION streams high-resolution satellite tiles (<strong className="text-gray-200">ESRI World Imagery</strong> 0.3m-15m GSD) and daily passes (<strong className="text-gray-200">NASA GIBS NRT</strong>) completely free without needing any API keys. Providing commercial keys below enables Google Traffic, Photorealistic 3D Tiles, and raw Sentinel-2 bands.
          </p>
        </div>

        <div className="space-y-3 font-mono text-xs">
          <div>
            <label className="block text-gray-300 mb-1 text-[11px] font-medium">
              Google Maps Platform API Key (Traffic, Places, 3D Tiles)
            </label>
            <input
              type="text"
              value={googleKey}
              onChange={(e) => setGoogleKey(e.target.value)}
              placeholder="AIzaSy..."
              className="w-full bg-[#030611] border border-[#1F2937] focus:border-cyan-400 rounded-lg px-3 py-2 text-white placeholder-gray-600 outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-1 text-[11px] font-medium">
              Mapbox Access Token (Optional Vector Basemaps)
            </label>
            <input
              type="text"
              value={mapboxKey}
              onChange={(e) => setMapboxKey(e.target.value)}
              placeholder="pk.eyJ1..."
              className="w-full bg-[#030611] border border-[#1F2937] focus:border-cyan-400 rounded-lg px-3 py-2 text-white placeholder-gray-600 outline-none transition-colors"
            />
          </div>

          <div>
            <label className="block text-gray-300 mb-1 text-[11px] font-medium">
              Copernicus Sentinel Hub OAuth Client ID (Optional)
            </label>
            <input
              type="text"
              value={sentinelKey}
              onChange={(e) => setSentinelKey(e.target.value)}
              placeholder="sh-oauth-client-id..."
              className="w-full bg-[#030611] border border-[#1F2937] focus:border-cyan-400 rounded-lg px-3 py-2 text-white placeholder-gray-600 outline-none transition-colors"
            />
          </div>
        </div>

        <div className="pt-3 border-t border-[#1F2937] flex items-center justify-between">
          <span className="text-[10px] font-mono text-cyan-400">
            {isSaved ? "Saved to Runtime Memory!" : "Keys persist in current session & .env"}
          </span>
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 text-white font-mono text-xs font-bold rounded-lg transition-all shadow-md"
          >
            {isSaved ? "Saved!" : "Save Keys"}
          </button>
        </div>

      </div>
    </div>
  );
}
