import type { User } from "../types";
import type { Route } from "../hooks/useHashRoute";
import { Avatar } from "./Avatar";

const LINKS: { id: Route; label: string; icon: string }[] = [
  { id: "live", label: "Live Monitor", icon: "📡" },
  { id: "incidents", label: "Incidents", icon: "🗂" },
  { id: "account", label: "Account", icon: "👤" },
];

export function Nav({ route, navigate, user, connected, muted, onToggleMute, onSignOut }: {
  route: Route; navigate: (r: Route) => void; user: User | null;
  connected: boolean; muted: boolean; onToggleMute: () => void; onSignOut: () => void;
}) {
  return (
    <div className="topbar">
      <div className="brand"><span className="logo">🛡</span> Scam<span className="hl">Shield</span></div>
      <nav className="nav">
        {LINKS.map((l) => (
          <button key={l.id} className={`navlink ${route === l.id ? "active" : ""}`}
                  onClick={() => navigate(l.id)}>
            <span aria-hidden>{l.icon}</span> {l.label}
          </button>
        ))}
      </nav>
      <div className="spacer" />
      <span className={`pill ${connected ? "live" : ""}`}>{connected ? "LIVE" : "OFFLINE"}</span>
      <button className="iconbtn" title={muted ? "Unmute alerts" : "Mute alerts"} onClick={onToggleMute}>
        {muted ? "🔇" : "🔔"}
      </button>
      {user && (
        <button className="userchip" onClick={() => navigate("account")} title="Account">
          <Avatar user={user} size={30} />
          <span className="small">{user.display_name || user.email.split("@")[0]}</span>
        </button>
      )}
      <button className="btn ghost" onClick={onSignOut}>Sign out</button>
    </div>
  );
}
