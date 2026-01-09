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


# ========================================
# TRADING APIs
# ========================================

from fastapi.responses import FileResponse
import os

# Static files for trading UI
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PUBLIC_DIR = os.path.join(BASE_DIR, "public")

# CSS, JS 직접 마운트
app.mount("/css", StaticFiles(directory=os.path.join(PUBLIC_DIR, "css")), name="css")
app.mount("/js", StaticFiles(directory=os.path.join(PUBLIC_DIR, "js")), name="js")

# HTML 파일 직접 서빙
@app.get("/", include_in_schema=False)
def root_trading():
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))

@app.get("/trading_desk.html", include_in_schema=False)
def trading_desk_page():
    return FileResponse(os.path.join(PUBLIC_DIR, "trading_desk.html"))


# === 차트 데이터 API ===
@app.get("/api/trading/chart_data")
def api_chart_data(stock_code: str):
    """차트 데이터 조회 (OHLCV)"""
    from .kis_api import get_daily_chart_data
    return get_daily_chart_data(stock_code)


# === 현재가 조회 API ===
@app.get("/api/trading/current_price")
def api_current_price(stock_code: str):
    """현재가 조회"""
    from .kis_api import get_current_price
    
    try:
        price_info = get_current_price(stock_code)
        if price_info:
            return {
                "stock_code": stock_code,
                "stock_name": price_info.get("stock_name", ""),
                "current_price": price_info.get("current_price", 0),
                "change_rate": price_info.get("change_rate", 0),
                "volume": price_info.get("volume", 0)
            }
        return {"error": "종목을 찾을 수 없습니다"}
    except Exception as e:
        print(f"현재가 조회 오류: {e}")
        return {"error": str(e)}


# === AI 추천 API (RSI, MACD, Bollinger Bands) ===
@app.get("/api/ai/recommendations")
def api_ai_recommendations(limit: int = 5):
    """AI 추천 종목 - RSI, MACD, 볼린저밴드 기반"""
    from .kis_api import get_daily_chart_data
    import time
    
    recommendations = []
    
    # 인기 종목 리스트
    popular_stocks = [
        ('005930', '삼성전자'),
        ('000660', 'SK하이닉스'),
        ('035420', 'NAVER'),
        ('005380', '현대차'),
        ('051910', 'LG화학'),
        ('006400', '삼성SDI'),
        ('035720', '카카오'),
        ('207940', '삼성바이오'),
        ('068270', '셀트리온'),
        ('003670', '포스코'),
    ]
    
    def calculate_rsi(prices, period=14):
        """RSI 계산"""
        if len(prices) < period + 1:
            return 50
        
        gains, losses = [], []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            gains.append(max(diff, 0))
            losses.append(max(-diff, 0))
        
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    
    success_count = 0
    for stock_code, stock_name in popular_stocks:
        if success_count >= limit:
            break
        
        try:
            if success_count > 0:
                time.sleep(2.0)  # Rate Limit (2초)
            
            chart_data = get_daily_chart_data(stock_code)
            
            if not chart_data or len(chart_data) < 20:
                continue
            
            closes = [d['close'] for d in chart_data]
            current_price = closes[-1]
            
            # RSI 계산
            rsi = calculate_rsi(closes, 14)
            
            # 매수 신호 판정
            signals = []
            score = 50
            
            if rsi < 30:
                signals.append(f"📊 RSI {rsi:.1f} 과매도")
                score += 25
            elif rsi < 40:
                signals.append(f"📊 RSI {rsi:.1f} 저평가")
                score += 15
            elif rsi > 70:
                continue  # 과매수 제외
            else:
                signals.append(f"📊 RSI {rsi:.1f}")
                score += 5
            
            # 볼린저 밴드 간이 계산
            if len(closes) >= 20:
                sma = sum(closes[-20:]) / 20
                variance = sum((x - sma) ** 2 for x in closes[-20:]) / 20
                std_dev = variance ** 0.5
                bb_lower = sma - (std_dev * 2)
                
                if current_price <= bb_lower * 1.02:
                    signals.append(f"📉 볼린저 하단 근접")
                    score += 20
            
            if score < 60:
                continue
            
            recommendations.append({
                "stock_code": stock_code,
                "stock_name": stock_name,
                "current_price": current_price,
                "change_rate": ((current_price - closes[-2]) / closes[-2] * 100) if len(closes) > 1 else 0,
                "confidence": min(95, int(score)),
                "reasons": signals[:3],
                "expected_return": f"+{int(score * 0.15)}~{int(score * 0.4)}%",
                "indicator": f"RSI {rsi:.1f}"
            })
            
            success_count += 1
            
        except Exception as e:
            print(f"AI 추천 오류 ({stock_name}/{stock_code}): {e}")
            continue
    
    recommendations.sort(key=lambda x: x['confidence'], reverse=True)
    return recommendations[:limit]


