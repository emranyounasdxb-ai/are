# ARE API

The ARE API is the single modular FastAPI boundary for the public and Admin applications. PostgreSQL is the canonical authority; Redis is limited to temporary rate-limit state.

Configuration is environment-driven. See the repository `.env.example`; never commit populated credentials.
