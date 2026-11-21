# PayGuard 360 — Hackathon Feasibility & Status Board

## 1. Execution Settings & Assumptions
- **Profile:** `standard` (Phases 0–5; P0 core fraud flow + P1 budgeting, awareness, Hindi i18n, evaluation).
- **Mode:** `checkpoint` (Continuous execution with pause after Phase 2d for human sign-off; immediate pause on failure or blocked state).
- **Core Strategy:** Vertical-slice delivery of fraud workflow first (P0). Phase 2 beats everything.
- **Offline & Self-Contained:** 100% deterministic local rules, SQLite WAL database, bundled fonts/assets, zero external live network/banking dependencies.

## 2. Cut Order (§0.3)
If time constraints require descope:
1. Phase 6 (ML anomaly model, spending forecast, AI summary) — Excluded by default in `standard`.
2. Extra charts and advanced forecasting.
3. Hindi translation refinement (fallback to English while keeping i18n structure).
4. Savings goals (keep main budget).
5. Scam-message checker.
6. What-if breakdown panel.
7. Per-category budgets (keep overall monthly budget).
8. **NEVER CUT:**
   - Full Phase 2 (Fraud engine, lifecycle, holds, reviewer workflow, customer alerts)
   - Credential protection (§11)
   - Ledger reconciliation (§8)
   - Demo-mode banner & notices
   - One-command reset (`< 5s`)
   - 3-minute demo script & verification

## 3. Status Board
- Phase 0: Kickoff & Planning: `IN PROGRESS`
- Phase 1: Foundation (DB, Auth, Seeds, Scaffolding): `NOT STARTED`
- Phase 2a: Pure Risk Engine: `NOT STARTED`
- Phase 2b: Accounting & Lifecycle: `NOT STARTED`
- Phase 2c: Review & Audit: `NOT STARTED`
- Phase 2d: Full UI Wire-up & Simulator: `NOT STARTED`
- Phase 3: Smart Budgeting: `NOT STARTED`
- Phase 4: Awareness & Hindi: `NOT STARTED`
- Phase 5: Evaluation & Demo Readiness: `NOT STARTED`