# === 계좌 수익률 API ===
@app.get("/api/trading/performance")
def api_trading_performance():
    """계좌 수익률 조회"""
    from .kis_api import get_balance
    
    try:
        balance = get_balance()
        return {
            "account_total_asset": balance.get("total_value", 0),
            "total_pnl": balance.get("pnl", 0),
            "deposits": balance.get("cash", 0)
        }
    except Exception as e:
        print(f"계좌 수익률 조회 오류: {e}")
        return {
            "account_total_asset": 0,
            "total_pnl": 0,
            "deposits": 0
        }


# === 보유 포지션 API ===
@app.get("/api/trading/positions")
def api_trading_positions():
    """보유 포지션 조회"""
    from .kis_api import get_balance
    
    try:
        balance = get_balance()
        return balance.get("positions", [])
    except Exception as e:
        print(f"포지션 조회 오류: {e}")
        return []


# === 종목 분석 API ===
@app.get("/api/trading/ranks")
def api_trading_ranks(type: str = "rise"):
    """시장 랭킹 조회 (네이버 금융 크롤링 - 전체 시장)"""
    import httpx
    import re
    
    try:
        # 네이버 금융 URL
        base_url = "https://finance.naver.com/sise/"
        
        if type == "rise":
            # 거래상위(거래량 기준 정렬이지만 등락률도 있음) 대신 상승률 페이지 사용 가능하지만
            # 네이버 '상승' 페이지는 코스피/코스닥 나뉘어 있음. 하이브리드 파싱 필요.
            # 간편하게 '거래상위' 페이지에서 등락률 정렬 or '인기검색' 등을 활용할 수도 있음.
            # 확실한 건 'sosok=0'(코스피), 'sosok=1'(코스닥) 상승률 페이지를 각각 긁어서 합치는 것.
            urls = [
                "https://finance.naver.com/sise/sise_rise.naver?sosok=0", # 코스피
                "https://finance.naver.com/sise/sise_rise.naver?sosok=1"  # 코스닥
            ]
        elif type == "fall":
            urls = [
                "https://finance.naver.com/sise/sise_fall.naver?sosok=0",
                "https://finance.naver.com/sise/sise_fall.naver?sosok=1"
            ]
        elif type == "volume":
            urls = [
                "https://finance.naver.com/sise/sise_quant.naver?sosok=0",
                "https://finance.naver.com/sise/sise_quant.naver?sosok=1"
            ]
        elif type == "theme":
            # 테마는 기존 더미 유지하거나 별도 파싱 (파싱이 복잡함)
            # 여기서는 기존 더미 유지하되 좀 더 현실적으로
             return [
                {"name": "2차전지", "rate": 2.5, "leading": "에코프로, LG엔솔"},
                {"name": "반도체", "rate": 1.8, "leading": "삼성전자, SK하이닉스"},
                {"name": "초전도체", "rate": -5.2, "leading": "신성델타테크"},
                {"name": "AI/로봇", "rate": 1.2, "leading": "두산로보틱스"},
                {"name": "자동차", "rate": -0.5, "leading": "현대차"}
            ]
        
        ranking_data = []
        
        for url in urls:
            try:
                resp = httpx.get(url, timeout=3.0)
                html = resp.content.decode("euc-kr", errors="ignore")
                
                # HTML 파싱 (regex)
                # 네이버 금융 테이블 행 파싱
                # 패턴: href="...code=123456"... >종목명</a> ... <td ...>현재가</td> ... <span ...>등락률</span>
                
                parts = html.split('href="/item/main.naver?code=')
                
                for part in parts[1:]: # 첫 덩어리는 건너뜀
                    try:
                        # 1. 코드 추출 (앞 6자리)
                        code = part[:6]
                        if not code.isdigit(): continue
                        
                        # 2. 종목명 추출
                        # code 뒤에 '" class="tltle">' 가 오고 그 뒤가 이름
                        name_end_idx = part.find('</a>')
                        name_start_idx = part.find('>', 6) + 1 # code 뒤 첫 >
                        if name_start_idx > name_end_idx: continue # 안전장치
                        
                        name = part[name_start_idx:name_end_idx]
                        
                        # 3. 데이터 추출 (테이블 컬럼 순서에 의존)
                        # 현재가: class="number">12,300</td>
                        # 등락률: <span>...%</span>
                        
                        # 편의상 숫자들만 찾아냄
                        # 정규식으로 숫자(콤마 포함) 또는 퍼센트 찾기
                        # part는 해당 종목의 <tr>...</tr> 전체를 포함하지 않고, 다음 code 전까지임.
                        
                        # number 클래스 태그 내부 값 추출
                        numbers = re.findall(r'class="number">([\d,\.\+\-]+)(?:</span>|</td>)', part)
                        
                        if not numbers: continue
                        
                        price = 0
                        rate = 0.0
                        volume = 0
                        
                        # 페이지별 컬럼 순서가 다름
                        if type == "rise" or type == "fall":
                            # [0]: 현재가, [1]: 전일비, [2]: 등락률(보통 span안에 있음), [3]: 거래량 ...
                            # 네이버 상승페이지: 현재가, 전일비, 등락률, 거래량, ...
                            
                            price = int(numbers[0].replace(',', ''))
                            
                            # 등락률은 별도 파싱 (tah 클래스 등)
                            # %가 포함된 텍스트 찾기
                            rate_match = re.search(r'([\+\-]?\d+\.\d+)%', part)
                            if rate_match:
                                rate = float(rate_match.group(1))
                            else:
                                # numbers[2]가 등락률일 가능성 (숫자만 있는 경우)
                                try:
                                    rate = float(numbers[2].strip().replace('%', ''))
                                except: pass
                                
                            # 거래량 (대략 4번째 숫자)
                            if len(numbers) > 3:
                                volume = int(numbers[3].replace(',', ''))
                                
                        elif type == "volume":
                            # 거래량상위: 현재가, 전일비, 등락률, 거래량, ...
                            price = int(numbers[0].replace(',', ''))
                            
                            rate_match = re.search(r'([\+\-]?\d+\.\d+)%', part)
                            if rate_match:
                                rate = float(rate_match.group(1))
                                
                            if len(numbers) > 3:
                                volume = int(numbers[3].replace(',', ''))
                        
                        ranking_data.append({
                            "code": code,
                            "name": name,
                            "price": price,
                            "change": 0, # 계산 생략
                            "rate": rate,
                            "volume": volume
                        })
                        
                    except Exception as parse_e:
                        continue
                        
            except Exception as e:
                print(f"크롤링 오류 ({url}): {e}")
                continue
                
        # 중복 제거 및 리스트 합치기
        seen = set()
        unique_ranking = []
        for item in ranking_data:
            if item['code'] not in seen:
                seen.add(item['code'])
                unique_ranking.append(item)
        
        # 정렬
        if type == "rise":
            unique_ranking.sort(key=lambda x: x['rate'], reverse=True)
        elif type == "fall":
            unique_ranking.sort(key=lambda x: x['rate'])
        elif type == "volume":
            unique_ranking.sort(key=lambda x: x['volume'], reverse=True)
            
        return unique_ranking[:10]


    except Exception as e:
        print(f"랭킹 조회 오류: {e}")
        return []



