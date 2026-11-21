from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.models.entities import SavingsGoal
from app.services.accounting_service import get_ledger_balances
from app.clock import utcnow
from app.errors import AppError

def format_goal_dto(goal: SavingsGoal) -> Dict[str, Any]:
    pct = (
        round(min(100.0, (goal.current_paise / goal.target_paise) * 100), 1)
        if goal.target_paise > 0
        else 0.0
    )
    return {
        "id": goal.id,
        "user_id": goal.user_id,
        "title": goal.title,
        "target_paise": goal.target_paise,
        "current_paise": goal.current_paise,
        "target_date": goal.target_date,
        "progress_percentage": pct,
        "created_at": goal.created_at.isoformat() if goal.created_at else ""
    }

def get_user_goals(db: Session, user_id: int) -> List[Dict[str, Any]]:
    goals = db.query(SavingsGoal).filter(
        SavingsGoal.user_id == user_id
    ).order_by(SavingsGoal.created_at.desc()).all()
    return [format_goal_dto(g) for g in goals]

def create_goal(
    db: Session,
    user_id: int,
    title: str,
    target_paise: int,
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    goal = SavingsGoal(
        user_id=user_id,
        title=title.strip(),
        target_paise=target_paise,
        current_paise=0,
        target_date=target_date,
        created_at=utcnow()
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    return format_goal_dto(goal)

def update_goal(
    db: Session,
    user_id: int,
    goal_id: int,
    title: Optional[str] = None,
    target_paise: Optional[int] = None,
    target_date: Optional[str] = None
) -> Dict[str, Any]:
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == user_id
    ).first()
    if not goal:
        raise AppError("NOT_FOUND", "Savings goal not found", status_code=404)

    if title is not None:
        goal.title = title.strip()
    if target_paise is not None:
        goal.target_paise = target_paise
    if target_date is not None:
        goal.target_date = target_date

    db.commit()
    db.refresh(goal)
    return format_goal_dto(goal)

def contribute_to_goal(
    db: Session,
    user_id: int,
    goal_id: int,
    amount_paise: int
) -> Dict[str, Any]:
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == user_id
    ).first()
    if not goal:
        raise AppError("NOT_FOUND", "Savings goal not found", status_code=404)

    # Validate against available ledger balance (§8, §13)
    balances = get_ledger_balances(db, user_id)
    if amount_paise > balances["available_balance_paise"]:
        raise AppError(
            code="INSUFFICIENT_FUNDS",
            message="Contribution amount exceeds your available balance.",
            status_code=409,
            params={
                "amount_paise": amount_paise,
                "available_balance_paise": balances["available_balance_paise"]
            }
        )

    goal.current_paise += amount_paise
    db.commit()
    db.refresh(goal)
    return format_goal_dto(goal)

def delete_goal(db: Session, user_id: int, goal_id: int) -> bool:
    goal = db.query(SavingsGoal).filter(
        SavingsGoal.id == goal_id,
        SavingsGoal.user_id == user_id
    ).first()
    if not goal:
        raise AppError("NOT_FOUND", "Savings goal not found", status_code=404)

    db.delete(goal)
    db.commit()
    return True
