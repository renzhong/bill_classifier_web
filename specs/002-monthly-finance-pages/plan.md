# Implementation Plan: Monthly finance pages

**Branch**: `codex/next-prd` | **Date**: 2026-09-24 | **Spec**: [spec.md](spec.md)

## Summary

Deliver five connected pages: staged bill upload/classify/archive, category spending, monthly named assets and liabilities, investments, and dated income entries. Keep existing API routes where possible, add additive MySQL tables and migrate legacy assets without changing original rows. Bill staging is independent of classification. The requested test regex runs only after a click. Archived bills alone contribute to reports.

## Technical Context

**Language/Version**: Python >=3.11, TypeScript, Vue 3
**Primary Dependencies**: FastAPI, SQLAlchemy async, Alembic, Naive UI, Vue Router
**Storage**: MySQL 8; Decimal/Numeric amounts
**Testing**: pytest, ruff, vue-tsc, Vite build; disposable MySQL test database for integration
**Target Platform**: Browser and existing FastAPI service
**Project Type**: Web application
**Performance Goals**: Paginated bill query; monthly aggregates scoped to user/month
**Constraints**: No real bill fixtures; no external asset price or bank sync; preserve old income dates as unknown
**Scale/Scope**: Five product pages, four additive migrations, existing single-user ownership model

## Constitution Check

| Principle | Decision |
|---|---|
| User-configured classification | Keep existing Pipeline API, but upload does not auto-run it. Implement only the explicitly requested fixed test regex in the manual batch action. |
| Privacy and ownership | Scope every new query/mutation by authenticated user; use synthetic fixtures. |
| Module contracts | Additive routes and models; update changed bill/report docs with implementation. |
| Proportionate validation | Run frontend build/type check, backend tests and isolated MySQL integration where available. |
| Specs describe change | PRD stays planning material; this spec tracks the current feature. |

Post-design gate: all principles satisfied. The fixed regex is an explicit user request for this trial, not a general rules engine.

## Project Structure

```text
backend/
├── migrations/versions/       # additive schema migrations
├── app/models/                # bill and finance entities
├── app/bills/                 # bill staging/classify/archive
├── app/assets/                # monthly assets and liabilities
├── app/investments/           # investment items/months
├── app/incomes/               # dated income entries and legacy totals
├── app/api/v1/                # route aggregation
├── app/reports/               # archived bill/report projections
└── tests/                     # synthetic API/logic coverage
frontend/src/
├── api/                       # typed API requests
├── views/                     # five product pages
├── components/AppLayout.vue   # navigation
├── router/index.ts            # routes and legacy redirects
└── styles/global.css          # Carbon light palette
```

**Structure Decision**: Extend existing FastAPI routers and Vue views. No new project or dependency is required.
