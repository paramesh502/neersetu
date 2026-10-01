"use client";
import { useEffect, useState } from "react";
import { getFarmers } from "@/lib/api";
import { Farmer } from "@/types";
import { cn, fwosColor } from "@/lib/utils";
import { compute_fwos_client } from "@/lib/fairness";
import {
  User, Droplets, Wheat, MapPin, TrendingDown,
  Award, ChevronDown, ChevronUp,
} from "lucide-react";

export default function FarmersPage() {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    getFarmers()
      .then(setFarmers)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <FarmersSkeleton />;

  return (
    <div className="space-y-6 animate-fade-in">
      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-5">
        {farmers.map((farmer) => {
          const fwos = compute_fwos_client(
            farmer.canal_position, farmer.flow_efficiency_index,
            farmer.historical_deficit, farmer.missed_turns, "medium",
          );
          const isOpen = expanded === farmer.id;
          return (
            <div key={farmer.id} className={cn("card overflow-hidden transition-all", isOpen && "ring-2 ring-water-300")}>
              {/* Header stripe */}
              <div className="h-2 bg-gradient-to-r from-water-500 to-farm-500"
                style={{ opacity: farmer.flow_efficiency_index }} />

              <div className="p-5">
                {/* Top row */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className="w-11 h-11 rounded-xl bg-gradient-to-br from-water-100 to-farm-100 flex items-center justify-center font-bold text-water-700">
                      {farmer.farmer_id}
                    </div>
                    <div>
                      <div className="font-semibold text-slate-900">{farmer.name}</div>
                      <div className="text-xs text-slate-500 flex items-center gap-1">
                        <MapPin className="w-3 h-3" />
                        {farmer.plot_number} · Position #{farmer.canal_position}
                      </div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className={cn("text-2xl font-bold", fwosColor(fwos))}>{fwos}</div>
                    <div className="text-xs text-slate-400">FWOS</div>
                  </div>
                </div>

                {/* Crop & Eta */}
                <div className="flex items-center gap-2 mb-4">
                  <span className="badge bg-farm-100 text-farm-700 flex items-center gap-1">
                    <Wheat className="w-3 h-3" />
                    {farmer.crop_type}
                  </span>
                  <EtaBadge eta={farmer.flow_efficiency_index} />
                </div>

                {/* Flow bar */}
                <div className="mb-4">
                  <div className="flex justify-between text-xs text-slate-500 mb-1">
                    <span>Flow Efficiency (η)</span>
                    <span className="font-semibold">{Math.round(farmer.flow_efficiency_index * 100)}%</span>
                  </div>
                  <div className="flow-bar">
                    <div className="flow-fill" style={{ width: `${farmer.flow_efficiency_index * 100}%` }} />
                  </div>
                </div>

                {/* Stats row */}
                <div className="grid grid-cols-3 gap-2 mb-3">
                  <MiniStat label="Credit" value={`${farmer.water_credit_balance.toFixed(1)}h`} color="text-farm-600" />
                  <MiniStat label="Deficit" value={`${farmer.historical_deficit.toFixed(1)}h`} color="text-red-500" />
                  <MiniStat label="Missed" value={farmer.missed_turns} color="text-orange-500" />
                </div>

                {/* Expand toggle */}
                <button
                  onClick={() => setExpanded(isOpen ? null : farmer.id)}
                  className="w-full text-xs text-water-600 hover:text-water-700 flex items-center justify-center gap-1 pt-2 border-t border-slate-100"
                >
                  {isOpen ? <><ChevronUp className="w-3 h-3" />Less</> : <><ChevronDown className="w-3 h-3" />More details</>}
                </button>

                {/* Expanded */}
                {isOpen && (
                  <div className="mt-3 pt-3 border-t border-slate-100 space-y-2 animate-fade-in">
                    <DetailRow label="Phone" value={farmer.phone} />
                    <DetailRow label="Hours Allocated" value={`${farmer.total_hours_allocated.toFixed(1)} hrs`} />
                    <DetailRow label="Hours Used" value={`${farmer.total_hours_used.toFixed(1)} hrs`} />
                    <DetailRow
                      label="Efficiency Ratio"
                      value={farmer.total_hours_allocated > 0
                        ? `${Math.round((farmer.total_hours_used / farmer.total_hours_allocated) * 100)}%`
                        : "N/A"}
                    />
                    <FWOSBreakdownView
                      canPos={farmer.canal_position}
                      eta={farmer.flow_efficiency_index}
                      deficit={farmer.historical_deficit}
                      missed={farmer.missed_turns}
                    />
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── Sub-components ───────────────────────────────────────────────────────────

function EtaBadge({ eta }: { eta: number }) {
  const pct = Math.round(eta * 100);
  const cls = pct >= 90 ? "bg-farm-100 text-farm-700"
    : pct >= 75 ? "bg-yellow-100 text-yellow-700"
    : "bg-red-100 text-red-700";
  return (
    <span className={cn("badge flex items-center gap-1", cls)}>
      <Droplets className="w-3 h-3" />
      η = {eta.toFixed(2)}
    </span>
  );
}

function MiniStat({ label, value, color }: { label: string; value: string | number; color: string }) {
  return (
    <div className="bg-slate-50 rounded-lg p-2 text-center">
      <div className={cn("font-bold text-sm", color)}>{value}</div>
      <div className="text-xs text-slate-400">{label}</div>
    </div>
  );
}

function DetailRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-xs">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-700">{value}</span>
    </div>
  );
}

function FWOSBreakdownView({
  canPos, eta, deficit, missed,
}: { canPos: number; eta: number; deficit: number; missed: number }) {
  const components = [
    { label: "Downstream Penalty", score: ((canPos - 1) / 5) * 30, max: 30 },
    { label: "Efficiency Deficit", score: (1 - eta) * 20, max: 20 },
    { label: "Historical Deficit", score: Math.min(deficit / 5, 1) * 25, max: 25 },
    { label: "Missed Turns", score: Math.min(missed / 5, 1) * 15, max: 15 },
    { label: "Crop Urgency", score: 5, max: 10 },
  ];

  return (
    <div className="mt-2 bg-slate-50 rounded-xl p-3">
      <div className="text-xs font-semibold text-slate-600 mb-2">FWOS Breakdown</div>
      {components.map((c) => (
        <div key={c.label} className="mb-1.5">
          <div className="flex justify-between text-xs mb-0.5">
            <span className="text-slate-500">{c.label}</span>
            <span className="font-medium">{c.score.toFixed(1)}/{c.max}</span>
          </div>
          <div className="h-1.5 bg-slate-200 rounded-full">
            <div
              className="h-full bg-water-500 rounded-full transition-all duration-700"
              style={{ width: `${(c.score / c.max) * 100}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

function FarmersSkeleton() {
  return (
    <div className="grid grid-cols-3 gap-5 animate-pulse">
      {[...Array(6)].map((_, i) => <div key={i} className="h-64 bg-slate-200 rounded-2xl" />)}
    </div>
  );
}
