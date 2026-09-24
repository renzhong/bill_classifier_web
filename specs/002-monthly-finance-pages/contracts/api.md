# API contract additions

Existing endpoints return the project's `{data, ...}` envelope. All endpoints require current authenticated user. Money serializes as decimal strings.

## Bills

- `POST /bills/upload` multipart: `file`, `source=alipay|wechat`, optional JSON `tag_ids`. Returns upload task. Parsing continues in background.
- `GET /upload-tasks/{id}` returns status, counts and parse warnings.
- `GET /upload-tasks/{id}/bills?page=&page_size=` returns that user's batch rows, same bill shape as `GET /bills`.
- `POST /upload-tasks/{id}/classify` applies requested test regex only; idempotent and preserves manual overrides. `409` if not parsed/ready.
- `POST /upload-tasks/{id}/archive` archives batch atomically; idempotent.
- `GET /bills` defaults to archived rows; existing month/source/category/tag/keyword/page filters remain. `PATCH /bills/{id}` accepts `category_id` only, including explicit null; tag edits return `400`.

## Assets and investments

- `GET,POST /asset-items`; `PATCH /asset-items/{id}` for name/active.
- `GET /asset-months/{month}` returns item rows (`amount: null` if missing), investment valuation rows (read-only), `asset_total`, `liability_total`, `net_assets`, `complete`.
- `PUT /asset-items/{id}/months/{month}` upserts non-negative amount/remark.
- `GET,POST /investments`; `PATCH /investments/{id}` updates item metadata. Optional `linked_asset_item_id` replaces an owned manual asset item from the investment start month to avoid duplicate totals.
- `GET /investments/months/{month}` returns items, month cash flows/value, `profit: null` when inputs incomplete.
- `PUT /investments/{id}/months/{month}` upserts buys/sells/closing value.

## Income and reports

- `GET,POST /income-entries`; `PATCH,DELETE /income-entries/{id}`. List may filter by `month` and returns true occurred dates only.
- `GET /income-summary?year=YYYY&month=YYYY-MM` returns current month and year totals, dated entries, and separate legacy month-only rows.
- `GET /reports/category-summary?month=YYYY-MM` and existing report routes exclude staged bills. Clicking category links to `/bills?month=&category_id=`.
