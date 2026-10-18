import type { Metadata } from "next";
import "./globals.css";
import { MotionConfig } from "framer-motion";

export const metadata: Metadata = {
  title: "Scyth Dashboard",
  description: "Modern dark dashboard for Scyth bot",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="h-full antialiased dark">
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet" />
      <MotionConfig transition={{ type: "tween", ease: [0.25, 0.46, 0.45, 0.94] }}>
        <body className="min-h-full flex flex-col">{children}</body>
      </MotionConfig>
    </html>
  );
}
