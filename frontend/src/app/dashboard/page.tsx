"use client";
import { useEffect, useState } from "react";
import { getDashboard } from "@/lib/api";
import { DashboardData } from "@/types";
import { cn, formatDate, fwosColor, statusColor } from "@/lib/utils";
import {
  Droplets, Users, AlertTriangle, CreditCard,
  TrendingUp, Clock, Zap, ChevronRight,
} from "lucide-react";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, RadialBarChart, RadialBar,
} from "recharts";
import Link from "next/link";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard()
      .then(setData)
      .catch(console.error)
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <DashboardSkeleton />;
  if (!data) return <div className="text-slate-500 p-8">Failed to load dashboard.</div>;

  const { summary, farmer_cards, upcoming_schedule, canal_flow } = data;

  const chartData = farmer_cards.map((f) => ({
    name: f.plot,
    eta: Math.round(f.eta * 100),
    fwos: f.fwos,
    deficit: f.historical_deficit,
  }));

  const radialData = farmer_cards.map((f, i) => ({
    name: f.plot,
    fwos: f.fwos,
    fill: ["#3b9af0", "#22c55e", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"][i % 6],
  }));

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<Users className="w-5 h-5 text-water-600" />}
          label="Total Farmers"
          value={summary.total_farmers}
          bg="bg-water-50"
          border="border-water-200"
        />
        <StatCard
          icon={<AlertTriangle className="w-5 h-5 text-red-500" />}
          label="Active Emergencies"
          value={summary.active_emergency_requests}
          bg="bg-red-50"
          border="border-red-200"
          urgent={summary.active_emergency_requests > 0}
        />
        <StatCard
          icon={<CreditCard className="w-5 h-5 text-farm-600" />}
          label="Active Credits"
          value={summary.active_credits}
          bg="bg-farm-50"
          border="border-farm-200"
        />
        <StatCard
          icon={<Droplets className="w-5 h-5 text-sky-600" />}
          label="Hours Owed"
          value={`${summary.total_credit_hours_owed} hrs`}
          bg="bg-sky-50"
          border="border-sky-200"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Upcoming Schedule */}
        <div className="lg:col-span-2 card">
          <div className="card-header flex items-center justify-between">
            <div className="flex items-center gap-2 font-semibold text-slate-800">
              <Clock className="w-4 h-4 text-water-600" />
              Upcoming Schedule
            </div>
            <Link href="/farmers" className="text-xs text-water-600 hover:underline flex items-center gap-1">
              View all <ChevronRight className="w-3 h-3" />
            </Link>
          </div>
          <div className="divide-y divide-slate-100">
            {upcoming_schedule.length === 0 ? (
              <div className="px-6 py-8 text-center text-slate-400">No upcoming slots</div>
            ) : (
              upcoming_schedule.map((slot) => (
                <div key={slot.schedule_id} className="px-6 py-3 flex items-center justify-between hover:bg-slate-50 transition">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 rounded-xl bg-water-100 flex items-center justify-center text-water-700 font-bold text-sm">
                      {slot.plot.replace("Plot-", "P")}
                    </div>
                    <div>
                      <div className="font-medium text-sm text-slate-800">{slot.farmer_name}</div>
                      <div className="text-xs text-slate-500">{formatDate(slot.slot_start)} · {slot.hours} hrs</div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FlowBadge eta={slot.eta} />
                    <span className={cn("badge", statusColor(slot.status))}>{slot.status}</span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Canal Flow Mini */}
        <div className="card">
          <div className="card-header font-semibold text-slate-800 flex items-center gap-2">
            <Droplets className="w-4 h-4 text-water-600" />
            Canal Flow Efficiency
          </div>
          <div className="card-body space-y-3">
            {canal_flow.map((c) => (
              <div key={c.position}>
                <div className="flex justify-between text-xs mb-1">
                  <span className="font-medium text-slate-700">{c.plot} · {c.farmer.split(" ")[0]}</span>
                  <span className="text-slate-500">η = {c.eta.toFixed(2)}</span>
                </div>
                <div className="flow-bar">
                  <div className="flow-fill" style={{ width: `${c.flow_percent}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Bar Chart */}
        <div className="card">
          <div className="card-header font-semibold text-slate-800 flex items-center gap-2">
            <TrendingUp className="w-4 h-4 text-water-600" />
            Flow Efficiency vs FWOS
          </div>
          <div className="card-body">
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={chartData} barCategoryGap="30%">
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip
                  contentStyle={{ borderRadius: 12, border: "1px solid #e2e8f0", fontSize: 12 }}
                />
                <Bar dataKey="eta" name="Flow Efficiency %" fill="#3b9af0" radius={[4, 4, 0, 0]} />
                <Bar dataKey="fwos" name="FWOS Score" fill="#22c55e" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Farmer FWOS Cards */}
        <div className="card">
          <div className="card-header font-semibold text-slate-800 flex items-center gap-2">
            <Zap className="w-4 h-4 text-yellow-500" />
            Fair Water Opportunity Scores
          </div>
          <div className="card-body grid grid-cols-2 gap-3">
            {farmer_cards.map((f) => (
              <div key={f.farmer_id} className="border border-slate-100 rounded-xl p-3 hover:border-water-200 transition">
                <div className="flex justify-between items-start mb-1">
                  <div className="text-xs font-semibold text-slate-700">{f.plot}</div>
                  <div className={cn("text-sm font-bold", fwosColor(f.fwos))}>{f.fwos}</div>
                </div>
                <div className="text-xs text-slate-500 truncate">{f.name}</div>
                <div className="text-xs text-slate-400 mt-0.5">{f.crop_type}</div>
                <div className="mt-2 flow-bar">
                  <div className="flow-fill" style={{ width: `${f.fwos}%` }} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Emergency Requests Alert */}
      {data.emergency_requests.length > 0 && (
        <div className="card border-red-200 bg-red-50">
          <div className="card-header flex items-center justify-between border-red-100">
            <div className="flex items-center gap-2 text-red-700 font-semibold">
              <AlertTriangle className="w-4 h-4" />
              Active Emergency Requests
            </div>
            <Link href="/emergency" className="btn-primary text-sm py-1.5 bg-red-600 hover:bg-red-700">
              Manage
            </Link>
          </div>
          <div className="card-body space-y-2">
            {data.emergency_requests.map((req) => (
              <div key={req.id} className="flex items-center gap-3 text-sm">
                <span className={cn("badge", req.urgency === "critical" ? "text-red-700 bg-red-100" : "text-orange-700 bg-orange-100")}>
                  {req.urgency || "medium"}
                </span>
                <span className="text-slate-700">{req.crop || "Unknown crop"} · Farmer #{req.farmer_id}</span>
                <span className="text-slate-400 text-xs ml-auto">{formatDate(req.created_at)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({
  icon, label, value, bg, border, urgent,
}: {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  bg: string;
  border: string;
  urgent?: boolean;
}) {
  return (
    <div className={cn("card p-5 border", border, urgent && "ring-2 ring-red-300")}>
      <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center mb-3", bg)}>
        {icon}
      </div>
      <div className="text-2xl font-bold text-slate-900">{value}</div>
      <div className="text-sm text-slate-500 mt-0.5">{label}</div>
    </div>
  );
}

function FlowBadge({ eta }: { eta: number }) {
  const pct = Math.round(eta * 100);
  const color = pct >= 90 ? "text-farm-700 bg-farm-100" : pct >= 75 ? "text-yellow-700 bg-yellow-100" : "text-red-700 bg-red-100";
  return <span className={cn("badge", color)}>η {eta.toFixed(2)}</span>;
}

function DashboardSkeleton() {
  return (
    <div className="space-y-6 animate-pulse">
      <div className="grid grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-28 bg-slate-200 rounded-2xl" />
        ))}
      </div>
      <div className="grid grid-cols-3 gap-6">
        <div className="col-span-2 h-64 bg-slate-200 rounded-2xl" />
        <div className="h-64 bg-slate-200 rounded-2xl" />
      </div>
    </div>
  );
}
