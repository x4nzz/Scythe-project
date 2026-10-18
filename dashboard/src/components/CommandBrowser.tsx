"use client";

import { useState } from "react";
import { COMMAND_SYNTAX } from "@/lib/commands";
import { BladeSlash } from "@/components/BladeSlash";

export default function CommandBrowser() {
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("Admin");

  // Convert COMMAND_SYNTAX to array format for easier filtering
  const commandsData = Object.entries(COMMAND_SYNTAX).map(([name, data]) => ({
    name,
    ...data,
  }));

  // Extract categories from command data
  const categories = [
    "All",
    ...Array.from(new Set(commandsData.map((cmd) =>
      cmd.desc.split(" ")[0] // Extract first word as category approximation
    ))).filter(Boolean)
  ];

  // For better category mapping, let's use predefined categories based on main.py
  const predefinedCategories = ["Admin", "Fun", "Music", "Config"];

  const filteredCommands = commandsData
    .filter((cmd) => {
      // Filter by category (simplified mapping)
      const categoryMatch =
        (selectedCategory === "Admin" && ["ban", "kick", "timeout", "warn", "purge", "nuke", "voicemaster", "serverinfo", "channelinfo", "userinfo", "snipe", "editsnipe", "afk", "jail", "unjail", "strip", "restore", "hardban", "tempban", "softban", "fakeperms", "autoresponder", "role", "prefix"].includes(cmd.name)) ||
        (selectedCategory === "Fun" && ["8ball", "joke", "meme"].includes(cmd.name)) ||
        (selectedCategory === "Music" && ["play", "playnext", "queue", "volume", "autoplay", "stop", "pause", "resume"].includes(cmd.name)) ||
        (selectedCategory === "Config" && ["prefix"].includes(cmd.name));

      if (!categoryMatch) return false;

      // Filter by search
      if (search) {
        const lowerSearch = search.toLowerCase();
        return (
          cmd.name.toLowerCase().includes(lowerSearch) ||
          cmd.desc.toLowerCase().includes(lowerSearch)
        );
      }
      return true;
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <section className="py-16 bg-black">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="text-center text-3xl font-display text-white mb-12">
          Command Browser
        </h2>
        <div className="mb-6">
          <input
            type="text"
            placeholder="Search commands..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-4 py-3 bg-dark-1 border border-dark-2 rounded-none text-white placeholder-dark-silver focus-2 focus:border-silver/50 focus:ring-silver/50"
          />
        </div>
        <div className="mb-6 flex flex-wrap gap-2">
          {predefinedCategories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-3 bg-dark-2 border border-dark-3 rounded-none text-sm font-medium ${
                selectedCategory === category
                  ? "text-white border-silver/50 bg-dark-1/50"
                  : "text-dark-silver hover:bg-dark-1/50"
              } transition-colors duration-300`}
            >
              {category}
            </button>
          ))}
        </div>
        <div className="space-y-4">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((cmd) => (
              <div
                key={cmd.name}
                className="relative flex w-full items-start gap-4 bg-dark-2 border border-dark-3 rounded-none hover:border-silver/50 transition-all duration-300"
              >
                <BladeSlash className="absolute inset-0 pointer-events-none" duration={0.6} trigger="hover" />
                <div className="relative z-10 flex flex-col items-start gap-3 text-left w-full">
                  <div className="flex items-start gap-3">
                    <span className="flex-shrink-0 font-mono text-silver">{`;${cmd.name}`}</span>
                    <div className="flex-1 space-y-1">
                      <p className="text-sm font-medium text-white">{cmd.desc}</p>
                      {cmd.aliases && cmd.aliases.length > 0 && (
                        <p className="text-xs font-mono text-dark-silver">
                          {cmd.aliases.join(', ')}
                        </p>
                      )}
                      <p className="text-xs font-mono text-dark-silver">
                        {cmd.usage?.[0] ?? ""}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-dark-silver py-8">No commands found.</p>
          )}
        </div>
      </div>
    </section>
  );
}