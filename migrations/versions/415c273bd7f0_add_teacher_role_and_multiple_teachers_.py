"""add teacher role and multiple teachers per class

Revision ID: 415c273bd7f0
Revises: 6780faef311d
Create Date: 2026-01-12 16:50:47.198325

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "415c273bd7f0"
down_revision: Union[str, Sequence[str], None] = "6780faef311d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Add teacher role and create class_teachers table"""
    # 1. Create class_teachers association table
    op.create_table(
        "class_teachers",
        sa.Column("class_id", sa.String(), nullable=False),
        sa.Column("teacher_id", sa.String(), nullable=False),
        sa.Column(
            "assigned_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("class_id", "teacher_id"),
    )

    # 2. Migrate existing teacher_id to association table
    connection = op.get_bind()
    result = connection.execute(
        sa.text("SELECT id, teacher_id FROM classes WHERE teacher_id IS NOT NULL")
    )
    classes = result.fetchall()

    for class_id, teacher_id in classes:
        if teacher_id:
            connection.execute(
                sa.text(
                    "INSERT INTO class_teachers (class_id, teacher_id) VALUES (:class_id, :teacher_id)"
                ),
                {"class_id": class_id, "teacher_id": teacher_id},
            )

    # 3. Drop old teacher_id column and index
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.drop_index("ix_classes_teacher_id")
        batch_op.drop_column("teacher_id")


def downgrade() -> None:
    """Downgrade schema: Restore single teacher_id column"""
    # 1. Add teacher_id column back to classes table
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.add_column(sa.Column("teacher_id", sa.String(), nullable=True))
        batch_op.create_index("ix_classes_teacher_id", ["teacher_id"])

    # 2. Migrate first teacher from association table back to teacher_id
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
                    "UPDATE classes SET teacher_id = :teacher_id WHERE id = :class_id"
                ),
                {"teacher_id": teacher_id, "class_id": class_id},
            )

    # 3. Make teacher_id non-nullable after migration
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.alter_column("teacher_id", nullable=False)

    # 4. Drop the association table
    op.drop_table("class_teachers")
