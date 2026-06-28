import type { useLiveCall } from "../hooks/useLiveCall";
import { RiskMeter } from "../components/RiskMeter";
import { ScamTypeBadge } from "../components/ScamTypeBadge";
import { LiveTranscript } from "../components/LiveTranscript";
import { BehaviourPanel } from "../components/BehaviourPanel";
import { EntitiesPanel } from "../components/EntitiesPanel";
import { ConversationTimeline } from "../components/ConversationTimeline";
import { CallerInfo } from "../components/CallerInfo";
import { RecommendationPanel } from "../components/RecommendationPanel";
import { PastIncidents } from "../components/PastIncidents";
import { Statistics } from "../components/Statistics";
import { CallSimulator } from "../components/CallSimulator";

type Live = ReturnType<typeof useLiveCall>;

function Hero({ live, onSimulate, onOpenIncidents }: {
  live: Live; onSimulate: () => void; onOpenIncidents: () => void;
}) {
  const a = live.assessment;
  const isLive = !!a && a.n_utterances > 0;
  return (
    <div className="panel hero">
      <div className="eyebrow">Real-time scam-call defense</div>
      <h1>Catch the scam <span className="grad">before it catches them.</span></h1>
      <p>
        ScamShield listens to a suspicious call as it happens and flags scam tactics
        sentence-by-sentence — explainable, multilingual, and built to protect people.
      </p>
      <div className="actions">
        <button className="btn" onClick={onSimulate}>▶ Simulate incoming scam call</button>
        <button className="btn ghost" onClick={onOpenIncidents}>View incidents</button>
        <span className={`pill ${live.connected ? "live" : ""}`}>{live.connected ? "Engine live" : "Connecting…"}</span>
      </div>
      <div className="hstats">
        <div className="hstat"><div className="n">{isLive ? a!.risk_score : "—"}</div><div className="l">Current risk</div></div>
        <div className="hstat"><div className="n">{live.stats?.total_calls ?? 0}</div><div className="l">Calls screened</div></div>
        <div className="hstat"><div className="n">{live.stats?.scam_calls ?? 0}</div><div className="l">Scams caught</div></div>
        <div className="hstat"><div className="n">20</div><div className="l">Scam types tracked</div></div>
      </div>
    </div>
  );
}

export function LiveMonitor({ live, onSimulate, onOpenIncidents }: {
  live: Live; onSimulate: () => void; onOpenIncidents: () => void;
}) {
  const a = live.assessment;
  return (
    <>
      <Hero live={live} onSimulate={onSimulate} onOpenIncidents={onOpenIncidents} />
      <div className="grid">
        <div className="col">
          <RiskMeter a={a} />
          <ScamTypeBadge a={a} />
          <CallerInfo a={a} caller={live.callerNumber} connected={live.connected} />
        </div>
        <div className="col">
          <CallSimulator
            phase={live.phase} active={live.active} caller={live.callerNumber}
            onStart={live.startScenario} onEnd={live.endCall} onReset={live.reset} onSendLine={live.sendLine}
          />
          <LiveTranscript lines={live.transcript} a={a} />
          <BehaviourPanel a={a} />
          <ConversationTimeline a={a} />
        </div>
        <div className="col">
          <RecommendationPanel a={a} />
          <EntitiesPanel a={a} />
          <Statistics stats={live.stats} />
          <PastIncidents incidents={live.incidents} />
        </div>
      </div>
    </>
  );
}
