"use client";
import { useEffect, useRef, useState } from "react";
import { getDashboard } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Droplets, Waves, Zap } from "lucide-react";

interface CanalPlot {
  position: number;
  plot: string;
  farmer: string;
  eta: number;
  flow_percent: number;
}

export default function CanalPage() {
  const [plots, setPlots] = useState<CanalPlot[]>([]);
  const [loading, setLoading] = useState(true);
  const [animating, setAnimating] = useState(false);
  const [waterPos, setWaterPos] = useState(0);
  const [highlight, setHighlight] = useState<number | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    getDashboard()
      .then((d) => setPlots(d.canal_flow))
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  function startAnimation() {
    setAnimating(true);
    setWaterPos(0);
    setHighlight(null);
    let pos = 0;
    intervalRef.current = setInterval(() => {
      pos += 1;
      setWaterPos(pos);
      // highlight plot when water reaches it
      const plotIdx = Math.floor((pos / 100) * plots.length);
      setHighlight(plotIdx < plots.length ? plotIdx : null);
      if (pos >= 100) {
        clearInterval(intervalRef.current!);
        setAnimating(false);
        setHighlight(null);
      }
    }, 40);
  }

  useEffect(() => () => { if (intervalRef.current) clearInterval(intervalRef.current); }, []);

  if (loading) return <div className="animate-pulse h-96 bg-slate-200 rounded-2xl" />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Canal Visualization */}
      <div className="card overflow-hidden">
        <div className="card-header flex items-center justify-between">
          <div className="font-semibold text-slate-800 flex items-center gap-2">
            <Waves className="w-4 h-4 text-water-600" />
            Canal Simulation — Flow Reduction Downstream
          </div>
          <button
            onClick={startAnimation}
            disabled={animating}
            className="btn-primary flex items-center gap-2 text-sm"
          >
            <Droplets className="w-4 h-4" />
            {animating ? "Flowing…" : "Simulate Flow"}
          </button>
        </div>

        <div className="p-8">
          {/* Canal body */}
          <div className="relative">
            {/* Main canal trunk */}
            <div className="flex items-stretch">
              {/* Source label */}
              <div className="flex flex-col items-center justify-center pr-4">
                <div className="w-16 h-12 bg-water-600 rounded-xl flex flex-col items-center justify-center text-white text-xs font-bold">
                  <Droplets className="w-4 h-4 mb-0.5" />
                  SOURCE
                </div>
                <div className="w-1 flex-1 bg-water-500 mt-1" />
              </div>

              {/* Trunk + branches */}
              <div className="flex-1">
                {/* Water flow pipe */}
                <div className="relative h-8 bg-gradient-to-r from-water-600 to-water-300 rounded-full overflow-hidden mb-6 shadow-lg">
                  {/* Animated water blob */}
                  {animating && (
                    <div
                      className="absolute inset-y-1 w-16 bg-white/40 rounded-full blur-sm transition-none"
                      style={{ left: `calc(${waterPos}% - 32px)` }}
                    />
                  )}
                  {/* Flow direction arrows */}
                  <div className="absolute inset-0 flex items-center justify-around px-4">
                    {[...Array(8)].map((_, i) => (
                      <span key={i} className="text-white/60 text-xs">›</span>
                    ))}
                  </div>
                </div>

                {/* Plot branches */}
                <div className="grid grid-cols-3 lg:grid-cols-6 gap-4">
                  {plots.map((plot, idx) => (
                    <PlotCard
                      key={plot.position}
                      plot={plot}
                      idx={idx}
                      highlight={highlight === idx}
                      waterPos={waterPos}
                    />
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Flow Loss Explainer */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="card-header font-semibold text-slate-800">Flow Efficiency (η) by Position</div>
          <div className="card-body space-y-4">
            {plots.map((plot) => (
              <div key={plot.position}>
                <div className="flex justify-between text-sm mb-1.5">
                  <div className="flex items-center gap-2">
                    <div className={cn(
                      "w-3 h-3 rounded-full",
                      plot.eta >= 0.9 ? "bg-farm-500"
                      : plot.eta >= 0.8 ? "bg-yellow-400"
                      : plot.eta >= 0.7 ? "bg-orange-400"
                      : "bg-red-500",
                    )} />
                    <span className="font-medium text-slate-700">{plot.plot}</span>
                    <span className="text-slate-500 text-xs">— {plot.farmer.split(" ")[0]}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Position #{plot.position}</span>
                    <span className="font-bold text-slate-800">η = {plot.eta.toFixed(2)}</span>
                  </div>
                </div>
                <div className="flow-bar h-3">
                  <div
                    className={cn(
                      "flow-fill h-full rounded-full transition-all duration-1000",
                      plot.eta >= 0.9 ? "bg-farm-500"
                      : plot.eta >= 0.8 ? "bg-yellow-400"
                      : plot.eta >= 0.7 ? "bg-orange-400"
                      : "bg-red-500",
                    )}
                    style={{ width: `${plot.flow_percent}%` }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Why flow decreases */}
        <div className="card">
          <div className="card-header font-semibold text-slate-800 flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-500" />
            Why Flow Decreases Downstream
          </div>
          <div className="card-body space-y-4 text-sm text-slate-600">
            <p>
              Canal water loses usable volume as it travels downstream due to:
            </p>
            <ul className="space-y-2">
              {[
                ["Seepage losses", "Water absorbs into unlined canal banks"],
                ["Evaporation", "Open surface water evaporates, especially in summer"],
                ["Upstream extraction", "Each upstream user reduces volume for downstream"],
                ["Head losses", "Friction and turbulence reduce flow velocity"],
              ].map(([cause, desc]) => (
                <li key={cause} className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-water-500 mt-1.5 shrink-0" />
                  <div>
                    <span className="font-medium text-slate-800">{cause}: </span>
                    {desc}
                  </div>
                </li>
              ))}
            </ul>
            <div className="bg-water-50 border border-water-200 rounded-xl p-4 mt-4">
              <div className="font-semibold text-water-800 mb-1">NeerSetu's Solution</div>
              <p className="text-water-700">
                NeerSetu accounts for η when computing swaps. Downstream farmers
                receive <strong>more compensated hours</strong> to offset their flow disadvantage.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Plot Card ────────────────────────────────────────────────────────────────

function PlotCard({
  plot, idx, highlight, waterPos,
}: { plot: CanalPlot; idx: number; highlight: boolean; waterPos: number }) {
  const flowColor =
    plot.eta >= 0.9 ? "border-farm-400 bg-farm-50"
    : plot.eta >= 0.8 ? "border-yellow-400 bg-yellow-50"
    : plot.eta >= 0.7 ? "border-orange-400 bg-orange-50"
    : "border-red-400 bg-red-50";

  const dotColor =
    plot.eta >= 0.9 ? "bg-farm-500"
    : plot.eta >= 0.8 ? "bg-yellow-500"
    : plot.eta >= 0.7 ? "bg-orange-500"
    : "bg-red-500";

  return (
    <div className={cn(
      "relative border-2 rounded-2xl p-3 transition-all duration-300",
      flowColor,
      highlight && "scale-105 shadow-lg ring-2 ring-water-400",
    )}>
      {/* Branch connector line */}
      <div className="absolute -top-6 left-1/2 transform -translate-x-1/2 w-0.5 h-6 bg-water-400" />

      {/* Flow dot */}
      <div className={cn(
        "w-3 h-3 rounded-full mx-auto mb-2",
        dotColor,
        highlight && "animate-ping",
      )} />

      <div className="text-center">
        <div className="font-bold text-xs text-slate-800">{plot.plot}</div>
        <div className="text-xs text-slate-500 mt-0.5">{plot.farmer.split(" ")[0]}</div>
        <div className="text-xs font-bold text-slate-700 mt-1">η={plot.eta.toFixed(2)}</div>
        <div className="mt-2 h-1.5 bg-white/60 rounded-full">
          <div
            className={cn("h-full rounded-full transition-all duration-500", dotColor)}
            style={{ width: `${plot.flow_percent}%` }}
          />
        </div>
        <div className="text-xs text-slate-500 mt-1">{plot.flow_percent}%</div>
      </div>
    </div>
  );
}
