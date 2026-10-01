"use client";
import { usePathname } from "next/navigation";
import { Bell, Wifi } from "lucide-react";

const PAGE_TITLES: Record<string, { title: string; subtitle: string }> = {
  "/dashboard":   { title: "Dashboard",          subtitle: "Real-time canal irrigation overview" },
  "/farmers":     { title: "Farmers",            subtitle: "Registered canal users and their profiles" },
  "/emergency":   { title: "Emergency Request",  subtitle: "Submit and track urgent irrigation requests" },
  "/negotiation": { title: "Agent Negotiation",  subtitle: "Live multi-agent reasoning and swap workflow" },
  "/canal":       { title: "Canal Simulation",   subtitle: "Visualise water flow and plot positions" },
  "/credits":     { title: "Water Credits",      subtitle: "Compensated swap ledger and credit history" },
};

export default function TopBar() {
  const pathname = usePathname();
  const page = PAGE_TITLES[pathname] ?? { title: "NeerSetu", subtitle: "Canal Dispatcher" };

  return (
    <header className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between shrink-0">
      <div>
        <h1 className="text-lg font-bold text-slate-900">{page.title}</h1>
        <p className="text-xs text-slate-500">{page.subtitle}</p>
      </div>

      <div className="flex items-center gap-3">
        <div className="flex items-center gap-1.5 text-xs text-farm-600 bg-farm-50 px-3 py-1.5 rounded-full border border-farm-200">
          <Wifi className="w-3 h-3" />
          <span className="font-medium">System Active</span>
        </div>
        <button className="relative w-8 h-8 flex items-center justify-center rounded-xl hover:bg-slate-100 transition">
          <Bell className="w-4 h-4 text-slate-600" />
          <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
        </button>
        <div className="w-8 h-8 rounded-xl bg-water-600 flex items-center justify-center text-white text-xs font-bold">
          AI
        </div>
      </div>
    </header>
  );
}
