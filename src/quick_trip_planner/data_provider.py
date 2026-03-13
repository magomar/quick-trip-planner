"""Curated seed data for airports and routes, organized by country.

Only countries marked as available=True will have their data loaded.
Currently only Spain (AENA network) is available.
"""

import json
import random
import sqlite3

COUNTRIES: list[dict] = [
    {"code": "ES", "name": "Spain", "flag": "🇪🇸", "available": True, "enabled": True},
    {"code": "GB", "name": "United Kingdom", "flag": "🇬🇧", "available": False, "enabled": False},
    {"code": "FR", "name": "France", "flag": "🇫🇷", "available": False, "enabled": False},
    {"code": "DE", "name": "Germany", "flag": "🇩🇪", "available": False, "enabled": False},
    {"code": "IT", "name": "Italy", "flag": "🇮🇹", "available": False, "enabled": False},
    {"code": "PT", "name": "Portugal", "flag": "🇵🇹", "available": False, "enabled": False},
    {"code": "NL", "name": "Netherlands", "flag": "🇳🇱", "available": False, "enabled": False},
    {"code": "BE", "name": "Belgium", "flag": "🇧🇪", "available": False, "enabled": False},
    {"code": "CH", "name": "Switzerland", "flag": "🇨🇭", "available": False, "enabled": False},
    {"code": "AT", "name": "Austria", "flag": "🇦🇹", "available": False, "enabled": False},
    {"code": "IE", "name": "Ireland", "flag": "🇮🇪", "available": False, "enabled": False},
    {"code": "SE", "name": "Sweden", "flag": "🇸🇪", "available": False, "enabled": False},
    {"code": "NO", "name": "Norway", "flag": "🇳🇴", "available": False, "enabled": False},
    {"code": "DK", "name": "Denmark", "flag": "🇩🇰", "available": False, "enabled": False},
    {"code": "FI", "name": "Finland", "flag": "🇫🇮", "available": False, "enabled": False},
    {"code": "PL", "name": "Poland", "flag": "🇵🇱", "available": False, "enabled": False},
    {"code": "CZ", "name": "Czech Republic", "flag": "🇨🇿", "available": False, "enabled": False},
    {"code": "GR", "name": "Greece", "flag": "🇬🇷", "available": False, "enabled": False},
    {"code": "TR", "name": "Turkey", "flag": "🇹🇷", "available": False, "enabled": False},
    {"code": "MA", "name": "Morocco", "flag": "🇲🇦", "available": False, "enabled": False},
    {"code": "US", "name": "United States", "flag": "🇺🇸", "available": False, "enabled": False},
    {"code": "CA", "name": "Canada", "flag": "🇨🇦", "available": False, "enabled": False},
    {"code": "MX", "name": "Mexico", "flag": "🇲🇽", "available": False, "enabled": False},
    {"code": "BR", "name": "Brazil", "flag": "🇧🇷", "available": False, "enabled": False},
    {"code": "AR", "name": "Argentina", "flag": "🇦🇷", "available": False, "enabled": False},
    {"code": "JP", "name": "Japan", "flag": "🇯🇵", "available": False, "enabled": False},
    {"code": "KR", "name": "South Korea", "flag": "🇰🇷", "available": False, "enabled": False},
    {"code": "AE", "name": "United Arab Emirates", "flag": "🇦🇪", "available": False, "enabled": False},
    {"code": "SG", "name": "Singapore", "flag": "🇸🇬", "available": False, "enabled": False},
    {"code": "AU", "name": "Australia", "flag": "🇦🇺", "available": False, "enabled": False},
]

