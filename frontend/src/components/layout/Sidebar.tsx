"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  AlertTriangle,
  GitMerge,
  Waves,
  CreditCard,
  Droplets,
} from "lucide-react";

const nav = [
  { href: "/dashboard", label: "Dashboard",         icon: LayoutDashboard },
  { href: "/farmers",   label: "Farmers",           icon: Users },
  { href: "/emergency", label: "Emergency Request",  icon: AlertTriangle },
  { href: "/negotiation", label: "Agent Negotiation", icon: GitMerge },
  { href: "/canal",     label: "Canal Simulation",  icon: Waves },
  { href: "/credits",   label: "Water Credits",     icon: CreditCard },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-64 bg-gradient-to-b from-water-950 to-water-900 text-white flex flex-col shrink-0">
      {/* Logo */}
      <div className="px-6 py-5 border-b border-water-800">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-water-500 flex items-center justify-center">
            <Droplets className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="font-bold text-lg leading-tight">NeerSetu</div>
            <div className="text-water-300 text-xs">WaterBridge AI</div>
          </div>
        </div>
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || pathname.startsWith(href + "/");
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-150",
                active
                  ? "bg-water-600 text-white shadow-lg shadow-water-900/50"
                  : "text-water-300 hover:bg-water-800 hover:text-white"
              )}
            >
              <Icon className="w-4 h-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-4 border-t border-water-800">
        <div className="text-water-400 text-xs text-center">
          ThinkByte
        </div>
        <div className="text-water-500 text-xs text-center">Canal AI Platform</div>
      </div>
    </aside>
  );
}
