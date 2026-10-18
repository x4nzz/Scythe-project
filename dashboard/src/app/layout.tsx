import type { Metadata } from "next";
import "./globals.css";
import { MotionConfig } from "framer-motion";
import Head from "next/head";

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
    <html lang="en" className="h-full antialiased dark" style={{ touchAction: "manipulation" }}>
      <Head>
        <meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no" />
      </Head>
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&display=swap" rel="stylesheet" />
      <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;700&display=swap" rel="stylesheet" />
      <div className="fixed inset-0 bg-grid-pattern pointer-events-none" />
      <MotionConfig transition={{ type: "tween", ease: [0.25, 0.46, 0.45, 0.94] }}>
        <body className="min-h-full flex flex-col" style={{ touchAction: "manipulation" }}>{children}</body>
      </MotionConfig>
    </html>
  );
}
