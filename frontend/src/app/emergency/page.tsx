"use client";
import { useEffect, useState } from "react";
import { getFarmers, getEmergencyRequests, processEmergency } from "@/lib/api";
import { Farmer, EmergencyRequest, PipelineResult } from "@/types";
import { cn, urgencyColor, statusColor, formatDate } from "@/lib/utils";
import {
  AlertTriangle, Send, Loader2, CheckCircle2, Zap,
  MessageSquare, Phone, Printer, ChevronDown, ChevronUp,
} from "lucide-react";

const DEMO_MESSAGES = [
  "My sugarcane is drying. I need 3 hours of water today urgently.",
  "Critical situation – my rice paddy has not received water in 2 days. Need water now.",
  "The cotton crop at Plot 3 needs irrigation. Can we get 2 hours this week?",
];

export default function EmergencyPage() {
  const [farmers, setFarmers] = useState<Farmer[]>([]);
  const [requests, setRequests] = useState<EmergencyRequest[]>([]);
  const [selectedFarmer, setSelectedFarmer] = useState("F006");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<PipelineResult | null>(null);
  const [showNotifs, setShowNotifs] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    getFarmers().then(setFarmers).catch(console.error);
    getEmergencyRequests().then(setRequests).catch(console.error);
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!message.trim()) return;
    setLoading(true);
    setResult(null);
    setError("");
    try {
      const res = await processEmergency(selectedFarmer, message);
      setResult(res);
      getEmergencyRequests().then(setRequests).catch(console.error);
    } catch (err: any) {
      setError(err?.response?.data?.detail || "Pipeline error. Is the backend running?");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-6 max-w-5xl animate-fade-in">
      {/* Submit Form */}
      <div className="card">
        <div className="card-header flex items-center gap-2 font-semibold text-slate-800">
          <AlertTriangle className="w-4 h-4 text-red-500" />
          Submit Emergency Irrigation Request
        </div>
        <form onSubmit={handleSubmit} className="card-body space-y-4">
          {/* Farmer select */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Select Farmer</label>
            <select
              value={selectedFarmer}
              onChange={(e) => setSelectedFarmer(e.target.value)}
              className="select"
            >
              {farmers.map((f) => (
                <option key={f.farmer_id} value={f.farmer_id}>
                  {f.farmer_id} — {f.name} ({f.plot_number}, η={f.flow_efficiency_index})
                </option>
              ))}
            </select>
          </div>

          {/* Quick prompts */}
          <div>
            <div className="text-xs text-slate-500 mb-2">Quick demo messages:</div>
            <div className="flex flex-wrap gap-2">
              {DEMO_MESSAGES.map((msg) => (
                <button
                  key={msg}
                  type="button"
                  onClick={() => setMessage(msg)}
                  className="text-xs px-3 py-1.5 rounded-lg bg-water-50 text-water-700 border border-water-200 hover:bg-water-100 transition"
                >
                  {msg.substring(0, 50)}…
                </button>
              ))}
            </div>
          </div>

          {/* Message */}
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Message (free text)</label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={3}
              placeholder="Describe your emergency irrigation need in natural language…"
              className="input resize-none"
            />
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-xl p-3">
              {error}
            </div>
          )}

          <button type="submit" disabled={loading || !message.trim()} className="btn-primary flex items-center gap-2">
            {loading
              ? <><Loader2 className="w-4 h-4 animate-spin" />Running agents…</>
              : <><Send className="w-4 h-4" />Run Pipeline</>}
          </button>
        </form>
      </div>

      {/* Pipeline Result */}
      {result && <PipelineResultCard result={result} showNotifs={showNotifs} setShowNotifs={setShowNotifs} />}

      {/* Past Requests */}
      {requests.length > 0 && (
        <div className="card">
          <div className="card-header font-semibold text-slate-800">Past Emergency Requests</div>
          <div className="divide-y divide-slate-100">
            {requests.map((req) => (
              <div key={req.id} className="px-6 py-3 flex items-center justify-between">
                <div>
                  <div className="text-sm font-medium text-slate-800">{req.farmer_name ?? `Farmer #${req.farmer_id}`}</div>
                  <div className="text-xs text-slate-500 mt-0.5 max-w-md truncate">{req.raw_message}</div>
                </div>
                <div className="flex items-center gap-2">
                  {req.extracted_urgency && (
                    <span className={cn("badge", urgencyColor(req.extracted_urgency))}>{req.extracted_urgency}</span>
                  )}
                  <span className={cn("badge", statusColor(req.status))}>{req.status}</span>
                  {req.fwos_score && (
                    <span className="text-xs font-bold text-water-600">FWOS {req.fwos_score}</span>
                  )}
                  <span className="text-xs text-slate-400">{formatDate(req.created_at)}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Pipeline Result ───────────────────────────────────────────────────────────

function PipelineResultCard({
  result, showNotifs, setShowNotifs,
}: {
  result: PipelineResult;
  showNotifs: string | null;
  setShowNotifs: (v: string | null) => void;
}) {
  const accepted = result.consent_decision === "accepted";

  return (
    <div className={cn("card border-2 animate-slide-in", accepted ? "border-farm-300" : "border-red-300")}>
      {/* Status Banner */}
      <div className={cn("px-6 py-4 flex items-center gap-3", accepted ? "bg-farm-50" : "bg-red-50")}>
        <div className={cn("w-10 h-10 rounded-xl flex items-center justify-center",
          accepted ? "bg-farm-500" : "bg-red-500")}>
          {accepted ? <CheckCircle2 className="w-6 h-6 text-white" /> : <AlertTriangle className="w-6 h-6 text-white" />}
        </div>
        <div>
          <div className="font-bold text-slate-900">
            Swap {accepted ? "Approved ✓" : "Rejected ✗"}
          </div>
          <div className="text-sm text-slate-600">{result.consent_reason}</div>
        </div>
        {result.fwos_score && (
          <div className="ml-auto text-right">
            <div className="text-3xl font-black text-water-600">{result.fwos_score}</div>
            <div className="text-xs text-slate-500">FWOS</div>
          </div>
        )}
      </div>

      <div className="p-6 grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Swap details */}
        {accepted && (
          <div className="space-y-3">
            <div className="font-semibold text-sm text-slate-700">Swap Details</div>
            <div className="bg-slate-50 rounded-xl p-4 space-y-2">
              <DetailLine label="Yielding Farmer" value={result.yielding_farmer_name ?? "—"} />
              <DetailLine label="Hours Yielded" value={`${result.hours_yielded ?? 0} hrs`} />
              <DetailLine label="Compensation" value={`${result.compensation_hours ?? 0} hrs`} highlight />
              <DetailLine label="Credit ID" value={result.credit_id ?? "—"} mono />
            </div>

            {/* Compensation formula */}
            {result.fwos_breakdown && (
              <div className="bg-water-50 border border-water-200 rounded-xl p-4">
                <div className="text-xs font-semibold text-water-700 mb-2">Compensation Formula</div>
                <div className="font-mono text-sm text-water-900">
                  {result.hours_yielded} hrs × (η={result.fwos_breakdown.inputs.eta.toFixed(2)} ÷ η_yielding)
                </div>
                <div className="font-mono text-lg font-bold text-water-700 mt-1">
                  = {result.compensation_hours} hrs owed back
                </div>
              </div>
            )}
          </div>
        )}

        {/* Explainability */}
        {result.fairness_explanation && (
          <div>
            <div className="font-semibold text-sm text-slate-700 mb-2 flex items-center gap-1">
              <Zap className="w-3.5 h-3.5 text-yellow-500" /> AI Decision Explanation
            </div>
            <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 text-sm text-slate-700 whitespace-pre-line leading-relaxed">
              {result.fairness_explanation}
            </div>
          </div>
        )}
      </div>

      {/* Notifications */}
      <div className="px-6 pb-6">
        <div className="font-semibold text-sm text-slate-700 mb-3">Omnichannel Notifications</div>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
          <NotifToggle
            icon={<MessageSquare className="w-4 h-4" />}
            label="Chat"
            id="chat"
            active={showNotifs === "chat"}
            onClick={() => setShowNotifs(showNotifs === "chat" ? null : "chat")}
          />
          <NotifToggle
            icon={<Phone className="w-4 h-4" />}
            label="SMS"
            id="sms"
            active={showNotifs === "sms"}
            onClick={() => setShowNotifs(showNotifs === "sms" ? null : "sms")}
          />
          <NotifToggle
            icon={<Phone className="w-4 h-4" />}
            label="IVR Script"
            id="ivr"
            active={showNotifs === "ivr"}
            onClick={() => setShowNotifs(showNotifs === "ivr" ? null : "ivr")}
          />
          <NotifToggle
            icon={<Printer className="w-4 h-4" />}
            label="Print"
            id="print"
            active={showNotifs === "print"}
            onClick={() => setShowNotifs(showNotifs === "print" ? null : "print")}
          />
        </div>

        {showNotifs === "chat" && result.chat_notification && (
          <NotifBox text={result.chat_notification} color="bg-sky-50 border-sky-200" />
        )}
        {showNotifs === "sms" && result.sms_notification && (
          <NotifBox text={result.sms_notification} color="bg-green-50 border-green-200" mono />
        )}
        {showNotifs === "ivr" && result.ivr_script && (
          <NotifBox text={result.ivr_script} color="bg-purple-50 border-purple-200" mono />
        )}
        {showNotifs === "print" && result.print_schedule && (
          <NotifBox text={result.print_schedule} color="bg-slate-50 border-slate-200" mono />
        )}
      </div>
    </div>
  );
}

function DetailLine({ label, value, highlight, mono }: { label: string; value: string; highlight?: boolean; mono?: boolean }) {
  return (
    <div className="flex justify-between text-sm">
      <span className="text-slate-500">{label}</span>
      <span className={cn("font-medium", highlight ? "text-farm-700 font-bold" : "text-slate-800", mono && "font-mono text-xs")}>{value}</span>
    </div>
  );
}

function NotifToggle({ icon, label, id, active, onClick }: {
  icon: React.ReactNode; label: string; id: string; active: boolean; onClick: () => void;
}) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "flex items-center gap-2 px-3 py-2 rounded-xl border text-sm font-medium transition-all",
        active ? "bg-water-600 text-white border-water-600" : "bg-white text-slate-600 border-slate-200 hover:border-water-300",
      )}
    >
      {icon} {label}
    </button>
  );
}

function NotifBox({ text, color, mono }: { text: string; color: string; mono?: boolean }) {
  return (
    <div className={cn("mt-3 rounded-xl border p-4 text-sm whitespace-pre-line leading-relaxed", color, mono && "font-mono text-xs")}>
      {text}
    </div>
  );
}