def get_stock_name(code):
    # 간단한 종목명 매핑 (없으면 코드 반환)
    mapping = {
        "005930": "삼성전자", "000660": "SK하이닉스", "035420": "NAVER", 
        "005380": "현대차", "051910": "LG화학", "006400": "3삼성SDI",
        "035720": "카카오", "207940": "삼성바이오로직스", "068270": "셀트리온",
        "003670": "포스코퓨처엠", "086520": "에코프로", "247540": "에코프로비엠",
        "035900": "JYP Ent.", "022100": "포스코DX", "066970": "엘앤에프"
    }
    return mapping.get(code, code)
  

# === 종목 분석 API ===
@app.post("/api/trading/analyze")
def api_trading_analyze(stock_code: str):
    """종목 AI 분석"""
    from .kis_api import get_current_price
    
    try:
        price_info = get_current_price(stock_code)
        
        if not price_info:
            return {"error": "종목 정보를 가져올 수 없습니다"}
        
        change_rate = price_info.get("change_rate", 0)
        
        # 간단한 의견 생성
        if change_rate > 5:
            opinion = "긍정적"
            confidence = 75
            reason = ["강한 상승세", f"+{change_rate:.1f}% 급등", "매수 타이밍"]
        elif change_rate > 2:
            opinion = "긍정적"
            confidence = 65
            reason = [f"+{change_rate:.1f}% 상승", "긍정적 흐름", "단기 매수 고려"]
        elif change_rate < -5:
            opinion = "부정적"
            confidence = 70
            reason = [f"{change_rate:.1f}% 급락", "하락 추세", "관망 권장"]
        elif change_rate < -2:
            opinion = "중립"
            confidence = 60
            reason = [f"{change_rate:.1f}% 하락", "변동성 주의", "반등 대기"]
        else:
            opinion = "중립"
            confidence = 55
            reason = ["횡보 중", "추세 불명확", "관망"]
        
        return {
            "opinion": opinion,
            "confidence": confidence,
            "reason": reason
        }
        
    except Exception as e:
        print(f"종목 분석 오류: {e}")
        return {"error": str(e)}


