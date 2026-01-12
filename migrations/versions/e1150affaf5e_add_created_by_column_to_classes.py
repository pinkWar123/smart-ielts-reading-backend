"""add_created_by_column_to_classes

Revision ID: e1150affaf5e
Revises: 415c273bd7f0
Create Date: 2026-01-12 21:21:59.609328

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1150affaf5e"
down_revision: Union[str, Sequence[str], None] = "415c273bd7f0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add created_by column to classes table.

    For existing classes, use the first teacher as the creator.
    """
    # 1. Add created_by column as nullable first
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_by", sa.String(), nullable=True))

    # 2. Populate created_by for existing classes using first teacher
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT DISTINCT class_id FROM class_teachers"))
    class_ids = [row[0] for row in result.fetchall()]

    for class_id in class_ids:
        # Get first teacher for this class
        teacher_result = connection.execute(
            sa.text(
                "SELECT teacher_id FROM class_teachers WHERE class_id = :class_id LIMIT 1"
            ),
            {"class_id": class_id},
        )
        teacher_id = teacher_result.scalar()
        if teacher_id:
            connection.execute(
                sa.text(
                    "UPDATE classes SET created_by = :teacher_id WHERE id = :class_id"
                ),
                {"teacher_id": teacher_id, "class_id": class_id},
            )

    # 3. Make created_by NOT NULL and add foreign key constraint
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.alter_column("created_by", nullable=False)
        batch_op.create_foreign_key(
            "fk_classes_created_by_users", "users", ["created_by"], ["id"]
        )


def downgrade() -> None:
    """Remove created_by column from classes table."""
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.drop_constraint("fk_classes_created_by_users", type_="foreignkey")
        batch_op.drop_column("created_by")
