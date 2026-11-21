# PayGuard 360 — Judge Q&A & Hackathon Defense (docs/JUDGE_QA.md)

This document provides authoritative, implementation-backed answers to all judge questions specified in Master Prompt v5 (§24 and §26.6), citing exact file names, schemas, and passing test suites.

---

### Q1: What exact user problem does PayGuard 360 solve?
**Answer:** Indian digital payments (UPI) execute in milliseconds and are irreversible. Users frequently face social-engineering scams (fake electricity disconnections, lottery/refund lures, fake customer care, collect-request traps). Users are presented with generic warning text that causes alert fatigue. PayGuard 360 solves this by:
1. Evaluating transactions *before* completion with an explainable 0–100 risk score and plain-language contributing signals.
2. Intercepting high-risk transactions with ledger-aware holds and bringing human reviewers into the decision loop.
3. Giving users transparent "what would change this score" breakdowns and contextual scam awareness right at the moment of payment.

### Q2: Why is fraud detection the core feature?
**Answer:** Without pre-payment fraud prevention, budgeting and payment history are purely post-mortem tools. If a user is defrauded of their savings in an instant UPI transfer, budgeting cannot recover those funds. By prioritizing fraud prevention as the core module (P0), budgeting and payment management serve to reinforce security context (e.g. balance drain alerts, ledger-aware holds).

### Q3: How does the risk score work?
**Answer:** Implemented as a pure deterministic function in `backend/app/services/risk_engine.py`:
- Context is loaded in one consistent database snapshot (zero I/O inside the engine).
- 10 deterministic rules (R1 to R10) evaluate amount anomalies, payee history, night window (00:00–05:00 IST), velocity bursts, synthetic device/city tags, watchlists, structuring patterns, scam phrases, balance drain, and inbound collect methods.
- Rule weights and phrase sets are loaded from `backend/app/risk_rules.json`.
- The final score is the sum of fired rule points, capped at 100.
- Bands: Low (0–39), Medium (40–69), High (70–100).
- Evidence: 100% line and branch coverage in `backend/tests/test_risk_engine.py`.

### Q4: Why explainable rules before machine learning?
**Answer:** 
1. **Explainability & Trust:** When a user's transaction is held or warned, they deserve an exact, plain-language reason (e.g. "Payment is 3.5x higher than your usual average to a first-time payee"), not an opaque neural network probability.
2. **Cold-Start & Auditability:** New users and fresh payees lack massive transaction corpora. Configurable deterministic rules have zero training lag, zero drift, and produce an auditable trail required for compliance.
3. **No Hallucination or Gaming:** Rules are predictable and can be tuned transparently without black-box retraining.

### Q5: How do you reduce false positives and alert fatigue?
**Answer:** 
1. **R5 (New device/city) alone stays Low:** Traveling or logging in from a new phone adds only 15 points, remaining in the Low band (<40) without prompting friction.
2. **Cold-Start Halving:** For users with fewer than 5 transactions, R2 (New payee) points are halved from 15 to 7.
3. **R8 (Scam language) is a weak signal:** Fires only 15 points once, regardless of how many keywords appear in the note.
4. **Hard-Negative Verification:** In holdout evaluation (`docs/EVALUATION.md`), 70 hard negatives (large rent payments, festival shopping, daytime first merchants) achieved a 0.0% false hold rate.

### Q6: What happens when a payment is held, and when it is escalated?
**Answer:** 
- **Held:** The payment transitions to `status = 'held'`. The transaction amount is atomically reserved: `available_balance = completed_balance - held_balance`. A `ReviewCase` (`case_type = 'hold_review'`) is created for fraud reviewers (`backend/app/services/payment_service.py`).
- **Reviewer Action:** A reviewer in `frontend/src/pages/ReviewQueuePage.tsx` can Approve, Reject, or Escalate. All actions require a mandatory justification note (5–500 chars).
- **Escalated:** Transitions to `status = 'escalated'`. Only a senior supervisor can resolve it. Enforces the two-person rule: `resolver_id != escalator_id` (`tests/test_phase2c.py::test_two_person_rule_blocks_self_resolving_supervisor`).

### Q7: Can the prototype stop a real UPI payment?
**Answer:** **No.** PayGuard 360 is an explicit software prototype with synthetic data. It connects to no real banking switches, NPCI networks, or live gateways. Persistent banner: `DEMO MODE — NO REAL MONEY MOVES`.

### Q8: Does the app store OTPs, PINs or card credentials?
**Answer:** **No, absolutely never.** Verified in `backend/app/services/credential_guard.py` and `tests/test_phase2b.py`. The system has no database fields, schemas, or memory stores for credentials. Free-text inputs containing PIN/OTP proximity, standalone numeric codes, or Luhn card numbers are rejected with 422 `CREDENTIAL_INPUT_REJECTED` without logging or echoing the secret.

### Q9: How is customer data isolated?
**Answer:** Enforced at the service and ORM query level: every customer query filters strictly by `user_id == current_user.id`. Cross-customer IDOR attempts return 404 (preventing record enumeration). Verified in `tests/test_phase2b.py::test_cross_customer_idor_prevention` and `tests/test_phase4.py::test_risk_breakdown_comprehensive`.

### Q10: How was the fraud engine evaluated?
**Answer:** Executed via `scripts/evaluate.py` using point-in-time correctness on a separate unobserved holdout dataset (seed 1337, N=300).
- Results: 100% Precision and 100% Recall at Medium+ threshold; 100% Precision and 42.5% Recall at High-only threshold; 0.0% false-positive rate on hard negatives. Documented in `docs/EVALUATION.md`.

