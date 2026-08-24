# ARE-ADM-01 Technical Decisions

Status: Implemented locally for the approved Admin CMS foundation.

- The versioned REST service lives in `services/api` and uses FastAPI, Pydantic, SQLAlchemy async sessions, Alembic, PostgreSQL and Redis.
- Authentication uses server-authoritative opaque sessions, an HttpOnly cookie, Argon2id password hashing, CSRF validation on mutations, origin-restricted CORS, login throttling and database revocation. No access token is stored in browser storage.
- Authorization uses relational roles and explicit permissions. The initial Super Admin is created interactively through the repository CLI; no default account or password is seeded.
- English and Arabic CMS content uses shared entities and relational locale rows. Public endpoints expose only Published properties and insights and only Open jobs.
- Public pages render CMS content on demand and degrade to honest empty states if the local API is unavailable; compilation does not depend on a running API.
- Property media management remains deferred. Records without approved media use a labelled media-neutral presentation.
- The three approved bilingual insight articles are seeded idempotently from the repository-controlled backend content payload. Public article rendering no longer uses the former static article array.
- Audit records contain actor/action/entity/time/correlation metadata and bounded before/after summaries; passwords, session tokens and full sensitive bodies are excluded.
- Local service bindings are `127.0.0.1:50003` (API), `127.0.0.1:50004` (PostgreSQL) and `127.0.0.1:50005` (Redis). Production secrets and secure-cookie enforcement remain environment controlled.
