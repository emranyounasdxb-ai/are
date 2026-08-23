# ARE Foundation Lock

## Status language

| Label | Meaning |
| --- | --- |
| `LOCKED` | Approved foundation constraint; do not change without explicit owner authority. |
| `PROVISIONAL` | Approved direction whose exact implementation must be verified in its bounded phase. |
| `PENDING` | Owner or architecture decision is missing; do not guess or implement it. |
| `FUTURE` | Intentionally deferred until an approved feature or measured need exists. |
| `EXCLUDED` | Not part of the approved initial architecture or current scope. |

## Product scope

- `LOCKED` ARE is one public UAE real-estate website, one secure browser-based ARE Admin Dashboard, and one planned customer-facing native mobile application for Android and iOS from a single codebase.
- `EXCLUDED` A staff/Admin mobile application and a WebView wrapper around the public website.
- `LOCKED` The product is data-driven. Public pages present approved canonical records; they are not a hardcoded business catalogue.
- `LOCKED` English and Arabic have equal product status, including complete RTL behavior.
- `LOCKED` Work is delivered through small, dependency-aware, owner-approved tasks with stop gates.
- `PROVISIONAL` Broader capabilities described by the blueprint require their own later scope and approval; their presence in the blueprint is not implementation authorization.

## Architecture boundaries

- `LOCKED` Public web and Admin web are separate deployable surfaces that may share approved tokens and reusable packages.
- `LOCKED` The customer mobile application is a separate native presentation surface and uses the same planned FastAPI backend; it must not create a mobile-specific backend.
- `LOCKED` One modular FastAPI backend enforces domain rules, contracts, authorization, and orchestration.
- `LOCKED` One PostgreSQL database is the canonical data authority.
- `LOCKED` Redis supports cache, coordination, rate-limit state, and queue support; it is not durable business truth.
- `LOCKED` Celery workers handle genuinely asynchronous work; normal request paths must not be moved to workers without need.
- `LOCKED` Start as a modular monolith. A browser must not depend directly on private backend internals, and frontends must not become a second business-data authority.
- `EXCLUDED` Multiple backend services or a microservice split without measured, owner-approved need.

## Technology baseline

Technology families are `LOCKED`. The approved frontend scaffold baselines are pinned below; other exact versions remain `PENDING` compatibility verification in their bounded phases.

| Area | Foundation status and baseline |
| --- | --- |
| Public web | `LOCKED` Next.js `16.3.2`, App Router, React, TypeScript |
| Admin web | `LOCKED` Next.js `16.3.2`, App Router, React, TypeScript |
| Customer mobile | `LOCKED` React Native with Expo, TypeScript, and Expo Router; Expo SDK 57 is the approved initial scaffold line, with exact compatible patch versions verified and pinned in `ARE-MOB-01` |
| Mobile build workflow | `LOCKED` Expo Development Build for production-grade development; `PROVISIONAL` EAS Build for later signed Android/iOS builds after account, identifier, and signing approval |
| Mobile motion and gestures | `LOCKED` React Native Reanimated and React Native Gesture Handler; reduced-motion support and performant opacity/transform animation are required |
| Public motion and sliders | `LOCKED` Motion is the approved animation system; Embla Carousel React is the approved slider engine. Additional animation engines require owner approval. |
| Styling and accessible UI | `LOCKED` Tailwind CSS with a lightweight accessible component system; shadcn/ui and Radix-based primitives where appropriate |
| Admin data/table handling | `LOCKED` TanStack Query and TanStack Table |
| Charts | `LOCKED` Recharts only where a chart materially helps |
| Forms | `LOCKED` React Hook Form and Zod |
| Localization | `LOCKED` English/Arabic; `PROVISIONAL` exact suitable Next.js i18n solution after verification |
| Backend | `LOCKED` Python, FastAPI, Pydantic, SQLAlchemy, Alembic |
| API | `LOCKED` REST and OpenAPI |
| Database/search | `LOCKED` PostgreSQL full-text search, `pg_trgm`, and approved indexes initially |
| Cache/queue/workers | `LOCKED` Redis and Celery |
| Local storage/email tests | `LOCKED` LocalStack S3 and Mailpit only when their active phase needs them |
| Local orchestration | `LOCKED` Docker Compose |
| Frontend tests | `LOCKED` Vitest where useful; Playwright for critical journeys |
| Backend tests | `LOCKED` Pytest |
| Component review | `PROVISIONAL` Storybook when the shared component foundation begins and the value justifies it |
| CI/CD | `LOCKED` GitHub Actions |
| Observability | `FUTURE` OpenTelemetry, Prometheus, and Grafana only when the relevant phase begins |
| Vector support | `FUTURE` `pgvector` only when an approved feature requires it |

