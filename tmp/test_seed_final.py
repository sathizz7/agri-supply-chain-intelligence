"""Final test: Get a non-empty seed result + Horti correct URL."""
import requests
import re
import json

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
}
BASE = "https://www.tnagrisnet.tn.gov.in/people_app"

session = requests.Session()
session.headers.update(headers)

# ─── 1. Try multiple crops to find non-empty seed_list ────
print("=" * 60)
print("1. Finding non-empty seed_list result")
print("=" * 60)

entry = session.get(f"{BASE}/Seed/seed_gov/en")

# Try Paddy (crop_id=1) with Coimbatore (id=11) which likely has stock
# getBlocks for Coimbatore
r = requests.post(f"{BASE}/Seed/getBlocks/11", headers=headers)
blocks = r.json()
print(f"Coimbatore has {len(blocks)} blocks")
print(f"First block: {json.dumps(blocks[0], indent=2)}")

# Try with Paddy (1) and first Coimbatore block
block_id = blocks[0]["id"]
for crop_id in ["1", "2", "3", "11"]:  # Paddy, Cholam, Maize, Blackgram
    data = {"district_id": "11", "block_id": block_id, "crop_id": crop_id}
    r2 = session.post(f"{BASE}/Seed/result/en", data=data) 
    
    # Parse ng-init
    ng_inits = re.findall(r"ng-init=['\"](.+?)['\"]", r2.text)
    seed_match = None
    for init in ng_inits:
        if "seed_list=" in init:
            _, raw = init.split("seed_list=", 1)
            if raw != "[]":
                seed_match = raw
                break
    
    if seed_match:
        print(f"\nFound data with crop_id={crop_id}!")
        # Parse it
        bracket_count = 0
        end_idx = 0
        for i, c in enumerate(seed_match):
            if c == "[": bracket_count += 1
            elif c == "]": bracket_count -= 1
            if bracket_count == 0:
                end_idx = i + 1
                break
        raw_json = seed_match[:end_idx].replace("\n", " ").replace("\\n", " ")
        try:
            seed_list = json.loads(raw_json)
            print(f"Parsed {len(seed_list)} seed records")
            print(f"\nKeys: {list(seed_list[0].keys())}")
            print(f"\nFirst record:")
            print(json.dumps(seed_list[0], indent=2, ensure_ascii=False))
        except json.JSONDecodeError as e:
            print(f"JSON error: {e}")
            print(f"Raw first 500: {raw_json[:500]}")
        break
    else:
        print(f"  crop_id={crop_id}: empty result")

# Also check cocn_list
for init in ng_inits:
    if "cocn_list=" in init:
        _, raw = init.split("cocn_list=", 1)
        print(f"\n  cocn_list content: {raw[:200]}")

# ─── 2. Try broader search (all blocks) ────
print(f"\n{'=' * 60}")
print("2. Try without specific block (block_id=0 or empty)")
print("=" * 60)

for block_val in ["", "0"]:
    data = {"district_id": "11", "block_id": block_val, "crop_id": "1"}
    r3 = session.post(f"{BASE}/Seed/result/en", data=data)
    ng_inits = re.findall(r"ng-init=['\"](.+?)['\"]", r3.text)
    for init in ng_inits:
        if "seed_list=" in init:
            _, raw = init.split("seed_list=", 1)
            count_approx = raw.count('"id"')
            print(f"  block_id='{block_val}': ~{count_approx} records (raw len={len(raw)})")
            if count_approx > 0 and count_approx <= 5:
                bracket_count = 0
                end_idx = 0
                for i, c in enumerate(raw):
                    if c == "[": bracket_count += 1
                    elif c == "]": bracket_count -= 1
                    if bracket_count == 0:
                        end_idx = i + 1
                        break
                raw_json = raw[:end_idx].replace("\n", " ").replace("\\n", " ")
                try:
                    parsed = json.loads(raw_json)
                    print(f"    Record keys: {list(parsed[0].keys())}")
                    print(f"    First record: {json.dumps(parsed[0], indent=2, ensure_ascii=False)}")
                except:
                    pass
            break

# ─── 3. Horticulture correct endpoint discovery ────
print(f"\n{'=' * 60}")
print("3. Horticulture - finding correct getBlocks URL")
print("=" * 60)

# Try various URL patterns
patterns = [
    f"{BASE}/Horti_seed/getBlocks/30",
    f"{BASE}/Horti_seed/getBlock/30",
    f"{BASE}/Horti_seed/get_blocks/30",
    f"{BASE}/Horti_seed/loadBlock/30",
    f"{BASE}/Horti_seed/loadBlocks/30",
]
for url in patterns:
    try:
        r4 = requests.post(url, headers=headers, timeout=5)
        print(f"  POST {url.split('/people_app')[1]} -> {r4.status_code} (len={len(r4.text)})")
        if r4.status_code == 200 and len(r4.text) < 5000:
            try:
                data = r4.json()
                print(f"    JSON! {len(data)} items. First: {data[0] if data else 'empty'}")
                break
            except:
                if "404" not in r4.text:
                    print(f"    Body: {r4.text[:200]}")
    except Exception as e:
        print(f"  {url}: {e}")

# ─── 4. Check the Horti entry page source for ajax URLs ────
print(f"\n{'=' * 60}")
print("4. Horti page - extracting JS URLs from source")
print("=" * 60)
r5 = requests.get(f"{BASE}/Horti_seed/index/en", headers=headers)
# Find any URLs in javascript
js_urls = re.findall(r"['\"](?:/people_app/[^'\"]+|https?://[^'\"]+)['\"]", r5.text)
print(f"Found {len(js_urls)} URLs in page source:")
for url in sorted(set(js_urls)):
    print(f"  {url}")

# Also find any $http calls or ajax patterns
ajax_patterns = re.findall(r"\$http\.(post|get)\s*\(\s*['\"]([^'\"]+)['\"]", r5.text)
print(f"\nAngularJS $http calls:")
for method, url in ajax_patterns:
    print(f"  {method.upper()} {url}")

# Also look for function definitions that handle block loading
fn_matches = re.findall(r"function\s+(\w+)\s*\(", r5.text)
print(f"\nJS functions: {fn_matches}")

# Find ng-change handlers
ng_changes = re.findall(r'ng-change=["\']([^"\']+)["\']', r5.text)
print(f"\nng-change handlers: {ng_changes}")

print("\n\nDone!")
