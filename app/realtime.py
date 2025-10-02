from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import asyncio, json, re, html, datetime as dt, time
from email.utils import parsedate_to_datetime
import httpx
from typing import Iterable, Optional, Set
from sqlalchemy import select

from .config import settings
from .keywords import COMBINED
from .db import SessionLocal
from .models import DimListing

router = APIRouter(prefix="/api/live", tags=["live"])

NAVER_URL = "https://openapi.naver.com/v1/search/news.json"
DART_URL = "https://opendart.fss.or.kr/api/list.json"

# ---- timezones / helpers ----
UTC = dt.timezone.utc
KST = dt.timezone(dt.timedelta(hours=9))


def _strip(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"</?b>", "", text)
    return html.unescape(text)


CLASSIFY_PATTERNS = {
    "REFIX": ("리픽싱", "재조정"),
    "CONVERSION": ("전환청구", "전환가", "전환권 행사"),
    "REDEMPTION": ("조기상환", "콜옵션", "풋옵션"),
    "ISSUE": ("발행결정", "발행", "매입", "취득"),
}


def _classify(text: str) -> str:
    """Roughly classify the headline into a CB-related category."""
    t = (text or "").lower()
    for tag, keywords in CLASSIFY_PATTERNS.items():
        if any(k.lower() in t for k in keywords):
            return tag
    return "OTHER"


def _to_utc(d: Optional[dt.datetime]) -> Optional[dt.datetime]:
    if d is None:
        return None
    if d.tzinfo is None:
        return d.replace(tzinfo=UTC)
    return d.astimezone(UTC)


def _iso_to_utc(s: Optional[str]) -> Optional[dt.datetime]:
    if not s:
        return None
    try:
        d = dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None
    return _to_utc(d)


# ---- listing cache (corp -> stock_code) ----
_CHOICES = None
_LAST_LOAD = None


def _load_choices():
    global _CHOICES, _LAST_LOAD
    now = dt.datetime.now(UTC)
    if (
        _CHOICES is None
        or _LAST_LOAD is None
        or (now - _LAST_LOAD).total_seconds() > 600
    ):
        with SessionLocal() as s:
            rows = s.execute(
                select(DimListing.corp_name_kr, DimListing.stock_code)
            ).all()
        _CHOICES = {name: code for name, code in rows}
        _LAST_LOAD = now
    return _CHOICES


def _lookup_code(corp_name: Optional[str]) -> Optional[str]:
    if not corp_name:
        return None
    return _load_choices().get(corp_name)


# ===================== NAVER NEWS =====================
def _parse_pubdate(s: Optional[str]) -> Optional[dt.datetime]:
    if not s:
        return None
    try:
        return parsedate_to_datetime(s)  # aware
    except Exception:
        return None


