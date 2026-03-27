"""
Phase 4: Pipeline Orchestrator

Ties together: SessionManager → FertilizerScraper → CardParser → Database.
Supports checkpointing (skip already-done blocks on resume).

Design ref: docs/revised_HLD.md (Phase 4)
"""
import logging
import time

from tfais.config.settings import RATE_LIMIT_SECONDS
from tfais.database.connection import create_all_tables, get_session
from tfais.database.operations import (
    complete_scrape_run,
    create_scrape_run,
    fail_scrape_run,
    is_block_done,
    mark_block_done,
    mark_block_error,
    persist_dealer_record,
)
from tfais.parser.card_parser import CardParser
from tfais.scraper.scraper import FertilizerScraper
from tfais.scraper.session_manager import SessionManager

log = logging.getLogger(__name__)


class Orchestrator:
    """
    End-to-end TFAIS scrape pipeline.

    Usage:
        orch = Orchestrator()
        orch.run()                           # full run
        orch.run(district_filter=["1","2"])  # limited run for testing
    """

    def __init__(self, rate_limit: float = RATE_LIMIT_SECONDS):
        self.rate_limit = rate_limit
        self.parser = CardParser()

    def run(self, district_filter: list[str] | None = None) -> dict:
        """
        Execute the full scrape pipeline.

        Args:
            district_filter: Limit to specific district codes (for testing).

        Returns:
            Summary dict with run stats.
        """
        log.info("=== TFAIS Scrape Pipeline Starting ===")

        # Ensure DB schema exists
        create_all_tables()

        session_manager = SessionManager()
        scraper = FertilizerScraper(session_manager, rate_limit=self.rate_limit)

        # Bootstrap: get district list
        try:
            districts = session_manager.bootstrap()
        except Exception as exc:
            log.critical(f"Bootstrap failed — cannot proceed: {exc}")
            return {"status": "failed", "error": str(exc)}

        if district_filter:
            districts = [d for d in districts if d["code"] in district_filter]

        total_districts = len(districts)
        log.info(f"Districts to scrape: {total_districts}")

        # Create scrape run record
        with get_session() as session:
            run = create_scrape_run(session)
            run_id = run.id

        dealers_scraped = 0
        errors_count = 0
        blocks_total = 0

        for district in districts:
            try:
                blocks = session_manager.get_blocks_for_district(district["code"])
            except Exception as exc:
                log.error(
                    f"Failed to get blocks for district {district.get('name_ta', district['code'])}: {exc}"
                )
                errors_count += 1
                continue

            blocks_total += len(blocks)
            log.info(
                f"District {district.get('name_ta', district['code'])} "
                f"({district['code']}): {len(blocks)} blocks"
            )

            for block in blocks:
                # Check checkpoint — skip if already done in this run
                with get_session() as session:
                    if is_block_done(session, run_id, district["code"], block["code"]):
                        log.debug(
                            f"  Skipping already-done: "
                            f"dist={district['code']} block={block['code']}"
                        )
                        continue

                try:
                    # Fetch raw HTML
                    html = session_manager.fetch_results(district["code"], block["code"])
                    time.sleep(self.rate_limit)

                    # Parse cards
                    records = self.parser.parse(html, district, block)
                    log.info(
                        f"  Block {block.get('name_ta', block['code'])}: "
                        f"{len(records)} dealers"
                    )

                    # Persist to DB
                    block_dealer_count = 0
                    with get_session() as session:
                        for record in records:
                            try:
                                count = persist_dealer_record(session, record, run_id)
                                dealers_scraped += count > 0
                                block_dealer_count += 1
                            except Exception as exc:
                                log.error(
                                    f"    DB write failed for dealer "
                                    f"{record.dealer_code}: {exc}"
                                )

                        mark_block_done(
                            session, run_id, district["code"], block["code"],
                            dealers_found=block_dealer_count,
                        )

                except Exception as exc:
                    log.error(
                        f"  FAILED block {block.get('name_ta', block['code'])} "
                        f"({block['code']}) in {district.get('name_ta', district['code'])}: {exc}"
                    )
                    errors_count += 1
                    with get_session() as session:
                        mark_block_error(session, run_id, district["code"], block["code"])

        # Finalize run record
        with get_session() as session:
            from tfais.database.models import ScrapeMetadata
            run_obj = session.get(ScrapeMetadata, run_id)
            if run_obj:
                complete_scrape_run(
                    session,
                    run_obj,
                    dealers_scraped=dealers_scraped,
                    errors_count=errors_count,
                    districts_total=total_districts,
                    blocks_total=blocks_total,
                )

        summary = {
            "status": "completed",
            "run_id": run_id,
            "districts": total_districts,
            "blocks": blocks_total,
            "dealers_scraped": dealers_scraped,
            "errors": errors_count,
        }
        log.info(f"=== Pipeline complete: {summary} ===")
        return summary
