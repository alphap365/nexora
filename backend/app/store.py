"""Feed aggregation and the in-memory article cache.

Design notes
------------
* Fetching is pure standard library (``urllib`` + ``xml.etree``), so the demo
  installs in seconds and has no scraping/parsing dependencies.
* Feeds are fetched concurrently on a small thread pool, then merged into a
  single recency-sorted list held behind a lock.
* A background task refreshes the cache every few minutes; the API never
  blocks on the network.
"""

from __future__ import annotations

import hashlib
import html
import logging
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from urllib.request import Request, urlopen
from xml.etree import ElementTree as ET

from .models import Article, Category
from .seed import SEED_ARTICLES
from .sources import CATEGORIES, CATEGORY_LABELS, SOURCES, Source

log = logging.getLogger("nexora.store")

USER_AGENT = "NexoraDemo/1.0 (news demo; +https://example.com/nexora)"
FETCH_TIMEOUT = 9
MAX_ARTICLES = 240
TAG_RE = re.compile(r"<[^>]+>")
WS_RE = re.compile(r"\s+")
IMG_RE = re.compile(r"""<img[^>]+src=["']([^"']+)["']""", re.I)
BLOCK_RE = re.compile(r"</(?:p|div|li|h[1-6])>|<br\s*/?>", re.I)


# --------------------------------------------------------------------------- #
# Parsing helpers
# --------------------------------------------------------------------------- #
def _local(tag: str) -> str:
    """`{ns}item` -> `item` (feeds mix RSS, Atom and Dublin Core)."""
    return tag.rsplit("}", 1)[-1]


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext())


def _clean(raw: str | None, limit: int | None = None) -> str:
    if not raw:
        return ""
    text = html.unescape(TAG_RE.sub(" ", raw))
    text = WS_RE.sub(" ", text).strip()
    if limit and len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:—-")
        text = f"{cut}…"
    return text


def _paragraphs(raw: str | None) -> list[str]:
    if not raw:
        return []
    chunks = [chunk for chunk in BLOCK_RE.split(raw) if chunk and chunk.strip()]
    if len(chunks) < 2 and "\n\n" in raw:
        chunks = raw.split("\n\n")
    out = [_clean(chunk) for chunk in chunks]
    return [p for p in out if len(p) >= 60][:4]


