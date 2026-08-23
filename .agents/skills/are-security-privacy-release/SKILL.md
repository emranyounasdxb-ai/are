---
name: are-security-privacy-release
description: Review or implement explicitly authorized ALIYAS Real Estate security, privacy, and release-readiness controls. Use for authentication, authorization, headers, CSP, CORS, CSRF, injection, uploads, dependency risk, personal-data handling, or evidence-based release gates; do not use for ordinary property cards, SEO copywriting, general feature development, or unauthorized production, DNS, deployment, or infrastructure changes.
---

# ARE Security, Privacy, and Release

## Establish authority and authorization

Read the current owner instruction and the relevant repository authorities:

- `AGENTS.md`
- `ARE ARCHITECTURE BLUEPRINT v1.0.md`
- `ARE DESIGN SYSTEM v1.0.md`
- `docs/ARE_FOUNDATION_LOCK.md`
- `docs/ARE_DESIGN_OWNER_DECISIONS.md`

Distinguish review from implementation. For a review, report evidence without changing controls. For an explicitly authorized correction, apply the smallest remediation inside the approved paths and retest the finding. Do not turn ordinary feature work into a broad security program.

## Assess the authorized surface

Use current primary OWASP and relevant official platform guidance. Evaluate only the surfaces in scope, including as applicable:

- Authentication, secure session lifecycle, authorization, object-level access, and least privilege.
- Secret and environment-variable ownership, separation, rotation boundaries, and accidental exposure.
- CSP and other security headers, CORS, CSRF, XSS, injection, request validation, and output encoding.
- Rate limiting, bot/abuse protection, retry behavior, and idempotency.
- Upload validation, malware strategy, private-file authorization, and safe media processing.
- Dependency, lockfile, build, artifact, and supply-chain risk.
- Logs, traces, analytics, and audit records without credentials, tokens, unnecessary personal data, or private message/file content.

Never print, commit, copy, or request secret values when safe variable names and configuration evidence are sufficient.

## Preserve privacy and legal boundaries

Review cookie, consent, inquiry data, analytics, AI conversation, candidate-file, and retention boundaries only where authorized. Minimize personal data and keep access, deletion, restriction, and retention decisions explicit.

Use current authoritative sources for UAE privacy or legal requirements. Present legal conclusions as subject to owner and qualified legal approval; do not invent compliance claims, licences, consent language, retention periods, or jurisdictional guarantees.

## Report evidence and release state accurately

Classify each finding by severity, affected surface, evidence, reproducible condition, impact, and smallest remediation. Separate confirmed vulnerabilities from hardening suggestions and unverified risks.

Keep these states distinct:

- Implementation complete.
- Locally validated.
- Deployed.
- Operationally verified in the target environment.
- Production ready and owner-approved.

Do not infer a later state from an earlier one. A local audit, passing build, HTTP response, or absence of a scanner finding is not production proof.

## Protect operational boundaries

- Use only the task-authorized ARE ports: public `50001`, Admin `50002`, future API `50003`, or Expo Metro `50018`.
- Never bind, stop, reconfigure, scan beyond the approved scope, or otherwise interfere with protected port `3000`.
- Never make destructive, production, DNS, deployment, credential, or infrastructure changes without explicit authorization.
- Exclude ordinary UI design, SEO copywriting, unrelated feature development, and speculative provider selection.
- Do not push, merge, deploy, or modify production unless explicitly authorized.
