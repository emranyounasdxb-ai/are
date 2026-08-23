# ARE Implementation Plan

## Planning rules

This is a dependency-aware sequence, not blanket implementation approval. Every phase is a separate bounded owner decision. `PENDING` decisions remain unresolved, `FUTURE` work stays deferred, and no phase may silently absorb work from a later phase.

## Phase 0 — Audit and Foundation Lock

- **Objective:** Establish verified repository/environment state and the minimum governing foundation before application code.
- **Included scope:** Complete source-document review; read-only repository/tool/port audit; `AGENTS.md`; current-state audit; foundation lock; this plan.
- **Explicitly excluded:** Git initialization, scaffold, source code, manifests, packages, services, browser work, runtime validation, commit, push, PR, or deployment.
- **Required validation:** Source hashes unchanged; only four authorized deliverables changed; Markdown/content consistency; Git checks when available; final port/service/package non-action confirmation.
- **Owner stop/approval gate:** Stop after Phase 0. Owner reviews the documentation and explicitly authorizes or changes the one proposed next task.

## Phase 1 — Minimal repository scaffold and reproducible local startup

- **Objective:** Create the smallest maintainable public/Admin/backend foundation with reproducible, localhost-only local startup.
- **Included scope:** Owner-authorized Git handling; compatibility verification and exact pins; minimal public/Admin Next.js and modular FastAPI shells; Docker Compose for only core active services; safe environment templates; locked ports; read-only port-preflight; basic GitHub Actions gates; startup documentation.
- **Explicitly excluded:** Business pages, final design, canonical property/content schema, production integrations, AI, analytics, OpenSearch, observability stack, deployment, and invented data.
- **Required validation:** Fresh documented setup; exact dependency installs; lint/type/unit/build smoke checks; backend health; Compose configuration; localhost bindings; conflict-safe port preflight; no use of port `3000`.
- **Owner stop/approval gate:** Owner accepts repository shape, pinned versions, reproducible startup evidence, and Git/CI baseline before design work.

## Phase 2 — Design tokens and essential shared UI primitives

- **Objective:** Turn the approved Future Heritage 2030 foundation into a minimal reusable bilingual component base.
- **Included scope:** Verified logo handling if the asset is supplied; color/type/spacing/radius/motion tokens; focus and reduced-motion behavior; essential layout, button, input, link, feedback, and locale/RTL primitives; focused component review.
- **Explicitly excluded:** Full page library, complete Admin system, final marketing content, property records, speculative variants, and route-specific one-off components.
- **Required validation:** Token consistency, contrast, keyboard/focus, 200% zoom, reduced motion, responsive checks, English/Arabic/RTL parity, and focused visual regression where useful.
- **Owner stop/approval gate:** Owner approves the palette application, typography, logo treatment, density, core controls, and Arabic direction before a homepage is composed.

## Phase 3 — Homepage vertical slice: desktop, mobile, English and Arabic/RTL

- **Objective:** Prove the design and application boundaries through one complete homepage experience across the required viewports/locales.
- **Included scope:** Homepage structure, navigation, hero/search presentation, selected approved sections, responsive behavior, English/Arabic routes, complete RTL, and honest empty/unavailable states using only owner-approved content/assets.
- **Explicitly excluded:** Invented business facts, production property feeds, full search, remaining public pages, Admin workflows, production analytics, maps, CRM, and AI service integration.
- **Required validation:** Desktop/mobile visual review, locale parity, RTL behavior, keyboard/screen-reader basics, WCAG checks, responsive images, performance budget evidence, build, and critical homepage smoke journey.
- **Owner stop/approval gate:** Owner performs the visual audit; no additional public pages proceed before a design decision is recorded.

## Phase 4 — Owner visual audit and design lock

