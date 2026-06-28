import type { Incident } from "../types";
import { api } from "../api/client";
import { riskColor } from "../format";

export function PastIncidents({ incidents }: { incidents: Incident[] }) {
  return (
    <div className="panel">
      <h3>Past Incidents</h3>
      {incidents.length === 0 ? (
        <div className="muted small">No incidents recorded yet.</div>
      ) : (
        <div className="list">
          {incidents.slice(0, 8).map((i) => (
            <div className="row" key={i.id}>
              <span>
                <b style={{ color: riskColor(i.risk_score) }}>{i.risk_score}</b>&nbsp;
                {i.scam_type ?? "unknown"}
                <span className="muted small"> · {i.caller_number}</span>
              </span>
              <a className="small" href={api.reportUrl(i.call_id)} target="_blank" rel="noreferrer">report</a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
