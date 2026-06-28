import type { RiskAssessment } from "../types";

export function ScamTypeBadge({ a }: { a: RiskAssessment | null }) {
  const top = a?.top_scam_type;
  return (
    <div className="panel">
      <h3>Detected Scam Type</h3>
      {top ? (
        <>
          <div style={{ fontSize: "1.3rem", fontWeight: 700 }}>{top.label}</div>
          <div className="small muted">match strength {Math.round(top.score * 100)}%</div>
          <div className="chips" style={{ marginTop: 10 }}>
            {a!.scam_types.slice(1, 6).map((t) => (
              <span className="chip" key={t.category}>{t.label} · {Math.round(t.score * 100)}%</span>
            ))}
          </div>
        </>
      ) : (
        <div className="muted small">No scam pattern matched yet.</div>
      )}
    </div>
  );
}
