# PayGuard 360 — Security Architecture & Threat Model (docs/SECURITY.md)

## 1. Prototype Boundary & Threat Assumptions

PayGuard 360 is an explainable fraud detection and financial safety prototype for India.

> **CRITICAL PROTOCOL BOUNDARY:**
> - PayGuard 360 operates exclusively on simulated transactions with synthetic entities.
> - The application does not connect to real bank accounts, card networks, NPCI UPI switches, or payment gateways.
> - No real money is transferred, held, frozen, or recovered.
> - The platform operates under an explicit persistent banner: `DEMO MODE — NO REAL MONEY MOVES`.

---

## 2. Credential & Sensitive-Input Protection (§11)

### Absolute Zero-Credential Storage Standard
The platform enforces a strict security policy: **PayGuard 360 will never ask for, accept, store, or log a PIN, OTP, CVV, password, or full card number.**

### Defense-in-Depth Pipeline (`backend/app/services/credential_guard.py`):
1. **Unicode NFKC Normalization & Devanagari Mapping:**
   - Normalizes all free-text input (`note`, `payee_display_name`, scam-checker input).
   - Strips invisible zero-width spaces (`\u200B`, `\u200C`, `\u200D`, `\uFEFF`).
   - Maps Devanagari numerals (`०-९`) to standard ASCII digits (`0-9`).
2. **Proactive Credential Detection:**
   - Detects sensitive keywords (`otp`, `pin`, `cvv`, `cvc`, `password`, `passcode`, `one time password`) within 25 characters of a 3–8 digit number.
   - Detects standalone 4–8 digit numeric codes.
   - Executes the Luhn checksum algorithm on any 13–19 digit numeric sequence to block payment card numbers.
   - Recognizes legitimate postal PIN codes (e.g. `pin code 560001`) without false-alarm rejection.
3. **Script & Code Injection Defense:**
   - Rejects `<`, `>`, backticks, control characters, and `javascript:` URIs with 422 `INVALID_TEXT`.
   - Allows safe punctuation (`. , - _ / : ( ) ₹ & ' ! ? %`).
4. **Authoritative Server Enforcement & Non-Echoing Logs:**
   - Rejected credential values are **never echoed** in error response bodies or exception traces.
   - Custom `RequestValidationError` handler strips raw input fields and context before returning generic JSON envelopes.
   - Capture tests in `backend/tests/test_phase2b.py` guarantee zero credential leakage.

---

## 3. STRIDE Threat Model

| Threat Category | Potential Attack Vector | PayGuard 360 Architectural Mitigation | Verification Evidence |
|---|---|---|---|
| **Spoofing** | Forged JWT access tokens or impersonation of administrative roles. | Cryptographically signed HS256 tokens using standard library HMAC-SHA256 with constant-time verification. Role enforcement (`customer`, `reviewer`, `supervisor`) verified in dependency injection. | `tests/test_foundation.py::test_users_me_forged_token` |
| **Tampering** | Modifying compliance audit history or altering reviewer actions. | Native SQLite triggers (`BEFORE UPDATE`, `BEFORE DELETE`) on `audit_log` and `review_case_actions` raising `ABORT('append-only table')`. | `tests/test_foundation.py::test_append_only_triggers` |
| **Repudiation** | Reviewer claiming action was taken by someone else or denying note justification. | Every reviewer/supervisor decision mandates a non-empty rationale note (5–500 chars), logged with immutable actor ID and timestamp. | `tests/test_phase2c.py::test_mandatory_note_enforced` |
| **Information Disclosure** | Customer IDOR (reading another user's balance, transactions, or breakdown). | Strict ownership validation in services: queries filter by `user_id == current_user.id`. Unauthorized access returns 404 (not 403) to prevent ID enumeration. | `tests/test_phase2b.py::test_cross_customer_idor_prevention` |
| **Denial of Service** | Rapid repeated payment submissions or credential brute-forcing. | SlowAPI rate limiters configured on `/auth/login` and `/payments`. Idempotency-Key caching prevents duplicate transaction processing. | `tests/test_phase2b.py::test_idempotency_replay_and_conflict` |
| **Elevation of Privilege** | Reviewer approving their own payment or supervisor bypassing two-person rule. | Separation of duties: Reviewers cannot review their own payments. Supervisors cannot resolve cases they escalated (`resolver_id != escalator_id`). | `tests/test_phase2c.py::test_two_person_rule_blocks_self_resolving_supervisor` |

---

## 4. Privacy & Data Handling Principles

1. **Zero-Retention Heuristic Scam Checker:**
   - Message text pasted into the scam checker is processed strictly in memory.
   - Text is never inserted into SQLite tables, temporary caches, or application logging streams.
2. **Synthetic Data Tags:**
   - No real device fingerprinting or GPS geolocation is collected.
   - Device (`D1`, `D2`) and City (`Bengaluru`, `Mumbai`) indicators are synthetic demo tags.
3. **Token Storage Hygiene:**
   - JWT tokens are stored strictly in browser `sessionStorage` (never `localStorage`), terminating automatically upon tab close.
   - User language preference is stored in `localStorage` under `payguard_lang`, strictly isolated from authentication state.

---

## 5. Risk Transparency vs. Gaming Trade-Off (§10, §24 Q14)

- **The Trade-Off:** Providing a score breakdown with "what would change this score" helps legitimate users understand why a payment is risky, but theoretically allows an attacker to tailor their requests just below risk thresholds.
- **Mitigation Architecture:**
  1. **Scores are Advisory:** Scoring low does not guarantee legitimate status; scoring high does not mean instant forfeiture.
  2. **Human-in-the-Loop Review:** High-risk payments are held for human reviewers who inspect full historical context, unconstrained by individual rule thresholds.
  3. **Atomic Fund Reservation:** Funds are held during investigation, preventing rapid liquidation.
  4. **Multi-Signal Combinations:** Rules operate synergistically; altering one factor (e.g. amount) does not circumvent velocity (R4), flagged payee lists (R6), or night hours (R3).
