"""FastAPI API routes for airports, routes, and admin country management."""

import json

from fastapi import APIRouter, HTTPException

from .db import get_db
from .data_provider import refresh_data
from .models import Airport, Country, RouteWithAirport

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


@router.get("/routes/{origin_iata}", response_model=list[RouteWithAirport])
def get_routes(origin_iata: str):
    with get_db() as conn:
        rows = conn.execute(
            """SELECT r.*, a.city as dest_city, a.name as dest_name, a.lat as dest_lat, a.lon as dest_lon
               FROM routes r
               JOIN airports a ON r.dest_iata = a.iata
               WHERE r.origin_iata = ?
               ORDER BY a.city""",
            (origin_iata.upper(),),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["days"] = json.loads(d["days"])
        d["has_am"] = bool(d["has_am"])
        d["has_pm"] = bool(d["has_pm"])
        result.append(RouteWithAirport(**d))
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
    return [Country(**{**dict(r), "enabled": bool(r["enabled"]), "available": bool(r["available"])}) for r in rows]


@router.put("/admin/countries/{code}")
def toggle_country(code: str, enabled: bool):
    with get_db() as conn:
        row = conn.execute("SELECT * FROM countries WHERE code = ?", (code.upper(),)).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Country not found")
        if not row["available"]:
            raise HTTPException(status_code=400, detail="This country is not yet available. Coming soon!")

        conn.execute("UPDATE countries SET enabled = ? WHERE code = ?", (int(enabled), code.upper()))
        conn.commit()

    return {"status": "ok", "code": code.upper(), "enabled": enabled}