# Full AENA airport network (Spain)
AIRPORTS_BY_COUNTRY: dict[str, list[dict]] = {
    "ES": [
        {"iata": "MAD", "name": "Adolfo Suárez Madrid–Barajas", "city": "Madrid", "lat": 40.4983, "lon": -3.5676},
        {"iata": "BCN", "name": "Josep Tarradellas Barcelona–El Prat", "city": "Barcelona", "lat": 41.2974, "lon": 2.0833},
        {"iata": "VLC", "name": "Valencia Airport", "city": "Valencia", "lat": 39.4893, "lon": -0.4816},
        {"iata": "AGP", "name": "Málaga–Costa del Sol", "city": "Málaga", "lat": 36.6749, "lon": -4.4991},
        {"iata": "ALC", "name": "Alicante–Elche Miguel Hernández", "city": "Alicante", "lat": 38.2822, "lon": -0.5582},
        {"iata": "PMI", "name": "Palma de Mallorca", "city": "Palma de Mallorca", "lat": 39.5517, "lon": 2.7388},
        {"iata": "SVQ", "name": "Seville–San Pablo", "city": "Seville", "lat": 37.418, "lon": -5.8931},
        {"iata": "BIO", "name": "Bilbao Airport", "city": "Bilbao", "lat": 43.3011, "lon": -2.9106},
        {"iata": "SCQ", "name": "Santiago de Compostela", "city": "Santiago de Compostela", "lat": 42.8963, "lon": -8.4151},
        {"iata": "TFS", "name": "Tenerife South", "city": "Tenerife", "lat": 28.0445, "lon": -16.5725},
        {"iata": "TFN", "name": "Tenerife North", "city": "Tenerife", "lat": 28.4827, "lon": -16.3415},
        {"iata": "LPA", "name": "Gran Canaria Airport", "city": "Las Palmas", "lat": 27.9319, "lon": -15.3866},
        {"iata": "IBZ", "name": "Ibiza Airport", "city": "Ibiza", "lat": 38.8729, "lon": 1.3731},
        {"iata": "MAH", "name": "Menorca Airport", "city": "Mahón", "lat": 39.8626, "lon": 4.2186},
        {"iata": "FUE", "name": "Fuerteventura Airport", "city": "Fuerteventura", "lat": 28.4527, "lon": -13.8638},
        {"iata": "ACE", "name": "Lanzarote Airport", "city": "Lanzarote", "lat": 28.9455, "lon": -13.6052},
        {"iata": "GRX", "name": "Federico García Lorca", "city": "Granada", "lat": 37.1887, "lon": -3.7774},
        {"iata": "OVD", "name": "Asturias Airport", "city": "Asturias", "lat": 43.5636, "lon": -6.0346},
        {"iata": "SDR", "name": "Seve Ballesteros–Santander", "city": "Santander", "lat": 43.4271, "lon": -3.8200},
        {"iata": "ZAZ", "name": "Zaragoza Airport", "city": "Zaragoza", "lat": 41.6662, "lon": -1.0415},
        {"iata": "VGO", "name": "Vigo–Peinador Airport", "city": "Vigo", "lat": 42.2318, "lon": -8.6267},
        {"iata": "XRY", "name": "Jerez Airport", "city": "Jerez de la Frontera", "lat": 36.7446, "lon": -6.0601},
        {"iata": "REU", "name": "Reus Airport", "city": "Reus", "lat": 41.1474, "lon": 1.1672},
        {"iata": "LEI", "name": "Almería Airport", "city": "Almería", "lat": 36.8439, "lon": -2.3701},
        {"iata": "MJV", "name": "Región de Murcia Airport", "city": "Murcia", "lat": 37.7749, "lon": -1.1252},
        {"iata": "VIT", "name": "Vitoria–Foronda Airport", "city": "Vitoria", "lat": 42.8828, "lon": -2.7245},
        {"iata": "RGS", "name": "Burgos Airport", "city": "Burgos", "lat": 42.3576, "lon": -3.6208},
        {"iata": "SPC", "name": "La Palma Airport", "city": "La Palma", "lat": 28.6265, "lon": -17.7556},
        {"iata": "VDE", "name": "El Hierro Airport", "city": "El Hierro", "lat": 27.8148, "lon": -17.8871},
        {"iata": "GMZ", "name": "La Gomera Airport", "city": "La Gomera", "lat": 28.0296, "lon": -17.2146},
        {"iata": "EAS", "name": "San Sebastián Airport", "city": "San Sebastián", "lat": 43.3565, "lon": -1.7906},
        {"iata": "LCG", "name": "A Coruña Airport", "city": "A Coruña", "lat": 43.3021, "lon": -8.3773},
        {"iata": "BJZ", "name": "Badajoz Airport", "city": "Badajoz", "lat": 38.8913, "lon": -6.8213},
        {"iata": "SLM", "name": "Salamanca Airport", "city": "Salamanca", "lat": 40.9520, "lon": -5.5019},
        {"iata": "VLL", "name": "Valladolid Airport", "city": "Valladolid", "lat": 41.7061, "lon": -4.8519},
    ],
}

