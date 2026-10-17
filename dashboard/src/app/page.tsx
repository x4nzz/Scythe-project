import Hero from "@/components/Hero";
import FeatureGrid from "@/components/FeatureGrid";
import CommandBrowser from "@/components/CommandBrowser";

export default function Home() {
  return (
    <main className="min-h-screen bg-black text-white">
      <Hero />
      <FeatureGrid />
      <CommandBrowser />
    </main>
  );
}
