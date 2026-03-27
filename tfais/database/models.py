"""
Phase 3: SQLAlchemy ORM Models

Tables:
  districts         — Tamil Nadu districts
  blocks            — Blocks/circles within districts
  dealers           — Fertilizer dealers
  fertilizers       — Fertilizer master reference
  fertilizer_stock  — Time-series stock snapshots
  scrape_metadata   — Per-run summary stats
  scrape_checkpoints— Resume-on-failure checkpoint log

Design ref: docs/revised_HLD.md (Phase 3 / Storage Layer)
"""
from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
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
    name_ta = Column(String(200), nullable=False)          # Tamil name (as scraped)
    name_en = Column(String(200), nullable=True)           # English name (optional)
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
        UniqueConstraint("dealer_code", "block_id", name="uq_dealer_block"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    dealer_code = Column(String(50), nullable=False, index=True)
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


class Fertilizer(Base):
    __tablename__ = "fertilizers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(100), nullable=False, unique=True, index=True)
    name_ta = Column(String(200), nullable=True)    # Tamil name (as seen on site)
    name_en = Column(String(200), nullable=True)    # English equivalent (manual mapping)
    category = Column(String(100), nullable=True)   # Nitrogenous / Phosphatic / etc.
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    stock_records = relationship("FertilizerStock", back_populates="fertilizer", lazy="dynamic")

    def __repr__(self):
        return f"<Fertilizer code={self.code}>"


# ---------------------------------------------------------------------------
# Fact table (time-series)
# ---------------------------------------------------------------------------

class FertilizerStock(Base):
    __tablename__ = "fertilizer_stock"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dealer_id = Column(Integer, ForeignKey("dealers.id"), nullable=False, index=True)
    fertilizer_id = Column(Integer, ForeignKey("fertilizers.id"), nullable=False, index=True)
    quantity_kg = Column(Float, nullable=False, default=0.0)
    scraped_at = Column(DateTime(timezone=True), nullable=False, index=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_metadata.id"), nullable=True, index=True)
    structure_sig = Column(String(64), nullable=True)   # MD5 from card parser

    dealer = relationship("Dealer", back_populates="stock_records")
    fertilizer = relationship("Fertilizer", back_populates="stock_records")
    scrape_run = relationship("ScrapeMetadata", back_populates="stock_records")

    def __repr__(self):
        return f"<Stock dealer={self.dealer_id} fert={self.fertilizer_id} qty={self.quantity_kg}>"


# ---------------------------------------------------------------------------
# Scrape run tracking
# ---------------------------------------------------------------------------

class ScrapeMetadata(Base):
    __tablename__ = "scrape_metadata"

    id = Column(Integer, primary_key=True, autoincrement=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=_now_utc)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running/completed/failed
    districts_total = Column(Integer, nullable=True)
    blocks_total = Column(Integer, nullable=True)
    dealers_scraped = Column(Integer, nullable=True, default=0)
    errors_count = Column(Integer, nullable=True, default=0)
    notes = Column(Text, nullable=True)

    stock_records = relationship("FertilizerStock", back_populates="scrape_run", lazy="dynamic")
    checkpoints = relationship("ScrapeCheckpoint", back_populates="scrape_run", lazy="dynamic")

    def __repr__(self):
        return f"<ScrapeRun id={self.id} status={self.status}>"


class ScrapeCheckpoint(Base):
    """
    Records completion status for each (district, block) pair per run.
    Used to skip already-completed pairs on resume.
    """
    __tablename__ = "scrape_checkpoints"
    __table_args__ = (
        UniqueConstraint(
            "scrape_run_id", "district_code", "block_code",
            name="uq_checkpoint_run_dist_block",
        ),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_metadata.id"), nullable=False, index=True)
    district_code = Column(String(20), nullable=False)
    block_code = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, default="pending")  # pending/done/error
    dealers_found = Column(Integer, nullable=True, default=0)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    scrape_run = relationship("ScrapeMetadata", back_populates="checkpoints")

    def __repr__(self):
        return (
            f"<Checkpoint run={self.scrape_run_id} "
            f"dist={self.district_code} block={self.block_code} "
            f"status={self.status}>"
        )
