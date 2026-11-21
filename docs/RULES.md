# PayGuard 360 — Explainable Risk Engine Specification (RULES.md)

**Rules Version:** `1.0.0`  
**Configuration Source:** `backend/app/risk_rules.json`  
**Implementation:** `backend/app/services/risk_engine.py` (100% line & branch coverage tested)

---

## 1. Principles & Design

1. **Advisory & Explainable:** Scores are advisory (0–100), not mathematical probabilities or absolute verdicts of fraud. Every non-zero score comes with plain-language, auditable reasons derived from a single rule execution.
2. **Pure & Deterministic:** `evaluate_risk(scoring_context, payment, rules_config, now) -> assessment_result`. Zero I/O, zero network calls, immutable context snapshot, reproducible at any point in time.
3. **No Sensitive Attributes:** No caste, religion, gender, health, biometric, or precise location signals. Synthetic tags only (`synthetic_device_tag`, `synthetic_city_tag`).
4. **Integer Paise Math:** All monetary thresholds, averages, and comparisons use integer paise (₹1 = 100 paise).
5. **Score Bands:**
   - **Low Risk:** `0 – 39` (Informational reasons displayed; payment proceeds to complete)
   - **Medium Risk:** `40 – 69` (Explicit customer review & confirmation required; post-review case logged)
   - **High Risk:** `70 – 100` (Simulated funds reserved, payment held for human reviewer evaluation)

---

## 2. Definitions & Context Contracts

- **Completed expenses:** Transactions with `type=expense` and `status=completed`, from both `payment` and `manual` sources.
- **Cold start:** User with fewer than 5 completed expenses (`len(completed_expenses) < 5`).
- **Counted payments:** Transactions with `source=payment` and status in (`pending`, `awaiting_confirmation`, `held`, `escalated`, `completed`). `cancelled` and `released` never count.
- **Tag history:** Set of synthetic device tags and city tags seen on the user's prior counted payments.

---

## 3. Rule Catalog (R1 – R10)

| Rule | Name | Points | Condition | Params Contract | Notes |
|---|---|:---:|---|---|---|
| **R1** | Unusual amount | 25 | `amount * n > 3 * sum` over most recent 30 completed expenses (requires `n >= 5`). Exactly 3× does not fire. | `{amount_paise, avg_paise, sample_size, multiple_x10}` | Skipped during cold start. Integer math only. |
| **R2** | New payee | 15 (7 in cold start) | No prior counted payment by this user to the payee. In cold start: `points // 2 = 7`. | `{payee_masked, cold_start}` | R2 alone on baseline = 15 (Low, informational). |
| **R3** | Unusual hour | 10 | Payment evaluated between `00:00 <= t < 05:00` Indian Standard Time (`Asia/Kolkata`). | `{local_hour, local_minute}` | Normalized to IST using tz-aware clock. |
| **R4** | High velocity | 25 | Counted payments within `now - 300 s`, including current: `>= 3` (personal) or `>= 8` (business). | `{count, window_seconds}` | Prevents rapid payment bursts. |
| **R5** | New synthetic tag | 15 | Device tag OR city tag not in tag history. | `{signals: ["device"\|"city"]}` | Skipped in cold start or if current tag is null. Never pushes to Medium alone. |
| **R6** | Flagged payee | 40 | Payee `trust_status = flagged`. | `{payee_masked}` | Set when confirmed fraud is recorded by human reviewers. |
| **R7** | Threshold / repeat pattern | 10 | `amount * 100 >= T * 95` and `amount < T` for `T in [₹10k, ₹50k, ₹100k]`, OR `>= 3` identical-amount counted payments to same payee within 24h. | `{conditions: ["near_threshold"\|"repeat_pattern"], threshold_paise?, repeat_count?}` | Round numbers alone never fire. |
| **R8** | Scam-language signal | 15 | Note contains whole-word scam phrase ("urgent", "refund", "lottery", "kyc update", etc.). | `{phrase_ids: [...]}` | Weak signal. Fires once regardless of phrase count. |
| **R9** | Drains balance | 15 | `amount_paise * 100 > available_balance_paise * 80`. Exactly 80% does not fire. | `{amount_paise, available_paise, share_pct}` | Protects account from near-total balance wipeout. |
| **R10** | Unknown collect request | 30 | Method is `collect_approval` and payee `trust_status != known`. | `{payee_masked, trust_status}` | High-risk UPI collect request from unfamiliar requester. |

---

## 4. Test Fixtures Summary (F1 – F11)

All 11 required fixtures from §10 pass automated verification:
- **F1 (Baseline B):** Score 0, Low, "No risk signals found".
- **F2 (New payee + ₹3,500):** R1 (25) + R2 (15) = 40, Medium.
- **F3 (Flagged payee + ₹4,000 + 02:30 IST):** R6 (40) + R1 (25) + R3 (10) = 75, High.
- **F4 (Velocity burst 3 payments):** First two 0, third R4 (25) + R2 (15) = 40, Medium.
- **F5 (Unknown collect request + scam note):** R2 (15) + R10 (30) + R8 (15) = 60, Medium.
- **F6 (F5 at 02:30 IST):** 60 + R3 (10) = 70, High.
- **F7 (New payee alone):** R2 (15) = 15, Low (informational).
- **F8 (Scam note alone):** R8 (15) = 15, Low.
- **F9 (Unseen device and city):** R5 (15) = 15, Low.
- **F10 (Constructed max context):** Raw score >= 180, capped at 100, High.
- **F11 (Cold start user):** R1 skipped, R5 skipped, R2 = 7, Low.
