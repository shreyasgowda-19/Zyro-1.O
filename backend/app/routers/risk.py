import json
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import Transaction, RiskAssessment, RiskReason, User
from app.security.auth import get_current_user
from app.errors import AppError

router = APIRouter(prefix="/risk", tags=["Risk"])

@router.get("/assessments/{transaction_id}")
def get_risk_assessment(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise AppError("NOT_FOUND", "Transaction not found", status_code=404)

    # Authorization: Customer can only access own assessment; Reviewer/Supervisor can access any
    if current_user.role == "customer" and tx.user_id != current_user.id:
        raise AppError("NOT_FOUND", "Transaction not found", status_code=404)

    assessment = db.query(RiskAssessment).filter(RiskAssessment.transaction_id == tx.id).first()
    if not assessment:
        raise AppError("NOT_FOUND", "Risk assessment not found for this transaction", status_code=404)

    reasons = []
    if assessment.reasons:
        for r in assessment.reasons:
            try:
                params = json.loads(r.params_json) if r.params_json else {}
            except Exception:
                params = {}
            reasons.append({
                "rule_code": r.rule_code,
                "points": r.points,
                "params": params
            })

    try:
        features = json.loads(assessment.features_json) if assessment.features_json else {}
    except Exception:
        features = {}

    return {
        "transaction_id": tx.id,
        "score": assessment.score,
        "band": assessment.band,
        "rules_version": assessment.rules_version,
        "features": features,
        "reasons": reasons,
        "created_at": assessment.created_at.isoformat()
    }

RULE_EXPLANATIONS = {
    "R1": {
        "factor": "amount",
        "explanation": "Reducing amount closer to your average spending would lower the score."
    },
    "R2": {
        "factor": "payee",
        "explanation": "Paying a known, trusted payee instead of a new one would lower the score."
    },
    "R3": {
        "factor": "time",
        "explanation": "Paying during standard daytime hours (05:00-23:59 IST) would lower the score."
    },
    "R4": {
        "factor": "velocity",
        "explanation": "Waiting at least 5 minutes between payments would lower the score."
    },
    "R5": {
        "factor": "device_city",
        "explanation": "Transacting from a recognized device and usual city would lower the score."
    },
    "R6": {
        "factor": "payee_trust",
        "explanation": "Payee is on security watchlists. Removing this flagged payee would reduce the score."
    },
    "R7": {
        "factor": "repeat_pattern",
        "explanation": "Avoiding amounts just under round limits or repeated identical payments within 24h would lower the score."
    },
    "R8": {
        "factor": "language",
        "explanation": "Removing urgency, lottery, or refund keywords from payment notes would lower the score."
    },
    "R9": {
        "factor": "balance_drain",
        "explanation": "Paying an amount that leaves a healthy available balance (>20%) would lower the score."
    },
    "R10": {
        "factor": "collect_method",
        "explanation": "Initiating a direct payment rather than approving an unknown collect request would lower the score."
    }
}

@router.get("/assessments/{transaction_id}/breakdown")
def get_risk_breakdown(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(Transaction.id == transaction_id).first()
    if not tx:
        raise AppError("NOT_FOUND", "Transaction not found", status_code=404)

    if current_user.role == "customer" and tx.user_id != current_user.id:
        raise AppError("NOT_FOUND", "Transaction not found", status_code=404)

    assessment = db.query(RiskAssessment).filter(RiskAssessment.transaction_id == tx.id).first()
    if not assessment:
        raise AppError("NOT_FOUND", "Risk assessment not found", status_code=404)

    reasons = assessment.reasons or []
    raw_points = sum(r.points for r in reasons)

    fired_reasons = []
    what_would_change = []

    for r in reasons:
        try:
            params = json.loads(r.params_json) if r.params_json else {}
        except Exception:
            params = {}

        without_score = max(0, min(100, raw_points - r.points))
        without_band = "Low" if without_score < 40 else "Medium" if without_score < 70 else "High"

        rule_info = RULE_EXPLANATIONS.get(r.rule_code, {
            "factor": "risk_signal",
            "explanation": f"Without this signal the score would reduce by {r.points} points."
        })

        fired_reasons.append({
            "rule_code": r.rule_code,
            "points": r.points,
            "params": params
        })

        what_would_change.append({
            "rule_code": r.rule_code,
            "factor": rule_info["factor"],
            "reduction_points": r.points,
            "without_signal_score": without_score,
            "without_signal_band": without_band,
            "explanation": f"{rule_info['explanation']} Without this signal, the score would be {without_score} ({without_band} risk)."
        })

    return {
        "transaction_id": tx.id,
        "score": assessment.score,
        "band": assessment.band,
        "rules_version": assessment.rules_version,
        "fired_reasons": fired_reasons,
        "what_would_change": what_would_change
    }
