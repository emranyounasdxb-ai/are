# ALIYAS Real Estate (ARE) Repository Rules

## Scope and authority

- This repository is the local ARE website repository at `C:\Projects\are`. Do not inspect, change, or operate another project from an ARE task.
- Authority order is: current explicit owner instruction; `ARE ARCHITECTURE BLUEPRINT v1.0.md`; `ARE DESIGN SYSTEM v1.0.md`; verified repository/environment evidence; then non-conflicting repository documentation.
- Read both approved ARE documents completely before planning or implementation that they govern. Treat `MUST`/`MUST NOT` as binding, keep `PENDING` unresolved, and do not pull `FUTURE` work forward.
- Execute only the bounded task that the owner approved. Do not infer approval for adjacent features, infrastructure, integrations, records, or documents. Stop and report conflicts, missing authority, or unsafe state instead of guessing.
- A completed approved boundary must not be broadly refactored without a reproducible defect and explicit owner authorization.

## Repository and runtime safety

- Work locally only. Do not use Codex Cloud or delegate unless the owner explicitly changes this rule.
- NexaHR is out of scope. Port `3000` is protected: never bind ARE to it, stop/restart its process, free it, or change NexaHR configuration. Read-only status checks are permitted.
- ARE host ports use the locked `50001–50017` registry, with `50018–50030` reserved. Bind exposed development ports to `127.0.0.1`; never kill an unrelated process to resolve a conflict.
- Do not expose secrets. Never print secret values or commit credentials. Report secret/environment filenames and safe variable names only when a task authorizes inspection.
- Do not autonomously commit, push, open a PR, deploy, change production, or operate production credentials or services.

## Product and content integrity

- Keep the initial architecture simple: separate public and Admin web surfaces, one modular FastAPI backend, PostgreSQL authority, and only the approved supporting services.
- Do not introduce speculative systems, microservices, providers, integrations, or dependencies.
- Do not invent property records, projects, prices, availability, statistics, contact details, addresses, testimonials, claims, awards, guarantees, or other business facts. Do not hardcode business records as frontend truth.
- Preserve English/Arabic parity, complete RTL behavior, WCAG 2.2 AA intent, and the approved Future Heritage 2030 design authority. Never guess or recolor the master logo.

## Validation and reporting

- Inspect before changing. Preserve unrelated work and stop if a task's allowed paths cannot be respected safely.
- Validate only with commands appropriate to the authorized phase. Report observed evidence; never convert an unrun or blocked check into a pass.
- Before handoff, review the actual changed-file set, run applicable content/format checks and `git diff --check` when Git exists, then report scope, files, validation, blockers, pending decisions, and every intentionally unexecuted delivery or operational step.
