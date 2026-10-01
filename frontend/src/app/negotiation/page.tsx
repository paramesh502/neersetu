"use client";
import { useEffect, useState } from "react";
import { getNegotiations } from "@/lib/api";
import { Negotiation, AgentStep } from "@/types";
import { cn, formatDate, statusColor } from "@/lib/utils";
import {
  GitMerge, ChevronDown, ChevronUp, CheckCircle2,
  AlertCircle, Loader, ArrowRight, Zap,
} from "lucide-react";

const AGENT_COLORS: Record<string, { bg: string; dot: string; icon: string }> = {
  "Intake Agent":           { bg: "bg-sky-50 border-sky-200",    dot: "bg-sky-500 text-white",    icon: "📥" },
  "Flow & Fairness Agent":  { bg: "bg-yellow-50 border-yellow-200", dot: "bg-yellow-500 text-white", icon: "⚖️" },
  "Negotiation Agent":      { bg: "bg-purple-50 border-purple-200", dot: "bg-purple-500 text-white", icon: "🤝" },
  "Consent Agent":          { bg: "bg-green-50 border-green-200",  dot: "bg-green-500 text-white",  icon: "✅" },
  "Ledger Agent":           { bg: "bg-orange-50 border-orange-200", dot: "bg-orange-500 text-white", icon: "📒" },
  "Dispatcher Agent":       { bg: "bg-pink-50 border-pink-200",   dot: "bg-pink-500 text-white",   icon: "📡" },
};

