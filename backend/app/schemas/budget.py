from typing import Optional, List
from pydantic import BaseModel, conint, constr, Field
from app.schemas.payments import StrictPaise

StrictCategory = constr(max_length=50, strict=True)
StrictPeriod = constr(regex=r"^\d{4}-\d{2}$", strict=True)

class BudgetCreateRequest(BaseModel):
    category: Optional[StrictCategory] = Field(None, description="Category name, or null for overall budget")
    amount_paise: StrictPaise = Field(..., description="Monthly budget limit in integer paise")
    period: StrictPeriod = Field(..., description="Budget period formatted as YYYY-MM")

class BudgetUpdateRequest(BaseModel):
    amount_paise: StrictPaise = Field(..., description="Updated budget limit in integer paise")

class BudgetResponse(BaseModel):
    id: int
    user_id: int
    category: Optional[str] = None
    amount_paise: int
    period: str
    created_at: str

class CategoryBudgetSummary(BaseModel):
    category: str
    budget_paise: Optional[int] = None
    spent_paise: int
    remaining_paise: Optional[int] = None
    percentage: Optional[float] = None

class OverallBudgetSummary(BaseModel):
    budget_paise: Optional[int] = None
    spent_paise: int
    remaining_paise: Optional[int] = None
    percentage: Optional[float] = None

class BudgetSummaryResponse(BaseModel):
    period: str
    overall: OverallBudgetSummary
    categories: List[CategoryBudgetSummary]
