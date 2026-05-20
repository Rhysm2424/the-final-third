.PHONY: help setup dev stop clean verify test lint typecheck \
        db-shell db-reset ingest train backtest \
        install-backend install-frontend \
        deploy-frontend deploy-backend

# ============================================================
# Help
# ============================================================
help:
	@echo "The Final Third — make targets"
	@echo ""
	@echo "  Setup"
	@echo "    setup             First-time setup: env files, deps, containers, migrations, seed"
	@echo "    install-backend   Install backend Python deps via uv"
	@echo "    install-frontend  Install frontend Node deps"
	@echo ""
	@echo "  Run"
	@echo "    dev               Start the full stack (FE + BE + DB) with hot reload"
	@echo "    stop              Stop all containers"
	@echo "    clean             Stop and remove volumes (DESTRUCTIVE — wipes local DB)"
	@echo ""
	@echo "  Quality"
	@echo "    verify            Lint + typecheck + tests across both stacks"
	@echo "    test              Tests only"
	@echo "    lint              Lint + format only"
	@echo "    typecheck         Type-check only"
	@echo ""
	@echo "  Data"
	@echo "    ingest            Run live ingestion (requires API keys, ignores demo mode)"
	@echo "    train             Train models"
	@echo "    backtest          Run the backtest harness"
	@echo ""
	@echo "  Database"
	@echo "    db-shell          psql into the local DB"
	@echo "    db-reset          Drop and recreate DB, re-migrate, re-seed"
	@echo ""
	@echo "  Deploy"
	@echo "    deploy-backend    Deploy backend to Railway"
	@echo "    deploy-frontend   Deploy frontend to Vercel"

# ============================================================
# Setup
# ============================================================
setup:
	@echo "→ Preparing environment files..."
	@test -f backend/.env || cp backend/.env.example backend/.env
	@test -f frontend/.env.local || cp frontend/.env.example frontend/.env.local
	@test -f .env || cp .env.example .env
	@echo "→ Installing backend dependencies..."
	@$(MAKE) install-backend
	@echo "→ Installing frontend dependencies..."
	@$(MAKE) install-frontend
	@echo "→ Building containers..."
	docker compose build
	@echo "→ Starting database..."
	docker compose up -d db
	@sleep 3
	@echo "→ Setup complete. Run 'make dev' to start the full stack."

install-backend:
	cd backend && uv sync

install-frontend:
	cd frontend && npm install

# ============================================================
# Run
# ============================================================
dev:
	docker compose up

stop:
	docker compose down

clean:
	docker compose down -v
	@echo "All containers and volumes removed."

# ============================================================
# Quality
# ============================================================
verify: lint typecheck test
	@echo "✓ All checks passed."

test:
	@echo "→ Backend tests..."
	cd backend && uv run pytest -q
	@echo "→ Frontend tests..."
	cd frontend && npm run test -- --run

lint:
	@echo "→ Backend lint..."
	cd backend && uv run ruff check . && uv run ruff format --check .
	@echo "→ Frontend lint..."
	cd frontend && npm run lint

typecheck:
	@echo "→ Backend typecheck..."
	cd backend && uv run mypy app
	@echo "→ Frontend typecheck..."
	cd frontend && npm run typecheck

# ============================================================
# Data
# ============================================================
ingest:
	docker compose exec backend python -m app.jobs.ingest_all

train:
	docker compose exec backend python -m app.jobs.train_models

backtest:
	docker compose exec backend python -m app.jobs.run_backtest

# ============================================================
# Database
# ============================================================
db-shell:
	docker compose exec db psql -U postgres -d finalthird

db-reset:
	docker compose down -v db
	docker compose up -d db
	@sleep 3
	docker compose exec backend alembic upgrade head
	docker compose exec backend python -m app.seed_loader

# ============================================================
# Deploy
# ============================================================
deploy-backend:
	@echo "→ Deploying backend to Railway..."
	cd backend && railway up

deploy-frontend:
	@echo "→ Deploying frontend to Vercel..."
	cd frontend && vercel --prod