- **Objective:** Resolve visual feedback and lock the proven reference patterns before broader implementation.
- **Included scope:** Owner review findings; bounded corrections to the homepage and shared components; approved reference screens; recorded accepted/deferred items.
- **Explicitly excluded:** New business capabilities, data model, additional routes, opportunistic redesign, or unapproved brand/content changes.
- **Required validation:** Re-run affected visual, responsive, accessibility, RTL, performance, build, and regression checks; confirm deferred items remain deferred.
- **Owner stop/approval gate:** Written owner acceptance of the homepage and reference components is required before canonical data/API work.

## Phase 5 — Minimum canonical property/content data and API foundation

- **Objective:** Establish the smallest approved PostgreSQL and REST authority needed for real public content without duplicate truth.
- **Included scope:** Approved minimum entities and invariants; Alembic migration; typed FastAPI contracts; publication/verification/freshness separation; minimal read paths; provenance and audit hooks required by the slice; safe approved test fixtures only.
- **Explicitly excluded:** Broad CRM, AI, ingestion engine, careers, analytics, OpenSearch, production imports, bulk Admin workflows, and speculative schema.
- **Required validation:** Fresh migration and recovery path; constraints/indexes; Pytest unit/database/API integration; authorization/public-field boundaries; OpenAPI consistency; no frontend business-data authority.
- **Owner stop/approval gate:** Owner approves the ERD/business rules, public field contract, pricing/freshness policy, and evidence before expanding page coverage.

## Phase 6 — Remaining approved public pages and search experience

- **Objective:** Build only the owner-approved public discovery and content routes on the canonical API.
- **Included scope:** Approved listing/detail/project/developer/location/content/contact routes; PostgreSQL search/filter/sort/pagination; localized URLs and SEO fundamentals; honest enquiry states; approved media only.
- **Explicitly excluded:** Unapproved categories/providers, OpenSearch, autonomous imports, speculative saved-search/account features, invented listings, and production launch.
- **Required validation:** Representative API/search correctness; route/build tests; critical Playwright journeys; English/Arabic/RTL parity; SEO crawl controls; accessibility; responsive and performance budgets.
- **Owner stop/approval gate:** Owner accepts public scope, content truth, search relevance, locale parity, and page quality before Admin workflows expand.

## Phase 7 — Minimum approved Admin Dashboard workflows

- **Objective:** Provide the smallest secure operational control surface for the approved canonical records and publication flow.
- **Included scope:** Server-managed authentication/session foundation; approved RBAC; Admin shell; minimum create/edit/review/publish workflows; tables/forms/states; material audit evidence.
- **Explicitly excluded:** Unapproved bulk operations, broad CRM, AI management, ingestion, careers, marketing dashboards, provider integrations, and UI-only authorization.
- **Required validation:** Server-side permission and object-access tests; session/CSRF controls as applicable; create-review-publish E2E; validation/conflict handling; audit events; accessibility and RTL Admin checks.
- **Owner stop/approval gate:** Owner accepts role boundaries, workflow transitions, audit evidence, and operational usability before release hardening.

## Phase 8 — Security, accessibility, SEO, performance and release audit

- **Objective:** Verify the approved implementation against measurable release gates without assuming production readiness.
- **Included scope:** Threat/access review; dependency and secret checks; WCAG/RTL audit; technical SEO crawl; performance budgets/Core Web Vitals; backup/recovery evidence where implemented; release checklist and residual risks.
- **Explicitly excluded:** Automatic production deployment, unapproved providers/credentials, scope-expanding remediation, and a claim of production readiness without owner/operations evidence.
- **Required validation:** Complete affected test/build matrix; security and privacy evidence; keyboard/screen-reader review; SEO/canonical/hreflang/robots/sitemap checks; representative performance; restore/recovery checks where authorized.
- **Owner stop/approval gate:** Owner decides whether findings authorize a separate remediation or release task. No commit, PR, deployment, or production activation is implied.

## Proposed next task

The only proposed next task is:

`ARE-FND-01 — Minimal Local Repository Scaffold`

It requires explicit owner authorization and must resolve the pending Git initialization/default-branch decision before version-controlled scaffolding. It was not executed during Phase 0.
