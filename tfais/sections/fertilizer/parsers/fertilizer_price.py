"""
Fertilizer Price Parser

Stateless POST per product — no session needed.
Discovers products at runtime from the entry page <select#fert_id>.

Design ref: docs/subsection_parser_logic.md (Section 2)
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

import requests
from bs4 import BeautifulSoup

from tfais.config.settings import (
    PRICE_API_URL,
    PRICE_ENTRY_URL,
    PRICE_RATE_LIMIT,
    MAX_RETRIES,
    REQUEST_TIMEOUT,
)
from tfais.core.http_utils import DEFAULT_HEADERS, rate_limit, retry_request
from tfais.core.metadata import safe_parse_number

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class PriceRecord:
    product_id: int
    product_name: str
    company: str
    price_per_50kg: Optional[float]  # None = unparseable
    scraped_at: datetime


# ---------------------------------------------------------------------------
# FertilizerPriceParser
# ---------------------------------------------------------------------------

class FertilizerPriceParser:
    """
    Self-contained parser for fertilizer price data.

    Stateless HTTP — each POST is independent. No session needed.
    """
    parser_id = "fertilizer_price"
    parser_name = "Fertilizer Price Details"

    # Validation thresholds
    COUNT_DROP_THRESHOLD = 0.5
    PRICE_SPIKE_MULTIPLIER = 10

    def run(self, db_session_factory, run_id: int, **kwargs) -> dict:
        """Full pipeline: fetch -> parse -> validate -> persist."""
        from tfais.database.operations import (
            insert_anomaly_batch,
            insert_price_batch,
            upsert_section_metadata,
            is_checkpoint_done,
            mark_checkpoint,
        )

        records = []
        with db_session_factory() as session:
            raw = self.fetch(session, run_id, is_checkpoint_done, mark_checkpoint)
            records = self.parse(raw)
            
            anomalies = self.validate(records, session)
            count = self.persist(records, session, run_id)

            if anomalies:
                insert_anomaly_batch(session, run_id, anomalies)

            upsert_section_metadata(session, "fertilizer", "fertilizer_price")
            session.commit()

        return {
            "parser_id": self.parser_id,
            "records": len(records),
            "persisted": count,
            "anomalies": anomalies,
        }

    # ------------------------------------------------------------------
    # Fetch
    # ------------------------------------------------------------------

    def fetch(self, session, run_id: int, is_checkpoint_done, mark_checkpoint) -> list[dict]:
        """
        1. GET entry page -> discover product catalog from <select#fert_id>
        2. For each product: POST -> JSON array of prices
        """
        log.info(f"Fetching product catalog from {PRICE_ENTRY_URL}")

        def _get_entry():
            return requests.get(PRICE_ENTRY_URL, headers=DEFAULT_HEADERS, timeout=REQUEST_TIMEOUT)

        resp = retry_request(_get_entry, max_retries=MAX_RETRIES)
        resp.raise_for_status()

        products = self._discover_products(BeautifulSoup(resp.text, "lxml"))
        log.info(f"Discovered {len(products)} products")

        results = []
        for pid, pname in products.items():
            work_unit_key = f"product:{pid}"
            if is_checkpoint_done(session, run_id, self.parser_id, work_unit_key):
                log.debug(f"Skipping product {pname} (checkpoint already done)")
                continue

            try:
                def _fetch_price(product_id=pid):
                    return requests.post(
                        f"{PRICE_API_URL}/{product_id}",
                        headers=DEFAULT_HEADERS,
                        timeout=REQUEST_TIMEOUT,
                    )

                resp = retry_request(_fetch_price, max_retries=MAX_RETRIES)
                resp.raise_for_status()

                # Ignored Header check: The PHP backend sends Content-Type: text/html even for valid JSON
                entries = resp.json()
                results.append({
                    "product_id": pid,
                    "product_name": pname,
                    "entries": entries if isinstance(entries, list) else [],
                })
                
                records_found = len(entries) if isinstance(entries, list) else 0
                log.debug(f"  Product {pname} (id={pid}): {records_found} entries")
                
                mark_checkpoint(session, run_id, self.parser_id, work_unit_key, status="done", records_found=records_found)

            except ValueError:
                log.warning(f"Got invalid JSON instead of data for product {pname} (id={pid}), marking failed.")
                mark_checkpoint(session, run_id, self.parser_id, work_unit_key, status="error", error_message="Invalid JSON payload")
            except Exception as exc:
                log.error(f"Failed product {pname} (id={pid}): {exc}")

            rate_limit(PRICE_RATE_LIMIT)

        return results

    # ------------------------------------------------------------------
    # Parse
    # ------------------------------------------------------------------

    def parse(self, raw: list[dict]) -> list[PriceRecord]:
        """Transform raw API responses into PriceRecord objects."""
        records = []
        now = datetime.now(tz=timezone.utc)

        for item in raw:
            for entry in item["entries"]:
                company = entry.get("company", "").strip()
                if not company:
                    continue

                price = safe_parse_number(entry.get("price", ""))

                records.append(PriceRecord(
                    product_id=item["product_id"],
                    product_name=item["product_name"],
                    company=company,
                    price_per_50kg=price,
                    scraped_at=now,
                ))

        log.info(f"Parsed {len(records)} price records")
        return records

    # ------------------------------------------------------------------
    # Validate
    # ------------------------------------------------------------------

    def validate(self, records: list[PriceRecord], session) -> list[dict]:
        """Validate parsed records. Returns list of anomaly dicts."""
        from tfais.database.operations import get_previous_count, get_previous_product_ids

        anomalies = []

        # Run-level: count comparison
        prev_count = get_previous_count(session, self.parser_id)
        if prev_count > 0 and len(records) < prev_count * self.COUNT_DROP_THRESHOLD:
            anomalies.append({
                "parser_id": self.parser_id,
                "anomaly_type": "count_drop",
                "detail": f"Price records dropped {prev_count} -> {len(records)}",
                "severity": "error",
            })

        # Record-level: price range checks
        prices = [r.price_per_50kg for r in records if r.price_per_50kg is not None and r.price_per_50kg > 0]
        if prices:
            median = sorted(prices)[len(prices) // 2]
            for r in records:
                if r.price_per_50kg is not None:
                    if r.price_per_50kg < 0:
                        anomalies.append({
                            "parser_id": self.parser_id,
                            "anomaly_type": "negative_price",
                            "detail": f"Negative price: {r.product_name} / {r.company} = {r.price_per_50kg}",
                            "severity": "warning",
                        })
                    elif r.price_per_50kg > median * self.PRICE_SPIKE_MULTIPLIER:
                        anomalies.append({
                            "parser_id": self.parser_id,
                            "anomaly_type": "price_spike",
                            "detail": f"Price spike: {r.product_name} / {r.company} = {r.price_per_50kg} (median={median})",
                            "severity": "warning",
                        })

        # Product discovery: flag new products
        prev_products = get_previous_product_ids(session)
        if prev_products:
            new_products = {r.product_id for r in records} - prev_products
            if new_products:
                anomalies.append({
                    "parser_id": self.parser_id,
                    "anomaly_type": "new_products",
                    "detail": f"New product IDs detected: {new_products}",
                    "severity": "warning",
                })

        return anomalies

    # ------------------------------------------------------------------
    # Persist
    # ------------------------------------------------------------------

    def persist(self, records: list[PriceRecord], session, run_id: int) -> int:
        """Persist price records to the database."""
        from tfais.database.operations import insert_price_batch

        count = insert_price_batch(session, records, run_id)
        log.info(f"Persisted {count} new price records (total: {len(records)})")
        return count

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _discover_products(self, soup: BeautifulSoup) -> dict[int, str]:
        """Parse <select#fert_id> to discover product catalog at runtime."""
        catalog = {}
        select = soup.find("select", id="fert_id")
        if not select:
            log.error("Product <select#fert_id> not found on entry page")
            return catalog

        for option in select.find_all("option"):
            val = option.get("value", "").strip()
            if val and val != "0":
                try:
                    catalog[int(val)] = option.get_text(strip=True)
                except ValueError:
                    continue

        return catalog
