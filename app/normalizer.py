import datetime as dt
from sqlalchemy import select
from .db import SessionLocal
from .models import RawEvent, NormEvent
from .match_ticker import match_stock_code


def classify_event(text: str) -> str:
    t = text or ""
    if "리픽싱" in t or ("전환가" in t and "조정" in t):
        return "REFIX"
    if "전환청구" in t:
        return "CONVERSION"
    if "조기상환" in t or "풋옵션" in t:
        return "REDEMPTION"
    if "발행결정" in t or "발행" in t:
        return "ISSUE"
    return "OTHER"


def compute_score(is_official: bool, event_type: str, age_minutes: int) -> float:
    base = 0.6 if is_official else 0.4
    type_bonus = 0.15 if event_type in {"REFIX", "CONVERSION"} else 0.0
    recency = max(0, 1 - age_minutes / 1440)
    return round(min(1.0, base * 0.6 + type_bonus + recency * 0.3), 3)


def normalize_recent(minutes=180):
    cutoff = dt.datetime.utcnow() - dt.timedelta(minutes=minutes)
    with SessionLocal() as s:
        raws = (
            s.execute(select(RawEvent).where(RawEvent.inserted_at >= cutoff))
            .scalars()
            .all()
        )
        for r in raws:
            text = f"{r.title or ''} {r.content or ''}"
            et = classify_event(text)
            corp = r.corp_name_kr
            code = match_stock_code(corp) if corp else None
            is_official = r.source == "dart"
            score = compute_score(is_official, et, 0)
            ne = NormEvent(
                stock_code=code,
                corp_name_kr=corp,
                event_type=et,
                headline=r.title,
                summary=(r.content or "")[:500],
                score=score,
                has_official=is_official,
                ref_raw_ids=str(r.id),
                event_time=r.published_at,
                created_at=dt.datetime.utcnow(),
            )
            s.add(ne)
        s.commit()
