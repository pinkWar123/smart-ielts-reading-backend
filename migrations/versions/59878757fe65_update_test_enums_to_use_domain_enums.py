"""update_test_enums_to_use_domain_enums

Revision ID: 59878757fe65
Revises: 7d8ec5f13c61
Create Date: 2026-01-03 14:00:23.906606

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "59878757fe65"
down_revision: Union[str, Sequence[str], None] = "7d8ec5f13c61"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - SQLite compatible using batch operations."""
    # For SQLite, we need to use batch operations to modify columns
    with op.batch_alter_table("questions", schema=None) as batch_op:
        # SQLite stores enums as VARCHAR, so we just ensure the column exists
        # The enum constraint is handled at the application layer by SQLAlchemy
        batch_op.alter_column(
            "question_type",
            existing_type=sa.VARCHAR(length=20),
            type_=sa.VARCHAR(length=50),  # Increase size for longer enum values
            existing_nullable=False,
        )

        # Add foreign key constraint
        batch_op.create_foreign_key(
            "fk_questions_question_group_id",
            "question_groups",
            ["question_group_id"],
            ["id"],
        )


def downgrade() -> None:
    """Downgrade schema - SQLite compatible."""
    with op.batch_alter_table("questions", schema=None) as batch_op:
        # Drop the foreign key constraint
        batch_op.drop_constraint("fk_questions_question_group_id", type_="foreignkey")

        # Revert column type
        batch_op.alter_column(
            "question_type",
            existing_type=sa.VARCHAR(length=50),
            type_=sa.VARCHAR(length=20),
            existing_nullable=False,
        )
