from sqlalchemy import select, desc
from .db import SessionLocal, engine
from .models import Base, NormEvent, DimListing
import datetime as dt, csv, os


def init_db_and_seed():
    Base.metadata.create_all(engine)
    path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "data", "dim_listing_sample.csv"
    )
    with SessionLocal() as s:
        has = s.execute(select(DimListing)).first()
        if not has and os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as f:
                rdr = csv.DictReader(f)
                for row in rdr:
                    s.add(
                        DimListing(
                            stock_code=row["stock_code"],
                            corp_name_kr=row["corp_name_kr"],
                            market=row.get("market"),
                        )
                    )
            s.commit()


def top_today(limit=10):
    with SessionLocal() as s:
        rows = (
            s.execute(
                select(NormEvent)
                .order_by(
                    desc(NormEvent.score),
                    desc(NormEvent.event_time),
                    desc(NormEvent.created_at),
                )
                .limit(limit)
            )
            .scalars()
            .all()
        )
        return [
            {
                "time": str(r.event_time or r.created_at),
                "stock_code": r.stock_code,
                "corp": r.corp_name_kr,
                "type": r.event_type,
                "headline": r.headline,
                "score": float(r.score) if r.score is not None else None,
            }
            for r in rows
        ]
