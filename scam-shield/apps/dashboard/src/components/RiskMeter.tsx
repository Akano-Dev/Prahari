import { useEffect, useRef, useState } from "react";
import type { RiskAssessment } from "../types";
import { riskColor } from "../format";

/** Smoothly counts the displayed number from its previous value to the target. */
function useCountUp(target: number, ms = 700) {
  const [val, setVal] = useState(target);
  const fromRef = useRef(target);
  useEffect(() => {
    const from = fromRef.current;
    const start = performance.now();
    let raf = 0;
    const tick = (t: number) => {
      const p = Math.min(1, (t - start) / ms);
      const eased = 1 - Math.pow(1 - p, 3);
      setVal(Math.round(from + (target - from) * eased));
      if (p < 1) raf = requestAnimationFrame(tick);
      else fromRef.current = target;
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [target, ms]);
  return val;
}

export function RiskMeter({ a }: { a: RiskAssessment | null }) {
  const s = a?.risk_score ?? 0;
  const display = useCountUp(s);
  const c = riskColor(s);
  return (
    <div className="panel meter">
      <h3>Live Risk</h3>
      <div className="dial" style={{ ["--v" as never]: s, ["--dial-c" as never]: c }}>
        <div className="inner">
          <div>
            <div className="score" style={{ color: c }}>{display}</div>
            <div className="band">{a?.band ?? "Awaiting call"}</div>
          </div>
        </div>
      </div>
      <div className="verdict" style={{ color: c }}>
        {a ? (a.is_scam ? "⚠ LIKELY SCAM" : "✓ Looks OK") : "—"}
      </div>
      <div className="small muted">confidence {a ? Math.round(a.confidence * 100) : 0}%</div>
    </div>
  );
}
