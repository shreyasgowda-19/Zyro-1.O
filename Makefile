.PHONY: dev reset test test-backend test-frontend build migrate seed

dev:
	powershell -ExecutionPolicy Bypass -File ./scripts/dev.ps1

reset:
	python scripts/reset_demo.py

migrate:
	cd backend && python -m alembic upgrade head

seed:
	python scripts/seed_demo.py

test-backend:
	cd backend && python -m pytest -v

test-frontend:
	cd frontend && npx vitest run

test: test-backend test-frontend

build:
	cd frontend && npm run build
