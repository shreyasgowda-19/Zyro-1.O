import os
import sys
import json
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.main import app
from app.services.credential_guard import validate_sensitive_input, normalize_text, luhn_checksum
from app.services.accounting_service import run_reconciliation
from app.database import SessionLocal
from app.errors import AppError
from scripts.reset_demo import reset_demo

client = TestClient(app)

@pytest.fixture(autouse=True)
def reset_db_before_tests():
    from app.database import engine
    engine.dispose()
    reset_demo()
    yield
    engine.dispose()

def get_auth_token(username: str = "rahul_personal") -> str:
    res = client.post("/auth/login", json={"username": username, "password": "password123"})
    assert res.status_code == 200
    return res.json()["access_token"]


# ============================================================================
# 1. CREDENTIAL & SENSITIVE INPUT GUARD TESTS (§11)
# ============================================================================

def test_credential_otp_rejected():
    with pytest.raises(AppError) as exc:
        validate_sensitive_input("my otp is 482913", "note")
    assert exc.value.code == "CREDENTIAL_INPUT_REJECTED"

def test_credential_pin_rejected():
    with pytest.raises(AppError) as exc:
        validate_sensitive_input("pin 1234 for upi", "note")
    assert exc.value.code == "CREDENTIAL_INPUT_REJECTED"

def test_credential_standalone_digits_rejected():
    with pytest.raises(AppError) as exc:
        validate_sensitive_input("123456", "note")
    assert exc.value.code == "CREDENTIAL_INPUT_REJECTED"

def test_credential_luhn_card_rejected():
    with pytest.raises(AppError) as exc:
        validate_sensitive_input("Card: 4111 1111 1111 1111 payment", "note")
    assert exc.value.code == "CREDENTIAL_INPUT_REJECTED"

def test_script_text_rejected():
    with pytest.raises(AppError) as exc:
        validate_sensitive_input("<script>alert(1)</script>", "note")
    assert exc.value.code == "INVALID_TEXT"

def test_legitimate_texts_accepted():
    assert validate_sensitive_input("rent 15000", "note") == "rent 15000"
    assert validate_sensitive_input("Invoice 2024-118", "note") == "Invoice 2024-118"
    assert validate_sensitive_input("pin code 560001 area", "note") == "pin code 560001 area"

def test_normalization_devanagari_digits():
    with pytest.raises(AppError) as exc:
        validate_sensitive_input("mera pin १२३४ hai", "note")
    assert exc.value.code == "CREDENTIAL_INPUT_REJECTED"

def test_api_credential_rejection_never_echoes_input():
    token = get_auth_token("rahul_personal")
    sensitive_val = "secret otp 987654"
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test_cred_strip"},
        json={
            "amount_paise": 50000,
            "category": "Shopping",
            "method": "upi",
            "note": sensitive_val
        }
    )
    assert res.status_code == 422
    err_json_str = json.dumps(res.json())
    assert sensitive_val not in err_json_str
    assert "987654" not in err_json_str


# ============================================================================
# 2. PAYMENT LIFECYCLE & TRANSITIONS (§8, §9)
# ============================================================================