### Q11: Why are synthetic evaluation results not proof of real-world accuracy?
**Answer:** Synthetic datasets and deterministic rules were authored by the same engineering team. In real-world environments, adversarial fraudsters actively evolve evasion techniques. Real production accuracy requires live production telemetry, consented device signals, and calibrated statistical validation.

### Q12: What would a regulated, production-grade deployment require?
**Answer:** 
1. Payment Aggregator (PA) or Payment System Operator (PSO) regulatory licenses from the Reserve Bank of India (RBI).
2. Direct API integration with bank switches and NPCI UPI rails.
3. Consent-driven device SDK for device binding and SIM verification.
4. Compliance with India's Digital Personal Data Protection (DPDP) Act 2023.
5. Migration from SQLite WAL to high-availability PostgreSQL with Kafka/RabbitMQ event queues and HSM credential security.

### Q13: Payment apps already show warnings. What is different here?
**Answer:** Existing apps display static, generic warnings that users routinely ignore. PayGuard 360 introduces:
1. **Explainable contributing reasons** showing exactly why the score was assigned.
2. **Interactive "what would change this score" breakdowns** showing actionable levers.
3. **Human-in-the-loop review** with funds reserved in the ledger.
4. **Integration with personal budgeting** showing the financial impact before payment execution.

### Q14: If the rules are transparent, can fraudsters game them?
**Answer:** Documented in `docs/SECURITY.md`. Mitigated by:
- Human review layer: Borderline transactions that evade one rule remain subject to synergistic multi-rule scoring and analyst inspection.
- Ledger holds: Funds are held during investigation, preventing instant fund extraction.
- Rules versioning: Rule thresholds and scam phrases are updated centrally in `risk_rules.json` without frontend exposure of raw logic.

### Q15: What privacy choices did you make?
**Answer:** 
- **Zero-retention scam checker:** Input text is evaluated in memory and never stored in SQLite or application logs (`backend/app/services/scam_checker_service.py`).
- **Synthetic tags:** Only high-level synthetic tags (`D1`, `Bengaluru`) are used, with zero GPS or hardware scraping.
- **Masked identifiers:** Payees (`••••1029`) and customers (`CUST-xxxx`) are masked in reviewer consoles.
- **Session-only tokens:** Auth tokens reside in `sessionStorage`, never `localStorage`.

### Q16: How would this scale?
**Answer:** The risk engine is a pure, stateless function with $O(1)$ computation time per payment. In production, it scales horizontally across stateless microservices behind an API gateway, utilizing Redis for velocity counters and PostgreSQL for ACID ledger transactions.

### Q17: What is your roadmap?
**Answer:** 
- **P0/P1 (Completed):** Pure risk engine, human review console, ledger holds, budgeting, scam checker, bilingual localization.
- **Phase 5 (Completed):** Point-in-time holdout evaluation, automated D1–D18 demo check suite, security audit.
- **Future:** Bank sandbox integration, calibrated ML anomaly detection with rule-based fallback, automated UPI auto-reversal integrations, and regional languages (Tamil, Telugu, Kannada, Bengali).

### Q18: What did you deliberately not build, and why?
**Answer:** 
1. **Real Payment Gateways:** Real money movements violate hackathon safety and licensing regulations.
2. **Black-box Deep Learning:** ML before verified rules obscures explainability and introduces false-positive unpredictability.
3. **PIN/OTP Input:** Building credential inputs violates zero-credential storage security principles.
4. **Biometric Scans / Fake Maps:** Gimmicks detract from core fintech integrity and ledger reliability.

---

### Hackathon Judging Questions (§26.6)

### Q19: What is innovative?
**Answer:** The innovation is the unified integration of **explainable pre-payment risk scoring**, **human-in-the-loop reviewer oversight**, and **ledger-aware fund holds**. Rather than treating fraud as a separate alert banner, PayGuard 360 embeds security into accounting continuity.

### Q20: What is the WOW moment?
**Answer:** When the customer triggers a High-risk payment (Preset F3), the platform explains three specific risk reasons, displays the score breakdown, automatically pauses the payment, and visibly splits balances: **Available balance drops immediately while Completed balance remains untouched**, visually demonstrating fund reservation. The reviewer then reviews the case, applies a mandatory rationale, and resolves the hold.

### Q21: Why is this feasible in a hackathon?
**Answer:** By establishing strict architectural boundaries (simulated data, pure deterministic rules, SQLite WAL, in-process evaluation), the entire stack runs offline, requires zero external paid APIs, and restores to a pristine seeded state in 0.28 seconds.

### Q22: What is genuinely working today?
**Answer:** All 18 Definition of Done items (D1 through D18) are 100% verified and demonstrable:
- Live customer pay flow with instant risk scoring and reasons.
- Reviewer console with case inspection, mandatory notes, and supervisor escalation.
- Ledger accounting with 4/4 live reconciliation checks.
- Smart budgeting with 80%/100% alert deduplication.
- Bilingual English/Hindi interface with 100% translation key parity.
- Deterministic scam checker with zero retention.
- One-click demo simulator and reset (< 0.5s).

### Q23: What are the prototype limitations?
**Answer:** 
- Simulated payments only (no real banking connections).
- Review cases in prototype are resolved manually by demo reviewers, whereas production would feature automated triage tiers.
- In-memory rate limiting and SQLite storage are tailored for prototype demonstrations, requiring distributed queues and databases for multi-tenant production scale.
