---
name: are-backend-api-implementation
description: Implement or review explicitly authorized ALIYAS Real Estate backend, database, REST API, search, and integration slices under the locked modular FastAPI architecture. Use for typed contracts, migrations, property or project APIs, search/filtering, inquiries, favorites, and shared web/mobile contracts; do not use for hero animation, frontend styling, marketing copy, deployment, 3D work, or an unapproved backend scaffold.
---

# ARE Backend and API Implementation

## Establish authority

Read the current owner instruction and the applicable repository authorities in full:

- `AGENTS.md`
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`
- `ARE DESIGN SYSTEM v1.0.md`
- `docs/ARE_FOUNDATION_LOCK.md`
- `docs/ARE_DESIGN_OWNER_DECISIONS.md`

Follow the locked modular-monolith direction before selecting or changing backend technology. Treat unresolved architecture, identifiers, authentication, retention, provider, and production-topology decisions as pending. Do not scaffold a database or backend until an explicit task authorizes it.

## Keep the domain slice bounded

Implement only specifically authorized property, project, community, inquiry, favorite, search/filter, integration, or shared-contract work. Do not invent modules, providers, workflows, roles, records, prices, availability, statistics, taxonomies, or production data.

Keep FastAPI as the planned domain and authorization boundary, PostgreSQL as canonical business authority, Redis as non-durable support, and workers for genuinely asynchronous tasks. Do not create a mobile-specific backend or move business truth into web/mobile clients.

## Build explicit contracts

- Define typed request and response models with safe, consistent error envelopes.
- Validate inputs and outputs at the boundary.
- Use stable identifiers and explicit public/admin read models.
- Implement deterministic pagination, filtering, sorting, and search semantics.
- Keep web and mobile contracts compatible without sharing framework-specific UI code.
- Document authorized API behavior and add focused automated tests.

Preserve publication, verification, rights, locale, and freshness rules in public responses. Never expose internal notes, private evidence, source payloads, secrets, stack traces, or personal data.

## Preserve data integrity and recoverability

- Use migrations for every schema change.
- Define database constraints, foreign keys, indexes, and transactions around real invariants.
- Verify upgrade and the task-approved rollback or forward-recovery path.
- Prevent lost updates and duplicate effects where concurrent or retryable actions require it.
- Add idempotency for retryable create/action endpoints and integrations where applicable.
- Keep material actions auditable without logging sensitive values.
- Validate file and media inputs, access, type, size, and storage boundaries when the slice includes them.

Enforce authentication and authorization server-side. Treat UI visibility as presentation, never permission. Do not select authentication, MFA, role grants, or session mechanics before their owner-approved decision.

## Protect local and delivery boundaries

- Use `127.0.0.1:50003` for the future API only when an approved task authorizes it. Preserve public web `50001`, Admin web `50002`, and Expo Metro `50018`.
- Never bind or interfere with protected port `3000`.
- Do not implement frontend styling, marketing content, 3D experiences, infrastructure, or deployment.
- Do not claim database, integration, production, or operational verification without measured evidence from the required environment.
- Do not push, merge, deploy, or modify production unless explicitly authorized.
