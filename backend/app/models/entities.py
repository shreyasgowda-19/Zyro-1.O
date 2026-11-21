from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, ForeignKey,
    Text, UniqueConstraint, CheckConstraint, Index
)
from sqlalchemy.orm import relationship
from app.database import Base

def utcnow():
    return datetime.now(timezone.utc)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)  # 'customer', 'reviewer', 'supervisor'
    profile_type = Column(String(20), nullable=True)  # 'personal', 'business' (customers only)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('customer', 'reviewer', 'supervisor')", name="check_user_role"),
        CheckConstraint("profile_type IS NULL OR profile_type IN ('personal', 'business')", name="check_user_profile_type"),
    )

    account = relationship("Account", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payees = relationship("Payee", back_populates="owner", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    budgets = relationship("Budget", back_populates="user", cascade="all, delete-orphan")
    savings_goals = relationship("SavingsGoal", back_populates="user", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="user", cascade="all, delete-orphan")

class Account(Base):
    __tablename__ = "accounts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    opening_balance_paise = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        CheckConstraint("opening_balance_paise >= 0", name="check_account_opening_balance"),
    )

    user = relationship("User", back_populates="account")

class Payee(Base):
    __tablename__ = "payees"

    id = Column(Integer, primary_key=True, index=True)
    owner_user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    display_name = Column(String(60), nullable=False)
    masked_identifier = Column(String(30), nullable=False)
    trust_status = Column(String(20), default="new", nullable=False)  # 'new', 'known', 'flagged'
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("owner_user_id", "masked_identifier", name="uq_owner_masked_identifier"),
        CheckConstraint("trust_status IN ('new', 'known', 'flagged')", name="check_payee_trust_status"),
    )

    owner = relationship("User", back_populates="payees")
    transactions = relationship("Transaction", back_populates="payee")

class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(10), nullable=False)  # 'income', 'expense'
    source = Column(String(10), nullable=False)  # 'payment', 'manual'
    amount_paise = Column(Integer, nullable=False)
    category = Column(String(50), nullable=False)
    payee_id = Column(Integer, ForeignKey("payees.id", ondelete="SET NULL"), nullable=True)
    method = Column(String(30), nullable=False)  # 'upi', 'card', 'netbanking', 'wallet', 'collect_approval'
    status = Column(String(30), nullable=False)  # 'pending', 'awaiting_confirmation', 'held', 'escalated', 'completed', 'cancelled', 'released'
    note = Column(String(140), nullable=True)
    synthetic_device_tag = Column(String(50), nullable=True)
    synthetic_city_tag = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="check_tx_amount_positive"),
        CheckConstraint("type IN ('income', 'expense')", name="check_tx_type"),
        CheckConstraint("source IN ('payment', 'manual')", name="check_tx_source"),
        CheckConstraint("method IN ('upi', 'card', 'netbanking', 'wallet', 'collect_approval')", name="check_tx_method"),
        CheckConstraint("status IN ('pending', 'awaiting_confirmation', 'held', 'escalated', 'completed', 'cancelled', 'released')", name="check_tx_status"),
        Index("idx_tx_user_created", "user_id", "created_at"),
        Index("idx_tx_user_status", "user_id", "status"),
    )

    user = relationship("User", back_populates="transactions")
    payee = relationship("Payee", back_populates="transactions")
    assessment = relationship("RiskAssessment", back_populates="transaction", uselist=False, cascade="all, delete-orphan")
    review_case = relationship("ReviewCase", back_populates="transaction", uselist=False, cascade="all, delete-orphan")

class RiskAssessment(Base):
    __tablename__ = "risk_assessments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False)
    score = Column(Integer, nullable=False)
    band = Column(String(10), nullable=False)  # 'low', 'medium', 'high'
    rules_version = Column(String(20), nullable=False)
    ml_model_version = Column(String(20), nullable=True)
    features_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("score >= 0 AND score <= 100", name="check_assessment_score_range"),
        CheckConstraint("band IN ('low', 'medium', 'high')", name="check_assessment_band"),
    )

    transaction = relationship("Transaction", back_populates="assessment")
    reasons = relationship("RiskReason", back_populates="assessment", cascade="all, delete-orphan")

