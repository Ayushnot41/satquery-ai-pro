"use client";

import React, { useState, useEffect, useRef } from "react";

export interface LocationItem {
  name: string;
  display_name: string;
  lat: number;
  lon: number;
  bbox?: number[];
  mgrs?: string;
  elevation_m?: number;
  category?: string;
  country?: string;
}

interface LocationSearchBarProps {
  onSelectLocation: (loc: LocationItem) => void;
  selectedLocationName?: string;
}

const DEFAULT_HOTSPOTS: LocationItem[] = [
  {
    name: "NCR Delhi Urban Fringe",
    display_name: "National Capital Region, Delhi, India",
    lat: 28.6139,
    lon: 77.209,
    mgrs: "43R FK 2145 6789",
    elevation_m: 216,
    category: "Urban & Construction",
    country: "India",
  },
  {
    name: "Bengaluru Tech Corridor",
    display_name: "Bengaluru Urban, Karnataka, India",
    lat: 12.9716,
    lon: 77.5946,
    mgrs: "43P FS 6520 3540",
    elevation_m: 920,
    category: "Urban Expansion",
    country: "India",
  },
  {
    name: "Brahmaputra Flood Plain",
    display_name: "Brahmaputra River Basin, Assam, India",
    lat: 26.2006,
    lon: 92.9376,
    mgrs: "46R ER 9210 0145",
    elevation_m: 86,
    category: "Flood Inundation (SAR)",
    country: "India",
  },
  {
    name: "Kedarnath Valley",
    display_name: "Kedarnath Glacial Valley, Rudraprayag, Uttarakhand, India",
    lat: 30.7346,
    lon: 79.0669,
    mgrs: "44R LL 0650 0120",
    elevation_m: 3583,
    category: "Glacial & Debris Flow",
    country: "India",
  },
  {
    name: "Western Ghats Buffer",
    display_name: "Western Ghats Ecological Corridor, India",
    lat: 10.1632,
    lon: 76.6413,
    mgrs: "43P FM 6120 2480",
    elevation_m: 1240,
    category: "Canopy & NDVI",
    country: "India",
  },
  {
    name: "Mumbai Coastal Road",
    display_name: "Mumbai Harbor & Coastal Reclamation, Maharashtra, India",
    lat: 18.922,
    lon: 72.8347,
    mgrs: "43Q DA 8240 9230",
    elevation_m: 8,
    category: "Reclamation Infrastructure",
    country: "India",
  },
  {
    name: "Dubai Palm Jumeirah",
    display_name: "Palm Jumeirah & Coastline, Dubai, UAE",
    lat: 25.1124,
    lon: 55.139,
    mgrs: "40R CN 1350 7820",
    elevation_m: 3,
    category: "Maritime Engineering",
    country: "UAE",
  },
];