# === 주식 주문 API ===
@app.post("/api/trading/manual_order")
def api_trading_manual_order(stock_code: str, order_type: str, quantity: int, price: int = 0, market: str = "KRX"):
    """수동 주문 (매수/매도)"""
    from .kis_api import order_stock
    
    try:
        return order_stock(stock_code, order_type, quantity, price)
    except Exception as e:
        print(f"주문 처리 오류: {e}")
        return {"status": "error", "message": str(e)}


# === 뉴스 API ===
@app.get("/api/news/headlines")
def api_news_headlines():
    """네이버 금융 실시간 속보 크롤링 (특징주 위주)"""
    import httpx
    import re
    
    try:
        # 실시간 속보 (전체)
        url = "https://finance.naver.com/news/news_list.naver?mode=LSS2D&section_id=101&section_id2=258"
        
        # 헤더 추가 (차단 방지)
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        resp = httpx.get(url, headers=headers, timeout=3.0)
        html = resp.content.decode("euc-kr", errors="ignore")
        
        # 뉴스 리스트 파싱
        # <dl> <dt> <a href="...">제목</a> </dt> ... </dl>
        # 특징주 뉴스는 보통 제목에 [특징주] 가 붙거나 종목명이 포함됨.
        
        # 정규식으로 링크와 제목 추출
        # <a href="/news/news_read.naver..." ... >제목</a>
        
        items = re.findall(r'<a href="(/news/news_read\.naver[^"]+)"[^>]*>([^<]+)</a>', html)
        
        news_list = []
        seen = set()
        
        for link, title in items:
            title = title.strip()
            # 불필요한 뉴스 필터링
            if title in seen: continue
            if not title: continue
            if "연관기사" in title: continue
            
            seen.add(title)
            
            # HTML 엔티티 제거 (&quot; 등)
            title = title.replace("&quot;", '"').replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
            
            full_link = "https://finance.naver.com" + link
            news_list.append({
                "title": title,
                "link": full_link
            })
            
        return news_list[:30] # 30개까지 넉넉하게 반환
        
    except Exception as e:
        print(f"뉴스 조회 오류: {e}")
        return [
            {"title": "뉴스 데이터를 불러오는 중입니다...", "link": "#"}
        ]


# ========================================
# [ADDED BY GEMINI] Missing Trading APIs
# ========================================

