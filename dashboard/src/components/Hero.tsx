"use client";

import { useState, useEffect } from "react";
import { BladeSlash } from "@/components/BladeSlash";
import { StatCard } from "@/components/ui/StatCard";
import NowPlaying from "./NowPlaying";

export default function Hero() {
  const [stats, setStats] = useState({ servers: 0, users: 0, commands_used: 0, uptime: 0 });

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await fetch("/api/stats");
        if (res.ok) {
          const data = await res.json();
          setStats(data);
        }
      } catch (e) {
        console.error("Failed to fetch stats:", e);
      }
    };

    // Fetch immediately
    fetchStats();

    // Set interval to update every 5 seconds
    const interval = setInterval(() => {
      fetchStats();
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <section className="relative flex min-h-[60vh] flex-col items-center justify-center gap-6 px-6 pt-20 pb-14 bg-black overflow-hidden">
      {/* Blade slash animation on hero - sweeps on mount */}
      <BladeSlash className="absolute inset-0 pointer-events-none" duration={0.6} trigger="mount" />
      {/* Title with slash animation */}
      <div className="relative z-10 text-center">
        {/* Blade slash on hover over title */}
        <BladeSlash className="absolute inset-0 pointer-events-none" duration={0.6} trigger="hover" />
        <h1 className="font-display text-5xl md:text-6xl lg:text-7xl text-white tracking-tighter">
          SCYTH
        </h1>
        <p className="mt-4 text-lg md:text-xl text-dark-silver max-w-md font-mono">
          Moderation • Music • Utilities
        </p>
        <div className="mt-8 flex flex-wrap gap-4 justify-center">
          <a
            href="https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=0"
            className="flex h-12 px-6 items-center justify-center gap-2 rounded-none bg-white text-black font-medium border border-white/20 hover:border-silver/50 transition-all duration-300"
          >
            Add to Discord
          </a>
          <a
            href="/commands"
            className="flex h-12 px-6 items-center justify-center gap-2 rounded-none border border-dark-3/50 bg-transparent text-white font-medium hover:bg-dark-1/50 transition-all duration-300"
          >
            Commands
          </a>
        </div>
      </div>
      {/* Now Playing Card */}
      <NowPlaying />
      {/* Live stats bar */}
      <div className="relative z-10 flex flex-wrap gap-4 justify-center mt-10">
        <StatCard label="Servers" value={stats.servers} />
        <StatCard label="Users" value={stats.users} />
        <StatCard label="Commands Used" value={stats.commands_used} />
        <StatCard label="Uptime" value={`${stats.uptime.toFixed(1)}%`} />
      </div>
    </section>
  );
}