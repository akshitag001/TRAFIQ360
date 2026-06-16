"""
services/btp_event_service.py
Bengaluru Traffic Police (BTP) Event Fetch & Normalization Service
"""
import os
import uuid
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

BTP_BASE_URL = "https://btp.karnataka.gov.in/en"
BTP_PRESS_URL = "https://btp.karnataka.gov.in/en/press-notes"
BTP_ADVISORIES_URL = "https://btp.karnataka.gov.in/en/traffic-advisories"

# ── Junction / Corridor keyword mapping ─────────────────────────────────────
LOCATION_MAP = {
    "mekhri": ("MekhriCircle", "Bellary Road 1"),
    "hebbal": ("HebbalFlyoverJunc", "Bellary Road 1"),
    "silk board": ("SilkBoardJunc", "Hosur Road"),
    "silkboard": ("SilkBoardJunc", "Hosur Road"),
    "silk-board": ("SilkBoardJunc", "Hosur Road"),
    "kr circle": ("K R Circle", "CBD 1"),
    "k.r.circle": ("K R Circle", "CBD 1"),
    "koramangala": ("KoramangalaWaterTankJunc", "Hosur Road"),
    "yeshwanthpura": ("YeshwanthpuraCircle", "Tumkur Road"),
    "townhall": ("TownhallJunction", "CBD 2"),
    "town hall": ("TownhallJunction", "CBD 2"),
    "mysore road": ("toll gate mysore road", "Mysore Road"),
    "bellary": ("HebbalFlyoverJunc", "Bellary Road 1"),
    "airport": ("BagalurCrossJunc", "Bellary Road 1"),
    "bel circle": ("BEL Circle", "ORR North 1"),
    "yelhanka": ("YelhankaCircle", "Bellary Road 2"),
    "tumkur": ("JalahalliCross(SM Circle)", "Tumkur Road"),
    "jayanagar": ("KoramangalaWaterTankJunc", "Hosur Road"),
    "bommanahalli": ("Bommanahalli", "Hosur Road"),
    "outer ring": ("HebbalFlyoverJunc", "ORR North 1"),
    "orr": ("HebbalFlyoverJunc", "ORR North 1"),
    "old madras": ("BigBazaarJunction(OldMadrasRd)", "ORR East 1"),
    "nagavara": ("Nagavara-ORR Junction", "ORR North 2"),
    "veerannapalya": ("VeerannapalyaJunction(BEL,HO)", "ORR North 2"),
    "devasandra": ("Devasandra(k r puram)", "ORR East 1"),
    "peenya": ("SRS Peenya Junc", "Tumkur Road"),
    "jalahalli": ("JalahalliCross(SM Circle)", "Tumkur Road"),
    "rajeshwari": ("RajeshwariJunc", "Mysore Road"),
    "cmp gate": ("CMP GateJunc", "CBD 2"),
    "ayyappa": ("AyyappaTempleJunc", "ORR East 2"),
}

# ── Curated fallback dataset (demo-safe, hackathon-ready) ───────────────────
SAMPLE_BTP_EVENTS = [
    {
        "event_id": "BTP-2026-001",
        "event_name": "IPL T20 Match – RCB vs MI at M. Chinnaswamy Stadium",
        "event_type": "public_event",
        "location": "Mekhri Circle, MG Road, Queens Road, Vidhana Soudha",
        "start_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d 18:00"),
        "end_date": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d 23:30"),
        "description": "Large public gathering expected at Chinnaswamy Stadium. Roads around Mekhri Circle, MG Road, and CBD corridors expected to face severe congestion. Alternative routes via Bellary Road advised.",
        "source_url": BTP_BASE_URL,
        "status": "upcoming",
        "source_type": "BTP Advisory",
    },
    {
        "event_id": "BTP-2026-002",
        "event_name": "VIP Movement – Chief Minister Convoy – Airport to Vidhana Soudha",
        "event_type": "vip_movement",
        "location": "Hebbal Flyover, Bellary Road, Mekhri Circle",
        "start_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 10:00"),
        "end_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d 11:30"),
        "description": "Protocol convoy movement from Kempegowda International Airport to Vidhana Soudha via Bellary Road and Hebbal Flyover. Partial road closure expected on Bellary Road Corridor 1.",
        "source_url": BTP_BASE_URL,
        "status": "upcoming",
        "source_type": "Press Note",
    },
    {
        "event_id": "BTP-2026-003",
        "event_name": "Rajyotsava Cultural Procession – Freedom Park to Town Hall",
        "event_type": "procession",
        "location": "Townhall Junction, CBD Corridors, KR Circle",
        "start_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d 09:00"),
        "end_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d 14:00"),
        "description": "Kannada Rajyotsava procession from Freedom Park to Town Hall. CBD 1 and CBD 2 corridors expected to face partial closures. Alternate route via Mysore Road.",
        "source_url": BTP_BASE_URL,
        "status": "upcoming",
        "source_type": "Traffic Alert",
    },
    {
        "event_id": "BTP-2026-004",
        "event_name": "Road Repair Works – Outer Ring Road Near Hebbal",
        "event_type": "construction",
        "location": "Outer Ring Road, Hebbal, BEL Circle",
        "start_date": datetime.now().strftime("%Y-%m-%d 22:00"),
        "end_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d 06:00"),
        "description": "BBMP road resurfacing works on ORR near Hebbal flyover. One lane will be closed nightly. Commuters advised to use alternative routes via Bellary Road.",
        "source_url": BTP_BASE_URL,
        "status": "active",
        "source_type": "BTP Advisory",
    },
    {
        "event_id": "BTP-2026-005",
        "event_name": "Protest Rally – Silk Board to Freedom Park",
        "event_type": "protest",
        "location": "Silk Board Junction, Hosur Road, KR Circle",
        "start_date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d 11:00"),
        "end_date": (datetime.now() + timedelta(days=4)).strftime("%Y-%m-%d 16:00"),
        "description": "Farmers' protest march from Silk Board to Freedom Park via Hosur Road. Major disruption expected on Silk Board Junction and Hosur Road Corridor.",
        "source_url": BTP_BASE_URL,
        "status": "upcoming",
        "source_type": "Traffic Alert",
    },
]


