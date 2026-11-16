"""Loopback-only FastAPI event service backed by a durable SQLite database."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field

from core.event_store import connect, events_after, initialize_database, record_event


class EventInput(BaseModel):
    event_type: str = Field(min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9._-]+$")
    payload: dict[str, str] = Field(default_factory=dict)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="NEXU-OS Local Service",
    version="1.0.0",
    lifespan=lifespan,
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get("/health")
def health() -> dict[str, str]:
    with connect() as connection:
        connection.execute("SELECT 1").fetchone()
    return {"status": "ok", "database": "ok"}


@app.post("/api/events", status_code=201)
def create_event(event: EventInput) -> dict[str, int]:
    return {"id": record_event(event.event_type, event.payload)}


@app.get("/api/events")
def list_events(after: int = 0, limit: int = 100) -> list[dict[str, object]]:
    return events_after(after, limit)


@app.websocket("/api/events/live")
async def live_events(websocket: WebSocket) -> None:
    origin = websocket.headers.get("origin")
    if origin not in (None, "http://127.0.0.1:8765"):
        await websocket.close(code=1008)
        return
    await websocket.accept()
    after = 0
    try:
        while True:
            events = list_events(after=after, limit=100)
            for event in events:
                await websocket.send_json(event)
                after = int(event["id"])
            await asyncio.sleep(0.5)
    except WebSocketDisconnect:
        return


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "core.local_server:app",
        host="127.0.0.1",
        port=8765,
        access_log=False,
        workers=1,
    )
