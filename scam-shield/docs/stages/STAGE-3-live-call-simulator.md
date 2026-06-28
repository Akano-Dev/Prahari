# Stage 3 — Polished Live Incoming-Call Simulator

**Goal:** Replace the single "Simulate incoming scam call" button with a
**realistic, cinematic incoming-call experience** that streams a transcript
through the **real** detection pipeline so risk rises live, signals pop in, and
the Stage-2 alert fires. This is the honest stand-in for "real call detection"
(see boundaries — we never tap real calls or dial real numbers).

## Scope / tasks
- [ ] **Incoming-call screen**: ringing animation, caller ID (number, unknown
      flag, fake "location"), **Accept / Decline**, call timer on accept.
- [ ] **Scenario picker** (multiple scripts), all routed through the live WS →
      backend pipeline:
      - Digital arrest (CBI/customs parcel)
      - Bank/KYC verification fraud
      - Lottery/prize
      - Tech-support refund
      - **Legit call** (delivery/friend) — proves it does NOT false-positive.
- [ ] Hinglish + Hindi variants for at least one scenario (shows multilingual).
- [ ] **Free-text mode**: user types/pastes a line → streamed → scored live.
- [ ] Live UI: transcript bubbles with highlighted evidence, risk meter ramping,
      signal chips appearing as they fire, "what to do" updating.
- [ ] On scam threshold → trigger Stage-2 alert + sound; on call end → incident
      recorded (already happens server-side) and shown.

## Files
- `apps/dashboard/src/hooks/useLiveCall.ts` (scenarios, accept/decline, free-text)
- `apps/dashboard/src/pages/LiveCall.tsx` + `components/IncomingCall`,
  `components/CallStage`
- `apps/dashboard/src/data/scenarios.ts` (script library)
- (No backend change required — `/calls`, `/calls/{id}/utterance`, WS already
  support this.)

## Out of scope
- Real telephony / Twilio / Android (future, gated on owner providing a number +
  credentials; documented as the "real inbound" upgrade path).
- Engine changes → Stage 4.

## Acceptance criteria
- Selecting a scenario plays a believable incoming call; risk ramps in real time
  via the actual backend pipeline (not faked client-side).
- The legit scenario stays low-risk / "Safe".
- Free-text line gets scored live.
- Alert + sound fire on scam scenarios; incident appears afterward.
- `npm run build` passes.
