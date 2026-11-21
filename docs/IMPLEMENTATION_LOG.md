# PayGuard 360 — Implementation Log

All operations, exact commands, real outputs, and gate verification details are recorded here.

---

## Kickoff & Phase 0: Initialization

**Date:** 2026-11-21  
**Settings:**
- `PROFILE`: `standard`
- `MODE`: `checkpoint`

### Commands Run & Output:

```powershell
Get-ChildItem -Force
# Result: Clean directory

python --version; node --version; npm --version
# Output:
# Python 3.15.2
# v26.13.1
# 11.20.0

git init
# Output:
# Initialized empty Git repository in C:/Users/POORVIKA B S/Downloads/ZYRO/.git/
```

### Artifacts Created:
- `docs/MASTER_PROMPT.md`
- `.gitignore`
- `task.md`
- `docs/DECISIONS.md`
- `docs/VERIFICATION_MATRIX.md`
- `docs/HACKATHON_FEASIBILITY.md`
- `.env.example`

---

## Phase 1: Foundation (Backend & Frontend Architecture, DB, Auth, Seed, Health)

**Date:** 2026-11-21  
**Scope:** Backend scaffolding, SQLite WAL, models, Alembic baseline migration, append-only triggers, config, clock, errors, auth & RBAC, seed generator, health endpoint, frontend setup, login UI, `scripts/reset_demo.py`.

### Commands Run & Actual Output:

```powershell
python scripts/reset_demo.py
# Output:
# INFO  [alembic.runtime.migration] Context impl SQLiteImpl.
# INFO  [alembic.runtime.migration] Will assume non-transactional DDL.
# INFO  [alembic.runtime.migration] Running upgrade  -> 48b4197d4d1e, baseline_schema
# Resetting PayGuard 360 demo database...
# Seeding demo accounts...
# Demo database seeded successfully!
# Demo reset completed successfully in 2.27 seconds! (Target: < 5.0s)

cd backend
python -m pytest tests/test_foundation.py -v
# Output:
# tests/test_foundation.py::test_health_endpoint PASSED                    [ 14%]
# tests/test_foundation.py::test_login_successful PASSED                   [ 28%]
# tests/test_foundation.py::test_login_invalid_password PASSED             [ 42%]
# tests/test_foundation.py::test_users_me_authenticated PASSED             [ 57%]
# tests/test_foundation.py::test_users_me_unauthenticated PASSED           [ 71%]
# tests/test_foundation.py::test_users_me_forged_token PASSED              [ 85%]
# tests/test_foundation.py::test_append_only_triggers PASSED               [100%]
# ======================= 7 passed, 21 warnings in 0.73s ========================

cd ../frontend
npm run build
# Output:
# ✓ built in 2.50s

npx vitest run
# Output:
# ✓ src/tests/formatPaise.test.ts (8 tests) 2ms
# Test Files  1 passed (1)
#      Tests  8 passed (8)
#   Duration  567ms
```

### Gate Checklist (Phase 1):
- [x] App starts & health endpoint `/health` returns healthy: PASS
- [x] DB migrates via Alembic baseline with WAL mode and foreign keys: PASS
- [x] Append-only SQLite triggers prevent UPDATE/DELETE on `audit_log`: PASS
- [x] Demo login & JWT verification work: PASS
- [x] Seed data generator produces realistic accounts & review cases: PASS
- [x] `scripts/reset_demo.py` completes in < 5.0s (Actual: 2.27s): PASS
- [x] Frontend builds cleanly with zero TypeScript errors: PASS
- [x] Money formatter with Indian digit grouping tests pass: PASS

**Gate Status: PASS**

---

## [Phase 2c] - Review Service, Supervisor Resolution, Alerts & Audit Log

