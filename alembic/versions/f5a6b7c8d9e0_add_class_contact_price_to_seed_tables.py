"""Add seed_class, contact_person, contact_phone, price to all seed tables

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-04-02 15:00:00.000000

The seed result pages show: Class, Contact Person, Price — none of these were
being captured. Also horti_seeds was missing crop_variety (varietyName field).

Changes (all three tables):
  - ADD seed_class        VARCHAR(200)  ← className
  - ADD contact_person    VARCHAR(300)  ← full_name
  - ADD contact_phone     VARCHAR(20)   ← user_phone
  - ADD price             VARCHAR(50)   ← price

horti_seeds only:
  - ADD crop_variety      VARCHAR(200)  ← varietyName
"""
from alembic import op
import sqlalchemy as sa

revision = "f5a6b7c8d9e0"
down_revision = "e4f5a6b7c8d9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ("agri_seeds", "horti_seeds", "season_seeds"):
        op.add_column(table, sa.Column("seed_class", sa.String(200), nullable=True), schema="seed")
        op.add_column(table, sa.Column("contact_person", sa.String(300), nullable=True), schema="seed")
        op.add_column(table, sa.Column("contact_phone", sa.String(20), nullable=True), schema="seed")
        op.add_column(table, sa.Column("price", sa.String(50), nullable=True), schema="seed")

    # horti_seeds also needs crop_variety (varietyName field in result)
    op.add_column("horti_seeds", sa.Column("crop_variety", sa.String(200), nullable=True), schema="seed")


def downgrade() -> None:
    op.drop_column("horti_seeds", "crop_variety", schema="seed")
    for table in ("agri_seeds", "horti_seeds", "season_seeds"):
        op.drop_column(table, "price", schema="seed")
        op.drop_column(table, "contact_phone", schema="seed")
        op.drop_column(table, "contact_person", schema="seed")
        op.drop_column(table, "seed_class", schema="seed")
