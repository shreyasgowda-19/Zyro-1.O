import json
import os
from datetime import datetime, timezone, timedelta
import pytz
import pytest

from app.services.risk_engine import evaluate_risk, RiskAssessmentResult
from app.config import BASE_DIR, settings

IST = pytz.timezone("Asia/Kolkata")

@pytest.fixture
def rules_config():
    rules_path = os.path.join(BASE_DIR, settings.RULES_CONFIG_PATH)
    with open(rules_path, "r", encoding="utf-8") as f:
        return json.load(f)

def make_baseline_b(now_utc: datetime):
    """
    Baseline B (§10):
    - personal user
    - exactly 10 completed expenses of ₹1,000 each (sum ₹10,000) within last 30 days
    - >= 1 prior payment with device D1 and city C1
    - available balance ₹50,000 (5,000,000 paise)
    - 14:00 IST
    - method 'upi'
    - amount ₹1,000 (100,000 paise)
    - known payee
    - no note
    """
    completed_expenses = [
        {"amount_paise": 100000, "created_at": now_utc - timedelta(days=i + 1)}
        for i in range(10)
    ]
    counted_payments = [
        {
            "payee_id": 1,
            "amount_paise": 100000,
            "created_at": now_utc - timedelta(days=i + 1),
            "device_tag": "D1",
            "city_tag": "C1"
        }
        for i in range(10)
    ]

    context = {
        "completed_expenses": completed_expenses,
        "counted_payments": counted_payments,
        "tag_history_devices": ["D1"],
        "tag_history_cities": ["C1"],
        "available_balance_paise": 5000000,  # ₹50,000
        "payee_trust_status": "known",
        "profile_type": "personal",
        "is_new_payee": False
    }

    payment = {
        "amount_paise": 100000,  # ₹1,000
        "payee_id": 1,
        "payee_masked": "••••1234",
        "method": "upi",
        "note": "",
        "synthetic_device_tag": "D1",
        "synthetic_city_tag": "C1"
    }

    return context, payment

def get_time_at_ist(hour: int, minute: int) -> datetime:
    dt = datetime(2026, 11, 21, hour, minute, 0)
    return IST.localize(dt).astimezone(timezone.utc)


# ============================================================================
# REQUIRED FIXTURES F1 - F11 (§10)
# ============================================================================

