# Tasks: Monthly finance pages

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, `contracts/api.md`

## Phase 1: Setup

- [X] T001 Confirm isolated project dependencies and available validation commands in `backend/pyproject.toml` and `frontend/package.json`

## Phase 2: Foundation

- [X] T002 Add additive bill and finance schema migrations in `backend/migrations/versions/0005_monthly_finance.py` through `0008_null_order_dedup.py`, backfilling archived bills and legacy asset projections without deleting old rows
- [X] T003 Register new finance models and routes in `backend/app/models/__init__.py` and `backend/app/api/v1/__init__.py`

## Phase 3: User Story 1 - Bill workspace

**Goal**: Upload modal, staged parsed bills, explicit test classification, manual edit and archive.

**Independent test**: Synthetic cross-month upload stays out of reports until archive; explicit classify and edits behave as specified.

- [X] T004 [US1] Add independent archive state to `backend/app/models/bill.py` and output in `backend/app/schemas/bill.py`
- [X] T005 [US1] Change upload to parse-only and implement test regex classify in `backend/app/tasks/upload_runner.py`
- [X] T006 [US1] Add batch list/classify/archive endpoints with ownership and status checks in `backend/app/bills/router.py` and `backend/app/bills/service.py`
- [X] T007 [US1] Reject post-upload tag edits, validate category ownership and allow explicit null in `backend/app/bills/service.py`
- [X] T008 [US1] Build upload modal, staged and archived tables and category management in `frontend/src/views/BillsDetail.vue` and `frontend/src/api/bills.ts`

## Phase 4: User Story 2 - Monthly category spending

**Goal**: Monthly category totals and direct drilldown to matching bills.

**Independent test**: Category totals agree with archived expense bill rows for selected month.

- [X] T009 [US2] Exclude unarchived bills in all bill aggregates in `backend/app/reports/router.py`
- [X] T010 [US2] Connect category spending to filtered bill view in `frontend/src/views/ReportsCategory.vue` and `frontend/src/router/index.ts`

## Phase 5: User Story 3 - Reusable monthly assets

**Goal**: Named asset/liability items persist across months while values start empty.

**Independent test**: New month shows same items with null values; investment values enter total once.

- [X] T011 [US3] Add asset item and month value models in `backend/app/models/asset.py` with kind `asset|liability`, non-negative Numeric(14,2) values and unique item/month
- [X] T012 [US3] Add user-scoped item CRUD, month value upsert and month summary in `backend/app/assets/router.py`
- [X] T013 [US3] Build monthly asset item/value page in `frontend/src/views/SettingsAssets.vue` and typed requests in `frontend/src/api/finance.ts`

## Phase 6: User Story 4 - Investments

**Goal**: Item principal, monthly buys/sells/value and computed profit.

**Independent test**: Two-month sample gives formula result; missing prior valuation returns null profit.

- [X] T014 [US4] Add investment item/month models in `backend/app/models/investment.py` with non-negative Numeric(14,2) and unique item/month
- [X] T015 [US4] Add user-scoped investment APIs and profit calculation in `backend/app/investments/router.py`
- [X] T016 [US4] Build investment page in `frontend/src/views/Investments.vue` and API bindings in `frontend/src/api/finance.ts`

## Phase 7: User Story 5 - Dated income

**Goal**: Multiple dated entries per month/source and month/year totals with legacy records.

**Independent test**: Two same-source entries remain separate, sums include legacy month-only rows once.

- [X] T017 [US5] Add dated income model in `backend/app/models/income.py` with positive Numeric(14,2) amount
- [X] T018 [US5] Add user-scoped entry CRUD and month/year summary in `backend/app/incomes/router.py`
- [X] T019 [US5] Build income page in `frontend/src/views/SettingsIncomes.vue` and API bindings in `frontend/src/api/finance.ts`

## Phase 8: Polish and validation

- [X] T020 Update navigation and Carbon light palette in `frontend/src/components/AppLayout.vue`, `frontend/src/router/index.ts`, and `frontend/src/styles/global.css`
- [X] T021 Update current behavior docs in `arch.md` and relevant `docs/` files without presenting PRD as implemented
- [X] T022 Validate `specs/002-monthly-finance-pages/quickstart.md` with type check, build, lint and available backend tests

## Dependencies and execution order

T001 → T002/T003 → US1 → US2. US3 and US4 share the asset total contract; complete US4 backend before finalizing T012. US5 is independent after foundation. T020-T022 follow all stories. Each story's independent test is stated above.

## Parallel opportunities

After T002/T003, investment and income backend models may be built separately from bills. Different frontend views may likewise be developed independently. Database migration and model contracts must land first.

## Implementation strategy

Deliver the bill workspace first, then monthly spending, asset/investment projections, and dated income. Verify each user story against synthetic data before final build and docs sync.
