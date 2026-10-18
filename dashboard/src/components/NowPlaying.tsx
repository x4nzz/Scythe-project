"use client";

import { useState, useEffect } from "react";
import { BladeSlash } from "@/components/BladeSlash";

export default function NowPlaying() {
  const [data, setData] = useState<{
    title: string;
    artist: string;
    uri: string;
    artwork: string;
    duration: number;
    started_at: number;
    is_playing: boolean;
    server_name: string;
  } | null>(null);

  useEffect(() => {
    const fetchNowPlaying = async () => {
      try {
        const res = await fetch("/api/now-playing");
        if (res.ok) {
          const nowPlayingData = await res.json();
          setData(nowPlayingData);
        } else {
          setData(null);
        }
      } catch (e) {
        console.error("Failed to fetch now playing:", e);
        setData(null);
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

  if (!data || !data.is_playing || !data.title) {
    return null;
  }

  // Format duration from seconds to mm:ss
  const formatTime = (seconds: number) => {
    if (!seconds) return "0:00";
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  };

  // Compute elapsed time in seconds
  const elapsed = data.started_at ? Math.floor(Date.now() / 1000 - data.started_at) : 0;
  const progressPercent = data.duration > 0 ? (elapsed / data.duration) * 100 : 0;

  return (
    <div className="relative flex items-center gap-4 bg-dark-2 border border-dark-3 rounded-lg px-4 py-3 hover:border-silver/50 transition-all duration-300">
      <BladeSlash className="absolute inset-0 pointer-events-none" duration={0.6} trigger="hover" />
      <div className="relative z-10 flex-shrink-0">
        {/* Album art */}
        {data.artwork ? (
          <img
            src={data.artwork}
            alt="Album Art"
            className="w-14 h-14 object-cover rounded-none"
          />
        ) : (
          <div className="w-14 h-14 bg-dark-1 flex items-center justify-center rounded-none">
            <div className="text-silver text-xs">🎵</div>
          </div>
        )}
      </div>
      <div className="flex-1 space-y-2">
        <p className="text-xs text-dark-silver">
          Playing in {data.server_name}
        </p>
        <div className="flex items-center gap-2">
          <a
            href={data.uri}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-white underline hover:no-underline"
          >
            {data.title}
          </a>
        </div>
        <p className="text-xs text-dark-silver">{data.artist}</p>
        <div className="flex items-center gap-2 text-xs text-dark-silver">
          <p className="flex-shrink-0">{formatTime(elapsed)}</p>
          <div className="flex-1 h-1 bg-dark-3 rounded">
            <div
              className={`h-full bg-silver rounded transition-all duration-200 w-[${progressPercent}%]`}
            ></div>
          </div>
          <p className="flex-shrink-0">{formatTime(data.duration)}</p>
        </div>
      </div>
    </div>
  );
}