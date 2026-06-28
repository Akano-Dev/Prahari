export const riskColor = (s: number) =>
  s >= 75 ? "var(--crit)" : s >= 50 ? "var(--high)" : s >= 25 ? "var(--susp)" : "var(--safe)";

export const BEHAVIOUR_LABELS: Record<string, string> = {
  urgency: "Urgency",
  fear: "Fear tactics",
  authority_impersonation: "Authority impersonation",
  money_request: "Money request",
  credential_request: "OTP / credentials",
  secrecy: "Secrecy pressure",
  threat: "Threats",
  emotional_manipulation: "Emotional manipulation",
  video_call_pressure: "Video-call pressure",
};

// Highlight matched evidence snippets inside a transcript line.
export function highlight(text: string, snippets: string[]): string {
  let out = text.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]!));
  for (const s of [...new Set(snippets)].sort((a, b) => b.length - a.length)) {
    if (!s) continue;
    const esc = s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    out = out.replace(new RegExp(esc, "gi"), (m) => `<mark>${m}</mark>`);
  }
  return out;
}