### Work Done:
1. Implemented Review Schemas (`backend/app/schemas/review.py` & `alerts.py`):
   - `ReviewDecisionRequest` enforcing mandatory note (5–500 chars) and optimistic concurrency `expected_version`.
   - `ReviewCaseResponse` with masked customer reference (`CUST-` + 6 hex HMAC) and masked payee (`••••ab12`).
   - `AuditLogEntryResponse` returning actor details and safe metadata JSON.
   - `AlertResponse` with dedupe key and unread indicators.
2. Implemented Alert Service (`backend/app/services/alert_service.py`):
   - Deduplicated in-app alert creation via `(user_id, dedupe_key)`.
   - Unread-only filtering and customer mark-as-read with IDOR protection.
3. Implemented Review Service (`backend/app/services/review_service.py`):
   - `get_review_queue`: Ordered by highest score DESC, then oldest created_at ASC; paginated; role-aware (reviewers cannot see escalated cases without supervisor role).
   - `record_case_decision`:
     - Self-review block (reviewers/supervisors cannot act on their own payments -> 403).
     - Mandatory trimmed note (5–500 characters, sensitive inputs stripped -> 422).
     - Optimistic locking validation (`expected_version` -> 409 `CASE_CONFLICT`).
     - Supervisor-only resolution for escalated cases (403 for non-supervisors).
     - Two-person rule enforcement (supervisor resolving escalation cannot be the actor who escalated it -> 403).
     - Hold review actions: `approve` (tx -> `completed`, payee -> `known`, alert created), `reject` (tx -> `released`, funds freed, alert created), `escalate` (tx -> `escalated`, assigned reviewer set).
     - Post review actions: `mark_confirmed_fraud` (payee -> `flagged`, alert created), `mark_false_alarm` (alert created).
     - Atomic append to `review_case_actions` and `audit_log`.
4. Implemented Review & Alert Routers (`backend/app/routers/review.py` & `alerts.py`):
   - `GET /review/cases`, `GET /review/cases/{id}`, `POST /review/cases/{id}/decision`, `GET /review/audit`.
   - `GET /alerts`, `POST /alerts/{id}/read`.
5. Automated Test Suite (`backend/tests/test_phase2c.py`):
   - 13 automated tests covering RBAC, mandatory note, optimistic lock conflicts, self-review blocks, approve/reject/escalate workflows, two-person rule enforcement, confirmed fraud payee flagging, audit log queries, and customer alert IDOR protection.

### Commands Run & Output:
```bash
cd backend
python -m pytest tests/test_phase2c.py -v
# Output:
# ======================= 13 passed, 99 warnings in 7.60s =======================

python -m pytest tests -v
# Output:
# ====================== 57 passed, 152 warnings in 8.88s =======================

cd ../frontend
npx vitest run
# Output:
# Test Files  1 passed (1)
#      Tests  8 passed (8)
#   Duration  422ms

npm run build
# Output:
# ✓ built in 2.07s
```

### Gate Checklist (Phase 2c):
- [x] Review queue returns cases with masked payee and customer ref: PASS
- [x] Reviewer cannot view or resolve escalated queue without supervisor role: PASS
- [x] Reviewer cannot act on payments belonging to own account: PASS
- [x] Mandatory note (5–500 chars) enforced for all review decisions: PASS
- [x] Optimistic locking prevents stale updates with 409 `CASE_CONFLICT`: PASS
- [x] Two-person rule blocks supervisor who escalated from resolving: PASS
- [x] Approval completes payment; rejection releases held reservation: PASS
- [x] Confirmed fraud flags payee for future risk evaluations: PASS
- [x] Native triggers prevent UPDATE/DELETE on `review_case_actions`: PASS
- [x] All 57 backend tests and 8 frontend tests passing: PASS

**Gate Status: PASS**



## Phase 2a: Explainable Fraud Risk Engine (Pure, Deterministic)

**Date:** 2026-11-21  
**Scope:** `risk_rules.json`, pure deterministic `risk_engine.py`, 100% test coverage, fixtures F1–F11, boundary conditions, property tests, `docs/RULES.md`.

