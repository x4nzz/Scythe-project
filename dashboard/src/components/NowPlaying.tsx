"use client";

import { useState, useEffect } from "react";
import { BladeSlash } from "@/components/BladeSlash";

export default function NowPlaying() {
  const [data, setData] = useState({
    title: "",
    artist: "",
    uri: "",
    artwork: "",
    duration: 0,
    elapsed: 0,
    is_playing: false
  });

  useEffect(() => {
    const fetchNowPlaying = async () => {
      try {
        const res = await fetch("/api/now-playing");
        if (res.ok) {
          const nowPlayingData = await res.json();
          setData(nowPlayingData);
        }
      } catch (e) {
        console.error("Failed to fetch now playing:", e);
      }
    };

    // Fetch immediately
    fetchNowPlaying();

    // Set interval to update every 5 seconds
    const interval = setInterval(() => {
      fetchNowPlaying();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  // Format duration from seconds to mm:ss
  const formatDuration = (seconds: number) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  // Format elapsed time similarly
  const formatElapsed = (seconds: number) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  return (
    <div className="relative flex items-center gap-4 bg-dark-2 border border-dark-3 rounded-none px-4 py-3 hover:border-silver/50 transition-all duration-300">
      <BladeSlash className="absolute inset-0 pointer-events-none" duration={0.6} trigger="hover" />
      <div className="relative z-10 flex-shrink-0">
        {/* Album art */}
        {data.artwork ? (
          <img
            src={data.artwork}
            alt="Album Art"
            className="w-12 h-12 object-cover rounded-none"
          />
        ) : (
          <div className="w-12 h-12 bg-dark-1 flex items-center justify-center rounded-none">
            <div className="text-silver text-xs">🎵</div>
          </div>
        )}
      </div>
      <div className="flex-1 space-y-1">
        {data.title && (
          <p className="text-sm font-medium text-white">
            <a href={data.uri} target="_blank" rel="noopener noreferrer" className="underline">
              {data.title}
            </a>
          </p>
        )}
        <p className="text-xs text-dark-silver">
          {data.artist} • {formatElapsed(data.elapsed)} / {formatDuration(data.duration)}
        </p>
      </div>
      {/* Play/pause indicator? Maybe just a simple dot */}
      {data.is_playing && (
        <div className="w-2 h-2 bg-silver rounded-full animate-pulse" />
      )}
    </div>
  );
}