# === 종목 검색 API ===
@app.get("/api/trading/search")
def api_trading_search(query: str, market: str = "KR"):
    "종목 검색 API"
    import json
    import os
    
    # 1. 파일에서 종목 DB 로드 시도
    stocks = []
    
    # 캐시된 종목 파일 확인 (현재 디렉토리 기준 상위/루트 등 확인)
    # 캐시된 종목 파일 확인 (현재 디렉토리 기준 상위/루트 등 확인)
    # c:\Project\CB_kis\data\all_stocks.json
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    stock_file = os.path.join(base_dir, "data", "all_stocks.json")
    
    if not os.path.exists(stock_file):
        # 백업 경로 (루트)
        stock_file_root = os.path.join(base_dir, "all_stocks.json")
        if os.path.exists(stock_file_root):
             stock_file = stock_file_root

    if not os.path.exists(stock_file):
        # 파일이 없으면 주요 종목만 반환
        fallback_stocks = [
            {"stock_code": "005930", "stock_name": "삼성전자", "exchange": "KRX"},
            {"stock_code": "000660", "stock_name": "SK하이닉스", "exchange": "KRX"},
            {"stock_code": "035420", "stock_name": "NAVER", "exchange": "KRX"},
            {"stock_code": "035720", "stock_name": "카카오", "exchange": "KRX"},
            {"stock_code": "005380", "stock_name": "현대차", "exchange": "KRX"},
            {"stock_code": "051910", "stock_name": "LG화학", "exchange": "KRX"},
            {"stock_code": "207940", "stock_name": "삼성바이오로직스", "exchange": "KRX"},
            {"stock_code": "000270", "stock_name": "기아", "exchange": "KRX"},
            {"stock_code": "068270", "stock_name": "셀트리온", "exchange": "KRX"},
            {"stock_code": "086520", "stock_name": "에코프로", "exchange": "KOSDAQ"},
            {"stock_code": "247540", "stock_name": "에코프로비엠", "exchange": "KOSDAQ"}
        ]
        
        # 검색 필터
        results = [s for s in fallback_stocks if query.upper() in s["stock_name"] or query in s["stock_code"]]
        return results

    try:
        with open(stock_file, "r", encoding="utf-8") as f:
            stocks = json.load(f)
            
        if isinstance(stocks, dict):
            # KR/US 키가 있는 경우
            all_list = stocks.get("KR", []) + stocks.get("US", [])
        else:
            # 리스트인 경우 (구버전 호환)
            all_list = stocks
            
        # 검색 로직
        import unicodedata
        
        normalized_query = unicodedata.normalize('NFC', query).upper()
        # print(f"DEBUG SEARCH: Query='{query}' Norm='{normalized_query}'")
        
        results = []
        for s in all_list:
            # Code or Name matching
            # Name: 'name' or 'stock_name'
            # Code: 'code' or 'stock_code'
            s_name = s.get("name") or s.get("stock_name") or ""
            s_code = s.get("code") or s.get("stock_code") or ""
            
            norm_name = unicodedata.normalize('NFC', s_name).upper()
            
            # if "이원" in norm_name:
            #     print(f"DEBUG CANDIDATE: {norm_name} ({s_code})")
            
            if normalized_query in norm_name or query in s_code:
                # 필드명 통일해서 반환
                results.append({
                    "stock_code": s_code,
                    "stock_name": s_name,
                    "market": s.get("market", "KR"),
                    "exchange": s.get("exchange", "KRX")
                })
                if len(results) >= 10: break
                
        return results
    except Exception as e:
        print(f"검색 오류: {e}")
        return []


