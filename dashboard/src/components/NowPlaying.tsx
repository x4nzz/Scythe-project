import { BladeSlash } from "@/components/BladeSlash";

export default function NowPlaying() {
  // Placeholder data - in a real implementation, this would come from the bot's state or an API
  const placeholderData = {
    title: "Never Gonna Give You Up",
    artist: "Rick Astley",
    duration: "3:33"
  };

  return (
    <div className="relative flex items-center gap-4 bg-dark-2 border border-dark-3 rounded-none px-4 py-3 hover:border-silver/50 transition-all duration-300">
      <BladeSlash className="absolute inset-0 pointer-events-none" duration={0.6} trigger="hover" />
      <div className="relative z-10 flex-shrink-0">
        {/* Placeholder for album art */}
        <div className="w-12 h-12 bg-dark-1 flex items-center justify-center rounded-none">
          <div className="text-silver text-xs">🎵</div>
        </div>
      </div>
      <div className="flex-1 space-y-1">
        <p className="text-sm font-medium text-white">{placeholderData.title}</p>
        <p className="text-xs text-dark-silver">
          {placeholderData.artist} • {placeholderData.duration}
        </p>
      </div>
    </div>
  );
}