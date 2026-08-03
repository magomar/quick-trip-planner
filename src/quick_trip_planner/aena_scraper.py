"""Scrape AENA Infovuelos API to enrich Spanish routes with schedule data.

AENA provides a 14-day flight schedule window via an internal JSON endpoint.
We aggregate this into day-of-week occurrence and AM/PM departure times.
"""

import json
import logging
import sqlite3
import time
from datetime import datetime
from urllib.error import URLError
from urllib.request import Request, urlopen

logger = logging.getLogger(__name__)

_BASE_URL = "https://www.aena.es/sites/Satellite"
_USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64; rv:120.0) Gecko/20100101 Firefox/120.0"
_DELAY_SECONDS = 1


def _fetch_departures(iata: str) -> list[dict]:
    """Fetch departure flights from AENA for a single airport."""
    url = f"{_BASE_URL}?pagename=AENA_ConsultarVuelos&airport={iata}&flightType=S"
    req = Request(
        url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, TimeoutError) as exc:
        logger.warning("AENA departure fetch failed for %s: %s", iata, exc)
        return []


def _fetch_arrivals(iata: str) -> list[dict]:
    """Fetch arrival flights from AENA for a single airport."""
    url = f"{_BASE_URL}?pagename=AENA_ConsultarVuelos&airport={iata}&flightType=L"
    req = Request(
        url, headers={"User-Agent": _USER_AGENT, "Accept": "application/json"}
    )
    try:
        with urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except (URLError, json.JSONDecodeError, TimeoutError) as exc:
        logger.warning("AENA arrival fetch failed for %s: %s", iata, exc)
        return []


def _extract_flights(
    flights: list[dict], current_iata: str, is_arrival: bool = False
) -> list[dict]:
    """Group flight instances by flight number/departure time and derive operational days."""
    flight_map: dict[tuple[str, str, str, str], dict] = {}
    for f in flights:
        other = f.get("iataOtro", "").strip()
        time_str = f.get("horaProgramada", "").strip()
        date_str = f.get("fecha", "").strip()
        flight_no = (
            f.get("numero", "").strip()
            or f.get("numVuelo", "").strip()
            or f.get("vuelo", "").strip()
            or None
        )
        iata_comp = f.get("iataCompania", "").strip()
        if flight_no and iata_comp and not flight_no.startswith(iata_comp):
            flight_no = f"{iata_comp}{flight_no}"

        airline = (
            f.get("nombreCompania", "").strip()
            or f.get("companyia", "").strip()
            or f.get("cia", "").strip()
            or None
        )

        if not other or not time_str or not date_str:
            continue

        dep_time = time_str[:5]

        if is_arrival:
            origin_iata = other
            dest_iata = current_iata
        else:
            origin_iata = current_iata
            dest_iata = other

        key = (origin_iata, dest_iata, flight_no or dep_time, dep_time)

        if key not in flight_map:
            flight_map[key] = {
                "origin_iata": origin_iata,
                "dest_iata": dest_iata,
                "flight_no": flight_no,
                "airline": airline,
                "dep_time": dep_time,
                "days": set(),
            }

        try:
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            js_dow = (dt.weekday() + 1) % 7  # Python Mon=0 -> JS Sun=0
            flight_map[key]["days"].add(js_dow)
        except ValueError:
            pass

    return list(flight_map.values())


def _aggregate_schedule(flights: list[dict]) -> dict[str, dict]:
    """Group flights by destination and derive route level schedule summaries."""
    routes: dict[str, dict] = {}
    for f in flights:
        dest = f.get("iataOtro", "").strip()
        time_str = f.get("horaProgramada", "").strip()
        date_str = f.get("fecha", "").strip()
        if not dest or not time_str or not date_str:
            continue

        if dest not in routes:
            routes[dest] = {"days": set(), "am_times": [], "pm_times": []}

        try:
            dt = datetime.strptime(date_str, "%d/%m/%Y")
            js_dow = (dt.weekday() + 1) % 7
            routes[dest]["days"].add(js_dow)
        except ValueError:
            pass

        try:
            hour = int(time_str.split(":")[0])
            if hour < 14:
                routes[dest]["am_times"].append(time_str[:5])
            else:
                routes[dest]["pm_times"].append(time_str[:5])
        except (ValueError, IndexError):
            pass

    return routes


