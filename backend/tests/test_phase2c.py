import os
import sys
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.database import SessionLocal, engine
from app.models.entities import ReviewCase, ReviewCaseAction, Transaction, Payee, User, Alert, AuditLog
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
# 1. RBAC & REVIEW QUEUE TESTS (§6, §12)
# ============================================================================

def test_review_queue_rbac_customer_forbidden():
    token = get_auth_token("rahul_personal")
    res = client.get("/review/cases", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"

def test_review_queue_reviewer_and_supervisor_access():
    reviewer_token = get_auth_token("ananya_reviewer")
    supervisor_token = get_auth_token("vikram_supervisor")

    # Reviewer queue returns seeded cases
    res_rev = client.get("/review/cases", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert res_rev.status_code == 200
    rev_data = res_rev.json()
    assert "items" in rev_data
    assert rev_data["total"] > 0
    # Masked fields present
    first_case = rev_data["items"][0]
    assert first_case["masked_customer_ref"].startswith("CUST-")
    assert "••••" in first_case["masked_payee"]

    # Reviewer cannot see escalated queue
    res_rev_esc = client.get("/review/cases?status=escalated", headers={"Authorization": f"Bearer {reviewer_token}"})
    assert res_rev_esc.status_code == 403
    assert res_rev_esc.json()["error"]["code"] == "FORBIDDEN"

    # Supervisor can see escalated queue
    res_sup_esc = client.get("/review/cases?status=escalated", headers={"Authorization": f"Bearer {supervisor_token}"})
    assert res_sup_esc.status_code == 200


# ============================================================================
# 2. DECISION VALIDATIONS: MANDATORY NOTE, OPTIMISTIC LOCK, SELF-REVIEW (§6, §12)
# ============================================================================

def test_mandatory_note_enforced():
    token = get_auth_token("ananya_reviewer")
    res_cases = client.get("/review/cases", headers={"Authorization": f"Bearer {token}"})
    case = res_cases.json()["items"][0]

    # Note too short (< 5 chars)
    res_short = client.post(
        f"/review/cases/{case['id']}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "approve", "note": "ok", "expected_version": case["version"]}
    )
    assert res_short.status_code == 422
    assert res_short.json()["error"]["code"] in ["VALIDATION_ERROR", "NOTE_REQUIRED"]

    # Note whitespace only
    res_spaces = client.post(
        f"/review/cases/{case['id']}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "approve", "note": "      ", "expected_version": case["version"]}
    )
    assert res_spaces.status_code == 422
    assert res_spaces.json()["error"]["code"] in ["VALIDATION_ERROR", "NOTE_REQUIRED"]

    # Note containing credentials
    res_cred = client.post(
        f"/review/cases/{case['id']}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={"action": "approve", "note": "customer confirmed otp is 592819", "expected_version": case["version"]}
    )
    assert res_cred.status_code == 422
    assert res_cred.json()["error"]["code"] == "CREDENTIAL_INPUT_REJECTED"

def test_optimistic_locking_conflict():
    token = get_auth_token("ananya_reviewer")
    res_cases = client.get("/review/cases", headers={"Authorization": f"Bearer {token}"})
    case = res_cases.json()["items"][0]

    # Send incorrect version
    res_conflict = client.post(
        f"/review/cases/{case['id']}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "approve",
            "note": "Valid justification for approval",
            "expected_version": case["version"] + 99
        }
    )
    assert res_conflict.status_code == 409
    assert res_conflict.json()["error"]["code"] == "CASE_CONFLICT"

def test_reviewer_cannot_act_on_own_payment():
    db = SessionLocal()
    rev_user = db.query(User).filter(User.username == "ananya_reviewer").first()

    # Create a payment and review case owned by the reviewer
    own_tx = Transaction(
        user_id=rev_user.id,
        type="expense",
        source="payment",
        amount_paise=50000,
        category="Shopping",
        method="upi",
        status="held"
    )
    db.add(own_tx)
    db.flush()

    own_case = ReviewCase(
        transaction_id=own_tx.id,
        case_type="hold_review",
        status="open",
        version=1
    )
    db.add(own_case)
    db.commit()
    case_id = own_case.id
    db.close()

    token = get_auth_token("ananya_reviewer")
    res = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "approve",
            "note": "Approving my own payment",
            "expected_version": 1
        }
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "FORBIDDEN"


