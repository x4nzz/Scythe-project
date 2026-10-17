import {
  ShieldCheck,
  Music,
  Terminal,
  Bot,
  Command
} from "lucide-react";

export default function FeatureGrid() {
  const features = [
    {
      name: "Moderation",
      icon: ShieldCheck,
      description: "Advanced moderation tools to keep your server safe and clean."
    },
    {
      name: "Music",
      icon: Music,
      description: "High-quality music playback with support for multiple sources."
    },
    {
      name: "Utility",
      icon: Terminal,
      description: "Useful utility commands for server management and fun."
    },
    {
      name: "Auto-Mod",
      icon: Bot,
      description: "Automatic moderation to handle common issues without intervention."
    },
    {
      name: "Custom Commands",
      icon: Command,
      description: "Create and manage custom commands tailored to your server's needs."
    }
  ];

  return (
    <section className="py-16 bg-black">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="text-center text-3xl font-bold text-white mb-12">
          Features
        </h2>
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <div
              key={feature.name}
              className="relative flex h-[180px] w-full items-center justify-center px-4 py-6 bg-gray-900/50 backdrop-blur-sm border border-gray-800/50 hover:border-gray-600 transition-all duration-300"
            >
              <div className="flex flex-col items-center gap-4 text-center">
                <feature.icon className="h-8 w-8 text-gray-300 transition-colors duration-300" />
                <h3 className="text-lg font-semibold text-white">{feature.name}</h3>
                <p className="text-sm text-gray-400">{feature.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}