---
name: are-mobile-implementation
description: Implement or review the ALIYAS Real Estate customer mobile application with React Native and Expo for Android and iOS, including Expo Router, native layouts and touch interaction, Reanimated and Gesture Handler motion, English/Arabic RTL, accessibility, reduced motion, mobile performance, and development-build or device verification. Use only for ARE mobile work in this repository; do not use for Next.js or web work, backend or database work, infrastructure or deployment, store submission, credentials or signing, content creation, architecture expansion, or unapproved authentication, payments, notifications, 3D, or AR.
---

# ARE Mobile Implementation

## Establish authority

Before mobile work, read completely from the repository root:

- `AGENTS.md`
- `docs/ARE_FOUNDATION_LOCK.md`
- `docs/ARE_MOBILE_FOUNDATION.md`
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`
- `ARE DESIGN SYSTEM v1.0.md`
- `docs/ARE_IMPLEMENTATION_PLAN.md`

Treat those authorities and the current explicit owner instruction as binding. Stop and report conflicts instead of resolving them by assumption.

## Keep the native slice bounded

- Implement or review only the explicitly approved React Native and Expo slice for the customer Android/iOS application.
- Do not perform Next.js or web implementation, backend or database work, infrastructure or deployment, store submission, credential or signing management, or product-content creation.
- Do not expand into unapproved authentication, payments, notifications, staff functionality, 3D, AR, analytics, offline-first behavior, or another architecture or dependency.
- Do not create a WebView wrapper or a separate mobile backend.

## Preserve native boundaries

- Use React Native with Expo, TypeScript, and Expo Router under the approved, exactly pinned Expo compatibility set.
- Build native layouts and touch interactions. Do not import Next.js pages, Server Components, DOM components, CSS, Tailwind classes, browser-only code, or web Motion components.
- Reuse API contracts, types, validation schemas, localization data, and semantic token values only when real cross-platform reuse exists and the task authorizes the shared boundary.
- Keep API URLs environment-driven. Use the same planned FastAPI backend; never hardcode emulator, LAN, or production addresses.

## Translate the ARE design system

- Treat `ARE DESIGN SYSTEM v1.0.md` as the visual authority and translate its semantic colors, typography, spacing, radii, elevation, and motion into native tokens.
- Use native controls and interaction conventions while preserving the Future Heritage 2030 direction. Do not invent brand values, business content, or logo treatments.
- Support safe areas, responsive device dimensions, orientation and text-size changes, and practical performance on representative mid-range devices.

## Support both locales and accessibility

- Build English and Arabic together with complete RTL mirroring, correct reading order, directional-control behavior, and mixed-script handling.
- Support Dynamic Type or equivalent font scaling, screen readers, sufficient contrast, accessible names and states, and touch-friendly targets.
- Preserve equivalent information and actions across locales, platforms, device sizes, accessibility settings, and reduced-motion preferences.

## Use the approved mobile motion stack

- React Native Reanimated is the primary animation engine, and React Native Gesture Handler is the gesture foundation.
- Prefer opacity and transform, keep essential content usable without animation, and respect the operating system's reduced-motion preference.
- Keep gestures interruptible, avoid blocking the JavaScript thread, and verify behavior on Android and iOS development builds or representative devices as the task requires.
- Additional animation, gesture, carousel, 3D, or AR engines require explicit owner approval.

## Protect development boundaries

- Reserve `127.0.0.1:50018` for Expo Metro only when an approved task authorizes it; check the port read-only before binding.
- Preserve public web `50001`, Admin web `50002`, and planned API `50003`. Never use or interfere with protected port `3000`.
- Treat Android emulator, physical-device LAN, and iPhone testing as separate documented profiles. Do not expose services to `0.0.0.0`, alter networking, or kill another process to resolve a conflict.
- Local iOS simulator builds require macOS and Xcode. Do not claim iOS simulator verification from Windows.

## Validate and report

Run only checks authorized and relevant to the slice, such as formatting, lint, type checking, focused tests, Expo diagnostics, development builds, device behavior, RTL, accessibility, reduced motion, and performance.

Do not claim Android, iOS, device, accessibility, RTL, or performance completion when the corresponding verification was not performed. Do not commit, install packages, start Metro, log into services, create signing material, push, open a pull request, submit to a store, or deploy unless the individual task explicitly authorizes that action.

Report changed files, validation performed, platforms and devices checked, locale/accessibility/motion results, known limitations, blockers, and the next bounded recommendation.
