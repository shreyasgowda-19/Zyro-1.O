from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import User
from app.security.auth import require_role
from app.clock import utcnow
from app.schemas.budget import (
    BudgetCreateRequest,
    BudgetUpdateRequest,
    BudgetResponse,
    BudgetSummaryResponse
)
from app.services.budget_service import (
    get_user_budgets,
    create_or_update_budget,
    update_budget,
    delete_budget,
    get_budget_summary
)

router = APIRouter(prefix="/budgets", tags=["Budgets"])

@router.get("", response_model=List[BudgetResponse])
def list_budgets(
    period: Optional[str] = Query(None, description="Filter by YYYY-MM period"),
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    budgets = get_user_budgets(db, current_user.id, period)
    return [
        {
            "id": b.id,
            "user_id": b.user_id,
            "category": b.category,
            "amount_paise": b.amount_paise,
            "period": b.period,
            "created_at": b.created_at.isoformat() if b.created_at else ""
        }
        for b in budgets
    ]

@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    payload: BudgetCreateRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    budget = create_or_update_budget(
        db=db,
        user_id=current_user.id,
        category=payload.category,
        amount_paise=payload.amount_paise,
        period=payload.period
    )
    return {
        "id": budget.id,
        "user_id": budget.user_id,
        "category": budget.category,
        "amount_paise": budget.amount_paise,
        "period": budget.period,
        "created_at": budget.created_at.isoformat() if budget.created_at else ""
    }

@router.put("/{budget_id}", response_model=BudgetResponse)
def modify_budget(
    budget_id: int,
    payload: BudgetUpdateRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    budget = update_budget(db, current_user.id, budget_id, payload.amount_paise)
    return {
        "id": budget.id,
        "user_id": budget.user_id,
        "category": budget.category,
        "amount_paise": budget.amount_paise,
        "period": budget.period,
        "created_at": budget.created_at.isoformat() if budget.created_at else ""
    }

@router.delete("/{budget_id}")
def remove_budget(
    budget_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    delete_budget(db, current_user.id, budget_id)
    return {"status": "ok", "message": "Budget deleted successfully"}

@router.get("/summary", response_model=BudgetSummaryResponse)
def get_summary(
    period: Optional[str] = Query(None, description="Budget period (YYYY-MM)"),
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    if not period:
        period = utcnow().strftime("%Y-%m")
    summary = get_budget_summary(db, current_user.id, period)
    return summary
