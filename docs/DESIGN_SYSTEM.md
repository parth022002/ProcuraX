# ProcuraX Design System — Website Refresh v2

## Product context
ProcuraX is an AI-native supply-chain and procurement decision-intelligence platform. The flagship PoC is supplier disruption decision intelligence: sense signals, predict risk, quantify exposure, simulate mitigation options, recommend using evidence, govern decisions, prepare actions and learn from outcomes.

## Creative direction
A light-first editorial SaaS surface paired with a vivid, mid-dark product visual. The visual identity should feel like intelligent decision software, not a transport operator or a consumer-commerce app. Use the supplied neon ProcuraX emblem only as a contained hero visual; do not scatter the full artwork throughout the UI. The rest of the experience uses abstract signal paths, data nodes, small charts and precise interface elements.

Reference synthesis:
- Linear / Notion: clear information hierarchy, calm working surfaces and task-oriented navigation.
- Heron AI / Epiminds: agent workflow and evidence progression.
- Spline / Luma / Active Theory: one memorable, controlled visual moment and subtle dimensionality.
- SharpLink-style metric transparency: show units, assumptions and evidence, not unsupported outcome claims.

These are design inspirations, not an attempt to duplicate any one site.

## Palette — Website Refresh v2
- Canvas / warm white: `#F7F8F5`
- Paper: `#FFFFFF`
- Ink / main text: `#151B2C`
- Mid-dark / product panels: `#171D37`
- Secondary text: `#657084`
- Hairline border: `#E2E6E8`
- Ocean teal: `#0AA995` (primary product action / connected signal)
- Deep teal: `#087F78` (button and link contrast)
- Cyan: `#55DCE5` (data connection and chart highlight)
- Citron: `#D9FA78` (rare high-energy emphasis / selected state)
- Intelligence violet: `#8B7CFF` (AI/agent activity)
- Coral: `#FF916F` (critical signal illustration; pair with a label)
- Signal amber: `#FFBF69` (review/attention)

Use 60/30/10 as a loose composition guide: neutral surfaces first, ink/dark panels second, colourful accents only where meaningful. Do not use every accent in each component. Avoid neon glow in the working dashboard; reserve it for the hero emblem and small, intentional motion moments.

## Typography
- Headings: Manrope, with a system sans-serif fallback.
- Body: DM Sans, with a system sans-serif fallback.
- Tiny technical labels: DM Mono, used sparingly for status metadata.
- Headlines should be tight but readable; body line-height should favour scanning and decision-making.

Fonts are loaded from Google Fonts with local/system fallbacks. The interface should remain legible if the font request fails.

## Website sections
1. Sticky-style responsive navigation and ProcuraX signal-node wordmark.
2. Hero: business outcome headline, two clear CTAs, supplied neon emblem in a dark contained panel, and three small evidence/risk/approval chips.
3. Eight-stage Sense → Predict → Quantify → Simulate → Recommend → Govern → Act → Learn ribbon.
4. Product dashboard preview with synthetic labels and an illustrative trend chart.
5. Interactive stage explorer. Selecting a stage changes the explanation panel.
6. Four capability cards with mild hover lift and contextual accents.
7. Interactive mitigation scenario comparison with clear illustrative-data labelling.
8. Dark governance section explaining the bounded Critic retry and human escalation.
9. Trust strip and final CTA.
10. Existing workspace preview remains available from the public website.

## Motion principles
- Use the hero art float, background glows/orbits, staggered entrance, chart-line draw, small status pulses, route-node motion, and card hover lift as the main motion vocabulary.
- Every motion must support hierarchy or explain a data/process relationship. Avoid constant particles, unnecessary parallax, animated noise, or motion in every component.
- Respect `prefers-reduced-motion: reduce`; remove nonessential animation and smooth scrolling.
- Do not animate real operational values in a way that could imply a live measurement. Demo values remain marked illustrative/synthetic.
- Keep the hero's dark 3D art contained; primary website surfaces stay light.

## Application design
- Calm, high-contrast data surfaces. Use navy/ink for headings and navigation, teal for primary action, violet for AI-state highlighting, amber/coral for review/critical states, green/mint for completed/approved states.
- Status must always include text or an icon; never rely on colour alone.
- Tables expose sort/filter states, timestamps, source attribution and empty/error states where applicable.
- Scenario options show cost, risk, lead time and service implications with assumptions available for inspection.
- The Critic evaluates evidence sufficiency; the policy engine enforces permissions. Keep human approval explicit.
- All demo values are synthetic/illustrative and must not be represented as validated model outputs or measured business results.

## Components and spacing
- Base spacing scale: 4, 8, 12, 16, 24, 32, 48, 64, 96 px.
- Cards: 14–22 px radii depending on importance; thin borders and subdued shadows.
- Buttons: one primary action per main panel, visible keyboard focus, disabled/loading states.
- Charts: units, period, accessible description and data source label.
- Avoid rainbow charts. Use a maximum of two data-series colours plus semantically meaningful status colours.

## Accessibility and responsive behaviour
- Semantic landmarks, headings in order, button labels and meaningful alt text.
- Visible focus rings and keyboard-operable stage/scenario controls.
- Contrast target WCAG AA for text and essential UI controls.
- Desktop layouts are multi-column; tablet collapses secondary panels; mobile becomes a single-column flow with a four-across stage selector and horizontally scrollable process ribbon where required.
- Check reduced-motion preferences and do not convey state through colour alone.

## Current asset
- `frontend/public/procurax-neon-emblem.webp` — optimised 1100px WebP of the supplied neon emblem. Used in the public hero only.
