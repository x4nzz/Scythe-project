import Hero from "@/components/Hero";
import FeatureGrid from "@/components/FeatureGrid";
import CommandBrowser from "@/components/CommandBrowser";
import NowPlaying from "@/components/NowPlaying";

export default function Home() {
  return (
    <main className="min-h-screen bg-black">
      <Hero />
      <FeatureGrid />
      <CommandBrowser />
      <NowPlaying className="fixed bottom-4 left-4 right-4 max-w-md mx-auto" />
    </main>
  );
}
