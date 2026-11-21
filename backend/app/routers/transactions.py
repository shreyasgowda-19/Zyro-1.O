from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import User, Transaction, AuditLog
from app.schemas.payments import PaymentResponse, ManualTransactionCreateRequest, CategoryPatchRequest
from app.security.auth import require_role
from app.services.credential_guard import validate_sensitive_input
from app.errors import AppError

router = APIRouter(prefix="", tags=["Transactions"])

@router.get("/transactions", response_model=List[PaymentResponse])
def get_transactions(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    txs = db.query(Transaction).filter(
        Transaction.user_id == current_user.id
    ).order_by(Transaction.created_at.desc()).offset(offset).limit(limit).all()

    return [
        {
            "id": t.id,
            "user_id": t.user_id,
            "type": t.type,
            "source": t.source,
            "amount_paise": t.amount_paise,
            "category": t.category,
            "payee_id": t.payee_id,
            "payee_name": t.payee.display_name if t.payee else None,
            "masked_payee": t.payee.masked_identifier if t.payee else None,
            "method": t.method,
            "status": t.status,
            "note": t.note,
            "created_at": t.created_at.isoformat(),
            "assessment": None
        }
        for t in txs
    ]

@router.get("/transactions/{transaction_id}", response_model=PaymentResponse)
def get_transaction_by_id(
    transaction_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    t = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not t:
        raise AppError("NOT_FOUND", "Transaction not found", status_code=404)

    return {
        "id": t.id,
        "user_id": t.user_id,
        "type": t.type,
        "source": t.source,
        "amount_paise": t.amount_paise,
        "category": t.category,
        "payee_id": t.payee_id,
        "payee_name": t.payee.display_name if t.payee else None,
        "masked_payee": t.payee.masked_identifier if t.payee else None,
        "method": t.method,
        "status": t.status,
        "note": t.note,
        "created_at": t.created_at.isoformat(),
        "assessment": None
    }

@router.post("/transactions", response_model=PaymentResponse)
def create_manual_transaction(
    tx_req: ManualTransactionCreateRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    if tx_req.type not in ("income", "expense"):
        raise AppError("VALIDATION_ERROR", "Type must be income or expense", status_code=422)

    safe_note = validate_sensitive_input(tx_req.note, "note") if tx_req.note else None
    created_at = tx_req.created_at or datetime.now(timezone.utc)

    # Manual transactions are never scored and always completed (§8, §13)
    tx = Transaction(
        user_id=current_user.id,
        type=tx_req.type,
        source="manual",
        amount_paise=tx_req.amount_paise,
        category=tx_req.category,
        payee_id=None,
        method="netbanking" if tx_req.type == "income" else "upi",
        status="completed",
        note=safe_note,
        created_at=created_at
    )
    db.add(tx)
    db.commit()

    if tx.type == "expense" and tx.status == "completed":
        from app.services.budget_service import evaluate_budget_alerts
        evaluate_budget_alerts(db, current_user.id, tx.created_at.strftime("%Y-%m"))

    return {
        "id": tx.id,
        "user_id": tx.user_id,
        "type": tx.type,
        "source": tx.source,
        "amount_paise": tx.amount_paise,
        "category": tx.category,
        "payee_id": None,
        "payee_name": None,
        "masked_payee": None,
        "method": tx.method,
        "status": tx.status,
        "note": tx.note,
        "created_at": tx.created_at.isoformat(),
        "assessment": None
    }

@router.patch("/transactions/{transaction_id}/category", response_model=PaymentResponse)
def patch_transaction_category(
    transaction_id: int,
    patch_req: CategoryPatchRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    tx = db.query(Transaction).filter(
        Transaction.id == transaction_id,
        Transaction.user_id == current_user.id
    ).first()

    if not tx:
        raise AppError("NOT_FOUND", "Transaction not found", status_code=404)

    tx.category = patch_req.category
    db.commit()

    if tx.type == "expense" and tx.status == "completed":
        from app.services.budget_service import evaluate_budget_alerts
        evaluate_budget_alerts(db, current_user.id, tx.created_at.strftime("%Y-%m"))

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
        "assessment": None
    }
