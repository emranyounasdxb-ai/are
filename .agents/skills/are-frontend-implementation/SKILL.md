---
name: are-frontend-implementation
description: Implement or review the ALIYAS Real Estate (ARE) frontend, including Next.js or React UI work, ARE page or component styling, responsive frontend review, English/Arabic RTL behavior, accessibility, and browser-based visual verification of ARE pages. Use only for ARE frontend work in this repository; do not use for backend or database implementation, infrastructure or deployment, legal or marketing content creation, unapproved architecture expansion, or unrelated repositories or websites.
---

# ARE Frontend Implementation

## Establish authority

Before frontend work, read completely from the repository root:

- `AGENTS.md`
- `docs/ARE_FOUNDATION_LOCK.md`
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`
- `ARE DESIGN SYSTEM v1.0.md`
- `docs/ARE_IMPLEMENTATION_PLAN.md`

Treat those authorities and the current explicit owner instruction as binding. Stop and report any conflict instead of resolving it by assumption.

## Keep the slice bounded

- Implement or review only the explicitly approved frontend slice.
- Do not expand one task into multiple pages, backend work, dashboards, APIs, deployment, or speculative features. Include an Admin surface only when it is the approved slice.
- Do not introduce an architecture, provider, dependency, integration, or feature that the task does not authorize.
- Stop after the requested slice. Do not broadly refactor completed approved boundaries without explicit authority and a reproducible defect.

## Preserve design and content truth

- Treat the approved architecture and design system as authoritative. Do not invent brand colours, typography, spacing systems, logo treatments, breakpoints, business claims, contact details, property listings, prices, testimonials, statistics, or legal content.
- Preserve the Future Heritage 2030 direction: premium UAE real estate, modern and futuristic but credible, strong editorial hierarchy, clean layouts, controlled whitespace, approved design tokens, and restrained motion.
- Avoid a generic template appearance. Do not copy the Homexa reference literally.
- Use only approved content. Clearly label placeholders as non-production, and never present invented data as real ALIYAS Real Estate information.
- Never guess, recolour, or recreate the master logo.

## Build a coherent frontend

- Reuse approved tokens and components.
- Avoid page-local duplicate styles, arbitrary colours, inconsistent spacing, unnecessary dependencies, and premature abstractions.
- Keep frontend code a presentation and interaction layer; do not make it a second source of business truth or couple browser code to private backend internals.
- Define honest loading, error, empty, stale, and unavailable states where the slice needs them.

## Support both locales

- Build English and Arabic support from the start.
- Implement complete RTL layout behavior, not text alignment alone.
- Prefer CSS logical properties where appropriate.
- Set correct text alignment, reading order, control direction, and directional-icon behavior.
- Do not hard-code layout assumptions that break Arabic or mixed-direction content.

## Meet accessibility and responsive expectations

- Target WCAG 2.2 AA with semantic HTML, keyboard navigation, visible focus states, accessible labels, sufficient contrast, reduced-motion support, and touch-friendly controls.
- Validate mobile, tablet, laptop, and wide-desktop layouts.
- Prevent horizontal overflow, clipped content, broken hierarchy, and desktop-only interactions.
- Preserve usable zoom, long-label behavior, and equivalent access to information across viewports and locales.

## Use the approved public motion stack

- Motion is the approved public-site animation library, and Embla Carousel React is the approved slider engine. Additional motion or carousel engines require owner approval.
- Use native browser scrolling. Use `whileInView` for appropriate entrance effects and `useScroll` with `useTransform` for approved scroll-linked effects.
- Animate text without fragmenting or duplicating its semantic screen-reader output. Use Next Image for animated imagery.
- Configure Embla and its content direction for RTL, and preserve equivalent controls and reading order.
- Respect the user's reduced-motion preference. Prefer opacity and transform, and keep animation inside small client islands.
- Never animate every section or hide essential content behind animation.

## Protect local ports

- Use `127.0.0.1:50001` for the public website.
- Use `127.0.0.1:50002` for the Admin frontend.
- Use `127.0.0.1:50003` for the API dependency.
- Use `127.0.0.1:50011` for Storybook only when separately approved.
- Never use or interfere with port `3000`.
- Check a required port read-only before binding it. Fail clearly on a conflict; never kill another process or alter Windows networking.

## Validate and report

After implementation, run only the relevant checks that are available and authorized:

- Formatting
- Lint
- Type checking
- Focused tests
- Relevant production build
- Browser console and network inspection
- Desktop, mobile, and RTL visual review
- Accessibility basics

Do not claim visual completion when browser verification was not performed. Clearly identify unverified or blocked checks.

Do not commit, push, open a pull request, deploy, install dependencies, or change production unless the individual task explicitly authorizes that action.

Report:

- Files changed
- Validation performed
- Browser routes checked
- Responsive, RTL, and accessibility result
- Known limitations
- Blockers
- Next bounded recommendation
