import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatHours(hours: number): string {
  if (hours === 1) return "1 hr";
  return `${hours.toFixed(1)} hrs`;
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString("en-IN", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function urgencyColor(urgency: string): string {
  switch (urgency?.toLowerCase()) {
    case "critical": return "text-red-600 bg-red-50 border-red-200";
    case "high":     return "text-orange-600 bg-orange-50 border-orange-200";
    case "medium":   return "text-yellow-600 bg-yellow-50 border-yellow-200";
    case "low":      return "text-green-600 bg-green-50 border-green-200";
    default:         return "text-gray-600 bg-gray-50 border-gray-200";
  }
}

export function statusColor(status: string): string {
  switch (status?.toLowerCase()) {
    case "accepted":    return "text-green-700 bg-green-100";
    case "pending":     return "text-yellow-700 bg-yellow-100";
    case "negotiating": return "text-blue-700 bg-blue-100";
    case "rejected":    return "text-red-700 bg-red-100";
    case "completed":   return "text-purple-700 bg-purple-100";
    case "swapped":     return "text-orange-700 bg-orange-100";
    case "scheduled":   return "text-sky-700 bg-sky-100";
    case "active":      return "text-emerald-700 bg-emerald-100";
    default:            return "text-gray-700 bg-gray-100";
  }
}

export function fwosColor(score: number): string {
  if (score >= 70) return "text-red-600";
  if (score >= 50) return "text-orange-500";
  if (score >= 30) return "text-yellow-500";
  return "text-green-600";
}

export function etaToFlowLabel(eta: number): string {
  if (eta >= 0.95) return "Full Flow";
  if (eta >= 0.85) return "Strong Flow";
  if (eta >= 0.75) return "Moderate Flow";
  if (eta >= 0.65) return "Reduced Flow";
  return "Weak Flow";
}
