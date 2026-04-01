"""Deep dive: ng-init structure and block JSON format."""
import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
}
BASE = "https://www.tnagrisnet.tn.gov.in/people_app"

# ─── 1. getBlocks response structure ────
print("=" * 60)
print("1. getBlocks JSON structure (Ariyalur, id=30)")
print("=" * 60)
r = requests.post(f"{BASE}/Seed/getBlocks/30", headers=headers)
blocks = r.json()
print(f"Total blocks: {len(blocks)}")
print(f"First block keys: {list(blocks[0].keys())}")
print(f"\nFirst 3 blocks (pretty):")
print(json.dumps(blocks[:3], indent=2))

# ─── 2. Seed result ng-init structure ────
print(f"\n{'=' * 60}")
print("2. Seed result ng-init structure (Ariyalur, first block, first crop)")
print("=" * 60)

session = requests.Session()
session.headers.update(headers)
entry = session.get(f"{BASE}/Seed/seed_gov/en")

# Use first block and first crop  
block_id = blocks[0]["id"]
data = {"district_id": "30", "block_id": block_id, "crop_id": "1056"}
r2 = session.post(f"{BASE}/Seed/result/en", data=data)

# Extract ALL ng-init attributes
ng_inits = re.findall(r"ng-init=['\"](.+?)['\"]", r2.text)
print(f"Found {len(ng_inits)} ng-init attributes")
for i, init in enumerate(ng_inits):
    print(f"\n  ng-init #{i}: (length={len(init)} chars)")
    print(f"  Content: {init[:300]}...")

# Try to extract and parse the seed_list JSON
seed_match = re.search(r"seed_list\s*=\s*(\[.*?\])\s*[;'\"]", r2.text, re.DOTALL)
if seed_match:
    raw_json = seed_match.group(1)
    # Clean up literal \n
    raw_json = raw_json.replace("\n", " ")
    try:
        seed_list = json.loads(raw_json)
        print(f"\n\nParsed seed_list: {len(seed_list)} records")
        if seed_list:
            print(f"First record keys: {list(seed_list[0].keys())}")
            print(f"\nFirst record (pretty):")
            print(json.dumps(seed_list[0], indent=2, ensure_ascii=False))
    except json.JSONDecodeError as e:
        print(f"JSON parse failed: {e}")
        print(f"Raw (first 500): {raw_json[:500]}")
else:
    # Try broader pattern
    seed_match2 = re.search(r"seed_list\s*=\s*(\[.+)", r2.text, re.DOTALL)
    if seed_match2:
        raw = seed_match2.group(1)
        # Find the closing bracket
        bracket_count = 0
        end_idx = 0
        for i, c in enumerate(raw):
            if c == "[": bracket_count += 1
            elif c == "]": bracket_count -= 1
            if bracket_count == 0:
                end_idx = i + 1
                break
        raw_json = raw[:end_idx].replace("\n", " ")
        try:
            seed_list = json.loads(raw_json)
            print(f"\n\nParsed seed_list (method 2): {len(seed_list)} records")
            if seed_list:
                print(f"First record keys: {list(seed_list[0].keys())}")
                print(f"\nFirst record (pretty):")
                print(json.dumps(seed_list[0], indent=2, ensure_ascii=False))
                if len(seed_list) > 1:
                    print(f"\nSecond record (pretty):")
                    print(json.dumps(seed_list[1], indent=2, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"JSON parse failed: {e}")
            print(f"Raw (first 800): {raw_json[:800]}")
    else:
        print("No seed_list found at all!")
        # Look for any variable assignment
        assignments = re.findall(r"(\w+_list)\s*=\s*\[", r2.text)
        print(f"Found list assignments: {assignments}")
        # Print html around seed area
        idx = r2.text.find("ng-init")
        if idx >= 0:
            print(f"\nHTML around ng-init: ...{r2.text[idx:idx+600]}...")

# ─── 3. Crop list ────
print(f"\n{'=' * 60}")
print("3. Full crop list from entry page")
print("=" * 60)
from html.parser import HTMLParser
class CropParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.in_crop = False
        self.options = []
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if tag == "select" and d.get("id") == "crop_id":
            self.in_crop = True
        elif tag == "option" and self.in_crop:
            self.options.append((d.get("value",""), ""))
    def handle_data(self, data):
        if self.in_crop and self.options:
            v, _ = self.options[-1]
            self.options[-1] = (v, data.strip())
    def handle_endtag(self, tag):
        if tag == "select" and self.in_crop:
            self.in_crop = False

cp = CropParser()
cp.feed(entry.text)
print(f"Total crops: {len(cp.options)}")
for v, t in cp.options[:15]:
    print(f"  id={v:>6s}  name={t}")
if len(cp.options) > 15:
    print(f"  ... and {len(cp.options)-15} more")

# ─── 4. Horticulture getBlocks + loadStockType ────
print(f"\n{'=' * 60}")
print("4. Horticulture: getBlocks + loadStockType")
print("=" * 60)

# Horti getBlocks
r3 = requests.post(f"{BASE}/Horti_seed/getBlocks/30", headers=headers)
print(f"Horti getBlocks status: {r3.status_code}")
print(f"Content-Type: {r3.headers.get('Content-Type')}")
print(f"Body (first 300): {r3.text[:300]}")

try:
    horti_blocks = r3.json()
    print(f"\nParsed {len(horti_blocks)} blocks")
    if horti_blocks:
        print(f"Keys: {list(horti_blocks[0].keys())}")
        print(json.dumps(horti_blocks[0], indent=2))
        
        # loadStockType
        hblock_id = horti_blocks[0].get("id", horti_blocks[0].get("block_id", ""))
        r4 = requests.post(f"{BASE}/Horti_seed/loadStockType/{hblock_id}", headers=headers)
        print(f"\nloadStockType status: {r4.status_code}")
        print(f"Body: {r4.text[:500]}")
except Exception as e:
    print(f"Parse error: {e}")

# ─── 5. Horticulture FARM/PARK table structure ────
print(f"\n{'=' * 60}")
print("5. Horticulture FARM/PARK table structure (category 1)")
print("=" * 60)
r5 = requests.get("https://tnhorticulture.com/farm_inputs/Report/report/1/en", headers=headers, timeout=15)
# Extract table headers
th_match = re.findall(r"<th[^>]*>(.*?)</th>", r5.text, re.DOTALL)
print(f"Table headers ({len(th_match)}):")
for h in th_match[:15]:
    clean = re.sub(r"<[^>]+>", "", h).strip()
    if clean:
        print(f"  {clean}")

# Extract category buttons/links
cat_links = re.findall(r'report/(\d+)/en["\s>]', r5.text)
print(f"\nCategory IDs found in page: {sorted(set(cat_links))}")

# Count data rows (excluding header)
tbody = r5.text.find("<tbody")
if tbody > 0:
    body_section = r5.text[tbody:]
    data_rows = body_section.count("<tr")
    print(f"Data rows in tbody: {data_rows}")

print("\n\nDone!")
