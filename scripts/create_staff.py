import argparse
import getpass
import os
import re
import sys
from typing import Optional, Sequence

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import SessionLocal
from app.models.entities import User
from app.security.auth import hash_password

STAFF_ROLES = {"reviewer", "supervisor"}


def create_staff_user(db, username: str, role: str, password: str) -> User:
    clean_username = username.strip().lower()
    if role not in STAFF_ROLES:
        raise ValueError("Staff role must be reviewer or supervisor.")
    if not re.fullmatch(r"[a-z0-9_.-]{3,50}", clean_username):
        raise ValueError("Username must be 3-50 characters using letters, numbers, dots, underscores, or hyphens.")
    if len(password) < 12 or len(password) > 100:
        raise ValueError("Staff passwords must be 12-100 characters long.")
    if db.query(User).filter(User.username == clean_username).first():
        raise ValueError(f"Username '{clean_username}' already exists.")

    user = User(
        username=clean_username,
        password_hash=hash_password(password),
        role=role,
        profile_type=None,
        is_active=True,
    )
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except Exception:
        db.rollback()
        raise
    return user


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Create a PayGuard bank reviewer or supervisor account.")
    parser.add_argument("username", help="New staff username")
    parser.add_argument("--role", required=True, choices=sorted(STAFF_ROLES))
    args = parser.parse_args(argv)

    password = getpass.getpass("New staff password (12-100 characters): ")
    confirm = getpass.getpass("Confirm staff password: ")
    if password != confirm:
        parser.error("Passwords do not match.")

    db = SessionLocal()
    try:
        user = create_staff_user(db, args.username, args.role, password)
    except ValueError as exc:
        parser.error(str(exc))
    finally:
        db.close()

    print(f"Created {user.role} account '{user.username}'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())