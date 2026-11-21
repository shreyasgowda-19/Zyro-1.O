import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.entities import User, Transaction, RiskAssessment, RiskReason

client = TestClient(app)

def get_auth_token(username: str, role: str) -> str:
    res = client.post("/auth/login", json={"username": username, "password": "password123"})
    assert res.status_code == 200, f"Login failed for {username}: {res.text}"
    return res.json()["access_token"]

def test_guidance_endpoints():
    token = get_auth_token("rahul_personal", "customer")
    headers = {"Authorization": f"Bearer {token}"}

    # Test English guidance
    res_en = client.get("/guidance?lang=en", headers=headers)
    assert res_en.status_code == 200
    items_en = res_en.json()
    assert isinstance(items_en, list)
    assert len(items_en) >= 3
    topics = [item["topic"] for item in items_en]
    assert "helpline" in topics
    assert "sanchar_saathi" in topics
    assert "qr_code_scams" in topics
    for item in items_en:
        assert item["language"] == "en"
        assert item["source_label"] is not None
        assert item["last_verified"] is not None

    # Test Hindi guidance
    res_hi = client.get("/guidance?lang=hi", headers=headers)
    assert res_hi.status_code == 200
    items_hi = res_hi.json()
    assert isinstance(items_hi, list)
    assert len(items_hi) >= 3
    for item in items_hi:
        assert item["language"] == "hi"
        assert item["source_label"] is not None

    # Test invalid language param
    res_invalid = client.get("/guidance?lang=fr", headers=headers)
    assert res_invalid.status_code == 422

def test_scam_checker_clean_message():
    token = get_auth_token("rahul_personal", "customer")
    headers = {"Authorization": f"Bearer {token}"}

    payload = {"message": "Meeting you at Bangalore office at 5 PM for coffee"}
    res = client.post("/guidance/scam-check", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["is_suspicious"] is False
    assert data["risk_level"] == "low"
    assert len(data["matched_signals"]) == 0
    assert "scam_advice.stay_vigilant" in data["advice_codes"]
    assert "Heuristic check" in data["disclaimer"]

def test_scam_checker_suspicious_patterns():
    token = get_auth_token("rahul_personal", "customer")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Urgency + Shortened link
    res1 = client.post("/guidance/scam-check", json={
        "message": "Urgent: Electricity will be disconnected tonight. Pay pending bill at bit.ly/power-pay"
    }, headers=headers)
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["is_suspicious"] is True
    assert data1["risk_level"] in ("medium", "high")
    codes = [s["code"] for s in data1["matched_signals"]]
    assert "urgency_threat" in codes
    assert "suspicious_link" in codes

    # 2. Remote access tool request + KYC update
    res2 = client.post("/guidance/scam-check", json={
        "message": "Your bank account suspended. Complete KYC update immediately using AnyDesk"
    }, headers=headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert data2["is_suspicious"] is True
    assert data2["risk_level"] == "high"
    codes2 = [s["code"] for s in data2["matched_signals"]]
    assert "remote_access" in codes2

    # 3. Collect request trap
    res3 = client.post("/guidance/scam-check", json={
        "message": "Congratulations! You won prize of 50000 rupees. Approve request to receive cashback."
    }, headers=headers)
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["is_suspicious"] is True
    codes3 = [s["code"] for s in data3["matched_signals"]]
    assert "financial_lure" in codes3 or "collect_trap" in codes3

def test_scam_checker_credential_rejection():
    token = get_auth_token("rahul_personal", "customer")
    headers = {"Authorization": f"Bearer {token}"}

    # Should reject OTP credential per §11, §14
    res_otp = client.post("/guidance/scam-check", json={
        "message": "Your OTP is 482913 please confirm"
    }, headers=headers)
    assert res_otp.status_code == 422
    err_otp = res_otp.json()
    assert err_otp["error"]["code"] == "CREDENTIAL_INPUT_REJECTED"
    # Never echo the rejected secret in response body
    assert "482913" not in str(err_otp)

    # Should reject standalone numbers
    res_digits = client.post("/guidance/scam-check", json={
        "message": "123456"
    }, headers=headers)
    assert res_digits.status_code == 422
    assert res_digits.json()["error"]["code"] == "CREDENTIAL_INPUT_REJECTED"

    # Should reject script injection
    res_script = client.post("/guidance/scam-check", json={
        "message": "<script>alert(1)</script>"
    }, headers=headers)
    assert res_script.status_code == 422
    assert res_script.json()["error"]["code"] == "INVALID_TEXT"

def test_risk_breakdown_comprehensive():
    token_rahul = get_auth_token("rahul_personal", "customer")
    token_priya = get_auth_token("priya_personal", "customer")
    token_reviewer = get_auth_token("ananya_reviewer", "reviewer")

    headers_rahul = {"Authorization": f"Bearer {token_rahul}"}
    headers_priya = {"Authorization": f"Bearer {token_priya}"}
    headers_reviewer = {"Authorization": f"Bearer {token_reviewer}"}

    db = SessionLocal()
    try:
        # Find a transaction belonging to Priya that has a risk assessment
        user_priya = db.query(User).filter(User.username == "priya_personal").first()
        assessment = (
            db.query(RiskAssessment)
            .join(Transaction)
            .filter(Transaction.user_id == user_priya.id)
            .first()
        )
        assert assessment is not None, "Seeded assessment not found for priya"
        tx_id = assessment.transaction_id

        # 1. Priya can access own transaction breakdown
        res_breakdown = client.get(f"/risk/assessments/{tx_id}/breakdown", headers=headers_priya)
        assert res_breakdown.status_code == 200
        data = res_breakdown.json()
        assert data["transaction_id"] == tx_id
        assert data["score"] == assessment.score
        assert data["band"] == assessment.band
        assert "what_would_change" in data
        assert isinstance(data["what_would_change"], list)

        # Check calculation for each what_would_change entry
        for item in data["what_would_change"]:
            assert "rule_code" in item
            assert "reduction_points" in item
            assert "without_signal_score" in item
            assert "without_signal_band" in item
            assert "explanation" in item
            assert item["without_signal_score"] <= data["score"] or data["score"] == 100
            if item["without_signal_score"] < 40:
                assert item["without_signal_band"] == "Low"
            elif item["without_signal_score"] < 70:
                assert item["without_signal_band"] == "Medium"
            else:
                assert item["without_signal_band"] == "High"

        # 2. Reviewer can access customer transaction breakdown
        res_rev = client.get(f"/risk/assessments/{tx_id}/breakdown", headers=headers_reviewer)
        assert res_rev.status_code == 200

        # 3. Another customer (Rahul) gets 404 (IDOR protection)
        res_rahul = client.get(f"/risk/assessments/{tx_id}/breakdown", headers=headers_rahul)
        assert res_rahul.status_code == 404

    finally:
        db.close()
