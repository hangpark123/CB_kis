# AntTrading Pro (CB_kis) 🐜📈

**AI 기반 주식 트레이딩 대시보드 및 CB(전환사채) 공시/뉴스 스캐너**

이 프로젝트는 한국투자증권(KIS) Open API를 연동하여 실시간 시세 조회, 차트 분석, **AI 종목 추천**, 그리고 **주식 주문(매수/매도/정정/취소)**을 웹 인터페이스에서 수행할 수 있는 트레이딩 터미널입니다.
또한, 기존의 CB(전환사채) 관련 공시 및 뉴스를 수집/분석하는 기능도 백엔드에 통합되어 있습니다.

## 🌟 주요 기능 (Key Features)

### 1. 🖥️ 프로 트레이딩 데스크 (Trading Desk)
- **실시간 차트**: TradingView Lightweight Charts 탑재 (반응형).
- **매매 패널**: 현금/미수 주문 선택, % 단위 수량 계산, 시장가/지정가 주문.
- **주문 관리**: 미체결 내역 조회 및 **즉시 정정/취소** 기능.
- **포트폴리오**: 실시간 잔고 확인, 평가손익 및 수익률 계산.

### 2. 🤖 AI 투자 분석 (AI Analytics)
- **종목 추천**: AI 스코어링 시스템을 통한 Top Pick 종목 선정.
- **실시간 분석**: 선택 종목에 대한 AI 매매 의견(긍정/부정) 및 신뢰도 점수 제공.
- **뉴스/공시**: 네이버 금융 뉴스 및 DART 공시 실시간 크롤링/요약.

### 3. 📡 백엔드 엔진 (CB Scanner Core)
- **DART 공시 수집**: 전환사채(CB), 신주인수권(BW) 등 주요 이벤트 감지.
- **키워드 필터링**: 발행, 리픽싱, 전환청구 등 핵심 키워드로 뉴스 필터링.
- **정규화 데이터베이스**: 수집된 데이터를 구조화하여 DB(SQLite/PostgreSQL)에 적재.

---

## 🛠️ 기술 스택 (Tech Stack)

*   **Frontend**: HTML5, CSS3 (Modern Dark UI), Vanilla JavaScript
*   **Backend**: Python, FastAPI
*   **Database**: SQLite (기본/개발용)
*   **External API**: Korea Investment Securities (KIS) Open API, Naver Finance, DART Open API
*   **Scheduler**: APScheduler (백그라운드 데이터 수집)

---

## 🚀 빠른 시작 (Quick Start)

### 1. 필수 요구사항
*   Python 3.11 이상
*   한국투자증권(KIS) API 계정 (App Key / Secret)

### 2. 설치 및 환경 설정

```bash
# 1) 저장소 클론
git clone https://github.com/hangpark123/CB_kis.git
cd CB_kis

# 2) 가상환경 생성 및 패키지 설치
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# 3) 환경 변수 설정 (.env 또는 kis_auth.py 설정)
# KIS_APPKEY, KIS_APPSECRET, KIS_ACCOUNT_NO 등을 설정해야 합니다.
```

### 3. 서버 실행

```bash
uvicorn app.api:app --reload --port 8000
```
브라우저에서 `http://localhost:8000` 로 접속하여 메인 대시보드(Rankings/News)를 확인하고, `Trading Desk` 버튼을 눌러 트레이딩 화면으로 이동합니다.

---

## 📂 프로젝트 구조
```
CB_kis/
├── app/
│   ├── api.py           # FastAPI 메인 서버/엔드포인트
│   ├── kis_api.py       # 한국투자증권 API 연동 모듈
│   ├── kis_auth.py      # 토큰 관리 및 인증
│   ├── scorer.py        # AI 점수 산출 로직
│   └── ...
├── public/              # 프론트엔드 정적 파일
│   ├── trading_desk.html # 트레이딩 터미널 UI
│   ├── index.html       # 메인 대시보드
│   ├── css/             # 스타일시트
│   └── js/              # 클라이언트 로직 (Chart, API Calls)
├── data/                # 종목 마스터 데이터 및 로컬 DB
└── requirements.txt     # 의존성 목록
```

## ⚠️ 주의사항
*   이 프로그램은 **개인 학습 및 보조용** 도구입니다.
*   실제 트레이딩 시 발생하는 금전적 손실에 대한 책임은 **사용자 본인**에게 있습니다.
*   API 과부하 방지를 위해 요청 제한(Rate Limit)을 준수하도록 설계되었습니다.
