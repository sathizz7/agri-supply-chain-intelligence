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

from sqlalchemy import func

from tfais.database.models import (
    Block,
    Dealer,
    District,
    FertilizerPrice,
    FertilizerStock,
    ScrapeAnomaly,
    ScrapeCheckpoint,
    ScrapeRun,
    SectionMetadata,
)

from tfais.sections.fertilizer.parsers.stock_position import DealerRecord

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# District
# ---------------------------------------------------------------------------

def upsert_district(session: Session, code: str, name_en: str = "", name_ta: str = "") -> District:
    """Insert or update a district record with bilingual names. Returns the persisted District object."""
    district = session.scalar(select(District).where(District.code == code))
    if district is None:
        district = District(code=code, name_en=name_en, name_ta=name_ta)
        session.add(district)
        session.flush()
        log.debug(f"Inserted district: {code} / EN:{name_en} TA:{name_ta}")
    else:
        district.name_ta = name_ta
    return district


# ---------------------------------------------------------------------------
# Block
# ---------------------------------------------------------------------------

def upsert_block(
    session: Session,
    code: str,
    name_en: str = "",
    name_ta: str = "",
    district_id: int = None,
) -> Block:
    """Insert or update a block record with bilingual names."""
    block = session.scalar(
        select(Block).where(Block.code == code, Block.district_id == district_id)
    )
    if block is None:
        block = Block(code=code, name_en=name_en, name_ta=name_ta, district_id=district_id)
        session.add(block)
        session.flush()
        log.debug(f"Inserted block: {code} / EN:{name_en} TA:{name_ta}")
    else:
        block.name_en = name_en
        block.name_ta = name_ta
    return block


# ---------------------------------------------------------------------------
# Dealer
# ---------------------------------------------------------------------------