export function LocationSearchBar({ onSelectLocation, selectedLocationName }: LocationSearchBarProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LocationItem[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  // Click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  // Debounced search
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setResults(DEFAULT_HOTSPOTS);
      return;
    }

    const timer = setTimeout(async () => {
      setLoading(true);
      try {
        // First try backend API
        const res = await fetch(`/api/locations/search?q=${encodeURIComponent(q)}&limit=6`);
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data) && data.length > 0) {
            setResults(data);
            setLoading(false);
            return;
          }
        }
      } catch (err) {
        // Fallback directly to Nominatim client-side if backend isn't responding
      }

      try {
        const nomRes = await fetch(
          `https://nominatim.openstreetmap.org/search?q=${encodeURIComponent(q)}&format=json&limit=6&addressdetails=1`
        );
        if (nomRes.ok) {
          const items = await nomRes.json();
          const mapped: LocationItem[] = items.map((it: any) => ({
            name: it.name || it.display_name.split(",")[0],
            display_name: it.display_name,
            lat: parseFloat(it.lat),
            lon: parseFloat(it.lon),
            category: (it.type || "Geographic").replace("_", " "),
            country: it.address?.country || "Global",
          }));
          setResults(mapped.length > 0 ? mapped : DEFAULT_HOTSPOTS);
        }
      } catch {
        // Filter local hotspots
        const filtered = DEFAULT_HOTSPOTS.filter(
          (h) =>
            h.name.toLowerCase().includes(q.toLowerCase()) ||
            h.display_name.toLowerCase().includes(q.toLowerCase()) ||
            h.category?.toLowerCase().includes(q.toLowerCase())
        );
        setResults(filtered.length > 0 ? filtered : DEFAULT_HOTSPOTS);
      } finally {
        setLoading(false);
      }
    }, 320);

    return () => clearTimeout(timer);
  }, [query]);

  const handleSelect = (item: LocationItem) => {
    setQuery(item.name);
    setIsOpen(false);
    onSelectLocation(item);
  };

  return (
    <div ref={containerRef} className="relative w-full text-white select-none">
      <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2">
        {/* Search Input Box */}
        <div className="relative flex-1">
          <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-cyan-400">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
            </svg>
          </div>

          <input
            type="text"
            value={query}
            onFocus={() => {
              setIsOpen(true);
              if (!query) setResults(DEFAULT_HOTSPOTS);
            }}
            onChange={(e) => {
              setQuery(e.target.value);
              setIsOpen(true);
            }}
            placeholder="Search any place on Earth (e.g., Delhi, Bengaluru, Kedarnath, Mumbai, Dubai, Suez)..."
            className="w-full bg-[#070C18] border border-[#1F2937] focus:border-cyan-400 rounded-xl pl-10 pr-10 py-2.5 text-xs text-white placeholder-gray-500 outline-none transition-all font-mono"
          />

          {loading ? (
            <div className="absolute inset-y-0 right-0 pr-3.5 flex items-center pointer-events-none">
              <div className="w-3.5 h-3.5 border-2 border-cyan-400 border-t-transparent rounded-full animate-spin" />
            </div>
          ) : query ? (
            <button
              onClick={() => {
                setQuery("");
                setResults(DEFAULT_HOTSPOTS);
              }}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-white cursor-pointer"
            >
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
            </button>
          ) : null}
        </div>

        {/* Selected target badge */}
        {selectedLocationName && (
          <div className="hidden md:flex items-center gap-2 bg-[#0C1527] border border-cyan-500/40 px-3 py-2 rounded-xl text-[11px] font-mono text-cyan-300 shrink-0">
            <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
            <span className="font-bold uppercase tracking-wider truncate max-w-[200px]">
              TARGET: {selectedLocationName}
            </span>
          </div>
        )}
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && (
        <div className="absolute top-full left-0 right-0 mt-1.5 bg-[#070B16] border border-[#1F2937] rounded-xl shadow-2xl z-50 max-h-80 overflow-y-auto backdrop-blur-xl">
          <div className="p-2 border-b border-[#1F2937]/70 flex items-center justify-between text-[10px] font-mono text-gray-400">
            <span>{query ? "GLOBAL SEARCH RESULTS" : "STRATEGIC RECON HOTSPOTS"}</span>
            <span className="text-cyan-400">OSM Nominatim + ESRI World Imagery</span>
          </div>

          <div className="divide-y divide-[#1F2937]/40">
            {results.map((loc, idx) => (
              <div
                key={idx}
                onClick={() => handleSelect(loc)}
                className="p-3 hover:bg-cyan-950/40 transition-colors cursor-pointer flex items-center justify-between group"
              >
                <div className="flex items-center gap-3">
                  <div className="w-7 h-7 rounded-lg bg-[#0C1527] border border-cyan-500/30 flex items-center justify-center text-cyan-300 group-hover:border-cyan-400 group-hover:bg-cyan-900/60 transition-colors">
                    <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M12 2a8 8 0 0 0-8 8c0 5.25 8 12 8 12s8-6.75 8-12a8 8 0 0 0-8-8z" />
                      <circle cx="12" cy="10" r="3" />
                    </svg>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-bold text-white group-hover:text-cyan-300 font-mono">
                        {loc.name}
                      </span>
                      {loc.category && (
                        <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-950 text-blue-300 border border-blue-500/30">
                          {loc.category}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-gray-400 font-mono truncate max-w-lg mt-0.5">
                      {loc.display_name}
                    </p>
                  </div>
                </div>

                <div className="text-right shrink-0 font-mono">
                  <span className="text-[10px] text-cyan-400 block font-bold">
                    {loc.lat.toFixed(4)}° N, {loc.lon.toFixed(4)}° E
                  </span>
                  <span className="text-[9px] text-gray-500">
                    {loc.mgrs ? `MGRS: ${loc.mgrs}` : loc.country}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
