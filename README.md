# Quick Trip Planner ✈️

A flight connections explorer that visualizes direct routes from any airport on an interactive map, filtered by departure and return day of the week. Plan weekend trips at a glance.

## Features

- 🗺️ **Interactive Map** — Leaflet-based visualization of direct flight routes
- 🔍 **Airport Search** — Autocomplete search across all enabled airports
- 📅 **Day Filtering** — Filter routes by departure and return day of the week
- 🎨 **Visual Encoding** — Blue (departure) / orange (return), solid (AM) / dashed (PM)
- 🏳️ **Country Management** — Admin page to enable/disable country airport networks
- 🔄 **Data Refresh** — Single endpoint to re-seed airport and route data

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.13, FastAPI, SQLite |
| Frontend | Vanilla HTML/JS, Tailwind CSS, Leaflet |
| Package Manager | uv |

## Quick Start

```bash
# First-time setup: install deps + seed database
make setup

# Run the dev server
make dev

# Open http://localhost:8000
```

## Available Commands

```
make help        Show all targets
make install     Install Python dependencies
make setup       First-time setup (install + seed DB)
make dev         Run dev server (port 8000, auto-reload)
make shutdown    Kill the dev server
make lint        Lint with ruff
make format      Auto-format with ruff
make refresh     Refresh data via API
make clean       Remove DB + caches
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/airports?search=` | List/search airports |
| `GET` | `/api/routes/{iata}` | Routes from an airport |
| `POST` | `/api/data/refresh` | Re-seed all data |
| `GET` | `/api/admin/countries` | List countries + status |
| `PUT` | `/api/admin/countries/{code}?enabled=` | Toggle a country |

## Current Data

- 🇪🇸 **Spain (AENA)** — 35 airports, 71 domestic routes
- 29 additional countries listed for future expansion

## Project Structure

```
├── Makefile
├── pyproject.toml
├── src/quick_trip_planner/
│   ├── main.py            # FastAPI app + static serving
│   ├── api.py             # API routes
│   ├── db.py              # SQLite schema + connection
│   ├── models.py          # Pydantic models
│   └── data_provider.py   # Seed data (airports, routes, countries)
├── static/
│   ├── index.html         # Map page
│   ├── app.js             # Map logic
│   ├── admin.html         # Admin page
│   ├── admin.js           # Admin logic
│   └── style.css          # Custom styles
└── data/
    └── trips.db           # SQLite database (auto-created)
```
