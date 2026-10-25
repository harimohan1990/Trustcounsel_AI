# ADR 004: Monorepo Structure with Decoupled Services and Shared Contracts

## Status
Accepted

## Context
TrustCounsel AI includes an API gateway, background ingestion worker, evaluation engine, and a React web application. Maintaining multiple separate repositories creates synchronization friction for data contracts, OpenAPI schemas, and shared TypeScript/Pydantic types, while hindering end-to-end local testing.

## Decision
We adopt a **modular monorepo** layout:
- `apps/web/`: React 19 + TypeScript + Vite + Tailwind CSS frontend application.
- `services/api/`: FastAPI backend providing REST endpoints, LangGraph agent execution, and database models.
- `workers/ingestion/`: Asynchronous ingestion pipeline workers.
- `packages/shared-contracts/`: OpenAPI specification and generated TypeScript definitions for client-server type safety.
- `tests/`: Unified test harness covering unit, integration, security, e2e, and evaluation benchmarks.
- `docker-compose.yml`: Local multi-service orchestration.

## Consequences
### Positive
- Single git history ensures atomic commits across frontend, backend, specifications, and test fixtures.
- Consistent developer experience: `make dev` or `docker compose up` brings up the entire platform.
- Straightforward CI pipeline validating end-to-end integration.

### Negative / Trade-offs
- Requires clear internal boundary discipline to prevent accidental circular imports across modules.