def upsert_dealer(
    session: Session,
    dealer_code: str,
    name_en: str,
    name_ta: str,
    address: str,
    contact: str,
    block_id: int,
) -> Dealer:
    """
    Upsert dealer by (dealer_code, block_id) — the canonical dedup key.
    Empty dealer_code is allowed (partial unique index handles it in DB).
    name_en (English, from delar_name) is primary; name_ta (Tamil, from tamil_agency) is fallback.
    """
    if dealer_code:
        dealer = session.scalar(
            select(Dealer).where(
                Dealer.dealer_code == dealer_code,
                Dealer.block_id == block_id,
            )
        )
    else:
        # No code: match by name_en + block to avoid duplicates on re-scrape
        dealer = session.scalar(
            select(Dealer).where(
                Dealer.dealer_code == "",
                Dealer.name_en == name_en,
                Dealer.block_id == block_id,
            )
        )

    if dealer is None:
        dealer = Dealer(
            dealer_code=dealer_code,
            name_en=name_en,
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
    Handles upserts for district, block, dealer, and stock with bilingual data.

    Returns number of stock rows inserted.
    """
    district = upsert_district(session, record.district_code, name_en=record.district_name_en, name_ta=record.district_name_ta)
    block = upsert_block(session, record.block_code, name_en=record.block_name_en, name_ta=record.block_name_ta, district_id=district.id)

    if not record.dealer_name_en and not record.dealer_name_ta:
        log.debug("Skipping record with empty dealer name")
        return 0

    dealer = upsert_dealer(
        session,
        dealer_code=record.dealer_code or "",
        name_en=record.dealer_name_en,
        name_ta=record.dealer_name_ta,
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
# Legacy checkpoint helpers (removed — use is_checkpoint_done / mark_checkpoint)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Generic checkpoint helpers (parser_id + work_unit_key)
# ---------------------------------------------------------------------------

def is_checkpoint_done(
    session: Session,
    run_id: int,
    parser_id: str,
    work_unit_key: str,
) -> bool:
    """Check if this work unit was already completed in this run."""
    cp = session.scalar(
        select(ScrapeCheckpoint).where(
            ScrapeCheckpoint.scrape_run_id == run_id,
            ScrapeCheckpoint.parser_id == parser_id,
            ScrapeCheckpoint.work_unit_key == work_unit_key,
            ScrapeCheckpoint.status == "done",
        )
    )
    return cp is not None


def mark_checkpoint(
    session: Session,
    run_id: int,
    parser_id: str,
    work_unit_key: str,
    status: str = "done",
    records_found: int = 0,
    error_message: str = "",
) -> None:
    """Record a checkpoint for a generic work unit."""
    cp = session.scalar(
        select(ScrapeCheckpoint).where(
            ScrapeCheckpoint.scrape_run_id == run_id,
            ScrapeCheckpoint.parser_id == parser_id,
            ScrapeCheckpoint.work_unit_key == work_unit_key,
        )
    )
    if cp is None:
        cp = ScrapeCheckpoint(
            scrape_run_id=run_id,
            parser_id=parser_id,
            work_unit_key=work_unit_key,
        )
        session.add(cp)
    cp.status = status
    cp.dealers_found = records_found
    cp.error_message = error_message
    cp.completed_at = datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def get_previous_count(session: Session, parser_id: str) -> int:
    """Get the total record count from the most recent completed run for this parser."""
    last_run = session.scalar(
        select(ScrapeRun)
        .where(
            ScrapeRun.subsection_id == parser_id,
            ScrapeRun.status == "completed",
        )
        .order_by(ScrapeRun.completed_at.desc())
        .limit(1)
    )
    if not last_run:
        return 0

    # Count checkpoints that recorded records_found
    total = session.scalar(
        select(func.sum(ScrapeCheckpoint.dealers_found))
        .where(
            ScrapeCheckpoint.scrape_run_id == last_run.id,
            ScrapeCheckpoint.parser_id == parser_id,
            ScrapeCheckpoint.status == "done",
        )
    )
    return total or 0


def get_previous_product_ids(session: Session) -> set[int]:
    """Get all product IDs from the most recent price scrape."""
    result = session.scalars(
        select(FertilizerPrice.product_id).distinct()
    ).all()
    return set(result)


# ---------------------------------------------------------------------------
# Anomaly persistence
# ---------------------------------------------------------------------------

def insert_anomaly_batch(
    session: Session,
    run_id: int,
    anomalies: list[dict],
) -> int:
    """Insert validation anomalies for a run. Returns count inserted."""
    inserted = 0
    for a in anomalies:
        session.add(ScrapeAnomaly(
            scrape_run_id=run_id,
            parser_id=a.get("parser_id", "unknown"),
            anomaly_type=a.get("anomaly_type", "unknown"),
            detail=a.get("detail", ""),
            severity=a.get("severity", "warning"),
        ))
        inserted += 1
    return inserted


# ---------------------------------------------------------------------------
# Section metadata
# ---------------------------------------------------------------------------

def upsert_section_metadata(
    session: Session,
    section_id: str,
    subsection_id: str,
    source_updated_at: Optional[datetime] = None,
) -> SectionMetadata:
    """Upsert the metadata record for a section/subsection."""
    meta = session.scalar(
        select(SectionMetadata).where(
            SectionMetadata.section_id == section_id,
            SectionMetadata.subsection_id == subsection_id,
        )
    )
    if meta is None:
        meta = SectionMetadata(section_id=section_id, subsection_id=subsection_id)
        session.add(meta)

    meta.last_scraped_at = datetime.now(tz=timezone.utc)
    if source_updated_at:
        meta.source_updated_at = source_updated_at
    session.flush()
    return meta


# ---------------------------------------------------------------------------
# Price persistence
# ---------------------------------------------------------------------------

def insert_price_batch(
    session: Session,
    records: list,
    run_id: int,
) -> int:
    """
    Insert/update fertilizer price records.
    Upserts on (product_id, company, scrape_date).
    Returns count of new rows inserted.
    """
    inserted = 0
    for r in records:
        scrape_date = r.scraped_at.date() if isinstance(r.scraped_at, datetime) else r.scraped_at
        existing = session.scalar(
            select(FertilizerPrice).where(
                FertilizerPrice.product_id == r.product_id,
                FertilizerPrice.company == r.company,
                FertilizerPrice.scrape_date == scrape_date,
            )
        )
        if existing:
            existing.price_per_50kg = r.price_per_50kg
        else:
            session.add(FertilizerPrice(
                product_id=r.product_id,
                product_name=r.product_name,
                company=r.company,
                price_per_50kg=r.price_per_50kg,
                scrape_date=scrape_date,
                scrape_run_id=run_id,
            ))
            inserted += 1
    return inserted


# ---------------------------------------------------------------------------
# Health check queries
# ---------------------------------------------------------------------------

def get_health_report(session: Session) -> list[dict]:
    """
    Build a health report for all known subsections.
    Returns list of dicts with last run info and record counts.
    """
    report = []
    metadata_rows = session.scalars(select(SectionMetadata)).all()

    for meta in metadata_rows:
        last_run = session.scalar(
            select(ScrapeRun)
            .where(
                ScrapeRun.section_id == meta.section_id,
                ScrapeRun.subsection_id == meta.subsection_id,
                ScrapeRun.status == "completed",
            )
            .order_by(ScrapeRun.completed_at.desc())
            .limit(1)
        )

        recent_anomalies = session.scalars(
            select(ScrapeAnomaly)
            .where(ScrapeAnomaly.parser_id == meta.subsection_id)
            .order_by(ScrapeAnomaly.created_at.desc())
            .limit(5)
        ).all()

        report.append({
            "section_id": meta.section_id,
            "subsection_id": meta.subsection_id,
            "last_scraped_at": meta.last_scraped_at,
            "source_updated_at": meta.source_updated_at,
            "last_run": {
                "id": last_run.id if last_run else None,
                "status": last_run.status if last_run else None,
                "completed_at": last_run.completed_at if last_run else None,
                "dealers_scraped": last_run.dealers_scraped if last_run else None,
            },
            "recent_anomalies": [
                {"type": a.anomaly_type, "detail": a.detail, "severity": a.severity}
                for a in recent_anomalies
            ],
        })

    return report
