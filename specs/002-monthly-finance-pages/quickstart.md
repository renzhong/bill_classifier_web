# Validation quickstart

Use synthetic data and a disposable MySQL database named with `_test`; follow `docs/test-data.md`. Do not restore personal SQL snapshots for these checks.

1. In `backend/`, run `uv sync --group dev`, then `uv run ruff check app tests` and `uv run pytest` (set `BCW_TEST_MYSQL=1` only with disposable DB).
2. In `frontend/`, run `npm ci`, `npm run type-check`, and `npm run build`.
3. Apply migrations to disposable DB, start API/UI, upload a synthetic Alipay/WeChat bill spanning two months. Verify parse preview has no checkboxes, category is a dropdown and source/tags cannot change. Run default rule, manually correct one category, archive and check monthly queries.
4. Create reusable asset/liability items, fill one month, move to next month and verify empty amounts. Add investment valuations; confirm they appear once in asset totals. Leave a value missing to verify incomplete status.
5. Add two dated incomes with same source/month. Confirm both rows remain and monthly/yearly totals include them alongside any existing month-only records.

Endpoint shapes and status codes are in `contracts/api.md`.
