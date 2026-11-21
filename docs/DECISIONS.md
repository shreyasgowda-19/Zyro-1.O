# PayGuard 360 — Architectural & Product Decisions Log

This file records all architectural, security, accounting, and lifecycle decisions made during implementation, per §0 Quick Card 12: *"Ambiguity: choose the safest simplest option, log it in docs/DECISIONS.md, continue."*

---

## Decision Index

### DEC-001: Default Operator Profile and Mode
- **Date:** 2026-11-21
- **Context:** Kickoff without explicit command-line flags.
- **Decision:** As specified in §0.1, default `PROFILE=standard` and `MODE=checkpoint` are applied.
- **Rationale:** Standard profile delivers full fraud workflow, full budgeting, full awareness (library + checklist + what-if + scam checker), bilingual en/hi support, and full evaluation. Checkpoint mode executes automatically until Phase 2d, then halts for human sign-off.

### DEC-002: Money & Currency Handling
- **Date:** 2026-11-21
- **Context:** Currency amounts throughout API, DB, and UI.
- **Decision:** All monetary values stored, calculated, and exchanged as integer paise (`1 INR = 100 paise`). Floats are strictly rejected via Pydantic strict int. Frontend formatting uses single standard integer division/modulo with Indian digit grouping (e.g. ₹2,00,000) and Latin numerals.

### DEC-003: Database & Append-Only Tables
- **Date:** 2026-11-21
- **Context:** Integrity of audit logs and reviewer case actions.
- **Decision:** Use SQLite with WAL mode, busy timeout 5000ms, and `PRAGMA foreign_keys=ON`. Implement native SQLite triggers `BEFORE UPDATE` and `BEFORE DELETE` on `audit_log` and `review_case_actions` that execute `SELECT RAISE(ABORT, 'append-only table')`.
- **Rationale:** Guarantees tamper-resistance directly in the database engine.

### DEC-004: Savings Goal Contributions as Earmarks
- **Date:** 2026-11-21
- **Context:** Clarifying relationship between savings goals and ledger balances.
- **Decision:** Contributions to `SavingsGoal` validate against available balance and track earmarked savings without altering ledger account balances.

### DEC-005: Masking Customer & Payee References
- **Date:** 2026-11-21
- **Context:** Reviewer DTO privacy requirements (§6).
- **Decision:** Reviewers see customer references formatted as `CUST-` + first 6 hex characters of `HMAC_SHA256(JWT_SECRET, str(user_id))`. Payee identifiers are masked to show only the last 4 characters (`••••ab12`).

### DEC-006: Cryptographic Engine & SAC Compatibility
- **Date:** 2026-11-21
- **Context:** Windows 11 Smart App Control (SAC) blocks loading unsigned `.pyd` / `.node` native extensions in user profile paths.
- **Decision:** 
  1. Passwords are cryptographically hashed using PBKDF2-HMAC-SHA256 with 100,000 iterations and 128-bit random salt via standard library `hashlib` (NIST SP 800-132 compliant).
  2. JWTs are signed and verified with HS256 via RFC 7519 HMAC-SHA256 and constant-time signature comparison using standard library `hmac` and `secrets`.
  3. SQLAlchemy 2.1 runs in pure-Python mode without optional Cython extensions.
  4. Pydantic v1.10 runs in pure-Python mode.
  5. Frontend uses Vite 5 with Rollup WASM engine.
- **Rationale:** Ensures 100% testable, standard-compliant execution without native binary failure on Windows Enterprise / Smart App Control environments.