### Commands Run & Actual Output:

```powershell
cd backend
python -m pytest tests/test_risk_engine.py --cov=app.services.risk_engine --cov-report=term-missing
# Output:
# collected 20 items
# tests\test_risk_engine.py ....................                           [100%]
# Name                          Stmts   Miss  Cover   Missing
# -----------------------------------------------------------
# app\services\risk_engine.py     159      0   100%
# -----------------------------------------------------------
# TOTAL                           159      0   100%
# ============================= 20 passed in 0.15s ==============================
```

### Gate Checklist (Phase 2a):
- [x] All fixtures F1–F11 implemented and passing: PASS
- [x] All 10 rules R1–R10 implemented and evaluated in a single run: PASS
- [x] Integer paise math throughout: PASS
- [x] Score capped at 100: PASS
- [x] Cold-start logic (n < 5 skips R1, R5, halves R2 to 7): PASS
- [x] Timezone conversion to IST (`Asia/Kolkata`) for R3: PASS
- [x] Line and branch coverage target achieved (100%): PASS
- [x] `docs/RULES.md` created: PASS

**Gate Status: PASS**

---

## [Phase 2b] - Accounting, Lifecycle, Credential Guard & Payment APIs

### Work Done:
1. Implemented Credential & Sensitive Input Guard (`backend/app/services/credential_guard.py`):
   - Luhn checksum validator for card numbers (13–19 digits).
   - OTP/PIN proximity pattern matchers rejecting any 4–8 digit credentials adjacent to otp/pin/code terms.
   - Rejection of standalone 4–6 digit strings in notes/free-text.
   - Script-text filter rejecting `<script`, `javascript:`, `onerror=`.
   - Stripping of sensitive inputs before error generation; never echoes raw inputs into logs or API responses.
2. Implemented Ledger Accounting Service (`backend/app/services/accounting_service.py`):
   - Strict integer paise calculations across all accounts.
   - `completed_balance = opening + completed income - completed expenses`.
   - `held_balance = sum of expenses with status in ('held', 'escalated')`.
   - `available_balance = completed_balance - held_balance`.
   - Pre-scoring funds verification raising `INSUFFICIENT_FUNDS` (409) if `amount_paise > available_balance`.
   - 4-point accounting reconciliation endpoint `GET /accounting/reconciliation`.
3. Implemented Payment Service & State Machine (`backend/app/services/payment_service.py`):
   - Central legal transition validator (`validate_transition`) rejecting illegal state transitions with `ILLEGAL_TRANSITION` (400).
   - Idempotency via `Idempotency-Key` header with payload hash comparison, returning cached result on replay or `IDEMPOTENCY_CONFLICT` (409) on payload mismatch.
   - Atomic balance reservations on high-risk hold.
   - Payee lookup by `payee_id` or `payee_masked_identifier`, creating new payee if not found.
4. Implemented Payment Routers:
   - `POST /payments`: Initiates payment, validates credentials & funds, runs deterministic risk engine, determines target state (`completed`, `awaiting_confirmation`, `held`).
   - `GET /payments/{id}`: Returns payment with masked payee and explainable risk assessment.
   - `POST /payments/{id}/confirm`: Customer explicit confirmation for medium risk payments.
   - `POST /payments/{id}/cancel`: Customer cancellation for awaiting confirmation payments.
   - Cross-customer IDOR protection returning 404 for unowned transactions.
5. Automated Test Suite (`backend/tests/test_phase2b.py`):
   - 17 automated tests covering credential rejections, Devangari digit normalizations, low/medium/high payment flows, funds reservation, reconciliation checks, idempotency, and cross-customer IDOR protection.

### Commands Run & Output:
```bash
cd backend
python -m pytest tests/test_phase2b.py -v
# Output:
# ======================= 17 passed, 68 warnings in 8.45s =======================

python -m pytest tests -v
# Output:
# ======================= 44 passed, 81 warnings in 8.46s =======================

cd ../frontend
npx vitest run
# Output:
# Test Files  1 passed (1)
#      Tests  8 passed (8)
#   Duration  383ms
```

