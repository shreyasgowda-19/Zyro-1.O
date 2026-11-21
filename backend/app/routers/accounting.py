from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import User
from app.schemas.payments import BalancesResponse, ReconciliationResponse
from app.services.accounting_service import get_ledger_balances, run_reconciliation
from app.services.analytics_service import get_cashflow_analytics, get_category_analytics
from app.security.auth import require_role
from app.clock import utcnow

router = APIRouter(prefix="/accounting", tags=["Accounting"])

@router.get("/summary", response_model=BalancesResponse)
def get_accounting_summary(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    balances = get_ledger_balances(db, current_user.id)
    return balances

@router.get("/reconciliation", response_model=ReconciliationResponse)
def get_accounting_reconciliation(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    recon = run_reconciliation(db, current_user.id)
    return recon

@router.get("/cashflow")
def get_cashflow(
    period: Optional[str] = Query(None, description="Period formatted as YYYY-MM"),
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    if not period:
        period = utcnow().strftime("%Y-%m")
    return get_cashflow_analytics(db, current_user.id, period)

@router.get("/categories")
def get_categories(
    period: Optional[str] = Query(None, description="Period formatted as YYYY-MM"),
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    if not period:
        period = utcnow().strftime("%Y-%m")
    return get_category_analytics(db, current_user.id, period)

