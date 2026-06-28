import type { Stats } from "../types";

export function Statistics({ stats }: { stats: Stats | null }) {
  return (
    <div className="panel">
      <h3>Statistics</h3>
      <div className="statgrid">
        <div className="stat"><div className="n">{stats?.total_calls ?? 0}</div><div className="l">Calls</div></div>
        <div className="stat"><div className="n">{stats?.scam_calls ?? 0}</div><div className="l">Scam calls</div></div>
        <div className="stat"><div className="n">{stats?.total_incidents ?? 0}</div><div className="l">Incidents</div></div>
        <div className="stat"><div className="n">{stats?.avg_peak_risk ?? 0}</div><div className="l">Avg peak risk</div></div>
      </div>
      {stats && Object.keys(stats.by_scam_type).length > 0 && (
        <div className="chips" style={{ marginTop: 12 }}>
          {Object.entries(stats.by_scam_type).map(([k, v]) => (
            <span className="chip" key={k}>{k}: {v}</span>
          ))}
        </div>
      )}
    </div>
  );
}
