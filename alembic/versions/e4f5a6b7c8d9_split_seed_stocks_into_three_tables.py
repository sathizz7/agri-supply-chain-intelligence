"""Split seed_stocks into three separate tables: agri_seeds, horti_seeds, season_seeds

Revision ID: e4f5a6b7c8d9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-02 13:00:00.000000

The single seed.seed_stocks table used a source_type discriminator column to store
all three subsections in one place. This caused:
  - season column NULL for agri/horti rows
  - horti stock_type/input_name crammed into crop_name/crop_variety (wrong semantics)

Changes:
  - DROP seed.seed_stocks
  - CREATE seed.agri_seeds   (crop_name, crop_variety, agency_name)
  - CREATE seed.horti_seeds  (stock_type, input_name, agency_name)
  - CREATE seed.season_seeds (season NOT NULL, crop_name, crop_variety, agency_name)
"""
from alembic import op
import sqlalchemy as sa

revision = "e4f5a6b7c8d9"
down_revision = "c3d4e5f6a7b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_table("seed_stocks", schema="seed")

    # --- agri_seeds ---
    op.create_table(
        "agri_seeds",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer,
                  sa.ForeignKey("public.scrape_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("crop_name", sa.String(200), nullable=False),
        sa.Column("crop_variety", sa.String(200), nullable=True),
        sa.Column("agency_name", sa.String(300), nullable=True),
        sa.Column("quantity_available", sa.Float, nullable=True),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "block_code", "crop_name", "crop_variety", "agency_name", "scrape_date",
            name="uq_agri_seed_date",
        ),
        schema="seed",
    )
    op.create_index("idx_agri_date_block", "agri_seeds", ["scrape_date", "block_code"], schema="seed")
    op.create_index("idx_agri_block", "agri_seeds", ["block_code"], schema="seed")
    op.create_index("idx_agri_run", "agri_seeds", ["scrape_run_id"], schema="seed")

    # --- horti_seeds ---
    op.create_table(
        "horti_seeds",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer,
                  sa.ForeignKey("public.scrape_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("stock_type", sa.String(200), nullable=True),   # e.g. "Vegetable Seeds"
        sa.Column("input_name", sa.String(300), nullable=True),   # e.g. "Tomato - CO3"
        sa.Column("agency_name", sa.String(300), nullable=True),
        sa.Column("quantity_available", sa.Float, nullable=True),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "block_code", "stock_type", "input_name", "agency_name", "scrape_date",
            name="uq_horti_seed_date",
        ),
        schema="seed",
    )
    op.create_index("idx_horti_date_block", "horti_seeds", ["scrape_date", "block_code"], schema="seed")
    op.create_index("idx_horti_block", "horti_seeds", ["block_code"], schema="seed")
    op.create_index("idx_horti_run", "horti_seeds", ["scrape_run_id"], schema="seed")

    # --- season_seeds ---
    op.create_table(
        "season_seeds",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer,
                  sa.ForeignKey("public.scrape_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("season", sa.String(100), nullable=False),      # e.g. "Kharif", "Rabi"
        sa.Column("crop_name", sa.String(200), nullable=False),
        sa.Column("crop_variety", sa.String(200), nullable=True),
        sa.Column("agency_name", sa.String(300), nullable=True),
        sa.Column("quantity_available", sa.Float, nullable=True),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "block_code", "season", "crop_name", "crop_variety", "agency_name", "scrape_date",
            name="uq_season_seed_date",
        ),
        schema="seed",
    )
    op.create_index("idx_season_date_block", "season_seeds", ["scrape_date", "block_code"], schema="seed")
    op.create_index("idx_season_block", "season_seeds", ["block_code"], schema="seed")
    op.create_index("idx_season_season", "season_seeds", ["season"], schema="seed")
    op.create_index("idx_season_run", "season_seeds", ["scrape_run_id"], schema="seed")


def downgrade() -> None:
    op.drop_table("season_seeds", schema="seed")
    op.drop_table("horti_seeds", schema="seed")
    op.drop_table("agri_seeds", schema="seed")

    op.create_table(
        "seed_stocks",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer, nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("source_type", sa.String(20), nullable=False),
        sa.Column("crop_name", sa.String(200), nullable=False),
        sa.Column("crop_variety", sa.String(200), nullable=True),
        sa.Column("agency_name", sa.String(300), nullable=True),
        sa.Column("quantity_available", sa.Float, nullable=True),
        sa.Column("unit", sa.String(20), nullable=True),
        sa.Column("season", sa.String(100), nullable=True),
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="seed",
    )