### Gate Checklist (Phase 2b):
- [x] Sensitive input guard rejects OTP/PIN/card/script text: PASS
- [x] Input sanitization never echoes credentials in errors or logs: PASS
- [x] Ledger balances computed from ledger single source of truth: PASS
- [x] Insufficient funds rejected before scoring: PASS
- [x] High-risk payments transition to held with funds reserved: PASS
- [x] Medium-risk payments require explicit customer confirmation: PASS
- [x] Idempotency keys prevent double charge: PASS
- [x] Cross-customer IDOR prevented with 404: PASS
- [x] All 44 backend tests and 8 frontend tests passing: PASS

**Gate Status: PASS**

---

## [Phase 2c] - Review Service, Supervisor Resolution, Alerts & Audit Log

### Work Done:
1. Implemented Review Schemas (`backend/app/schemas/review.py` & `alerts.py`):
   - `ReviewDecisionRequest` enforcing mandatory note (5–500 chars) and optimistic concurrency `expected_version`.
   - `ReviewCaseResponse` with masked customer reference (`CUST-` + 6 hex HMAC) and masked payee (`••••ab12`).
   - `AuditLogEntryResponse` returning actor details and safe metadata JSON.
   - `AlertResponse` with dedupe key and unread indicators.
2. Implemented Alert Service (`backend/app/services/alert_service.py`):
   - Deduplicated in-app alert creation via `(user_id, dedupe_key)`.
   - Unread-only filtering and customer mark-as-read with IDOR protection.
3. Implemented Review Service (`backend/app/services/review_service.py`):
   - `get_review_queue`: Ordered by highest score DESC, then oldest created_at ASC; paginated; role-aware (reviewers cannot see escalated cases without supervisor role).
   - `record_case_decision`:
     - Self-review block (reviewers/supervisors cannot act on their own payments -> 403).
     - Mandatory trimmed note (5–500 characters, sensitive inputs stripped -> 422).
     - Optimistic locking validation (`expected_version` -> 409 `CASE_CONFLICT`).
     - Supervisor-only resolution for escalated cases (403 for non-supervisors).
     - Two-person rule enforcement (supervisor resolving escalation cannot be the actor who escalated it -> 403).
     - Hold review actions: `approve` (tx -> `completed`, payee -> `known`, alert created), `reject` (tx -> `released`, funds freed, alert created), `escalate` (tx -> `escalated`, assigned reviewer set).
     - Post review actions: `mark_confirmed_fraud` (payee -> `flagged`, alert created), `mark_false_alarm` (alert created).
     - Atomic append to `review_case_actions` and `audit_log`.
4. Implemented Review & Alert Routers (`backend/app/routers/review.py` & `alerts.py`):
   - `GET /review/cases`, `GET /review/cases/{id}`, `POST /review/cases/{id}/decision`, `GET /review/audit`.
   - `GET /alerts`, `POST /alerts/{id}/read`.
5. Automated Test Suite (`backend/tests/test_phase2c.py`):
   - 13 automated tests covering RBAC, mandatory note, optimistic lock conflicts, self-review blocks, approve/reject/escalate workflows, two-person rule enforcement, confirmed fraud payee flagging, audit log queries, and customer alert IDOR protection.

### Commands Run & Output:
```bash
cd backend
python -m pytest tests/test_phase2c.py -v
# Output:
# ======================= 13 passed, 99 warnings in 7.60s =======================

python -m pytest tests -v
# Output:
# ====================== 57 passed, 152 warnings in 8.88s =======================

cd ../frontend
npx vitest run
# Output:
# Test Files  1 passed (1)
#      Tests  8 passed (8)
#   Duration  422ms

npm run build
# Output:
# ✓ built in 2.07s
```