def enrich_spanish_routes(conn: sqlite3.Connection) -> dict[str, int]:
    """Scrape AENA for all Spanish airports and update route schedule data and flights table."""
    airports = conn.execute(
        "SELECT iata FROM airports WHERE country_code = 'ES'"
    ).fetchall()
    iata_codes = [row["iata"] for row in airports]

    logger.info("AENA enrichment: %d Spanish airports to scrape", len(iata_codes))

    enriched_routes = 0
    enriched_airports = 0
    total_flights_inserted = 0

    for i, iata in enumerate(iata_codes):
        departures = _fetch_departures(iata)
        arrivals = _fetch_arrivals(iata)
        if not departures and not arrivals:
            if i < len(iata_codes) - 1:
                time.sleep(_DELAY_SECONDS)
            continue

        schedule = _aggregate_schedule(departures)
        outbound_flights = _extract_flights(departures, iata, is_arrival=False)
        return_flights = _extract_flights(arrivals, iata, is_arrival=True)
        all_detailed_flights = outbound_flights + return_flights

        enriched_airports += 1
        logger.info(
            "AENA [%d/%d] %s: %d departures, %d arrivals -> %d destinations (%d distinct flight schedules)",
            i + 1,
            len(iata_codes),
            iata,
            len(departures),
            len(arrivals),
            len(schedule),
            len(all_detailed_flights),
        )

        # Clear existing scraped flights for this origin airport
        conn.execute("DELETE FROM flights WHERE origin_iata = ?", (iata,))

        # Insert detailed flight records
        for fl in all_detailed_flights:
            days_list = sorted(fl["days"])
            try:
                conn.execute(
                    """INSERT OR REPLACE INTO flights
                       (origin_iata, dest_iata, flight_no, airline, dep_time, days)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (
                        fl["origin_iata"],
                        fl["dest_iata"],
                        fl["flight_no"],
                        fl["airline"],
                        fl["dep_time"],
                        json.dumps(days_list),
                    ),
                )
                total_flights_inserted += 1
            except sqlite3.Error:
                pass

        # Update routes table summary
        for dest_iata, info in schedule.items():
            days_list = sorted(info["days"])
            has_am = len(info["am_times"]) > 0
            has_pm = len(info["pm_times"]) > 0
            dep_am = min(info["am_times"]) if info["am_times"] else None
            dep_pm = max(info["pm_times"]) if info["pm_times"] else None

            updated = conn.execute(
                """UPDATE routes
                   SET days = ?, has_am = ?, has_pm = ?, dep_am = ?, dep_pm = ?
                   WHERE origin_iata = ? AND dest_iata = ?""",
                (
                    json.dumps(days_list),
                    int(has_am),
                    int(has_pm),
                    dep_am,
                    dep_pm,
                    iata,
                    dest_iata,
                ),
            ).rowcount

            if updated:
                enriched_routes += updated
            else:
                try:
                    conn.execute(
                        """INSERT OR IGNORE INTO routes
                           (origin_iata, dest_iata, days, has_am, has_pm, dep_am, dep_pm)
                           VALUES (?, ?, ?, ?, ?, ?, ?)""",
                        (
                            iata,
                            dest_iata,
                            json.dumps(days_list),
                            int(has_am),
                            int(has_pm),
                            dep_am,
                            dep_pm,
                        ),
                    )
                    enriched_routes += 1
                except sqlite3.Error:
                    pass

        conn.commit()

        if i < len(iata_codes) - 1:
            time.sleep(_DELAY_SECONDS)

    # --- Cross-reference return times from reverse routes ---
    conn.execute(
        """UPDATE routes
           SET ret_am = (SELECT r2.dep_am FROM routes r2
                         WHERE r2.origin_iata = routes.dest_iata
                           AND r2.dest_iata = routes.origin_iata),
               ret_pm = (SELECT r2.dep_pm FROM routes r2
                         WHERE r2.origin_iata = routes.dest_iata
                           AND r2.dest_iata = routes.origin_iata)
           WHERE EXISTS (
               SELECT 1 FROM routes r2
               WHERE r2.origin_iata = routes.dest_iata
                 AND r2.dest_iata = routes.origin_iata
                 AND (r2.dep_am IS NOT NULL OR r2.dep_pm IS NOT NULL)
           )"""
    )

    # Cross-reference return times in flights table
    conn.execute(
        """UPDATE flights
           SET ret_time = (
               SELECT f2.dep_time FROM flights f2
               WHERE f2.origin_iata = flights.dest_iata
                 AND f2.dest_iata = flights.origin_iata
               LIMIT 1
           )"""
    )
    conn.commit()

    logger.info(
        "AENA enrichment complete: %d airports scraped, %d routes enriched, %d flight instances saved",
        enriched_airports,
        enriched_routes,
        total_flights_inserted,
    )
    return {
        "aena_airports": enriched_airports,
        "aena_routes": enriched_routes,
        "aena_flights": total_flights_inserted,
    }
