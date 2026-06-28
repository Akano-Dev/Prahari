import type { RiskAssessment } from "../types";
import { highlight } from "../format";

export function LiveTranscript({ lines, a }: { lines: string[]; a: RiskAssessment | null }) {
  const snippets = (a?.signals ?? []).flatMap((s) => s.evidence.map((e) => e.text));
  return (
    <div className="panel">
      <h3>Live Transcript {a?.languages?.length ? `· ${a.languages.join(", ")}` : ""}</h3>
      <div className="transcript">
        {lines.length === 0 && <div className="muted small">No audio yet. Start or simulate a call.</div>}
        {lines.map((line, i) => (
          <div className="utt" key={i} dangerouslySetInnerHTML={{ __html: highlight(line, snippets) }} />
        ))}
      </div>
    </div>
  );
}
