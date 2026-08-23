---
name: are-3d-ar-implementation
description: Plan, implement, or audit explicitly approved ALIYAS Real Estate 3D models, GLB/glTF assets, 360 tours, WebGL, WebXR, AR, and scroll-driven spatial experiences. Use only for authorized post-MVP spatial work with rights-cleared assets and accessible fallbacks; do not use for a normal Embla image slider, ordinary CSS decoration, general Motion animation, backend work, or unapproved engine selection.
---

# ARE 3D and AR Implementation

## Confirm the post-MVP authority

Read the current owner instruction and relevant repository authorities before planning, installing, implementing, or auditing:

- `AGENTS.md`
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`
- `ARE DESIGN SYSTEM v1.0.md`
- `docs/ARE_FOUNDATION_LOCK.md`
- `docs/ARE_DESIGN_OWNER_DECISIONS.md`

Treat 3D, 360-view, WebXR, and AR as optional post-MVP work. Stop unless the specific experience, platform, asset, and change boundary are explicitly approved.

Do not select or install Three.js, React Three Fiber, `model-viewer`, a tour platform, or another engine without owner approval. Do not reinterpret ordinary image sliders, CSS decoration, or public Motion effects as 3D work.

## Protect property truth and asset rights

- Require an owner-approved, rights-cleared source asset and its non-sensitive provenance reference before runtime use.
- Preserve the approved ALIYAS identity; never recolor, reconstruct, or spatially reinterpret the official logo.
- Never reconstruct, complete, beautify, or misrepresent a real property beyond verified source material.
- Label conceptual or AI-generated media according to owner policy and never imply real-world accuracy, availability, specifications, views, finishes, location, or construction status.
- Do not invent an Arabic logo, wordmark, property detail, price, statistic, award, licence, partnership, or legal claim.

## Build progressive, accessible experiences

- Keep initial page rendering, navigation, facts, and enquiry actions independent of the 3D engine.
- Provide an accessible static poster or gallery fallback with equivalent essential information.
- Lazy-load heavy code, models, textures, environments, and tour media after user intent or safe viewport criteria.
- Preserve native scrolling and predictable browser or native navigation; never trap scrolling, focus, gestures, or back behavior.
- Support keyboard access, screen-reader labels and instructions, sufficient contrast, touch targets, and non-WebGL or unsupported devices.
- Respect operating-system reduced-motion preferences and offer a non-motion path to the same information.
- Keep Admin interfaces free of decorative 3D.

## Measure technical viability

Record device/browser/platform, route, asset identity, dimensions, polygon count, texture count and resolution, compression, transfer size, decode/load time, memory, frame behavior, battery/thermal observations, and fallback result as applicable.

Assess GLB/glTF validation, texture and geometry compression, draw calls, shader cost, interaction responsiveness, context loss, mobile memory, and cleanup. Do not accept a visually successful desktop demo as proof of mobile or production viability.

For scroll-driven spatial effects, preserve normal scrolling, avoid main-thread obstruction, use restrained transforms, and ensure all content remains understandable with the effect disabled.

## Preserve scope and runtime safety

- Use public web `50001` or Expo Metro `50018` only when the authorized task requires runtime testing. Preserve Admin `50002` and future API `50003`.
- Never bind or interfere with protected port `3000`.
- Exclude normal Embla galleries, ordinary CSS decoration, general Motion effects, backend/API implementation, marketing content, and deployment.
- Report measured local/device evidence without claiming production readiness or operational verification.
- Do not push, merge, deploy, or modify production unless explicitly authorized.