class RiskReason(Base):
    __tablename__ = "risk_reasons"

    id = Column(Integer, primary_key=True, index=True)
    assessment_id = Column(Integer, ForeignKey("risk_assessments.id", ondelete="CASCADE"), nullable=False, index=True)
    rule_code = Column(String(10), nullable=False)  # R1..R10
    points = Column(Integer, nullable=False)
    params_json = Column(Text, nullable=False)

    assessment = relationship("RiskAssessment", back_populates="reasons")

class ReviewCase(Base):
    __tablename__ = "review_cases"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="CASCADE"), unique=True, nullable=False)
    case_type = Column(String(20), nullable=False)  # 'hold_review', 'post_review'
    status = Column(String(20), nullable=False)  # 'open', 'escalated', 'closed'
    decision = Column(String(30), nullable=True)  # 'approved', 'rejected', 'false_alarm', 'confirmed_fraud'
    version = Column(Integer, default=1, nullable=False)
    assigned_reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("case_type IN ('hold_review', 'post_review')", name="check_case_type"),
        CheckConstraint("status IN ('open', 'escalated', 'closed')", name="check_case_status"),
        CheckConstraint("decision IS NULL OR decision IN ('approved', 'rejected', 'false_alarm', 'confirmed_fraud')", name="check_case_decision"),
        Index("idx_cases_status_created", "status", "created_at"),
    )

    transaction = relationship("Transaction", back_populates="review_case")
    assigned_reviewer = relationship("User", foreign_keys=[assigned_reviewer_id])
    actions = relationship("ReviewCaseAction", back_populates="case", cascade="all, delete-orphan")

class ReviewCaseAction(Base):
    __tablename__ = "review_case_actions"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("review_cases.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(30), nullable=False)  # 'approve', 'reject', 'escalate', 'mark_false_alarm', 'mark_confirmed_fraud'
    note = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    case = relationship("ReviewCase", back_populates="actions")
    actor = relationship("User", foreign_keys=[actor_id])

class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    actor_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(Integer, nullable=False)
    action = Column(String(50), nullable=False)
    safe_metadata_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        Index("idx_audit_entity", "entity_type", "entity_id"),
    )

    actor = relationship("User", foreign_keys=[actor_id])

class Budget(Base):
    __tablename__ = "budgets"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(50), nullable=True)  # null = overall monthly budget
    amount_paise = Column(Integer, nullable=False)
    period = Column(String(10), nullable=False)  # 'YYYY-MM'
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("amount_paise > 0", name="check_budget_amount_positive"),
        Index("idx_budget_user_period", "user_id", "period"),
    )

    user = relationship("User", back_populates="budgets")

class SavingsGoal(Base):
    __tablename__ = "savings_goals"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(100), nullable=False)
    target_paise = Column(Integer, nullable=False)
    current_paise = Column(Integer, default=0, nullable=False)
    target_date = Column(String(20), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        CheckConstraint("target_paise > 0", name="check_goal_target_positive"),
        CheckConstraint("current_paise >= 0", name="check_goal_current_non_negative"),
    )

    user = relationship("User", back_populates="savings_goals")

class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(20), nullable=False)  # 'budget', 'fraud', 'review'
    title_code = Column(String(100), nullable=False)
    params_json = Column(Text, nullable=False)
    related_transaction_id = Column(Integer, ForeignKey("transactions.id", ondelete="SET NULL"), nullable=True)
    dedupe_key = Column(String(150), nullable=False)
    read_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "dedupe_key", name="uq_user_dedupe_alert"),
        CheckConstraint("type IN ('budget', 'fraud', 'review')", name="check_alert_type"),
    )

    user = relationship("User", back_populates="alerts")
    transaction = relationship("Transaction")

class GuidanceItem(Base):
    __tablename__ = "guidance_items"

    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String(50), nullable=False)
    language = Column(String(10), default="en", nullable=False)  # 'en', 'hi'
    title = Column(String(150), nullable=False)
    body = Column(Text, nullable=False)
    source_label = Column(String(100), nullable=False)
    source_url = Column(String(255), nullable=True)
    last_verified = Column(String(20), nullable=False)

class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    key = Column(String(100), nullable=False)
    request_hash = Column(String(64), nullable=False)
    response_json = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_idempotency_key"),
    )
