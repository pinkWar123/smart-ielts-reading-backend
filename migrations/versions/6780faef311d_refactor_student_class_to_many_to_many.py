"""refactor student class to many to many

Revision ID: 6780faef311d
Revises: 5cbeb33460e3
Create Date: 2026-01-12 15:41:05.132221

"""

import json
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "6780faef311d"
down_revision: Union[str, Sequence[str], None] = "5cbeb33460e3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema: Create association table and migrate data."""
    # 1. Create class_students association table
    op.create_table(
        "class_students",
        sa.Column("class_id", sa.String(), nullable=False),
        sa.Column("student_id", sa.String(), nullable=False),
        sa.Column(
            "enrolled_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["class_id"], ["classes.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("class_id", "student_id"),
    )

    # 2. Migrate data from JSON column to association table
    connection = op.get_bind()

    # Fetch all classes with student_ids
    result = connection.execute(
        sa.text("SELECT id, student_ids FROM classes WHERE student_ids IS NOT NULL")
    )
    classes = result.fetchall()

    for class_id, student_ids_json in classes:
        if student_ids_json:
            # Parse JSON - handle both string and already-parsed formats
            try:
                if isinstance(student_ids_json, str):
                    student_ids = json.loads(student_ids_json)
                else:
                    student_ids = student_ids_json

                # Insert association records
                for student_id in student_ids:
                    if student_id:  # Skip empty strings
                        connection.execute(
                            sa.text(
                                "INSERT INTO class_students (class_id, student_id) VALUES (:class_id, :student_id)"
                            ),
                            {"class_id": class_id, "student_id": student_id},
                        )
            except (json.JSONDecodeError, TypeError):
                # Skip invalid JSON data
                continue

    # 3. Drop the old student_ids column
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.drop_column("student_ids")


def downgrade() -> None:
    """Downgrade schema: Restore JSON column and migrate data back."""
    # 1. Add student_ids column back to classes table
    with op.batch_alter_table("classes", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("student_ids", sa.JSON(), nullable=False, server_default="[]")
        )

    # 2. Migrate data back from association table to JSON column
    connection = op.get_bind()

    # Get all classes
    result = connection.execute(sa.text("SELECT DISTINCT class_id FROM class_students"))
    class_ids = [row[0] for row in result.fetchall()]

    for class_id in class_ids:
        # Get all students for this class
        student_result = connection.execute(
            sa.text("SELECT student_id FROM class_students WHERE class_id = :class_id"),
            {"class_id": class_id},
        )
        student_ids = [row[0] for row in student_result.fetchall()]

        # Update the JSON column
        connection.execute(
            sa.text("UPDATE classes SET student_ids = :ids WHERE id = :class_id"),
            {"ids": json.dumps(student_ids), "class_id": class_id},
        )

    # 3. Drop the association table
    op.drop_table("class_students")
