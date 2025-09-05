import re, html, httpx, datetime as dt, logging
from typing import Iterable
from email.utils import parsedate_to_datetime
from .db import SessionLocal
from .models import RawEvent
from .keywords import COMBINED
from .config import settings

log = logging.getLogger("cb.naver")
NAVER_URL = "https://openapi.naver.com/v1/search/news.json"

def _strip(text: str) -> str:
    if not text: return ""
    text = re.sub(r"</?b>", "", text)
    return html.unescape(text)

def _parse_pubdate(s: str | None):
    if not s:
        return None
    try:
        # ex) 'Wed, 03 Sep 2025 07:10:00 +0900'
        return parsedate_to_datetime(s)
    except Exception:
        return None

def fetch_naver_news(queries: Iterable[str] | None = None) -> int:
    """네이버 뉴스 '작성 시각(pubDate)'을 published_at으로 저장."""
    cid, csec = settings.NAVER_CLIENT_ID, settings.NAVER_CLIENT_SECRET
    if not cid or not csec:
        log.warning("NAVER API 키가 없습니다. .env 확인")
        return 0
    if queries is None:
        queries = settings.NAVER_NEWS_QUERIES

    headers = {"X-Naver-Client-Id": cid, "X-Naver-Client-Secret": csec}
    inserted = 0
    timeout = httpx.Timeout(connect=3.0, read=6.0, write=5.0, pool=3.0)
    with httpx.Client(timeout=timeout) as c, SessionLocal() as s:
        for q in queries:
            try:
                r = c.get(NAVER_URL, headers=headers, params={"query": q, "display": 30, "sort": "date", "start": 1})
                data = r.json()
            except Exception as e:
                log.error("NAVER 요청 실패: %s", e)
                continue

            for item in data.get("items", []):
                title = _strip(item.get("title", ""))
                desc  = _strip(item.get("description", ""))
                link  = item.get("link")
                pub_dt = _parse_pubdate(item.get("pubDate"))  # ✅ 기사 원본 pubDate
                if re.search(COMBINED, f"{title}\n{desc}", flags=re.I):
                    s.add(RawEvent(
                        source="naver_news", url=link, title=title, content=desc,
                        corp_name_kr=None, published_at=pub_dt,  # ✅ 원본 시간 사용
                        raw_json=item, inserted_at=dt.datetime.utcnow()
                    ))
                    inserted += 1
        s.commit()
    log.info("NAVER 수집 완료: %d건 (pubDate 저장)", inserted)
    return inserted
