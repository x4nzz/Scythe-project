import { useState } from "react";

const commandsData = [
  { category: "Admin", name: ";ban", description: "Ban a member from the server." },
  { category: "Admin", name: ";kick", description: "Kick a member from the server." },
  { category: "Admin", name: ";mute", description: "Mute a member in the server." },
  { category: "Admin", name: ";unmute", description: "Unmute a member in the server." },
  { category: "Admin", name: ";warn", description: "Warn a member." },
  { category: "Fun", name: ";8ball", description: "Ask the magic 8-ball a question." },
  { category: "Fun", name: ";joke", description: "Tell a random joke." },
  { category: "Fun", name: ";meme", description: "Fetch a random meme." },
  { category: "Music", name: ";play", description: "Play a song from YouTube or Spotify." },
  { category: "Music", name: ";skip", description: "Skip the current song." },
  { category: "Music", name: ";queue", description: "View the current queue." },
  { category: "Music", name: ";stop", description: "Stop the music and clear the queue." },
  { category: "Config", name: ";prefix", description: "Change the bot's prefix." },
  { category: "Config", name: ";setlog", description: "Set the logging channel." },
  { category: "Config", name: ";setwelcome", description: "Set the welcome message." },
];

export default function CommandBrowser() {
  const [search, setSearch] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");

  const categories = ["All", ...new Set(commandsData.map((cmd) => cmd.category))];

  const filteredCommands = commandsData
    .filter((cmd) => {
      if (selectedCategory !== "All" && cmd.category !== selectedCategory) return false;
      if (search) {
        const lowerSearch = search.toLowerCase();
        return (
          cmd.name.toLowerCase().includes(lowerSearch) ||
          cmd.description.toLowerCase().includes(lowerSearch)
        );
      }
      return true;
    })
    .sort((a, b) => a.name.localeCompare(b.name));

  return (
    <section className="py-16 bg-black">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="text-center text-3xl font-bold text-white mb-12">
          Command Browser
        </h2>
        <div className="mb-8">
          <input
            type="text"
            placeholder="Search commands..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full px-4 py-2 bg-gray-900/50 border border-gray-800/50 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-white/20 backdrop-blur-sm"
          />
        </div>
        <div className="mb-6 flex flex-wrap gap-2">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-4 py-2 bg-gray-900/50 border border-gray-800/50 rounded-lg text-sm font-medium ${
                selectedCategory === category
                  ? "text-white border-white/20"
                  : "text-gray-300 hover:bg-gray-800/50 hover:text-white"
              } transition-colors`}
            >
              {category}
            </button>
          ))}
        </div>
        <div className="space-y-4">
          {filteredCommands.length > 0 ? (
            filteredCommands.map((cmd) => (
              <div
                key={`${cmd.category}-${cmd.name}`}
                className="flex w-full items-start gap-4 bg-gray-900/50 px-4 py-3 rounded-lg border border-gray-800/50 hover:border-gray-600 transition-colors duration-200"
              >
                <span className="flex-shrink-0 text-gray-400">{cmd.name}</span>
                <div className="flex-1 space-y-1">
                  <p className="text-sm font-medium text-white">{cmd.description}</p>
                  <span className="text-xs text-gray-500">{cmd.category}</span>
                </div>
              </div>
            ))
          ) : (
            <p className="text-center text-gray-400 py-8">No commands found.</p>
          )}
        </div>
      </div>
    </section>
  );
}