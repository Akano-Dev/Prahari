// Live call state machine for the simulator: ring → accept/decline → active
// (streams a scenario through the REAL backend pipeline) → ended. Also supports
// injecting custom free-text lines mid-call. No real telephony is involved.
import { useCallback, useEffect, useRef, useState } from "react";
import { api, callSocket, dashboardSocket } from "../api/client";
import type { Incident, RiskAssessment, Stats } from "../types";
import { DEFAULT_SCENARIO, type Scenario } from "../data/scenarios";

export type CallPhase = "idle" | "ringing" | "active" | "ended";

export function useLiveCall(authed: boolean) {
  const [assessment, setAssessment] = useState<RiskAssessment | null>(null);
  const [transcript, setTranscript] = useState<string[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [connected, setConnected] = useState(false);
  const [phase, setPhase] = useState<CallPhase>("idle");
  const [incoming, setIncoming] = useState<Scenario | null>(null);
  const [active, setActive] = useState<Scenario | null>(null);

  const dashRef = useRef<WebSocket | null>(null);
  const csRef = useRef<WebSocket | null>(null);
  const cancelRef = useRef(false);

  const callerNumber = active?.caller ?? incoming?.caller ?? "+91 98XXXXXX21";

  const refresh = useCallback(async () => {
    try { setIncidents(await api.incidents()); setStats(await api.stats()); }
    catch { /* not logged in yet */ }
  }, []);

  // Dashboard WS — keeps incidents/stats + latest assessment live.
  useEffect(() => {
    if (!authed) return;
    const ws = dashboardSocket();
    dashRef.current = ws;
    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = () => { refresh(); };
    refresh();
    return () => ws.close();
  }, [authed, refresh]);

  const send = useCallback((line: string) => {
    const cs = csRef.current;
    if (!cs || cs.readyState !== WebSocket.OPEN) return;
    setTranscript((t) => [...t, line]);
    cs.send(JSON.stringify({ text: line }));
  }, []);

  // Ring an incoming call for the chosen scenario (no analysis yet).
  const startScenario = useCallback((s: Scenario = DEFAULT_SCENARIO) => {
    cancelRef.current = true;
    csRef.current?.close();
    setAssessment(null); setTranscript([]); setActive(null);
    setIncoming(s); setPhase("ringing");
  }, []);

  const decline = useCallback(() => {
    setIncoming(null); setPhase("idle");
  }, []);

  // Accept: open a call, stream the scenario lines through the live pipeline.
  const accept = useCallback(async () => {
    const s = incoming;
    if (!s) return;
    setIncoming(null); setActive(s); setPhase("active");
    setTranscript([]); setAssessment(null);
    cancelRef.current = false;

    const { id } = await api.createCall(s.caller);
    const cs = callSocket(id);
    csRef.current = cs;
    cs.onmessage = (e) => setAssessment(JSON.parse(e.data));
    await new Promise<void>((res) => { cs.onopen = () => res(); });

    for (const line of s.lines) {
      if (cancelRef.current || cs.readyState !== WebSocket.OPEN) break;
      send(line);
      await new Promise((r) => setTimeout(r, 1100));
    }
    refresh();
  }, [incoming, send, refresh]);

  const endCall = useCallback(() => {
    cancelRef.current = true;
    csRef.current?.close();
    csRef.current = null;
    setPhase((p) => (p === "active" ? "ended" : p));
    refresh();
  }, [refresh]);

  const reset = useCallback(() => {
    cancelRef.current = true;
    csRef.current?.close();
    csRef.current = null;
    setPhase("idle"); setIncoming(null); setActive(null);
  }, []);

  return {
    assessment, transcript, incidents, stats, connected,
    phase, incoming, active, callerNumber,
    startScenario, accept, decline, endCall, reset, sendLine: send,
    // Back-compat: hero button rings the default scenario.
    simulateCall: () => startScenario(DEFAULT_SCENARIO),
  };
}
