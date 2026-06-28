import type { User } from "../types";

// Deterministic gradient from a string, so the initials fallback looks intentional.
function gradientFor(seed: string): string {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (h * 31 + seed.charCodeAt(i)) % 360;
  return `linear-gradient(135deg, hsl(${h} 80% 60%), hsl(${(h + 60) % 360} 80% 55%))`;
}

function initials(user: User): string {
  const base = user.display_name?.trim() || user.email;
  const parts = base.split(/[\s@._-]+/).filter(Boolean);
  return ((parts[0]?.[0] ?? "") + (parts[1]?.[0] ?? "")).toUpperCase() || base[0]?.toUpperCase() || "?";
}

export function Avatar({ user, size = 36 }: { user: User; size?: number }) {
  const style: React.CSSProperties = {
    width: size, height: size, borderRadius: "50%", flexShrink: 0,
    display: "grid", placeItems: "center", fontWeight: 700,
    fontSize: size * 0.4, color: "#0a0a14", overflow: "hidden",
    border: "1px solid var(--glass-brd)",
  };
  if (user.avatar) {
    return <img src={user.avatar} alt="avatar" style={{ ...style, objectFit: "cover" }} />;
  }
  return <div style={{ ...style, background: gradientFor(user.email) }}>{initials(user)}</div>;
}
