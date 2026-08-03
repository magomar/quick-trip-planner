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


class FlightDetail(BaseModel):
    id: int
    origin_iata: str
    dest_iata: str
    flight_no: str | None = None
    airline: str | None = None
    dep_time: str | None = None
    arr_time: str | None = None
    duration_mins: int | None = None
    days: list[int]


class DestinationRouteSummary(RouteWithAirport):
    flight_count: int = 0
    outbound_count: int = 0
    return_count: int = 0
    has_schedule: bool = False
    outbound_flights: list[FlightDetail] = []
    return_flights: list[FlightDetail] = []
    flights: list[FlightDetail] = []
