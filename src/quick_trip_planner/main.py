"""FastAPI application entry point."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .api import router
from .db import get_db, init_db
from .data_provider import refresh_data


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    # Seed data if airports table is empty
    with get_db() as conn:
        count = conn.execute("SELECT COUNT(*) FROM airports").fetchone()[0]
        if count == 0:
            refresh_data(conn)
    yield


app = FastAPI(title="Quick Trip Planner", lifespan=lifespan)
app.include_router(router)
app.mount("/", StaticFiles(directory="static", html=True), name="static")


def run():
    import uvicorn
    uvicorn.run("quick_trip_planner.main:app", host="0.0.0.0", port=8000, reload=True)