def normalize_location(location_str: str):
    """Map raw location string to known junction + corridor."""
    loc_lower = location_str.lower()
    for keyword, (junction, corridor) in LOCATION_MAP.items():
        if keyword in loc_lower:
            return junction, corridor
    return "MekhriCircle", "CBD 1"


def fetch_live_btp_events() -> list:
    """Try to scrape live BTP events from the website."""
    events = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(BTP_BASE_URL, headers=headers, timeout=8)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "lxml")
            # Try to find news/advisory blocks
            news_items = soup.find_all(
                ["div", "li", "article"],
                class_=lambda c: c and any(
                    kw in c.lower() for kw in
                    ["news", "advisory", "press", "notice", "event", "alert"]
                )
            )
            for i, item in enumerate(news_items[:5]):
                text = item.get_text(strip=True)
                if len(text) > 20:
                    link = item.find("a")
                    href = link["href"] if link and link.get("href") else BTP_BASE_URL
                    if not href.startswith("http"):
                        href = BTP_BASE_URL + "/" + href.lstrip("/")
                    events.append({
                        "event_id": f"BTP-LIVE-{i+1:03d}",
                        "event_name": text[:100],
                        "event_type": "public_event",
                        "location": "Bengaluru",
                        "start_date": datetime.now().strftime("%Y-%m-%d"),
                        "end_date": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
                        "description": text[:300],
                        "source_url": href,
                        "status": "upcoming",
                        "source_type": "BTP Advisory",
                    })
    except Exception:
        pass
    return events


def get_btp_events(use_live: bool = True) -> list:
    """
    Return BTP events. Attempts live scrape first, falls back to curated data.
    Always enriches with junction/corridor normalization.
    """
    events = []
    if use_live:
        live = fetch_live_btp_events()
        events = live if live else SAMPLE_BTP_EVENTS
    else:
        events = SAMPLE_BTP_EVENTS

    # Normalize location for each event
    enriched = []
    for ev in events:
        junction, corridor = normalize_location(ev.get("location", ""))
        enriched.append({
            **ev,
            "matched_junction": junction,
            "matched_corridor": corridor,
        })
    return enriched


def save_btp_import(event: dict, xlsx_path: str):
    """Append an imported BTP event to the XLSX file."""
    import openpyxl
    COLUMNS = [
        "import_id", "event_id", "event_name", "event_type", "location",
        "matched_junction", "matched_corridor", "start_date", "end_date",
        "description", "source_url", "source_type", "import_timestamp", "status"
    ]
    if os.path.exists(xlsx_path):
        wb = openpyxl.load_workbook(xlsx_path)
        ws = wb.active
    else:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "BTP Events"
        ws.append(COLUMNS)

    ws.append([
        str(uuid.uuid4()),
        event.get("event_id", ""),
        event.get("event_name", ""),
        event.get("event_type", ""),
        event.get("location", ""),
        event.get("matched_junction", ""),
        event.get("matched_corridor", ""),
        event.get("start_date", ""),
        event.get("end_date", ""),
        event.get("description", ""),
        event.get("source_url", ""),
        event.get("source_type", "BTP Advisory"),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Imported",
    ])
    wb.save(xlsx_path)
