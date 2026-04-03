"""
Seed Section Controller — orchestrates all seed parsers with error isolation.
"""
import asyncio
import logging
from typing import Optional

from sqlalchemy.orm import sessionmaker

from tfais.sections.seed.parsers.agri_seed import AgriSeedParser
from tfais.sections.seed.parsers.horti_seed import HortiSeedParser
from tfais.sections.seed.parsers.season_seed import SeasonSeedParser

log = logging.getLogger(__name__)


class SeedController:
    """Controller for seed section — runs parsers (agri, horti, season) with error isolation."""

    PARSERS = {
        "agri": AgriSeedParser,
        "horti": HortiSeedParser,
        "season": SeasonSeedParser,
    }

    def run(
        self,
        db_session_factory: sessionmaker,
        run_id: int,
        subsection_filter: Optional[list[str]] = None,
        district_filter: Optional[list[str]] = None,
    ) -> dict:
        """
        Run seed parsers with error isolation.

        Args:
            db_session_factory: SQLAlchemy session factory
            run_id: Current scrape run ID
            subsection_filter: If provided, only run these parsers (e.g. ["agri", "horti"])
            district_filter: If provided, only scrape these districts

        Returns:
            {
                "section": "seed",
                "subsections": {
                    "agri_seed": {
                        "status": "completed" | "not_implemented" | "error",
                        "records": [...],
                        "persisted": N,
                        "anomalies": [...],
                        "error": "error message (if status='error')"
                    },
                    ...
                }
            }
        """
        result = {
            "section": "seed",
            "subsections": {},
        }

        # Determine which parsers to run
        parsers_to_run = self.PARSERS.keys()
        if subsection_filter:
            parsers_to_run = [p for p in parsers_to_run if p in subsection_filter]

        # Run each parser with error isolation
        for subsection_name in parsers_to_run:
            parser_class = self.PARSERS.get(subsection_name)
            if not parser_class:
                result["subsections"][subsection_name] = {
                    "status": "error",
                    "error": f"Unknown subsection: {subsection_name}",
                    "records": [],
                    "persisted": 0,
                    "anomalies": [],
                }
                continue

            try:
                log.info(f"Running seed parser: {subsection_name}")
                parser = parser_class()
                parser_result = parser.run(
                    db_session_factory,
                    run_id,
                    district_filter=district_filter,
                )

                result["subsections"][subsection_name] = {
                    "status": "completed",
                    "records": len(parser_result.get("records", [])),
                    "persisted": parser_result.get("persisted", 0),
                    "anomalies": parser_result.get("anomalies", []),
                }

                log.info(
                    f"{subsection_name}: {parser_result.get('persisted', 0)} records persisted"
                )

            except NotImplementedError as e:
                log.warning(f"{subsection_name}: Not implemented - {e}")
                result["subsections"][subsection_name] = {
                    "status": "not_implemented",
                    "error": str(e),
                    "records": 0,
                    "persisted": 0,
                    "anomalies": [],
                }

            except Exception as e:
                log.error(f"{subsection_name}: Error - {e}", exc_info=True)
                result["subsections"][subsection_name] = {
                    "status": "error",
                    "error": str(e),
                    "records": 0,
                    "persisted": 0,
                    "anomalies": [],
                }

        return result

    async def run_async(
        self,
        db_session_factory: sessionmaker,
        run_id: int,
        subsection_filter: Optional[list[str]] = None,
        district_filter: Optional[list[str]] = None,
    ) -> dict:
        """
        Run seed parsers concurrently via asyncio.gather().
        Each parser's run_async() wraps the existing sync run() in a thread,
        so CSRF/cookie session state is fully preserved.
        Error isolation is preserved: one parser failure never affects others.
        """
        result = {
            "section": "seed",
            "subsections": {},
        }

        parsers_to_run = list(self.PARSERS.keys())
        if subsection_filter:
            parsers_to_run = [p for p in parsers_to_run if p in subsection_filter]

        async def _run_one(subsection_name: str) -> tuple[str, dict]:
            parser_class = self.PARSERS.get(subsection_name)
            if not parser_class:
                return subsection_name, {
                    "status": "error",
                    "error": f"Unknown subsection: {subsection_name}",
                    "records": 0, "persisted": 0, "anomalies": [],
                }
            try:
                log.info(f"[async] Running seed parser: {subsection_name}")
                parser = parser_class()
                parser_result = await parser.run_async(
                    db_session_factory, run_id, district_filter=district_filter
                )
                log.info(f"{subsection_name}: {parser_result.get('persisted', 0)} records persisted")
                return subsection_name, {
                    "status": "completed",
                    "records": len(parser_result.get("records", [])),
                    "persisted": parser_result.get("persisted", 0),
                    "anomalies": parser_result.get("anomalies", []),
                }
            except NotImplementedError as e:
                log.warning(f"{subsection_name}: Not implemented - {e}")
                return subsection_name, {
                    "status": "not_implemented",
                    "error": str(e),
                    "records": 0, "persisted": 0, "anomalies": [],
                }
            except Exception as e:
                log.error(f"{subsection_name}: Error - {e}", exc_info=True)
                return subsection_name, {
                    "status": "error",
                    "error": str(e),
                    "records": 0, "persisted": 0, "anomalies": [],
                }

        task_results = await asyncio.gather(
            *[_run_one(name) for name in parsers_to_run],
            return_exceptions=False,  # _run_one catches internally
        )
        result["subsections"] = dict(task_results)
        return result
