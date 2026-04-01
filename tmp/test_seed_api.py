"""Test Seed Stock API endpoints to understand structure."""
import requests
from html.parser import HTMLParser

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
}

BASE = "https://www.tnagrisnet.tn.gov.in/people_app"

# ─── Parse <select> elements from HTML ─────────────────────────────
class SelectParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_select = False
        self.current_id = ""
        self.options = []
        self.selects = {}
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "select":
            self.in_select = True
            self.current_id = d.get("id", d.get("name","?"))
            self.options = []
        elif tag == "option" and self.in_select:
            self.options.append((d.get("value",""), ""))
    def handle_data(self, data):
        if self.in_select and self.options:
            v, _ = self.options[-1]
            self.options[-1] = (v, data.strip())
    def handle_endtag(self, tag):
        if tag == "select":
            self.in_select = False
            self.selects[self.current_id] = list(self.options)

# ─── TEST 1: Agriculture Dept entry page ────
print("=" * 60)
print("TEST 1: Seed Agriculture Entry Page")
print("=" * 60)
r = requests.get(f"{BASE}/Seed/seed_gov/en", headers=headers)
print(f"Status: {r.status_code}")

p = SelectParser()
p.feed(r.text)
for sid, opts in p.selects.items():
    print(f"\n  <select id='{sid}'> ({len(opts)} total options):")
    for v, t in opts[:6]:
        print(f"    value={v:>6s}  text={t}")
    if len(opts) > 6:
        print(f"    ... and {len(opts)-6} more")

# Grab first valid district ID for further tests
districts = [(v, t) for v, t in p.selects.get("district_id", []) if v and v != "0"]
crops = [(v, t) for v, t in p.selects.get("crop_id", []) if v and v != "0"]
print(f"\nTotal districts: {len(districts)}")
print(f"Total crops: {len(crops)}")

# ─── TEST 2: getBlocks API ────
if districts:
    dist_id = districts[0][0]
    dist_name = districts[0][1]
    print(f"\n{'='*60}")
    print(f"TEST 2: getBlocks for district '{dist_name}' (id={dist_id})")
    print("=" * 60)
    r2 = requests.post(f"{BASE}/Seed/getBlocks/{dist_id}", headers=headers)
    print(f"Status: {r2.status_code}")
    print(f"Content-Type: {r2.headers.get('Content-Type')}")
    print(f"Body (first 500 chars): {r2.text[:500]}")
    
    # Parse blocks
    try:
        blocks = r2.json()
        print(f"\nParsed {len(blocks)} blocks. First 3:")
        for b in blocks[:3]:
            print(f"  {b}")
    except Exception as e:
        print(f"JSON parse failed: {e}")

# ─── TEST 3: Search/Result ────
if districts and crops:
    block_id = ""
    try:
        blocks = r2.json()
        if blocks:
            # Try to get block_id from first block
            if isinstance(blocks[0], dict):
                block_id = str(blocks[0].get("block_id", blocks[0].get("id", "")))
            elif isinstance(blocks[0], (list, tuple)):
                block_id = str(blocks[0][0])
    except:
        pass
    
    crop_id = crops[0][0]
    print(f"\n{'='*60}")
    print(f"TEST 3: Search result POST")
    print(f"  district_id={dist_id}, block_id={block_id}, crop_id={crop_id}")
    print("=" * 60)
    
    # Need session for CSRF
    session = requests.Session()
    session.headers.update(headers)
    
    # First GET the entry to grab session cookie
    entry = session.get(f"{BASE}/Seed/seed_gov/en")
    print(f"Entry cookies: {dict(session.cookies)}")
    
    # POST search
    data = {
        "district_id": dist_id,
        "block_id": block_id,
        "crop_id": crop_id,
    }
    r3 = session.post(f"{BASE}/Seed/result/en", data=data)
    print(f"Status: {r3.status_code}")
    print(f"Content-Type: {r3.headers.get('Content-Type')}")
    
    # Look for ng-init with seed data
    import re
    ng_init_match = re.search(r"ng-init=['\"](.+?)['\"]", r3.text)
    if ng_init_match:
        init_text = ng_init_match.group(1)
        print(f"\nFound ng-init! (length={len(init_text)} chars)")
        print(f"First 500 chars: {init_text[:500]}")
    else:
        print("\nNo ng-init found. Checking raw HTML length...")
        print(f"HTML length: {len(r3.text)} chars")
        # Look for any JSON-like structure
        json_match = re.search(r"seed_list\s*=\s*(\[.+?\])", r3.text, re.DOTALL)
        if json_match:
            print(f"Found seed_list! First 500 chars: {json_match.group(1)[:500]}")
        else:
            # Just print a chunk around 'seed' keyword
            idx = r3.text.lower().find("seed_list")
            if idx >= 0:
                print(f"Found 'seed_list' at char {idx}:")
                print(r3.text[idx:idx+500])
            else:
                print("No 'seed_list' found in response")
                # Print a portion of the body to understand the structure
                print(f"Body snippet: {r3.text[1000:2000]}")

# ─── TEST 4: Horticulture Dept entry page ────
print(f"\n{'='*60}")
print("TEST 4: Horticulture Seed Entry Page")
print("=" * 60)
r4 = requests.get(f"{BASE}/Horti_seed/index/en", headers=headers)
print(f"Status: {r4.status_code}")

p2 = SelectParser()
p2.feed(r4.text)
for sid, opts in p2.selects.items():
    print(f"\n  <select id='{sid}'> ({len(opts)} total options):")
    for v, t in opts[:5]:
        print(f"    value={v:>6s}  text={t}")
    if len(opts) > 5:
        print(f"    ... and {len(opts)-5} more")

# ─── TEST 5: Horticulture Farm/Park (external domain) ────
print(f"\n{'='*60}")
print("TEST 5: Horticulture FARM/PARK Stocks (tnhorticulture.com)")
print("=" * 60)
r5 = requests.get("https://tnhorticulture.com/farm_inputs/Report/report/1/en", headers=headers, timeout=10)
print(f"Status: {r5.status_code}")
print(f"Content-Type: {r5.headers.get('Content-Type')}")
print(f"HTML length: {len(r5.text)} chars")

# Check for data table
if "DataTable" in r5.text or "datatable" in r5.text.lower():
    print("DataTable detected!")
if "<table" in r5.text:
    # Count rows
    row_count = r5.text.count("<tr")
    print(f"Table rows: ~{row_count}")

# ─── TEST 6: Season Wise Seed page ─────
print(f"\n{'='*60}")
print("TEST 6: Season Wise Seed Availability Page")
print("=" * 60)
r6 = requests.get(f"{BASE}/Season/index/en", headers=headers)
print(f"Status: {r6.status_code}")

p3 = SelectParser()
p3.feed(r6.text)
for sid, opts in p3.selects.items():
    print(f"\n  <select id='{sid}'> ({len(opts)} total options):")
    for v, t in opts[:5]:
        print(f"    value={v:>6s}  text={t}")
    if len(opts) > 5:
        print(f"    ... and {len(opts)-5} more")

print("\n\nDone!")