### Gate Checklist (Phase 2c):
- [x] Review queue returns cases with masked payee and customer ref: PASS
- [x] Reviewer cannot view or resolve escalated queue without supervisor role: PASS
- [x] Reviewer cannot act on payments belonging to own account: PASS
- [x] Mandatory note (5–500 chars) enforced for all review decisions: PASS
- [x] Optimistic locking prevents stale updates with 409 `CASE_CONFLICT`: PASS
- [x] Two-person rule blocks supervisor who escalated from resolving: PASS
- [x] Approval completes payment; rejection releases held reservation: PASS
- [x] Confirmed fraud flags payee for future risk evaluations: PASS
- [x] Native triggers prevent UPDATE/DELETE on `review_case_actions`: PASS
- [x] All 57 backend tests and 8 frontend tests passing: PASS

**Gate Status: PASS**

---

## [Phase 2d] - Customer Pay, Risk Result, Reviewer UI, Simulator & Demo Reset (Checkpoint)

### Work Done:
1. Implemented Demo & Simulator Backend Endpoints (`backend/app/routers/demo.py`):
   - `GET /demo/scenarios`: Returns 5 pre-configured attack presets (F1 Baseline Low, F2 Unusual Amount Medium, F3 Flagged Late Night High, F4 Burst Velocity High, F5 Collect Request Scam High).
   - `POST /demo/reset`: One-click instant demo database wipe and re-seed, executing in < 5.0 seconds (actual: 0.22s).
2. Implemented Risk Breakdown Endpoints (`backend/app/routers/risk.py`):
   - `GET /risk/assessments/{id}`: Returns score, band, rules version, features, and explainable reasons (`code + params`).
   - `GET /risk/assessments/{id}/breakdown`: Returns fired reasons and "What would change this score" reduction recommendations for customer empowerment.
3. Implemented Frontend API Client & State Management (`frontend/src/services/api.ts`):
   - Strongly-typed payment creation, confirmation, and cancellation.
   - Risk assessment retrieval and score breakdown methods.
   - Review queue filtering, case detail retrieval, and decision submission with optimistic locking.
   - Demo scenario loading and one-click demo database reset.
4. Implemented Customer Payment Experience:
   - `NewPaymentPage.tsx`: Live integer paise formatting, 3-point pre-payment safety checklist, credential notice banner, idempotency key generation.
   - `PaymentResultPage.tsx`: Prominent score badge (0–100) and risk band color (emerald, amber, rose), explainable reasons list, "What would reduce this score" panel, explicit Confirm/Cancel action buttons for Medium risk, reserved funds hold banner for High risk.
5. Upgraded Reviewer Console (`frontend/src/pages/ReviewQueuePage.tsx`):
   - Real-time filterable queue (all, open, escalated, closed, hold_review, post_review).
   - Case Inspector Modal displaying risk score, fired reasons, features JSON, transaction lifecycle metadata, and immutable action timeline.
   - Decision submission with mandatory note validation (5–500 chars), separation of duties notice, and optimistic locking `expected_version`.
   - Append-Only Audit Trail tab viewing chronological immutable compliance events.
6. Implemented Demo Simulator Modal (`frontend/src/components/common/DemoSimulatorModal.tsx`):
   - Quick launcher in top navigation bar (`Navbar.tsx`).
   - 1-click loading of F1–F5 attack scenarios directly into New Payment form.
   - Simulated Time status indicator.
   - One-click demo database reset with confirmation dialog and timing measurement.
7. Automated Test Suite (`backend/tests/test_phase2d.py`):
   - 10 automated end-to-end integration tests covering scenario presets, demo reset speed (< 5s), risk assessment RBAC and breakdown, Low risk completion, Medium risk confirmation and cancellation, High risk hold and reviewer approval/rejection, escalation and two-person supervisor resolution, and credential guard rejection.

