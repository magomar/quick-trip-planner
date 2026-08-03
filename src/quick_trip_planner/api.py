"""FastAPI API routes for airports, routes, and admin country management."""

import json
import math

from fastapi import APIRouter, HTTPException

from .db import get_db
from .data_provider import refresh_data
from .models import (
    Airport,
    Country,
    DestinationRouteSummary,
    FlightDetail,
)

router = APIRouter(prefix="/api")


@router.get("/airports", response_model=list[Airport])
def list_airports(search: str | None = None):
    with get_db() as conn:
        if search:
            rows = conn.execute(
                """SELECT a.* FROM airports a
                   JOIN countries c ON a.country_code = c.code
                   WHERE c.enabled = 1
                     AND (a.city LIKE ? OR a.iata LIKE ? OR a.name LIKE ?)
                   ORDER BY a.city""",
                (f"%{search}%", f"%{search.upper()}%", f"%{search}%"),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT a.* FROM airports a
                   JOIN countries c ON a.country_code = c.code
                   WHERE c.enabled = 1
                   ORDER BY a.city""",
            ).fetchall()
    return [Airport(**dict(r)) for r in rows]


def _calculate_duration_mins(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """Calculate flight duration in minutes based on Great-Circle distance."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))
    dist_km = R * c
    flight_mins = int(25 + (dist_km / 750) * 60)
    return max(35, flight_mins)


def _enrich_flight_times(
    fl: dict, orig_lat: float, orig_lon: float, dest_lat: float, dest_lon: float
) -> dict:
    """Calculate duration and arrival time for a flight dictionary."""
    fl = dict(fl)
    duration = _calculate_duration_mins(orig_lat, orig_lon, dest_lat, dest_lon)
    fl["duration_mins"] = duration

    dep = fl.get("dep_time")
    if dep and ":" in dep:
        try:
            h, m = map(int, dep.split(":")[:2])
            arr_mins = (h * 60 + m + duration) % 1440
            fl["arr_time"] = f"{arr_mins // 60:02d}:{arr_mins % 60:02d}"
        except ValueError:
            fl["arr_time"] = None
    else:
        fl["arr_time"] = None

    return fl


@router.get("/routes/{origin_iata}", response_model=list[DestinationRouteSummary])
def get_routes(
    origin_iata: str,
    dep_day: int | None = None,
    ret_day: int | None = None,
):
    with get_db() as conn:
        routes_rows = conn.execute(
            """SELECT r.*, a.city as dest_city, a.name as dest_name, a.lat as dest_lat, a.lon as dest_lon
               FROM routes r
               JOIN airports a ON r.dest_iata = a.iata
               WHERE r.origin_iata = ?
               ORDER BY a.city""",
            (origin_iata.upper(),),
        ).fetchall()

        outbound_rows = conn.execute(
            """SELECT * FROM flights WHERE origin_iata = ?""",
            (origin_iata.upper(),),
        ).fetchall()

        return_rows = conn.execute(
            """SELECT * FROM flights WHERE dest_iata = ?""",
            (origin_iata.upper(),),
        ).fetchall()

        airports_rows = conn.execute(
            """SELECT iata, lat, lon FROM airports"""
        ).fetchall()
        coords = {r["iata"]: (r["lat"], r["lon"]) for r in airports_rows}

    outbound_by_dest: dict[str, list[dict]] = {}
    for fr in outbound_rows:
        fd = dict(fr)
        fd["days"] = json.loads(fd["days"])
        outbound_by_dest.setdefault(fd["dest_iata"], []).append(fd)

    return_by_dest: dict[str, list[dict]] = {}
    for fr in return_rows:
        fd = dict(fr)
        fd["days"] = json.loads(fd["days"])
        return_by_dest.setdefault(fd["origin_iata"], []).append(fd)

    orig_coords = coords.get(origin_iata.upper(), (40.0, -3.0))

    result = []
    for r in routes_rows:
        d = dict(r)
        days = json.loads(d["days"])
        d["days"] = days
        d["has_am"] = bool(d["has_am"])
        d["has_pm"] = bool(d["has_pm"])

        dest_iata = d["dest_iata"]
        dest_coords = coords.get(dest_iata, (d["dest_lat"], d["dest_lon"]))

        raw_outbound = outbound_by_dest.get(dest_iata, [])
        raw_return = return_by_dest.get(dest_iata, [])

        matching_outbound = []
        for fl in raw_outbound:
            if dep_day is not None and dep_day != -1:
                if dep_day not in fl["days"]:
                    continue
            enriched = _enrich_flight_times(
                fl, orig_coords[0], orig_coords[1], dest_coords[0], dest_coords[1]
            )
            matching_outbound.append(FlightDetail(**enriched))

        matching_return = []
        for fl in raw_return:
            if ret_day is not None and ret_day != -1:
                if ret_day not in fl["days"]:
                    continue
            enriched = _enrich_flight_times(
                fl, dest_coords[0], dest_coords[1], orig_coords[0], orig_coords[1]
            )
            matching_return.append(FlightDetail(**enriched))

        has_schedule = len(days) > 0 or bool(d["ret_am"] or d["ret_pm"])

        # Departure day filter check
        if dep_day is not None and dep_day != -1:
            if not has_schedule:
                continue
            if len(raw_outbound) > 0 and len(matching_outbound) == 0:
                continue
            if len(raw_outbound) == 0 and dep_day not in days:
                continue

        # Return day filter check
        if ret_day is not None and ret_day != -1:
            if not has_schedule:
                continue
            if len(raw_return) > 0 and len(matching_return) == 0:
                continue
            if len(raw_return) == 0 and ret_day not in days:
                continue

        d["has_schedule"] = has_schedule
        d["outbound_count"] = len(matching_outbound)
        d["return_count"] = len(matching_return)
        total_count = len(matching_outbound) + len(matching_return)
        d["flight_count"] = (
            total_count if total_count > 0 else (1 if has_schedule else 0)
        )
        d["outbound_flights"] = matching_outbound
        d["return_flights"] = matching_return
        d["flights"] = matching_outbound

        result.append(DestinationRouteSummary(**d))

    return result


@router.post("/data/refresh")
def trigger_refresh():
    with get_db() as conn:
        stats = refresh_data(conn)
    return {"status": "ok", "seeded": stats}


# --- Admin endpoints ---


@router.get("/admin/countries", response_model=list[Country])
def list_countries():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM countries ORDER BY name").fetchall()
    return [
        Country(
            **{
                **dict(r),
                "enabled": bool(r["enabled"]),
                "available": bool(r["available"]),
            }
        )
        for r in rows
    ]


@router.put("/admin/countries/{code}")
def toggle_country(code: str, enabled: bool):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM countries WHERE code = ?", (code.upper(),)
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Country not found")
        if not row["available"]:
            raise HTTPException(
                status_code=400,
                detail="This country is not yet available. Coming soon!",
            )

        conn.execute(
            "UPDATE countries SET enabled = ? WHERE code = ?",
            (int(enabled), code.upper()),
        )
        conn.commit()

    return {"status": "ok", "code": code.upper(), "enabled": enabled}