# === 계좌 잔고/자산 API ===
@app.get("/api/trading/performance")
def api_trading_performance(stock_code: str = "005930"):
    """계좌 자산/잔고 + 주문가능금액 조회"""
    from .kis_auth import get_access_token
    import httpx
    
    try:
        from .kis_auth import KIS_APPKEY, KIS_APPSECRET, KIS_ACCOUNT_NO, KIS_ACCOUNT_PROD, KIS_BASE_URL
        
        # Alias if needed for internal logic or just use new names
        KIS_CANO = KIS_ACCOUNT_NO
        KIS_ACNT_PRDT_CD = KIS_ACCOUNT_PROD
        
        token = get_access_token()
        headers = {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {token}",
            "appkey": KIS_APPKEY,
            "appsecret": KIS_APPSECRET,
            "tr_id": "VTTC8908R" if "vts" in KIS_BASE_URL else "TTTC8908R" # 매수주문가능조회
        }
        
        # 1. 매수주문가능조회 (TTTC8908R)
        url = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/trading/inquire-psbl-order"
        params = {
            "CANO": KIS_CANO,
            "ACNT_PRDT_CD": KIS_ACNT_PRDT_CD,
            "PDNO": stock_code, 
            "ORD_UNPR": "0", 
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "Y", 
            "OVRS_ICLD_YN": "N"
        }
        
        resp = httpx.get(url, headers=headers, params=params, timeout=5.0)
        data = resp.json()
        
        cash_buy_amt = 0
        max_buy_amt = 0
        
        if data.get('rt_cd') == '0':
            output = data.get('output', {})
            cash_buy_amt = int(output.get('ord_psbl_cash', 0) or output.get('nrcvb_buy_amt', 0))
            max_buy_amt = int(output.get('max_buy_amt', 0) or output.get('ord_psbl_amt', 0))
        else:
            print(f"주문가능조회 실패: {data.get('msg1')}")
            
        # 2. 총 평가자산/예수금 조회
        headers["tr_id"] = "VTTC8434R" if "vts" in KIS_BASE_URL else "TTTC8434R"
        url_bal = f"{KIS_BASE_URL}/uapi/domestic-stock/v1/trading/inquire-balance"
        params_bal = {
            "CANO": KIS_CANO,
            "ACNT_PRDT_CD": KIS_ACNT_PRDT_CD,
            "AFHR_FLPR_YN": "N",
            "OFL_YN": "",
            "INQR_DVSN": "02",
            "UNPR_DVSN": "01",
            "FUND_STTL_ICLD_YN": "N",
            "FNCG_AMT_AUTO_RDPT_YN": "N",
            "PRCS_DVSN": "00",
            "CTX_AREA_FK100": "",
            "CTX_AREA_NK100": ""
        }
        
        resp_bal = httpx.get(url_bal, headers=headers, params=params_bal, timeout=5.0)
        data_bal = resp_bal.json()
        
        total_asset = 0
        total_pnl = 0
        deposits = 0
        
        if data_bal.get('rt_cd') == '0':
            output2 = data_bal.get('output2', [])
            if output2:
                total_asset = int(output2[0].get('tot_evlu_amt', 0))
                deposits = int(output2[0].get('dnca_tot_amt', 0))
                total_pnl = int(output2[0].get('evlu_pfls_smt_tl', 0))

        return {
            "account_total_asset": total_asset,
            "total_pnl": total_pnl,
            "deposits": deposits,
            "cash_buy_amount": cash_buy_amt, # 현금주문가능
            "max_buy_amount": max_buy_amt   # 최대주문가능 (미수포함)
        }

    except Exception as e:
        print(f"Performance API Error: {e}")
        return {"error": str(e)}

# === 미체결 내역 API (더미) ===
@app.get("/api/trading/orders")
def api_trading_orders():
    "미체결 내역 조회 (더미)"
    return [
        {
            "order_id": "1001",
            "stock_code": "005930",
            "stock_name": "삼성전자",
            "side": "매수",
            "price": 72000,
            "quantity": 10,
            "executed_qty": 0,
            "status": "접수",
            "time": "14:20:05"
        }
    ]

# === 거래 내역 API (더미) ===
@app.get("/api/trading/history")
def api_trading_history():
    "거래 내역 조회 (더미)"
    return [
        {
            "id": "2001",
            "stock_name": "SK하이닉스",
            "side": "매수",
            "price": 135000,
            "quantity": 5,
            "amount": 675000,
            "time": "2026-01-09 10:00:00"
        },
        {
            "id": "2002",
            "stock_name": "NAVER",
            "side": "매도",
            "price": 210000,
            "quantity": 2,
            "amount": 420000,
            "time": "2026-01-08 15:30:00"
        }
    ]
# Reload trigger
# Reload trigger 2
# Force Reload 3


# ===�N��&/?���/�ue$�� API (New) ===

@app.post("/api/trading/manual_order")

def api_manual_order(stock_code: str, order_type: str, quantity: int, price: int, market: str = "KR"):

    """?�޸ �N��& ?}1�� (��|1Բ/��{1ĸ)"""

    # ?|1#� KIS API ?լ޸ ?���� (?H��?�ė� ?��?/�o�����??c$? or ?|1#� �cK}�)

    # TTTC8001R (��|1Բ), TTTC8002R (��{1ĸ)

    import logging

    print(f"[ORDER] {order_type} {stock_code} : {quantity}�N?@ {price}??({market})")

    

    # ?C��� ?��� �Z�??

    return {"status": "ok", "message": "�N��& ?��� ?����", "order_id": "123456"}



@app.post("/api/trading/revise_cancel")

def api_revise_cancel(order_id: str, type: str, quantity: int = 0, price: int = 0):

    """�N��& ?���/�ue$��"""

    # type: 'revise' or 'cancel'

    print(f"[REVISE/CANCEL] Order {order_id} -> {type} (Qty:{quantity}, Price:{price})")

    return {"status": "ok", "message": f"�N��& {type} ���% ?����"}

