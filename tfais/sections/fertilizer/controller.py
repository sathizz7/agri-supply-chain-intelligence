"""
Fertilizer Section Controller

Plain class — no ABC inheritance. Runs registered parsers with error isolation.
Each parser failure is logged and skipped; it never kills other parsers.

Design ref: docs/modular_HLD.md (Section 3)
"""
import asyncio
import logging

from tfais.sections.fertilizer.parsers.biofertilizer import BiofertilizerParser
from tfais.sections.fertilizer.parsers.fertilizer_price import FertilizerPriceParser
from tfais.sections.fertilizer.parsers.stock_position import StockPositionParser

log = logging.getLogger(__name__)


class FertilizerController:
    """
    Orchestrates all fertilizer subsection parsers.

    Usage:
        ctrl = FertilizerController()
        results = ctrl.run(db_session_factory, run_id, subsection_filter=["stock"])
    """

    PARSERS = {
        "stock": StockPositionParser,
        "price": FertilizerPriceParser,
        "biofertilizer": BiofertilizerParser,
    }

    def run(
        self,
        db_session_factory,
        run_id: int,
        subsection_filter: list[str] | None = None,
        district_filter: list[str] | None = None,
    ) -> dict:
        """
        Run all (or filtered) parsers for the fertilizer section.

        Returns dict of {parser_name: result_dict_or_error}.
        """
        results = {}

        for name, ParserClass in self.PARSERS.items():
            if subsection_filter and name not in subsection_filter:
                continue

            log.info(f"--- Running parser: {name} ---")
            try:
                parser = ParserClass()
                kwargs = {}
                if name == "stock" and district_filter:
                    kwargs["district_filter"] = district_filter

                result = parser.run(db_session_factory, run_id, **kwargs)
                results[name] = result
                log.info(f"--- Parser {name} completed: {result.get('records', 0)} records ---")

            except NotImplementedError as exc:
                log.info(f"Parser {name}: not implemented ({exc})")
                results[name] = {"status": "not_implemented", "message": str(exc)}

            except Exception as exc:
                log.error(f"Parser {name} FAILED: {exc}", exc_info=True)
                results[name] = {"status": "error", "error": str(exc)}

        return results

    async def run_async(
        self,
        db_session_factory,
        run_id: int,
        subsection_filter: list[str] | None = None,
        district_filter: list[str] | None = None,
    ) -> dict:
        """
        Run fertilizer parsers concurrently via asyncio.gather().
        Each parser's run_async() wraps the existing sync run() in a thread.
        Error isolation is preserved: one parser failure never affects others.
        """
        async def _run_one(name: str) -> tuple[str, dict]:
            ParserClass = self.PARSERS.get(name)
            if not ParserClass:
                return name, {"status": "error", "error": f"Unknown parser: {name}"}
            try:
                log.info(f"[async] --- Running parser: {name} ---")
                parser = ParserClass()
                kwargs = {}
                if name == "stock" and district_filter:
                    kwargs["district_filter"] = district_filter
                result = await parser.run_async(db_session_factory, run_id, **kwargs)
                log.info(f"[async] --- Parser {name} completed: {result.get('records', 0)} records ---")
                return name, result
            except NotImplementedError as exc:
                log.info(f"Parser {name}: not implemented ({exc})")
                return name, {"status": "not_implemented", "message": str(exc)}
            except Exception as exc:
                log.error(f"Parser {name} FAILED: {exc}", exc_info=True)
                return name, {"status": "error", "error": str(exc)}

        names_to_run = [n for n in self.PARSERS if not subsection_filter or n in subsection_filter]
        task_results = await asyncio.gather(
            *[_run_one(name) for name in names_to_run],
            return_exceptions=False,  # _run_one catches internally
        )
        return dict(task_results)
