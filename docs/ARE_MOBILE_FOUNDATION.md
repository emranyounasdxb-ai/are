# ARE Mobile Foundation

## Purpose and scope

This document locks the planned foundation for one customer-facing native ARE application for Android and iOS from one React Native codebase. It is a documentation authority only: it does not authorize an `apps/mobile` scaffold, dependency installation, services, credentials, signing, store work, or feature implementation.

The owner's `ARE-MOB-00` decision supersedes the blueprint's earlier native-mobile exclusion only for this bounded mobile workstream. All other blueprint and design-system constraints remain in force.

## Application topology

| Path | Surface | Status |
| --- | --- | --- |
| `apps/public-web` | Customer-facing Next.js website | Existing |
| `apps/admin-web` | Browser-based administration application | Existing |
| `apps/mobile` | Customer-facing native Android and iOS application | Planned; not created by `ARE-MOB-00` |

The mobile application will use one cross-platform codebase. A staff or Admin mobile application is not approved, and the customer application must not be a WebView wrapper around the website.

## Approved technology baseline

- React Native with Expo and TypeScript.
- Expo Router for native navigation.
- Expo Development Build for production-grade local development.
- EAS Build as the planned signed Android and iOS build workflow.
- Expo SDK 57 as the approved initial scaffold line.
- Exact compatible patch versions remain unselected until `ARE-MOB-01`, when Expo compatibility tooling must verify and pin them. This task does not guess or install versions.

## Web/mobile separation

Mobile screens, navigation, layouts, controls, media behavior, and touch interaction must be implemented with native React Native capabilities. Do not reuse Next.js pages, Server Components, DOM components, CSS, Tailwind classes, browser-only modules, or the public website's Motion components in React Native.

Web Motion `13.1.1` remains limited to `apps/public-web`. Mobile is a separate native presentation surface, not an alternate rendering mode for either website.

## Code-sharing boundaries

Share API contracts, TypeScript types, validation schemas, localization data, and semantic design-token values only when real consumers and compatible runtimes demonstrate reuse. Do not force shared abstractions prematurely.

Do not share web pages, DOM-oriented UI, CSS, Tailwind classes, Server Components, or browser-only code with mobile. No shared package is authorized in `ARE-MOB-00`.

## Mobile design-system translation

`ARE DESIGN SYSTEM v1.0.md` remains the visual source of truth. Mobile must translate its semantic colors, typography, spacing, radii, elevation, and motion principles into native tokens and native touch components without redesigning the brand or inventing colors, fonts, styles, content, or logo treatments.

## Motion and gesture policy

- React Native Reanimated is the approved primary mobile animation engine.
- React Native Gesture Handler is the approved gesture foundation.
- Do not use DOM-based Motion components in React Native or introduce another mobile motion engine without owner approval.
- Respect the operating system's reduced-motion preference.
- Prefer transform and opacity, preserve essential content without animation, and validate performance on representative mid-range devices.

## Localization, RTL, and accessibility

English and Arabic are foundational and must receive equivalent functionality. Native implementation must support complete RTL mirroring, safe areas, Dynamic Type or equivalent font scaling, accessible touch targets, screen readers, sufficient contrast, logical reading and focus order, and reduced motion. Directional controls may mirror; logos, imagery, maps, and other non-directional content must not be mirrored mechanically.

## API and local networking model

Mobile will use the same planned FastAPI backend as the web applications. The planned API development port remains `50003`; a second mobile-specific backend is prohibited. API base URLs must be environment-driven and must never be hardcoded into mobile source.

`ARE-MOB-01` must document separate development profiles for Android emulator host mapping, approved physical-device LAN access, and iPhone testing. This foundation does not change the localhost-only policy, authorize `0.0.0.0`, select LAN addresses, or start the API.

## Port reservation

| Port | Purpose | Rule |
| ---: | --- | --- |
| `3000` | NexaHR | Protected; never use or alter |
| `50001` | Public web | Existing locked allocation |
| `50002` | Admin web | Existing locked allocation |
| `50003` | Planned FastAPI API | Existing locked allocation |
| `50018` | Future Expo Metro development server | Reserved; do not bind before an approved mobile scaffold task |

## Build and device-testing approach

Expo Development Builds are the approved local verification vehicle once the scaffold is authorized. EAS Build is the planned signed Android/iOS build path, but no EAS project, account login, credentials, signing material, identifiers, store record, or deployment configuration is authorized now.

Windows local native development supports Android tooling. Local iOS simulator builds require macOS and Xcode. Physical iPhone and EAS-based verification require later approved profiles, accounts, and authority.

## MVP scope

The planned customer mobile MVP contains only:

- Property and project discovery.
- Search and filtering.
- Property details.
- Native image galleries and sliders.
- Favorites and saved properties.
- Inquiry and contact actions.
- Map and location presentation.
- English and Arabic RTL experience.

## Deferred scope

The following are explicitly deferred and require separate owner-approved tasks:

- Authentication and customer accounts.
- Push notifications.
- Appointment scheduling.
- Payments.
- Agent or staff functionality.
- Offline-first architecture.
- Production analytics.
- App Store or Play Store submission.
- Any unapproved business workflow.

## 3D/AR readiness

Property 3D viewing and augmented reality are optional post-MVP capabilities. No mobile 3D engine is selected or authorized. Do not assume a website `model-viewer` implementation can be reused natively.

Actual property models must be approved and accurate; conceptual models must be clearly labelled. A later feasibility task must evaluate asset formats, native compatibility, representative device performance, fallbacks, accessibility, and download size before any engine or implementation is approved.

## Pending owner decisions

- Exact Expo SDK 57-compatible package patch versions.
- App identifiers, display naming, store ownership, privacy declarations, and signing authority.
- Expo, EAS, Apple, and Google account ownership and access policy.
- EAS project creation and build/distribution profiles.
- Approved emulator, physical-device LAN, and iPhone development profiles.
- Map provider, credentials, data terms, and fallback behavior.
- Authentication, accounts, notifications, payments, analytics, and other deferred product workflows.

## ARE-MOB-01 entry criteria

`ARE-MOB-01 — Minimal Expo Mobile Scaffold` may begin only when:

- The owner explicitly authorizes that task from a clean, verified repository state.
- Expo SDK 57 and compatible React Native, Expo Router, Reanimated, and Gesture Handler patch versions are verified with Expo compatibility tooling and pinned exactly.
- The minimal workspace change, Metro port `50018` preflight, and environment-driven API configuration are defined without creating a second backend.
- Android, physical-device, and iPhone verification profiles are documented with no invented credentials or network exposure.
- App identifiers, signing, EAS project creation, store work, and every deferred feature remain excluded unless separately approved.
