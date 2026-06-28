import type { RiskAssessment } from "../types";

export function CallerInfo({ a, caller, connected }:
  { a: RiskAssessment | null; caller: string; connected: boolean }) {
  const oc = a?.officer_claim;
  return (
    <div className="panel">
      <h3>Caller Information</h3>
      <div className="list">
        <div className="row"><span className="muted">Number</span><span>{caller}</span></div>
        <div className="row"><span className="muted">Contact</span><span>Unknown caller</span></div>
        <div className="row"><span className="muted">Channel</span>
          <span>{connected ? "Live" : "Offline"}</span></div>
        <div className="row"><span className="muted">Utterances</span><span>{a?.n_utterances ?? 0}</span></div>
      </div>
      {oc?.claimed && (
        <>
          <h3 style={{ marginTop: 14 }}>Officer Claim Check</h3>
          <div className="list">
            <div className="row"><span className="muted">Department</span><span>{oc.department ?? "—"}</span></div>
            <div className="row"><span className="muted">Name</span><span>{oc.name ?? "—"}</span></div>
            <div className="row"><span className="muted">Designation</span><span>{oc.designation ?? "—"}</span></div>
            <div className="row"><span className="muted">Location</span><span>{oc.location ?? "—"}</span></div>
            <div className="row">
              <span className="muted">Consistency</span>
              <span style={{ color: oc.consistency === "impossible" ? "var(--crit)" : "var(--susp)" }}>
                {oc.consistency.toUpperCase()}
              </span>
            </div>
          </div>
          <div className="chips" style={{ marginTop: 8 }}>
            {oc.notes.map((n, i) => <span className="chip alert" key={i}>{n}</span>)}
          </div>
        </>
      )}
    </div>
  );
}
