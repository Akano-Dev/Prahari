import type { RiskAssessment } from "../types";
import { api } from "../api/client";

// Full-screen scam alert that pops when live risk crosses the scam threshold.
export function AlertModal({ a, onClose }: { a: RiskAssessment; onClose: () => void }) {
  const top = a.top_scam_type;
  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal alarm" onClick={(e) => e.stopPropagation()} role="alertdialog" aria-modal="true">
        <div className="alarm-ring" aria-hidden />
        <div className="alarm-icon">⚠</div>
        <h2>Likely scam detected</h2>
        <div className="alarm-score">Risk {a.risk_score}/100 · {a.band}</div>
        {top && <div className="chip alert" style={{ margin: "0 auto" }}>{top.label}</div>}
        <p className="reco" style={{ textAlign: "left", marginTop: 16 }}>{a.recommendation}</p>
        <div className="alarm-actions">
          <a className="btn ghost" href={api.reportUrl(a.call_id)} target="_blank" rel="noreferrer">Open report</a>
          <button className="btn" onClick={onClose}>Dismiss</button>
        </div>
        <div className="small muted" style={{ marginTop: 10 }}>
          Never share OTPs or transfer money. Report at cybercrime.gov.in or call 1930.
        </div>
      </div>
    </div>
  );
}
