# Task Tracking: PayGuard 360

**Operator Settings:**
- PROFILE: `standard`
- MODE: `checkpoint` (runs through Phase 0, 1, 2a, 2b, 2c, 2d, then pauses for human sign-off; pauses on any failure/BLOCKED)

---

## Phase Checklist

- [x] **Phase 0: Kickoff, Inspection, Plan & Setup**
  - [x] Inspect repo & verify environment (Python, Node, npm)
  - [x] Save `docs/MASTER_PROMPT.md`
  - [x] Create `task.md`, `docs/IMPLEMENTATION_LOG.md`, `docs/DECISIONS.md`, `docs/VERIFICATION_MATRIX.md`, `docs/HACKATHON_FEASIBILITY.md`
  - [x] Create `.env.example` & `.gitignore`
  - [x] Phase 0 Gate check & phase report (commit: `c797c97`, tag: `phase-0-verified`)

- [x] **Phase 1: Foundation (Backend + Frontend Scaffolding, Models, DB, Auth, Seed, Health)**
  - [x] Backend scaffolding (FastAPI, config, clock, errors, database with WAL & foreign keys)
  - [x] Pydantic schemas with strict integer paise & clean error envelope
  - [x] SQLAlchemy 2.x models & Alembic baseline migration (`render_as_batch=True`)
  - [x] SQLite triggers for append-only `AuditLog` and `ReviewCaseAction`
  - [x] Auth & security (JWT HS256, PBKDF2 password hashing, RBAC roles: customer, reviewer, supervisor)
  - [x] Seed generator (`scripts/seed_demo.py`, `scripts/reset_demo.py` < 5s)
  - [x] Health endpoint (`GET /health`)
  - [x] Frontend scaffolding (Vite + React + TypeScript + Tailwind CSS + React Router + Vitest)
  - [x] Login screen with demo account quick-picker (`rahul_personal`, `priya_personal`, `sharma_kirana`, etc.)
  - [x] Makefile / scripts (`make dev`, `make reset`, `scripts/dev.ps1`)
  - [x] Auth & foundation tests pass (7 backend, 8 frontend)
  - [x] Phase 1 Gate check & report (tag: `phase-1-verified`)

- [ ] **Phase 2a: Explainable Fraud Risk Engine (Pure, Deterministic)**
  - [ ] `backend/app/risk_rules.json` (schema-validated config)
  - [ ] Pure `risk_engine.py` implementation (R1–R10, capped at 100, bands: Low 0-39, Medium 40-69, High 70-100)
  - [ ] All fixtures F1–F11 passing
  - [ ] Unit & property tests (boundary, cap, ordering, cold start, 100% line & branch coverage)
  - [ ] `docs/RULES.md`
  - [ ] Phase 2a Gate check & report (commit: `phase-2a-verified`)

- [ ] **Phase 2b: Accounting, Lifecycle, Credential Guard, Payment API**
  - [ ] `credential_guard.py` (Luhn, OTP/PIN proximity, script-text filter, never logs sensitive input)
  - [ ] Custom `RequestValidationError` handler stripping sensitive values
  - [ ] `accounting_service.py` (integer paise, completed/held/available balances, reconciliation checks)
  - [ ] `payment_service.py` (lifecycle state machine, atomic reservations, idempotency via `Idempotency-Key`)
  - [ ] Payment routers (`POST /payments`, `GET /payments/{id}`, confirm, cancel, transactions)
  - [ ] Cross-customer IDOR protection & tests
  - [ ] Concurrency & optimistic locking tests
  - [ ] Phase 2b Gate check & report (commit: `phase-2b-verified`)

- [ ] **Phase 2c: Review Service, Supervisor Resolution, Alerts, Audit**
  - [ ] `review_service.py` (hold_review, post_review, mandatory note 5-500 chars, optimistic locking `expected_version`)
  - [ ] Supervisor escalation resolution (two-person rule: resolver != escalator)
  - [ ] `alert_service.py` (dedupe_key, customer in-app alerts)
  - [ ] Review & audit routers (`/review/cases`, `/review/cases/{id}`, `/review/cases/{id}/decision`, `/review/audit`, `/alerts`)
  - [ ] Reviewer masking: payee `••••ab12`, customer `CUST-` + 6 hex HMAC
  - [ ] Append-only DB triggers verification tests
  - [ ] Phase 2c Gate check & report (commit: `phase-2c-verified`)

- [ ] **Phase 2d: Customer Pay, Risk Result, Reviewer UI, Simulator, Reset (CHECKPOINT STOP)**
  - [ ] Frontend API client & central error layer
  - [ ] Demo banner ("DEMO MODE — NO REAL MONEY MOVES") & credential notice
  - [ ] Customer payment flow (form, before-you-pay checklist, risk result with score/reasons/badge)
  - [ ] Medium confirmation & High held flows
  - [ ] Reviewer UI (queue, case detail, mandatory note, approve/reject/escalate, supervisor resolution)
  - [ ] Customer alert drawer & transaction receipt
  - [ ] Demo simulator presets (F1 Low, F2 Medium, F3 High, F4 Burst, F5 Collect Request) + Reset button
  - [ ] One-command reset verification (`< 5s`)
  - [ ] End-to-end integration tests & verification
  - [ ] Phase 2d Checkpoint Gate check & report (commit: `phase-2d-verified`)
  - [ ] **STOP AND WAIT FOR OPERATOR SIGN-OFF**

- [ ] **Phase 3: Smart Budgeting & Reconciliation UI**
  - [ ] Manual transactions API & UI
  - [ ] Category budgets & overall budget
  - [ ] Budget 80%/100% alert engine with dedupe
  - [ ] Savings goals with earmark progress
  - [ ] Cash flow, trend, and category charts backed by real API
  - [ ] Live reconciliation UI panel
  - [ ] Phase 3 Gate check & report (commit: `phase-3-verified`)

- [ ] **Phase 4: Financial Awareness & Polish**
  - [ ] Guidance library with official verified sources (1930, cybercrime.gov.in, Sanchar Saathi)
  - [ ] Before-you-pay checklist
  - [ ] Deterministic scam-message checker (unretained input)
  - [ ] What-if / score breakdown panel
  - [ ] English + Hindi bilingual support (i18n, key parity tests, `TODO_HINDI_REVIEW.md`)
  - [ ] Responsive design (360px pass) & accessibility (WCAG AA, aria-live, tap targets >= 44px)
  - [ ] Phase 4 Gate check & report (commit: `phase-4-verified`)

- [ ] **Phase 5: Evaluation & Demo Readiness**
  - [ ] Security audit (headers, CSP, CORS, slowapi rate limits)
  - [ ] Startup checks & OpenAPI auth validation
  - [ ] Point-in-time evaluation (`scripts/evaluate.py` -> `docs/EVALUATION.md`)
  - [ ] Automated verification script (`scripts/demo_check.py` covering D1–D18)
  - [ ] Documentation (`README.md`, `DEMO_SCRIPT.md`, `DEMO_READ_ALOUD.md`, `JUDGE_DEMO_EVIDENCE.md`, `docs/JUDGE_QA.md`, `docs/ARCHITECTURE.md`, `docs/SECURITY.md`)
  - [ ] Phase 5 Gate check & report (commit: `phase-5-verified`)
