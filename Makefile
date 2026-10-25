.PHONY: help setup dev dev-api dev-web test lint typecheck eval clean docker-up docker-down

VENV = .venv
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip
PYTEST = $(VENV)/bin/pytest
RUFF = $(VENV)/bin/ruff
MYPY = $(VENV)/bin/mypy

help:
	@echo "TrustCounsel AI - Development Task Runner"
	@echo "----------------------------------------"
	@echo "make setup       : Set up virtualenv, install backend and frontend dependencies"
	@echo "make dev         : Run backend and frontend locally in mock mode"
	@echo "make dev-api     : Run FastAPI backend server on :8000"
	@echo "make dev-web     : Run Vite React frontend on :5173"
	@echo "make test        : Run pytest automated test suite"
	@echo "make lint        : Run ruff linting checks"
	@echo "make typecheck   : Run mypy static type checking"
	@echo "make eval        : Run evaluation benchmark runner"
	@echo "make docker-up   : Launch PostgreSQL+pgvector, Redis, API, and Web in Docker"
	@echo "make docker-down : Tear down Docker containers"

setup:
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r services/api/requirements.txt
	$(PIP) install -r services/api/requirements-dev.txt
	cd apps/web && npm install

dev-api:
	$(PYTHON) -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload

dev-web:
	cd apps/web && npm run dev

dev:
	@echo "Starting TrustCounsel AI (Mock Mode)..."
	$(PYTHON) -m uvicorn services.api.main:app --host 0.0.0.0 --port 8000 --reload

test:
	$(PYTEST) tests/ -v

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) services/api

eval:
	$(PYTHON) -m services.api.eval.runner --dataset legal_qa_contracts_v1

docker-up:
	docker compose up -d --build

docker-down:
	docker compose down -v

clean:
	rm -rf __pycache__ .pytest_cache .ruff_cache .mypy_cache
