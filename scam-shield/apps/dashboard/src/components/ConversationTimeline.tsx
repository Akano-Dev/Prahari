import type { RiskAssessment } from "../types";

export function ConversationTimeline({ a }: { a: RiskAssessment | null }) {
  const events = (a?.timeline ?? []).slice(-14);
  return (
    <div className="panel">
      <h3>Behaviour / Conversation Timeline</h3>
      {events.length === 0 ? (
        <div className="muted small">Events will appear as the call progresses.</div>
      ) : (
        <div className="timeline">
          {events.map((t, i) => (
            <div className={`tl ${t.kind}`} key={i}>
              <span className="dot" />
              <span>
                <b>{t.label}</b>
                {t.detail ? <span className="muted"> — {t.detail}</span> : null}
                {t.risk_after != null ? <span className="small muted"> (risk {t.risk_after})</span> : null}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
