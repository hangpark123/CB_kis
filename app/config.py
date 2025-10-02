from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseModel):
    DART_API_KEY: str = os.getenv("DART_API_KEY", "")
    NAVER_CLIENT_ID: str = os.getenv("NAVER_CLIENT_ID", "")
    NAVER_CLIENT_SECRET: str = os.getenv("NAVER_CLIENT_SECRET", "")
    NAVER_NEWS_QUERIES: list[str] = [
        s.strip()
        for s in os.getenv("NAVER_NEWS_QUERIES", "전환사채,리픽싱").split(",")
        if s.strip()
    ]
    PG_DSN: str | None = os.getenv("PG_DSN") or None
    TZ: str = "Asia/Seoul"


settings = Settings()
