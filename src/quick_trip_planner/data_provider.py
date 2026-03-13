"""Download and seed airport/route data from OpenFlights into SQLite.

Data source: https://openflights.org/data
License: Open Database License (ODbL)

Schedule columns (days, dep_am, dep_pm, etc.) are preserved but left NULL
for routes sourced from OpenFlights. Future per-country enrichment providers
(e.g. AENA scraper for Spain) can populate them.
"""

import csv
import io
import json
import logging
import sqlite3
from urllib.request import urlopen

logger = logging.getLogger(__name__)

_AIRPORTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
_ROUTES_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/routes.dat"

# OpenFlights uses \N as a NULL marker in CSV fields
_NULL = chr(92) + "N"  # backslash + N

# ISO 3166 country name → 2-letter code mapping.
# OpenFlights uses full English names; we need codes for the countries table.
# This covers all countries present in the OpenFlights dataset.
COUNTRY_NAME_TO_CODE: dict[str, str] = {
    "Afghanistan": "AF", "Albania": "AL", "Algeria": "DZ", "American Samoa": "AS",
    "Angola": "AO", "Anguilla": "AI", "Antarctica": "AQ", "Antigua and Barbuda": "AG",
    "Argentina": "AR", "Armenia": "AM", "Aruba": "AW", "Australia": "AU",
    "Austria": "AT", "Azerbaijan": "AZ", "Bahamas": "BS", "Bahrain": "BH",
    "Bangladesh": "BD", "Barbados": "BB", "Belarus": "BY", "Belgium": "BE",
    "Belize": "BZ", "Benin": "BJ", "Bermuda": "BM", "Bhutan": "BT",
    "Bolivia": "BO", "Bosnia and Herzegovina": "BA", "Botswana": "BW", "Brazil": "BR",
    "British Indian Ocean Territory": "IO", "British Virgin Islands": "VG",
    "Brunei": "BN", "Bulgaria": "BG", "Burkina Faso": "BF", "Burma": "MM",
    "Burundi": "BI", "Cambodia": "KH", "Cameroon": "CM", "Canada": "CA",
    "Cape Verde": "CV", "Cayman Islands": "KY", "Central African Republic": "CF",
    "Chad": "TD", "Chile": "CL", "China": "CN", "Christmas Island": "CX",
    "Cocos (Keeling) Islands": "CC", "Colombia": "CO", "Comoros": "KM",
    "Congo (Brazzaville)": "CG", "Congo (Kinshasa)": "CD", "Cook Islands": "CK",
    "Costa Rica": "CR", "Cote d'Ivoire": "CI", "Croatia": "HR", "Cuba": "CU",
    "Curacao": "CW", "Cyprus": "CY", "Czech Republic": "CZ", "Czechia": "CZ",
    "Denmark": "DK", "Djibouti": "DJ", "Dominica": "DM", "Dominican Republic": "DO",
    "East Timor": "TL", "Ecuador": "EC", "Egypt": "EG", "El Salvador": "SV",
    "Equatorial Guinea": "GQ", "Eritrea": "ER", "Estonia": "EE", "Ethiopia": "ET",
    "Falkland Islands": "FK", "Faroe Islands": "FO", "Fiji": "FJ", "Finland": "FI",
    "France": "FR", "French Guiana": "GF", "French Polynesia": "PF",
    "French Southern Territories": "TF", "Gabon": "GA", "Gambia": "GM",
    "Georgia": "GE", "Germany": "DE", "Ghana": "GH", "Gibraltar": "GI",
    "Greece": "GR", "Greenland": "GL", "Grenada": "GD", "Guadeloupe": "GP",
    "Guam": "GU", "Guatemala": "GT", "Guernsey": "GG", "Guinea": "GN",
    "Guinea-Bissau": "GW", "Guyana": "GY", "Haiti": "HT", "Honduras": "HN",
    "Hong Kong": "HK", "Hungary": "HU", "Iceland": "IS", "India": "IN",
    "Indonesia": "ID", "Iran": "IR", "Iraq": "IQ", "Ireland": "IE",
    "Isle of Man": "IM", "Israel": "IL", "Italy": "IT", "Jamaica": "JM",
    "Japan": "JP", "Jersey": "JE", "Johnston Atoll": "UM", "Jordan": "JO",
    "Kazakhstan": "KZ", "Kenya": "KE", "Kiribati": "KI", "Kosovo": "XK",
    "Kuwait": "KW", "Kyrgyzstan": "KG", "Laos": "LA", "Latvia": "LV",
    "Lebanon": "LB", "Lesotho": "LS", "Liberia": "LR", "Libya": "LY",
    "Lithuania": "LT", "Luxembourg": "LU", "Macau": "MO", "Macedonia": "MK",
    "North Macedonia": "MK", "Madagascar": "MG", "Malawi": "MW", "Malaysia": "MY",
    "Maldives": "MV", "Mali": "ML", "Malta": "MT", "Marshall Islands": "MH",
    "Martinique": "MQ", "Mauritania": "MR", "Mauritius": "MU", "Mayotte": "YT",
    "Mexico": "MX", "Micronesia": "FM", "Midway Islands": "UM", "Moldova": "MD",
    "Monaco": "MC", "Mongolia": "MN", "Montenegro": "ME", "Morocco": "MA",
    "Mozambique": "MZ", "Myanmar": "MM", "Namibia": "NA", "Nauru": "NR",
    "Nepal": "NP", "Netherlands": "NL", "Netherlands Antilles": "AN",
    "New Caledonia": "NC", "New Zealand": "NZ", "Nicaragua": "NI", "Niger": "NE",
    "Nigeria": "NG", "Norfolk Island": "NF", "North Korea": "KP",
    "Northern Mariana Islands": "MP", "Norway": "NO", "Oman": "OM",
    "Pakistan": "PK", "Palau": "PW", "Palestinian Territory": "PS", "Panama": "PA",
    "Papua New Guinea": "PG", "Paraguay": "PY", "Peru": "PE", "Philippines": "PH",
    "Poland": "PL", "Portugal": "PT", "Puerto Rico": "PR", "Qatar": "QA",
    "Reunion": "RE", "Romania": "RO", "Russia": "RU", "Rwanda": "RW",
    "Saint Helena": "SH", "Saint Kitts and Nevis": "KN", "Saint Lucia": "LC",
    "Saint Pierre and Miquelon": "PM", "Saint Vincent and the Grenadines": "VC",
    "Samoa": "WS", "Sao Tome and Principe": "ST", "Saudi Arabia": "SA",
    "Senegal": "SN", "Serbia": "RS", "Seychelles": "SC", "Sierra Leone": "SL",
    "Singapore": "SG", "Slovakia": "SK", "Slovenia": "SI", "Solomon Islands": "SB",
    "Somalia": "SO", "South Africa": "ZA", "South Korea": "KR", "South Sudan": "SS",
    "Spain": "ES", "Sri Lanka": "LK", "Sudan": "SD", "Suriname": "SR",
    "Svalbard": "SJ", "Swaziland": "SZ", "Eswatini": "SZ", "Sweden": "SE",
    "Switzerland": "CH", "Syria": "SY", "Taiwan": "TW", "Tajikistan": "TJ",
    "Tanzania": "TZ", "Thailand": "TH", "Timor-Leste": "TL", "Togo": "TG",
    "Tonga": "TO", "Trinidad and Tobago": "TT", "Tunisia": "TN", "Turkey": "TR",
    "Turkmenistan": "TM", "Turks and Caicos Islands": "TC", "Tuvalu": "TV",
    "Uganda": "UG", "Ukraine": "UA", "United Arab Emirates": "AE",
    "United Kingdom": "GB", "United States": "US",
    "United States Minor Outlying Islands": "UM",
    "United States Virgin Islands": "VI", "Uruguay": "UY", "Uzbekistan": "UZ",
    "Vanuatu": "VU", "Venezuela": "VE", "Vietnam": "VN",
    "Virgin Islands": "VI", "Wake Island": "UM",
    "Wallis and Futuna": "WF", "Western Sahara": "EH", "Yemen": "YE",
    "Zambia": "ZM", "Zimbabwe": "ZW",
}