async def _fetch_naver_once(
    queries: Iterable[str], display: int = 30, mode: str = "all"
):
    """Fetch a batch of Naver news results for the given queries.

    Args:
        queries: Search keywords to request.
        display: Maximum results per query.
        mode: 'cb' to filter by CB keywords, otherwise 'all'.
    """
    cid, csec = settings.NAVER_CLIENT_ID, settings.NAVER_CLIENT_SECRET
    if not cid or not csec:
        return []

    headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}
    timeout = httpx.Timeout(connect=3.0, read=7.0, write=5.0, pool=5.0)
    out = []
    async with httpx.AsyncClient(timeout=timeout) as c:
        for q in queries:
            try:
                r = await c.get(
                    NAVER_URL,
                    headers=headers,
                    params={"query": q, "display": display, "sort": "date", "start": 1},
                )
                data = r.json()
            except Exception:
                data = {}

            for item in data.get("items", []):
                title = _strip(item.get("title", ""))
                desc = _strip(item.get("description", ""))
                link = item.get("link")
                pub = _parse_pubdate(item.get("pubDate"))  # aware
                pub_u = _to_utc(pub)  # UTC-aware
                text = f"{title}\n{desc}"

                if mode == "cb" and not re.search(COMBINED, text, flags=re.I):
                    continue

                ts = int(pub_u.timestamp() * 1000) if pub_u else None
                out.append(
                    {
                        "source": "naver_news",
                        "time": pub_u.isoformat() if pub_u else None,
                        "time_ts": ts,
                        "type": _classify(text),
                        "headline": title,
                        "summary": desc,
                        "corp": None,
                        "stock_code": None,
                        "url": link,
                        "raw": item,
                    }
                )

    out.sort(
        key=lambda x: _iso_to_utc(x["time"]) or dt.datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return out


@router.get("/news")
async def live_news(
    q: Optional[str] = None, display: int = 30, minutes: int = 60, mode: str = "auto"
):
    """
    온디맨드 뉴스 조회.
    mode: 'auto'|'cb'|'all'
      - auto: q 있으면 'all', 없으면 'cb'
    """
    queries = [
        s.strip()
        for s in (q or ",".join(settings.NAVER_NEWS_QUERIES)).split(",")
        if s.strip()
    ]
    use_mode = "all" if (mode == "auto" and q) else ("cb" if mode == "auto" else mode)
    rows = await _fetch_naver_once(queries, display=display, mode=use_mode)

    cutoff = dt.datetime.now(UTC) - dt.timedelta(minutes=minutes)

    def ok(r):
        t = _iso_to_utc(r.get("time"))
        return (t is None) or (t >= cutoff)

    return [r for r in rows if ok(r)]


@router.get("/stream")
async def news_stream(
    request: Request,
    q: Optional[str] = None,
    interval: int = 8,
    minutes: int = 60,
    display: int = 30,
    mode: str = "auto",
):
    """뉴스 SSE 스트림 (즉시 ping + heartbeat)."""
    queries = [
        s.strip()
        for s in (q or ",".join(settings.NAVER_NEWS_QUERIES)).split(",")
        if s.strip()
    ]
    use_mode = "all" if (mode == "auto" and q) else ("cb" if mode == "auto" else mode)
    seen: Set[str] = set()

    def _cutoff():
        return dt.datetime.now(UTC) - dt.timedelta(minutes=minutes)

    async def event_gen():
        try:
            yield ":connected\n\n"  # onopen 유도
            last_hb = time.monotonic()
            while True:
                if await request.is_disconnected():
                    break
                rows = await _fetch_naver_once(queries, display=display, mode=use_mode)
                co = _cutoff()
                sent = False
                for r in rows:
                    key = f"{r.get('url')}|{r.get('time')}"
                    if key in seen:
                        continue
                    seen.add(key)
                    t = _iso_to_utc(r.get("time"))
                    if t is not None and t < co:
                        continue
                    yield f"data: {json.dumps(r, ensure_ascii=False)}\n\n"
                    sent = True
                now = time.monotonic()
                if not sent and now - last_hb > 15:
                    last_hb = now
                    yield ":hb\n\n"
                await asyncio.sleep(max(2, min(60, interval)))
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ===================== DART DISCLOSURES =====================
def _parse_rcept_dt(s: Optional[str]) -> Optional[dt.datetime]:
    if not s:
        return None
    try:
        return dt.datetime.strptime(s, "%Y%m%d%H%M%S").replace(
            tzinfo=KST
        )  # aware (KST)
    except Exception:
        return None


async def _fetch_dart_once(
    minutes: int = 60, page_count: int = 100, max_pages: int = 3
):
    """Fetch a slice of the DART disclosure list within the look-back window.

    Args:
        minutes: Look-back window in minutes.
        page_count: Items per page for the DART API.
        max_pages: Maximum number of pages to iterate.
    """
    key = settings.DART_API_KEY
    if not key:
        return []

    now_kst = dt.datetime.now(KST)
    start_kst = now_kst - dt.timedelta(minutes=minutes)
    params_base = {
        "crtfc_key": key,
        "bgn_de": start_kst.strftime("%Y%m%d"),
        "end_de": now_kst.strftime("%Y%m%d"),
        "page_count": page_count,
    }

    timeout = httpx.Timeout(connect=3.0, read=7.0, write=5.0, pool=5.0)
    out = []
    async with httpx.AsyncClient(timeout=timeout) as c:
        for page_no in range(1, max_pages + 1):
            params = dict(params_base)
            params["page_no"] = page_no
            try:
                r = await c.get(DART_URL, params=params)
                data = r.json()
            except Exception:
                data = {}

            items = data.get("list", []) or []
            if not items:
                break

            for it in items:
                title = it.get("report_nm") or ""
                corp = it.get("corp_name")
                code = _lookup_code(corp)
                pub = _parse_rcept_dt(it.get("rcept_dt"))  # aware(KST)
                rcp_no = it.get("rcp_no")
                url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}"
                ts = None
                if pub is not None:
                    try:
                        ts = int(pub.astimezone(UTC).timestamp() * 1000)
                    except Exception:
                        ts = None
                out.append(
                    {
                        "source": "dart",
                        "time": pub.isoformat() if pub else None,  # ISO(±tz)
                        "time_ts": ts,
                        "type": _classify(title),
                        "headline": title,
                        "summary": "",
                        "corp": corp,
                        "stock_code": code,
                        "rcp_no": rcp_no,
                        "url": url,
                        "raw": it,
                    }
                )

    out.sort(
        key=lambda x: _iso_to_utc(x["time"]) or dt.datetime.min.replace(tzinfo=UTC),
        reverse=True,
    )
    return out


