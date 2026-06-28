// Synthesized alert beep via the Web Audio API — no audio asset needed.
// Browsers block audio until a user gesture, so call enable() from a click.
import { useCallback, useEffect, useRef, useState } from "react";

export function useAlertSound() {
  const ctxRef = useRef<AudioContext | null>(null);
  const [muted, setMuted] = useState<boolean>(() => localStorage.getItem("ss_muted") === "1");

  useEffect(() => { localStorage.setItem("ss_muted", muted ? "1" : "0"); }, [muted]);

  const enable = useCallback(() => {
    if (!ctxRef.current) {
      const AC = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      ctxRef.current = new AC();
    }
    if (ctxRef.current.state === "suspended") void ctxRef.current.resume();
  }, []);

  // Two urgent rising beeps.
  const play = useCallback(() => {
    if (muted) return;
    const ctx = ctxRef.current;
    if (!ctx) return;
    const now = ctx.currentTime;
    [0, 0.22].forEach((offset, i) => {
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "square";
      osc.frequency.setValueAtTime(i === 0 ? 740 : 988, now + offset);
      gain.gain.setValueAtTime(0.0001, now + offset);
      gain.gain.exponentialRampToValueAtTime(0.18, now + offset + 0.03);
      gain.gain.exponentialRampToValueAtTime(0.0001, now + offset + 0.18);
      osc.connect(gain).connect(ctx.destination);
      osc.start(now + offset);
      osc.stop(now + offset + 0.2);
    });
  }, [muted]);

  return { play, enable, muted, setMuted };
}
