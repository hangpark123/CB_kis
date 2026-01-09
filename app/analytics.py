from sqlalchemy import select, func
import datetime as dt
from .db import SessionLocal
from .models import NormEvent, RawEvent

def counts_by_type(hours: int = 24):
    """24시간 집계 기준을 created_at이 아닌 event_time(원본 시간)으로 변경, 없으면 created_at 백업."""
    cutoff = dt.datetime.utcnow() - dt.timedelta(hours=hours)
    with SessionLocal() as s:
        # COALESCE(event_time, created_at) >= cutoff
        rows = s.execute(
            select(NormEvent.event_type, func.count())
            .where(func.coalesce(NormEvent.event_time, NormEvent.created_at) >= cutoff)
            .group_by(NormEvent.event_type)
        ).all()
    return {k or "UNKNOWN": int(v) for k, v in rows}

def top_enriched(limit: int = 50):
    with SessionLocal() as s:
        rows = s.execute(
            select(NormEvent).order_by(
                NormEvent.score.desc(),
                func.coalesce(NormEvent.event_time, NormEvent.created_at).desc()
            ).limit(limit)
        ).scalars().all()
        out = []
        for r in rows:
            url = None
            try:
                raw_id = int((r.ref_raw_ids or '').split(',')[0])
                if raw_id:
                    raw = s.execute(select(RawEvent).where(RawEvent.id == raw_id)).scalar_one_or_none()
                    if raw:
                        url = raw.url
            except Exception:
                pass
            out.append({
                "time": str(r.event_time or r.created_at),
                "stock_code": r.stock_code,
                "corp": r.corp_name_kr,
                "type": r.event_type,
                "headline": r.headline,
                "score": float(r.score) if r.score is not None else None,
                "url": url
            })
    return out
