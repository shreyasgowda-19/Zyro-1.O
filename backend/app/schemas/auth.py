from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    profile_type: Optional[str] = Field("personal")
    initial_balance_paise: Optional[int] = Field(5000000, ge=0, le=1000000000)

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    profile_type: Optional[str] = None
    is_active: bool
    created_at: datetime

    class Config:
        orm_mode = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
