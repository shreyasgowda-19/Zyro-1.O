from typing import Optional
from pydantic import BaseModel, conint, constr, Field

StrictTitle = constr(min_length=1, max_length=100, strict=True)
StrictDateStr = constr(max_length=20, strict=True)
StrictGoalPaise = conint(ge=100, le=1000000000, strict=True)

class GoalCreateRequest(BaseModel):
    title: StrictTitle = Field(..., description="Title of the savings goal")
    target_paise: StrictGoalPaise = Field(..., description="Target savings amount in integer paise (up to ₹1,00,00,000)")
    target_date: Optional[StrictDateStr] = Field(None, description="Target completion date (YYYY-MM-DD)")

class GoalUpdateRequest(BaseModel):
    title: Optional[StrictTitle] = None
    target_paise: Optional[StrictGoalPaise] = None
    target_date: Optional[StrictDateStr] = None

class GoalContributionRequest(BaseModel):
    amount_paise: StrictGoalPaise = Field(..., description="Contribution amount in integer paise")

class GoalResponse(BaseModel):
    id: int
    user_id: int
    title: str
    target_paise: int
    current_paise: int
    target_date: Optional[str] = None
    progress_percentage: float
    created_at: str
