"""create users and transactions tables

Revision ID: 0001
Revises:
Create Date: 2026-10-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('username', sa.String(), nullable=True),
        sa.Column('hash_password', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    op.create_index('ix_users_id', 'users', ['id'], unique=False)

    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('amount', sa.Float(), nullable=True),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('date', sa.Date(), nullable=True),
        sa.Column('owner_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        'ix_transactions_id', 'transactions', ['id'], unique=False
    )


def downgrade() -> None:
    op.drop_index('ix_transactions_id', table_name='transactions')
    op.drop_table('transactions')
    op.drop_index('ix_users_id', table_name='users')
    op.drop_table('users')
