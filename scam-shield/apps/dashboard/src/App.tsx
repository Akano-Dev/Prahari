import { useCallback, useEffect, useRef, useState } from "react";
import { api, getToken, setToken } from "./api/client";
import type { User } from "./types";
import { useLiveCall } from "./hooks/useLiveCall";
import { useHashRoute } from "./hooks/useHashRoute";
import { useAlertSound } from "./hooks/useAlertSound";
import { Nav } from "./components/Nav";
import { AlertModal } from "./components/AlertModal";
import { IncomingCall } from "./components/IncomingCall";
import { LiveMonitor } from "./pages/LiveMonitor";
import { Incidents } from "./pages/Incidents";
import { Account } from "./pages/Account";

function Aurora() {
  return <div className="aurora"><div className="grain" /></div>;
}

function Login({ onAuthed }: { onAuthed: () => void }) {
  const [email, setEmail] = useState("agent@scamshield.test");
  const [password, setPassword] = useState("supersecret1");
  const [err, setErr] = useState("");
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setErr(""); setBusy(true);
    try {
      await api.register(email, password).catch(() => {});
      await api.login(email, password);
      onAuthed();
    } catch (e) { setErr((e as Error).message); } finally { setBusy(false); }
  };
  return (
    <>
      <Aurora />
      <div className="login">
        <div className="panel">
          <div className="brand" style={{ fontSize: "1.5rem", justifyContent: "center" }}>
            <span className="logo">🛡</span> Scam<span className="hl">Shield</span>
          </div>
          <div className="muted small" style={{ textAlign: "center" }}>Threat Operations Center — sign in</div>
          <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="email" />
          <input value={password} type="password" onChange={(e) => setPassword(e.target.value)}
                 placeholder="password" onKeyDown={(e) => e.key === "Enter" && submit()} />
          {err && <div className="small" style={{ color: "var(--crit)" }}>{err}</div>}
          <button className="btn" onClick={submit} disabled={busy}>{busy ? "Signing in…" : "Enter dashboard →"}</button>
          <div className="small muted" style={{ textAlign: "center" }}>
            Registers on first use. Backend: {import.meta.env.VITE_API_BASE || "http://localhost:8000"}
          </div>
        </div>
      </div>
    </>
  );
}

export default function App() {
  const [authed, setAuthed] = useState(!!getToken());
  const [user, setUser] = useState<User | null>(null);
  const [route, navigate] = useHashRoute();
  const live = useLiveCall(authed);
  const sound = useAlertSound();
  const [alertA, setAlertA] = useState<typeof live.assessment>(null);
  const alertedCall = useRef<string | null>(null);

  // Load the signed-in user's profile.
  useEffect(() => {
    if (!authed) { setUser(null); return; }
    api.me().then(setUser).catch(() => { setToken(null); setAuthed(false); });
  }, [authed]);

  // Fire the alert + beep once per call when it crosses the scam threshold.
  const a = live.assessment;
  useEffect(() => {
    if (a && a.is_scam && a.call_id !== alertedCall.current) {
      alertedCall.current = a.call_id;
      setAlertA(a);
      sound.play();
    }
  }, [a, sound]);

  const signOut = useCallback(() => { setToken(null); setAuthed(false); navigate("live"); }, [navigate]);
  const simulate = useCallback(() => { sound.enable(); alertedCall.current = null; navigate("live"); live.simulateCall(); }, [sound, live, navigate]);
  const accept = useCallback(() => { sound.enable(); alertedCall.current = null; live.accept(); }, [sound, live]);

  if (!authed) return <Login onAuthed={() => setAuthed(true)} />;

  return (
    <>
      <Aurora />
      <div className="app">
        <Nav route={route} navigate={navigate} user={user} connected={live.connected}
             muted={sound.muted} onToggleMute={() => sound.setMuted(!sound.muted)} onSignOut={signOut} />

        {route === "live" && (
          <LiveMonitor live={live} onSimulate={simulate} onOpenIncidents={() => navigate("incidents")} />
        )}
        {route === "incidents" && (
          <div className="pagewrap"><Incidents incidents={live.incidents} stats={live.stats} /></div>
        )}
        {route === "account" && user && (
          <div className="pagewrap"><Account user={user} onUpdated={setUser} onSignOut={signOut} /></div>
        )}
      </div>

      {live.phase === "ringing" && live.incoming && (
        <IncomingCall scenario={live.incoming} onAccept={accept} onDecline={live.decline} />
      )}
      {alertA && <AlertModal a={alertA} onClose={() => setAlertA(null)} />}
    </>
  );
}
