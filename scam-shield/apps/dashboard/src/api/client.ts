// Thin API client: auth, REST helpers, and live WebSocket URLs.
import type { Incident, RiskAssessment, Stats, User } from "../types";

const BASE = (import.meta.env.VITE_API_BASE as string) || "http://localhost:8000";
const WS_BASE = BASE.replace(/^http/, "ws");

let token: string | null = localStorage.getItem("ss_token");

export function getToken() { return token; }
export function setToken(t: string | null) {
  token = t;
  if (t) localStorage.setItem("ss_token", t);
  else localStorage.removeItem("ss_token");
}

async function req<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(BASE + path, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.headers || {}),
    },
  });
  if (!res.ok) throw new Error((await res.json().catch(() => ({}))).detail || `HTTP ${res.status}`);
  return res.status === 204 ? (undefined as T) : res.json();
}

export const api = {
  async register(email: string, password: string) {
    return req("/auth/register", { method: "POST", body: JSON.stringify({ email, password }) });
  },
  async login(email: string, password: string) {
    const r = await req<{ access_token: string }>("/auth/login", {
      method: "POST", body: JSON.stringify({ email, password }),
    });
    setToken(r.access_token);
    return r;
  },
  createCall: (caller_number: string) =>
    req<{ id: string }>("/calls", { method: "POST", body: JSON.stringify({ caller_number }) }),
  pushUtterance: (callId: string, text: string) =>
    req<RiskAssessment>(`/calls/${callId}/utterance`, { method: "POST", body: JSON.stringify({ text }) }),
  incidents: () => req<Incident[]>("/incidents"),
  stats: () => req<Stats>("/stats"),
  reportUrl: (callId: string) => `${BASE}/calls/${callId}/report.html`,
  me: () => req<User>("/auth/me"),
  updateProfile: (patch: { display_name?: string; avatar?: string }) =>
    req<User>("/auth/me", { method: "PATCH", body: JSON.stringify(patch) }),
};

export function dashboardSocket(): WebSocket {
  return new WebSocket(`${WS_BASE}/ws/dashboard?token=${token}`);
}
export function callSocket(callId: string): WebSocket {
  return new WebSocket(`${WS_BASE}/ws/calls/${callId}?token=${token}`);
}
