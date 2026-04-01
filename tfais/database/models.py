"""
SQLAlchemy ORM Models

Tables:
  districts           — Tamil Nadu districts (bilingual)
  blocks              — Blocks/circles within districts (bilingual)
  dealers             — Fertilizer dealers
  fertilizer_stock    — Time-series stock snapshots (fact table)
  fertilizer_prices   — Fertilizer price data per product/company
  scrape_runs         — Per-run summary stats
  scrape_checkpoints  — Resume-on-failure checkpoint log (generic key)
  scrape_anomalies    — Structured validation anomalies
  section_metadata    — Last-scraped and source-updated timestamps per subsection

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
    name_en = Column(String(200), nullable=True)     # English name (primary, from /en/ URLs)
    name_ta = Column(String(200), nullable=True)     # Tamil name (fallback)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    blocks = relationship("Block", back_populates="district", lazy="dynamic")

    def __repr__(self):
        return f"<District code={self.code} name={self.name_ta}>"


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (UniqueConstraint("code", "district_id", name="uq_block_district"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    name_en = Column(String(200), nullable=True)     # English name (primary, from /getBlocks API)
    name_ta = Column(String(200), nullable=True)     # Tamil name (fallback)
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
    name_en = Column(String(300), nullable=True)     # English name (primary, from delar_name in ng-init)
    name_ta = Column(String(300), nullable=True)     # Tamil name (fallback, from tamil_agency in ng-init)
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
    fertilizer_name = Column(String(100), nullable=False)  # English names from ng-init JSON keys (e.g. "DAP", "MOP", "Urea")
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
    section_id = Column(String(50), nullable=True)         # e.g. "fertilizer"
    subsection_id = Column(String(50), nullable=True)      # e.g. "stock_position", "fertilizer_price"
    source_updated_at = Column(DateTime(timezone=True), nullable=True)  # "Last update date" from source
    districts_total = Column(Integer, nullable=True)
    blocks_total = Column(Integer, nullable=True)
    dealers_scraped = Column(Integer, nullable=True, default=0)
    errors_count = Column(Integer, nullable=True, default=0)
    notes = Column(Text, nullable=True)

    stock_records = relationship("FertilizerStock", back_populates="scrape_run", lazy="dynamic")
    price_records = relationship("FertilizerPrice", back_populates="scrape_run", lazy="dynamic")
    checkpoints = relationship("ScrapeCheckpoint", back_populates="scrape_run", lazy="dynamic")
    anomalies = relationship("ScrapeAnomaly", back_populates="scrape_run", lazy="dynamic")

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
            "scrape_run_id", "parser_id", "work_unit_key",
            name="uq_checkpoint_run_parser_key",
        ),
        Index("idx_checkpoint_run_status", "scrape_run_id", "status"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=False, index=True)
    parser_id = Column(String(50), nullable=False)       # e.g. "stock_position", "fertilizer_price"
    work_unit_key = Column(String(200), nullable=False)  # e.g. "3317:101", "product:1"
    status = Column(String(20), nullable=False, default="pending")  # pending/done/error
    dealers_found = Column(Integer, nullable=True, default=0)
    error_message = Column(Text, nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    scrape_run = relationship("ScrapeRun", back_populates="checkpoints")

    def __repr__(self):
        return (
            f"<Checkpoint run={self.scrape_run_id} "
            f"parser={self.parser_id} key={self.work_unit_key} "
            f"status={self.status}>"
        )


# ---------------------------------------------------------------------------
# Fertilizer prices
# ---------------------------------------------------------------------------

class FertilizerPrice(Base):
    __tablename__ = "fertilizer_prices"
    __table_args__ = (
        UniqueConstraint("product_id", "company", "scrape_date", name="uq_price_product_company_date"),
        Index("idx_price_product_date", "product_id", "scrape_date"),
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    company = Column(String(200), nullable=False)
    price_per_50kg = Column(Float, nullable=True)          # None = unparseable
    scrape_date = Column(Date, nullable=False)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship("ScrapeRun", back_populates="price_records")

    def __repr__(self):
        return f"<FertilizerPrice product={self.product_name} company={self.company} price={self.price_per_50kg}>"


# ---------------------------------------------------------------------------
# Validation anomalies
# ---------------------------------------------------------------------------

class ScrapeAnomaly(Base):
    __tablename__ = "scrape_anomalies"
    __table_args__ = (
        Index("idx_anomaly_run_parser", "scrape_run_id", "parser_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=False)
    parser_id = Column(String(50), nullable=False)
    anomaly_type = Column(String(50), nullable=False)  # count_drop, price_spike, empty_district, etc.
    detail = Column(Text, nullable=True)
    severity = Column(String(20), nullable=False, default="warning")  # warning/error
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship("ScrapeRun", back_populates="anomalies")

    def __repr__(self):
        return f"<ScrapeAnomaly parser={self.parser_id} type={self.anomaly_type} severity={self.severity}>"


# ---------------------------------------------------------------------------
# Section metadata (last-scraped timestamps)
# ---------------------------------------------------------------------------

class SectionMetadata(Base):
    __tablename__ = "section_metadata"
    __table_args__ = (
        UniqueConstraint("section_id", "subsection_id", name="uq_section_subsection"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(String(50), nullable=False)
    subsection_id = Column(String(50), nullable=False)
    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    def __repr__(self):
        return f"<SectionMetadata {self.section_id}.{self.subsection_id}>"
