"""
Phase 3: SQLAlchemy ORM Models

Tables (6 — fertilizers master table dropped per MVP schema review):
  districts         — Tamil Nadu districts
  blocks            — Blocks/circles within districts
  dealers           — Fertilizer dealers
  fertilizer_stock  — Time-series stock snapshots (fact table)
  scrape_runs       — Per-run summary stats (renamed from scrape_metadata)
  scrape_checkpoints— Resume-on-failure checkpoint log

Key schema decisions (from docs/db_schema_critique.md):
  - fertilizer_name stored directly on fertilizer_stock (no master table)
  - dealers uses partial unique index (WHERE dealer_code != '') to handle empty codes
  - scrape_date DATE separates logical date from created_at TIMESTAMP
  - UNIQUE(dealer_id, fertilizer_name, scrape_date) prevents duplicate daily rows
  - Composite index (scrape_date, dealer_id) for dashboard's primary query pattern
"""
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _now_utc():
    return datetime.now(tz=timezone.utc)


# ---------------------------------------------------------------------------
# Reference / dimension tables
# ---------------------------------------------------------------------------

class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    name_ta = Column(String(200), nullable=False)   # Tamil name (as scraped)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    blocks = relationship("Block", back_populates="district", lazy="dynamic")

    def __repr__(self):
        return f"<District code={self.code} name={self.name_ta}>"


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (UniqueConstraint("code", "district_id", name="uq_block_district"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    name_ta = Column(String(200), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    district = relationship("District", back_populates="blocks")
    dealers = relationship("Dealer", back_populates="block", lazy="dynamic")

    def __repr__(self):
        return f"<Block code={self.code} name={self.name_ta}>"


class Dealer(Base):
    __tablename__ = "dealers"
    __table_args__ = (
        # Partial unique index: only enforce uniqueness when dealer_code is non-empty.
        # Prevents constraint violations when a dealer card has no extractable code.
        Index(
            "idx_dealer_dedup",
            "dealer_code",
            "block_id",
            unique=True,
            postgresql_where=text("dealer_code != ''"),
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    dealer_code = Column(String(50), nullable=False, default="", index=True)
    name_ta = Column(String(300), nullable=False)
    address = Column(Text, nullable=True)
    contact = Column(String(20), nullable=True)
    block_id = Column(Integer, ForeignKey("blocks.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc)
    updated_at = Column(DateTime(timezone=True), default=_now_utc, onupdate=_now_utc)

    block = relationship("Block", back_populates="dealers")
    stock_records = relationship("FertilizerStock", back_populates="dealer", lazy="dynamic")

    def __repr__(self):
        return f"<Dealer code={self.dealer_code} name={self.name_ta}>"


# ---------------------------------------------------------------------------
# Fact table (time-series)
# ---------------------------------------------------------------------------

class FertilizerStock(Base):
    __tablename__ = "fertilizer_stock"
    __table_args__ = (
        # Prevents duplicate rows if the scraper runs twice on the same day
        UniqueConstraint("dealer_id", "fertilizer_name", "scrape_date", name="uq_stock_dealer_fert_date"),
        # Composite index: the dashboard's primary query pattern is (date + dealer)
        Index("idx_stock_date_dealer", "scrape_date", "dealer_id"),
        # Secondary index for filtering by fertilizer type across all dealers
        Index("idx_stock_fertilizer_name", "fertilizer_name"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=False)
    fertilizer_name = Column(String(100), nullable=False)  # stored as-is from card headers (Tamil)
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(10), nullable=False, default="KG")
    scrape_date = Column(Date, nullable=False)              # logical date this data represents
    created_at = Column(DateTime(timezone=True), default=_now_utc)  # when this row was written
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)

    dealer = relationship("Dealer", back_populates="stock_records")
    scrape_run = relationship("ScrapeRun", back_populates="stock_records")

    def __repr__(self):
        return f"<Stock dealer={self.dealer_id} fert={self.fertilizer_name} qty={self.quantity}{self.unit}>"


# ---------------------------------------------------------------------------
# Scrape run tracking
# ---------------------------------------------------------------------------

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_now_utc)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running/completed/failed/partial
    trigger_type = Column(String(20), nullable=False, default="manual")  # manual/scheduled/resume
    districts_total = Column(Integer, nullable=True)
    blocks_total = Column(Integer, nullable=True)
    dealers_scraped = Column(Integer, nullable=True, default=0)
    errors_count = Column(Integer, nullable=True, default=0)
    notes = Column(Text, nullable=True)

    stock_records = relationship("FertilizerStock", back_populates="scrape_run", lazy="dynamic")
    checkpoints = relationship("ScrapeCheckpoint", back_populates="scrape_run", lazy="dynamic")

    def __repr__(self):
        return f"<ScrapeRun id={self.id} status={self.status} trigger={self.trigger_type}>"


class ScrapeCheckpoint(Base):
    """
    Records completion status for each (district, block) pair per run.
    Uses string codes (not FK integer IDs) because checkpoints are written
    before districts/blocks are guaranteed to be committed — avoids chicken-and-egg.
    """
    __tablename__ = "scrape_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "scrape_run_id", "district_code", "block_code",
            name="uq_checkpoint_run_dist_block",
        ),
        Index("idx_checkpoint_run_status", "scrape_run_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=False, index=True)
    district_code = Column(String(20), nullable=False)
    block_code = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending/done/error
    dealers_found = Column(Integer, nullable=True, default=0)
    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    scrape_run = relationship("ScrapeRun", back_populates="checkpoints")

    def __repr__(self):
        return (
            f"<Checkpoint run={self.scrape_run_id} "
            f"dist={self.district_code} block={self.block_code} "
            f"status={self.status}>"
        )
