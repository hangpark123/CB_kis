# 주요 종목 데이터 (코스피/코스닥 상위) - 검색용
KOREA_STOCKS = [
    {"code": "005930", "name": "삼성전자"},
    {"code": "000660", "name": "SK하이닉스"},
    {"code": "373220", "name": "LG에너지솔루션"},
    {"code": "207940", "name": "삼성바이오로직스"},
    {"code": "005380", "name": "현대차"},
    {"code": "000270", "name": "기아"},
    {"code": "005490", "name": "POSCO홀딩스"},
    {"code": "051910", "name": "LG화학"},
    {"code": "035420", "name": "NAVER"},
    {"code": "006400", "name": "삼성SDI"},
    {"code": "068270", "name": "셀트리온"},
    {"code": "035720", "name": "카카오"},
    {"code": "105560", "name": "KB금융"},
    {"code": "028260", "name": "삼성물산"},
    {"code": "012330", "name": "현대모비스"},
    {"code": "055550", "name": "신한지주"},
    {"code": "003550", "name": "LG"},
    {"code": "032830", "name": "삼성생명"},
    {"code": "086790", "name": "하나금융지주"},
    {"code": "034730", "name": "SK"},
    {"code": "000810", "name": "삼성화재"},
    {"code": "015760", "name": "한국전력"},
    {"code": "017670", "name": "SK텔레콤"},
    {"code": "033780", "name": "KT&G"},
    {"code": "018260", "name": "삼성에스디에스"},
    {"code": "323410", "name": "카카오뱅크"},
    {"code": "010950", "name": "S-Oil"},
    {"code": "009150", "name": "삼성전기"},
    {"code": "316140", "name": "우리금융지주"},
    {"code": "034020", "name": "두산에너빌리티"},
    {"code": "036570", "name": "NCsoft"},
    {"code": "011070", "name": "LG이노텍"},
    {"code": "003490", "name": "대한항공"},
    {"code": "090430", "name": "아모레퍼시픽"},
    {"code": "086280", "name": "현대글로비스"},
    {"code": "024110", "name": "기업은행"},
    {"code": "010130", "name": "고려아연"},
    {"code": "030200", "name": "KT"},
    {"code": "047810", "name": "한국항공우주"},
    {"code": "066570", "name": "LG전자"},
    {"code": "251270", "name": "넷마블"},
    {"code": "096770", "name": "SK이노베이션"},
    {"code": "247540", "name": "에코프로비엠"},
    {"code": "086520", "name": "에코프로"},
    {"code": "091990", "name": "셀트리온헬스케어"},
    {"code": "022100", "name": "POSCO퓨처엠"},
    {"code": "403870", "name": "HPSP"},
    {"code": "028300", "name": "HLB"},
    {"code": "293490", "name": "카카오게임즈"},
    {"code": "263750", "name": "펄어비스"},
    {"code": "035900", "name": "JYP Ent."},
    {"code": "352820", "name": "하이브"},
    {"code": "041510", "name": "에스엠"},
    {"code": "122870", "name": "와이지엔터테인먼트"},
]

def search_korea_stocks(keyword: str):
    """
    메모리에 있는 종목 리스트에서 검색
    """
    results = []
    
    # 코드로 정확히 일치
    if keyword.isdigit() and len(keyword) == 6:
        for s in KOREA_STOCKS:
            if s["code"] == keyword:
                results.append(s)
                return results
    
    # 이름으로 검색 (포함 여부)
    for s in KOREA_STOCKS:
        if keyword in s["name"] or keyword in s["code"]:
            results.append(s)
            
    return results


def get_stock_name(code: str) -> str:
    """종목 코드로 이름 찾기"""
    for s in KOREA_STOCKS:
        if s["code"] == code:
            return s["name"]
    return code  # 없으면 코드 반환
