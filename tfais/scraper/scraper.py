"""
Phase 1: POST-Based Fertilizer Scraper

Iterates over all (district, block) pairs using SessionManager,
collecting raw HTML for each result page.

Design ref: docs/revised_HLD.md  (Phase 1 section)
"""
import logging
import time

from tfais.config.settings import RATE_LIMIT_SECONDS
from tfais.scraper.session_manager import SessionManager

log = logging.getLogger(__name__)


class FertilizerScraper:
    """
    Orchestrates scraping of all district→block→dealer data.

    Error isolation: a failure in one district/block is logged and skipped;
    it never stops the entire run.

    Usage:
        sm = SessionManager()
        scraper = FertilizerScraper(sm)
        raw_results = scraper.scrape_all()
        # or single pair for testing:
        raw_results = scraper.scrape_one("1", "101")
    """

    def __init__(
        self,
        session_manager: SessionManager,
        rate_limit: float = RATE_LIMIT_SECONDS,
    ):
        self.sm = session_manager
        self.rate_limit = rate_limit

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def scrape_all(
        self,
        district_filter: list[str] | None = None,
    ) -> list[dict]:
        """
        Full scrape: all districts → all blocks → POST results.

        Args:
            district_filter: Optional list of district codes to limit the run.
                             None means scrape all districts.

        Returns:
            List of dicts:
            [
                {
                    'district': {'code': '1', 'name_ta': '...'},
                    'block':    {'code': '101', 'name_ta': '...'},
                    'html':     '<html>...',
                    'status':   'ok' | 'error',
                    'error':    None | str,
                },
                ...
            ]
        """
        districts = self.sm.bootstrap()

        if district_filter:
            districts = [d for d in districts if d["code"] in district_filter]
            log.info(f"Filtered to {len(districts)} districts: {district_filter}")
        else:
            log.info(f"Scraping all {len(districts)} districts")

        results = []

        for district in districts:
            district_results = self._scrape_district(district)
            results.extend(district_results)

        ok = sum(1 for r in results if r["status"] == "ok")
        err = sum(1 for r in results if r["status"] == "error")
        log.info(f"Scrape complete — {ok} ok, {err} errors out of {len(results)} total")
        return results

    def scrape_one(self, district_code: str, block_code: str) -> dict:
        """
        Scrape a single (district, block) pair. Useful for testing.

        Returns:
            Single result dict (same structure as scrape_all items).
        """
        # Bootstrap session if not already done
        if not hasattr(self.sm, "_bootstrapped"):
            self.sm.bootstrap()

        return self._fetch_block(
            district={"code": district_code, "name_ta": district_code},
            block={"code": block_code, "name_ta": block_code},
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _scrape_district(self, district: dict) -> list[dict]:
        """Fetch all blocks for a district and scrape each one."""
        results = []
        try:
            blocks = self.sm.get_blocks_for_district(district["code"])
            log.info(
                f"  District {district['name_ta']} ({district['code']}): "
                f"{len(blocks)} blocks"
            )
        except Exception as exc:
            log.error(
                f"  FAILED to get blocks for district "
                f"{district['name_ta']} ({district['code']}): {exc}"
            )
            return results  # skip entire district, don't crash

        for block in blocks:
            result = self._fetch_block(district, block)
            results.append(result)
            time.sleep(self.rate_limit)

        return results

    def _fetch_block(self, district: dict, block: dict) -> dict:
        """POST results for one (district, block) pair with error handling."""
        try:
            html = self.sm.fetch_results(district["code"], block["code"])
            log.debug(
                f"    OK  block {block['name_ta']} ({block['code']}) "
                f"— {len(html)} bytes"
            )
            return {
                "district": district,
                "block": block,
                "html": html,
                "status": "ok",
                "error": None,
            }
        except Exception as exc:
            log.error(
                f"    FAIL block {block['name_ta']} ({block['code']}) "
                f"in {district['name_ta']}: {exc}"
            )
            return {
                "district": district,
                "block": block,
                "html": "",
                "status": "error",
                "error": str(exc),
            }
