"""
Phase 0: Session Bootstrap & HTTP Workflow

Manages a persistent requests.Session for the entire scrape run.
Handles: cookies, CSRF tokens, district list extraction, block list, results POST.

Design ref: docs/revised_HLD.md  (Phase 0 section)
"""
import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup

from tfais.config.settings import (
    ENTRY_URL,
    BLOCKS_URL,
    RESULTS_URL,
    REQUEST_TIMEOUT,
    HTTP_HEADERS,
)

log = logging.getLogger(__name__)


class SessionManager:
    """
    Manages a persistent HTTP session for the entire scrape run.

    Usage:
        sm = SessionManager()
        districts = sm.bootstrap()          # GET entry page, capture session
        blocks = sm.get_blocks_for_district("1")
        html = sm.fetch_results("1", "101")
    """

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update(HTTP_HEADERS)
        self._csrf_token: Optional[str] = None
        self._hidden_fields: dict = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def bootstrap(self) -> list[dict]:
        """
        GET the entry page to:
        - Establish session cookies
        - Extract CSRF token (if present)
        - Extract full district list from <select> dropdown

        Returns:
            List of dicts: [{'code': '1', 'name_ta': 'அரியலூர்'}, ...]
        """
        log.info(f"Bootstrapping session from {ENTRY_URL}")
        resp = self.session.get(ENTRY_URL, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        soup = BeautifulSoup(resp.text, "lxml")

        # Capture CSRF token
        csrf_input = soup.find("input", {"name": "_token"})
        if csrf_input:
            self._csrf_token = csrf_input.get("value", "")
            log.debug(f"CSRF token captured: {self._csrf_token[:10]}...")

        # Capture all hidden form fields
        for hidden in soup.find_all("input", {"type": "hidden"}):
            name = hidden.get("name", "")
            value = hidden.get("value", "")
            if name:
                self._hidden_fields[name] = value

        # Extract district list
        districts = self._extract_districts(soup)
        log.info(f"Found {len(districts)} districts")
        return districts

    def get_blocks_for_district(self, district_code: str) -> list[dict]:
        """
        POST to /Fertilizer/getBlocks/{district_id} to get blocks.
        Response may be JSON array or HTML <option> tags — handles both.

        Returns:
            List of dicts: [{'code': '101', 'name_ta': 'ஆண்டிமடம்'}, ...]
        """
        url = f"{BLOCKS_URL}/{district_code}"
        log.debug(f"Fetching blocks for district {district_code} → {url}")

        resp = self.session.post(url, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()

        # Try JSON first (AJAX endpoint often returns JSON)
        try:
            data = resp.json()
            if isinstance(data, list):
                blocks = []
                for item in data:
                    # Live site JSON keys (from AngularJS ng-repeat):
                    #   value  → item.subdistrict_id   (form POST value)
                    #   label  → item.tamil_subdistrict_name
                    # Fallback to generic names for resilience
                    code = str(
                        item.get("subdistrict_id")
                        or item.get("id")
                        or item.get("value")
                        or ""
                    )
                    name = str(
                        item.get("tamil_subdistrict_name")
                        or item.get("name")
                        or item.get("text")
                        or ""
                    )
                    if code and code not in ("0", ""):
                        blocks.append({"code": code, "name_ta": name})
                log.debug(f"  Got {len(blocks)} blocks (JSON)")
                return blocks
        except (ValueError, AttributeError):
            pass

        # Fallback: parse as HTML <option> tags
        soup = BeautifulSoup(resp.text, "lxml")
        blocks = []
        for option in soup.find_all("option"):
            val = option.get("value", "").strip()
            if val and val != "0":
                blocks.append({"code": val, "name_ta": option.get_text(strip=True)})
        log.debug(f"  Got {len(blocks)} blocks (HTML fallback)")
        return blocks

    def fetch_results(self, district_code: str, block_code: str) -> str:
        """
        POST the search form to get dealer stock results HTML.

        Returns:
            Raw HTML string of the results page.
        """
        form_data: dict = {
            "district_id": district_code,   # form field name is district_id, not district
            "block_id": block_code,          # form field name is block_id, not block
            **self._hidden_fields,
        }
        if self._csrf_token:
            form_data["_token"] = self._csrf_token

        log.debug(f"Fetching results for district={district_code} block={block_code}")
        resp = self.session.post(RESULTS_URL, data=form_data, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return resp.text

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _extract_districts(self, soup: BeautifulSoup) -> list[dict]:
        """
        Parse district <option> tags from the main page <select> dropdown.

        The live site uses id="district_id" / name="district_id".
        Selector chain tries specific names first, then falls back to any
        <select> containing Tamil text options with numeric values.
        """
        districts = []

        # Primary: exact attribute names found on the live site
        select = (
            soup.find("select", id="district_id")
            or soup.find("select", {"name": "district_id"})
            # Fallback: any select whose id/name contains "district"
            or soup.find("select", {"id": lambda x: x and "district" in x.lower()})
            or soup.find("select", {"name": lambda x: x and "district" in x.lower()})
        )

        if not select:
            # Last resort: find any <select> with many numeric-valued options (likely districts)
            for sel in soup.find_all("select"):
                opts = [o for o in sel.find_all("option") if o.get("value", "").strip().isdigit()]
                if len(opts) >= 10:  # TN has 38 districts
                    select = sel
                    log.info("District select found via heuristic (numeric options fallback)")
                    break

        if not select:
            log.warning(
                "Could not find district <select> — page HTML may have changed. "
                "Run: python inspect_site.py"
            )
            return districts

        for option in select.find_all("option"):
            val = option.get("value", "").strip()
            if val and val not in ("0", ""):
                districts.append(
                    {"code": val, "name_ta": option.get_text(strip=True)}
                )

        # Log all found districts so users know the real codes
        if districts:
            log.info(
                "District codes (use these with --district flag): "
                + ", ".join(f"{d['code']}" for d in districts[:5])
                + (f" ... (+{len(districts)-5} more)" if len(districts) > 5 else "")
            )

        return districts
