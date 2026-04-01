import requests
from bs4 import BeautifulSoup

url = "http://115.243.209.84/people_app/fertilizer_price/index/en/20/2020"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "en-US,en;q=0.9,ta;q=0.8",
}

print(f"1. Fetching URL: {url}")
resp = requests.get(url, headers=headers)
resp.raise_for_status()

soup = BeautifulSoup(resp.text, "html.parser")
select = soup.find("select", id="fert_id")
products = {}

for option in select.find_all("option"):
    val = option.get("value", "").strip()
    text = option.get_text(strip=True)
    if val and val != "0":
        products[int(val)] = text

print(f"2. Found {len(products)} products! First 3 products:")
count = 0
for pid, pname in products.items():
    if count >= 3:
        break
    count += 1
    
    api_url = f"http://115.243.209.84/people_app/fertilizer_price/fertDetails/{pid}"
    print(f"\n   -> Fetching {pname} (ID: {pid}) via POST {api_url}")
    api_resp = requests.post(api_url, headers=headers)
    
    # Ignore Content-Type, just try JSON parse
    try:
        data = api_resp.json()
        print(f"      Success! Server returned JSON array with {len(data)} items:")
        for item in data:
            print(f"        Company: {item.get('company')}, Price: {item.get('price')} Rs/50kgs")
    except ValueError:
        print("      Failed! Server did not return JSON.")
