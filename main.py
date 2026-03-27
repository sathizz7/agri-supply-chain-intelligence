"""
TFAIS — CLI entry point

Usage:
    python main.py                          # full scrape
    python main.py --district 1 2 3         # scrape specific districts only
    python main.py --create-tables          # create DB schema (no scrape)

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
        "--district",
        nargs="+",
        metavar="CODE",
        help=(
            "Limit scrape to specific district codes. "
            "Use --list-districts first to see the real 4-digit codes "
            "(e.g. --district 3317 3338)"
        ),
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

    if args.list_districts:
        import io, sys
        # Force UTF-8 for Tamil text on Windows terminals
        out = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
        from tfais.scraper.session_manager import SessionManager
        sm = SessionManager()
        districts = sm.bootstrap()
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
    result = orch.run(district_filter=args.district)

    print("\n=== Run Summary ===")
    for k, v in result.items():
        print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
