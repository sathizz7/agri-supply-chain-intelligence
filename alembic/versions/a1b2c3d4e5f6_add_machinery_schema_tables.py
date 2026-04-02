"""Add machinery schema: tractor_owners, woman_mechanics, drone_owners

Revision ID: a1b2c3d4e5f6
Revises: d3f7a2b1e9c4
Create Date: 2026-04-02 10:00:00.000000

Creates a new 'machinery' PostgreSQL schema with 3 tables:
  machinery.tractor_owners    — Private Tractor Owner details
  machinery.woman_mechanics   — Woman Mechanics (Magalir Thittam) details
  machinery.drone_owners      — Private Agriculture Drone Owner details

All tables FK → public.scrape_runs.
Tractor and woman_mechanics iterate district→block; drone is district-only.
"""
from alembic import op
import sqlalchemy as sa

revision = "a1b2c3d4e5f6"
down_revision = "d3f7a2b1e9c4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS machinery")

    # ------------------------------------------------------------------
    # machinery.tractor_owners
    # ------------------------------------------------------------------
    op.create_table(
        "tractor_owners",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer,
                  sa.ForeignKey("public.scrape_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("owner_name", sa.String(300), nullable=True),
        sa.Column("mobile_number", sa.String(20), nullable=True),
        sa.Column("registration_no", sa.String(100), nullable=True),
        sa.Column("maker_model", sa.String(200), nullable=True),
        sa.Column("machinery_name", sa.String(200), nullable=True),
        sa.Column("implement_name", sa.String(300), nullable=True),
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "district_code", "block_code", "owner_name", "machinery_name", "scrape_date",
            name="uq_tractor_owner_machine_date",
        ),
        schema="machinery",
    )
    op.create_index("idx_tractor_date_district", "tractor_owners",
                    ["scrape_date", "district_code"], schema="machinery")
    op.create_index("idx_tractor_block", "tractor_owners",
                    ["block_code"], schema="machinery")
    op.create_index("idx_tractor_run", "tractor_owners",
                    ["scrape_run_id"], schema="machinery")

    # ------------------------------------------------------------------
    # machinery.woman_mechanics
    # ------------------------------------------------------------------
    op.create_table(
        "woman_mechanics",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer,
                  sa.ForeignKey("public.scrape_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("mechanic_name", sa.String(300), nullable=True),  # WomenPLF
        sa.Column("mobile_number", sa.String(20), nullable=True),
        sa.Column("machinery_name", sa.String(200), nullable=True),
        sa.Column("implement_name", sa.String(300), nullable=True),
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "district_code", "block_code", "mechanic_name", "machinery_name", "scrape_date",
            name="uq_woman_mechanic_machine_date",
        ),
        schema="machinery",
    )
    op.create_index("idx_wm_date_district", "woman_mechanics",
                    ["scrape_date", "district_code"], schema="machinery")
    op.create_index("idx_wm_block", "woman_mechanics",
                    ["block_code"], schema="machinery")
    op.create_index("idx_wm_run", "woman_mechanics",
                    ["scrape_run_id"], schema="machinery")

    # ------------------------------------------------------------------
    # machinery.drone_owners  (district-only — no block columns)
    # ------------------------------------------------------------------
    op.create_table(
        "drone_owners",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer,
                  sa.ForeignKey("public.scrape_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("owner_name", sa.String(300), nullable=True),     # ownerName
        sa.Column("mobile_number", sa.String(20), nullable=True),
        sa.Column("drone_count", sa.Integer, nullable=True),        # NoOfDrone
        sa.Column("implement_name", sa.String(300), nullable=True), # implements
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "district_code", "owner_name", "scrape_date",
            name="uq_drone_owner_date",
        ),
        schema="machinery",
    )
    op.create_index("idx_drone_date_district", "drone_owners",
                    ["scrape_date", "district_code"], schema="machinery")
    op.create_index("idx_drone_run", "drone_owners",
                    ["scrape_run_id"], schema="machinery")


def downgrade() -> None:
    op.drop_table("drone_owners", schema="machinery")
    op.drop_table("woman_mechanics", schema="machinery")
    op.drop_table("tractor_owners", schema="machinery")
    op.execute("DROP SCHEMA IF EXISTS machinery")
