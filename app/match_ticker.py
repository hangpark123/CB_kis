from sqlalchemy import select
from rapidfuzz import fuzz, process
from .db import SessionLocal
from .models import DimListing


def match_stock_code(corp_name: str) -> str | None:
    if not corp_name:
        return None
    with SessionLocal() as s:
        rows = s.execute(select(DimListing.corp_name_kr, DimListing.stock_code)).all()
    if not rows:
        return None
    choices = {name: code for name, code in rows}
    best = process.extractOne(
        corp_name, list(choices.keys()), scorer=fuzz.token_sort_ratio
    )
    if best and best[1] >= 85:
        return choices[best[0]]
    return None
