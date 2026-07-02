# Jobify

**Jobify** is a full-stack job discovery and tracking platform that aggregates listings from company career pages and ATS systems (Greenhouse, Lever, Ashby, and others), deduplicates them, and layers in AI-native features — natural language search, vector-based skill matching, and resume tailoring — on top of a clean FastAPI backend.

Jobify is a ground-up rebuild of an earlier Spring Boot/Java + Node.js prototype, migrated to Python so the AI features can live natively in the backend instead of being bolted on.

---

## What Jobify Does

- Aggregates job listings directly from company career pages and ATS platforms — sources that often never surface on mainstream boards like LinkedIn or Indeed
- Deduplicates listings deterministically so the same job never appears twice, even across repeated pipeline runs
- Lets users search jobs in plain English ("remote React roles in Bangalore above 15 LPA") via an LLM-backed query parser
- Matches user skills to job descriptions using vector embeddings and cosine similarity, instead of brittle keyword/regex matching
- Tailors a user's resume against a specific job description with streamed LLM suggestions
- Tracks saved jobs and application status in a personal dashboard

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                         │
│                  React 18 + Vite + Tailwind                 │
└───────────────────────────┬───────────────────────────────────┘
                            │ HTTPS / REST (credentials included)
┌───────────────────────────▼───────────────────────────────────┐
│                        API LAYER                             │
│         FastAPI (Python 3.11+) — async, JWT via cookie       │
│     Routers → Services → SQLAlchemy Models (async ORM)       │
└──────────────┬─────────────────────────────┬─────────────────┘
               │                             │
┌──────────────▼──────────┐   ┌──────────────▼───────────────┐
│       DATA LAYER         │   │        PIPELINE LAYER        │
│  Supabase Postgres        │◄──│   Python scrapers (batch)    │
│  + pgvector extension     │   │   Scrape → Dedup → Upsert    │
│  Users · Jobs · Skills    │   │   ATS: Greenhouse, Lever...  │
└───────────────────────────┘   └───────────────────────────────┘
```

**Request lifecycle:**
1. React client sends a request with an HttpOnly session cookie attached automatically by the browser
2. FastAPI's auth dependency decodes and validates the JWT from the cookie
3. The relevant router delegates to a service, which queries the database via async SQLAlchemy
4. Supabase Postgres returns data; FastAPI serializes it as JSON
5. Independently, Python pipeline scripts scrape ATS sources on a schedule and upsert fresh listings into the same database

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, Vite, Tailwind CSS |
| Backend | FastAPI (Python 3.11+), managed with `uv` |
| Database | Supabase (PostgreSQL + `pgvector`), via async SQLAlchemy + `asyncpg` |
| Migrations | Alembic |
| Auth | JWT in `HttpOnly; Secure; SameSite=Strict` cookies |
| Password hashing | `passlib` (bcrypt) |
| API key encryption | `cryptography` (Fernet / AES) |
| AI layer | LLM-based query parsing, text embeddings for skill matching, resume tailoring via streamed LLM output |

---

## Security Principles

These are non-negotiable design decisions, not defaults left in place by accident:

- **JWTs live in HttpOnly cookies, never `localStorage`.** JavaScript — including an attacker's injected script in an XSS scenario — cannot read an HttpOnly cookie. The browser attaches it to requests automatically.
- **Passwords are hashed, never encrypted.** One-way bcrypt hashing means even a full database leak doesn't expose usable passwords.
- **User-provided LLM API keys are encrypted, not hashed.** They need to be recoverable so the backend can use them on the user's behalf, so they're stored with reversible Fernet (AES) encryption under a master key that lives only in server-side environment variables — never in source control.
- **The LLM never writes or executes SQL.** Natural language queries are parsed into structured JSON filters only. The backend builds all SQL itself using parameterized queries, so the LLM has no path to injection or data exfiltration.
- **Deduplication is deterministic and enforced at the database level.** Each job gets a stable `external_id` (`company-ats-jobid`, no date component) with a `UNIQUE` constraint, and ingestion uses `ON CONFLICT ... DO UPDATE` as the final safety net — not just an application-layer check.

---

## Project Roadmap

| Phase | Scope | Status |
|---|---|---|
| 0–1 | Project skeleton, folder structure, health check endpoint | ✅ Done |
| 2–3 | User model, password hashing, API key encryption, Alembic migrations | ✅ Done |
| 4 | `/auth/register` and `/auth/login` routes | 🔜 Next |
| 5 | Job API — browsing, filtering, pagination | Planned |
| 5 (pipeline) | ATS scrapers, dedup/upsert pipeline | Planned |
| 6 | Vector search — `pgvector` embeddings for skill matching | Planned |
| 7 | AI chatbot — natural language search (LLM → JSON → parameterized SQL) | Planned |
| 8 | Resume upload/tailoring with streamed LLM suggestions | Planned |
| 9 | "For You" personalized feed | Planned |
| 10 | Polish, error boundaries, deployment (Vercel + Render + Supabase) | Planned |

---

## Getting Started

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) for dependency management
- Node.js 18+ (frontend)
- A Supabase project with the `pgvector` extension enabled

### Backend Setup

```bash
git clone <your-repo-url>
cd jobify
uv sync
```

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://<user>:<url-encoded-password>@<supabase-pooler-host>:6543/postgres
ENCRYPTION_KEY=<generate with the command below>
JWT_SECRET=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
```

Generate an encryption key:
```bash
uv run python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

> **Note:** If your database password contains special characters (`@`, `#`, `%`, etc.), URL-encode it before placing it in `DATABASE_URL`, or connection parsing will fail.

Run migrations:
```bash
uv run alembic upgrade head
```

Start the dev server:
```bash
uv run fastapi dev app/main.py
```

Visit `http://localhost:8000/health` — should return `{"status": "ok"}`.

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend `.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
```

---

## Project Structure

```
jobify/
├── app/
│   ├── main.py                 # FastAPI app, CORS config
│   ├── core/
│   │   ├── config.py           # env var loading via pydantic-settings
│   │   └── security.py         # password hashing, API key encryption
│   ├── db/
│   │   └── database.py         # async engine, session dependency
│   ├── models/                 # SQLAlchemy models
│   ├── schemas/                # Pydantic request/response models
│   ├── api/routes/             # FastAPI routers
│   └── services/                # business logic
├── pipeline/
│   ├── scrapers/                # per-ATS scraping logic
│   └── dedup.py                 # external_id generation, upsert logic
├── alembic/                     # database migrations
├── frontend/                    # React + Vite + Tailwind app
└── .env                         # local secrets (never committed)
```

---

## License

TBD