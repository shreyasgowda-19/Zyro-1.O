from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field, conint, constr


BalancePaise = conint(strict=True, ge=-1000000000000, le=1000000000000)
AccountName = constr(strict=True, min_length=1, max_length=50)
InstitutionName = constr(strict=True, min_length=1, max_length=80)


class TrackedAccountCreate(BaseModel):
    institution_name: InstitutionName
    account_name: AccountName
    account_type: Literal["savings", "current", "cash", "other"]
    last_four: Optional[constr(strict=True, regex=r"^\d{4}$")] = None
    reported_balance_paise: BalancePaise


class TrackedBalanceUpdate(BaseModel):
    reported_balance_paise: BalancePaise


class TrackedAccountResponse(BaseModel):
    id: int
    institution_name: str
    account_name: str
    account_type: str
    last_four: Optional[str]
    reported_balance_paise: int
    balance_as_of: datetime
    created_at: datetime

    class Config:
        orm_mode = True
