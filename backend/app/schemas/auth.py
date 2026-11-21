from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=100)

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
