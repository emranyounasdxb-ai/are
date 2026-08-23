---
name: are-quality-performance-audit
description: Audit or explicitly fix ALIYAS Real Estate web and mobile quality using measurable responsive, accessibility, browser, device, and performance evidence. Use for ARE Core Web Vitals, RTL, interaction, rendering, bundle, motion, or mobile-performance work; do not use for property copywriting, backend feature development, unrelated redesign, or unrequested remediation.
---

# ARE Quality and Performance Audit

## Establish authority and mode

Read the current owner instruction and relevant repository authorities before testing or changing anything:

- `AGENTS.md`
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`
- `ARE DESIGN SYSTEM v1.0.md`
- `docs/ARE_FOUNDATION_LOCK.md`
- `docs/ARE_DESIGN_OWNER_DECISIONS.md`

Use the frontend or mobile implementation skill for platform-specific constraints when the tested surface requires it.

- Audit only when asked to audit. Do not repair findings.
- When explicitly asked to fix, reproduce the defect first and apply the smallest correction inside the authorized paths.
- Do not broaden an audit or fix into content creation, feature development, dependency replacement, or redesign.

## Define the evidence boundary

Record the tested URL or mobile route, build/runtime mode, environment, locale, viewport or device, browser/platform, network or CPU conditions when relevant, tool version, and timestamp. Preserve reproducible steps and concrete evidence for every failure.

Use existing browser, device, profiler, test, and repository tools when available. Do not install a new tool, package, browser, emulator, or service without explicit authorization.

## Verify the affected platforms

For public web and Admin web, inspect the applicable desktop, tablet, and mobile layouts in English and Arabic RTL. Check:

- Keyboard order, visible focus, semantic names/roles, screen-reader structure, contrast, touch targets, zoom, and reduced motion.
- Navigation, links, forms, validation, sliders, galleries, dialogs, filters, and interactive states.
- Browser console errors, failed or excessive network requests, hydration warnings, and cross-browser behavior required by the task.
- Loading, empty, stale, unavailable, success, and error states that exist in scope.

For mobile, use representative Android/iOS evidence authorized by the task. Check native layout, safe areas, font scaling, screen readers, touch targets, gestures, RTL, reduced motion, memory, rendering stability, and responsiveness. Do not claim iOS simulator verification from Windows.

## Measure performance

Use Lighthouse and field or lab Core Web Vitals evidence appropriate to the task. Record LCP, INP, CLS, and other relevant diagnostics without turning a single score into a universal verdict.

Inspect affected Next.js rendering mode, client JavaScript and bundles, hydration, fonts, images, caching, and third-party work. Review Motion, Embla, scroll effects, and any approved 3D surface for main-thread, layout, input, and loading cost. Review mobile rendering, gesture, memory, battery, and thermal impact when applicable.

Prefer a reproducible root cause over score chasing. Preserve server-first rendering, accessible fallbacks, native scrolling, and essential content without animation.

## Protect runtime and reporting boundaries

- Use public web `50001`, Admin web `50002`, future API `50003`, and Expo Metro `50018` only when the task authorizes the relevant runtime.
- Never bind, stop, reconfigure, or otherwise interfere with protected port `3000`.
- Stop applications and temporary listeners started by the task, and confirm their ports are free afterward.
- Never treat local, simulated, or lab results as proof of production performance or operational verification.
- Report findings by affected surface, severity, evidence, reproduction, user impact, and smallest remediation.
- Do not push, merge, deploy, or modify production unless explicitly authorized.