def test_f1_baseline(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 0
    assert res.band == "low"
    assert len(res.reasons) == 0

def test_f2_new_payee_unusual_amount(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    ctx["is_new_payee"] = True
    pay["amount_paise"] = 350000
    pay["payee_id"] = 999

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 40
    assert res.band == "medium"
    assert len(res.reasons) == 2
    rule_codes = {r.rule_code for r in res.reasons}
    assert rule_codes == {"R1", "R2"}

def test_f3_flagged_payee_unusual_amount_unusual_hour(rules_config):
    now = get_time_at_ist(2, 30)
    ctx, pay = make_baseline_b(now)
    ctx["payee_trust_status"] = "flagged"
    ctx["is_new_payee"] = False
    pay["amount_paise"] = 400000

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 75
    assert res.band == "high"
    assert len(res.reasons) == 3
    rule_codes = {r.rule_code for r in res.reasons}
    assert rule_codes == {"R6", "R1", "R3"}

def test_f4_velocity_burst(rules_config):
    t0 = get_time_at_ist(14, 0)
    ctx, _ = make_baseline_b(t0)

    # First payment: ₹250 at t0
    pay1 = {
        "amount_paise": 25000,
        "payee_id": 1,
        "payee_masked": "••••1234",
        "method": "upi",
        "synthetic_device_tag": "D1",
        "synthetic_city_tag": "C1"
    }
    res1 = evaluate_risk(ctx, pay1, rules_config, t0)
    assert res1.score == 0

    # Second payment: ₹310 at t0 + 120s
    t1 = t0 + timedelta(seconds=120)
    ctx["counted_payments"].append({"amount_paise": 25000, "payee_id": 1, "created_at": t0})
    pay2 = {
        "amount_paise": 31000,
        "payee_id": 1,
        "payee_masked": "••••1234",
        "method": "upi",
        "synthetic_device_tag": "D1",
        "synthetic_city_tag": "C1"
    }
    res2 = evaluate_risk(ctx, pay2, rules_config, t1)
    assert res2.score == 0

    # Third payment: ₹275 to new payee at t0 + 239s
    t2 = t0 + timedelta(seconds=239)
    ctx["counted_payments"].append({"amount_paise": 31000, "payee_id": 1, "created_at": t1})
    ctx["is_new_payee"] = True
    pay3 = {
        "amount_paise": 27500,
        "payee_id": 999,
        "payee_masked": "••••9999",
        "method": "upi",
        "synthetic_device_tag": "D1",
        "synthetic_city_tag": "C1"
    }
    res3 = evaluate_risk(ctx, pay3, rules_config, t2)
    assert res3.score == 40
    assert res3.band == "medium"
    assert {r.rule_code for r in res3.reasons} == {"R4", "R2"}

def test_f5_collect_approval_unknown_requester_scam_note(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    ctx["is_new_payee"] = True
    ctx["payee_trust_status"] = "new"
    pay["method"] = "collect_approval"
    pay["note"] = "Please complete KYC update immediately"

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 60
    assert res.band == "medium"
    assert {r.rule_code for r in res.reasons} == {"R2", "R10", "R8"}

def test_f6_f5_at_unusual_hour(rules_config):
    now = get_time_at_ist(2, 30)
    ctx, pay = make_baseline_b(now)
    ctx["is_new_payee"] = True
    ctx["payee_trust_status"] = "new"
    pay["method"] = "collect_approval"
    pay["note"] = "Please complete KYC update immediately"

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 70
    assert res.band == "high"
    assert {r.rule_code for r in res.reasons} == {"R2", "R10", "R8", "R3"}

def test_f7_new_payee_alone_informational(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    ctx["is_new_payee"] = True
    pay["payee_id"] = 888

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 15
    assert res.band == "low"
    assert len(res.reasons) == 1
    assert res.reasons[0].rule_code == "R2"

def test_f8_scam_note_alone(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    pay["note"] = "urgent refund of taxes"

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 15
    assert res.band == "low"
    assert len(res.reasons) == 1
    assert res.reasons[0].rule_code == "R8"

def test_f9_unseen_device_and_city(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    pay["synthetic_device_tag"] = "D2"
    pay["synthetic_city_tag"] = "C2"

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 15
    assert res.band == "low"
    assert len(res.reasons) == 1
    assert res.reasons[0].rule_code == "R5"
    assert set(res.reasons[0].params["signals"]) == {"device", "city"}

def test_f10_constructed_context_capped_at_100(rules_config):
    now = get_time_at_ist(2, 30)
    ctx, pay = make_baseline_b(now)
    ctx["payee_trust_status"] = "flagged"
    ctx["is_new_payee"] = True
    ctx["available_balance_paise"] = 5000000
    ctx["counted_payments"] = [
        {"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=100)},
        {"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=200)},
    ]

    pay["method"] = "collect_approval"
    pay["amount_paise"] = 4900000
    pay["note"] = "urgent KYC update"
    pay["synthetic_device_tag"] = "D_NEW"
    pay["synthetic_city_tag"] = "C_NEW"

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.raw_score >= 180
    assert res.score == 100
    assert res.band == "high"

def test_f11_cold_start_user(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    ctx["completed_expenses"] = [
        {"amount_paise": 100000, "created_at": now - timedelta(days=1)},
        {"amount_paise": 100000, "created_at": now - timedelta(days=2)},
    ]
    ctx["is_new_payee"] = True
    pay["amount_paise"] = 500000
    pay["synthetic_device_tag"] = "D_NEW"

    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 7
    assert res.band == "low"
    assert len(res.reasons) == 1
    assert res.reasons[0].rule_code == "R2"
    assert res.reasons[0].points == 7
    assert res.reasons[0].params["cold_start"] is True


# ============================================================================
# BOUNDARY & PROPERTY TESTS (§10)
# ============================================================================

def test_r1_boundaries(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)

    pay["amount_paise"] = 300000
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert not any(r.rule_code == "R1" for r in res.reasons)

    pay["amount_paise"] = 300100
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert any(r.rule_code == "R1" for r in res.reasons)

    ctx["completed_expenses"] = ctx["completed_expenses"][:4]
    pay["amount_paise"] = 1000000
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert not any(r.rule_code == "R1" for r in res.reasons)

def test_r3_hour_boundaries(rules_config):
    ctx, pay = make_baseline_b(get_time_at_ist(14, 0))

    # 00:00 IST -> fires
    t_0000 = get_time_at_ist(0, 0)
    res = evaluate_risk(ctx, pay, rules_config, t_0000)
    assert any(r.rule_code == "R3" for r in res.reasons)

    # 04:59 IST -> fires
    t_0459 = get_time_at_ist(4, 59)
    res = evaluate_risk(ctx, pay, rules_config, t_0459)
    assert any(r.rule_code == "R3" for r in res.reasons)

    # 05:00 IST -> does NOT fire
    t_0500 = get_time_at_ist(5, 0)
    res = evaluate_risk(ctx, pay, rules_config, t_0500)
    assert not any(r.rule_code == "R3" for r in res.reasons)

    # 23:59 IST -> does NOT fire
    t_2359 = get_time_at_ist(23, 59)
    res = evaluate_risk(ctx, pay, rules_config, t_2359)
    assert not any(r.rule_code == "R3" for r in res.reasons)

def test_r4_velocity_boundaries(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)

    ctx["counted_payments"] = [
        {"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=299)},
        {"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=150)},
    ]
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert any(r.rule_code == "R4" for r in res.reasons)

    ctx["counted_payments"] = [
        {"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=301)},
        {"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=150)},
    ]
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert not any(r.rule_code == "R4" for r in res.reasons)

    ctx["profile_type"] = "business"
    ctx["counted_payments"] = [
        {"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=100)}
        for _ in range(6)
    ]
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert not any(r.rule_code == "R4" for r in res.reasons)

    ctx["counted_payments"].append({"amount_paise": 100000, "payee_id": 1, "created_at": now - timedelta(seconds=50)})
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert any(r.rule_code == "R4" for r in res.reasons)

def test_r7_threshold_and_repeat_boundaries(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)

    pay["amount_paise"] = 949999
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert not any(r.rule_code == "R7" for r in res.reasons)

    pay["amount_paise"] = 950000
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert any(r.rule_code == "R7" for r in res.reasons)

    pay["amount_paise"] = 999999
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert any(r.rule_code == "R7" for r in res.reasons)

    pay["amount_paise"] = 1000000
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert not any(r.rule_code == "R7" for r in res.reasons)

    pay["amount_paise"] = 123400
    ctx["counted_payments"] = [
        {"amount_paise": 123400, "payee_id": pay["payee_id"], "created_at": now - timedelta(hours=2)},
        {"amount_paise": 123400, "payee_id": pay["payee_id"], "created_at": now - timedelta(hours=5)},
    ]
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert any(r.rule_code == "R7" for r in res.reasons)
    r7_reason = next(r for r in res.reasons if r.rule_code == "R7")
    assert "repeat_pattern" in r7_reason.params["conditions"]

def test_r9_drains_balance_boundaries(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    ctx["available_balance_paise"] = 1000000

    pay["amount_paise"] = 800000
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert not any(r.rule_code == "R9" for r in res.reasons)

    pay["amount_paise"] = 800001
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert any(r.rule_code == "R9" for r in res.reasons)

def test_property_determinism_and_order_independence(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    pay["amount_paise"] = 350000
    ctx["is_new_payee"] = True

    res1 = evaluate_risk(ctx, pay, rules_config, now)
    res2 = evaluate_risk(ctx, pay, rules_config, now)

    assert res1.score == res2.score
    assert res1.band == res2.band
    assert len(res1.reasons) == len(res2.reasons)

    import random
    shuffled_ctx = dict(ctx)
    shuffled_expenses = list(ctx["completed_expenses"])
    random.shuffle(shuffled_expenses)
    shuffled_ctx["completed_expenses"] = shuffled_expenses

    res3 = evaluate_risk(shuffled_ctx, pay, rules_config, now)
    assert res3.score == res1.score
    assert res3.band == res1.band

def test_property_band_boundaries(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)

    res_low = evaluate_risk(ctx, pay, rules_config, now)
    assert res_low.score <= 39
    assert res_low.band == "low"

def test_coverage_to_dict_and_medium_band(rules_config):
    now = get_time_at_ist(14, 0)
    ctx, pay = make_baseline_b(now)
    # Give a score of 50 (medium band)
    ctx["is_new_payee"] = True
    pay["amount_paise"] = 350000
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.band == "medium"
    d = res.to_dict()
    assert "score" in d
    assert "reasons" in d
    assert len(d["reasons"]) > 0
    assert "rule_code" in d["reasons"][0]

def test_timezone_naive_in_history(rules_config):
    now = datetime(2026, 11, 21, 14, 0, 0)
    ctx, pay = make_baseline_b(now)
    # Naive counted payment
    ctx["counted_payments"] = [
        {"amount_paise": 100000, "payee_id": 1, "created_at": datetime(2026, 11, 21, 13, 59, 0)}
    ]
    res = evaluate_risk(ctx, pay, rules_config, now)
    assert res.score == 0
