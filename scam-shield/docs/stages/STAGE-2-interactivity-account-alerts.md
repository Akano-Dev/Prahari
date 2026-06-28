# Stage 2 — Routing, Account Page, Interactivity, Alert + Sound

**Goal:** Turn the single screen into a real **multi-page app** where every
element does something, add a proper **Account** area (profile + picture), and
fire an **interactive pop-up alert with a beep/alert sound** when a scam is
detected.

## Scope / tasks

### Navigation / pages
- [ ] Lightweight client routing (hash-based or `react-router-dom`) with a glass
      sidebar/nav: **Overview**, **Live Call**, **Incidents**, **Account**.
- [ ] Move existing panels onto the relevant pages; Overview = stats + recent
      incidents + quick actions.

### Account page (after login)
- [ ] Show the signed-in user: display name, email, member-since.
- [ ] **Profile picture**: upload/preview + remove. Backend gets
      `display_name` + `avatar` (base64/data-URL) on the `User` model with a
      `PATCH /auth/me` (or `POST /auth/avatar`) endpoint; in-memory + SQL repos
      both updated. Client falls back to a generated initials/gradient avatar.
- [ ] Editable display name; sign-out here too.

### Interactivity
- [ ] Clickable **signal** rows expand to show evidence spans + description.
- [ ] Tabs / collapsibles where panels are dense; hover/active states; toasts.
- [ ] Buttons actually act (open report, copy verdict, clear call, re-run).

### Alert + sound (explicit ask)
- [ ] When live risk crosses the scam threshold, show a **modal/pop-up alert**
      ("⚠ Likely scam — do not share OTP / transfer money") with the
      recommendation and a dismiss.
- [ ] Play an **alert/beep** via the Web Audio API (synthesized — no asset
      needed) on trigger; a mute toggle in the nav; respect autoplay rules
      (sound after first user interaction).

## Files
- `apps/dashboard/src/` — new `pages/`, `components/Nav`, `components/AlertModal`,
  `hooks/useAlertSound`, router wiring in `App.tsx`/`main.tsx`.
- `apps/dashboard/src/api/client.ts`, `types.ts` — profile/avatar calls + types.
- `services/api/app/domain/models.py`, `schemas/api.py`, `routes/auth.py`,
  `repositories/{memory,sql}.py` — avatar/display-name persistence.

## Out of scope
- Visual system itself (done in Stage 1 — reuse tokens/primitives).
- Simulator scenarios/ringing UX → Stage 3.
- AI/LLM → Stage 4.

## Acceptance criteria
- Routing works; each nav item shows a distinct page.
- Account page shows details + lets the user set/clear a profile picture that
  persists across reload (server-side).
- Detecting a scam pops the alert **and** plays a beep; mute works.
- `npm run build` passes; backend tests still green (+ a new avatar test).