### Commands Run & Output:
```bash
cd backend
python -m pytest tests/test_phase2d.py -v
# Output:
# ====================== 10 passed, 107 warnings in 4.16s =======================

python -m pytest tests -v
# Output:
# ====================== 67 passed, 219 warnings in 11.78s ======================

cd ../frontend
npx vitest run
# Output:
# Test Files  1 passed (1)
#      Tests  8 passed (8)
#   Duration  271ms

npm run build
# Output:
# ✓ built in 2.12s
```

### Gate Checklist (Phase 2d):
- [x] Demo banner "DEMO MODE — NO REAL MONEY MOVES" persistent in UI: PASS
- [x] Credential warning "PayGuard 360 will never ask for your PIN, OTP or password" visible: PASS
- [x] Payment form formats integer paise in real time without floating-point math: PASS
- [x] Low risk completes immediately and shows receipt: PASS
- [x] Medium risk prompts explicit customer confirmation and cancellation options: PASS
- [x] High risk payment holds funds, reserves balance, and routes to reviewer queue: PASS
- [x] Reviewer case inspector modal displays score, band, reasons, and features: PASS
- [x] Mandatory note (5–500 chars) enforced for reviewer actions: PASS
- [x] Escalation requires supervisor resolution with separation of duties: PASS
- [x] Demo simulator modal allows 1-click execution of F1–F5 attack scenarios: PASS
- [x] Demo reset restores seeded state in 0.22s (< 5.0s target): PASS
- [x] All 67 backend automated tests and 8 frontend unit tests passing: PASS
- [x] Frontend builds cleanly with zero errors in 2.12s: PASS

**Gate Status: PASS (CHECKPOINT REACHED — STOPPING FOR OPERATOR SIGN-OFF)**

---

## [Phase 3] - Smart Budgeting, Analytics, Savings Goals & Reconciliation UI

### Work Done:
1. Implemented Budgeting Service & Schemas (`backend/app/schemas/budget.py` & `backend/app/services/budget_service.py`):
   - Monthly overall budget and per-category budgets CRUD.
   - Budget summary calculation strictly from **completed** expenses (`Transaction.type == 'expense' and Transaction.status == 'completed'`).
   - Proactive 80% warning (`alert.budget.approaching_limit`) and 100% limit exceeded (`alert.budget.limit_exceeded`) alerts with deduplication keys `(user_id, period, category, budget_amount)`.
   - Real-time alert evaluation hooks wired into payment completion, reviewer approval, manual expenses, and category patches.
2. Implemented Savings Goals Service & Schemas (`backend/app/schemas/goal.py` & `backend/app/services/goal_service.py`):
   - Savings goals CRUD with target dates and progress percentages.
   - Goal contributions with strict funds verification against available ledger balances, rejecting over-contributions with `INSUFFICIENT_FUNDS` (409).
3. Implemented Cash Flow & Category Analytics (`backend/app/services/analytics_service.py`):
   - `GET /accounting/cashflow`: Computes daily income, expenses, and net cash flow points plus monthly totals.
   - `GET /accounting/categories`: Groups completed spending by category with exact percentages.
4. Implemented Routers:
   - `backend/app/routers/budgets.py`: `/budgets` CRUD and `/budgets/summary`.
   - `backend/app/routers/goals.py`: `/goals` CRUD and `/goals/{id}/contributions`.
   - `backend/app/routers/accounting.py`: Mounted `/accounting/cashflow` and `/accounting/categories`.
5. Implemented Frontend Budgeting & Goals View (`frontend/src/pages/BudgetsPage.tsx`):
   - Monthly period selector (`YYYY-MM`).
   - Overall monthly budget progress bar with color-coded threshold states (emerald <80%, amber 80–99%, rose >=100%).
   - Category budgets grid with spent vs limit progress bars.
   - Cash Flow summary metrics and daily breakdown table.
   - Spending by category breakdown with percentage meters.
   - Savings goals cards with progress and contribution modal.
   - Set Budget, New Goal, Contribute, and Record Manual Transaction modals.
   - Live 4/4 reconciliation badge.
