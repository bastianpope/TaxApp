# 📊 TaxApp

A freemium tax preparation web app for US federal + state taxes (Tax Year 2025).  
Calculates federal income tax, self-employment tax, state tax (IL / MN), generates an audit-risk score, and suggests deduction strategies across three aggressiveness levels (Conservative / Moderate / Aggressive).

> **Legal notice:** This app produces educational estimates only and does not constitute tax, legal, or financial advice. Always consult a qualified CPA or tax professional before filing.

---

## Features

| Feature | Free | Pro (signed in) |
|---------|------|----------------|
| Federal tax calculation | ✅ | ✅ |
| Schedule C (self-employment) | ✅ | ✅ |
| 3 aggressiveness scenarios | ✅ | ✅ |
| Comparison table | ✅ | ✅ |
| State tax (IL / MN) | 🔒 | ✅ |
| Audit risk score | 🔒 | ✅ |
| PDF export | 🔒 | ✅ |
| Save / load returns | — | ✅ |
| 2FA (TOTP) | — | ✅ |

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 (async) · PostgreSQL |
| Auth | JWT (httpOnly cookies) · Argon2 password hashing · pyotp TOTP |
| Frontend | Next.js 15 (App Router) · TypeScript · Tailwind CSS |
| PDF | ReportLab |
| Database | PostgreSQL 17 (Docker) |
| Tests | pytest · pytest-asyncio · httpx |

---

## Prerequisites

- **Python 3.12+**
- **Node.js 20+** (with npm)
- **Docker + Docker Compose** (for PostgreSQL)

---

## Quick Start

### 1. Clone the repo

```bash
git clone <repo-url>
cd TaxApp
```

### 2. Start PostgreSQL

```bash
docker compose up -d db
```

This starts Postgres 17 on `localhost:5432` with:
- **Database:** `taxapp`
- **User:** `taxapp`
- **Password:** `dev_password`

An optional pgAdmin UI is available at [http://localhost:5050](http://localhost:5050)  
(email: `admin@taxapp.local` / password: `admin`) — start it with `docker compose up -d pgadmin`.

### 3. Backend setup

```bash
cd backend

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

Create a `.env` file (optional — all values have safe defaults for local dev):

```ini
# backend/.env
DATABASE_URL=postgresql+asyncpg://taxapp:dev_password@localhost:5432/taxapp
JWT_SECRET_KEY=change_me_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Start the API server:

```bash
uvicorn main:app --reload
# → http://localhost:8000
# → http://localhost:8000/docs  (Swagger UI)
```

Tables are created automatically on first startup (dev mode).

### 4. Frontend setup

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3000
```

The frontend proxies API requests to `http://localhost:8000` via `next.config.ts`.

---

## Running Tests

```bash
cd backend
source .venv/bin/activate
pytest -v
```

94 tests covering:
- Federal tax brackets (all filing statuses)
- Schedule C / self-employment tax
- IL and MN state calculators
- Audit risk scoring (15-factor model)
- Aggressiveness engine (3-level recommendation taxonomy)
- Orchestrator integration
- API endpoints (calculate, export, auth, returns)

Lint:

```bash
ruff check .
```

TypeScript check:

```bash
cd frontend
npx tsc --noEmit
```

---

## Project Structure

```
TaxApp/
├── backend/
│   ├── api/            # FastAPI routers (calculate, auth, export, returns)
│   ├── auth/           # JWT + password security utilities
│   ├── db/             # SQLAlchemy engine, models, migrations (Alembic)
│   ├── engine/         # Tax engine (federal, states, audit risk, aggressiveness)
│   │   ├── federal.py
│   │   ├── state_il.py
│   │   ├── state_mn.py
│   │   ├── audit_risk.py
│   │   ├── aggressiveness.py
│   │   └── orchestrator.py
│   ├── tests/          # pytest suite (94 tests)
│   ├── main.py         # FastAPI app entry point
│   └── pyproject.toml
│
├── frontend/
│   ├── app/
│   │   ├── page.tsx            # Landing page
│   │   ├── return/[1-6]/       # 6-step wizard
│   │   ├── results/            # Tax results + scenarios
│   │   ├── auth/               # Login / register
│   │   ├── dashboard/          # Saved returns
│   │   └── settings/           # Account + 2FA
│   ├── components/             # Shared UI components
│   ├── context/                # ReturnContext, AuthContext
│   ├── lib/                    # API client, types, utils
│   └── package.json
│
└── docker-compose.yml          # PostgreSQL + pgAdmin
```

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `postgresql+asyncpg://taxapp:dev_password@localhost:5432/taxapp` | Async PostgreSQL connection string |
| `JWT_SECRET_KEY` | `dev_secret_change_in_production` | **Change this in production!** |
| `JWT_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `15` | Access token lifetime |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` | Refresh token lifetime |

### Frontend (`frontend/.env.local`)

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend base URL |

---

## API Overview

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/calculate` | Calculate taxes (all scenarios) |
| `POST` | `/api/export/pdf` | Generate PDF report |
| `POST` | `/api/auth/register` | Create account |
| `POST` | `/api/auth/login` | Login (sets httpOnly JWT cookie) |
| `POST` | `/api/auth/refresh` | Refresh access token |
| `POST` | `/api/auth/logout` | Clear auth cookies |
| `POST` | `/api/auth/totp/setup` | Begin 2FA setup (get QR code) |
| `POST` | `/api/auth/totp/confirm` | Confirm and enable 2FA |
| `DELETE` | `/api/auth/totp` | Disable 2FA |
| `GET` | `/api/returns` | List saved returns |
| `POST` | `/api/returns` | Save a new return |
| `GET` | `/api/returns/{id}` | Load a saved return |
| `PATCH` | `/api/returns/{id}` | Update a saved return |
| `DELETE` | `/api/returns/{id}` | Delete a saved return |

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Production Notes

1. **Change `JWT_SECRET_KEY`** to a random 64-byte hex string before deploying.
2. Run migrations with Alembic rather than relying on `Base.metadata.create_all`.
3. Set `CORS` origins in `main.py` to your actual frontend domain.
4. Enable HTTPS and set `Secure` + `SameSite=Strict` on cookies.
5. Use a managed Postgres service (RDS, Cloud SQL, Neon, etc.) instead of the Docker dev instance.

---

## License

This project is for educational purposes. Tax calculations are estimates only.