Before production, recheck and explicitly approve the latest security-patched Next.js `16.3.x` release; do not change the locked baseline silently.

## Mobile foundation boundaries

- `LOCKED` Web Motion `13.1.1` remains limited to `apps/public-web`; DOM-based Motion components must not be reused in React Native.
- `LOCKED` Share API contracts, TypeScript types, validation schemas, localization data, and semantic design-token values only when real reuse exists.
- `LOCKED` Do not share Next.js pages, Server Components, DOM components, CSS, Tailwind classes, or browser-only code with mobile.
- `LOCKED` The ARE Design System remains the visual authority; mobile translates its semantic foundation into native tokens and touch components with English/Arabic parity, RTL, safe areas, font scaling, screen-reader support, contrast, accessible touch targets, and reduced motion.
- `FUTURE` Mobile 3D and AR require a dedicated post-MVP feasibility task; no engine is selected.

## Locked local port registry

All exposed development ports must bind to `127.0.0.1`, not `0.0.0.0`.

| Host port | ARE service | Standard container/internal port | Status |
| ---: | --- | ---: | --- |
| `50001` | Public website | `3000` | Locked core |
| `50002` | Admin Dashboard | `3000` | Locked core |
| `50003` | FastAPI backend | `8000` | Locked core |
| `50004` | PostgreSQL | `5432` | Locked core |
| `50005` | Redis | `6379` | Locked core |
| `50006` | LocalStack S3 | `4566` | Reserved for media phase |
| `50007` | Mailpit web UI | `8025` | Reserved |
| `50008` | Mailpit SMTP | `1025` | Reserved |
| `50009` | Celery Flower | `5555` | Reserved |
| `50010` | pgAdmin | `80` | Optional development profile |
| `50011` | Storybook | `6006` | Reserved for design-system phase |
| `50012` | Prometheus | `9090` | Reserved for observability phase |
| `50013` | Grafana | `3000` | Reserved for observability phase |
| `50014` | OpenTelemetry gRPC | `4317` | Reserved |
| `50015` | OpenTelemetry HTTP | `4318` | Reserved |
| `50016` | OpenSearch API | `9200` | Future only; do not activate |
| `50017` | OpenSearch Dashboard | `5601` | Future only; do not activate |
| `50018` | Expo Metro development server | — | Reserved for the approved mobile scaffold phase |
| `50019–50030` | Future ARE allocation | — | Reserved and unused |

Additional `LOCKED` port rules:

- `50001` is the final local public-website port.
- `50018` is reserved for future Expo Metro use and must not be bound before an approved mobile scaffold task.
- Swagger and ReDoc will later use `http://localhost:50003/docs` and `http://localhost:50003/redoc`.
- Celery workers and test runners do not receive permanent public host ports.
- Only active-phase services may run.
- Port `3000` belongs to NexaHR and must never be bound, stopped, restarted, freed, or reconfigured by ARE work.
- Because the registry overlaps the Windows dynamic-port range, Phase 1 must add a read-only port-preflight command/script that returns a clear conflict error. It must never kill a process or change Windows dynamic-port settings.

## Data authority and security

- `LOCKED` PostgreSQL-backed approved records are the business source of truth. Imported, translated, or AI-produced material is untrusted until the required validation and approval.
- `LOCKED` Business status, verification status, publication status, and dynamic-data freshness are separate concerns.
- `LOCKED` Unknown, unverified, or stale price/availability must not appear current; use an approved enquiry state instead.
- `LOCKED` Authentication and sessions are server-managed and secure. Access or refresh tokens must not be stored in browser local storage.
- `LOCKED` Authorization is enforced server-side. UI hiding is not authorization.
- `LOCKED` Least privilege, protected private files, safe input/file validation, secret management, auditability, and environment separation are foundational requirements.
- `LOCKED` Secrets and credentials are never hardcoded, committed, or printed.

