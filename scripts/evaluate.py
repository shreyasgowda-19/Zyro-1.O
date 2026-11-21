import os
import sys
import json
import random
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Tuple
import pytz

# Add backend directory to sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.services.risk_engine import evaluate_risk
from app.config import BASE_DIR, settings

IST = pytz.timezone("Asia/Kolkata")

def load_rules_config() -> Dict[str, Any]:
    rules_path = os.path.join(BACKEND_DIR, settings.RULES_CONFIG_PATH)
    if not os.path.exists(rules_path):
        rules_path = os.path.join(PROJECT_ROOT, "backend", "app", "risk_rules.json")
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)

class SyntheticTransactionGenerator:
    """
    Deterministic synthetic transaction generator for tuning and holdout datasets.
    Supports fraud-like scenarios, hard negatives, and standard normal traffic.
    """
    def __init__(self, seed: int):
        self.rng = random.Random(seed)
        self.base_time = datetime(2026, 11, 1, 10, 0, 0, tzinfo=timezone.utc)

    def generate_user_history(self, num_expenses: int = 15) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[str], List[str], int]:
        completed = []
        counted = []
        devices = ["D1", "D2"]
        cities = ["Bengaluru", "Mysuru"]
        
        for i in range(num_expenses):
            t = self.base_time - timedelta(days=num_expenses - i, hours=self.rng.randint(1, 10))
            amt = self.rng.choice([50000, 80000, 100000, 120000, 150000])  # ₹500 - ₹1,500
            payee = self.rng.choice([1, 2, 3])
            dev = self.rng.choice(devices)
            city = self.rng.choice(cities)
            
            completed.append({"amount_paise": amt, "created_at": t})
            counted.append({
                "payee_id": payee,
                "amount_paise": amt,
                "created_at": t,
                "device_tag": dev,
                "city_tag": city
            })
            
        avail_balance = self.rng.choice([3000000, 5000000, 7500000])  # ₹30k - ₹75k
        return completed, counted, devices, cities, avail_balance

    def generate_dataset(self, num_fraud: int, num_hard_neg: int, num_normal: int) -> List[Dict[str, Any]]:
        dataset = []

        # 1. Fraud-like scenarios
        fraud_types = [
            "large_first_time",
            "burst_velocity",
            "late_night_flagged",
            "scam_note_lure",
            "unknown_collect"
        ]
        for i in range(num_fraud):
            completed, counted, devices, cities, avail = self.generate_user_history()
            ftype = fraud_types[i % len(fraud_types)]
            tx_time = self.base_time + timedelta(hours=i * 2)

            if ftype == "large_first_time":
                # High amount to new payee (R1 + R2)
                payment = {
                    "amount_paise": 400000,  # ₹4,000 (>3x avg)
                    "payee_id": 999 + i,
                    "payee_masked": "••••8888",
                    "method": "upi",
                    "note": "Payment",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "new",
                    "is_new_payee": True,
                    "profile_type": "personal"
                }

            elif ftype == "burst_velocity":
                # 3 rapid payments in 2 mins (R4)
                recent_time = tx_time - timedelta(seconds=60)
                counted.append({"payee_id": 1, "amount_paise": 20000, "created_at": recent_time, "device_tag": devices[0], "city_tag": cities[0]})
                counted.append({"payee_id": 1, "amount_paise": 25000, "created_at": recent_time + timedelta(seconds=30), "device_tag": devices[0], "city_tag": cities[0]})
                payment = {
                    "amount_paise": 30000,
                    "payee_id": 999 + i,
                    "payee_masked": "••••7777",
                    "method": "upi",
                    "note": "Quick split",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "new",
                    "is_new_payee": True,
                    "profile_type": "personal"
                }

            elif ftype == "late_night_flagged":
                # 02:30 IST to flagged payee (R6 + R3 + R1)
                tx_time_ist = datetime(2026, 11, 2, 2, 30, 0, tzinfo=IST).astimezone(timezone.utc)
                tx_time = tx_time_ist
                payment = {
                    "amount_paise": 450000,
                    "payee_id": 888,
                    "payee_masked": "••••9191",
                    "method": "upi",
                    "note": "Urgent transfer",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "flagged",
                    "is_new_payee": False,
                    "profile_type": "personal"
                }

            elif ftype == "scam_note_lure":
                # New payee + scam note + drains balance (R2 + R8 + R9)
                payment = {
                    "amount_paise": int(avail * 0.85),
                    "payee_id": 999 + i,
                    "payee_masked": "••••5555",
                    "method": "upi",
                    "note": "Lottery prize processing fee urgent refund",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "new",
                    "is_new_payee": True,
                    "profile_type": "personal"
                }

            else:  # unknown_collect
                # Collect request + new requester + scam phrase (R10 + R2 + R8)
                payment = {
                    "amount_paise": 50000,
                    "payee_id": 999 + i,
                    "payee_masked": "••••4444",
                    "method": "collect_approval",
                    "note": "Electricity KYC update",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "new",
                    "is_new_payee": True,
                    "profile_type": "personal"
                }

            dataset.append({
                "id": f"fraud_{i}",
                "is_fraud": True,
                "is_hard_negative": False,
                "category_label": ftype,
                "payment": payment,
                "context": ctx,
                "timestamp": tx_time
            })

        # 2. Hard Negatives (Legitimate but unusual)
        hn_types = [
            "large_rent_tuition_known",
            "new_payee_daytime_normal",
            "travelling_new_city",
            "festival_spike_known",
            "first_merchant_normal_hour"
        ]
        for i in range(num_hard_neg):
            completed, counted, devices, cities, avail = self.generate_user_history()
            htype = hn_types[i % len(hn_types)]
            tx_time = self.base_time + timedelta(hours=14)  # 2 PM daytime

            if htype == "large_rent_tuition_known":
                # Known payee, large rent payment (R1 fires, but known payee so R2 doesn't)
                payment = {
                    "amount_paise": 350000,  # ₹3,500
                    "payee_id": 1,  # Known payee in history
                    "payee_masked": "••••1111",
                    "method": "netbanking",
                    "note": "Monthly house rent",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": 20000000,
                    "payee_trust_status": "known",
                    "is_new_payee": False,
                    "profile_type": "personal"
                }

            elif htype == "new_payee_daytime_normal":
                # Ordinary ₹600 payment to new payee at 14:00 (Only R2 fires: 15 pts -> Low)
                payment = {
                    "amount_paise": 60000,
                    "payee_id": 800 + i,
                    "payee_masked": "••••8234",
                    "method": "upi",
                    "note": "Lunch bill split",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "new",
                    "is_new_payee": True,
                    "profile_type": "personal"
                }

            elif htype == "travelling_new_city":
                # User travelling to Mumbai with new city tag (Only R5 fires: 15 pts -> Low)
                payment = {
                    "amount_paise": 75000,
                    "payee_id": 1,  # known payee
                    "payee_masked": "••••1111",
                    "method": "upi",
                    "note": "Hotel chai and snacks",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": "Mumbai"  # Unseen city
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "known",
                    "is_new_payee": False,
                    "profile_type": "personal"
                }

            elif htype == "festival_spike_known":
                # Festival gifts to known relative (₹2,500, known payee)
                payment = {
                    "amount_paise": 250000,
                    "payee_id": 2,
                    "payee_masked": "••••2222",
                    "method": "upi",
                    "note": "Diwali gift sweets",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "known",
                    "is_new_payee": False,
                    "profile_type": "personal"
                }

            else:  # first_merchant_normal_hour
                # First payment to supermarket merchant during day (₹850)
                payment = {
                    "amount_paise": 85000,
                    "payee_id": 850 + i,
                    "payee_masked": "••••9911",
                    "method": "upi",
                    "note": "Groceries purchase",
                    "synthetic_device_tag": devices[0],
                    "synthetic_city_tag": cities[0]
                }
                ctx = {
                    "completed_expenses": completed,
                    "counted_payments": counted,
                    "tag_history_devices": devices,
                    "tag_history_cities": cities,
                    "available_balance_paise": avail,
                    "payee_trust_status": "new",
                    "is_new_payee": True,
                    "profile_type": "personal"
                }

            dataset.append({
                "id": f"hard_neg_{i}",
                "is_fraud": False,
                "is_hard_negative": True,
                "category_label": htype,
                "payment": payment,
                "context": ctx,
                "timestamp": tx_time
            })

        # 3. Standard Normal Legitimate Transactions
        for i in range(num_normal):
            completed, counted, devices, cities, avail = self.generate_user_history()
            tx_time = self.base_time + timedelta(hours=11)
            amt = self.rng.choice([25000, 50000, 75000, 100000, 120000])
            payment = {
                "amount_paise": amt,
                "payee_id": 1,
                "payee_masked": "••••1111",
                "method": "upi",
                "note": "Daily expense",
                "synthetic_device_tag": devices[0],
                "synthetic_city_tag": cities[0]
            }
            ctx = {
                "completed_expenses": completed,
                "counted_payments": counted,
                "tag_history_devices": devices,
                "tag_history_cities": cities,
                "available_balance_paise": avail,
                "payee_trust_status": "known",
                "is_new_payee": False,
                "profile_type": "personal"
            }
            dataset.append({
                "id": f"normal_{i}",
                "is_fraud": False,
                "is_hard_negative": False,
                "category_label": "standard_normal",
                "payment": payment,
                "context": ctx,
                "timestamp": tx_time
            })

        # Deterministic shuffle
        self.rng.shuffle(dataset)
        return dataset

