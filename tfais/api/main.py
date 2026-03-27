"""
Phase 5: FastAPI REST API

Endpoints:
  GET /districts                          — all districts
  GET /blocks?district_code=1             — blocks for a district
  GET /fertilizer-stock                   — stock records (filterable)
  GET /dealer-details?dealer_code=999210  — dealer info + stock history
  GET /summary                            — district-level aggregates

Run: uvicorn tfais.api.main:app --reload
Docs: http://127.0.0.1:8000/docs
"""
from datetime import date, datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func, select

from tfais.database.connection import get_session
from tfais.database.models import (
    Block,
    Dealer,
    District,
    Fertilizer,
    FertilizerStock,
)

app = FastAPI(
    title="TFAIS API",
    description="Tamil Nadu Fertilizer Availability Intelligence System",
    version="1.0.0",
)


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class DistrictOut(BaseModel):
    id: int
    code: str
    name_ta: str
    name_en: Optional[str]

    class Config:
        from_attributes = True


class BlockOut(BaseModel):
    id: int
    code: str
    name_ta: str
    district_code: str

    class Config:
        from_attributes = True


class StockItem(BaseModel):
    fertilizer_code: str
    fertilizer_name_ta: Optional[str]
    fertilizer_name_en: Optional[str]
    quantity_kg: float
    scraped_at: datetime


class DealerOut(BaseModel):
    id: int
    dealer_code: str
    name_ta: str
    address: Optional[str]
    contact: Optional[str]
    block_name: str
    district_name: str


class DealerDetailOut(DealerOut):
    stock_history: list[StockItem]


class StockRecord(BaseModel):
    dealer_code: str
    dealer_name: str
    block_code: str
    block_name: str
    district_code: str
    district_name: str
    fertilizer_name: str
    quantity_kg: float
    scraped_at: datetime


class DistrictSummary(BaseModel):
    district_code: str
    district_name: str
    total_dealers: int
    total_stock_kg: float
    last_scraped: Optional[datetime]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/districts", response_model=list[DistrictOut])
def list_districts():
    """List all districts."""
    with get_session() as session:
        districts = session.scalars(select(District).order_by(District.code)).all()
        return [DistrictOut(
            id=d.id, code=d.code, name_ta=d.name_ta, name_en=d.name_en
        ) for d in districts]


@app.get("/blocks", response_model=list[BlockOut])
def list_blocks(district_code: str = Query(..., description="District code")):
    """List blocks for a given district."""
    with get_session() as session:
        district = session.scalar(
            select(District).where(District.code == district_code)
        )
        if not district:
            raise HTTPException(status_code=404, detail=f"District '{district_code}' not found")

        blocks = session.scalars(
            select(Block)
            .where(Block.district_id == district.id)
            .order_by(Block.code)
        ).all()

        return [BlockOut(
            id=b.id,
            code=b.code,
            name_ta=b.name_ta,
            district_code=district_code,
        ) for b in blocks]


