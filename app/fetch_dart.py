from __future__ import annotations

import datetime as dt
import logging
import re
from typing import Optional

import httpx

from .config import settings
from .db import SessionLocal
from .keywords import COMBINED
from .models import RawEvent

LOGGER = logging.getLogger("cb.dart.fetch")

DART_URL = "https://opendart.fss.or.kr/api/list.json"
KST = dt.timezone(dt.timedelta(hours=9))


def _parse_receipt_datetime(raw: str | None) -> Optional[dt.datetime]:
    """Return a timezone-aware datetime parsed from a DART rcept_dt field."""
    if not raw:
        return None

    try:
        return dt.datetime.strptime(raw, "%Y%m%d%H%M%S").replace(tzinfo=KST)
    except ValueError:
        LOGGER.debug("Failed to parse rcept_dt value: %s", raw, exc_info=True)
        return None


def _should_capture(title: str) -> bool:
    """Check whether the disclosure title matches CB-related keywords."""
    return bool(title and re.search(COMBINED, title, flags=re.I))


def fetch_dart_today() -> int:
    """Fetch today's disclosures from DART and persist convertible-bond items.

    Returns the number of RawEvent records created.
    """
    api_key = settings.DART_API_KEY
    if not api_key:
        LOGGER.warning("DART_API_KEY is not configured; skipping DART fetch")
        return 0

    today = dt.datetime.now(tz=KST).strftime("%Y%m%d")
    params = {"crtfc_key": api_key, "bgn_de": today, "page_no": 1, "page_count": 100}
    timeout = httpx.Timeout(connect=3.0, read=6.0, write=5.0, pool=3.0)

    inserted = 0
    with httpx.Client(timeout=timeout) as client, SessionLocal() as session:
        try:
            response = client.get(DART_URL, params=params)
            response.raise_for_status()
            payload = response.json()
        except Exception as exc:
            LOGGER.error("Failed to fetch DART list.json: %s", exc, exc_info=True)
            return 0

        for item in payload.get("list", []):
            title = item.get("report_nm") or ""
            if not _should_capture(title):
                continue

            published_at = _parse_receipt_datetime(item.get("rcept_dt"))

            session.add(
                RawEvent(
                    source="dart",
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={item.get('rcp_no')}",
                    title=title,
                    content=None,
                    corp_name_kr=item.get("corp_name"),
                    published_at=published_at,
                    raw_json=item,
                    inserted_at=dt.datetime.utcnow(),
                )
            )
            inserted += 1

        session.commit()

    LOGGER.info("DART ingest complete (inserted=%d)", inserted)
    return inserted
