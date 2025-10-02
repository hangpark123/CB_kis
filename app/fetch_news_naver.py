from __future__ import annotations

import datetime as dt
import html
import logging
import re
from email.utils import parsedate_to_datetime
from typing import Iterable, Optional

import httpx

from .config import settings
from .db import SessionLocal
from .keywords import COMBINED
from .models import RawEvent

LOGGER = logging.getLogger("cb.naver.fetch")
NAVER_URL = "https://openapi.naver.com/v1/search/news.json"


def _strip(text: Optional[str]) -> str:
    """Remove simple HTML decoration from the Naver API fields."""
    if not text:
        return ""
    text = re.sub(r"</?b>", "", text)
    return html.unescape(text)


def _parse_pubdate(raw: Optional[str]) -> Optional[dt.datetime]:
    """Parse the RFC822 pubDate field into an aware datetime."""
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)
    except (TypeError, ValueError):
        LOGGER.debug("Invalid pubDate value: %s", raw, exc_info=True)
        return None


def fetch_naver_news(queries: Iterable[str] | None = None) -> int:
    """Fetch convertible-bond related news from Naver and persist them."""
    client_id = settings.NAVER_CLIENT_ID
    client_secret = settings.NAVER_CLIENT_SECRET
    if not client_id or not client_secret:
        LOGGER.warning("NAVER API credentials are missing; skipping news pull")
        return 0

    if queries is None:
        queries = settings.NAVER_NEWS_QUERIES

    headers = {"X-Naver-Client-Id": client_id, "X-Naver-Client-Secret": client_secret}
    timeout = httpx.Timeout(connect=3.0, read=6.0, write=5.0, pool=3.0)

    inserted = 0
    with httpx.Client(timeout=timeout) as client, SessionLocal() as session:
        for query in queries:
            try:
                response = client.get(
                    NAVER_URL,
                    headers=headers,
                    params={"query": query, "display": 30, "sort": "date", "start": 1},
                )
                response.raise_for_status()
                payload = response.json()
            except Exception as exc:
                LOGGER.error(
                    "Failed to fetch Naver news for '%s': %s", query, exc, exc_info=True
                )
                continue

            for item in payload.get("items", []):
                title = _strip(item.get("title"))
                desc = _strip(item.get("description"))
                link = item.get("link")
                published_at = _parse_pubdate(item.get("pubDate"))

                if not re.search(COMBINED, f"{title}\n{desc}", flags=re.I):
                    continue

                session.add(
                    RawEvent(
                        source="naver_news",
                        url=link,
                        title=title,
                        content=desc,
                        corp_name_kr=None,
                        published_at=published_at,
                        raw_json=item,
                        inserted_at=dt.datetime.utcnow(),
                    )
                )
                inserted += 1

        session.commit()

    LOGGER.info("Naver ingest complete (inserted=%d)", inserted)
    return inserted