# Emoji flags keyed by ISO 2-letter code (auto-generated from regional indicator symbols)
def _flag_emoji(code: str) -> str:
    return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in code.upper())


def _download_csv(url: str) -> list[list[str]]:
    """Download a CSV file and return parsed rows."""
    logger.info("Downloading %s ...", url)
    with urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8")
    reader = csv.reader(io.StringIO(text))
    return list(reader)


def refresh_data(conn: sqlite3.Connection) -> dict[str, int]:
    """Clear and re-seed all data from OpenFlights CSVs."""
    airports_csv = _download_csv(_AIRPORTS_URL)
    routes_csv = _download_csv(_ROUTES_URL)

    conn.execute("DELETE FROM routes")
    conn.execute("DELETE FROM airports")

    # --- Parse airports ---
    # Format: id,name,city,country,iata,icao,lat,lon,alt,tz,dst,tz_db,type,source
    seen_countries: dict[str, str] = {}  # code -> name
    pending_airports: list[tuple[str, str, str, str, float, float]] = []

    for row in airports_csv:
        if len(row) < 14:
            continue
        _id, name, city, country_name, iata, _icao, lat, lon = row[:8]
        ap_type = row[12] if len(row) > 12 else ""

        # Only commercial airports with valid IATA codes
        if ap_type != "airport" or not iata or iata == _NULL or len(iata) != 3:
            continue

        code = COUNTRY_NAME_TO_CODE.get(country_name)
        if not code:
            continue

        seen_countries[code] = country_name
        try:
            pending_airports.append((iata, name, city, code, float(lat), float(lon)))
        except ValueError:
            continue

    # --- Upsert countries (must come before airports due to FK) ---
    existing = {
        row["code"]: row["enabled"]
        for row in conn.execute("SELECT code, enabled FROM countries").fetchall()
    }
    for code, country_name in seen_countries.items():
        flag = _flag_emoji(code)
        if code in existing:
            conn.execute(
                "UPDATE countries SET name = ?, flag = ?, available = 1 WHERE code = ?",
                (country_name, flag, code),
            )
        else:
            # New country: enabled only if Spain
            enabled = 1 if code == "ES" else 0
            conn.execute(
                "INSERT INTO countries (code, name, flag, enabled, available) VALUES (?, ?, ?, ?, 1)",
                (code, country_name, flag, enabled),
            )

    # --- Insert airports (countries exist now) ---
    airport_count = 0
    for ap in pending_airports:
        try:
            conn.execute(
                "INSERT OR REPLACE INTO airports (iata, name, city, country_code, lat, lon) VALUES (?, ?, ?, ?, ?, ?)",
                ap,
            )
            airport_count += 1
        except sqlite3.Error:
            continue

    # --- Parse routes ---
    # Format: airline,airline_id,src_iata,src_id,dest_iata,dest_id,codeshare,stops,equipment
    airport_iatas = {
        row["iata"]
        for row in conn.execute("SELECT iata FROM airports").fetchall()
    }

    route_count = 0
    for row in routes_csv:
        if len(row) < 8:
            continue
        src_iata, dest_iata = row[2], row[4]
        stops = row[7]

        # Only direct flights with valid IATA codes
        if (
            not src_iata or src_iata == _NULL
            or not dest_iata or dest_iata == _NULL
            or stops != "0"
        ):
            continue

        if src_iata not in airport_iatas or dest_iata not in airport_iatas:
            continue

        try:
            conn.execute(
                """INSERT OR IGNORE INTO routes
                   (origin_iata, dest_iata, days, has_am, has_pm)
                   VALUES (?, ?, '[]', 0, 0)""",
                (src_iata, dest_iata),
            )
            route_count += 1
        except sqlite3.Error:
            continue

    conn.commit()
    logger.info("Seeded %d airports, %d routes", airport_count, route_count)

    # --- Enrich Spanish routes with AENA schedule data ---
    from .aena_scraper import enrich_spanish_routes

    aena_stats = enrich_spanish_routes(conn)

    stats = {"airports": airport_count, "routes": route_count}
    stats.update(aena_stats)
    return stats
