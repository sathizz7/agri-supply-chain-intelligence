"""finalize_checkpoint_schema

Drop legacy district_code/block_code from scrape_checkpoints.
Make parser_id and work_unit_key NOT NULL.
Add unique constraint on (scrape_run_id, parser_id, work_unit_key).

Revision ID: 530819517819
Revises: 734a2e0f842d
Create Date: 2026-03-31 10:43:23.277784

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '530819517819'
down_revision: Union[str, Sequence[str], None] = '734a2e0f842d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop old unique constraint
    op.drop_constraint('uq_checkpoint_run_dist_block', 'scrape_checkpoints', type_='unique')

    # Drop legacy columns
    op.drop_column('scrape_checkpoints', 'district_code')
    op.drop_column('scrape_checkpoints', 'block_code')

    # Backfill legacy rows with unique keys, then deduplicate
    op.execute("UPDATE scrape_checkpoints SET parser_id = 'legacy' WHERE parser_id IS NULL")
    op.execute("""
        UPDATE scrape_checkpoints SET work_unit_key = 'legacy:' || id::text
        WHERE work_unit_key IS NULL
    """)
    # Remove any remaining duplicates (keep the row with the highest id)
    op.execute("""
        DELETE FROM scrape_checkpoints
        WHERE id NOT IN (
            SELECT MAX(id) FROM scrape_checkpoints
            GROUP BY scrape_run_id, parser_id, work_unit_key
        )
    """)

    op.alter_column('scrape_checkpoints', 'parser_id',
                     existing_type=sa.VARCHAR(length=50),
                     nullable=False)
    op.alter_column('scrape_checkpoints', 'work_unit_key',
                     existing_type=sa.VARCHAR(length=200),
                     nullable=False)

    # Add new unique constraint
    op.create_unique_constraint(
        'uq_checkpoint_run_parser_key',
        'scrape_checkpoints',
        ['scrape_run_id', 'parser_id', 'work_unit_key'],
    )


def downgrade() -> None:
    op.drop_constraint('uq_checkpoint_run_parser_key', 'scrape_checkpoints', type_='unique')

    op.alter_column('scrape_checkpoints', 'work_unit_key',
                     existing_type=sa.VARCHAR(length=200),
                     nullable=True)
    op.alter_column('scrape_checkpoints', 'parser_id',
                     existing_type=sa.VARCHAR(length=50),
                     nullable=True)

    op.add_column('scrape_checkpoints', sa.Column('block_code', sa.VARCHAR(length=20), nullable=True))
    op.add_column('scrape_checkpoints', sa.Column('district_code', sa.VARCHAR(length=20), nullable=True))

    op.create_unique_constraint(
        'uq_checkpoint_run_dist_block',
        'scrape_checkpoints',
        ['scrape_run_id', 'district_code', 'block_code'],
    )
