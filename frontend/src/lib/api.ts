import axios from "axios";

const BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const api = axios.create({
  baseURL: BASE,
  headers: { "Content-Type": "application/json" },
});

// ─── Dashboard ────────────────────────────────────────────────────────────────
export const getDashboard = () => api.get("/dashboard/").then((r) => r.data);

// ─── Farmers ──────────────────────────────────────────────────────────────────
export const getFarmers = () => api.get("/farmers/").then((r) => r.data);
export const getFarmer = (id: string) => api.get(`/farmers/${id}`).then((r) => r.data);
export const getFarmerStats = (id: string) => api.get(`/farmers/${id}/stats`).then((r) => r.data);

// ─── Schedules ────────────────────────────────────────────────────────────────
export const getSchedules = () => api.get("/schedules/").then((r) => r.data);
export const getActiveSchedule = () => api.get("/schedules/active").then((r) => r.data);

// ─── Emergency ────────────────────────────────────────────────────────────────
export const getEmergencyRequests = () => api.get("/emergency/").then((r) => r.data);
export const processEmergency = (farmerId: string, message: string) =>
  api.post("/emergency/process", { farmer_id: farmerId, raw_message: message }).then((r) => r.data);

// ─── Negotiations ─────────────────────────────────────────────────────────────
export const getNegotiations = () => api.get("/negotiations/").then((r) => r.data);
export const getNegotiation = (id: number) => api.get(`/negotiations/${id}`).then((r) => r.data);

// ─── Credits ──────────────────────────────────────────────────────────────────
export const getCredits = () => api.get("/credits/").then((r) => r.data);
export const getCreditsSummary = () => api.get("/credits/summary").then((r) => r.data);
export const redeemCredit = (creditId: string) =>
  api.patch(`/credits/${creditId}/redeem`).then((r) => r.data);

// ─── Audit ────────────────────────────────────────────────────────────────────
export const getAuditLog = (limit = 50) => api.get(`/audit/?limit=${limit}`).then((r) => r.data);
