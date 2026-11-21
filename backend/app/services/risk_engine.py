import re
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, List, Optional, Set
import pytz

IST = pytz.timezone("Asia/Kolkata")

class RiskReasonResult:
    def __init__(self, rule_code: str, points: int, params: Dict[str, Any]):
        self.rule_code = rule_code
        self.points = points
        self.params = params

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_code": self.rule_code,
            "points": self.points,
            "params": self.params
        }

class RiskAssessmentResult:
    def __init__(
        self,
        score: int,
        raw_score: int,
        band: str,
        rules_version: str,
        reasons: List[RiskReasonResult],
        features: Dict[str, Any]
    ):
        self.score = score
        self.raw_score = raw_score
        self.band = band
        self.rules_version = rules_version
        self.reasons = reasons
        self.features = features

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "raw_score": self.raw_score,
            "band": self.band,
            "rules_version": self.rules_version,
            "reasons": [r.to_dict() for r in self.reasons],
            "features": self.features
        }

def evaluate_risk(
    scoring_context: Dict[str, Any],
    payment: Dict[str, Any],
    rules_config: Dict[str, Any],
    now: datetime
) -> RiskAssessmentResult:
    """
    Pure, deterministic risk engine (§10).
    (scoring_context, payment, rules_config, now) -> RiskAssessmentResult
    """
    rules = rules_config.get("rules", {})
    rules_version = rules_config.get("rules_version", "1.0.0")
    bands_config = rules_config.get("bands", {"low": [0, 39], "medium": [40, 69], "high": [70, 100]})

    # Ensure now is timezone aware UTC
    now_utc = now if now.tzinfo else now.replace(tzinfo=timezone.utc)
    now_utc = now_utc.astimezone(timezone.utc)
    now_ist = now_utc.astimezone(IST)

    # Extract payment details
    amount_paise = int(payment["amount_paise"])
    payee_id = payment.get("payee_id")
    payee_masked = payment.get("payee_masked", "••••0000")
    method = payment.get("method", "upi")
    note = (payment.get("note") or "").strip()
    device_tag = payment.get("synthetic_device_tag")
    city_tag = payment.get("synthetic_city_tag")

    # Extract context
    completed_expenses = scoring_context.get("completed_expenses", [])
    counted_payments = scoring_context.get("counted_payments", [])
    tag_history_devices: Set[str] = set(scoring_context.get("tag_history_devices", []))
    tag_history_cities: Set[str] = set(scoring_context.get("tag_history_cities", []))
    available_balance_paise = int(scoring_context.get("available_balance_paise", 0))
    payee_trust_status = scoring_context.get("payee_trust_status", "new")
    profile_type = scoring_context.get("profile_type", "personal")
    is_new_payee = scoring_context.get("is_new_payee", False)

    # Context flags
    num_completed_expenses = len(completed_expenses)
    is_cold_start = num_completed_expenses < 5

    reasons: List[RiskReasonResult] = []

    # Features for audit and deterministic re-explanation
    features = {
        "completed_expenses_count": num_completed_expenses,
        "is_cold_start": is_cold_start,
        "amount_paise": amount_paise,
        "available_balance_paise": available_balance_paise,
        "payee_trust_status": payee_trust_status,
        "method": method,
        "local_hour": now_ist.hour,
        "local_minute": now_ist.minute,
        "profile_type": profile_type
    }

    # -------------------------------------------------------------
    # R1: Unusual amount
    # >= 5 completed expenses and amount * n > 3 * sum over most recent 30 completed expenses.
    # Exactly 3x does not fire.
    # -------------------------------------------------------------
    if "R1" in rules and not is_cold_start:
        r1_cfg = rules["R1"]
        # Take up to most recent 30 completed expenses
        sample_expenses = completed_expenses[:r1_cfg.get("max_history_size", 30)]
        n = len(sample_expenses)
        if n >= r1_cfg.get("min_sample_size", 5):
            sum_paise = sum(int(e["amount_paise"]) for e in sample_expenses)
            avg_paise = sum_paise // n
            multiplier = r1_cfg.get("multiplier", 3)
            if amount_paise * n > multiplier * sum_paise:
                multiple_x10 = (amount_paise * 10) // (avg_paise if avg_paise > 0 else 1)
                reasons.append(RiskReasonResult(
                    rule_code="R1",
                    points=r1_cfg["points"],
                    params={
                        "amount_paise": amount_paise,
                        "avg_paise": avg_paise,
                        "sample_size": n,
                        "multiple_x10": multiple_x10
                    }
                ))

    # -------------------------------------------------------------
    # R2: New payee
    # No prior counted payment to this payee.
    # In cold start: points // 2 = 7.
    # -------------------------------------------------------------
    if "R2" in rules and is_new_payee:
        r2_cfg = rules["R2"]
        points = r2_cfg["cold_start_points"] if is_cold_start else r2_cfg["points"]
        reasons.append(RiskReasonResult(
            rule_code="R2",
            points=points,
            params={
                "payee_masked": payee_masked,
                "cold_start": is_cold_start
            }
        ))

    # -------------------------------------------------------------
    # R3: Unusual hour
    # Local time 00:00 <= t < 05:00 IST.
    # -------------------------------------------------------------
    if "R3" in rules:
        r3_cfg = rules["R3"]
        start_hour = r3_cfg.get("start_hour", 0)
        end_hour = r3_cfg.get("end_hour", 5)
        # Hour check: 0 <= hour < 5
        if start_hour <= now_ist.hour < end_hour:
            reasons.append(RiskReasonResult(
                rule_code="R3",
                points=r3_cfg["points"],
                params={
                    "local_hour": now_ist.hour,
                    "local_minute": now_ist.minute
                }
            ))

    # -------------------------------------------------------------
    # R4: High velocity
    # Counted payments with created_at > now - 300 s, INCLUDING current:
    # >= 3 (personal) or >= 8 (business).
    # -------------------------------------------------------------
    if "R4" in rules:
        r4_cfg = rules["R4"]
        window_seconds = r4_cfg.get("window_seconds", 300)
        cutoff = now_utc - timedelta(seconds=window_seconds)

        # Count prior counted payments within window
        window_count = 0
        for p in counted_payments:
            p_time = p["created_at"]
            if p_time.tzinfo is None:
                p_time = p_time.replace(tzinfo=timezone.utc)
            if p_time > cutoff:
                window_count += 1

        total_velocity = window_count + 1  # Including current payment
        features["velocity_count_300s"] = total_velocity

        threshold = r4_cfg.get("business_threshold", 8) if profile_type == "business" else r4_cfg.get("personal_threshold", 3)
        if total_velocity >= threshold:
            reasons.append(RiskReasonResult(
                rule_code="R4",
                points=r4_cfg["points"],
                params={
                    "count": total_velocity,
                    "window_seconds": window_seconds
                }
            ))

    # -------------------------------------------------------------
    # R5: New synthetic device or city
    # Device tag OR city tag not seen in tag history.
    # Fires once; params list signals. Skipped when user has no tag history or tag is null.
    # -------------------------------------------------------------
    if "R5" in rules and not is_cold_start:
        r5_cfg = rules["R5"]
        signals = []
        has_tag_history = len(tag_history_devices) > 0 or len(tag_history_cities) > 0

        if has_tag_history:
            if device_tag and device_tag not in tag_history_devices:
                signals.append("device")
            if city_tag and city_tag not in tag_history_cities:
                signals.append("city")

            if signals:
                reasons.append(RiskReasonResult(
                    rule_code="R5",
                    points=r5_cfg["points"],
                    params={"signals": signals}
                ))

    # -------------------------------------------------------------
    # R6: Flagged payee
    # Payee trust_status = flagged.
    # -------------------------------------------------------------
    if "R6" in rules and payee_trust_status == "flagged":
        r6_cfg = rules["R6"]
        reasons.append(RiskReasonResult(
            rule_code="R6",
            points=r6_cfg["points"],
            params={"payee_masked": payee_masked}
        ))

    # -------------------------------------------------------------
    # R7: Threshold / repeat pattern
    # amount_paise * 100 >= T_paise * 95 and amount_paise < T_paise for a configured T
    # OR >= 3 identical-amount counted payments to same payee within 24 h including current.
    # Fires once; params list conditions. Round numbers alone never fire.
    # -------------------------------------------------------------
    if "R7" in rules:
        r7_cfg = rules["R7"]
        conditions = []
        matched_threshold = None
        repeat_count = 0

        # Check threshold avoidance
        margin_pct = r7_cfg.get("margin_pct", 95)
        for t_paise in r7_cfg.get("thresholds_paise", [1000000, 5000000, 10000000]):
            if (amount_paise * 100 >= t_paise * margin_pct) and (amount_paise < t_paise):
                conditions.append("near_threshold")
                matched_threshold = t_paise
                break

        # Check repeat pattern (>= 3 identical amounts to same payee within 24h including current)
        repeat_window = r7_cfg.get("repeat_window_seconds", 86400)
        repeat_cutoff = now_utc - timedelta(seconds=repeat_window)
        same_payee_same_amount = 0
        for p in counted_payments:
            if p.get("payee_id") == payee_id and int(p.get("amount_paise", 0)) == amount_paise:
                p_time = p["created_at"]
                if p_time.tzinfo is None:
                    p_time = p_time.replace(tzinfo=timezone.utc)
                if p_time > repeat_cutoff:
                    same_payee_same_amount += 1

        total_same = same_payee_same_amount + 1  # Including current payment
        if total_same >= r7_cfg.get("repeat_count", 3):
            conditions.append("repeat_pattern")
            repeat_count = total_same

        if conditions:
            params_dict: Dict[str, Any] = {"conditions": conditions}
            if matched_threshold is not None:
                params_dict["threshold_paise"] = matched_threshold
            if repeat_count > 0:
                params_dict["repeat_count"] = repeat_count

            reasons.append(RiskReasonResult(
                rule_code="R7",
                points=r7_cfg["points"],
                params=params_dict
            ))

    # -------------------------------------------------------------
    # R8: Scam-language signal
    # Note contains configured phrase (urgent, refund, lottery, KYC update, ...),
    # case-insensitive, whole-word. Fires once.
    # -------------------------------------------------------------
    if "R8" in rules and note:
        r8_cfg = rules["R8"]
        note_lower = note.lower()
        matched_phrase_ids = []

        for phrase in r8_cfg.get("phrases", []):
            phrase_clean = phrase.lower()
            # Whole word / phrase boundary match
            pattern = rf"\b{re.escape(phrase_clean)}\b"
            if re.search(pattern, note_lower):
                matched_phrase_ids.append(phrase_clean)

        if matched_phrase_ids:
            reasons.append(RiskReasonResult(
                rule_code="R8",
                points=r8_cfg["points"],
                params={"phrase_ids": matched_phrase_ids}
            ))

    # -------------------------------------------------------------
    # R9: Drains balance
    # amount_paise * 100 > available_balance_paise * 80 (exactly 80% does not fire).
    # -------------------------------------------------------------
    if "R9" in rules and available_balance_paise > 0:
        r9_cfg = rules["R9"]
        threshold_pct = r9_cfg.get("threshold_pct", 80)
        if amount_paise * 100 > available_balance_paise * threshold_pct:
            share_pct = (amount_paise * 100) // available_balance_paise
            reasons.append(RiskReasonResult(
                rule_code="R9",
                points=r9_cfg["points"],
                params={
                    "amount_paise": amount_paise,
                    "available_paise": available_balance_paise,
                    "share_pct": share_pct
                }
            ))

    # -------------------------------------------------------------
    # R10: Unknown collect request
    # Method is collect_approval and requester trust_status is not known.
    # -------------------------------------------------------------
    if "R10" in rules and method == "collect_approval" and payee_trust_status != "known":
        r10_cfg = rules["R10"]
        reasons.append(RiskReasonResult(
            rule_code="R10",
            points=r10_cfg["points"],
            params={
                "payee_masked": payee_masked,
                "trust_status": payee_trust_status
            }
        ))

    # -------------------------------------------------------------
    # Scoring & Bands
    # -------------------------------------------------------------
    raw_score = sum(r.points for r in reasons)
    score = min(100, raw_score)

    if score <= bands_config["low"][1]:
        band = "low"
    elif score <= bands_config["medium"][1]:
        band = "medium"
    else:
        band = "high"

    return RiskAssessmentResult(
        score=score,
        raw_score=raw_score,
        band=band,
        rules_version=rules_version,
        reasons=reasons,
        features=features
    )
