import httpx
from bs4 import BeautifulSoup
import asyncio

async def get_naver_rank(rank_type='rise'):
    """
    네이버 금융 랭킹 크롤링
    rank_type: 'rise' (상승), 'fall' (하락), 'volume' (거래량상위)
    """
    base_url = "https://finance.naver.com/sise/"
    target_url = ""
    
    if rank_type == 'rise':
        target_url = base_url + "sise_rise.naver"
    elif rank_type == 'fall':
        target_url = base_url + "sise_fall.naver"
    elif rank_type == 'volume':
        target_url = base_url + "sise_quant.naver" # 거래량상위
    else:
        return []

    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(target_url)
            res.encoding = 'euc-kr' # 네이버 금융은 euc-kr
            
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 테이블 파싱
        rows = soup.select('table.type_2 tr')
        results = []
        
        for row in rows:
            cols = row.select('td')
            if len(cols) < 5:
                continue
                
            # 순위 있는 행만
            try:
                rank_text = cols[0].text.strip()
                if not rank_text.isdigit():
                    continue
                    
                rank = int(rank_text)
                name = cols[1].text.strip()
                code = cols[1].select_one('a')['href'].split('code=')[1]
                
                # 현재가, 등락률
                price = cols[2].text.strip()
                diff_rate = cols[4].text.strip().replace('%', '')
                
                results.append({
                    "rank": rank,
                    "code": code,
                    "name": name,
                    "price": price,
                    "change_rate": diff_rate,
                    "volume": cols[5].text.strip() if rank_type == 'volume' else cols[6].text.strip()
                })
                
                if len(results) >= 10: # 상위 10개만
                    break
            except:
                continue
                
        return results

    except Exception as e:
        print(f"[Crawler Error] {e}")
        return []

async def get_theme_rank():
    """
    네이버 금융 테마 랭킹 크롤링 (mock 또는 실제)
    https://finance.naver.com/sise/theme.naver
    """
    url = "https://finance.naver.com/sise/theme.naver"
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        async with httpx.AsyncClient() as client:
            res = await client.get(url, headers=headers)
            res.encoding = 'euc-kr' 
            
        soup = BeautifulSoup(res.text, 'html.parser')
        rows = soup.select('table.type_1 tr')
        results = []
        
        for row in rows:
            cols = row.select('td')
            if len(cols) < 3: continue
            
            try:
                theme_name = cols[0].text.strip()
                if not theme_name: continue
                
                rate = cols[1].text.strip().replace('%', '')
                leading_stock = cols[6].text.strip() # 주도주 (최근 3일 등락률 칸 옆) - 구조 확인 필요
                # 네이버 테마 페이지 구조: 테마명(0), 전일대비(1), 최근3일(2)... 주도주 정보는 상세에 있음.
                # 편의상 테마명과 등락률만
                
                results.append({
                    "theme_name": theme_name,
                    "change_rate": rate,
                    "leading_stock": "-" # 상세 크롤링 필요하여 생략
                })
                
                if len(results) >= 10:
                    break
            except:
                continue
        return results
    except:
        return []

if __name__ == "__main__":
    # Test
    data = asyncio.run(get_naver_rank('rise'))
    print("Rise:", data[:3])