def run_evaluation():
    rules_config = load_rules_config()
    
    # 1. Generate Datasets
    # Tuning set: seed 42 (200 records)
    tuning_gen = SyntheticTransactionGenerator(seed=42)
    tuning_data = tuning_gen.generate_dataset(num_fraud=50, num_hard_neg=50, num_normal=100)

    # Holdout set: seed 1337 (300 records)
    holdout_gen = SyntheticTransactionGenerator(seed=1337)
    holdout_data = holdout_gen.generate_dataset(num_fraud=80, num_hard_neg=70, num_normal=150)

    # 2. Evaluate Holdout (reporting final metrics strictly on holdout per §18)
    results = []
    rule_activations_fraud = {f"R{i}": 0 for i in range(1, 11)}
    rule_activations_non_fraud = {f"R{i}": 0 for i in range(1, 11)}

    for item in holdout_data:
        res = evaluate_risk(
            scoring_context=item["context"],
            payment=item["payment"],
            rules_config=rules_config,
            now=item["timestamp"]
        )
        
        # Track activations
        for r in res.reasons:
            if item["is_fraud"]:
                rule_activations_fraud[r.rule_code] += 1
            else:
                rule_activations_non_fraud[r.rule_code] += 1

        results.append({
            "id": item["id"],
            "is_fraud": item["is_fraud"],
            "is_hard_negative": item["is_hard_negative"],
            "category": item["category_label"],
            "score": res.score,
            "band": res.band,
            "reasons": [r.rule_code for r in res.reasons]
        })

    # 3. Compute Metrics for Medium+ (Score >= 40)
    tp_med = sum(1 for r in results if r["is_fraud"] and r["score"] >= 40)
    fp_med = sum(1 for r in results if not r["is_fraud"] and r["score"] >= 40)
    fn_med = sum(1 for r in results if r["is_fraud"] and r["score"] < 40)
    tn_med = sum(1 for r in results if not r["is_fraud"] and r["score"] < 40)

    precision_med = tp_med / (tp_med + fp_med) if (tp_med + fp_med) > 0 else 0.0
    recall_med = tp_med / (tp_med + fn_med) if (tp_med + fn_med) > 0 else 0.0
    fpr_med = fp_med / (fp_med + tn_med) if (fp_med + tn_med) > 0 else 0.0

    # 4. Compute Metrics for High-Only (Score >= 70)
    tp_high = sum(1 for r in results if r["is_fraud"] and r["score"] >= 70)
    fp_high = sum(1 for r in results if not r["is_fraud"] and r["score"] >= 70)
    fn_high = sum(1 for r in results if r["is_fraud"] and r["score"] < 70)
    tn_high = sum(1 for r in results if not r["is_fraud"] and r["score"] < 70)

    precision_high = tp_high / (tp_high + fp_high) if (tp_high + fp_high) > 0 else 0.0
    recall_high = tp_high / (tp_high + fn_high) if (tp_high + fn_high) > 0 else 0.0
    fpr_high = fp_high / (fp_high + tn_high) if (fp_high + tn_high) > 0 else 0.0

    # 5. Hard Negatives Specific Analysis
    hard_negs = [r for r in results if r["is_hard_negative"]]
    hn_total = len(hard_negs)
    hn_med_plus = sum(1 for r in hard_negs if r["score"] >= 40)
    hn_high = sum(1 for r in hard_negs if r["score"] >= 70)
    hn_share_med = (hn_med_plus / hn_total) if hn_total > 0 else 0.0
    hn_share_high = (hn_high / hn_total) if hn_total > 0 else 0.0

    # 6. Score Distribution
    fraud_scores = [r["score"] for r in results if r["is_fraud"]]
    non_fraud_scores = [r["score"] for r in results if not r["is_fraud"]]

    def get_distribution(scores: List[int]) -> Dict[str, Any]:
        if not scores:
            return {}
        sorted_s = sorted(scores)
        n = len(sorted_s)
        mean_s = sum(sorted_s) / n
        median_s = sorted_s[n // 2]
        low_count = sum(1 for s in scores if s < 40)
        med_count = sum(1 for s in scores if 40 <= s < 70)
        high_count = sum(1 for s in scores if s >= 70)
        return {
            "count": n,
            "min": min(scores),
            "max": max(scores),
            "mean": round(mean_s, 2),
            "median": median_s,
            "low_pct": round(low_count / n * 100, 1),
            "med_pct": round(med_count / n * 100, 1),
            "high_pct": round(high_count / n * 100, 1)
        }

    fraud_dist = get_distribution(fraud_scores)
    non_fraud_dist = get_distribution(non_fraud_scores)

    # 7. Write docs/EVALUATION.md
    eval_doc_path = os.path.join(PROJECT_ROOT, "docs", "EVALUATION.md")
    with open(eval_doc_path, "w", encoding="utf-8") as f:
        f.write(f"""# PayGuard 360 — Fraud Risk Engine Evaluation Report

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
| **Precision** | **{precision_med * 100:.1f}%** | True Positives / Total Flagged ($TP / (TP + FP)$) |
| **Recall (Sensitivity)** | **{recall_med * 100:.1f}%** | Detected Fraud / Total Real Fraud ($TP / (TP + FN)$) |
| **False Positive Rate (FPR)** | **{fpr_med * 100:.1f}%** | Normal Transactions Flagged ($FP / (FP + TN)$) |
| **True Positives (TP)** | {tp_med} | Fraud correctly scored Medium or High |
| **False Positives (FP)** | {fp_med} | Legitimate transactions flagged as Medium+ |
| **True Negatives (TN)** | {tn_med} | Legitimate transactions permitted as Low |
| **False Negatives (FN)** | {fn_med} | Fraud transactions scoring Low |

### Operating Threshold: High Only (Score ≥ 70)
*Represents the strict hold boundary where payments are paused and funds are reserved for human review.*

| Metric | Holdout Value | Description |
|---|---|---|
| **Precision** | **{precision_high * 100:.1f}%** | True Positives / Total Held ($TP / (TP + FP)$) |
| **Recall** | **{recall_high * 100:.1f}%** | Severe Fraud Held ($TP / (TP + FN)$) |
| **False Positive Rate (FPR)** | **{fpr_high * 100:.1f}%** | Normal Transactions Incorrectly Held |
| **True Positives (TP)** | {tp_high} | Severe fraud successfully held |
| **False Positives (FP)** | {fp_high} | Non-fraud payments held |
| **True Negatives (TN)** | {tn_high} | Non-fraud payments avoiding hold |
| **False Negatives (FN)** | {fn_high} | Fraud payments not held (handled at Medium warning) |

---

## 3. Hard-Negative Analysis (False Positive Control)

Hard negatives are legitimate transactions that share one or more surface characteristics with fraud (e.g., travel to a new city, large rent payment, first payment to a neighborhood shop).

- **Total Hard Negatives Evaluated:** {hn_total}
- **Share Scored Medium+ (Advisory Confirmation):** {hn_share_med * 100:.1f}% ({hn_med_plus} / {hn_total})
- **Share Scored High (Reserved/Held):** **{hn_share_high * 100:.1f}%** ({hn_high} / {hn_total})
- **False-Positive Mitigation Analysis:**
  - Rule R5 (Unseen device/city) contributes only 15 points, preventing traveling users from being falsely held.
  - Rule R2 (New payee) contributes 15 points (or 7 points in cold start), ensuring routine first-time payments remain Low risk.
  - Rule R1 (Unusual amount) skips when payee is known and trusted, allowing routine rent/tuition payments to complete smoothly.

---

## 4. Rule Activation Breakdown

Frequency of each deterministic rule firing across Fraud (n = 80) vs. Non-Fraud (n = 220) transactions:

| Rule Code | Rule Description | Points | Fraud Activations | Non-Fraud Activations | Dominant Target Signal |
|---|---|:---:|:---:|:---:|---|
| **R1** | Unusual Amount (> 3x mean) | 25 | {rule_activations_fraud['R1']} | {rule_activations_non_fraud['R1']} | Amount anomalies |
| **R2** | New / Unfamiliar Payee | 15 / 7 | {rule_activations_fraud['R2']} | {rule_activations_non_fraud['R2']} | Novel recipient |
| **R3** | Unusual Night Window (00:00–05:00) | 10 | {rule_activations_fraud['R3']} | {rule_activations_non_fraud['R3']} | Temporal anomaly |
| **R4** | Rapid Velocity Burst | 25 | {rule_activations_fraud['R4']} | {rule_activations_non_fraud['R4']} | Rapid consecutive payments |
| **R5** | Synthetic Device / City Anomaly | 15 | {rule_activations_fraud['R5']} | {rule_activations_non_fraud['R5']} | Location / device shift |
| **R6** | Flagged Payee on Watchlist | 40 | {rule_activations_fraud['R6']} | {rule_activations_non_fraud['R6']} | Security watchlists |
| **R7** | Structured Limit / Repeat Pattern | 10 | {rule_activations_fraud['R7']} | {rule_activations_non_fraud['R7']} | Structuring & duplicates |
| **R8** | Scam-Language Signal | 15 | {rule_activations_fraud['R8']} | {rule_activations_non_fraud['R8']} | Social engineering lures |
| **R9** | Drains Available Balance (> 80%) | 15 | {rule_activations_fraud['R9']} | {rule_activations_non_fraud['R9']} | Balance depletion |
| **R10** | Unknown Collect Request | 30 | {rule_activations_fraud['R10']} | {rule_activations_non_fraud['R10']} | Inbound collect lure |

---

## 5. Score Distribution Summary

| Cohort | Count | Min Score | Max Score | Mean Score | Median Score | Low Band (< 40) | Medium Band (40–69) | High Band (≥ 70) |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Fraud Cases** | {fraud_dist['count']} | {fraud_dist['min']} | {fraud_dist['max']} | {fraud_dist['mean']} | {fraud_dist['median']} | {fraud_dist['low_pct']}% | {fraud_dist['med_pct']}% | {fraud_dist['high_pct']}% |
| **Non-Fraud Cases** | {non_fraud_dist['count']} | {non_fraud_dist['min']} | {non_fraud_dist['max']} | {non_fraud_dist['mean']} | {non_fraud_dist['median']} | {non_fraud_dist['low_pct']}% | {non_fraud_dist['med_pct']}% | {non_fraud_dist['high_pct']}% |

---

## 6. Summary of Architectural Safeguards
1. **Advisory Scores Only:** Scores are never treated as probabilities or definitive verdicts.
2. **Separation of Duties:** High-risk holds require explicit human decision with auditable notes.
3. **No Credential Access:** The risk engine relies exclusively on transaction context, timing, amounts, and synthetic tags—never accessing or requesting sensitive user credentials.
""")
    print("Evaluation completed successfully!")
    print(f"Results written to: {eval_doc_path}")
    print(f"Holdout Medium+ Recall: {recall_med * 100:.1f}%, Precision: {precision_med * 100:.1f}%")
    print(f"Holdout High-Only Recall: {recall_high * 100:.1f}%, Precision: {precision_high * 100:.1f}%")

if __name__ == "__main__":
    run_evaluation()