def _parse_date(value: str) -> datetime | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        parsed = parsedate_to_datetime(value)
        if parsed is not None:
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError, IndexError):
        pass
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _iso(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _find_image(node: ET.Element, description: str) -> str | None:
    for child in node.iter():
        name = _local(child.tag)
        url = child.get("url") or child.get("href")
        if not url:
            continue
        mime = (child.get("type") or "").lower()
        if name in ("content", "thumbnail"):
            if mime and not mime.startswith("image"):
                continue
            return url
        if name in ("enclosure", "link") and mime.startswith("image"):
            return url
    match = IMG_RE.search(description or "")
    return match.group(1) if match else None


def _link(node: ET.Element) -> str:
    for child in node:
        if _local(child.tag) != "link":
            continue
        href = child.get("href")
        rel = child.get("rel")
        if href and rel in (None, "alternate"):
            return href.strip()
        if child.text and child.text.strip():
            return child.text.strip()
    return ""


def _read_minutes(text: str) -> int:
    words = len(text.split())
    return max(1, min(20, round(words / 210)))


def _article_key(url: str, title: str) -> str:
    seed = (url or title).encode("utf-8", "ignore")
    return hashlib.sha1(seed).hexdigest()[:12]


def parse_feed(payload: bytes, source: Source) -> list[Article]:
    """Turn one RSS/Atom document into articles."""
    root = ET.fromstring(payload)
    entries = [el for el in root.iter() if _local(el.tag) in ("item", "entry")]
    articles: list[Article] = []
    now = datetime.now(timezone.utc)

    for entry in entries:
        fields: dict[str, ET.Element] = {}
        for child in entry:
            fields.setdefault(_local(child.tag), child)

        title = _clean(_text(fields.get("title")))
        if not title:
            continue

        raw_description = _text(fields.get("description")) or _text(
            fields.get("summary")
        ) or _text(fields.get("content"))
        summary = _clean(raw_description, limit=240) or title
        body = _paragraphs(raw_description)
        url = _link(entry)
        published = (
            _parse_date(_text(fields.get("pubDate")))
            or _parse_date(_text(fields.get("published")))
            or _parse_date(_text(fields.get("updated")))
            or _parse_date(_text(fields.get("date")))
            or now
        )

        articles.append(
            Article(
                id=_article_key(url, title),
                title=title,
                summary=summary,
                body=body,
                source=source.name,
                category=source.category,
                category_label=CATEGORY_LABELS.get(source.category, "World"),
                url=url,
                image=_find_image(entry, raw_description),
                published_at=_iso(published),
                read_minutes=_read_minutes(" ".join([summary, *body])),
            )
        )

    return articles


def fetch_source(source: Source) -> list[Article]:
    request = Request(source.url, headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml, text/xml"})
    with urlopen(request, timeout=FETCH_TIMEOUT) as response:
        payload = response.read()
    return parse_feed(payload, source)


# --------------------------------------------------------------------------- #
# Store
# --------------------------------------------------------------------------- #
class NewsStore:
    def __init__(self, articles: list[Article] | None = None) -> None:
        self._lock = threading.RLock()
        self._articles: list[Article] = list(articles or SEED_ARTICLES)
        self._updated_at: str | None = None
        self._live = False

    # -- writing ------------------------------------------------------------
    def refresh(self) -> None:
        """Fetch every source, merge, and swap the cache. Blocking by design."""
        collected: list[Article] = []
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = [(source, pool.submit(fetch_source, source)) for source in SOURCES]
            for source, future in futures:
                try:
                    collected.extend(future.result())
                except Exception as exc:  # noqa: BLE001 - one bad feed must not stop the rest
                    log.warning("feed failed (%s): %s", source.name, exc)

        if not collected:
            log.warning("no live articles; keeping %d cached stories", len(self._articles))
            with self._lock:
                self._updated_at = _iso(datetime.now(timezone.utc))
            return

        merged = self._dedupe(collected)
        with self._lock:
            self._articles = merged[:MAX_ARTICLES]
            self._updated_at = _iso(datetime.now(timezone.utc))
            self._live = True
        log.info("cached %d stories from %d sources", len(self._articles), len(SOURCES))

    @staticmethod
    def _dedupe(articles: list[Article]) -> list[Article]:
        seen_urls: set[str] = set()
        seen_titles: set[str] = set()
        unique: list[Article] = []
        for article in sorted(articles, key=lambda item: item.published_at, reverse=True):
            title_key = re.sub(r"[^a-z0-9]+", "", article.title.lower())[:80]
            if article.url and article.url in seen_urls:
                continue
            if title_key and title_key in seen_titles:
                continue
            if article.url:
                seen_urls.add(article.url)
            seen_titles.add(title_key)
            unique.append(article)
        return unique

    # -- reading ------------------------------------------------------------
    def query(
        self,
        category: str = "top",
        q: str = "",
        limit: int = 60,
        offset: int = 0,
    ) -> tuple[list[Article], int, str | None, bool]:
        with self._lock:
            articles = list(self._articles)
            updated_at = self._updated_at
            live = self._live

        selected = (category or "top").strip().lower()
        if selected not in ("", "top", "all"):
            articles = [a for a in articles if a.category == selected]

        needle = q.strip().lower()
        if needle:
            articles = [
                a
                for a in articles
                if needle in a.title.lower()
                or needle in a.summary.lower()
                or needle in a.source.lower()
            ]

        return articles[offset : offset + limit], len(articles), updated_at, live

    def get(self, article_id: str) -> Article | None:
        with self._lock:
            for article in self._articles:
                if article.id == article_id:
                    return article
        return None

    def categories(self) -> list[Category]:
        _, total, _, _ = self.query(limit=1)
        with self._lock:
            articles = list(self._articles)
        counts: dict[str, int] = {}
        for article in articles:
            counts[article.category] = counts.get(article.category, 0) + 1
        return [
            Category(id=key, label=label, count=total if key == "top" else counts.get(key, 0))
            for key, label in CATEGORIES
        ]

    def stats(self) -> dict:
        with self._lock:
            return {
                "status": "ok",
                "articles": len(self._articles),
                "live": self._live,
                "updated_at": self._updated_at,
                "sources": len(SOURCES),
            }


store = NewsStore()
