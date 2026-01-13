"""Replace users with user_profiles for Neon Auth integration

Revision ID: b3c7d8e9f012
Revises: 4914e5ef88b4
Create Date: 2026-01-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b3c7d8e9f012'
down_revision: Union[str, Sequence[str], None] = '4914e5ef88b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Replace users table with user_profiles for Neon Auth integration."""

    # 1. Drop existing foreign key constraints
    op.drop_constraint('children_user_id_fkey', 'children', type_='foreignkey')
    op.drop_constraint('subscriptions_user_id_fkey', 'subscriptions', type_='foreignkey')

    # 2. Truncate dependent tables (Clean Start approach)
    op.execute('TRUNCATE TABLE devices CASCADE')
    op.execute('TRUNCATE TABLE children CASCADE')
    op.execute('TRUNCATE TABLE subscriptions CASCADE')

    # 3. Drop users table
    op.drop_index(op.f('ix_users_is_active'), table_name='users')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')

    # 4. Create user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column(
            'user_id',
            sa.UUID(),
            nullable=False,
            comment='Neon Auth user ID (from JWT sub claim)',
        ),
        sa.Column(
            'phone',
            sa.String(length=20),
            nullable=True,
            comment='Optional phone number',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
            comment='Timestamp when the record was created',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text('now()'),
            comment='Timestamp when the record was last updated',
        ),
        sa.PrimaryKeyConstraint('user_id'),
    )

    # 5. Re-create foreign key constraints pointing to user_profiles
    op.create_foreign_key(
        'children_user_id_fkey',
        'children',
        'user_profiles',
        ['user_id'],
        ['user_id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'subscriptions_user_id_fkey',
        'subscriptions',
        'user_profiles',
        ['user_id'],
        ['user_id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    """Revert to users table."""

    # 1. Drop foreign key constraints
    op.drop_constraint('children_user_id_fkey', 'children', type_='foreignkey')
    op.drop_constraint('subscriptions_user_id_fkey', 'subscriptions', type_='foreignkey')

    # 2. Drop user_profiles table
    op.drop_table('user_profiles')

    # 3. Recreate users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(), nullable=False, comment='Unique user identifier'),
        sa.Column(
            'email',
            sa.String(length=255),
            nullable=False,
            comment='User email address (unique, used for login)',
        ),
        sa.Column(
            'password_hash',
            sa.String(length=255),
            nullable=False,
            comment='Bcrypt hashed password',
        ),
        sa.Column(
            'name',
            sa.String(length=100),
            nullable=False,
            comment="Parent's full name",
        ),
        sa.Column(
            'phone', sa.String(length=20), nullable=True, comment='Optional phone number'
        ),
        sa.Column(
            'is_active',
            sa.Boolean(),
            nullable=False,
            comment='Account active status (soft delete flag)',
        ),
        sa.Column(
            'email_verified',
            sa.Boolean(),
            nullable=False,
            comment='Email verification status',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            comment='Timestamp when the record was created',
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            comment='Timestamp when the record was last updated',
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_is_active'), 'users', ['is_active'], unique=False)

    # 4. Recreate foreign key constraints pointing to users
    op.create_foreign_key(
        'children_user_id_fkey',
        'children',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'subscriptions_user_id_fkey',
        'subscriptions',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE',
    )
