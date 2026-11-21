import hmac
import hashlib
import base64
import json
import time
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.entities import User
from app.errors import AppError

security_scheme = HTTPBearer(auto_error=False)

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"pbkdf2_sha256:100000:{salt}:{key.hex()}"

def verify_password(plain_password: str, hashed: str) -> bool:
    try:
        parts = hashed.split(":")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iters = int(parts[1])
        salt = parts[2]
        expected_hex = parts[3]
        computed = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iters)
        return secrets.compare_digest(computed.hex(), expected_hex)
    except Exception:
        return False

def b64_url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")

def b64_url_decode(s: str) -> bytes:
    padding = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode((s + padding).encode("ascii"))

def create_access_token(user_id: int, role: str, profile_type: Optional[str] = None) -> str:
    now = int(time.time())
    exp = now + (settings.JWT_EXPIRATION_MINUTES * 60)
    header = {"alg": settings.JWT_ALGORITHM, "typ": "JWT"}
    payload = {
        "sub": str(user_id),
        "role": role,
        "profile_type": profile_type,
        "iat": now,
        "exp": exp
    }
    h_b64 = b64_url_encode(json.dumps(header).encode("utf-8"))
    p_b64 = b64_url_encode(json.dumps(payload).encode("utf-8"))
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    return f"{h_b64}.{p_b64}.{b64_url_encode(sig)}"

def decode_access_token(token: str) -> Dict[str, Any]:
    parts = token.split(".")
    if len(parts) != 3:
        raise AppError("UNAUTHENTICATED", "Invalid token format", status_code=status.HTTP_401_UNAUTHORIZED)
    h_b64, p_b64, s_b64 = parts
    signing_input = f"{h_b64}.{p_b64}".encode("ascii")
    expected_sig = hmac.new(settings.JWT_SECRET.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        actual_sig = b64_url_decode(s_b64)
    except Exception:
        raise AppError("UNAUTHENTICATED", "Invalid token signature encoding", status_code=status.HTTP_401_UNAUTHORIZED)

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise AppError("UNAUTHENTICATED", "Invalid token signature", status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        payload = json.loads(b64_url_decode(p_b64).decode("utf-8"))
    except Exception:
        raise AppError("UNAUTHENTICATED", "Invalid token payload", status_code=status.HTTP_401_UNAUTHORIZED)

    if "exp" in payload and payload["exp"] < int(time.time()):
        raise AppError("UNAUTHENTICATED", "Token has expired", status_code=status.HTTP_401_UNAUTHORIZED)

    return payload

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
    db: Session = Depends(get_db)
) -> User:
    if not credentials or not credentials.credentials:
        raise AppError("UNAUTHENTICATED", "Missing authorization header", status_code=status.HTTP_401_UNAUTHORIZED)
    
    payload = decode_access_token(credentials.credentials)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise AppError("UNAUTHENTICATED", "Missing subject claim", status_code=status.HTTP_401_UNAUTHORIZED)

    try:
        user_id = int(user_id_str)
    except ValueError:
        raise AppError("UNAUTHENTICATED", "Invalid subject claim", status_code=status.HTTP_401_UNAUTHORIZED)

    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise AppError("UNAUTHENTICATED", "User not found or inactive", status_code=status.HTTP_401_UNAUTHORIZED)

    return user

def require_role(*roles: str):
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise AppError("FORBIDDEN", f"Access denied. Requires role: {', '.join(roles)}", status_code=status.HTTP_403_FORBIDDEN)
        return current_user
    return role_checker

def mask_customer_reference(user_id: int) -> str:
    """Masked customer reference: CUST- + first 6 hex chars of HMAC(secret, user_id)."""
    h = hmac.new(settings.JWT_SECRET.encode("utf-8"), str(user_id).encode("utf-8"), hashlib.sha256).hexdigest()
    return f"CUST-{h[:6].upper()}"

def mask_payee_identifier(identifier: str) -> str:
    """Masked payee identifier: last 4 chars (••••ab12)."""
    clean = identifier.strip()
    if len(clean) <= 4:
        return f"••••{clean}"
    return f"••••{clean[-4:]}"
