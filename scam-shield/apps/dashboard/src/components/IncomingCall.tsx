import type { Scenario } from "../data/scenarios";

// Full-screen "incoming call" ring screen with Accept / Decline.
export function IncomingCall({ scenario, onAccept, onDecline }: {
  scenario: Scenario; onAccept: () => void; onDecline: () => void;
}) {
  return (
    <div className="modal-backdrop">
      <div className="callcard" role="dialog" aria-modal="true">
        <div className="small muted">Incoming call · unknown number</div>
        <div className="caller-orb">
          <span className="ring2" aria-hidden /><span className="ring3" aria-hidden />
          <span className="orb">📞</span>
        </div>
        <div className="caller-num">{scenario.caller}</div>
        <div className="chip" style={{ margin: "0 auto" }}>{scenario.tag} · {scenario.language}</div>
        <div className="small muted" style={{ marginTop: 6 }}>ScamShield is listening…</div>
        <div className="call-actions">
          <button className="callbtn decline" onClick={onDecline} title="Decline">✕</button>
          <button className="callbtn accept" onClick={onAccept} title="Accept">✓</button>
        </div>
        <div className="call-actions-labels">
          <span>Decline</span><span>Accept &amp; analyze</span>
        </div>
      </div>
    </div>
  );
}
