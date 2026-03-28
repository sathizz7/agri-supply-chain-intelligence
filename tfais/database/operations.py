"""
Database operations: upserts, inserts, and query helpers.

All functions accept a SQLAlchemy Session and return ORM objects.
The caller is responsible for committing (typically via get_session() context manager).
"""
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from tfais.database.models import (
    Block,
    Dealer,
    District,
    FertilizerStock,
    ScrapeCheckpoint,
    ScrapeRun,
)
from tfais.parser.card_parser import DealerRecord

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# District
# ---------------------------------------------------------------------------

def upsert_district(session: Session, code: str, name_ta: str) -> District:
    """Insert or update a district record. Returns the persisted District object."""
    district = session.scalar(select(District).where(District.code == code))
    if district is None:
        district = District(code=code, name_ta=name_ta)
        session.add(district)
        session.flush()
        log.debug(f"Inserted district: {code} / {name_ta}")
    else:
        district.name_ta = name_ta
    return district


# ---------------------------------------------------------------------------
# Block
# ---------------------------------------------------------------------------

def upsert_block(
    session: Session,
    code: str,
    name_ta: str,
    district_id: int,
) -> Block:
    """Insert or update a block record."""
    block = session.scalar(
        select(Block).where(Block.code == code, Block.district_id == district_id)
    )
    if block is None:
        block = Block(code=code, name_ta=name_ta, district_id=district_id)
        session.add(block)
        session.flush()
        log.debug(f"Inserted block: {code} / {name_ta}")
    else:
        block.name_ta = name_ta
    return block


# ---------------------------------------------------------------------------
# Dealer
# ---------------------------------------------------------------------------

def upsert_dealer(
    session: Session,
    dealer_code: str,
    name_ta: str,
    address: str,
    contact: str,
    block_id: int,
) -> Dealer:
    """
    Upsert dealer by (dealer_code, block_id) — the canonical dedup key.
    Empty dealer_code is allowed (partial unique index handles it in DB).
    Never uses license number (not visible on result cards).
    """
    if dealer_code:
        dealer = session.scalar(
            select(Dealer).where(
                Dealer.dealer_code == dealer_code,
                Dealer.block_id == block_id,
            )
        )
    else:
        # No code: match by name + block to avoid duplicates on re-scrape
        dealer = session.scalar(
            select(Dealer).where(
                Dealer.dealer_code == "",
                Dealer.name_ta == name_ta,
                Dealer.block_id == block_id,
            )
        )

    if dealer is None:
        dealer = Dealer(
            dealer_code=dealer_code,
            name_ta=name_ta,
            address=address,
            contact=contact,
            block_id=block_id,
        )
        session.add(dealer)
        session.flush()
        log.debug(f"Inserted dealer: '{dealer_code}' / {name_ta}")
    else:
        dealer.name_ta = name_ta
        dealer.address = address
        dealer.contact = contact
    return dealer


# ---------------------------------------------------------------------------
# Stock insert
# ---------------------------------------------------------------------------

def insert_stock_batch(
    session: Session,
    dealer_id: int,
    stocks: dict[str, float],
    scrape_date,
    scrape_run_id: Optional[int],
) -> int:
    """
    Bulk-insert fertilizer stock records for one dealer.
    Uses ON CONFLICT DO NOTHING logic via UNIQUE(dealer_id, fertilizer_name, scrape_date).
    Returns number of rows inserted.
    """
    inserted = 0
    for fert_name, quantity in stocks.items():
        if not fert_name:
            continue

        # Check for existing row (handles re-runs on same day gracefully)
        existing = session.scalar(
            select(FertilizerStock).where(
                FertilizerStock.dealer_id == dealer_id,
                FertilizerStock.fertilizer_name == fert_name,
                FertilizerStock.scrape_date == scrape_date,
            )
        )
        if existing is not None:
            existing.quantity = quantity  # update if re-scraping same day
            continue

        record = FertilizerStock(
            dealer_id=dealer_id,
            fertilizer_name=fert_name,
            quantity=quantity,
            unit="KG",
            scrape_date=scrape_date,
            scrape_run_id=scrape_run_id,
        )
        session.add(record)
        inserted += 1

    return inserted


# ---------------------------------------------------------------------------
# Full DealerRecord → DB
# ---------------------------------------------------------------------------

