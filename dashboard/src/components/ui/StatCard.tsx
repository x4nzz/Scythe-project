import { BladeSlash } from "@/components/BladeSlash";

interface StatCardProps {
  label: string;
  value: string | number;
}

export function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="relative flex flex-col items-center bg-dark-1/50 px-4 py-3 rounded-lg backdrop-blur-sm border border-dark-3/50 hover:border-silver/50 transition-all duration-300">
      <BladeSlash className="absolute inset-0 pointer-events-none" duration={0.6} trigger="hover" />
      <p className="text-xs text-dark-silver mb-1">{label}</p>
      <p className="text-sm font-bold text-white">{value}</p>
    </div>
  );
}