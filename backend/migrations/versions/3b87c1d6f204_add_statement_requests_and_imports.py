"""add statement request workflow and idempotent CSV imports

Revision ID: 3b87c1d6f204
Revises: 7a91c2e3d405
Create Date: 2026-11-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3b87c1d6f204"
down_revision: Union[str, Sequence[str], None] = "7a91c2e3d405"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("import_fingerprint", sa.String(length=64), nullable=True))
        batch_op.create_unique_constraint(
            "uq_tx_user_import_fingerprint",
            ["user_id", "import_fingerprint"],
        )

    op.create_table(
        "statement_requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reviewed_by_id", sa.Integer(), nullable=True),
        sa.Column("review_note", sa.String(length=500), nullable=True),
        sa.CheckConstraint("status IN ('pending', 'approved', 'rejected')", name="check_statement_request_status"),
        sa.CheckConstraint("start_date <= end_date", name="check_statement_request_dates"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_statement_requests_id", "statement_requests", ["id"], unique=False)
    op.create_index("ix_statement_requests_user_id", "statement_requests", ["user_id"], unique=False)
    op.create_index("idx_statement_request_status", "statement_requests", ["status", "requested_at"], unique=False)


def downgrade() -> None:
    op.drop_index("idx_statement_request_status", table_name="statement_requests")
    op.drop_index("ix_statement_requests_user_id", table_name="statement_requests")
    op.drop_index("ix_statement_requests_id", table_name="statement_requests")
    op.drop_table("statement_requests")
    with op.batch_alter_table("transactions", schema=None) as batch_op:
        batch_op.drop_constraint("uq_tx_user_import_fingerprint", type_="unique")
        batch_op.drop_column("import_fingerprint")
