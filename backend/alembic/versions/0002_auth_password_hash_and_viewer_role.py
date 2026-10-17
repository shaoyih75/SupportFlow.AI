"""auth password hash and viewer role

- users.password_hash (nullable: existing users have none until a password is set)
- workspace_members.role allows VIEWER
- workspace_members.status allows INVITED and SUSPENDED

Autogenerate only detected the new column. CHECK constraint changes are NOT detected
by `alembic revision --autogenerate`, so the four constraint ops below were written by hand.

Revision ID: 0002
Revises: 0001
Create Date: 2026-10-17 01:45:19.896991

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0002'
down_revision: Union[str, Sequence[str], None] = '0001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('password_hash', sa.String(length=255), nullable=True))

    op.drop_constraint(op.f('ck_workspace_members_role_valid'), 'workspace_members', type_='check')
    op.create_check_constraint(
        'role_valid', 'workspace_members', "role IN ('OWNER', 'MEMBER', 'VIEWER')"
    )
    op.drop_constraint(op.f('ck_workspace_members_status_valid'), 'workspace_members', type_='check')
    op.create_check_constraint(
        'status_valid', 'workspace_members', "status IN ('ACTIVE', 'INVITED', 'SUSPENDED', 'REMOVED')"
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Rows using the new values would violate the old constraints: map them first.
    # VIEWER -> MEMBER keeps read access; INVITED/SUSPENDED -> REMOVED keeps them locked out.
    op.execute("UPDATE workspace_members SET role = 'MEMBER' WHERE role = 'VIEWER'")
    op.execute("UPDATE workspace_members SET status = 'REMOVED' WHERE status IN ('INVITED', 'SUSPENDED')")

    op.drop_constraint(op.f('ck_workspace_members_status_valid'), 'workspace_members', type_='check')
    op.create_check_constraint('status_valid', 'workspace_members', "status IN ('ACTIVE', 'REMOVED')")
    op.drop_constraint(op.f('ck_workspace_members_role_valid'), 'workspace_members', type_='check')
    op.create_check_constraint('role_valid', 'workspace_members', "role IN ('OWNER', 'MEMBER')")

    op.drop_column('users', 'password_hash')
