"""
Biofertilizer & MN Mixture Parser — STUB

Deferred because:
- Different domain (tnagrisnet.tn.gov.in, not 115.243.209.84)
- Angular SPA with mat-select components — BeautifulSoup cannot parse
- Requires either direct REST API calls or Playwright

See docs/subsection_parser_logic.md (Section 3) for prerequisites.
"""


class BiofertilizerParser:
    parser_id = "biofertilizer"
    parser_name = "Biofertilizer & MN Mixture Stock"

    def run(self, db_session_factory, run_id: int, **kwargs) -> dict:
        raise NotImplementedError(
            "Biofertilizer parser not yet implemented. "
            "Requires REST API investigation or Playwright. "
            "See docs/subsection_parser_logic.md section 3."
        )
