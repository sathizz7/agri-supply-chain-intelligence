"""restore_bilingual_name_columns_name_en_before_name_ta

Revision ID: 77eae4d502b9
Revises: bbe3617efcd2
Create Date: 2026-03-31 15:22:43.301803

Restores bilingual name columns (name_en, name_ta) for districts, blocks, dealers.
Column order: name_en (English, primary) BEFORE name_ta (Tamil, fallback).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '77eae4d502b9'
down_revision: Union[str, Sequence[str], None] = 'bbe3617efcd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Restore bilingual schema: name_en (English) before name_ta (Tamil)."""
    # Districts: rename name to name_en, keep name_ta
    op.add_column('districts', sa.Column('name_en', sa.String(length=200), nullable=True))
    op.alter_column('districts', 'name_ta',
               existing_type=sa.VARCHAR(length=200),
               nullable=True)
    op.drop_column('districts', 'name')

    # Blocks: rename name to name_en, keep name_ta
    op.add_column('blocks', sa.Column('name_en', sa.String(length=200), nullable=True))
    op.alter_column('blocks', 'name_ta',
               existing_type=sa.VARCHAR(length=200),
               nullable=True)
    op.drop_column('blocks', 'name')

    # Dealers: rename name to name_en (name_ta already exists from earlier migration)
    op.add_column('dealers', sa.Column('name_en', sa.String(length=300), nullable=True))
    op.drop_column('dealers', 'name')


def downgrade() -> None:
    """Revert to single 'name' column (English only)."""
    # Districts: revert to single name column
    op.add_column('districts', sa.Column('name', sa.VARCHAR(length=200), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.alter_column('districts', 'name_ta',
               existing_type=sa.VARCHAR(length=200),
               nullable=False)
    op.drop_column('districts', 'name_en')

    # Blocks: revert to single name column
    op.add_column('blocks', sa.Column('name', sa.VARCHAR(length=200), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.alter_column('blocks', 'name_ta',
               existing_type=sa.VARCHAR(length=200),
               nullable=False)
    op.drop_column('blocks', 'name_en')

    # Dealers: revert to single name column (keep name_ta for safety)
    op.add_column('dealers', sa.Column('name', sa.VARCHAR(length=300), server_default=sa.text("''::character varying"), autoincrement=False, nullable=False))
    op.drop_column('dealers', 'name_en')
