"use client";
import { motion } from "framer-motion";

interface BladeSlashProps {
  className?: string;
  duration?: number;
  trigger?: "mount" | "hover";
}

export function BladeSlash({ className = "", duration = 0.6, trigger = "mount" }: BladeSlashProps) {
  const variants = {
    hidden: { x: "-100%", opacity: 0 },
    visible: { x: "100%", opacity: 1 },
    exit: { x: "100%", opacity: 0 },
  };

  return (
    <motion.div
      data-testid="blade-slash"
      className={`absolute inset-0 bg-[linear-gradient(135deg,transparent_48%,rgba(255,255,255,0.12)_50%,transparent_52%)] pointer-events-none ${className}`}
      initial={trigger === "mount" ? "hidden" : "visible"}
      animate={trigger === "mount" ? "visible" : "visible"}
      exit="exit"
      variants={variants}
      transition={{ duration, ease: [0.25, 0.46, 0.45, 0.94] }}
    />
  );
}