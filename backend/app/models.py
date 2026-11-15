"""API models.

These are the contract between the Python engine and every client
(the bundled web reader and the Kotlin/Compose app).
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Article(BaseModel):
    """A single story in the feed."""

    id: str
    title: str
    summary: str = ""
    body: list[str] = Field(default_factory=list)
    source: str = ""
    category: str = "world"
    category_label: str = "World"
    url: str = ""
    image: str | None = None
    published_at: str = ""
    read_minutes: int = 2


class Category(BaseModel):
    """A navigable topic, with its current story count."""

    id: str
    label: str
    count: int = 0


class FeedResponse(BaseModel):
    """Payload returned by ``GET /api/articles``."""

    articles: list[Article]
    total: int
    updated_at: str | None = None
    categories: list[Category]
    live: bool = False
