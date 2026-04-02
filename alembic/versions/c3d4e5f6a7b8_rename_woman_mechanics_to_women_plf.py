"""Rename woman_mechanics to women_plf with corrected schema

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-02 12:00:00.000000

The woman_mechanics table had incorrect field mapping — mobile, address, and
machinery list were all NULL. The data is actually Women's PLF (Producer
Livelihood Federation) groups that hire out farm implements, not individual
mechanics.

Changes:
  - DROP machinery.woman_mechanics (all data is nulls in new columns anyway)
  - CREATE machinery.women_plf with correct columns:
      plf_name       ← WomenPLF
      mobile_number  ← PLF_President (was MobileNumber — field doesn't exist)
      contact_address← ContactAddress (new)
      machinery_procured ← MachineryProcurred (replaces implement_name)
      available_count← MachineryAvailable (new)
      panchayat      ← panchayat (new)
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b8"
down_revision = "b2c3d4e5f6a7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the old incorrectly-mapped table
    op.drop_table("woman_mechanics", schema="machinery")

    # Create correctly mapped table
    op.create_table(
        "women_plf",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer,
                  sa.ForeignKey("public.scrape_runs.id", ondelete="SET NULL"),
                  nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("plf_name", sa.String(300), nullable=True),          # WomenPLF
        sa.Column("mobile_number", sa.String(20), nullable=True),      # PLF_President
        sa.Column("contact_address", sa.Text, nullable=True),          # ContactAddress
        sa.Column("machinery_procured", sa.Text, nullable=True),       # MachineryProcurred
        sa.Column("available_count", sa.String(20), nullable=True),    # MachineryAvailable
        sa.Column("panchayat", sa.String(200), nullable=True),         # panchayat
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint(
            "district_code", "block_code", "plf_name", "scrape_date",
            name="uq_women_plf_date",
        ),
        schema="machinery",
    )
    op.create_index("idx_wplf_date_district", "women_plf",
                    ["scrape_date", "district_code"], schema="machinery")
    op.create_index("idx_wplf_block", "women_plf",
                    ["block_code"], schema="machinery")
    op.create_index("idx_wplf_run", "women_plf",
                    ["scrape_run_id"], schema="machinery")


def downgrade() -> None:
    op.drop_table("women_plf", schema="machinery")
    op.create_table(
        "woman_mechanics",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("scrape_run_id", sa.Integer, nullable=True),
        sa.Column("district_code", sa.String(20), nullable=False),
        sa.Column("district_name", sa.String(200), nullable=True),
        sa.Column("block_code", sa.String(20), nullable=False),
        sa.Column("block_name", sa.String(200), nullable=True),
        sa.Column("mechanic_name", sa.String(300), nullable=True),
        sa.Column("mobile_number", sa.String(20), nullable=True),
        sa.Column("machinery_name", sa.String(200), nullable=True),
        sa.Column("implement_name", sa.String(300), nullable=True),
        sa.Column("scrape_date", sa.Date, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        schema="machinery",
    )
