import json
from typing import Optional
from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import User, Transaction, RiskAssessment
from app.schemas.payments import PaymentCreateRequest, PaymentResponse
from app.services.payment_service import create_payment, confirm_payment, cancel_payment
from app.security.auth import get_current_user, require_role
from app.errors import AppError

router = APIRouter(prefix="", tags=["Payments"])

@router.post("/payments", response_model=PaymentResponse)
async def post_payment(
    payment_req: PaymentCreateRequest,
    request: Request,
    idempotency_key: Optional[str] = Header(None, alias="Idempotency-Key"),
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    if not idempotency_key or len(idempotency_key.strip()) < 4:
        raise AppError("VALIDATION_ERROR", "Missing or invalid Idempotency-Key header.", status_code=422)

    raw_bytes = await request.body()
    payment_dict = payment_req.dict()

    result = create_payment(
        db=db,
        user=current_user,
        payment_data=payment_dict,
        idempotency_key=idempotency_key,
        raw_payload_bytes=raw_bytes
    )
    return result

@router.get("/payments/{payment_id}", response_model=PaymentResponse)
def get_payment_by_id(
    payment_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == payment_id,
        Transaction.user_id == current_user.id
    ).first()

    if not tx:
        raise AppError("NOT_FOUND", "Payment not found", status_code=404)

    assessment_data = None
    if tx.assessment:
        assessment_data = {
            "score": tx.assessment.score,
            "band": tx.assessment.band,
            "rules_version": tx.assessment.rules_version,
            "reasons": [
                {
                    "rule_code": r.rule_code,
                    "points": r.points,
                    "params": json.loads(r.params_json)
                }
                for r in tx.assessment.reasons
            ]
        }

    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "type": tx.type,
        "source": tx.source,
        "amount_paise": tx.amount_paise,
        "category": tx.category,
        "payee_id": tx.payee_id,
        "payee_name": tx.payee.display_name if tx.payee else None,
        "masked_payee": tx.payee.masked_identifier if tx.payee else None,
        "method": tx.method,
        "status": tx.status,
        "note": tx.note,
        "created_at": tx.created_at.isoformat(),
        "assessment": assessment_data
    }

@router.post("/payments/{payment_id}/confirm")
def post_confirm_payment(
    payment_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    return confirm_payment(db, current_user, payment_id)

@router.post("/payments/{payment_id}/cancel")
def post_cancel_payment(
    payment_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    return cancel_payment(db, current_user, payment_id)
