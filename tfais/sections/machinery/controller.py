"""
Machinery Section Controller — orchestrates all machinery parsers with error isolation.
"""
import logging
from typing import Optional

from sqlalchemy.orm import sessionmaker

from tfais.sections.machinery.parsers.drone import DroneOwnersParser
from tfais.sections.machinery.parsers.tractor import PrivateTractorParser
from tfais.sections.machinery.parsers.woman_mechanics import WomenPLFParser

log = logging.getLogger(__name__)


class MachineryController:
    """Controller for machinery section — runs parsers (tractor, woman_mechanics, drone) with error isolation."""

    PARSERS = {
        "tractor": PrivateTractorParser,
        "women_plf": WomenPLFParser,
        "drone": DroneOwnersParser,
    }

    def run(
        self,
        db_session_factory: sessionmaker,
        run_id: int,
        subsection_filter: Optional[list[str]] = None,
        district_filter: Optional[list[str]] = None,
    ) -> dict:
        """
        Run machinery parsers with error isolation.

        Returns:
            {
                "section": "machinery",
                "subsections": {
                    "tractor": {"status": ..., "records": N, "persisted": N, "anomalies": [...]},
                    "woman_mechanics": {...},
                    "drone": {...},
                }
            }
        """
        result = {
            "section": "machinery",
            "subsections": {},
        }

        parsers_to_run = list(self.PARSERS.keys())
        if subsection_filter:
            parsers_to_run = [p for p in parsers_to_run if p in subsection_filter]

        for subsection_name in parsers_to_run:
            parser_class = self.PARSERS.get(subsection_name)
            if not parser_class:
                result["subsections"][subsection_name] = {
                    "status": "error",
                    "error": f"Unknown subsection: {subsection_name}",
                    "records": 0,
                    "persisted": 0,
                    "anomalies": [],
                }
                continue

            try:
                log.info(f"Running machinery parser: {subsection_name}")
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