## Design-system authority

- `LOCKED` `ARE DESIGN SYSTEM v1.0.md` is the visual and interaction reference for Future Heritage 2030.
- `LOCKED` The direction is premium, modern UAE real estate with mobile-first responsiveness, reusable tokens/components, English/Arabic parity, complete RTL, and a WCAG 2.2 AA target.
- `LOCKED` Loading, error, empty, stale, and unavailable states are designed explicitly.
- `LOCKED` Use authentic, rights-approved UAE property imagery. References may inspire structure but must not be cloned.
- `LOCKED` Preserve the ARE brown/tan/black/white visual authority; do not replace it with navy/gold. Digital Aqua remains limited to intelligent/live/map context.
- `PENDING` The approved master logo asset, exact logo colors, and approved lockups. Never guess, recolor, or recreate the logo.
- `PENDING` Final business content and claims. Layout work must not invent content to fill sections.

## Content truth restrictions

- `LOCKED` Do not invent property listings, projects, prices, availability, statistics, phone numbers, addresses, testimonials, partnerships, awards, claims, guarantees, or market facts.
- `LOCKED` Do not publish third-party text, logos, images, or documents without documented authority.
- `LOCKED` Frontend placeholders must be explicit, non-production, and never masquerade as approved business records.

## Testing baseline

- `LOCKED` Each bounded implementation phase defines proportional lint, format, type, unit, integration, build, and behavior checks.
- `LOCKED` Critical public/Admin journeys use Playwright when implemented; backend behavior uses Pytest; frontend units/components use Vitest where useful.
- `LOCKED` English/Arabic parity, RTL, accessibility, responsive behavior, error/data states, SEO, security, and performance are validated where affected.
- `LOCKED` A passing inspection or HTTP status alone is not proof of business, database, accessibility, or security behavior.

## Git and local workflow

- `LOCKED` Work remains inside `C:\Projects\are` and local unless separately authorized.
- `LOCKED` No autonomous commit, push, PR, deployment, production operation, or credential change.
- `LOCKED` Preserve unrelated work. Review changed paths and run `git diff --check` when Git exists.
- `PENDING` Git initialization, default branch, and remote because the audited directory is not currently a Git repository.

## Explicit exclusions

- `EXCLUDED` GraphQL, Kubernetes, microservices, Kafka, multiple backend services, and a separate vector database.
- `EXCLUDED` OpenSearch during initial implementation; it remains a measured future option only.
- `EXCLUDED` A third-party CMS as business-data authority.
- `EXCLUDED` Unnecessary SaaS dependencies, premature analytics infrastructure, speculative AI services, and placeholder production integrations.
- `EXCLUDED` Unapproved maps, email, storage, analytics, AI, CRM, hosting, or monitoring providers.
- `EXCLUDED` Hardcoded business records or invented business facts.

## Pending owner decisions

- `PENDING` Remaining phase-specific dependency versions beyond the approved frontend scaffold baseline.
- `PENDING` Exact Expo SDK 57-compatible package patch versions, mobile app identifiers, store ownership, privacy declarations, signing authority, EAS project/profile ownership, and mobile development-network profiles.
- `PENDING` Git initialization/default branch/remote.
- `PENDING` Exact authentication, session, MFA, role, and permission design.
- `PENDING` Canonical identifiers, archive/history rules, initial taxonomies, translations/source locale, localized URL structure, and price/availability freshness policy.
- `PENDING` Source/media rights process, lead routing/SLA, AI data/provider/retention, privacy/consent, and record-retention policy.
- `PENDING` Production hosting, storage, email, maps, analytics, monitoring, deployment topology, regions, and credentials.
- `PENDING` Master logo asset/colors/lockups and final approved business content.
- `PENDING` Numeric performance budgets, freshness limits, SLO, RPO, RTO, backup retention, and restore expectations.
