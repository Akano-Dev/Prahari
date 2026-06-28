import type { RiskAssessment } from "../types";
import { BEHAVIOUR_LABELS, riskColor } from "../format";

export function BehaviourPanel({ a }: { a: RiskAssessment | null }) {
  const b = a?.behaviour;
  return (
    <div className="panel">
      <h3>Behaviour Analysis</h3>
      <div className="bars">
        {Object.entries(BEHAVIOUR_LABELS).map(([key, label]) => {
          const v = b ? ((b as never)[key] as number) ?? 0 : 0;
          const pct = Math.round(v * 100);
          return (
            <div className="bar" key={key}>
              <span className="muted">{label}</span>
              <span className="track">
                <span className="fill" style={{ width: `${pct}%`, background: riskColor(pct) }} />
              </span>
              <span className="small">{pct}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
