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

    fired_reasons = []
    what_would_change = []

    for r in assessment.reasons:
        try:
            params = json.loads(r.params_json) if r.params_json else {}
        except Exception:
            params = {}

        fired_reasons.append({
            "rule_code": r.rule_code,
            "points": r.points,
            "params": params
        })

        if r.rule_code == "R1":
            what_would_change.append({
                "factor": "amount",
                "reduction_points": r.points,
                "explanation": f"Reducing amount closer to your average spending would lower the score by {r.points} points."
            })
        elif r.rule_code == "R2":
            what_would_change.append({
                "factor": "payee",
                "reduction_points": r.points,
                "explanation": f"Paying a known, trusted payee instead of a new one would lower the score by {r.points} points."
            })
        elif r.rule_code == "R3":
            what_would_change.append({
                "factor": "time",
                "reduction_points": r.points,
                "explanation": f"Paying between 5 AM and 11 PM instead of late night would lower the score by {r.points} points."
            })
        elif r.rule_code == "R4":
            what_would_change.append({
                "factor": "velocity",
                "reduction_points": r.points,
                "explanation": f"Waiting 5 minutes between payments would lower the score by {r.points} points."
            })
        elif r.rule_code == "R6":
            what_would_change.append({
                "factor": "payee_trust",
                "reduction_points": r.points,
                "explanation": f"Payee is on security watchlists. Removing this flagged payee would reduce the score by {r.points} points."
            })
        elif r.rule_code == "R8":
            what_would_change.append({
                "factor": "language",
                "reduction_points": r.points,
                "explanation": f"Removing urgency/scam keywords from payment note would lower the score by {r.points} points."
            })
        elif r.rule_code == "R10":
            what_would_change.append({
                "factor": "method",
                "reduction_points": r.points,
                "explanation": f"Initiating a direct payment rather than approving an unknown collect request would lower the score by {r.points} points."
            })

    return {
        "transaction_id": tx.id,
        "score": assessment.score,
        "band": assessment.band,
        "rules_version": assessment.rules_version,
        "fired_reasons": fired_reasons,
        "what_would_change": what_would_change
    }
