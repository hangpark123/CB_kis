"""원본 시간으로 과거 데이터 보정 스크립트
사용법:
    python -m app.tools_backfill_times
"""

import datetime as dt
from email.utils import parsedate_to_datetime
from sqlalchemy import select
from .db import SessionLocal
from .models import RawEvent, NormEvent


def run():
    fixed_raw, fixed_norm = 0, 0
    with SessionLocal() as s:
        raws = s.execute(select(RawEvent)).scalars().all()
        for r in raws:
            # NAVER: pubDate
            if r.source == "naver_news" and r.raw_json and not r.published_at:
                pub = r.raw_json.get("pubDate")
                if pub:
                    try:
                        r.published_at = parsedate_to_datetime(pub)
                        fixed_raw += 1
                    except Exception:
                        pass
            # DART: rcept_dt
            if r.source == "dart" and r.raw_json and not r.published_at:
                s2 = r.raw_json.get("rcept_dt")
                if s2 and len(s2) == 14:
                    try:
                        KST = dt.timezone(dt.timedelta(hours=9))
                        r.published_at = dt.datetime.strptime(
                            s2, "%Y%m%d%H%M%S"
                        ).replace(tzinfo=KST)
                        fixed_raw += 1
                    except Exception:
                        pass
        s.commit()

        # NormEvent.event_time 보정 (ref_raw_ids = RawEvent.id)
        norms = s.execute(select(NormEvent)).scalars().all()
        for n in norms:
            try:
                rid = int((n.ref_raw_ids or "").split(",")[0])
            except Exception:
                continue
            raw = s.execute(
                select(RawEvent).where(RawEvent.id == rid)
            ).scalar_one_or_none()
            if raw and raw.published_at and not n.event_time:
                n.event_time = raw.published_at
                fixed_norm += 1
        s.commit()
    print(f"backfill done: raw={fixed_raw}, norm={fixed_norm}")


if __name__ == "__main__":
    run()
