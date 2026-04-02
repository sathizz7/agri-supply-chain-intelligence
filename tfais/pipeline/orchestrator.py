"""
Pipeline Orchestrator — Section-aware.

Routes CLI commands to the appropriate section controller.
Supports: --section, --subsection, --check-health, and legacy --district mode.

Design ref: docs/modular_HLD.md (Layer 2)
"""
import logging
from datetime import datetime, timezone

from tfais.database.connection import get_session
from tfais.database.operations import (
    complete_scrape_run,
    create_scrape_run,
    fail_scrape_run,
    get_health_report,
)

log = logging.getLogger(__name__)


class Orchestrator:
    """
    End-to-end TFAIS pipeline orchestrator.

    Usage:
        orch = Orchestrator()
        orch.run(section="fertilizer", subsection="price")
        orch.run(section="fertilizer", district_filter=["3317"])
        orch.check_health()
    """

    # Known sections → controller classes (lazy imports to avoid circular deps)
    SECTIONS = {
        "fertilizer": "tfais.sections.fertilizer.controller.FertilizerController",
        "seed": "tfais.sections.seed.controller.SeedController",
        "machinery": "tfais.sections.machinery.controller.MachineryController",
    }

    def run(
        self,
        section: str | None = None,
        subsection: str | None = None,
        district_filter: list[str] | None = None,
    ) -> dict:
        """
        Execute the pipeline for a section/subsection.

        Args:
            section: Section name (default: "fertilizer")
            subsection: Subsection filter (e.g. "stock", "price")
            district_filter: Limit to specific district codes

        Returns:
            Summary dict with run stats.
        """
        section = section or "fertilizer"
        log.info(f"=== TFAIS Pipeline Starting: section={section} subsection={subsection} ===")

        if section not in self.SECTIONS:
            log.error(f"Unknown section: {section}. Available: {list(self.SECTIONS.keys())}")
            return {"status": "error", "error": f"Unknown section: {section}"}

        # Create scrape run record
        with get_session() as session:
            run = create_scrape_run(session, trigger_type="manual")
            run.section_id = section
            run.subsection_id = subsection
            run_id = run.id

        try:
            # Get controller
            controller = self._get_controller(section)

            # Build subsection filter
            subsection_filter = [subsection] if subsection else None

            # Run the section controller
            results = controller.run(
                db_session_factory=get_session,
                run_id=run_id,
                subsection_filter=subsection_filter,
                district_filter=district_filter,
            )

            # Finalize run — results = {"section": ..., "subsections": {name: {...}}}
            subsections = results.get("subsections", {}) if isinstance(results, dict) else {}
            total_records = sum(
                r.get("records", 0) if not isinstance(r.get("records"), list)
                else len(r.get("records", []))
                for r in subsections.values()
                if isinstance(r, dict)
            )
            total_errors = sum(
                1 for r in subsections.values()
                if isinstance(r, dict) and r.get("status") == "error"
            )

            with get_session() as session:
                from tfais.database.models import ScrapeRun
                run_obj = session.get(ScrapeRun, run_id)
                if run_obj:
                    complete_scrape_run(
                        session, run_obj,
                        dealers_scraped=total_records,
                        errors_count=total_errors,
                    )

            summary = {
                "status": "completed",
                "run_id": run_id,
                "section": section,
                "subsection": subsection,
                "results": results,
                "total_records": total_records,
                "total_errors": total_errors,
            }
            log.info(f"=== Pipeline complete: {summary} ===")
            return summary

        except Exception as exc:
            log.critical(f"Pipeline failed: {exc}", exc_info=True)
            with get_session() as session:
                from tfais.database.models import ScrapeRun
                run_obj = session.get(ScrapeRun, run_id)
                if run_obj:
                    fail_scrape_run(session, run_obj, notes=str(exc))
            return {"status": "failed", "run_id": run_id, "error": str(exc)}

    def check_health(self) -> None:
        """
        Print a health report for all known subsections.
        Queries section_metadata, scrape_anomalies, and last run stats.
        """
        from datetime import timezone

        print()
        print(f"TFAIS Health Report — {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
        print("=" * 50)

        with get_session() as session:
            report = get_health_report(session)

        if not report:
            print("\nNo scrape data found. Run the pipeline first.")
            print()
            return

        for item in report:
            section_key = f"{item['section_id']}.{item['subsection_id']}"
            print(f"\n{section_key}")

            last_run = item.get("last_run", {})
            if last_run.get("id"):
                completed = last_run.get("completed_at")
                if completed:
                    age = datetime.now(tz=timezone.utc) - completed
                    age_str = f"{age.total_seconds() / 3600:.0f}h ago"
                else:
                    age_str = "in progress"
                print(f"  Last run:     {age_str} (run #{last_run['id']}, {last_run['status']})")
                if last_run.get("dealers_scraped") is not None:
                    print(f"  Records:      {last_run['dealers_scraped']}")
            else:
                print("  Last run:     never")

            source_date = item.get("source_updated_at")
            if source_date:
                print(f"  Source date:  {source_date.strftime('%d-%m-%Y')}")

            anomalies = item.get("recent_anomalies", [])
            if anomalies:
                print(f"  Anomalies:    {len(anomalies)} recent")
                for a in anomalies[:3]:
                    print(f"    [{a['severity']}] {a['type']}: {a['detail']}")
            else:
                print("  Anomalies:    None")

        print()

    def _get_controller(self, section: str):
        """Lazy-import and instantiate a section controller."""
        import importlib

        module_path, class_name = self.SECTIONS[section].rsplit(".", 1)
        module = importlib.import_module(module_path)
        ControllerClass = getattr(module, class_name)
        return ControllerClass()
