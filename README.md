# The Final Third

A football match prediction platform delivering probabilistic forecasts, calibration-tracked predictions, and data-driven insights for the Premier League and the European competitions its clubs play in.

> **Demo Mode is enabled by default.** The site renders with a small set of seed fixtures so it works the moment you boot it. Set `DEMO_MODE=false` in your backend environment to switch to live data.

---

## Table of contents

1. [What this is](#what-this-is)
2. [Tech stack](#tech-stack)
3. [Local development setup](#local-development-setup)
4. [Environment variables](#environment-variables)
5. [Project structure](#project-structure)
6. [Data sources](#data-sources)
7. [Deployment](#deployment)
8. [Pushing to GitHub](#pushing-to-github)
9. [How the model works](#how-the-model-works)
10. [Roadmap](#roadmap)
11. [License](#license)

---

## What this is

The Final Third is a portfolio-grade web application that:

- **Predicts** match outcomes (1X2), Both Teams To Score, Over/Under 2.5 goals, correct scorelines, selected player props, and end-of-season league positions
- **Tracks** every prediction it has ever made, with a public calibration curve and Brier-score comparison against bookmaker closing odds
- **Surfaces** statistical patterns ("Player X has 3+ shots in 10 straight matches") that are auto-mined from the data
- **Backtests** every model against five seasons of historical Premier League data with a walk-forward validation harness
- **Ships honest** — predictions are framed as statistical analysis, not betting tips. Calibration is treated as a first-class quality metric.

It is **not** a betting service and is not marketed as one. All references to bookmaker odds are for benchmarking only.

---

## Tech stack

| Layer | Tech |
| --- | --- |
| Frontend | Next.js 15 (App Router) · TypeScript · Tailwind CSS · shadcn/ui · Recharts · D3 · Framer Motion |
| Backend | Python 3.12 · FastAPI · SQLAlchemy 2 · Alembic · uv |
| Database | PostgreSQL 16 (local Docker, Supabase in production) |
| Modeling | NumPy · SciPy · scikit-learn · XGBoost · PyMC (scaffolded) |
| Ingestion | httpx · BeautifulSoup · pandas |
| Quality | ruff · mypy · eslint · prettier · pytest · vitest · pre-commit |
| Monitoring | Sentry (FE + BE) |
| Deploy | Vercel (FE) · Railway (BE + cron) · Supabase (DB) |

---

## Local development setup

### Prerequisites

You need these installed before you start:

- **macOS** (tested) — Linux works, Windows via WSL2 should work
- **Docker Desktop** 4.x+ — running before you start
- **Node.js** 20+ — `node --version`
- **Python** 3.12+ — `python3.12 --version`
- **uv** — `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **make** — comes with macOS Command Line Tools

### First-time setup

From the repo root:

```bash
# One command. Sets up env files, installs deps, starts containers, runs migrations, seeds demo data.
make setup

# Run the dev stack (frontend + backend + database)
make dev
```

When `make dev` completes you should be able to open:

- Frontend: <http://localhost:3000>
- Backend API docs: <http://localhost:8000/docs>
- Backend health: <http://localhost:8000/health>

A yellow **DEMO MODE** banner will be visible at the top of the frontend until you flip the env var.

### Useful commands

```bash
make verify          # Lint + typecheck + tests across both stacks. Use before commits.
make test            # Tests only
make lint            # Lint + format only
make typecheck       # Type-check only
make db-shell        # psql into the local DB
make db-reset        # Drop and recreate local DB, re-run migrations and seed
make ingest          # Manually trigger an ingestion run (live mode)
make train           # Train the active models from scratch
make backtest        # Run the backtest harness and write results to disk
make stop            # Stop all containers
make clean           # Stop containers and remove volumes (destroys local DB)
```

---

## Environment variables

Three `.env` files. Templates committed; real values never committed.

### `backend/.env`

Copy from `backend/.env.example` and fill in. Variables:

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `DATABASE_URL` | Yes | `postgresql+asyncpg://postgres:postgres@db:5432/finalthird` | Local default works as-is |
| `DEMO_MODE` | No | `true` | Set to `false` to use live data |
| `FOOTBALL_DATA_API_KEY` | Live mode only | — | Register at <https://www.football-data.org/client/register> (free) |
| `RAPIDAPI_KEY` | Live mode only | — | Register at <https://rapidapi.com/api-sports/api/api-football/> (free, 100 req/day) |
| `SENTRY_DSN_BACKEND` | No | — | From <https://sentry.io> project settings |
| `CORS_ORIGINS` | No | `http://localhost:3000` | Comma-separated |
| `LOG_LEVEL` | No | `INFO` | `DEBUG` for verbose |

### `frontend/.env.local`

Copy from `frontend/.env.example`. Variables:

| Variable | Required | Default | Notes |
| --- | --- | --- | --- |
| `NEXT_PUBLIC_API_URL` | Yes | `http://localhost:8000` | Backend URL |
| `NEXT_PUBLIC_SENTRY_DSN` | No | — | From Sentry frontend project |
| `NEXT_PUBLIC_DEMO_MODE` | No | `true` | Controls the banner only — actual data mode is backend-side |

### `.env` (root, docker-compose only)

Used by docker-compose. Defaults work for local. Override only if you have port conflicts.

```env
POSTGRES_PORT=5432
BACKEND_PORT=8000
FRONTEND_PORT=3000
```

---

## Project structure

```
the-final-third/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   ├── core/             # Config, logging, exceptions
│   │   ├── db/               # Models, session, base
│   │   ├── features/         # Rolling stats, rest days, H2H
│   │   ├── ingestion/        # Clients for the four data sources
│   │   ├── insights/         # Pattern miner + templated phrasing
│   │   ├── jobs/             # Scheduled tasks (ingest, retrain)
│   │   └── models/           # Dixon-Coles, XGBoost, Bayesian, ensemble
│   ├── alembic/              # Database migrations
│   ├── tests/                # pytest
│   ├── seed/                 # Demo Mode seed data (JSON)
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/
│   ├── app/                  # Next.js App Router pages
│   ├── components/           # React components
│   ├── lib/                  # API client, types, utilities
│   ├── styles/               # Tailwind + globals
│   ├── public/               # Static assets
│   ├── package.json
│   └── Dockerfile
├── .github/workflows/        # CI: lint + test on PR
├── docker-compose.yml
├── Makefile
├── LICENSE
└── README.md
```

---

## Data sources

All four are free. The site degrades gracefully if any one fails.

| Source | Role | Auth | Limit |
| --- | --- | --- | --- |
| [football-data.org](https://www.football-data.org/) | Live fixtures, results, standings | Free API key | 10 req/min |
| [API-Football](https://rapidapi.com/api-sports/api/api-football/) | Lineups, pre-match odds | RapidAPI key | 100 req/day |
| [Understat](https://understat.com/) | xG, shot data | Scraping (no auth) | Be polite |
| [Football-Data.co.uk](https://www.football-data.co.uk/) | Historical results + closing odds for backtest | None | Static CSV files |

**Demo Mode** uses a small bundled JSON dataset and makes zero network calls. Flip `DEMO_MODE=false` to switch to live ingestion.

---

## Deployment

The stack splits across three free-tier services.

### 1. Database — Supabase

1. Create a project at <https://supabase.com>.
2. From `Project Settings → Database`, copy the connection string (the URL-encoded one for connection pooling).
3. Save it as `DATABASE_URL` in Railway (next step). The backend uses asyncpg, so swap the `postgresql://` prefix for `postgresql+asyncpg://`.
4. Migrations run automatically as part of the Railway deploy hook.

### 2. Backend — Railway

1. Create a project at <https://railway.app>.
2. `railway login` from your terminal.
3. From the repo root: `cd backend && railway up`.
4. Set environment variables in the Railway dashboard — copy from `backend/.env.example`.
5. The cron jobs are defined in `railway.json` and run automatically (twice daily).

### 3. Frontend — Vercel

1. Push the repo to GitHub (instructions below).
2. Import the repo at <https://vercel.com/new>.
3. Set the root directory to `frontend/`.
4. Set environment variables:
   - `NEXT_PUBLIC_API_URL` → your Railway backend URL
   - `NEXT_PUBLIC_SENTRY_DSN` → optional
   - `NEXT_PUBLIC_DEMO_MODE` → `false` once live
5. Deploy.

### Monitoring — Sentry

1. Create two projects at <https://sentry.io>: one Node (frontend), one Python (backend).
2. Copy the DSNs into the env files above.

---

## Pushing to GitHub

```bash
# From the repo root:
git init
git add .
git commit -m "Initial scaffold"

# Create a new private repo on GitHub, then:
git remote add origin git@github.com:YOUR_USERNAME/the-final-third.git
git branch -M main
git push -u origin main
```

The `.gitignore` is configured to never commit `.env` files, node_modules, Python caches, model artifacts, or the local database volume.

---

## How the model works

For v1 the active model is **Dixon-Coles** — a Poisson-based bivariate match outcome model with a low-score correlation adjustment. Team attack and defense strengths are estimated by maximum likelihood on weighted historical data.

The architecture supports an **ensemble** of three models with a shared `BaseModel` interface:

1. **Dixon-Coles** (active in v1) — fast, interpretable, well-suited to football's score distribution
2. **XGBoost** (scaffolded, to be trained) — gradient boosting on engineered features
3. **Bayesian hierarchical** via PyMC (scaffolded) — full posterior with uncertainty quantification

The ensemble combines them by stacked logistic regression once all three are trained. Until they are, the ensemble passes through Dixon-Coles unchanged.

### Backtesting

Walk-forward validation across five Premier League seasons. Metrics reported:

- **Brier score** (multi-class, lower is better)
- **Log loss**
- **Calibration curve** (binned by predicted probability)
- **Top-pick accuracy**
- **Simulated betting P&L** vs closing market odds, flat-staking, with a prominent disclaimer

All backtest outputs are stored in the database and exposed via the `/api/track-record` endpoint.

### Insights

The insight engine is **rule-based with templated phrasing**. Every claim ("Palmer 3+ shots in 10 straight games") is the output of a deterministic query against the database. No LLM is used in v1 — when you add an API key later, the LLM will be constrained to *rephrase only*, never to invent stats.

---

## Roadmap

- **v1.0 (this scaffold)** — Dixon-Coles, demo mode, all four data sources stubbed, five page types
- **v1.1** — XGBoost trained and active in ensemble, Team and Player pages
- **v1.2** — PyMC Bayesian model active, in-play updates
- **v1.3** — Championship + Champions League non-PL teams
- **v2** — LLM-narrated insights, user accounts, fixture watchlists

---

## License

MIT — see [LICENSE](./LICENSE).
