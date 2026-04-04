# Feature Test Checklist

Generated: 2026-03-24

This document lists the main features to test for the project in a systematic, actionable format. For each feature include: test case description, expected result, request/steps, and edge cases.

---

## 1. Authentication
- JWT token issuance: POST `/api/token/` with valid credentials → returns `access`, `refresh` and `user` payload.
- Token refresh: POST `/api/token/refresh/` with valid `refresh` → returns new `access`.
- Token verify: POST `/api/token/verify/` with `access` → 200 for valid token.
- Current user: GET `/api/user/me/` authenticated → returns user details.
- Invalid credentials: token endpoint returns 401 and error message.
- Expired/invalid token: protected endpoints return 401.

## 2. Users & Permissions
- Create user (Admin only): POST `/api/users/` as admin → user created, password hashed.
- Create user as non-admin: POST `/api/users/` as engineer → 403.
- Update/Delete user: ensure only admin can update/delete; list/retrieve allowed for authenticated.
- Email uniqueness: creating user with exi  sting email → validation error.
- Role validation: only `admin` or `engineer` allowed.
- Password handling: password field write-only, not returned in responses.
                                                                            
## 3. Categories
- CRUD operations: list/retrieve/create/update/delete via `/api/categories/`.
- Unique name constraint: creating duplicate category name → validation error.
- `items_count` correctness: category details show accurate count.
- List ordering: categories ordered by `name`.

## 4. Items
- CRUD operations: `/api/items/` create, list, retrieve, update, delete.
- Unique (name, category): creating duplicate item under same category → error.
- Filtering by category: `GET /api/items/?category=<id>` returns only matching items.
- `current_stock` value: matches related `Stock` record or 0 if none.
- Field validations: required fields, max lengths, etc.

## 5. Stock Model & Endpoints
- Stock creation: saving `GoodsReceived` creates/updates `Stock` record.
- Stock prevents negative: `Stock.clean()` validation rejects negative quantities.
- Stock read-only API: `GET /api/stocks/` shows current quantities.
- Filtering: `/api/stocks/?item=<id>` and `/api/stocks/?low_stock=<threshold>` work as expected.
- Last updated timestamps reflect changes.

## 6. Goods Received (Stock IN)
- Create GR: POST `/api/goods-received/` with positive `quantity` → stock increases.
- Serializer sets `received_by` to request user.
- Ledger entry: corresponding `StockLedger` created with `transaction_type=IN`, correct `balance_after`, `reference_type='GoodsReceived'`.
- Quantity validation: `quantity <= 0` → validation error.
- Query filtering: `?item=`, `?user=` filters work.

## 7. Goods Issue (Stock OUT)
- Create GI: POST `/api/goods-issues/` with positive `quantity` and sufficient stock → stock decreases.
- Prevent over-issue: if requested `quantity` > available → validation error and 400.
- Serializer sets `issued_by` to request user.
- Ledger entry: `StockLedger` created with `transaction_type=OUT`, correct `balance_after`, `reference_type='GoodsIssue'`.
- `issued_to` recorded in remarks and response.
- Query filtering: `?item=`, `?user=`, `?issued_to=` works.

## 8. Stock Ledger / History
- Read-only endpoints: `GET /api/ledger/` returns ledger entries.
- Fields: includes `transaction_type`, `quantity`, `balance_after`, `user`, `reference_type`, `reference_id`, `remarks`.
- Filtering: by `item`, `user`, `transaction_type` returns expected entries.
- Ordering: newest entries first.

## 9. Reports
- Stock report: `GET /api/reports/stock/` returns current stock list; supports `category` and `low_stock` filters.
- Issues report: `GET /api/reports/issues/` supports `start_date`, `end_date`, `user`, `item` and returns `count` and `total_quantity_issued`.
- Ledger report: `GET /api/reports/ledger/` supports `start_date`, `end_date`, `user`, `item`, `transaction_type`.
- Date parsing: invalid date formats are handled gracefully (ignored or return 400 depending on implementation).

## 10. Serializers & Validation
- Custom token serializer returns embedded `user` info and custom claims.
- Goods serializers validate positive quantities and stock availability.
- User serializer enforces email uniqueness and role restriction.
- Item/category serializers compute derived fields (`current_stock`, `items_count`).

## 11. Admin Site Behavior
- `User` admin shows `role`, supports adding/editing users.
- `Stock` admin is read-only (no add/delete permitted).
- `StockLedger` admin read-only; no add/delete permitted.
- `GoodsReceived` and `GoodsIssue` admin show readonly timestamps and allow listing.

## 12. Data Integrity & Migrations
- Migrations apply successfully: run `python manage.py migrate` in a test DB.
- Unique constraints and `unique_together` enforced at DB level.
- Rolling back a `GoodsReceived`/`GoodsIssue` should maintain ledger/stock consistency (test manual deletion edge-case behavior).

## 13. Concurrency & Race Conditions (advanced)
- Simulate concurrent `GoodsIssue` requests to ensure no oversell (use transactions or DB-level locks if required).
- Concurrent `GoodsReceived` updates accumulate correctly.

## 14. Edge Cases & Error Handling
- Large quantities near `max_digits` boundary behave correctly.
- Non-existent item IDs in requests return 404.
- Missing required fields return 400 with helpful messages.
- Decimal precision preserved across create/update/save cycles.

## 15. Security & Permissions
- Ensure endpoints require authentication where specified.
- Ensure only admins can perform user management actions.
- Test token payload does not leak sensitive data (passwords).

## 16. Smoke & Integration Tests
- End-to-end flow: create category → create item → receive goods → check stock → issue goods → check ledger and stock.
- API contract tests: verify response schemas match serializers.

---

## How to use
- Create a test plan from this checklist and convert items into unit tests or integration tests under `api/tests.py` or a `tests/` package.
- For each feature, create at least one positive and one negative test case.

---

If you want, I can (1) add this file to the repo (done), (2) convert checklist items into `pytest`/`django` test skeletons in `api/tests.py`, or (3) run the project's test suite. Which next step would you like?