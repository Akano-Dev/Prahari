import type { Incident, Stats } from "../types";
import { api } from "../api/client";
import { riskColor } from "../format";

export function Incidents({ incidents, stats }: { incidents: Incident[]; stats: Stats | null }) {
  return (
    <div className="page">
      <div className="panel hero" style={{ marginInline: 0 }}>
        <div className="eyebrow">Case history</div>
        <h1>Detected <span className="grad">incidents</span></h1>
        <p>Every call that crossed the scam threshold, with its peak risk and a full explainable report.</p>
        <div className="hstats">
          <div className="hstat"><div className="n">{stats?.total_incidents ?? incidents.length}</div><div className="l">Incidents</div></div>
          <div className="hstat"><div className="n">{stats?.scam_calls ?? 0}</div><div className="l">Scam calls</div></div>
          <div className="hstat"><div className="n">{stats ? Math.round(stats.avg_peak_risk) : 0}</div><div className="l">Avg peak risk</div></div>
        </div>
      </div>

      <div className="panel" style={{ marginTop: 18 }}>
        <h3>All incidents</h3>
        {incidents.length === 0 && <div className="muted small">No incidents yet. Simulate a scam call to generate one.</div>}
        <div className="list">
          {incidents.map((i) => (
            <div className="row incident" key={i.id}>
              <div>
                <div style={{ fontWeight: 600 }}>{i.caller_number || "unknown"}</div>
                <div className="small muted">
                  {i.scam_type ? i.scam_type.replace(/_/g, " ") : "scam"} · {new Date(i.created_at).toLocaleString()}
                </div>
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
                <span className="riskbadge" style={{ color: riskColor(i.risk_score), borderColor: riskColor(i.risk_score) }}>
                  {i.risk_score}
                </span>
                <a className="btn ghost" href={api.reportUrl(i.call_id)} target="_blank" rel="noreferrer">Report</a>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
