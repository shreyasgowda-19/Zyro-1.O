import os
import sys

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

backend_dir = os.path.join(project_root, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.database import Base
from app.models.entities import User
from app.security.auth import verify_password
from scripts.create_staff import create_staff_user


@pytest.fixture
def staff_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(autocommit=False, autoflush=False, bind=engine)()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)
        engine.dispose()


def test_create_staff_user_hashes_password_and_assigns_role(staff_db):
    user = create_staff_user(staff_db, "Branch.Reviewer", "reviewer", "A-long-staff-password")
    assert user.username == "branch.reviewer"
    assert user.role == "reviewer"
    assert user.profile_type is None
    assert user.password_hash != "A-long-staff-password"
    assert verify_password("A-long-staff-password", user.password_hash)


def test_create_staff_user_rejects_duplicate_or_customer_role(staff_db):
    create_staff_user(staff_db, "branch.manager", "supervisor", "A-long-staff-password")
    with pytest.raises(ValueError, match="already exists"):
        create_staff_user(staff_db, "BRANCH.MANAGER", "reviewer", "Another-long-password")
    with pytest.raises(ValueError, match="reviewer or supervisor"):
        create_staff_user(staff_db, "not-a-customer", "customer", "A-long-staff-password")


def test_create_staff_user_requires_strong_password(staff_db):
    with pytest.raises(ValueError, match="12-100"):
        create_staff_user(staff_db, "branch.reviewer", "reviewer", "short")