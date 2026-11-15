"""Curated RSS sources and the topic taxonomy they map onto."""

from __future__ import annotations

from dataclasses import dataclass

# (id, label) — "top" is a virtual topic meaning "everything, newest first".
CATEGORIES: list[tuple[str, str]] = [
    ("top", "Top"),
    ("world", "World"),
    ("tech", "Technology"),
    ("science", "Science"),
    ("business", "Business"),
    ("culture", "Culture"),
]

CATEGORY_LABELS: dict[str, str] = dict(CATEGORIES)


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    category: str


SOURCES: list[Source] = [
    Source("BBC News", "https://feeds.bbci.co.uk/news/rss.xml", "world"),
    Source("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml", "tech"),
    Source("The Guardian", "https://www.theguardian.com/world/rss", "world"),
    Source("The Guardian Culture", "https://www.theguardian.com/culture/rss", "culture"),
    Source("NPR News", "https://feeds.npr.org/1001/rss.xml", "world"),
    Source("Al Jazeera", "https://www.aljazeera.com/xml/rss/all.xml", "world"),
    Source("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", "tech"),
    Source("ScienceDaily", "https://www.sciencedaily.com/rss/all.xml", "science"),
    Source("MarketWatch", "https://feeds.content.dowjones.io/public/rss/mw_topstories", "business"),
    Source("Hacker News", "https://hnrss.org/frontpage", "tech"),
]
