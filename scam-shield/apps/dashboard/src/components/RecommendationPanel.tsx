import type { RiskAssessment } from "../types";

export function RecommendationPanel({ a }: { a: RiskAssessment | null }) {
  if (!a) return null;
  return (
    <div className="panel">
      <h3>Recommendation</h3>
      <div className={`reco ${a.is_scam ? "" : "safe"}`}>{a.recommendation}</div>
      {a.reasoning && (
        <>
          <h3 style={{ marginTop: 14 }}>Reasoning</h3>
          <div className="small">{a.reasoning}</div>
        </>
      )}
      {a.signals.length > 0 && (
        <>
          <h3 style={{ marginTop: 14 }}>Why (red flags)</h3>
          <div className="list">
            {a.signals.map((s) => (
              <div className="row" key={s.id}>
                <span>{s.label}</span>
                <span className="muted small">“{s.evidence[0]?.text}”</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
