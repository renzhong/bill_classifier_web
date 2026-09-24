# Research and decisions

## Upload lifecycle

**Decision**: Add a separate archived flag to bills and parsed/classified/archived upload task statuses. Existing bills migrate as archived. New uploads parse into unarchived rows, then expose explicit classify and archive actions.

**Rationale**: `lifecycle` currently means classification outcome and reports query all bills. Reusing it for staging would corrupt both meanings.

**Alternatives considered**: A separate temporary-bills table duplicates bill schema, tags and update logic. Immediate archive bypasses the requested parsed preview.

## Classification and editing

**Decision**: Manual action runs only `地铁|公交` against bill name and maps to user's `交通` category. A missing category is created for that user. Manually overridden bills are skipped. Category patch validates ownership and accepts explicit null. Source and upload tags are immutable after upload.

**Rationale**: User approved one test rule and postponed rule UI. Existing AI Pipeline is not suitable for this specific test.

**Alternatives considered**: Auto-run existing Pipeline or build rule CRUD now. Both exceed the approved interaction.

## Financial migration and totals

**Decision**: New named asset items and month values supplement legacy `assets`. Backfill creates items from distinct user/type/name and month values, summing old duplicates for the same key. Keep original rows untouched, and use only the new projection for the new page totals. Old income rows remain as month-only records, summed alongside dated entries without inventing dates.

**Rationale**: Old rows have neither stable item IDs nor income dates. Non-destructive migration preserves auditability and avoids duplicate totals.

**Alternatives considered**: Changing old table semantics in place; assigning fake first-of-month dates to legacy income. Both lose meaning.

## Investment valuations

**Decision**: Investment month-end value is a read-only row on the asset page and counted once alongside manual assets, minus liabilities. Missing value is null. Profit is current value minus prior value minus buys plus sells; first month uses initial principal.

**Rationale**: This matches the approved accounting rule and prevents entry in two places.

**Alternatives considered**: Copying valuations into manual asset values would create a second editable source and allow double counting.
