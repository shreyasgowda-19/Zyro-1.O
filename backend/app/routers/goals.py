from typing import List
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.entities import User
from app.security.auth import require_role
from app.schemas.goal import (
    GoalCreateRequest,
    GoalUpdateRequest,
    GoalContributionRequest,
    GoalResponse
)
from app.services.goal_service import (
    get_user_goals,
    create_goal,
    update_goal,
    contribute_to_goal,
    delete_goal
)

router = APIRouter(prefix="/goals", tags=["Goals"])

@router.get("", response_model=List[GoalResponse])
def list_goals(
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    return get_user_goals(db, current_user.id)

@router.post("", response_model=GoalResponse, status_code=status.HTTP_201_CREATED)
def new_goal(
    payload: GoalCreateRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    return create_goal(
        db=db,
        user_id=current_user.id,
        title=payload.title,
        target_paise=payload.target_paise,
        target_date=payload.target_date
    )

@router.patch("/{goal_id}", response_model=GoalResponse)
def modify_goal(
    goal_id: int,
    payload: GoalUpdateRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    return update_goal(
        db=db,
        user_id=current_user.id,
        goal_id=goal_id,
        title=payload.title,
        target_paise=payload.target_paise,
        target_date=payload.target_date
    )

@router.post("/{goal_id}/contributions", response_model=GoalResponse)
def add_contribution(
    goal_id: int,
    payload: GoalContributionRequest,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    return contribute_to_goal(
        db=db,
        user_id=current_user.id,
        goal_id=goal_id,
        amount_paise=payload.amount_paise
    )

@router.delete("/{goal_id}")
def remove_goal(
    goal_id: int,
    current_user: User = Depends(require_role("customer")),
    db: Session = Depends(get_db)
):
    delete_goal(db, current_user.id, goal_id)
    return {"status": "ok", "message": "Goal deleted successfully"}