def test_payment_low_completes():
    token = get_auth_token("rahul_personal")
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test_low_p1"},
        json={
            "amount_paise": 100000,
            "category": "Groceries",
            "payee_display_name": "Airtel Broadband",
            "payee_masked_identifier": "••••8891",
            "method": "upi",
            "note": "Broadband bill"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "completed"
    assert data["assessment"]["score"] <= 39
    assert data["assessment"]["band"] == "low"

def test_payment_medium_awaits_confirmation_and_confirms():
    token = get_auth_token("rahul_personal")
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test_med_p1"},
        json={
            "amount_paise": 700000,
            "category": "Shopping",
            "payee_display_name": "Brand New Merchant",
            "payee_masked_identifier": "••••7777",
            "method": "upi",
            "note": "Urgent refund processing"
        }
    )
    assert res.status_code == 200
    data = res.json()
    payment_id = data["id"]
    assert data["status"] == "awaiting_confirmation"
    assert data["assessment"]["band"] == "medium"
    assert data["assessment"]["score"] >= 40

    confirm_res = client.post(
        f"/payments/{payment_id}/confirm",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert confirm_res.status_code == 200
    assert confirm_res.json()["status"] == "completed"

    get_res = client.get(f"/payments/{payment_id}", headers={"Authorization": f"Bearer {token}"})
    assert get_res.json()["status"] == "completed"

def test_payment_medium_cancellation():
    token = get_auth_token("rahul_personal")
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test_med_cancel"},
        json={
            "amount_paise": 700000,
            "category": "Shopping",
            "payee_display_name": "Brand New Merchant",
            "payee_masked_identifier": "••••4321",
            "method": "upi",
            "note": "Urgent prize claim"
        }
    )
    payment_id = res.json()["id"]
    assert res.json()["status"] == "awaiting_confirmation"

    cancel_res = client.post(
        f"/payments/{payment_id}/cancel",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    re_confirm = client.post(
        f"/payments/{payment_id}/confirm",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert re_confirm.status_code == 400
    assert re_confirm.json()["error"]["code"] == "ILLEGAL_TRANSITION"

def test_payment_high_is_held_and_reserves_funds():
    token = get_auth_token("rahul_personal")
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test_high_hold"},
        json={
            "amount_paise": 400000,
            "category": "Utilities",
            "payee_display_name": "Suspicious Tele-Services",
            "payee_masked_identifier": "••••9941",
            "method": "upi",
            "note": "Urgent electricity bill",
            "simulated_at": "2026-11-21T02:30:00+05:30"
        }
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "held"
    assert data["assessment"]["score"] >= 70
    assert data["assessment"]["band"] == "high"

    bal_res = client.get("/accounting/summary", headers={"Authorization": f"Bearer {token}"})
    balances = bal_res.json()
    assert balances["held_balance_paise"] >= 400000
    assert balances["available_balance_paise"] == balances["completed_balance_paise"] - balances["held_balance_paise"]


# ============================================================================
# 3. ACCOUNTING & INSUFFICIENT FUNDS (§8)
# ============================================================================

def test_insufficient_funds_rejected_before_scoring():
    token = get_auth_token("priya_personal")
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test_insufficient"},
        json={
            "amount_paise": 4000000,
            "category": "General",
            "method": "upi"
        }
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "INSUFFICIENT_FUNDS"

def test_strict_int_paise_rejects_floats():
    token = get_auth_token("rahul_personal")
    res = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {token}", "Idempotency-Key": "test_float"},
        json={
            "amount_paise": 100.50,
            "category": "General",
            "method": "upi"
        }
    )
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "VALIDATION_ERROR"

def test_reconciliation_endpoint():
    token = get_auth_token("rahul_personal")
    res = client.get("/accounting/reconciliation", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["all_passed"] is True
    assert len(data["checks"]) == 4
    for check in data["checks"]:
        assert check["passed"] is True


# ============================================================================
# 4. IDEMPOTENCY (§9)
# ============================================================================

def test_idempotency_replay_and_conflict():
    token = get_auth_token("rahul_personal")
    key = "unique-key-xyz-12345"
    payload1 = {
        "amount_paise": 25000,
        "category": "Groceries",
        "method": "upi"
    }

    res1 = client.post("/payments", headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key}, json=payload1)
    assert res1.status_code == 200
    tx1_id = res1.json()["id"]

    res2 = client.post("/payments", headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key}, json=payload1)
    assert res2.status_code == 200
    assert res2.json()["id"] == tx1_id

    payload2 = {
        "amount_paise": 50000,
        "category": "Shopping",
        "method": "upi"
    }
    res3 = client.post("/payments", headers={"Authorization": f"Bearer {token}", "Idempotency-Key": key}, json=payload2)
    assert res3.status_code == 409
    assert res3.json()["error"]["code"] == "IDEMPOTENCY_CONFLICT"


# ============================================================================
# 5. CROSS-CUSTOMER IDOR PROTECTION (§6)
# ============================================================================

def test_cross_customer_idor_prevention():
    rahul_token = get_auth_token("rahul_personal")
    priya_token = get_auth_token("priya_personal")

    res_rahul = client.post(
        "/payments",
        headers={"Authorization": f"Bearer {rahul_token}", "Idempotency-Key": "rahul_payment_idor"},
        json={"amount_paise": 15000, "category": "Food", "method": "upi"}
    )
    rahul_tx_id = res_rahul.json()["id"]

    res_priya = client.get(
        f"/payments/{rahul_tx_id}",
        headers={"Authorization": f"Bearer {priya_token}"}
    )
    assert res_priya.status_code == 404
    assert res_priya.json()["error"]["code"] == "NOT_FOUND"

    res_priya_confirm = client.post(
        f"/payments/{rahul_tx_id}/confirm",
        headers={"Authorization": f"Bearer {priya_token}"}
    )
    assert res_priya_confirm.status_code == 404
