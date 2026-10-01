"use client";
import { useEffect, useState } from "react";
import { getCredits, getCreditsSummary, redeemCredit, getAuditLog } from "@/lib/api";
import { WaterCredit, AuditEntry } from "@/types";
import { cn, statusColor, formatDate } from "@/lib/utils";
import {
  CreditCard, CheckCircle2, Clock, ArrowRightLeft,
  RefreshCw, TrendingUp, Droplets, Shield,
} from "lucide-react";

interface Summary {
  total_credits: number;
  active_credits: number;
  redeemed_credits: number;
  total_hours_given: number;
  total_hours_owed: number;
  net_compensation: number;
}

export default function CreditsPage() {
  const [credits, setCredits] = useState<WaterCredit[]>([]);
  const [summary, setSummary] = useState<Summary | null>(null);
  const [auditLog, setAuditLog] = useState<AuditEntry[]>([]);
  const [redeeming, setRedeeming] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"credits" | "audit">("credits");

  async function loadAll() {
    const [c, s, a] = await Promise.all([
      getCredits(),
      getCreditsSummary(),
      getAuditLog(30),
    ]);
    setCredits(c);
    setSummary(s);
    setAuditLog(a);
  }

  useEffect(() => {
    loadAll().catch(console.error).finally(() => setLoading(false));
  }, []);

  async function handleRedeem(creditId: string) {
    setRedeeming(creditId);
    try {
      await redeemCredit(creditId);
      await loadAll();
    } catch (e) {
      console.error(e);
    } finally {
      setRedeeming(null);
    }
  }

  if (loading) return <div className="animate-pulse h-96 bg-slate-200 rounded-2xl" />;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Summary stats */}
      {summary && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <SummaryCard icon={<CreditCard className="w-5 h-5 text-water-600" />}
            label="Total Credits" value={summary.total_credits} bg="bg-water-50" />
          <SummaryCard icon={<CheckCircle2 className="w-5 h-5 text-farm-600" />}
            label="Active" value={summary.active_credits} bg="bg-farm-50" />
          <SummaryCard icon={<Droplets className="w-5 h-5 text-sky-600" />}
            label="Hours Given" value={`${summary.total_hours_given}h`} bg="bg-sky-50" />
          <SummaryCard icon={<TrendingUp className="w-5 h-5 text-purple-600" />}
            label="Hours Owed Back" value={`${summary.total_hours_owed}h`} bg="bg-purple-50" />
        </div>
      )}

      {/* Tabs */}
      <div className="flex gap-2">
        {(["credits", "audit"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={cn(
              "px-4 py-2 rounded-xl text-sm font-medium transition",
              activeTab === tab
                ? "bg-water-600 text-white"
                : "bg-white text-slate-600 border border-slate-200 hover:border-water-300",
            )}
          >
            {tab === "credits" ? "💧 Water Credits" : "🔒 Audit Log"}
          </button>
        ))}
      </div>

      {activeTab === "credits" && (
        <div className="card">
          <div className="card-header font-semibold text-slate-800 flex items-center gap-2">
            <ArrowRightLeft className="w-4 h-4 text-water-600" />
            Water Credit Ledger
          </div>
          {credits.length === 0 ? (
            <div className="px-6 py-16 text-center text-slate-400">
              <CreditCard className="w-10 h-10 mx-auto mb-2 opacity-30" />
              No credits issued yet. Submit an emergency request to generate the first swap.
            </div>
          ) : (
            <div className="divide-y divide-slate-100">
              {credits.map((credit) => (
                <CreditRow
                  key={credit.id}
                  credit={credit}
                  onRedeem={handleRedeem}
                  redeeming={redeeming === credit.credit_id}
                />
              ))}
            </div>
          )}
        </div>
      )}

      {activeTab === "audit" && (
        <div className="card">
          <div className="card-header font-semibold text-slate-800 flex items-center gap-2">
            <Shield className="w-4 h-4 text-slate-600" />
            Immutable Audit Log
            <span className="ml-auto text-xs text-slate-400 font-normal">Read-only · Append-only</span>
          </div>
          {auditLog.length === 0 ? (
            <div className="px-6 py-16 text-center text-slate-400">No audit entries yet.</div>
          ) : (
            <div className="divide-y divide-slate-100">
              {auditLog.map((entry) => (
                <AuditRow key={entry.id} entry={entry} />
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ─── Credit Row ────────────────────────────────────────────────────────────────

function CreditRow({
  credit, onRedeem, redeeming,
}: { credit: WaterCredit; onRedeem: (id: string) => void; redeeming: boolean }) {
  const isActive = credit.status === "active";

  return (
    <div className="px-6 py-4 flex items-center justify-between gap-4">
      <div className="flex items-center gap-3 min-w-0">
        <div className={cn(
          "w-10 h-10 rounded-xl flex items-center justify-center shrink-0",
          isActive ? "bg-farm-100" : "bg-slate-100",
        )}>
          <CreditCard className={cn("w-5 h-5", isActive ? "text-farm-600" : "text-slate-400")} />
        </div>
        <div className="min-w-0">
          <div className="font-semibold text-sm text-slate-900 font-mono">{credit.credit_id}</div>
          <div className="text-xs text-slate-500 mt-0.5">
            {credit.giving_farmer_name ?? "Unknown"} owes {credit.receiving_farmer_name ?? "Unknown"}
          </div>
          {credit.notes && <div className="text-xs text-slate-400 truncate mt-0.5">{credit.notes}</div>}
        </div>
      </div>

      <div className="flex items-center gap-4 shrink-0">
        {/* Hours exchange */}
        <div className="text-right">
          <div className="flex items-center gap-1.5 text-sm justify-end">
            <span className="text-red-600 font-medium">{credit.hours_given}h given</span>
            <ArrowRightLeft className="w-3 h-3 text-slate-400" />
            <span className="text-farm-600 font-bold">{credit.hours_owed}h owed</span>
          </div>
          <div className="text-xs text-slate-400 mt-0.5">{formatDate(credit.created_at)}</div>
        </div>

        {/* Status badge */}
        <span className={cn("badge", statusColor(credit.status))}>{credit.status}</span>

        {/* Redeem button */}
        {isActive && (
          <button
            onClick={() => onRedeem(credit.credit_id)}
            disabled={redeeming}
            className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
          >
            {redeeming ? <RefreshCw className="w-3 h-3 animate-spin" /> : <CheckCircle2 className="w-3 h-3" />}
            Redeem
          </button>
        )}
        {credit.redeemed_at && (
          <div className="text-xs text-slate-400">{formatDate(credit.redeemed_at)}</div>
        )}
      </div>
    </div>
  );
}

// ─── Audit Row ────────────────────────────────────────────────────────────────

const EVENT_STYLES: Record<string, string> = {
  swap_accepted:    "bg-farm-100 text-farm-700",
  swap_proposed:    "bg-yellow-100 text-yellow-700",
  credit_issued:    "bg-water-100 text-water-700",
  schedule_changed: "bg-purple-100 text-purple-700",
  system_seed:      "bg-slate-100 text-slate-600",
};

function AuditRow({ entry }: { entry: AuditEntry }) {
  const style = EVENT_STYLES[entry.event_type] ?? "bg-slate-100 text-slate-600";
  return (
    <div className="px-6 py-3 flex items-start gap-3">
      <span className={cn("badge mt-0.5 shrink-0", style)}>{entry.event_type}</span>
      <div className="flex-1 min-w-0">
        <div className="text-sm text-slate-700">{entry.description}</div>
        <div className="text-xs text-slate-400 mt-0.5">{entry.actor} · {formatDate(entry.timestamp)}</div>
      </div>
    </div>
  );
}

function SummaryCard({ icon, label, value, bg }: {
  icon: React.ReactNode; label: string; value: string | number; bg: string;
}) {
  return (
    <div className={cn("card p-5 border", bg.replace("bg-", "border-").replace("-50", "-200"))}>
      <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-3", bg)}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="text-sm text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}
