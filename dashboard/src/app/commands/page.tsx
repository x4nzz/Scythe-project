import CommandBrowser from "@/components/CommandBrowser";
import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Commands - Scyth Dashboard",
  description: "Browse all available Scyth bot commands",
};

export default function CommandsPage() {
  return (
    <div className="min-h-screen bg-black">
      <CommandBrowser />
    </div>
  );
}