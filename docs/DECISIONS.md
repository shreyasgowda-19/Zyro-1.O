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

### DEC-007: Safe Punctuation Inclusion in Credential Guard (Phase 4)
- **Date:** 2026-11-21
- **Context:** §11 specified allowed characters in free text as Unicode letters, digits, spaces, and punctuation `(. , - _ / : ( ) ₹ & ')`. Legitimate payment notes and real-world SMS messages submitted to the scam checker frequently include exclamation marks (`!`), question marks (`?`), and percentages (`%`).
- **Decision:** Include `!`, `?`, and `%` in `SAFE_TEXT_PATTERN`. Retain strict rejection of script tags (`< >`), backticks, control characters, and `javascript:`.
- **Rationale:** Prevents false-rejection of natural SMS messages and notes while preserving full protection against script and template injection.

### DEC-008: Zero-Retention Heuristic Scam-Message Checker (Phase 4)
- **Date:** 2026-11-21
- **Context:** Scam-message checker requirements (§14, §17).
- **Decision:** The scam-message checker evaluates input text strictly in memory through deterministic pattern matchers after passing input through the credential guard. The text is never stored in SQLite and never written to logging streams or error responses.
- **Rationale:** Ensures zero risk of data leakage or unintentional retention of sensitive user communications.

### DEC-009: Bilingual i18n Key & Placeholder Parity (Phase 4)
- **Date:** 2026-11-21
- **Context:** English and Hindi localization (§15).
- **Decision:** All UI copy, advisory risk reasons (R1–R10), in-app alerts, safety checklists, and scam advice are maintained in `frontend/src/i18n/en.json` and `hi.json`. Unit tests enforce 100% key and parameter-placeholder parity. The user language preference is persisted in `localStorage` under `payguard_lang`, strictly separated from JWT credentials which reside only in `sessionStorage`.
- **Rationale:** Guarantees seamless switching between English and Hindi without runtime placeholder missing errors.