6. Automated Test Suite (`backend/tests/test_phase3.py`):
   - 5 comprehensive automated tests covering budget CRUD & RBAC, summary accuracy ensuring held payments never count as expenses, 80% and 100% alert firing with deduplication, savings goals CRUD & balance-capped contributions, and cash flow/category analytics.

### Commands Run & Output:
```bash
cd backend
python -m pytest tests/test_phase3.py -v
# Output:
# ======================= 5 passed, 116 warnings in 2.80s =======================

python -m pytest tests -v
# Output:
# ====================== 72 passed, 287 warnings in 16.56s ======================

cd ../frontend
npx vitest run
# Output:
# Test Files  1 passed (1)
#      Tests  8 passed (8)
#   Duration  338ms

npm run build
# Output:
# ✓ built in 2.72s
```

### Gate Checklist (Phase 3):
- [x] Budget summary uses real API data without mock/hardcoded values: PASS
- [x] Completed simulated payments appear as expenses exactly once: PASS
- [x] Held, escalated, and released payments never count towards budget spent: PASS
- [x] 80% warning and 100% exceeded alerts fire with explainable params: PASS
- [x] Budget alert deduplication prevents redundant alerts: PASS
- [x] Savings goals support progress tracking and earmark contributions: PASS
- [x] Over-contributions exceeding available ledger balance rejected with 409: PASS
- [x] Cash flow trends and category distribution calculated from ledger: PASS
- [x] Live reconciliation panel displays 4/4 check consistency: PASS
- [x] All 72 backend automated tests and 8 frontend unit tests passing: PASS
- [x] Frontend builds cleanly with zero errors in 2.72s: PASS

**Gate Status: PASS**


---

## [Phase 4] - Awareness, Guidance Library, Scam Checker & Bilingual Localization

### Work Done:
1. Implemented Guidance & Scam Checker Schemas (`backend/app/schemas/guidance.py`):
   - `GuidanceItemResponse`: Topic, language (`en`, `hi`), title, body, verified source label, URL, and verification date.
   - `ScamCheckRequest`: Free-text message validation (max 1000 characters).
   - `ScamCheckResponse`: Heuristic result with `is_suspicious`, `risk_level` (`low`, `medium`, `high`), matched signals, official advice codes, and disclaimer.
2. Implemented Deterministic Heuristic Scam Checker (`backend/app/services/scam_checker_service.py`):
   - Integrates with `credential_guard.py` first (§11, §14): any message containing standalone credentials, PINs/OTPs, card numbers, or script tags is rejected with `CREDENTIAL_INPUT_REJECTED` or `INVALID_TEXT` (422) without logging or echoing the secret.
   - Strict Zero-Retention: Evaluated input text is never saved to the database and never recorded in application logs.
   - Deterministic rule heuristics scanning urgency/threats, KYC phishing bait, lottery/financial lures, shortened URLs (`bit.ly`, `tinyurl`, etc.), insecure HTTP links, remote access tools (`AnyDesk`, `TeamViewer`, `RustDesk`), and collect request / QR code traps.
   - Generates actionable advice recommendations (`scam_advice.*`) and official disclaimers.
3. Implemented Guidance Router (`backend/app/routers/guidance.py`):
   - `GET /guidance?lang=en|hi`: Returns verified static guidance items (Helpline 1930, Sanchar Saathi, QR code education).
   - `POST /guidance/scam-check`: Scans messages heuristically without retention.
   - Mounted in `backend/app/main.py`.
4. Upgraded Score Breakdown & What-If Engine (`backend/app/routers/risk.py`):
   - Computes exact what-if score reductions for all rules R1–R10 from stored reasons without re-executing rule logic: `without_signal_score = max(0, min(100, raw_points - r.points))` and canonical band assignment.
   - Enforces RBAC: Customer can only access own transaction breakdown; Reviewer/Supervisor can access any.