def persist_dealer_record(
    session: Session,
    record: DealerRecord,
    scrape_run_id: Optional[int] = None,
) -> int:
    """
    Persist a fully parsed DealerRecord to the database.
    Handles upserts for district, block, dealer, and stock.

    Returns number of stock rows inserted.
    """
    district = upsert_district(session, record.district_code, record.district_name)
    block = upsert_block(session, record.block_code, record.block_name, district.id)

    if not record.dealer_name:
        log.debug("Skipping record with empty dealer name")
        return 0

    dealer = upsert_dealer(
        session,
        dealer_code=record.dealer_code or "",
        name_ta=record.dealer_name,
        address=record.address,
        contact=record.contact,
        block_id=block.id,
    )

    scrape_date = record.scraped_at.date() if isinstance(record.scraped_at, datetime) else record.scraped_at

    count = insert_stock_batch(
        session,
        dealer_id=dealer.id,
        stocks=record.stocks,
        scrape_date=scrape_date,
        scrape_run_id=scrape_run_id,
    )
    return count


# ---------------------------------------------------------------------------
# Scrape run metadata
# ---------------------------------------------------------------------------

def create_scrape_run(session: Session, trigger_type: str = "manual") -> ScrapeRun:
    """Create a new scrape run record and return it (with id)."""
    run = ScrapeRun(
        status="running",
        trigger_type=trigger_type,
        started_at=datetime.now(tz=timezone.utc),
    )
    session.add(run)
    session.flush()
    log.info(f"Scrape run created: id={run.id} trigger={trigger_type}")
    return run


def complete_scrape_run(
    session: Session,
    run: ScrapeRun,
    dealers_scraped: int,
    errors_count: int,
    districts_total: int = 0,
    blocks_total: int = 0,
) -> None:
    """Mark a scrape run as completed with stats."""
    run.completed_at = datetime.now(tz=timezone.utc)
    run.status = "completed"
    run.dealers_scraped = dealers_scraped
    run.errors_count = errors_count
    run.districts_total = districts_total
    run.blocks_total = blocks_total


def fail_scrape_run(session: Session, run: ScrapeRun, notes: str = "") -> None:
    """Mark a scrape run as failed."""
    run.completed_at = datetime.now(tz=timezone.utc)
    run.status = "failed"
    run.notes = notes


# ---------------------------------------------------------------------------
# Checkpoint helpers
# ---------------------------------------------------------------------------

def is_block_done(
    session: Session,
    scrape_run_id: int,
    district_code: str,
    block_code: str,
) -> bool:
    """Check if this (district, block) was already completed in this run."""
    cp = session.scalar(
        select(ScrapeCheckpoint).where(
            ScrapeCheckpoint.scrape_run_id == scrape_run_id,
            ScrapeCheckpoint.district_code == district_code,
            ScrapeCheckpoint.block_code == block_code,
            ScrapeCheckpoint.status == "done",
        )
    )
    return cp is not None


def mark_block_done(
    session: Session,
    scrape_run_id: int,
    district_code: str,
    block_code: str,
    dealers_found: int = 0,
) -> None:
    """Record a successfully scraped block in the checkpoint table."""
    cp = session.scalar(
        select(ScrapeCheckpoint).where(
            ScrapeCheckpoint.scrape_run_id == scrape_run_id,
            ScrapeCheckpoint.district_code == district_code,
            ScrapeCheckpoint.block_code == block_code,
        )
    )
    if cp is None:
        cp = ScrapeCheckpoint(
            scrape_run_id=scrape_run_id,
            district_code=district_code,
            block_code=block_code,
        )
        session.add(cp)
    cp.status = "done"
    cp.dealers_found = dealers_found
    cp.completed_at = datetime.now(tz=timezone.utc)


def mark_block_error(
    session: Session,
    scrape_run_id: int,
    district_code: str,
    block_code: str,
    error_message: str = "",
) -> None:
    """Record a failed block in the checkpoint table."""
    cp = session.scalar(
        select(ScrapeCheckpoint).where(
            ScrapeCheckpoint.scrape_run_id == scrape_run_id,
            ScrapeCheckpoint.district_code == district_code,
            ScrapeCheckpoint.block_code == block_code,
        )
    )
    if cp is None:
        cp = ScrapeCheckpoint(
            scrape_run_id=scrape_run_id,
            district_code=district_code,
            block_code=block_code,
        )
        session.add(cp)
    cp.status = "error"
    cp.error_message = error_message
    cp.completed_at = datetime.now(tz=timezone.utc)
