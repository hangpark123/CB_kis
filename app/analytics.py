from __future__ import annotations

import datetime as dt
from typing import Dict, List

from sqlalchemy import func, select

from .db import SessionLocal
from .models import NormEvent, RawEvent


def counts_by_type(hours: int = 24) -> Dict[str, int]:
    """Return counts of normalized events grouped by type for the last *hours*."""
    cutoff = dt.datetime.utcnow() - dt.timedelta(hours=hours)
    with SessionLocal() as session:
        rows = session.execute(
            select(NormEvent.event_type, func.count())
            .where(func.coalesce(NormEvent.event_time, NormEvent.created_at) >= cutoff)
            .group_by(NormEvent.event_type)
        ).all()
    return {event_type or "UNKNOWN": int(count) for event_type, count in rows}


def top_enriched(limit: int = 50) -> List[dict]:
    """Return the top *limit* normalized events ordered by score then recency."""
    with SessionLocal() as session:
        rows = (
            session.execute(
                select(NormEvent)
                .order_by(
                    NormEvent.score.desc(),
                    func.coalesce(NormEvent.event_time, NormEvent.created_at).desc(),
                )
                .limit(limit)
            )
            .scalars()
            .all()
        )

        enriched = []
        for row in rows:
            url = None
            try:
                raw_id = int((row.ref_raw_ids or "").split(",")[0])
                if raw_id:
                    raw = session.execute(
                        select(RawEvent).where(RawEvent.id == raw_id)
                    ).scalar_one_or_none()
                    if raw:
                        url = raw.url
            except (ValueError, TypeError):
                # ref_raw_ids may be empty or malformed; ignore and continue
                pass

            enriched.append(
                {
                    "time": str(row.event_time or row.created_at),
                    "stock_code": row.stock_code,
                    "corp": row.corp_name_kr,
                    "type": row.event_type,
                    "headline": row.headline,
                    "score": float(row.score) if row.score is not None else None,
                    "url": url,
                }
            )

    return enriched