# ============================================================================
# 3. HOLD REVIEW ACTIONS: APPROVE, REJECT, ESCALATE (§9, §12)
# ============================================================================

def test_hold_review_approve_workflow():
    token = get_auth_token("ananya_reviewer")
    # Get seeded open hold_review case
    res_cases = client.get("/review/cases?case_type=hold_review&status=open", headers={"Authorization": f"Bearer {token}"})
    assert len(res_cases.json()["items"]) > 0
    case = res_cases.json()["items"][0]
    case_id = case["id"]
    tx_id = case["transaction_id"]

    res_approve = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "approve",
            "note": "Verified customer identity and merchant legitimacy.",
            "expected_version": case["version"]
        }
    )
    assert res_approve.status_code == 200
    data = res_approve.json()
    assert data["status"] == "closed"
    assert data["decision"] == "approved"
    assert data["version"] == case["version"] + 1
    assert data["transaction_status"] == "completed"

    # Verify DB state
    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    assert tx.status == "completed"

    # Verify alert created for customer
    alert = db.query(Alert).filter(Alert.user_id == tx.user_id, Alert.type == "review").first()
    assert alert is not None
    assert alert.title_code == "alert.review.approved"
    db.close()

def test_hold_review_reject_workflow():
    token = get_auth_token("ananya_reviewer")
    res_cases = client.get("/review/cases?case_type=hold_review&status=open", headers={"Authorization": f"Bearer {token}"})
    case = res_cases.json()["items"][0]
    case_id = case["id"]
    tx_id = case["transaction_id"]

    res_reject = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "reject",
            "note": "High risk indicators confirmed. Rejecting transaction.",
            "expected_version": case["version"]
        }
    )
    assert res_reject.status_code == 200
    data = res_reject.json()
    assert data["status"] == "closed"
    assert data["decision"] == "rejected"
    assert data["transaction_status"] == "released"

    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    assert tx.status == "released"

    alert = db.query(Alert).filter(Alert.user_id == tx.user_id, Alert.title_code == "alert.review.rejected").first()
    assert alert is not None
    db.close()

def test_escalation_and_two_person_rule():
    rev_token = get_auth_token("ananya_reviewer")
    sup_token = get_auth_token("vikram_supervisor")

    # 1. Ananya (reviewer) escalates an open case
    res_cases = client.get("/review/cases?case_type=hold_review&status=open", headers={"Authorization": f"Bearer {rev_token}"})
    case = res_cases.json()["items"][0]
    case_id = case["id"]

    res_esc = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {rev_token}"},
        json={
            "action": "escalate",
            "note": "Suspicious payee name requires supervisor signoff.",
            "expected_version": case["version"]
        }
    )
    assert res_esc.status_code == 200
    assert res_esc.json()["status"] == "escalated"

    # 2. Ananya (reviewer) cannot resolve the escalated case
    res_rev_try = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {rev_token}"},
        json={
            "action": "approve",
            "note": "Trying to resolve escalated case as reviewer.",
            "expected_version": res_esc.json()["version"]
        }
    )
    assert res_rev_try.status_code == 403
    assert res_rev_try.json()["error"]["code"] == "FORBIDDEN"

    # 3. Vikram (supervisor who did NOT escalate) CAN resolve
    res_sup = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {sup_token}"},
        json={
            "action": "approve",
            "note": "Supervisor reviewed and approved after secondary verification.",
            "expected_version": res_esc.json()["version"]
        }
    )
    assert res_sup.status_code == 200
    assert res_sup.json()["status"] == "closed"
    assert res_sup.json()["decision"] == "approved"

def test_two_person_rule_blocks_self_resolving_supervisor():
    sup_token = get_auth_token("vikram_supervisor")

    res_cases = client.get("/review/cases?case_type=hold_review&status=open", headers={"Authorization": f"Bearer {sup_token}"})
    case = res_cases.json()["items"][0]
    case_id = case["id"]

    # Vikram (supervisor) escalates
    res_esc = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {sup_token}"},
        json={
            "action": "escalate",
            "note": "Escalating for higher tier approval.",
            "expected_version": case["version"]
        }
    )
    assert res_esc.status_code == 200

    # Vikram tries to resolve his OWN escalation -> MUST BE BLOCKED BY TWO-PERSON RULE
    res_resolve = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {sup_token}"},
        json={
            "action": "approve",
            "note": "Resolving my own escalation.",
            "expected_version": res_esc.json()["version"]
        }
    )
    assert res_resolve.status_code == 403
    assert res_resolve.json()["error"]["code"] == "FORBIDDEN"


