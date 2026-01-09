import httpx, datetime as dt, re, logging
from .config import settings
from .db import SessionLocal
from .models import RawEvent
from .keywords import COMBINED

log = logging.getLogger("cb.dart")
DART_URL = "https://opendart.fss.or.kr/api/list.json"
KST = dt.timezone(dt.timedelta(hours=9))

def _parse_rcept_dt(s: str | None):
    # ex) '20250102123456' (YYYYMMDDHHMMSS), KST 기준
    if not s: return None
    try:
        return dt.datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=KST)
    except Exception:
        return None

def fetch_dart_today() -> int:
    if not settings.DART_API_KEY:
        log.warning("DART_API_KEY 미설정")
        return 0
    params = {"crtfc_key": settings.DART_API_KEY, "bgn_de": dt.datetime.now().strftime("%Y%m%d"),
              "page_no": 1, "page_count": 100}
    inserted = 0
    timeout = httpx.Timeout(connect=3.0, read=6.0, write=5.0, pool=3.0)
    with httpx.Client(timeout=timeout) as c, SessionLocal() as s:
        r = c.get(DART_URL, params=params)
        try:
            data = r.json()
        except Exception as e:
            log.error("DART 응답 파싱 실패: %s", e); return 0
        for it in data.get("list", []):
            title = (it.get("report_nm") or "")
            if re.search(COMBINED, title, flags=re.I):
                pub_dt = _parse_rcept_dt(it.get("rcept_dt"))  # ✅ 접수시각 기준
                s.add(RawEvent(
                    source="dart",
                    url=f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={it.get('rcp_no')}",
                    title=title, content=None, corp_name_kr=it.get("corp_name"),
                    published_at=pub_dt, raw_json=it, inserted_at=dt.datetime.utcnow()
                ))
                inserted += 1
        s.commit()
    log.info("DART 수집 완료: %d건 (rcept_dt 저장)", inserted)
    return inserted