# Route data: realistic domestic connections within Spain.
# Each route is (origin, dest, days, has_am, has_pm, dep_am, dep_pm, ret_am, ret_pm)
_SPAIN_ROUTES: list[tuple] = [
    # Madrid hub — connects to almost everywhere
    ("MAD", "BCN", [0,1,2,3,4,5,6], True, True, "07:00", "18:30", "09:15", "21:00"),
    ("MAD", "VLC", [0,1,2,3,4,5,6], True, True, "07:30", "19:15", "09:00", "21:30"),
    ("MAD", "AGP", [0,1,2,3,4,5,6], True, True, "07:15", "20:00", "08:45", "21:45"),
    ("MAD", "ALC", [0,1,2,3,4,5,6], True, True, "08:00", "19:00", "09:30", "20:30"),
    ("MAD", "PMI", [0,1,2,3,4,5,6], True, True, "06:45", "22:10", "08:15", "23:45"),
    ("MAD", "SVQ", [0,1,2,3,4,5,6], True, True, "07:20", "19:45", "08:50", "21:15"),
    ("MAD", "BIO", [0,1,2,3,4,5,6], True, True, "07:10", "20:30", "08:40", "22:00"),
    ("MAD", "SCQ", [0,1,2,3,4,5,6], True, True, "08:30", "18:00", "10:15", "19:45"),
    ("MAD", "TFS", [0,1,2,3,4,5,6], True, True, "08:00", "16:00", "11:30", "19:30"),
    ("MAD", "TFN", [0,1,2,3,4,5,6], True, True, "10:00", "17:00", "13:30", "20:30"),
    ("MAD", "LPA", [0,1,2,3,4,5,6], True, True, "09:00", "15:30", "12:30", "19:00"),
    ("MAD", "IBZ", [0,1,4,5,6], False, True, "17:30", None, "19:00", None),
    ("MAD", "FUE", [1,3,5,6], True, False, "09:45", None, "13:15", None),
    ("MAD", "ACE", [0,2,4,6], True, True, "08:15", "16:45", "11:45", "20:15"),
    ("MAD", "GRX", [1,2,3,4,5], True, False, "09:00", None, "10:30", None),
    ("MAD", "OVD", [0,1,2,3,4,5,6], True, True, "07:45", "19:30", "09:15", "21:00"),
    ("MAD", "VGO", [1,3,5], True, False, "08:20", None, "10:05", None),
    ("MAD", "LCG", [0,1,2,3,4,5,6], True, True, "07:50", "18:45", "09:35", "20:30"),
    ("MAD", "ZAZ", [1,3,5], True, False, "08:45", None, "10:00", None),
    ("MAD", "MAH", [4,5,6], False, True, "18:00", None, "19:30", None),
    ("MAD", "SDR", [1,3,5], True, False, "09:15", None, "10:45", None),
    ("MAD", "EAS", [1,4,5], False, True, "18:30", None, "20:00", None),
    ("MAD", "VLL", [1,3,5], True, False, "08:00", None, "09:15", None),
    ("MAD", "SPC", [2,4,6], True, False, "10:30", None, "14:00", None),

    # Barcelona hub
    ("BCN", "VLC", [1,2,3,4,5], True, False, "08:15", None, "10:45", None),
    ("BCN", "AGP", [0,1,2,3,4,5,6], True, True, "07:30", "19:00", "09:15", "20:45"),
    ("BCN", "PMI", [0,1,2,3,4,5,6], True, True, "07:00", "21:00", "08:30", "22:30"),
    ("BCN", "SVQ", [0,1,2,3,4,5,6], True, True, "08:00", "18:30", "09:45", "20:15"),
    ("BCN", "BIO", [1,2,3,4,5], True, True, "07:45", "19:15", "09:15", "20:45"),
    ("BCN", "IBZ", [0,4,5,6], False, True, "16:30", None, "18:00", None),
    ("BCN", "TFS", [0,2,4,6], True, True, "08:30", "15:00", "12:00", "18:30"),
    ("BCN", "LPA", [1,3,5], True, False, "09:00", None, "12:30", None),
    ("BCN", "MAH", [4,5,6], True, False, "09:30", None, "10:45", None),
    ("BCN", "SCQ", [1,3,5], True, False, "08:00", None, "09:45", None),
    ("BCN", "GRX", [1,3,5], False, True, "18:00", None, "19:30", None),
    ("BCN", "FUE", [3,6], True, False, "09:00", None, "12:30", None),
    ("BCN", "ACE", [2,5], True, False, "08:45", None, "12:15", None),

    # Valencia hub
    ("VLC", "PMI", [0,1,2,3,4,5,6], True, True, "06:45", "22:10", "08:15", "23:45"),
    ("VLC", "IBZ", [0,1,4,5,6], False, True, "17:30", None, "19:00", None),
    ("VLC", "SVQ", [1,3,5], True, False, "09:20", None, "11:35", None),
    ("VLC", "BIO", [0,2,4], False, True, "18:00", None, "20:15", None),
    ("VLC", "AGP", [1,4,6], True, True, "07:50", "21:00", "09:50", "22:45"),
    ("VLC", "TFN", [2,4,6], True, False, "10:00", None, "13:30", None),
    ("VLC", "TFS", [0,3,5], True, True, "08:30", "16:00", "12:00", "19:30"),
    ("VLC", "LPA", [1,4], True, False, "09:15", None, "12:45", None),
    ("VLC", "SCQ", [1,3,5], False, True, "17:00", None, "18:45", None),
    ("VLC", "OVD", [2,4], True, False, "09:00", None, "10:30", None),
    ("VLC", "LCG", [1,5], False, True, "18:30", None, "20:15", None),

    # Seville connections
    ("SVQ", "BCN", [0,1,2,3,4,5,6], True, True, "08:00", "18:30", "09:45", "20:15"),
    ("SVQ", "BIO", [1,3,5], True, False, "08:30", None, "10:15", None),
    ("SVQ", "TFS", [2,5,6], True, False, "09:00", None, "12:30", None),
    ("SVQ", "LPA", [1,4,6], True, False, "08:45", None, "12:15", None),
    ("SVQ", "PMI", [0,4,5,6], False, True, "17:00", None, "18:30", None),

    # Málaga connections
    ("AGP", "BIO", [1,3,5], True, False, "08:45", None, "10:30", None),
    ("AGP", "SCQ", [2,4,6], False, True, "18:00", None, "19:45", None),
    ("AGP", "TFS", [0,2,4,6], True, True, "08:00", "15:30", "11:30", "19:00"),
    ("AGP", "PMI", [0,1,2,3,4,5,6], True, True, "07:30", "20:00", "09:00", "21:30"),

    # Bilbao connections
    ("BIO", "PMI", [0,4,5,6], False, True, "17:30", None, "19:00", None),
    ("BIO", "TFS", [3,6], True, False, "08:30", None, "12:00", None),
    ("BIO", "LPA", [2,5], True, False, "09:00", None, "12:30", None),
    ("BIO", "AGP", [1,3,5], True, False, "08:45", None, "10:30", None),

    # Inter-island Canaries connections
    ("TFS", "LPA", [0,1,2,3,4,5,6], True, True, "07:00", "19:00", "07:45", "19:45"),
    ("TFS", "FUE", [0,1,3,5], True, False, "08:30", None, "09:30", None),
    ("TFS", "ACE", [0,2,4,6], True, False, "08:00", None, "09:15", None),
    ("TFS", "SPC", [1,3,5], True, False, "09:00", None, "09:45", None),
    ("LPA", "FUE", [0,1,2,3,4,5,6], True, True, "07:30", "18:00", "08:15", "18:45"),
    ("LPA", "ACE", [0,1,2,3,4,5,6], True, True, "08:00", "17:30", "08:45", "18:15"),
    ("LPA", "SPC", [1,3,5,6], True, False, "09:30", None, "10:15", None),

    # Balearic inter-island
    ("PMI", "IBZ", [0,1,2,3,4,5,6], True, True, "07:30", "20:00", "08:15", "20:45"),
    ("PMI", "MAH", [0,1,2,3,4,5,6], True, True, "08:00", "19:30", "08:30", "20:00"),
    ("IBZ", "MAH", [1,3,5,6], True, False, "09:00", None, "09:40", None),
]


