import os
import sys
import json
import time
import pytest
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database import engine, SessionLocal
from app.models.entities import Transaction, ReviewCase, Alert, AuditLog, User
from scripts.reset_demo import reset_demo

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_before_tests():
    engine.dispose()
    reset_demo()
    yield
    engine.dispose()

def get_auth_token(username: str) -> str:
    res = client.post("/auth/login", json={"username": username, "password": "password123"})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    return res.json()["access_token"]


# ============================================================================
# 1. DEMO SIMULATOR & RESET TESTS (§16, §20 Phase 2d)
# ============================================================================

def test_demo_scenarios_list():
    res = client.get("/demo/scenarios")
    assert res.status_code == 200
    data = res.json()
    assert "scenarios" in data
    scenarios = data["scenarios"]
    assert len(scenarios) == 5

    scenario_ids = [s["id"] for s in scenarios]
    assert "low_baseline" in scenario_ids
    assert "medium_unusual_amount_new_payee" in scenario_ids
    assert "high_flagged_late_night" in scenario_ids
    assert "high_burst_velocity" in scenario_ids
    assert "high_collect_request" in scenario_ids

    # Validate structure of each scenario
    for s in scenarios:
        assert "id" in s
        assert "fixture" in s
        assert "title" in s
        assert "description" in s
        assert "payload" in s
        payload = s["payload"]
        assert "amount_paise" in payload
        assert "category" in payload
        assert "method" in payload
        assert "payee_display_name" in payload


def test_demo_reset_speed_and_state():
    # Measure reset execution time
    start_time = time.time()
    supervisor_token = get_auth_token('vikram_supervisor')
    res = client.post('/demo/reset', headers={'Authorization': f'Bearer {supervisor_token}'})
    duration = time.time() - start_time

    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "ok"
    assert "duration_seconds" in body
    # Master prompt requirement: Demo reset executes in < 5.0 seconds
    assert duration < 5.0
    assert body["duration_seconds"] < 5.0

    # Verify reconciliation right after reset
    rahul_token = get_auth_token("rahul_personal")
    rec_res = client.get("/accounting/reconciliation", headers={"Authorization": f"Bearer {rahul_token}"})
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["all_passed"] is True
    assert len(rec_data["checks"]) == 4
    for check in rec_data["checks"]:
        assert check["passed"] is True


# ============================================================================
# 2. RISK ASSESSMENT & WHAT-WOULD-CHANGE BREAKDOWN TESTS (§10, §14)
# ============================================================================

