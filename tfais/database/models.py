"""
SQLAlchemy ORM Models

Schema layout:
  public schema (shared master data + pipeline tracking)
    districts           — Tamil Nadu districts (bilingual)
    blocks              — Blocks/circles within districts (bilingual)
    scrape_runs         — Per-run summary stats
    scrape_checkpoints  — Resume-on-failure checkpoint log (generic key)
    scrape_anomalies    — Structured validation anomalies
    section_metadata    — Last-scraped and source-updated timestamps per subsection

  fertilizer schema (fertilizer section only)
    dealers             — Fertilizer dealers (FK → public.blocks)
    fertilizer_stock    — Time-series stock snapshots (FK → fertilizer.dealers, public.scrape_runs)
    fertilizer_prices   — Fertilizer price data per product/company (FK → public.scrape_runs)

  seed schema (seed section only)
    agri_seeds          — Agriculture dept seed stock (FK → public.scrape_runs)
    horti_seeds         — Horticulture dept seed stock (FK → public.scrape_runs)
    season_seeds        — Season-wise seed stock, Kharif/Rabi (FK → public.scrape_runs)

Key schema decisions:
  - fertilizer_name stored directly on fertilizer_stock (no master table)
  - dealers uses partial unique index (WHERE dealer_code != '') to handle empty codes
  - scrape_date DATE separates logical date from created_at TIMESTAMP
  - UNIQUE(dealer_id, fertilizer_name, scrape_date) prevents duplicate daily rows
  - Composite index (scrape_date, dealer_id) for dashboard's primary query pattern
  - seed tables reference districts/blocks by string code (not FK) — no cross-schema FK coupling
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
# public schema — shared reference tables
# ---------------------------------------------------------------------------

class District(Base):
    __tablename__ = "districts"
    # No schema arg → defaults to public

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, unique=True, index=True)
    name_en = Column(String(200), nullable=True)     # English name (primary, from /en/ URLs)
    name_ta = Column(String(200), nullable=True)     # Tamil name (fallback)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    blocks = relationship("Block", back_populates="district", lazy="dynamic")

    def __repr__(self):
        return f"<District code={self.code} name={self.name_en}>"


class Block(Base):
    __tablename__ = "blocks"
    __table_args__ = (UniqueConstraint("code", "district_id", name="uq_block_district"),)
    # No schema arg → defaults to public

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(20), nullable=False, index=True)
    name_en = Column(String(200), nullable=True)     # English name (primary, from /getBlocks API)
    name_ta = Column(String(200), nullable=True)     # Tamil name (fallback)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    district = relationship("District", back_populates="blocks")
    dealers = relationship(
        "Dealer",
        primaryjoin="Block.id == foreign(Dealer.block_id)",
        lazy="dynamic",
        viewonly=True,
    )

    def __repr__(self):
        return f"<Block code={self.code} name={self.name_en}>"


# ---------------------------------------------------------------------------
# fertilizer schema — fertilizer section tables
# ---------------------------------------------------------------------------

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
        {"schema": "fertilizer"},
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

    block = relationship(
        "Block",
        primaryjoin="Dealer.block_id == foreign(Block.id)",
        viewonly=True,
    )
    stock_records = relationship("FertilizerStock", back_populates="dealer", lazy="dynamic")

    def __repr__(self):
        return f"<Dealer code={self.dealer_code} name={self.name_en}>"


class FertilizerStock(Base):
    __tablename__ = "fertilizer_stock"
    __table_args__ = (
        # Prevents duplicate rows if the scraper runs twice on the same day
        UniqueConstraint("dealer_id", "fertilizer_name", "scrape_date", name="uq_stock_dealer_fert_date"),
        # Composite index: the dashboard's primary query pattern is (date + dealer)
        Index("idx_stock_date_dealer", "scrape_date", "dealer_id"),
        # Secondary index for filtering by fertilizer type across all dealers
        Index("idx_stock_fertilizer_name", "fertilizer_name"),
        {"schema": "fertilizer"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    dealer_id = Column(Integer, ForeignKey("fertilizer.dealers.id"), nullable=False)
    fertilizer_name = Column(String(100), nullable=False)  # English names from ng-init JSON keys (e.g. "DAP", "MOP", "Urea")
    quantity = Column(Float, nullable=False, default=0.0)
    unit = Column(String(10), nullable=False, default="KG")
    scrape_date = Column(Date, nullable=False)              # logical date this data represents
    created_at = Column(DateTime(timezone=True), default=_now_utc)  # when this row was written
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)

    dealer = relationship("Dealer", back_populates="stock_records")
    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="FertilizerStock.scrape_run_id == ScrapeRun.id",
        foreign_keys="[FertilizerStock.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<Stock dealer={self.dealer_id} fert={self.fertilizer_name} qty={self.quantity}{self.unit}>"


class FertilizerPrice(Base):
    __tablename__ = "fertilizer_prices"
    __table_args__ = (
        UniqueConstraint("product_id", "company", "scrape_date", name="uq_price_product_company_date"),
        Index("idx_price_product_date", "product_id", "scrape_date"),
        {"schema": "fertilizer"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    product_id = Column(Integer, nullable=False)
    product_name = Column(String(100), nullable=False)
    company = Column(String(200), nullable=False)
    price_per_50kg = Column(Float, nullable=True)          # None = unparseable
    scrape_date = Column(Date, nullable=False)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="FertilizerPrice.scrape_run_id == ScrapeRun.id",
        foreign_keys="[FertilizerPrice.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<FertilizerPrice product={self.product_name} company={self.company} price={self.price_per_50kg}>"


# ---------------------------------------------------------------------------
# public schema — pipeline tracking tables
# ---------------------------------------------------------------------------

class ScrapeRun(Base):
    __tablename__ = "scrape_runs"
    # No schema arg → defaults to public

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

    stock_records = relationship(
        "FertilizerStock",
        primaryjoin="ScrapeRun.id == FertilizerStock.scrape_run_id",
        foreign_keys="[FertilizerStock.scrape_run_id]",
        lazy="dynamic",
        viewonly=True,
    )
    price_records = relationship(
        "FertilizerPrice",
        primaryjoin="ScrapeRun.id == FertilizerPrice.scrape_run_id",
        foreign_keys="[FertilizerPrice.scrape_run_id]",
        lazy="dynamic",
        viewonly=True,
    )
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
    # No schema arg → defaults to public

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


class ScrapeAnomaly(Base):
    __tablename__ = "scrape_anomalies"
    __table_args__ = (
        Index("idx_anomaly_run_parser", "scrape_run_id", "parser_id"),
    )
    # No schema arg → defaults to public

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


class SectionMetadata(Base):
    __tablename__ = "section_metadata"
    __table_args__ = (
        UniqueConstraint("section_id", "subsection_id", name="uq_section_subsection"),
    )
    # No schema arg → defaults to public

    id = Column(Integer, primary_key=True, autoincrement=True)
    section_id = Column(String(50), nullable=False)
    subsection_id = Column(String(50), nullable=False)
    source_updated_at = Column(DateTime(timezone=True), nullable=True)
    last_scraped_at = Column(DateTime(timezone=True), nullable=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    def __repr__(self):
        return f"<SectionMetadata {self.section_id}.{self.subsection_id}>"


# ---------------------------------------------------------------------------
# machinery schema — machinery section tables (CHC Mobile portal)
# ---------------------------------------------------------------------------

class TractorOwner(Base):
    __tablename__ = "tractor_owners"
    __table_args__ = (
        UniqueConstraint(
            "district_code", "block_code", "owner_name", "machinery_name", "scrape_date",
            name="uq_tractor_owner_machine_date",
        ),
        Index("idx_tractor_date_district", "scrape_date", "district_code"),
        Index("idx_tractor_block", "block_code"),
        {"schema": "machinery"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    district_code = Column(String(20), nullable=False)
    district_name = Column(String(200), nullable=True)
    block_code = Column(String(20), nullable=False, index=True)
    block_name = Column(String(200), nullable=True)
    owner_name = Column(String(300), nullable=True)
    mobile_number = Column(String(20), nullable=True)
    registration_no = Column(String(100), nullable=True)
    maker_model = Column(String(200), nullable=True)
    machinery_name = Column(String(200), nullable=True)
    implement_name = Column(String(300), nullable=True)
    scrape_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="TractorOwner.scrape_run_id == ScrapeRun.id",
        foreign_keys="[TractorOwner.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<TractorOwner district={self.district_code} block={self.block_code} owner={self.owner_name}>"


class WomenPLF(Base):
    """
    Women's PLF (Producer Livelihood Federation) machinery hiring groups — Magalir Thittam.
    Each record is a women's SHG that provides farm implements for hire.
    """
    __tablename__ = "women_plf"
    __table_args__ = (
        UniqueConstraint(
            "district_code", "block_code", "plf_name", "scrape_date",
            name="uq_women_plf_date",
        ),
        Index("idx_wplf_date_district", "scrape_date", "district_code"),
        Index("idx_wplf_block", "block_code"),
        {"schema": "machinery"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    district_code = Column(String(20), nullable=False)   # DistrictId from WDS API
    district_name = Column(String(200), nullable=True)   # District
    block_code = Column(String(20), nullable=False, index=True)  # BlockId
    block_name = Column(String(200), nullable=True)              # Block
    plf_name = Column(String(300), nullable=True)         # WomenPLF — name of the group
    mobile_number = Column(String(20), nullable=True)     # PLF_President
    contact_address = Column(Text, nullable=True)         # ContactAddress
    machinery_procured = Column(Text, nullable=True)      # MachineryProcurred — full list
    available_count = Column(String(20), nullable=True)   # MachineryAvailable
    panchayat = Column(String(200), nullable=True)        # panchayat
    scrape_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="WomenPLF.scrape_run_id == ScrapeRun.id",
        foreign_keys="[WomenPLF.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<WomenPLF district={self.district_code} block={self.block_code} plf={self.plf_name}>"


class DroneOwner(Base):
    __tablename__ = "drone_owners"
    __table_args__ = (
        # API returns Block/BlockCode per record — block is part of identity
        UniqueConstraint(
            "district_code", "block_code", "owner_name", "scrape_date",
            name="uq_drone_owner_date",
        ),
        Index("idx_drone_date_district", "scrape_date", "district_code"),
        Index("idx_drone_block", "block_code"),
        {"schema": "machinery"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    district_code = Column(String(20), nullable=False)
    district_name = Column(String(200), nullable=True)
    block_code = Column(String(20), nullable=True, index=True)   # BlockCode from API
    block_name = Column(String(200), nullable=True)              # Block (village name) from API
    owner_name = Column(String(300), nullable=True)              # ownerName from API
    mobile_number = Column(String(20), nullable=True)
    scrape_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="DroneOwner.scrape_run_id == ScrapeRun.id",
        foreign_keys="[DroneOwner.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<DroneOwner district={self.district_code} block={self.block_code} owner={self.owner_name}>"


# ---------------------------------------------------------------------------
# seed schema — seed section tables (one table per subsection)
# ---------------------------------------------------------------------------

class AgriSeed(Base):
    __tablename__ = "agri_seeds"
    __table_args__ = (
        UniqueConstraint("block_code", "crop_name", "crop_variety", "agency_name", "scrape_date",
                         name="uq_agri_seed_date"),
        Index("idx_agri_date_block", "scrape_date", "block_code"),
        Index("idx_agri_block", "block_code"),
        {"schema": "seed"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    district_code = Column(String(20), nullable=False)
    district_name = Column(String(200), nullable=True)
    block_code = Column(String(20), nullable=False, index=True)
    block_name = Column(String(200), nullable=True)
    crop_name = Column(String(200), nullable=False)           # cropName
    crop_variety = Column(String(200), nullable=True)         # varietyName
    seed_class = Column(String(200), nullable=True)           # className
    agency_name = Column(String(300), nullable=True)          # aecName
    contact_person = Column(String(300), nullable=True)       # full_name
    contact_phone = Column(String(20), nullable=True)         # user_phone
    quantity_available = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    price = Column(String(50), nullable=True)                 # price (string e.g. "43")
    scrape_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="AgriSeed.scrape_run_id == ScrapeRun.id",
        foreign_keys="[AgriSeed.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<AgriSeed crop={self.crop_name} variety={self.crop_variety} qty={self.quantity_available}>"


class HortiSeed(Base):
    __tablename__ = "horti_seeds"
    __table_args__ = (
        UniqueConstraint("block_code", "stock_type", "input_name", "agency_name", "scrape_date",
                         name="uq_horti_seed_date"),
        Index("idx_horti_date_block", "scrape_date", "block_code"),
        Index("idx_horti_block", "block_code"),
        {"schema": "seed"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    district_code = Column(String(20), nullable=False)
    district_name = Column(String(200), nullable=True)
    block_code = Column(String(20), nullable=False, index=True)
    block_name = Column(String(200), nullable=True)
    stock_type = Column(String(200), nullable=True)           # stock_type_name (e.g. "Fruits Seedlings")
    input_name = Column(String(300), nullable=True)           # cropName from result (e.g. "Acidlime")
    seed_class = Column(String(200), nullable=True)           # className
    crop_variety = Column(String(200), nullable=True)         # varietyName
    agency_name = Column(String(300), nullable=True)          # aecName
    contact_person = Column(String(300), nullable=True)       # full_name
    contact_phone = Column(String(20), nullable=True)         # user_phone
    quantity_available = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    price = Column(String(50), nullable=True)                 # price
    scrape_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="HortiSeed.scrape_run_id == ScrapeRun.id",
        foreign_keys="[HortiSeed.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<HortiSeed stock_type={self.stock_type} input={self.input_name} qty={self.quantity_available}>"


class SeasonSeed(Base):
    __tablename__ = "season_seeds"
    __table_args__ = (
        UniqueConstraint("block_code", "season", "crop_name", "crop_variety", "agency_name", "scrape_date",
                         name="uq_season_seed_date"),
        Index("idx_season_date_block", "scrape_date", "block_code"),
        Index("idx_season_block", "block_code"),
        Index("idx_season_season", "season"),
        {"schema": "seed"},
    )

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scrape_run_id = Column(Integer, ForeignKey("scrape_runs.id"), nullable=True, index=True)
    district_code = Column(String(20), nullable=False)
    district_name = Column(String(200), nullable=True)
    block_code = Column(String(20), nullable=False, index=True)
    block_name = Column(String(200), nullable=True)
    season = Column(String(100), nullable=False)              # e.g. "Kuruvai", "Adipattam"
    crop_name = Column(String(200), nullable=False)           # cropName
    crop_variety = Column(String(200), nullable=True)         # varietyName
    seed_class = Column(String(200), nullable=True)           # className
    agency_name = Column(String(300), nullable=True)          # aecName
    contact_person = Column(String(300), nullable=True)       # full_name
    contact_phone = Column(String(20), nullable=True)         # user_phone
    quantity_available = Column(Float, nullable=True)
    unit = Column(String(20), nullable=True)
    price = Column(String(50), nullable=True)                 # price
    scrape_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), default=_now_utc)

    scrape_run = relationship(
        "ScrapeRun",
        primaryjoin="SeasonSeed.scrape_run_id == ScrapeRun.id",
        foreign_keys="[SeasonSeed.scrape_run_id]",
        viewonly=True,
    )

    def __repr__(self):
        return f"<SeasonSeed season={self.season} crop={self.crop_name} qty={self.quantity_available}>"