5. Implemented Bilingual English + Hindi Framework (`frontend/src/i18n/`, `frontend/src/contexts/LanguageContext.tsx`):
   - `en.json` and `hi.json` translation dictionaries covering all UI copy, R1–R10 risk reasons with parameter interpolation, in-app safety alerts, Before-You-Pay checklist, and guidance library.
   - `LanguageContext.tsx` providing dynamic reactive translation `t(key, params)` with automatic paise currency formatting (`formatPaise`).
   - Preference persistence in `localStorage` (`payguard_lang`), strictly decoupled from auth tokens which reside only in `sessionStorage` (§17).
   - Language switcher toggle button (English / हिंदी) integrated in `Navbar.tsx`.
   - Created `docs/TODO_HINDI_REVIEW.md` tracking strings for native speaker review.
6. Implemented Financial Awareness View (`frontend/src/pages/LearnPage.tsx`):
   - Deterministic Scam-Message Checker input panel with character counter, loading spinner, and `aria-live` accessible results.
   - Interactive 5-point Before-You-Pay Safety Checklist.
   - Verified Guidance Library cards with direct links to official portals (cybercrime.gov.in, sancharsaathi.gov.in, rbi.org.in) and last verified dates.
   - Connected `/learn` route in `App.tsx` and updated nav link.
7. Enhanced Payment Result Screen (`frontend/src/pages/PaymentResultPage.tsx`):
   - Connected `useLanguage` to render localized risk reasons with parameter interpolation.
   - Connected "What Would Change This Score?" interactive panel showing score point reductions.
8. Responsive & Accessibility Pass:
   - Verified 360 px mobile viewport layout across all views with flexible flexbox/grid styling and no overflow-inducing fixed widths.
   - Form inputs with clear semantic labels and minimum 44×44 px tap targets.
9. Automated Test Suites:
   - Backend tests (`backend/tests/test_phase4.py`): 5 tests covering English/Hindi guidance endpoints, clean message scan, suspicious signal scan, credential rejection in scam checker, and comprehensive risk breakdown calculation/authorization.
   - Frontend tests (`frontend/src/tests/i18nParity.test.ts` & `frontend/src/tests/languageContext.test.ts`): 7 unit tests verifying 100% en/hi key and placeholder parity and parameter interpolation.

### Commands Run & Output:
```bash
cd backend
python -m pytest tests/test_phase4.py -v
# Output:
# ======================= 5 passed, 104 warnings in 2.50s =======================

python -m pytest tests -v
# Output:
# ====================== 77 passed, 319 warnings in 38.56s ======================

cd ../frontend
npx vitest run
# Output:
# Test Files  3 passed (3)
#      Tests  15 passed (15)
#   Duration  400ms

npm run build
# Output:
# ✓ 2171 modules transformed.
# dist/assets/index-B2Bf_ceu.js   417.23 kB │ gzip: 117.99 kB
# ✓ built in 2.75s
```

### Gate Checklist (Phase 4):
- [x] Guidance library returns verified static items in English and Hindi: PASS
- [x] Scam-message checker detects urgency, links, lures, and traps: PASS
- [x] Scam-message checker rejects credentials and scripts via credential guard: PASS
- [x] Evaluated message text is never stored in DB or written to logs: PASS
- [x] What-if breakdown calculates exact point reductions for R1–R10 from stored reasons: PASS
- [x] English and Hindi translations maintain 100% key and placeholder parity: PASS
- [x] Language switcher toggle works reactively in top navbar: PASS
- [x] Interactive 5-point Before-You-Pay checklist functional: PASS
- [x] App layout responsive at 360 px viewport with minimum 44×44 px tap targets: PASS
- [x] All 77 backend automated tests and 15 frontend unit tests passing: PASS
- [x] Frontend builds cleanly with zero errors in 2.75s: PASS

**Gate Status: PASS**
