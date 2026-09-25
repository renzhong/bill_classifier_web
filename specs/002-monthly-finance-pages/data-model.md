# Data model

## Bill and upload task

`bills.archived` is non-null Boolean, default false for new rows and true for legacy rows. `lifecycle` remains classification outcome. When order ID is absent, a nullable `dedup_hash` records the exact parsed identity and is unique per user/source; legacy null-order bills are checked by their fields before insertion. `upload_tasks.status` transitions `pending -> parsing -> parsed -> classified -> archived`; `failed` is terminal for parse/storage failures. `upload_tasks.parse_errors` lists failed source rows. A task owns zero or more bills. Source and bill tags are fixed from upload; category is editable by owner. A manually set category, including explicit null, sets `manual_overridden` and blocks later automatic classification.

## AssetItem and AssetMonthValue

`asset_items`: id, user_id, name (1–64 chars), kind (`asset` or `liability`), active, legacy_type nullable. Name uniqueness is per user/kind. `asset_month_values`: id, item_id, month (`YYYY-MM`), amount (non-negative Numeric(14,2)), remark; unique item/month. No row means not filled; zero is explicit. Deactivated items remain visible for months where a value exists.

## InvestmentItem and InvestmentMonth

`investment_items`: id, user_id, name (1–64 chars), initial_principal (non-negative Numeric(14,2)), first_month (`YYYY-MM`), active, optional unique `linked_asset_item_id` owned by same user. A linked manual asset's amounts remain historical but are excluded from totals in months from the investment start while its investment valuation takes their place. `investment_months`: id, item_id, month, buys, sells (non-negative Numeric(14,2), default zero), closing_value (nullable non-negative Numeric(14,2)); unique item/month. A missing month or null closing value is incomplete. Profit is null when prior value is missing except in first month, which uses initial principal.

## IncomeEntry

`income_entries`: id, user_id, occurred_at (date/time), amount (positive Numeric(14,2)), source (nullable 64 chars), remark (nullable 255 chars). Multiple rows per same date/source are allowed. Legacy `monthly_incomes` remain distinct month-only rows; monthly and yearly totals add both sources once.

## Ownership and reports

Every mutation joins or checks authenticated user, including child rows. Category spending counts only archived, non-skipped expense bills. Monthly assets sum manual asset values plus investment closing values minus liability values; missing required values set `complete=false` and are excluded from arithmetic.
