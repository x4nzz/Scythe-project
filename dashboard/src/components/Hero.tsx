import { BladeSlash } from "@/components/BladeSlash";
import { StatCard } from "@/components/ui/StatCard";

export default function Hero() {
  return (
    <section className="relative flex min-h-[60vh] flex-col items-center justify-center gap-6 px-6 pt-20 pb-14 bg-black overflow-hidden">
      {/* Background grid pattern */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22 viewBox=%220 0 100 100%22><path d=%22M0 0 L100 100 M100 0 L0 100%22 stroke=%22%231a1a1a%22 stroke-width=%220.5%22/%22></svg>')] opacity-20 pointer-events-none" />
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
      {/* Live stats bar */}
      <div className="relative z-10 flex flex-wrap gap-4 justify-center mt-10">
        <StatCard label="Servers" value="--" />
        <StatCard label="Users" value="--" />
        <StatCard label="Commands Used" value="--" />
        <StatCard label="Uptime" value="--" />
      </div>
    </section>
  );
}