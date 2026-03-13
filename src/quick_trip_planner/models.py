"""Pydantic models for API request/response schemas."""

from pydantic import BaseModel


class Country(BaseModel):
    code: str
    name: str
    flag: str
    enabled: bool
    available: bool


class Airport(BaseModel):
    iata: str
    name: str
    city: str
    country_code: str
    lat: float
    lon: float


class Route(BaseModel):
    id: int
    origin_iata: str
    dest_iata: str
    days: list[int]
    has_am: bool
    has_pm: bool
    dep_am: str | None = None
    dep_pm: str | None = None
    ret_am: str | None = None
    ret_pm: str | None = None


class RouteWithAirport(Route):
    dest_city: str
    dest_name: str
    dest_lat: float
    dest_lon: float
