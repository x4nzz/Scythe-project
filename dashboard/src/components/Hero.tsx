import { motion } from "framer-motion";

export default function Hero() {
  return (
    <section className="relative flex min-h-[60vh] flex-col items-center justify-center gap-6 px-6 pt-20 pb-14 bg-black overflow-hidden">
      {/* Background grid pattern */}
      <div className="absolute inset-0 bg-[url('data:image/svg+xml;utf8,<svg xmlns=%22http://www.w3.org/2000/svg%22 width=%22100%22 height=%22100%22 viewBox=%220 0 100 100%22><path d=%22M0 0 L100 100 M100 0 L0 100%22 stroke=%22%231a1a1a%22 stroke-width=%220.5%22/%22></svg>')] opacity-20 pointer-events-none" />
      {/* Blade slash animation on hero */}
      <motion.div
        className="absolute inset-0 bg-[linear-gradient(to_bottom_right,transparent,rgba(255,255,255,0.05),transparent)] blur-3xl"
        initial={{ x: "-100%" }}
        animate={{ x: "100%" }}
        transition={{ duration: 3, repeat: Infinity, ease: "linear" }}
      />
      {/* Title with slash animation */}
      <div className="relative z-10 text-center">
        <motion.h1
          className="font-bold text-5xl md:text-6xl lg:text-7xl text-white tracking-tighter"
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ duration: 0.8, ease: "easeOut" }}
        >
          SCYTH
        </motion.h1>
        <p className="mt-4 text-lg md:text-xl text-gray-300 max-w-md">
          Moderation • Music • Utilities
        </p>
        <div className="mt-8 flex flex-wrap gap-4 justify-center">
          <a
            href="https://discord.com/oauth2/authorize?client_id=YOUR_CLIENT_ID&scope=bot&permissions=0"
            className="flex h-12 px-6 items-center justify-center gap-2 rounded-lg bg-white text-black font-medium transition-all hover:bg-gray-50"
          >
            Add to Discord
          </a>
          <a
            href="/commands"
            className="flex h-12 px-6 items-center justify-center gap-2 rounded-lg border border-gray-300 bg-transparent text-gray-100 font-medium transition-all hover:bg-gray-800 hover:border-gray-600"
          >
            Commands
          </a>
        </div>
      </div>
      {/* Live stats bar */}
      <div className="relative z-10 flex flex-wrap gap-4 justify-center mt-10">
        <div className="flex flex-col items-center bg-gray-900/50 px-6 py-4 rounded-lg backdrop-blur-sm border border-gray-800/50">
          <p className="text-sm text-gray-400">Servers</p>
          <p className="mt-1 text-2xl font-bold text-white">1,234</p>
        </div>
        <div className="flex flex-col items-center bg-gray-900/50 px-6 py-4 rounded-lg backdrop-blur-sm border border-gray-800/50">
          <p className="text-sm text-gray-400">Users</p>
          <p className="mt-1 text-2xl font-bold text-white">12,345</p>
        </div>
        <div className="flex flex-col items-center bg-gray-900/50 px-6 py-4 rounded-lg backdrop-blur-sm border border-gray-800/50">
          <p className="text-sm text-gray-400">Commands Used</p>
          <p className="mt-1 text-2xl font-bold text-white">54,321</p>
        </div>
        <div className="flex flex-col items-center bg-gray-900/50 px-6 py-4 rounded-lg backdrop-blur-sm border border-gray-800/50">
          <p className="text-sm text-gray-400">Uptime</p>
          <p className="mt-1 text-2xl font-bold text-white">99.9%</p>
        </div>
      </div>
    </section>
  );
}