# ============================================================================
# 4. POST REVIEW & CONFIRMED FRAUD (§12)
# ============================================================================

def test_post_review_confirmed_fraud_flags_payee():
    token = get_auth_token("ananya_reviewer")

    # Get seeded post_review case
    res_cases = client.get("/review/cases?case_type=post_review&status=open", headers={"Authorization": f"Bearer {token}"})
    assert len(res_cases.json()["items"]) > 0
    case = res_cases.json()["items"][0]
    case_id = case["id"]
    tx_id = case["transaction_id"]

    res_fraud = client.post(
        f"/review/cases/{case_id}/decision",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "action": "mark_confirmed_fraud",
            "note": "Pattern matches known phishing scam syndicate.",
            "expected_version": case["version"]
        }
    )
    assert res_fraud.status_code == 200
    assert res_fraud.json()["status"] == "closed"
    assert res_fraud.json()["decision"] == "confirmed_fraud"

    # Verify payee is now flagged
    db = SessionLocal()
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    assert tx.payee.trust_status == "flagged"

    # Verify alert created
    alert = db.query(Alert).filter(Alert.user_id == tx.user_id, Alert.title_code == "alert.fraud.confirmed_fraud").first()
    assert alert is not None
    db.close()


# ============================================================================
# 5. AUDIT LOG & APPEND-ONLY TRIGGERS (§12, §13)
# ============================================================================

def test_review_audit_log_endpoint():
    rev_token = get_auth_token("ananya_reviewer")
    cust_token = get_auth_token("rahul_personal")

    # Customer forbidden
    res_cust = client.get("/review/audit", headers={"Authorization": f"Bearer {cust_token}"})
    assert res_cust.status_code == 403

    # Reviewer gets audit logs with safe metadata
    res_rev = client.get("/review/audit", headers={"Authorization": f"Bearer {rev_token}"})
    assert res_rev.status_code == 200
    data = res_rev.json()
    assert "items" in data
    assert len(data["items"]) > 0
    first_item = data["items"][0]
    assert "actor_username" in first_item
    assert "safe_metadata" in first_item

def test_append_only_triggers_prevent_update_delete():
    from app.config import settings
    url = settings.DATABASE_URL.replace("sqlite:///", "").replace("sqlite://", "")

    conn = sqlite3.connect(url)
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM review_case_actions LIMIT 1")
        row = cursor.fetchone()
        assert row is not None
        action_id = row[0]
        # UPDATE must be aborted by trigger
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError)) as exc_update:
            cursor.execute("UPDATE review_case_actions SET note = 'tampered' WHERE id = ?", (action_id,))
        assert "append-only table" in str(exc_update.value)

        # DELETE must be aborted by trigger
        with pytest.raises((sqlite3.OperationalError, sqlite3.IntegrityError)) as exc_delete:
            cursor.execute("DELETE FROM review_case_actions WHERE id = ?", (action_id,))
        assert "append-only table" in str(exc_delete.value)
    finally:
        conn.close()


# ============================================================================
# 6. CUSTOMER ALERTS ENDPOINTS & IDOR PROTECTION (§14, §6)
# ============================================================================

def test_customer_alerts_read_and_idor_protection():
    priya_token = get_auth_token("priya_personal")
    rahul_token = get_auth_token("rahul_personal")

    # Priya has seeded alerts
    res_alerts = client.get("/alerts", headers={"Authorization": f"Bearer {priya_token}"})
    assert res_alerts.status_code == 200
    alerts = res_alerts.json()["items"]
    assert len(alerts) > 0
    first_alert = alerts[0]
    alert_id = first_alert["id"]

    # Rahul tries to mark Priya's alert as read -> MUST RETURN 404 (IDOR)
    res_idor = client.post(f"/alerts/{alert_id}/read", headers={"Authorization": f"Bearer {rahul_token}"})
    assert res_idor.status_code == 404
    assert res_idor.json()["error"]["code"] == "NOT_FOUND"

    # Priya marks her own alert as read -> SUCCESS
    res_read = client.post(f"/alerts/{alert_id}/read", headers={"Authorization": f"Bearer {priya_token}"})
    assert res_read.status_code == 200
    assert res_read.json()["read_at"] is not None
