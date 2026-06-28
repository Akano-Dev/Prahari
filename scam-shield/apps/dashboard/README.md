# ScamShield Dashboard

Enterprise, dark-themed, real-time React dashboard. Subscribes to
`/ws/dashboard` and renders the live, explainable assessment: risk meter,
detected scam type, live highlighted transcript, behaviour analysis, conversation
timeline, caller + officer-claim check, recommendation, entities, statistics, and
past incidents.

```bash
npm install
VITE_API_BASE=http://localhost:8000 npm run dev   # http://localhost:5173
```

Sign in (registers on first use), then click **▶ Simulate incoming scam call** to
drive the whole pipeline end-to-end without the Android app — the dashboard
creates a call, streams a sample digital-arrest script over the call WebSocket,
and updates live as risk escalates.

## Components (`src/components/`)
`RiskMeter` · `ScamTypeBadge` · `LiveTranscript` · `BehaviourPanel` ·
`ConversationTimeline` · `CallerInfo` (incl. officer-claim check) ·
`RecommendationPanel` · `EntitiesPanel` · `Statistics` · `PastIncidents`.

State is centralised in the `useLiveCall` hook; the API/WS client is `src/api/client.ts`.
