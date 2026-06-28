# Stage 1 — Aurora-Glass UI Redesign + Design System

**Goal:** Replace the flat, lifeless dashboard with a modern **aurora-glass**
design system: animated aurora background, frosted-glass surfaces, neon accents,
a big bold hero, a glowing risk meter, and a real typographic scale. This stage
is **visual only** — no new pages, no new behaviour, no backend changes.

## Why
The product owner's #1 complaint: "Lifeless / soulless UI. Don't just use the
pre-assets." So Stage 1 is a ground-up restyle, not a tweak.

## Scope / tasks
- [ ] New design tokens in `theme.css`: aurora gradient layers, glass surface
      vars (`--glass`, `--glass-brd`, blur), neon accents, elevation, a type
      scale (display / h / body / mono), risk-band color ramp.
- [ ] Animated **aurora background** (CSS-only conic/radial gradient blobs that
      drift) behind a `backdrop-filter: blur` glass layer. Respect
      `prefers-reduced-motion`.
- [ ] **Glassmorphism** `.glass` card primitive; migrate `.panel` to it.
- [ ] **Hero banner** at the top of the dashboard: big bold headline, live
      status, primary action. Large display font weight (800–900).
- [ ] **Glowing risk meter**: gradient conic dial + outer glow whose color +
      intensity track the live score; animated number count-up.
- [ ] Restyle every existing component (transcript, behaviour bars, chips,
      timeline, stats, recommendation, incidents, login) to the new system —
      **same props, same data**, new look.
- [ ] Typography: pick a display + body stack. Prefer a bundled font
      (`@fontsource/*`) if npm registry is reachable; otherwise a strong
      system-font stack with heavy weights (must build offline either way).

## Files
- `apps/dashboard/src/theme.css` (rewrite — the design system)
- `apps/dashboard/src/App.tsx` (hero + layout shell; logic unchanged)
- `apps/dashboard/src/components/*.tsx` (class/markup restyle only)
- `apps/dashboard/index.html` (font preconnect/title if needed)

## Out of scope (do later)
- Routing / multiple pages → Stage 2
- Account page, avatar, alerts/sound → Stage 2
- Call simulator UX overhaul → Stage 3
- Any engine/AI change → Stage 4

## Acceptance criteria
- `npm run build` passes (tsc + vite), no new TS errors.
- Dashboard renders the aurora background, glass cards, hero, glowing meter.
- All existing data still displays; no behavioural regression.
- Works offline (no runtime CDN/font fetch required to render).
- Looks coherent at desktop and narrow (<1200px) widths.
