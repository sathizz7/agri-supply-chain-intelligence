"""schema segregation: move tables to fertilizer and seed schemas

Revision ID: d3f7a2b1e9c4
Revises: c4e5d1f2a8b3
Create Date: 2026-04-01 17:00:00.000000

Moves domain-specific tables out of public into named schemas:
  public     → stays: districts, blocks, scrape_runs, scrape_checkpoints,
                       scrape_anomalies, section_metadata
  fertilizer → moved: dealers, fertilizer_stock, fertilizer_prices
  seed       → moved: seed_stocks

Also fixes seed_stocks UNIQUE constraint to include `season` column,
preventing cross-season collisions for the same crop/agency in the same block.

Note: PostgreSQL SET SCHEMA preserves indexes, NOT NULL, and check constraints
but drops all FK constraints that reference the moved table. We drop FKs before
moving, then recreate them with the new schema-qualified names.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd3f7a2b1e9c4'
down_revision: Union[str, Sequence[str], None] = 'c4e5d1f2a8b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # -------------------------------------------------------------------------
    # 1. Create new schemas
    # -------------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS fertilizer")
    op.execute("CREATE SCHEMA IF NOT EXISTS seed")

    # -------------------------------------------------------------------------
    # 2. Drop FK constraints before moving tables
    #    (PostgreSQL drops FKs when table schema changes)
    # -------------------------------------------------------------------------

    # dealers → blocks FK (will be recreated as public.blocks after move)
    op.drop_constraint("dealers_block_id_fkey", "dealers", type_="foreignkey")

    # fertilizer_stock → dealers FK (dealers not yet moved, so still public.dealers)
    op.drop_constraint("fertilizer_stock_dealer_id_fkey", "fertilizer_stock", type_="foreignkey")
    op.drop_constraint("fertilizer_stock_scrape_run_id_fkey", "fertilizer_stock", type_="foreignkey")

    # fertilizer_prices → scrape_runs FK
    op.drop_constraint("fertilizer_prices_scrape_run_id_fkey", "fertilizer_prices", type_="foreignkey")

    # seed_stocks → scrape_runs FK
    op.drop_constraint("seed_stocks_scrape_run_id_fkey", "seed_stocks", type_="foreignkey")

    # -------------------------------------------------------------------------
    # 3. Drop old seed UNIQUE constraint (will recreate with season column)
    # -------------------------------------------------------------------------
    op.drop_constraint("uq_seed_block_crop_agency_date", "seed_stocks", type_="unique")

    # -------------------------------------------------------------------------
    # 4. Move tables to their new schemas
    # -------------------------------------------------------------------------
    op.execute("ALTER TABLE public.dealers SET SCHEMA fertilizer")
    op.execute("ALTER TABLE public.fertilizer_stock SET SCHEMA fertilizer")
    op.execute("ALTER TABLE public.fertilizer_prices SET SCHEMA fertilizer")
    op.execute("ALTER TABLE public.seed_stocks SET SCHEMA seed")

    # -------------------------------------------------------------------------
    # 5. Recreate FK constraints with schema-qualified references
    # -------------------------------------------------------------------------

    # fertilizer.dealers → public.blocks
    op.create_foreign_key(
        "dealers_block_id_fkey",
        "dealers", "blocks",
        ["block_id"], ["id"],
        source_schema="fertilizer",
        referent_schema="public",
    )

    # fertilizer.fertilizer_stock → fertilizer.dealers
    op.create_foreign_key(
        "fertilizer_stock_dealer_id_fkey",
        "fertilizer_stock", "dealers",
        ["dealer_id"], ["id"],
        source_schema="fertilizer",
        referent_schema="fertilizer",
    )

    # fertilizer.fertilizer_stock → public.scrape_runs
    op.create_foreign_key(
        "fertilizer_stock_scrape_run_id_fkey",
        "fertilizer_stock", "scrape_runs",
        ["scrape_run_id"], ["id"],
        source_schema="fertilizer",
        referent_schema="public",
    )

    # fertilizer.fertilizer_prices → public.scrape_runs
    op.create_foreign_key(
        "fertilizer_prices_scrape_run_id_fkey",
        "fertilizer_prices", "scrape_runs",
        ["scrape_run_id"], ["id"],
        source_schema="fertilizer",
        referent_schema="public",
    )

    # seed.seed_stocks → public.scrape_runs
    op.create_foreign_key(
        "seed_stocks_scrape_run_id_fkey",
        "seed_stocks", "scrape_runs",
        ["scrape_run_id"], ["id"],
        source_schema="seed",
        referent_schema="public",
    )

    # -------------------------------------------------------------------------
    # 6. Recreate seed UNIQUE constraint including season column
    # -------------------------------------------------------------------------
    op.create_unique_constraint(
        "uq_seed_block_crop_agency_season_date",
        "seed_stocks",
        ["block_code", "crop_name", "crop_variety", "agency_name",
         "source_type", "season", "scrape_date"],
        schema="seed",
    )


def downgrade() -> None:
    # -------------------------------------------------------------------------
    # Reverse: drop new UNIQUE, drop new FKs, move tables back to public,
    # recreate original FKs and original UNIQUE
    # -------------------------------------------------------------------------

    # Drop new seed UNIQUE
    op.drop_constraint("uq_seed_block_crop_agency_season_date", "seed_stocks",
                       schema="seed", type_="unique")

    # Drop new FKs
    op.drop_constraint("dealers_block_id_fkey", "dealers",
                       schema="fertilizer", type_="foreignkey")
    op.drop_constraint("fertilizer_stock_dealer_id_fkey", "fertilizer_stock",
                       schema="fertilizer", type_="foreignkey")
    op.drop_constraint("fertilizer_stock_scrape_run_id_fkey", "fertilizer_stock",
                       schema="fertilizer", type_="foreignkey")
    op.drop_constraint("fertilizer_prices_scrape_run_id_fkey", "fertilizer_prices",
                       schema="fertilizer", type_="foreignkey")
    op.drop_constraint("seed_stocks_scrape_run_id_fkey", "seed_stocks",
                       schema="seed", type_="foreignkey")

    # Move tables back to public
    op.execute("ALTER TABLE fertilizer.dealers SET SCHEMA public")
    op.execute("ALTER TABLE fertilizer.fertilizer_stock SET SCHEMA public")
    op.execute("ALTER TABLE fertilizer.fertilizer_prices SET SCHEMA public")
    op.execute("ALTER TABLE seed.seed_stocks SET SCHEMA public")

    # Recreate original FKs in public schema
    op.create_foreign_key(
        "dealers_block_id_fkey", "dealers", "blocks", ["block_id"], ["id"]
    )
    op.create_foreign_key(
        "fertilizer_stock_dealer_id_fkey", "fertilizer_stock", "dealers",
        ["dealer_id"], ["id"]
    )
    op.create_foreign_key(
        "fertilizer_stock_scrape_run_id_fkey", "fertilizer_stock", "scrape_runs",
        ["scrape_run_id"], ["id"]
    )
    op.create_foreign_key(
        "fertilizer_prices_scrape_run_id_fkey", "fertilizer_prices", "scrape_runs",
        ["scrape_run_id"], ["id"]
    )
    op.create_foreign_key(
        "seed_stocks_scrape_run_id_fkey", "seed_stocks", "scrape_runs",
        ["scrape_run_id"], ["id"]
    )

    # Recreate original seed UNIQUE (without season)
    op.create_unique_constraint(
        "uq_seed_block_crop_agency_date",
        "seed_stocks",
        ["block_code", "crop_name", "crop_variety", "agency_name",
         "source_type", "scrape_date"],
    )

    # Drop schemas (only if empty)
    op.execute("DROP SCHEMA IF EXISTS fertilizer")
    op.execute("DROP SCHEMA IF EXISTS seed")
