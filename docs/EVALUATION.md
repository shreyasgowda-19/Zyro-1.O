# PayGuard 360 — Fraud Risk Engine Evaluation Report

> **Regulatory & Prototype Notice (§18):**
> *Data and rules were designed by the same team, so results are illustrative and do not prove real-world accuracy.*  
> Evaluation performed strictly with point-in-time correctness on a separate, unobserved **holdout dataset** (seed 1337).

---

## 1. Evaluation Methodology (§18)
- **Point-in-Time Correctness:** Every evaluated transaction is assessed using only transaction history, velocity counts, and device/city signals timestamped prior to the transaction's simulated occurrence.
- **Tuning vs. Holdout Protocol:** Rule weights, phrase sets, and threshold boundaries were configured on the tuning dataset (seed 42, 200 samples). Final metrics reported below were computed strictly on the separate **holdout dataset** (seed 1337, 300 samples).
- **Holdout Dataset Composition (N = 300):**
  - **Fraud-like Scenarios (n = 80):** High-amount payments to unfamiliar payees, rapid payment velocity bursts, late-night transactions to flagged payees, social engineering lures in payment notes, and unsolicited UPI collect approval requests.
  - **Hard Negatives (n = 70):** Legitimate but unusual transactions designed to test false-positive resistance (large rent/tuition payments to known payees, daytime payments to first-time payees, traveling users with unseen city tags, festival-season expenditure spikes, first merchant transactions during daytime).
  - **Standard Normal Transactions (n = 150):** Typical daily transactions matching historical spending patterns.

---

## 2. Key Performance Indicators on Holdout Dataset

### Operating Threshold: Medium or Higher (Score ≥ 40)
*Represents the advisory alert boundary where transactions either require explicit customer confirmation or are held for human review.*

| Metric | Holdout Value | Description |
|---|---|---|
| **Precision** | **100.0%** | True Positives / Total Flagged ($TP / (TP + FP)$) |
| **Recall (Sensitivity)** | **100.0%** | Detected Fraud / Total Real Fraud ($TP / (TP + FN)$) |
| **False Positive Rate (FPR)** | **0.0%** | Normal Transactions Flagged ($FP / (FP + TN)$) |
| **True Positives (TP)** | 80 | Fraud correctly scored Medium or High |
| **False Positives (FP)** | 0 | Legitimate transactions flagged as Medium+ |
| **True Negatives (TN)** | 220 | Legitimate transactions permitted as Low |
| **False Negatives (FN)** | 0 | Fraud transactions scoring Low |

### Operating Threshold: High Only (Score ≥ 70)
*Represents the strict hold boundary where payments are paused and funds are reserved for human review.*

| Metric | Holdout Value | Description |
|---|---|---|
| **Precision** | **100.0%** | True Positives / Total Held ($TP / (TP + FP)$) |
| **Recall** | **42.5%** | Severe Fraud Held ($TP / (TP + FN)$) |
| **False Positive Rate (FPR)** | **0.0%** | Normal Transactions Incorrectly Held |
| **True Positives (TP)** | 34 | Severe fraud successfully held |
| **False Positives (FP)** | 0 | Non-fraud payments held |
| **True Negatives (TN)** | 220 | Non-fraud payments avoiding hold |
| **False Negatives (FN)** | 46 | Fraud payments not held (handled at Medium warning) |

---

## 3. Hard-Negative Analysis (False Positive Control)

Hard negatives are legitimate transactions that share one or more surface characteristics with fraud (e.g., travel to a new city, large rent payment, first payment to a neighborhood shop).

- **Total Hard Negatives Evaluated:** 70
- **Share Scored Medium+ (Advisory Confirmation):** 0.0% (0 / 70)
- **Share Scored High (Reserved/Held):** **0.0%** (0 / 70)
- **False-Positive Mitigation Analysis:**
  - Rule R5 (Unseen device/city) contributes only 15 points, preventing traveling users from being falsely held.
  - Rule R2 (New payee) contributes 15 points (or 7 points in cold start), ensuring routine first-time payments remain Low risk.
  - Rule R1 (Unusual amount) skips when payee is known and trusted, allowing routine rent/tuition payments to complete smoothly.

---

## 4. Rule Activation Breakdown

Frequency of each deterministic rule firing across Fraud (n = 80) vs. Non-Fraud (n = 220) transactions:

| Rule Code | Rule Description | Points | Fraud Activations | Non-Fraud Activations | Dominant Target Signal |
|---|---|:---:|:---:|:---:|---|
| **R1** | Unusual Amount (> 3x mean) | 25 | 48 | 14 | Amount anomalies |
| **R2** | New / Unfamiliar Payee | 15 / 7 | 64 | 28 | Novel recipient |
| **R3** | Unusual Night Window (00:00–05:00) | 10 | 27 | 150 | Temporal anomaly |
| **R4** | Rapid Velocity Burst | 25 | 16 | 0 | Rapid consecutive payments |
| **R5** | Synthetic Device / City Anomaly | 15 | 0 | 14 | Location / device shift |
| **R6** | Flagged Payee on Watchlist | 40 | 16 | 0 | Security watchlists |
| **R7** | Structured Limit / Repeat Pattern | 10 | 0 | 0 | Structuring & duplicates |
| **R8** | Scam-Language Signal | 15 | 48 | 0 | Social engineering lures |
| **R9** | Drains Available Balance (> 80%) | 15 | 16 | 0 | Balance depletion |
| **R10** | Unknown Collect Request | 30 | 16 | 0 | Inbound collect lure |

---

## 5. Score Distribution Summary

| Cohort | Count | Min Score | Max Score | Mean Score | Median Score | Low Band (< 40) | Medium Band (40–69) | High Band (≥ 70) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fraud Cases** | 80 | 40 | 90 | 61.38 | 60 | 0.0% | 57.5% | 42.5% |
| **Non-Fraud Cases** | 220 | 0 | 25 | 11.27 | 10 | 100.0% | 0.0% | 0.0% |

---

## 6. Summary of Architectural Safeguards
1. **Advisory Scores Only:** Scores are never treated as probabilities or definitive verdicts.
2. **Separation of Duties:** High-risk holds require explicit human decision with auditable notes.
3. **No Credential Access:** The risk engine relies exclusively on transaction context, timing, amounts, and synthetic tags—never accessing or requesting sensitive user credentials.
