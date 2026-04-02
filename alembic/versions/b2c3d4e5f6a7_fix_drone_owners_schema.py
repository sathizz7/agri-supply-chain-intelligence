"""Fix drone_owners table: add block columns, drop drone_count and implement_name

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-02 11:30:00.000000

The drone API (loadDrone/{district_id}) returns Block and BlockCode per record —
not NoOfDrone or implements as originally assumed. This migration corrects the schema:
  - DROP: drone_count (NoOfDrone field doesn't exist in API)
  - DROP: implement_name (implements field doesn't exist in API)
  - ADD: block_code VARCHAR(20)
  - ADD: block_name VARCHAR(200)
  - DROP old UNIQUE constraint (district_code, owner_name, scrape_date)
  - ADD new UNIQUE constraint (district_code, block_code, owner_name, scrape_date)
  - ADD index on block_code
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old unique constraint
    op.drop_constraint("uq_drone_owner_date", "drone_owners", schema="machinery")

    # Drop the two columns that don't exist in the real API
    op.drop_column("drone_owners", "drone_count", schema="machinery")
    op.drop_column("drone_owners", "implement_name", schema="machinery")

    # Add block columns (API returns Block/BlockCode per record)
    op.add_column("drone_owners",
        sa.Column("block_code", sa.String(20), nullable=True),
        schema="machinery",
    )
    op.add_column("drone_owners",
        sa.Column("block_name", sa.String(200), nullable=True),
        schema="machinery",
    )

    # Add index on block_code
    op.create_index("idx_drone_block", "drone_owners", ["block_code"], schema="machinery")

    # Recreate unique constraint with block_code
    op.create_unique_constraint(
        "uq_drone_owner_date",
        "drone_owners",
        ["district_code", "block_code", "owner_name", "scrape_date"],
        schema="machinery",
    )


def downgrade() -> None:
    op.drop_constraint("uq_drone_owner_date", "drone_owners", schema="machinery")
    op.drop_index("idx_drone_block", "drone_owners", schema="machinery")
    op.drop_column("drone_owners", "block_name", schema="machinery")
    op.drop_column("drone_owners", "block_code", schema="machinery")
    op.add_column("drone_owners",
        sa.Column("implement_name", sa.String(300), nullable=True),
        schema="machinery",
    )
    op.add_column("drone_owners",
        sa.Column("drone_count", sa.Integer, nullable=True),
        schema="machinery",
    )
    op.create_unique_constraint(
        "uq_drone_owner_date",
        "drone_owners",
        ["district_code", "owner_name", "scrape_date"],
        schema="machinery",
    )