def test_risk_assessment_rbac_and_breakdown():
    rahul_token = get_auth_token("rahul_personal")
    priya_token = get_auth_token("priya_personal")
    reviewer_token = get_auth_token("ananya_reviewer")

    # Rahul submits a payment with known parameters
    pay_res = client.post(
        "/payments",
        json={
            "amount_paise": 700000,
            "category": "Shopping",
            "payee_display_name": "Apex Electronic Hub",
            "payee_masked_identifier": "••••7777",
            "method": "upi",
            "note": "Urgent refund processing for gadget purchase",
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "test-risk-breakdown-1"
        }
    )
    assert pay_res.status_code == 200
    tx_id = pay_res.json()["id"]

    # 1. Rahul accesses own risk assessment
    risk_res = client.get(f"/risk/assessments/{tx_id}", headers={"Authorization": f"Bearer {rahul_token}"})
    assert risk_res.status_code == 200
    risk_data = risk_res.json()
    assert risk_data["transaction_id"] == tx_id
    assert risk_data["score"] >= 40  # Medium risk triggered
    assert risk_data["band"] == "medium"
    assert "reasons" in risk_data
    assert len(risk_data["reasons"]) > 0

    # 2. Priya (another customer) is forbidden from viewing Rahul's assessment
    priya_res = client.get(f"/risk/assessments/{tx_id}", headers={"Authorization": f"Bearer {priya_token}"})
    assert priya_res.status_code == 404

    # 3. Reviewer can view Rahul's risk assessment
    rev_res = client.get(f"/risk/assessments/{tx_id}", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert rev_res.status_code == 200

    # 4. Rahul accesses "What would change this score" breakdown
    breakdown_res = client.get(f"/risk/assessments/{tx_id}/breakdown", headers={"Authorization": f"Bearer {rahul_token}"})
    assert breakdown_res.status_code == 200
    breakdown = breakdown_res.json()
    assert "score" in breakdown
    assert "band" in breakdown
    assert "fired_reasons" in breakdown
    assert "what_would_change" in breakdown
    assert len(breakdown["what_would_change"]) > 0
    factors = [f["factor"] for f in breakdown["what_would_change"]]
    assert any(factor in ["amount", "payee", "time", "note"] for factor in factors)


# ============================================================================
# 3. END-TO-END FLOW: LOW RISK PAYMENT (IMMEDIATE COMPLETION)
# ============================================================================

def test_e2e_low_risk_flow():
    rahul_token = get_auth_token("rahul_personal")

    # Get initial balance
    bal_res_0 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"})
    bal_0 = bal_res_0.json()

    # Submit Low-risk payment (₹800 to known groceries payee)
    pay_res = client.post(
        "/payments",
        json={
            "amount_paise": 80000,
            "category": "Groceries",
            "payee_display_name": "Fresh Mart Groceries",
            "payee_masked_identifier": "••••1029",
            "method": "upi",
            "note": "Weekly groceries supplies",
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "e2e-low-risk-001"
        }
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    tx_id = pay_data["id"]
    assert pay_data["status"] == "completed"
    assert pay_data["assessment"]["band"] == "low"
    assert pay_data["assessment"]["score"] < 40

    # Balance check
    bal_res_1 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"})
    bal_1 = bal_res_1.json()
    assert bal_1["available_balance_paise"] == bal_0["available_balance_paise"] - 80000
    assert bal_1["completed_expenses_paise"] == bal_0["completed_expenses_paise"] + 80000
    assert bal_1["held_balance_paise"] == bal_0["held_balance_paise"]

    # Transaction details check
    tx_res = client.get(f"/transactions/{tx_id}", headers={"Authorization": f"Bearer {rahul_token}"})
    assert tx_res.status_code == 200
    tx_data = tx_res.json()
    assert tx_data["status"] == "completed"
    assert tx_data["amount_paise"] == 80000


# ============================================================================
# 4. END-TO-END FLOW: MEDIUM RISK PAYMENT (CONFIRM & CANCEL)
# ============================================================================

def test_e2e_medium_risk_confirm_flow():
    rahul_token = get_auth_token("rahul_personal")

    # Submit payment triggering Medium risk
    pay_res = client.post(
        "/payments",
        json={
            "amount_paise": 700000,
            "category": "Shopping",
            "payee_display_name": "Apex Electronic Hub",
            "payee_masked_identifier": "••••7777",
            "method": "upi",
            "note": "Urgent refund processing for gadget purchase",
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "e2e-med-confirm-001"
        }
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    tx_id = pay_data["id"]
    assert pay_data["status"] == "awaiting_confirmation"
    assert pay_data["assessment"]["band"] == "medium"

    # Customer confirms payment
    conf_res = client.post(f"/payments/{tx_id}/confirm", headers={"Authorization": f"Bearer {rahul_token}"})
    assert conf_res.status_code == 200
    assert conf_res.json()["status"] == "completed"

    # Post-review case must be created in review queue
    db = SessionLocal()
    post_review = db.query(ReviewCase).filter(
        ReviewCase.transaction_id == tx_id,
        ReviewCase.case_type == "post_review"
    ).first()
    assert post_review is not None
    assert post_review.status == "open"
    db.close()


def test_e2e_medium_risk_cancel_flow():
    rahul_token = get_auth_token("rahul_personal")
    bal_0 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()

    # Submit Medium risk payment
    pay_res = client.post(
        "/payments",
        json={
            "amount_paise": 700000,
            "category": "Shopping",
            "payee_display_name": "Apex Electronic Hub",
            "payee_masked_identifier": "••••7777",
            "method": "upi",
            "note": "Urgent refund processing for gadget purchase",
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "e2e-med-cancel-001"
        }
    )
    assert pay_res.status_code == 200
    tx_id = pay_res.json()["id"]

    # Customer cancels payment
    cancel_res = client.post(f"/payments/{tx_id}/cancel", headers={"Authorization": f"Bearer {rahul_token}"})
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Balances must be untouched
    bal_1 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert bal_1["available_balance_paise"] == bal_0["available_balance_paise"]
    assert bal_1["completed_expenses_paise"] == bal_0["completed_expenses_paise"]
    assert bal_1["held_balance_paise"] == bal_0["held_balance_paise"]


# ============================================================================
# 5. END-TO-END FLOW: HIGH RISK PAYMENT (HOLD -> REVIEWER APPROVE / REJECT)
# ============================================================================

def test_e2e_high_risk_hold_and_reviewer_approve():
    rahul_token = get_auth_token("rahul_personal")
    reviewer_token = get_auth_token("ananya_reviewer")

    bal_0 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()

    # Submit High risk payment (Score >= 70)
    pay_res = client.post(
        "/payments",
        json={
            "amount_paise": 400000,
            "category": "Utilities",
            "payee_display_name": "Suspicious Tele-Services",
            "payee_masked_identifier": "••••9941",
            "method": "upi",
            "note": "Urgent electricity bill clearance",
            "simulated_at": "2026-11-21T02:30:00+05:30",
            "synthetic_device_tag": "D9",
            "synthetic_city_tag": "Delhi"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "e2e-high-approve-001"
        }
    )
    assert pay_res.status_code == 200
    pay_data = pay_res.json()
    tx_id = pay_data["id"]
    assert pay_data["status"] == "held"
    assert pay_data["assessment"]["band"] == "high"
    assert pay_data["assessment"]["score"] >= 70

    # Check that funds are reserved in held balance
    bal_1 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert bal_1["held_balance_paise"] == bal_0["held_balance_paise"] + 400000
    assert bal_1["available_balance_paise"] == bal_0["available_balance_paise"] - 400000

    # Reviewer finds case in review queue
    db = SessionLocal()
    case = db.query(ReviewCase).filter(
        ReviewCase.transaction_id == tx_id,
        ReviewCase.case_type == "hold_review"
    ).first()
    assert case is not None
    case_id = case.id
    db.close()

    case_res = client.get(f"/review/cases/{case_id}", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert case_res.status_code == 200
    case_detail = case_res.json()
    assert case_detail["status"] == "open"

    # Reviewer approves with valid note (5-500 chars)
    dec_res = client.post(
        f"/review/cases/{case_id}/decision",
        json={
            "action": "approve",
            "note": "Verified genuine utility bill payment with customer confirmation via telephone",
            "expected_version": case_detail["version"]
        },
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert dec_res.status_code == 200
    assert dec_res.json()["status"] == "closed"
    assert dec_res.json()["decision"] == "approved"

    # Transaction status must now be completed
    tx_check = client.get(f"/transactions/{tx_id}", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert tx_check["status"] == "completed"

    # Balances: held returns to 0, completed reflects payment
    bal_2 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert bal_2["held_balance_paise"] == bal_0["held_balance_paise"]
    assert bal_2["completed_expenses_paise"] == bal_0["completed_expenses_paise"] + 400000

    # Customer received notification alert
    alert_res = client.get("/alerts", headers={"Authorization": f"Bearer {rahul_token}"})
    assert alert_res.status_code == 200
    alerts = alert_res.json()["items"]
    assert any(a["title_code"] == "alert.review.approved" for a in alerts)


def test_e2e_high_risk_hold_and_reviewer_reject():
    rahul_token = get_auth_token("rahul_personal")
    reviewer_token = get_auth_token("ananya_reviewer")

    bal_0 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()

    # Submit High risk payment
    pay_res = client.post(
        "/payments",
        json={
            "amount_paise": 400000,
            "category": "Utilities",
            "payee_display_name": "Suspicious Tele-Services",
            "payee_masked_identifier": "••••9941",
            "method": "upi",
            "note": "Urgent electricity bill clearance",
            "simulated_at": "2026-11-21T02:30:00+05:30",
            "synthetic_device_tag": "D9",
            "synthetic_city_tag": "Delhi"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "e2e-high-reject-001"
        }
    )
    assert pay_res.status_code == 200
    tx_id = pay_res.json()["id"]

    db = SessionLocal()
    case = db.query(ReviewCase).filter(ReviewCase.transaction_id == tx_id).first()
    case_id = case.id
    db.close()

    # Reviewer rejects case
    dec_res = client.post(
        f"/review/cases/{case_id}/decision",
        json={
            "action": "reject",
            "note": "Confirmed utility fraud impersonation campaign, blocking transaction",
            "expected_version": 1
        },
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert dec_res.status_code == 200

    # Transaction transitions to released
    tx_check = client.get(f"/transactions/{tx_id}", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert tx_check["status"] == "released"

    # Held funds are completely returned to available
    bal_2 = client.get("/accounting/summary", headers={"Authorization": f"Bearer {rahul_token}"}).json()
    assert bal_2["held_balance_paise"] == bal_0["held_balance_paise"]
    assert bal_2["available_balance_paise"] == bal_0["available_balance_paise"]
    assert bal_2["completed_expenses_paise"] == bal_0["completed_expenses_paise"]

    # Customer received notification alert
    alert_res = client.get("/alerts", headers={"Authorization": f"Bearer {rahul_token}"})
    alerts = alert_res.json()["items"]
    assert any(a["title_code"] == "alert.review.rejected" for a in alerts)


# ============================================================================
# 6. END-TO-END FLOW: ESCALATION & SUPERVISOR RESOLUTION
# ============================================================================

def test_e2e_escalate_and_supervisor_resolve():
    rahul_token = get_auth_token("rahul_personal")
    reviewer_token = get_auth_token("ananya_reviewer")
    supervisor_token = get_auth_token("vikram_supervisor")

    # Submit High risk payment
    pay_res = client.post(
        "/payments",
        json={
            "amount_paise": 400000,
            "category": "Utilities",
            "payee_display_name": "Suspicious Tele-Services",
            "payee_masked_identifier": "••••9941",
            "method": "upi",
            "note": "Urgent electricity bill clearance",
            "simulated_at": "2026-11-21T02:30:00+05:30",
            "synthetic_device_tag": "D9",
            "synthetic_city_tag": "Delhi"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "e2e-escalate-001"
        }
    )
    tx_id = pay_res.json()["id"]

    db = SessionLocal()
    case = db.query(ReviewCase).filter(ReviewCase.transaction_id == tx_id).first()
    case_id = case.id
    db.close()

    # Reviewer escalates case
    esc_res = client.post(
        f"/review/cases/{case_id}/decision",
        json={
            "action": "escalate",
            "note": "Unusual pattern requires supervisor verification and clearance",
            "expected_version": 1
        },
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert esc_res.status_code == 200
    assert esc_res.json()["status"] == "escalated"

    # Reviewer cannot resolve escalated case (must be supervisor)
    unauth_res = client.post(
        f"/review/cases/{case_id}/decision",
        json={
            "action": "approve",
            "note": "Attempting unauthorized resolution by reviewer",
            "expected_version": 2
        },
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert unauth_res.status_code == 403

    # Supervisor resolves escalation
    sup_res = client.post(
        f"/review/cases/{case_id}/decision",
        json={
            "action": "approve",
            "note": "Supervisor cleared after cross-referencing customer security profile",
            "expected_version": 2
        },
        headers={"Authorization": f"Bearer {supervisor_token}"}
    )
    assert sup_res.status_code == 200
    assert sup_res.json()["status"] == "closed"
    assert sup_res.json()["decision"] == "approved"

    # Audit log contains complete timeline
    audit_res = client.get("/review/audit", headers={"Authorization": f"Bearer {supervisor_token}"})
    assert audit_res.status_code == 200
    entries = audit_res.json()["items"]
    case_events = [e for e in entries if e["entity_id"] == case_id]
    assert len(case_events) >= 2


# ============================================================================
# 7. CREDENTIAL GUARD VALIDATION (§11)
# ============================================================================

def test_credential_guard_blocks_payment_payload():
    rahul_token = get_auth_token("rahul_personal")

    # Payment payload with a 16-digit card number in note
    bad_res = client.post(
        "/payments",
        json={
            "amount_paise": 100000,
            "category": "Shopping",
            "payee_display_name": "Merchant",
            "payee_masked_identifier": "••••1111",
            "method": "upi",
            "note": "Payment using card 4532015112830366 expiry 12/28",
            "synthetic_device_tag": "D1",
            "synthetic_city_tag": "Bengaluru"
        },
        headers={
            "Authorization": f"Bearer {rahul_token}",
            "Idempotency-Key": "cred-guard-test-01"
        }
    )
    assert bad_res.status_code == 422
    err = bad_res.json()["error"]
    assert err["code"] == "CREDENTIAL_INPUT_REJECTED"
