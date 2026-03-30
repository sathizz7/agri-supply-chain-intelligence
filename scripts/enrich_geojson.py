"""
One-time script: enriches the Tamil Nadu districts GeoJSON with
scraper_code (4-digit backend code) and name_ta (Tamil name).

Usage:
  python scripts/enrich_geojson.py

Output:
  data/tn-districts-enriched.geojson
  frontend/public/geo/tn-districts.geojson  (copy for frontend)
"""
import json
import shutil
from pathlib import Path

# ── Authoritative mapping: GeoJSON English name → scraper code + Tamil name ──
# Source: logs/site_snapshot.html (live portal, 2026-03-27)
MAPPING = {
    "Ariyalur":        ("3317", "அரியலூர்"),
    "Chengalpattu":    ("3338", "செங்கல்பட்டு"),
    "Chennai":         ("3302", "சென்னை"),
    "Coimbatore":      ("3333", "கோயம்புத்தூர்"),
    "Cuddalore":       ("3318", "கடலூர்"),
    "Dharmapuri":      ("3331", "தர்மபுரி"),
    "Dindigul":        ("3313", "திண்டுக்கல்"),
    "Erode":           ("3310", "ஈரோடு"),
    "Kallakurichi":    ("3337", "கள்ளக்குறிச்சி"),
    "Kanchipuram":     ("3303", "காஞ்சிபுரம்"),
    "Kanyakumari":     ("3330", "கன்னியாகுமரி"),
    "Kanniyakumari":   ("3330", "கன்னியாகுமரி"),
    "Karur":           ("3314", "கரூர்"),
    "Krishnagiri":     ("3332", "கிருஷ்ணகிரி"),
    "Madurai":         ("3324", "மதுரை"),
    "Mayiladuthurai":  ("3340", "மயிலாடுதுறை"),
    "Nagapattinam":    ("3319", "நாகப்பட்டினம்"),
    "Namakkal":        ("3309", "நாமக்கல்"),
    "Perambalur":      ("3316", "பெரம்பலூர்"),
    "Pudukkottai":     ("3322", "புதுக்கோட்டை"),
    "Ramanathapuram":  ("3327", "ராமநாதபுரம்"),
    "Ranipet":         ("3335", "ராணிப்பேட்டை"),
    "Salem":           ("3308", "சேலம்"),
    "Sivagangai":      ("3323", "சிவகங்கை"),
    "Sivaganga":       ("3323", "சிவகங்கை"),
    "Tenkasi":         ("3339", "தென்காசி"),
    "Thanjavur":       ("3321", "தஞ்சாவூர்"),
    "The Nilgiris":    ("3311", "நீலகிரி"),
    "Theni":           ("3325", "தேனி"),
    "Tiruvallur":      ("3301", "திருவள்ளூர்"),
    "Thiruvallur":     ("3301", "திருவள்ளூர்"),
    "Tiruvarur":       ("3320", "திருவாரூர்"),
    "Thiruvarur":      ("3320", "திருவாரூர்"),
    "Thoothukudi":     ("3328", "தூத்துக்குடி"),
    "Tuticorin":       ("3328", "தூத்துக்குடி"),
    "Tiruchirappalli": ("3315", "திருச்சிராப்பள்ளி"),
    "Tirunelveli":     ("3329", "திருநெல்வேலி"),
    "Tirupathur":      ("3336", "திருப்பத்தூர்"),
    "Tiruppur":        ("3334", "திருப்பூர்"),
    "Tiruvannamalai":  ("3306", "திருவண்ணாமலை"),
    "Vellore":         ("3304", "வேலூர்"),
    "Villupuram":      ("3307", "விழுப்புரம்"),
    "Virudhunagar":    ("3326", "விருதுநகர்"),
}

ROOT = Path(__file__).parent.parent
SRC  = ROOT / "data" / "TAMIL NADU_DISTRICTS (2).geojson"
OUT  = ROOT / "data" / "tn-districts-enriched.geojson"
FE   = ROOT / "frontend" / "public" / "geo" / "tn-districts.geojson"

def main():
    print(f"Reading {SRC} …")
    with open(SRC, encoding="utf-8") as f:
        geo = json.load(f)

    matched, unmatched = 0, []

    for feature in geo["features"]:
        props = feature["properties"]
        # GeoJSON uses 'dtname' or 'dist' for English district name
        en_name = props.get("dtname") or props.get("dist", "")

        if en_name in MAPPING:
            scraper_code, name_ta = MAPPING[en_name]
            props["scraper_code"] = scraper_code
            props["name_ta"] = name_ta
            matched += 1
        else:
            unmatched.append(en_name)

    print(f"Matched: {matched}/38")
    if unmatched:
        print(f"UNMATCHED ({len(unmatched)}): {unmatched}")
    else:
        print("OK: All 38 districts matched")

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(geo, f, ensure_ascii=False)
    print(f"Written: {OUT}")

    FE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(OUT, FE)
    print(f"Copied to: {FE}")

if __name__ == "__main__":
    main()
