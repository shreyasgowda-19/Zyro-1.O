from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import User
from app.schemas.auth import LoginRequest, TokenResponse, UserResponse
from app.security.auth import verify_password, create_access_token, get_current_user
from app.errors import AppError

router = APIRouter(prefix="", tags=["Auth"])

@router.post("/auth/login", response_model=TokenResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == login_req.username).first()
    if not user or not verify_password(login_req.password, user.password_hash):
        raise AppError("UNAUTHENTICATED", "Invalid username or password", status_code=status.HTTP_401_UNAUTHORIZED)

    if not user.is_active:
        raise AppError("UNAUTHENTICATED", "User account is inactive", status_code=status.HTTP_401_UNAUTHORIZED)

    token = create_access_token(
        user_id=user.id,
        role=user.role,
        profile_type=user.profile_type
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.get("/users/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)
