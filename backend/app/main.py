"""FastAPI application: JSON API + the bundled web reader.

Run it with:
    python -m uvicorn app.main:app --reload --port 8000
from the ``backend/`` folder.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .models import Article, Category, FeedResponse
from .store import store

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
log = logging.getLogger("nexora.api")

STATIC_DIR = Path(__file__).resolve().parent / "static"
REFRESH_SECONDS = 300


async def _refresh_loop() -> None:
    while True:
        await asyncio.sleep(REFRESH_SECONDS)
        try:
            await asyncio.to_thread(store.refresh)
        except Exception as exc:  # noqa: BLE001 - keep the loop alive
            log.warning("scheduled refresh failed: %s", exc)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await asyncio.to_thread(store.refresh)
    task = asyncio.create_task(_refresh_loop())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    title="Nexora News API",
    description="Aggregated headlines for the Nexora web reader and Kotlin app.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return store.stats()


@app.get("/api/categories", response_model=list[Category])
def categories() -> list[Category]:
    return store.categories()


@app.get("/api/articles", response_model=FeedResponse)
def articles(
    category: str = Query("top", description="top | world | tech | science | business | culture"),
    q: str = Query("", description="Free-text search over titles, summaries and sources"),
    limit: int = Query(60, ge=1, le=120),
    offset: int = Query(0, ge=0),
) -> FeedResponse:
    items, total, updated_at, live = store.query(
        category=category, q=q, limit=limit, offset=offset
    )
    return FeedResponse(
        articles=items,
        total=total,
        updated_at=updated_at,
        categories=store.categories(),
        live=live,
    )


@app.get("/api/articles/{article_id}", response_model=Article)
def article(article_id: str) -> Article:
    found = store.get(article_id)
    if found is None:
        raise HTTPException(status_code=404, detail="Article not found")
    return found


@app.post("/api/refresh", status_code=202)
async def refresh() -> dict:
    asyncio.create_task(asyncio.to_thread(store.refresh))
    return {"status": "refreshing"}


if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR), name="assets")

    @app.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/favicon.ico", include_in_schema=False)
    def favicon() -> FileResponse:
        return FileResponse(STATIC_DIR / "favicon.svg", media_type="image/svg+xml")
