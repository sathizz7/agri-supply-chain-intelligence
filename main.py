"""
TFAIS — CLI entry point

Usage:
    python main.py                                          # full scrape (all fertilizer subsections)
    python main.py --section fertilizer --subsection stock  # stock position only
    python main.py --section fertilizer --subsection price  # price only
    python main.py --district 3317 3338                     # stock position, specific districts
    python main.py --check-health                           # health report
    python main.py --create-tables                          # create DB schema (no scrape)
    python main.py --list-districts                         # print district codes

Logging is written to both stdout and logs/tfais.log.
"""
import argparse
import logging
import sys
from pathlib import Path

from tfais.config.settings import LOG_FILE, LOG_LEVEL


def setup_logging():
    Path("logs").mkdir(exist_ok=True)
    fmt = "%(asctime)s [%(levelname)s] %(name)s — %(message)s"
    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
        format=fmt,
        handlers=[
            logging.StreamHandler(
                stream=open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
            ),
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
        ],
    )


def main():
    setup_logging()

    parser = argparse.ArgumentParser(description="TFAIS Scraper Pipeline")
    parser.add_argument(
        "--section",
        choices=["fertilizer", "seed", "machinery"],
        default=None,
        help="Section to scrape (default: fertilizer)",
    )
    parser.add_argument(
        "--subsection",
        choices=["stock", "price", "biofertilizer", "agri", "horti", "season",
                 "tractor", "women_plf", "drone"],
        default=None,
        help="Subsection to scrape within the section",
    )
    parser.add_argument(
        "--district",
        nargs="+",
        metavar="CODE",
        help=(
            "Limit stock scrape to specific district codes. "
            "Use --list-districts to see codes (e.g. --district 3317 3338)"
        ),
    )
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Print health report for all subsections and exit",
    )
    parser.add_argument(
        "--create-tables",
        action="store_true",
        help="Create DB tables and exit (no scrape)",
    )
    parser.add_argument(
        "--list-districts",
        action="store_true",
        help="Print all district codes and names, then exit",
    )
    args = parser.parse_args()

    if args.check_health:
        from tfais.pipeline.orchestrator import Orchestrator
        orch = Orchestrator()
        orch.check_health()
        return

    if args.list_districts:
        import io
        out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        from tfais.sections.fertilizer.parsers.stock_position import StockPositionParser
        sp = StockPositionParser()
        districts = sp.bootstrap()
        out.write(f"\nAvailable districts ({len(districts)} total):\n\n")
        for d in districts:
            out.write(f"  {d['code']:>6}  {d['name_ta']}\n")
        sample = " ".join(d["code"] for d in districts[:3])
        out.write(f"\nUsage: python main.py --district {sample}\n")
        out.flush()
        return

    if args.create_tables:
        from tfais.database.connection import create_all_tables
        create_all_tables()
        print("Tables created successfully.")
        return

    from tfais.pipeline.orchestrator import Orchestrator

    orch = Orchestrator()

    # If --district is given without --subsection, default to stock
    subsection = args.subsection
    if args.district and not subsection:
        subsection = "stock"

    result = orch.run(
        section=args.section,
        subsection=subsection,
        district_filter=args.district,
    )

    print("\n=== Run Summary ===")
    for k, v in result.items():
        if k == "results" and isinstance(v, dict):
            for parser_name, parser_result in v.items():
                print(f"  {parser_name}:")
                if isinstance(parser_result, dict):
                    for pk, pv in parser_result.items():
                        if pk != "anomalies":
                            print(f"    {pk}: {pv}")
                        elif pv:
                            print(f"    anomalies: {len(pv)}")
        else:
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
