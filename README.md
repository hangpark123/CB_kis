# CB Scanner (뉴스/공시 스캐너 + 정규화 + Top Feed)

한국 전환사채(CB) 관련 **뉴스/RSS + DART 공시**를 수집하고, 키워드 기반으로 이벤트(발행/리픽싱/전환/조기상환 등)를 분류해
정규화 테이블에 저장한 뒤, Top N 피드를 제공하는 **MVP 프로젝트**입니다.

## 구성
- 수집: `app/fetch_news.py`(RSS), `app/fetch_dart.py`(DART OpenAPI)
- 정규화/스코어링: `app/normalizer.py`, `app/scorer.py`
- 종목 매핑: `app/match_ticker.py` (회사명 → 종목코드)
- API: `app/api.py` (FastAPI, read-only)
- 스케줄러: `app/scheduler.py` (APScheduler, 분 단위 주기 실행)

## 빠른 시작

### 1) Python 가상환경 및 설치
```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 2) 환경변수 설정
`.env`를 프로젝트 루트에 생성하거나 `.env.example`를 복사해 수정하세요.
```bash
cp .env.example .env
```

### 3) DB 준비
PostgreSQL을 권장하지만, 개발용으로는 **SQLite**도 동작합니다(PG_DSN이 비어있을 때).
초기 테이블은 첫 실행 시 자동 생성됩니다. (SQLAlchemy)

### 4) 상장사 매핑 사전
`data/dim_listing_sample.csv`를 참고해, 실제 상장사(종목코드/회사명)를 채워 `dim_listing` 테이블에 적재하세요.
(초기 실행 시 샘플 CSV를 DB에 적재하는 훅이 포함되어 있습니다.)

### 5) 실행
- 스케줄러(백그라운드 작업):
```bash
python -m app.scheduler
```
- API 서버(FastAPI):
```bash
uvicorn app.api:app --reload --port 8000
```
- Top N 테스트 출력:
```bash
python -m app.scorer
```

## 환경 변수(.env)

- `DART_API_KEY` : DART OpenAPI 키
- `NEWS_RSS_LIST` : 쉼표로 구분된 RSS 주소 목록
- `PG_DSN` : PostgreSQL DSN (예: postgresql+psycopg2://user:pass@localhost:5432/cbdesk)
- 빈 값이면 개발용 SQLite(`cb_scanner.db`)를 사용합니다.

## 요구사항
- Python 3.11+
- 주요 라이브러리: FastAPI, SQLAlchemy, APScheduler, httpx, feedparser, rapidfuzz

## 로드맵 (MVP 이후)
- NER 모델 도입(회사명 인식 정확도↑)
- KRX/SEIBRO 데이터 보강(전환가/패리티/괴리율)
- Slack/Telegram 알림
- KIS OpenAPI 연동(조건부 자동주문/시뮬레이션)

git status              # 어떤 파일이 변경됐는지 확인
git add .               # 변경/추가된 파일 전부 스테이징(현재 폴더 기준)
# 또는 전체 저장소 기준이면: git add -A
git commit -m "메시지"   # 스냅샷(커밋) 생성
git push -u origin main # 이 커밋들을 원격(main)으로 푸시
