import type { RiskAssessment } from "../types";

export function EntitiesPanel({ a }: { a: RiskAssessment | null }) {
  const ents = a?.entities ?? [];
  return (
    <div className="panel">
      <h3>Detected Entities</h3>
      {ents.length === 0 ? (
        <div className="muted small">No entities extracted yet.</div>
      ) : (
        <div className="chips">
          {ents.map((e, i) => (
            <span className="chip" key={i}><b>{e.type}</b>&nbsp;{e.value}</span>
          ))}
        </div>
      )}
    </div>
  );
}
