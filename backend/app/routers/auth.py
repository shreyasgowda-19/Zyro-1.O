from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.entities import User, Account
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.security.auth import verify_password, hash_password, create_access_token, get_current_user
from app.errors import AppError

router = APIRouter(prefix="", tags=["Auth"])

@router.post("/auth/register", response_model=TokenResponse)
def register(reg_req: RegisterRequest, db: Session = Depends(get_db)):
    clean_username = reg_req.username.strip().lower()
    existing = db.query(User).filter(User.username == clean_username).first()
    if existing:
        raise AppError("CONFLICT", f"Username '{clean_username}' is already taken. Please choose another.", status_code=status.HTTP_409_CONFLICT)

    # Create new customer user
    profile_type = reg_req.profile_type if reg_req.profile_type in ("personal", "business") else "personal"
    new_user = User(
        username=clean_username,
        password_hash=hash_password(reg_req.password),
        role="customer",
        profile_type=profile_type,
        is_active=True
    )
    db.add(new_user)
    db.flush()

    # Create customer ledger account with initial deposit (stored in database)
    opening_balance = reg_req.initial_balance_paise if reg_req.initial_balance_paise is not None else 5000000
    account = Account(
        user_id=new_user.id,
        opening_balance_paise=opening_balance
    )
    db.add(account)
    db.commit()
    db.refresh(new_user)

    token = create_access_token(
        user_id=new_user.id,
        role=new_user.role,
        profile_type=new_user.profile_type
    )

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.from_orm(new_user)
    )

@router.post("/auth/login", response_model=TokenResponse)
def login(login_req: LoginRequest, db: Session = Depends(get_db)):
    clean_username = login_req.username.strip().lower()
    user = db.query(User).filter(User.username == clean_username).first()
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