@app.get("/fertilizer-stock", response_model=list[StockRecord])
def get_fertilizer_stock(
    district_code: Optional[str] = Query(None),
    block_code: Optional[str] = Query(None),
    fertilizer_code: Optional[str] = Query(None),
    scrape_date: Optional[date] = Query(None, description="Filter by date (YYYY-MM-DD)"),
    limit: int = Query(500, le=5000),
):
    """
    Query fertilizer stock records with optional filters.
    Default: returns the latest 500 records across all districts.
    """
    with get_session() as session:
        stmt = (
            select(
                FertilizerStock,
                Dealer.dealer_code,
                Dealer.name_ta.label("dealer_name"),
                Block.code.label("block_code"),
                Block.name_ta.label("block_name"),
                District.code.label("district_code"),
                District.name_ta.label("district_name"),
                Fertilizer.code.label("fert_code"),
                Fertilizer.name_ta.label("fert_name_ta"),
            )
            .join(Dealer, FertilizerStock.dealer_id == Dealer.id)
            .join(Block, Dealer.block_id == Block.id)
            .join(District, Block.district_id == District.id)
            .join(Fertilizer, FertilizerStock.fertilizer_id == Fertilizer.id)
            .order_by(FertilizerStock.scraped_at.desc())
            .limit(limit)
        )

        if district_code:
            stmt = stmt.where(District.code == district_code)
        if block_code:
            stmt = stmt.where(Block.code == block_code)
        if fertilizer_code:
            stmt = stmt.where(Fertilizer.code == fertilizer_code)
        if scrape_date:
            stmt = stmt.where(func.date(FertilizerStock.scraped_at) == scrape_date)

        rows = session.execute(stmt).all()

        return [
            StockRecord(
                dealer_code=row.dealer_code,
                dealer_name=row.dealer_name,
                block_code=row.block_code,
                block_name=row.block_name,
                district_code=row.district_code,
                district_name=row.district_name,
                fertilizer_name=row.fert_name_ta or row.fert_code,
                quantity_kg=row.FertilizerStock.quantity_kg,
                scraped_at=row.FertilizerStock.scraped_at,
            )
            for row in rows
        ]


@app.get("/dealer-details", response_model=DealerDetailOut)
def get_dealer_details(
    dealer_code: str = Query(..., description="Dealer code (from card parentheses)"),
    history_limit: int = Query(50, le=500),
):
    """Dealer profile + stock history."""
    with get_session() as session:
        dealer = session.scalar(
            select(Dealer).where(Dealer.dealer_code == dealer_code)
        )
        if not dealer:
            raise HTTPException(status_code=404, detail=f"Dealer '{dealer_code}' not found")

        block = session.get(Block, dealer.block_id)
        district = session.get(District, block.district_id) if block else None

        stock_rows = session.execute(
            select(FertilizerStock, Fertilizer)
            .join(Fertilizer, FertilizerStock.fertilizer_id == Fertilizer.id)
            .where(FertilizerStock.dealer_id == dealer.id)
            .order_by(FertilizerStock.scraped_at.desc())
            .limit(history_limit)
        ).all()

        history = [
            StockItem(
                fertilizer_code=row.Fertilizer.code,
                fertilizer_name_ta=row.Fertilizer.name_ta,
                fertilizer_name_en=row.Fertilizer.name_en,
                quantity_kg=row.FertilizerStock.quantity_kg,
                scraped_at=row.FertilizerStock.scraped_at,
            )
            for row in stock_rows
        ]

        return DealerDetailOut(
            id=dealer.id,
            dealer_code=dealer.dealer_code,
            name_ta=dealer.name_ta,
            address=dealer.address,
            contact=dealer.contact,
            block_name=block.name_ta if block else "",
            district_name=district.name_ta if district else "",
            stock_history=history,
        )


@app.get("/summary", response_model=list[DistrictSummary])
def get_summary(scrape_date: Optional[date] = Query(None)):
    """District-level aggregate: total dealers and total stock."""
    with get_session() as session:
        stmt = (
            select(
                District.code.label("district_code"),
                District.name_ta.label("district_name"),
                func.count(func.distinct(Dealer.id)).label("total_dealers"),
                func.coalesce(func.sum(FertilizerStock.quantity_kg), 0).label("total_stock_kg"),
                func.max(FertilizerStock.scraped_at).label("last_scraped"),
            )
            .join(Block, Block.district_id == District.id)
            .join(Dealer, Dealer.block_id == Block.id)
            .join(FertilizerStock, FertilizerStock.dealer_id == Dealer.id)
            .group_by(District.id, District.code, District.name_ta)
            .order_by(District.code)
        )

        if scrape_date:
            stmt = stmt.where(func.date(FertilizerStock.scraped_at) == scrape_date)

        rows = session.execute(stmt).all()

        return [
            DistrictSummary(
                district_code=row.district_code,
                district_name=row.district_name,
                total_dealers=row.total_dealers,
                total_stock_kg=float(row.total_stock_kg),
                last_scraped=row.last_scraped,
            )
            for row in rows
        ]


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "ok"}
