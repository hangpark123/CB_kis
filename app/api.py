from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from .scorer import top_today, init_db_and_seed
from .fetch_dart import fetch_dart_today
from .fetch_news_naver import fetch_naver_news
from .normalizer import normalize_recent
from .analytics import counts_by_type, top_enriched
from .realtime import router as live_router

app = FastAPI(title="CB Scanner (Dashboard)", version="0.4.0")

app.include_router(live_router)


@app.on_event("startup")
def startup():
    init_db_and_seed()


@app.get("/", include_in_schema=False)
def root_redirect():
    return RedirectResponse(url="/dash/")


# Static dashboard at /dash
app.mount("/dash", StaticFiles(directory="public", html=True), name="dash")


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/top")
def api_top(limit: int = 10):
    return top_today(limit=limit)


@app.get("/api/top_enriched")
def api_top_enriched(limit: int = 50):
    return top_enriched(limit=limit)


@app.get("/api/stats/by_type")
def api_stats_by_type(hours: int = 24):
    return counts_by_type(hours=hours)


@app.post("/api/run/once")
def run_once():
    fetch_dart_today()
    fetch_naver_news()
    normalize_recent()
    return {"status": "ok"}


# ----- Redirect helper to avoid external referrer issues -----
@app.get("/go/dart/{rcp_no}")
def go_dart(rcp_no: str):
    url = f"https://dart.fss.or.kr/dsaf001/main.do?rcpNo={rcp_no}"
    return RedirectResponse(url)