export default function NegotiationPage() {
  const [negotiations, setNegotiations] = useState<Negotiation[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<number | null>(null);

  useEffect(() => {
    getNegotiations()
      .then(setNegotiations)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="animate-pulse space-y-4">{[...Array(3)].map((_, i) => <div key={i} className="h-40 bg-slate-200 rounded-2xl" />)}</div>;

  if (negotiations.length === 0) {
    return (
      <div className="card p-16 text-center text-slate-400">
        <GitMerge className="w-12 h-12 mx-auto mb-3 opacity-30" />
        <div className="font-medium">No negotiations yet.</div>
        <div className="text-sm mt-1">Submit an emergency request to start the agent pipeline.</div>
      </div>
    );
  }

  return (
    <div className="space-y-5 animate-fade-in">
      {negotiations.map((neg) => {
        const isOpen = expanded === neg.id;
        return (
          <div key={neg.id} className={cn("card overflow-hidden", isOpen && "ring-2 ring-purple-300")}>
            {/* Header */}
            <div
              className="px-6 py-4 flex items-center justify-between cursor-pointer hover:bg-slate-50 transition"
              onClick={() => setExpanded(isOpen ? null : neg.id)}
            >
              <div className="flex items-center gap-4">
                <div className="w-10 h-10 rounded-xl bg-purple-100 flex items-center justify-center text-purple-700 font-bold">
                  #{neg.id}
                </div>
                <div>
                  <div className="font-semibold text-slate-900">
                    {neg.requesting_farmer_name ?? "Farmer"} → {neg.yielding_farmer_name ?? "Farmer"}
                  </div>
                  <div className="text-xs text-slate-500">
                    {neg.requesting_farmer_plot} ← {neg.yielding_farmer_plot} · {formatDate(neg.created_at)}
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <SwapBadge yielded={neg.hours_yielded} compensation={neg.compensation_hours} />
                <span className={cn("badge", statusColor(neg.status))}>{neg.status}</span>
                {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
              </div>
            </div>

            {/* Expanded */}
            {isOpen && (
              <div className="border-t border-slate-100 animate-fade-in">
                <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
                  {/* Swap card */}
                  <div>
                    <div className="font-semibold text-sm text-slate-700 mb-3">Swap Details</div>
                    <div className="bg-slate-50 rounded-xl p-4 space-y-2">
                      <SwapRow label="Hours Requested" value={`${neg.hours_requested} hrs`} />
                      <SwapRow label="Hours Yielded" value={`${neg.hours_yielded} hrs`} />
                      <div className="border-t border-slate-200 my-2" />
                      <div className="bg-water-50 border border-water-200 rounded-lg p-3">
                        <div className="text-xs font-semibold text-water-700 mb-1">Compensation Formula</div>
                        <div className="font-mono text-xs text-water-900">
                          {neg.hours_yielded} × (η={neg.yielding_farmer_eta.toFixed(2)} ÷ η={neg.receiving_farmer_eta.toFixed(2)})
                        </div>
                        <div className="font-mono text-lg font-bold text-water-700 mt-1">
                          = {neg.compensation_hours} hrs
                        </div>
                      </div>
                    </div>

                    {/* Proposal text */}
                    <div className="mt-3 bg-purple-50 border border-purple-200 rounded-xl p-4 text-xs text-slate-700 whitespace-pre-line leading-relaxed">
                      {neg.proposal_text}
                    </div>
                  </div>

                  {/* Agent steps timeline */}
                  {neg.agent_steps && neg.agent_steps.length > 0 && (
                    <div>
                      <div className="font-semibold text-sm text-slate-700 mb-3 flex items-center gap-2">
                        <Zap className="w-3.5 h-3.5 text-yellow-500" />
                        Agent Decision Trace
                      </div>
                      <AgentTimeline steps={neg.agent_steps} />
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ─── Agent Timeline ───────────────────────────────────────────────────────────

function AgentTimeline({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="relative">
      {steps.map((step, idx) => {
        const style = AGENT_COLORS[step.agent] ?? {
          bg: "bg-slate-50 border-slate-200",
          dot: "bg-slate-500 text-white",
          icon: "🤖",
        };
        return (
          <div key={idx} className="agent-step">
            {/* Connector line */}
            {idx < steps.length - 1 && (
              <div className="absolute left-3 top-7 bottom-0 w-px bg-slate-200" />
            )}
            {/* Dot */}
            <div className={cn("agent-dot w-7 h-7 rounded-full flex items-center justify-center text-xs", style.dot)}>
              {style.icon}
            </div>
            {/* Card */}
            <div className={cn("ml-4 rounded-xl border p-3 mb-3", style.bg)}>
              <div className="flex items-center justify-between mb-1">
                <div className="font-semibold text-xs text-slate-800">{step.agent}</div>
                <StatusIcon status={step.status} />
              </div>
              <div className="text-xs text-slate-600 leading-relaxed">{step.output}</div>

              {/* Details */}
              {step.details && Object.keys(step.details).length > 0 && (
                <div className="mt-2 pt-2 border-t border-slate-200/70">
                  {Object.entries(step.details).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-xs text-slate-500">
                      <span>{k.replace(/_/g, " ")}</span>
                      <span className="font-medium text-slate-700 max-w-[50%] text-right truncate">
                        {typeof v === "object" ? JSON.stringify(v) : String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function StatusIcon({ status }: { status: string }) {
  if (status === "complete") return <CheckCircle2 className="w-3.5 h-3.5 text-green-600" />;
  if (status === "error")    return <AlertCircle className="w-3.5 h-3.5 text-red-500" />;
  return <Loader className="w-3.5 h-3.5 text-blue-500 animate-spin" />;
}

function SwapBadge({ yielded, compensation }: { yielded: number; compensation: number }) {
  return (
    <div className="flex items-center gap-1.5 text-xs font-medium">
      <span className="bg-red-100 text-red-700 px-2 py-0.5 rounded-full">{yielded}h given</span>
      <ArrowRight className="w-3 h-3 text-slate-400" />
      <span className="bg-farm-100 text-farm-700 px-2 py-0.5 rounded-full">{compensation}h owed</span>
    </div>
  );
}

function SwapRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-slate-500">{label}</span>
      <span className="font-medium text-slate-800">{value}</span>
    </div>
  );
}
