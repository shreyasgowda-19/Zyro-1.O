"""add manually tracked personal accounts

Revision ID: 7a91c2e3d405
Revises: 48b4197d4d1e
Create Date: 2026-11-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7a91c2e3d405"
down_revision: Union[str, Sequence[str], None] = "48b4197d4d1e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tracked_accounts",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("institution_name", sa.String(length=80), nullable=False),
        sa.Column("account_name", sa.String(length=50), nullable=False),
        sa.Column("account_type", sa.String(length=20), nullable=False),
        sa.Column("last_four", sa.String(length=4), nullable=True),
        sa.Column("reported_balance_paise", sa.Integer(), nullable=False),
        sa.Column("balance_as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint(
            "account_type IN ('savings', 'current', 'cash', 'other')",
            name="check_tracked_account_type",
        ),
        sa.CheckConstraint(
            "last_four IS NULL OR length(last_four) = 4",
            name="check_tracked_account_last_four",
        ),
        sa.CheckConstraint(
            "reported_balance_paise BETWEEN -1000000000000 AND 1000000000000",
            name="check_tracked_account_balance",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tracked_accounts_id", "tracked_accounts", ["id"], unique=False)
    op.create_index("ix_tracked_accounts_user_id", "tracked_accounts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_tracked_accounts_user_id", table_name="tracked_accounts")
    op.drop_index("ix_tracked_accounts_id", table_name="tracked_accounts")
    op.drop_table("tracked_accounts")