def _random_time(start_h: int, end_h: int) -> str:
    h = random.randint(start_h, end_h)
    m = random.choice([0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55])
    return f"{h:02d}:{m:02d}"


def refresh_data(conn: sqlite3.Connection) -> dict[str, int]:
    """Clear and re-seed all data for enabled countries."""
    conn.execute("DELETE FROM routes")
    conn.execute("DELETE FROM airports")

    # Seed countries (upsert)
    for c in COUNTRIES:
        conn.execute(
            """INSERT INTO countries (code, name, flag, enabled, available)
               VALUES (?, ?, ?, ?, ?)
               ON CONFLICT(code) DO UPDATE SET name=excluded.name, flag=excluded.flag""",
            (c["code"], c["name"], c["flag"], int(c["enabled"]), int(c["available"])),
        )

    # Find enabled countries
    enabled = {
        row["code"]
        for row in conn.execute("SELECT code FROM countries WHERE enabled = 1").fetchall()
    }

    airport_count = 0
    route_count = 0

    for country_code in enabled:
        airports = AIRPORTS_BY_COUNTRY.get(country_code, [])
        for a in airports:
            conn.execute(
                "INSERT OR REPLACE INTO airports (iata, name, city, country_code, lat, lon) VALUES (?, ?, ?, ?, ?, ?)",
                (a["iata"], a["name"], a["city"], country_code, a["lat"], a["lon"]),
            )
            airport_count += 1

    # Insert routes where both origin and dest airports exist in the DB
    airport_iatas = {
        row["iata"]
        for row in conn.execute("SELECT iata FROM airports").fetchall()
    }

    if "ES" in enabled:
        for origin, dest, days, has_am, has_pm, dep_am, dep_pm, ret_am, ret_pm in _SPAIN_ROUTES:
            if origin in airport_iatas and dest in airport_iatas:
                conn.execute(
                    """INSERT OR REPLACE INTO routes
                       (origin_iata, dest_iata, days, has_am, has_pm, dep_am, dep_pm, ret_am, ret_pm)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (origin, dest, json.dumps(days), int(has_am), int(has_pm), dep_am, dep_pm, ret_am, ret_pm),
                )
                route_count += 1

    conn.commit()
    return {"airports": airport_count, "routes": route_count}
