import { useEffect, useState } from "react";
import { SCENARIOS, type Scenario } from "../data/scenarios";
import type { CallPhase } from "../hooks/useLiveCall";

function Timer({ running }: { running: boolean }) {
  const [s, setS] = useState(0);
  useEffect(() => {
    if (!running) { setS(0); return; }
    const id = setInterval(() => setS((x) => x + 1), 1000);
    return () => clearInterval(id);
  }, [running]);
  const mm = String(Math.floor(s / 60)).padStart(2, "0");
  const ss = String(s % 60).padStart(2, "0");
  return <span className="call-timer">{mm}:{ss}</span>;
}

export function CallSimulator({ phase, active, caller, onStart, onEnd, onReset, onSendLine }: {
  phase: CallPhase; active: Scenario | null; caller: string;
  onStart: (s: Scenario) => void; onEnd: () => void; onReset: () => void; onSendLine: (t: string) => void;
}) {
  const [line, setLine] = useState("");
  const busy = phase === "ringing" || phase === "active";
  const submit = () => { const t = line.trim(); if (t) { onSendLine(t); setLine(""); } };

  return (
    <div className="panel">
      <h3>📞 Call Simulator</h3>

      {phase === "active" && (
        <div className="incall">
          <span className="dotpulse" aria-hidden />
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 600 }}>{caller}</div>
            <div className="small muted">{active?.tag} · live analysis</div>
          </div>
          <Timer running />
          <button className="btn" style={{ background: "linear-gradient(135deg,#e11d48,#fb3b6b)" }} onClick={onEnd}>
            End call
          </button>
        </div>
      )}

      {phase === "active" && (
        <div className="composer">
          <input value={line} placeholder="Type a line the caller says… (streamed live)"
                 onChange={(e) => setLine(e.target.value)} onKeyDown={(e) => e.key === "Enter" && submit()} />
          <button className="btn ghost" onClick={submit}>Send</button>
        </div>
      )}

      {phase === "ended" && (
        <div className="incall ended">
          <div style={{ flex: 1 }} className="small muted">Call ended — review the analysis below.</div>
          <button className="btn ghost" onClick={onReset}>New call</button>
        </div>
      )}

      {(phase === "idle" || phase === "ended") && (
        <>
          <div className="small muted" style={{ marginBottom: 10 }}>
            Pick a scenario to receive a simulated incoming call. Each line is scored by the real engine — nothing is dialed.
          </div>
          <div className="scenario-grid">
            {SCENARIOS.map((s) => (
              <button key={s.id} className="scenario" onClick={() => onStart(s)} disabled={busy}>
                <div className="scenario-top">
                  <span className="scenario-label">{s.label}</span>
                  <span className={`tagdot ${s.scam ? "scam" : "safe"}`}>{s.scam ? "scam" : "safe"}</span>
                </div>
                <div className="small muted">{s.caller} · {s.language}</div>
              </button>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