@router.get("/dart")
async def live_dart(
    minutes: int = 60, page_count: int = 100, limit: int = 10, scope: str = "cb"
):
    """Return recent DART disclosures filtered by scope and time window.

    Args:
        minutes: Look-back window in minutes.
        page_count: Items per page for the DART API.
        limit: Maximum number of rows to return.
        scope: 'cb' to keep CB-related items, 'all' otherwise.
    """
    rows = await _fetch_dart_once(minutes=minutes, page_count=page_count, max_pages=3)
    cutoff = dt.datetime.now(UTC) - dt.timedelta(minutes=minutes)

    def match_scope(r):
        if scope == "all":
            return True
        return bool(re.search(COMBINED, r.get("headline") or "", flags=re.I))

    def ok(r):
        t = _iso_to_utc(r.get("time"))
        return ((t is None) or (t >= cutoff)) and match_scope(r)

    out = [r for r in rows if ok(r)]
    return out[: max(1, min(200, limit))]


@router.get("/dart/stream")
async def dart_stream(
    request: Request,
    interval: int = 8,
    minutes: int = 60,
    page_count: int = 100,
    scope: str = "cb",
):
    """Server-sent events stream of DART disclosures.

    Args:
        request: FastAPI request used to detect disconnects.
        interval: Polling interval in seconds.
        minutes: Look-back window in minutes.
        page_count: Items per page for the DART API.
        scope: 'cb' to keep CB-related items, 'all' otherwise.
    """
    seen: Set[str] = set()

    def _cutoff():
        return dt.datetime.now(UTC) - dt.timedelta(minutes=minutes)

    async def event_gen():
        try:
            yield ":connected\n\n"
            last_hb = time.monotonic()
            while True:
                if await request.is_disconnected():
                    break
                rows = await _fetch_dart_once(
                    minutes=minutes, page_count=page_count, max_pages=3
                )
                co = _cutoff()
                sent = False
                for r in rows:
                    key = f"{r.get('url')}|{r.get('time')}"
                    if key in seen:
                        continue
                    if scope != "all" and not re.search(
                        COMBINED, r.get("headline") or "", flags=re.I
                    ):
                        continue
                    t = _iso_to_utc(r.get("time"))
                    if t is not None and t < co:
                        continue

                    seen.add(key)
                    yield f"data: {json.dumps(r, ensure_ascii=False)}\n\n"
                    sent = True

                now = time.monotonic()
                if not sent and now - last_hb > 15:
                    last_hb = now
                    yield ":hb\n\n"

                await asyncio.sleep(max(2, min(60, interval)))
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
