from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.clock import utcnow
from app.database import get_db
from app.errors import AppError
from app.models.entities import TrackedAccount, User
from app.schemas.tracked_account import (
    TrackedAccountCreate,
    TrackedAccountResponse,
    TrackedBalanceUpdate,
)
from app.security.auth import require_role

router = APIRouter(prefix="/accounts", tags=["Personal Accounts"])


@router.get("", response_model=list[TrackedAccountResponse])
def list_tracked_accounts(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    return (
        db.query(TrackedAccount)
        .filter(TrackedAccount.user_id == current_user.id)
        .order_by(TrackedAccount.created_at.desc(), TrackedAccount.id.desc())
        .all()
    )


@router.post("", response_model=TrackedAccountResponse, status_code=status.HTTP_201_CREATED)
def create_tracked_account(
    payload: TrackedAccountCreate,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    account = TrackedAccount(
        user_id=current_user.id,
        institution_name=payload.institution_name.strip(),
        account_name=payload.account_name.strip(),
        account_type=payload.account_type,
        last_four=payload.last_four,
        reported_balance_paise=payload.reported_balance_paise,
        balance_as_of=utcnow(),
    )
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.patch("/{account_id}/balance", response_model=TrackedAccountResponse)
def update_tracked_balance(
    account_id: int,
    payload: TrackedBalanceUpdate,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    account = (
        db.query(TrackedAccount)
        .filter(TrackedAccount.id == account_id, TrackedAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise AppError("NOT_FOUND", "Account not found", status_code=status.HTTP_404_NOT_FOUND)
    account.reported_balance_paise = payload.reported_balance_paise
    account.balance_as_of = utcnow()
    db.commit()
    db.refresh(account)
    return account


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_tracked_account(
    account_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db),
):
    account = (
        db.query(TrackedAccount)
        .filter(TrackedAccount.id == account_id, TrackedAccount.user_id == current_user.id)
        .first()
    )
    if not account:
        raise AppError("NOT_FOUND", "Account not found", status_code=status.HTTP_404_NOT_FOUND)
    db.delete(account)
    db.commit()
