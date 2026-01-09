// =======================================
// TRADINGVIEW STYLE - MAIN JAVASCRIPT
// =======================================

let currentMarket = 'KR';
let selectedStock = {
    code: '005930',
    name: '삼성전자',
    exchange: 'KRX'
};
let currentOrderType = 'BUY';
let accountData = null; // 계좌 정보 저장
let portfolioData = []; // 포트폴리오 저장

// === INITIALIZATION ===
// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', async () => {
    // 1. URL 파라미터 확인
    const urlParams = new URLSearchParams(window.location.search);
    const code = urlParams.get('code');
    const name = urlParams.get('name');
    const exchange = urlParams.get('exchange') || 'KRX';

    loadWatchlist();
    loadAIPicks();

    // 2. 잔고/포트폴리오 순차 로드
    await refreshAccountInfo();
    await new Promise(r => setTimeout(r, 500));
    await loadPortfolio();

    // 3. 종목 선택
    if (code && name) {
        selectStock(code, name, exchange);
    } else {
        selectStock('005930', '삼성전자', 'KRX');
    }

    // 4. 이벤트 리스너 설정
    setupSearch();
    setupTabs(); // 탭 기능 설정

    // Auto-refresh (30초)
    setInterval(async () => {
        await refreshAccountInfo();
    }, 30000);

    // Sidebar '보유잔고' 버튼 동작 강화
    const sidebarBtns = document.querySelectorAll('.sidebar-left .tab-btn');
    if (sidebarBtns.length > 1) { // 0: 관심종목, 1: 보유잔고
        sidebarBtns[1].addEventListener('click', () => loadPortfolio());
    }
});

// === TABS ===
function setupTabs() {
    // 하단 패널 탭 (보유잔고, 미체결, 거래내역)
    const tabs = document.querySelectorAll('.panel-tab');
    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            // Active 클래스 토글
            tabs.forEach(t => t.classList.remove('active'));
            tab.classList.add('active');

            // 탭 이름에 따라 컨텐츠 로드
            const tabName = tab.textContent.trim();
            if (tabName.includes('보유잔고') || tabName.includes('Positions')) {
                loadPortfolio();
            } else if (tabName.includes('미체결') || tabName.includes('Orders')) {
                loadOrders();
            } else if (tabName.includes('거래내역') || tabName.includes('History')) {
                loadHistory();
            }
        });
    });
}

// === SEARCH ===
function setupSearch() {
    const input = document.getElementById('symbolSearch');
    const results = document.getElementById('searchResults');

    let searchTimer;
    input.addEventListener('input', (e) => {
        clearTimeout(searchTimer);
        const query = e.target.value.trim();

        if (query.length < 1) {
            results.style.display = 'none';
            return;
        }
        searchTimer = setTimeout(() => searchStocks(query), 300);
    });

    // 외부 클릭 시 검색창 닫기
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.search-bar-wrap')) {
            results.style.display = 'none';
        }
    });

    // 검색창 클릭 시 다시 보이기 (내용 있으면)
    input.addEventListener('click', () => {
        if (input.value.trim().length > 0) {
            results.style.display = 'block';
        }
    });
}

async function searchStocks(query) {
    try {
        const res = await fetch(`/api/trading/search?query=${encodeURIComponent(query)}&market=${currentMarket}`);
        if (!res.ok) throw new Error('Search failed');

        const stocks = await res.json();
        const results = document.getElementById('searchResults');

        if (!stocks || stocks.length === 0) {
            results.style.display = 'none';
            return;
        }

        results.innerHTML = stocks.map(stock => `
            <div class="search-result-item" onclick="selectStockFromSearch('${stock.stock_code}', '${stock.stock_name}', '${stock.exchange || 'KRX'}')">
                <div style="font-weight:700;">${stock.stock_name}</div>
                <div style="font-size:12px; color:#5e6673; font-family:var(--font-mono);">${stock.stock_code}</div>
            </div>
        `).join('');

        results.style.display = 'block'; // 명시적 표시

    } catch (e) {
        console.error('Search error:', e);
    }
}

// === DATA FUNCTIONS (Orders, History) ===
async function loadOrders() {
    // 헤더 변경
    const thead = document.querySelector('.pro-table thead tr');
    thead.innerHTML = '<th>주문시간</th><th>종목명</th><th>구분</th><th>주문가격</th><th>주문수량</th><th>상태</th>';

    // 바디 로드
    const tbody = document.getElementById('portfolioTableBody');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">로딩중...</td></tr>';

    try {
        const res = await fetch('/api/trading/orders');
        const orders = await res.json();

        if (!orders || orders.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#5e6673;">미체결 주문이 없습니다.</td></tr>';
            return;
        }

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td style="font-family:var(--font-mono);">${o.time}</td>
                <td style="font-weight:700;">${o.stock_name} <span style="font-size:10px; color:#5e6673;">${o.stock_code}</span></td>
                <td style="color:${o.side === '매수' ? '#00e676' : '#ff3b69'}">${o.side}</td>
                <td style="font-family:var(--font-mono);">${o.price.toLocaleString()}</td>
                <td style="font-family:var(--font-mono);">${o.quantity}</td>
                <td><span style="background:#2a2e39; padding:2px 6px; border-radius:4px; font-size:11px;">${o.status}</span></td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#ff3b69;">데이터 로드 실패</td></tr>';
    }
}

async function loadHistory() {
    // 헤더 변경
    const thead = document.querySelector('.pro-table thead tr');
    thead.innerHTML = '<th>체결시간</th><th>종목명</th><th>구분</th><th>체결가</th><th>수량</th><th>거래금액</th>';

    // 바디 로드
    const tbody = document.getElementById('portfolioTableBody');
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">로딩중...</td></tr>';

    try {
        const res = await fetch('/api/trading/history');
        const history = await res.json();

        if (!history || history.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#5e6673;">거래 내역이 없습니다.</td></tr>';
            return;
        }

        tbody.innerHTML = history.map(h => `
            <tr>
                <td style="font-family:var(--font-mono);">${h.time.substring(5, 16)}</td>
                <td style="font-weight:700;">${h.stock_name}</td>
                <td style="color:${h.side === '매수' ? '#00e676' : '#ff3b69'}">${h.side}</td>
                <td style="font-family:var(--font-mono);">${h.price.toLocaleString()}</td>
                <td style="font-family:var(--font-mono);">${h.quantity}</td>
                <td style="font-family:var(--font-mono);">${h.amount.toLocaleString()}</td>
            </tr>
        `).join('');
    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#ff3b69;">데이터 로드 실패</td></tr>';
    }
}


function selectStockFromSearch(code, name, exchange) {
    selectStock(code, name, exchange);
    document.getElementById('searchResults').style.display = 'none';
    document.getElementById('symbolSearch').value = '';
}

// === STOCK SELECTION ===
function selectStock(code, name, exchange) {
    selectedStock = { code, name, exchange };

    document.getElementById('stockName').textContent = name;
    document.getElementById('stockCode').textContent = code;
    document.getElementById('stockExchange').textContent = exchange;

    initChart(code, exchange);
    loadAIAnalysis(code);

    // Update watchlist active state
    document.querySelectorAll('.watch-item').forEach(item => {
        item.classList.remove('active');
    });

    // 현재가 조회하여 주문 가격에 자동 설정
    fetchCurrentPrice(code, exchange);
}

async function fetchCurrentPrice(code, exchange) {
    try {
        // KIS API로 현재가 조회 (한국 주식만)
        if (exchange === 'KRX' || exchange === 'KOSPI' || exchange === 'KOSDAQ') {
            const res = await fetch(`/api/trading/current_price?stock_code=${code}`);
            const data = await res.json();

            if (data && data.current_price) {
                document.getElementById('orderPrice').value = data.current_price;
                document.getElementById('currentPrice').textContent = data.current_price.toLocaleString() + '원';

                const changeRate = data.change_rate || 0;
                const changeElem = document.getElementById('priceChange');
                changeElem.textContent = (changeRate > 0 ? '+' : '') + changeRate + '%';
                changeElem.style.color = changeRate >= 0 ? '#00e676' : '#ff3b69';
            }
        }
    } catch (e) {
        console.error('Current price fetch error:', e);
        document.getElementById('orderPrice').value = 0;
    }
}



let tvWidget = null;
let lwChart = null;
let candleSeries = null;
let volumeSeries = null;

async function initChart(code, exchange) {
    const container = document.getElementById('chartContainer');
    container.innerHTML = '';

    // 리소스 정리
    if (lwChart) {
        lwChart.remove();
        lwChart = null;
    }

    if (exchange === 'KRX' || exchange === 'KOSPI' || exchange === 'KOSDAQ') {
        // === Korean Market: Use Lightweight Charts with KIS Data ===
        container.style.position = 'relative';

        // 1. 차트 데이터 가져오기
        try {
            console.log(`[Chart] Fetching data for ${code}...`);
            const res = await fetch(`/api/trading/chart_data?stock_code=${code}`);

            if (!res.ok) {
                throw new Error(`API Error ${res.status}`);
            }

            const data = await res.json();
            console.log(`[Chart] Data received: ${data ? data.length : 0} candles`);

            if (!data || data.length === 0) {
                container.innerHTML = `<div style="color:#787b86; display:flex; justify-content:center; align-items:center; height:100%;">
                    <div>
                        <div>차트 데이터 없음 (${code})</div>
                        <div style="font-size:12px; margin-top:5px;">장 운영시간이 아니거나 데이터가 부족합니다</div>
                    </div>
                </div>`;
                return;
            }

            // 데이터 변환 (YYYYMMDD -> YYYY-MM-DD)
            const ohlcData = data.map(d => {
                const dateStr = d.time;
                return {
                    time: `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`,
                    open: d.open,
                    high: d.high,
                    low: d.low,
                    close: d.close
                };
            });

            const volData = data.map(d => {
                const dateStr = d.time;
                return {
                    time: `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`,
                    value: d.volume,
                    color: d.close >= d.open ? 'rgba(0, 230, 118, 0.5)' : 'rgba(255, 59, 105, 0.5)'
                };
            });

            // 2. 차트 생성
            if (!window.LightweightCharts) {
                throw new Error('LightweightCharts library not loaded');
            }

            lwChart = LightweightCharts.createChart(container, {
                width: container.clientWidth,
                height: container.clientHeight,
                layout: {
                    background: { type: 'solid', color: '#131722' },
                    textColor: '#d1d4dc',
                },
                grid: {
                    vertLines: { color: '#1e222d' },
                    horzLines: { color: '#1e222d' },
                },
                rightPriceScale: {
                    borderColor: '#2a2e39',
                },
                timeScale: {
                    borderColor: '#2a2e39',
                    timeVisible: true,
                    secondsVisible: false,
                },
                crosshair: {
                    mode: LightweightCharts.CrosshairMode.Normal,
                },
            });

            // 3. 캔들스틱 시리즈 추가
            candleSeries = lwChart.addCandlestickSeries({
                upColor: '#00e676',
                downColor: '#ff3b69',
                borderVisible: false,
                wickUpColor: '#00e676',
                wickDownColor: '#ff3b69',
            });
            candleSeries.setData(ohlcData);

            // === 이동평균선(MA) 추가 ===
            function calculateSMA(data, count) {
                var avg = function (data) {
                    var sum = 0;
                    var avg = 0;
                    for (var i = 0; i < data.length; i++) {
                        sum += data[i].close;
                    }
                    avg = sum / data.length;
                    return avg;
                };
                var result = [];
                for (var i = count - 1, len = data.length; i < len; i++) {
                    var val = avg(data.slice(i - count + 1, i + 1));
                    result.push({ time: data[i].time, value: val });
                }
                return result;
            }

            const ma20Data = calculateSMA(ohlcData, 20);
            const ma60Data = calculateSMA(ohlcData, 60);

            const ma20Series = lwChart.addLineSeries({ color: '#FFD700', lineWidth: 1, title: 'MA20' });
            ma20Series.setData(ma20Data);

            const ma60Series = lwChart.addLineSeries({ color: '#2962ff', lineWidth: 1, title: 'MA60' });
            ma60Series.setData(ma60Data);


            // 4. 거래량 시리즈 추가 (오버레이)
            volumeSeries = lwChart.addHistogramSeries({
                color: '#26a69a',
                priceFormat: {
                    type: 'volume',
                },
                priceScaleId: '', // 같은 스케일에 오버레이 (아래쪽에 배치하려면 조정 필요)
            });

            // 거래량을 아래 20% 높이로 제한하기 위해 가격 스케일 조정 (트릭)
            volumeSeries.priceScale().applyOptions({
                scaleMargins: {
                    top: 0.8, // 상단 80%는 비워둠 (캔들 영역)
                    bottom: 0,
                },
            });
            volumeSeries.setData(volData);

            // 5. 반응형 리사이징
            new ResizeObserver(entries => {
                if (entries.length === 0 || entries[0].target !== container) { return; }
                const newRect = entries[0].contentRect;
                lwChart.applyOptions({ height: newRect.height, width: newRect.width });
            }).observe(container);

        } catch (e) {
            console.error('Chart load error:', e);
            container.innerHTML = '<div style="color:#ff3b69; display:flex; justify-content:center; align-items:center; height:100%;">차트 로딩 실패</div>';
        }

    } else {
        // === US Market: Use TradingView Widget ===
        // US: TradingView
        new TradingView.widget({
            "width": "100%",
            "height": "100%",
            "symbol": `${exchange}:${code}`,
            "interval": "D",
            "timezone": "America/New_York",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#131722",
            "enable_publishing": false,
            "backgroundColor": "#131722",
            "gridColor": "#1e222d",
            "hide_side_toolbar": false,
            "allow_symbol_change": false,
            "container_id": "chartContainer"
        });
    }
}


// === MARKET TOGGLE ===
function toggleMarket() {
    currentMarket = currentMarket === 'KR' ? 'US' : 'KR';
    const btn = document.getElementById('marketSwitch');
    btn.textContent = currentMarket === 'KR' ? '🇰🇷 KR' : '🇺🇸 US';

    if (currentMarket === 'US') {
        selectStock('AAPL', 'Apple Inc', 'NASDAQ');
    } else {
        selectStock('005930', '삼성전자', 'KRX');
    }
}

// === WATCHLIST ===
function loadWatchlist() {
    const saved = localStorage.getItem('watchlist_tv');
    const watchlist = saved ? JSON.parse(saved) : [
        { code: '005930', name: '삼성전자', exchange: 'KRX' },
        { code: '000660', name: 'SK하이닉스', exchange: 'KRX' },
        { code: '035420', name: 'NAVER', exchange: 'KRX' },
        { code: 'AAPL', name: 'Apple', exchange: 'NASDAQ' }
    ];

    const container = document.getElementById('watchlist');
    container.innerHTML = watchlist.map(stock => `
        <div class="watch-item" onclick="selectStock('${stock.code}', '${stock.name}', '${stock.exchange}')">
            <div class="item-row">
                <span class="item-name">${stock.name}</span>
                <span class="item-price">--</span>
            </div>
            <div class="item-row">
                <span class="item-code">${stock.code}</span>
                <span class="item-change up">--</span>
            </div>
        </div>
    `).join('');
}

function showAddSymbol() {
    const code = prompt('종목 코드 입력:');
    if (!code) return;
    const name = prompt('종목명 입력:');
    if (!name) return;

    const saved = localStorage.getItem('watchlist_tv') || '[]';
    const watchlist = JSON.parse(saved);
    watchlist.push({ code, name, exchange: currentMarket === 'KR' ? 'KRX' : 'NASDAQ' });
    localStorage.setItem('watchlist_tv', JSON.stringify(watchlist));
    loadWatchlist();
}

// === PORTFOLIO (Pro Table) ===
async function loadPortfolio() {
    // Sidebar 연동: 하단 탭 UI 활성화 (Loop 방지: click() 대신 클래스만 조작)
    const bottomTabs = document.querySelectorAll('.panel-tab');
    if (bottomTabs.length > 0) {
        document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
        bottomTabs[0].classList.add('active');
    }

    // 헤더 복구 (Orders/History 탭에서 왔을 경우)
    const thead = document.querySelector('.pro-table thead tr');
    if (thead) {
        thead.innerHTML = '<th>종목명</th><th>구분</th><th>보유수량</th><th>매입단가</th><th>현재가</th><th>평가손익 (수익률)</th>';
    }

    try {
        const res = await fetch('/api/trading/positions');
        const positions = await res.json();

        portfolioData = positions || []; // 전역 변수 업데이트

        // Table Body Target
        const tbody = document.getElementById('portfolioTableBody');
        if (!tbody) return; // 호환성 체크

        if (!positions || positions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#5e6673;">보유 중인 종목이 없습니다.</td></tr>';
            return;
        }

        tbody.innerHTML = positions.map(p => {
            const isPlus = p.pnl_rate >= 0;
            const pnlClass = isPlus ? 'up' : 'down';
            // 보유수량, 평가금액, 현재가 등
            const qty = parseInt(p.quantity).toLocaleString();
            const pnl = parseInt(p.pnl).toLocaleString();
            const rate = p.pnl_rate?.toFixed(2);

            return `
            <tr onclick="selectStock('${p.stock_code}', '${p.corp_name_kr || p.stock_name}', 'KRX')" style="cursor:pointer;">
                <td>
                    <div style="font-weight:700;">${p.corp_name_kr || p.stock_name}</div>
                    <div style="font-size:10px; color:#5e6673; font-family:var(--font-mono);">${p.stock_code}</div>
                </td>
                <td style="color:#00e676;">Long</td>
                <td style="font-family:var(--font-mono);">${qty}</td>
                <td style="font-family:var(--font-mono);">${parseInt(p.avg_price).toLocaleString()}</td>
                <td style="font-family:var(--font-mono); font-weight:700;">${parseInt(p.current_price).toLocaleString()}</td>
                <td class="${pnlClass}" style="font-family:var(--font-mono); font-weight:700;">
                    ${pnl} <span style="font-size:11px; font-weight:400;">(${rate}%)</span>
                </td>
            </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Portfolio error:', e);
    }
}

function refreshPortfolio() {
    loadPortfolio();
}

// === ACCOUNT INFO ===
// 토글 UI 업데이트 함수
function updateToggleUI(labelElem) {
    // 1. 모든 라디오 해제/선택 처리 (HTML label for 연결로 자동 처리되지만 스타일 위해)
    const container = labelElem.parentElement;
    const labels = container.querySelectorAll('.toggle-btn');

    labels.forEach(l => {
        l.classList.remove('active');
        l.style.color = '#848e9c';
        l.style.background = 'transparent';
    });

    // 2. 선택된 녀석 스타일 적용
    labelElem.classList.add('active');
    labelElem.style.color = '#eaecef';
    labelElem.style.background = '#333';

    // 3. 연결된 라디오 체크 (이미 click event로 label-for가 작동하겠지만 명시적으로)
    const inputId = labelElem.getAttribute('for');
    const input = document.getElementById(inputId);
    if (input) input.checked = true;
}

// === ACCOUNT INFO ===
async function refreshAccountInfo() {
    try {
        // 선택된 종목 코드가 있으면 이를 기준으로 최대주문가능금액 조회
        const code = (typeof selectedStock !== 'undefined' && selectedStock.code) ? selectedStock.code : '005930';

        const res = await fetch(`/api/trading/performance?stock_code=${code}`);
        let data = null;

        if (res.ok) {
            data = await res.json();
        }

        // 데이터가 없거나, cash_buy_amount가 없으면(0 포함) 데모용 더미 데이터 사용 (UI 프리뷰용)
        // 실제 API가 성공해서 0원이 나온 경우일 수도 있지만, 현재 개발 단계에서는
        // 0원이면 뭔가 잘못된(필드 누락) 상태로 간주하고 데모 값을 보여준다.
        if (!data || !data.cash_buy_amount) {
            console.warn('Using dummy account data for preview (Missing API fields)');
            data = {
                account_total_asset: data && data.account_total_asset ? data.account_total_asset : 98924616,
                total_pnl: data && data.total_pnl ? data.total_pnl : -4000,
                deposits: 100000000,
                cash_buy_amount: 97689000, // 약 9.7천만
                max_buy_amount: 497800000 // 약 5억 (미수)
            };
        }

        // 전역 변수 매핑 (setQtyPct에서 사용)
        accountData = {
            cash: data.cash_buy_amount || data.deposits || 0, // 주문 시 현금 주문 기준
            max_buy: data.max_buy_amount || 0,
            total_asset: data.account_total_asset
        };

        // 원화 표시로 변경
        const assetElem = document.getElementById('accountAsset');
        if (assetElem) assetElem.textContent = '₩' + (data.account_total_asset || 0).toLocaleString();

        const pnl = data.total_pnl || 0;
        const pnlElem = document.getElementById('accountPnL');
        if (pnlElem) {
            pnlElem.textContent = (pnl > 0 ? '+₩' : '₩') + pnl.toLocaleString();
            pnlElem.style.color = pnl >= 0 ? '#00e676' : '#ff3b69';
        }

        // 호가창 하단 주문가능 금액 업데이트 (현금/최대 분리)
        const cashElem = document.querySelector('.max-cash-bal');
        if (cashElem) cashElem.textContent = (data.cash_buy_amount || 0).toLocaleString();

        const marginElem = document.querySelector('.max-margin-bal');
        if (marginElem) marginElem.textContent = (data.max_buy_amount || 0).toLocaleString();

    } catch (e) {
        console.error('Account info error:', e);
    }
}

// === AI PICKS ===
async function loadAIPicks() {
    try {
        const res = await fetch('/api/ai/recommendations?limit=3');
        const picks = await res.json();

        const container = document.getElementById('aiPicks');
        if (!container) return; // 요소 없으면 무시

        if (!picks || picks.length === 0) {
            container.innerHTML = '<div style="padding:8px; color:#5e6673; font-size:11px;">추천 종목이 없습니다.</div>';
            return;
        }

        container.innerHTML = picks.map(pick => `
            <div class="ai-pick-item" style="padding:6px; cursor:pointer;" onclick="selectStock('${pick.stock_code}', '${pick.stock_name}', 'KRX')">
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:12px; font-weight:700;">${pick.stock_name}</span>
                    <span style="color:#00e676; font-size:11px; font-weight:700;">${pick.confidence}%</span>
                </div>
                <div style="display:flex; justify-content:space-between;">
                    <span style="font-size:10px; color:#5e6673;">${pick.stock_code}</span>
                    <span style="font-size:10px; color:#d1d4dc;">${pick.expected_return}</span>
                </div>
            </div>
        `).join('');
    } catch (e) {
        console.error('AI picks error:', e);
    }
}


function refreshAIPicks() {
    loadAIPicks();
}

// === BOTTOM TABS ===
function switchBottomTab(tab) {
    document.querySelectorAll('.tab-header').forEach(h => h.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

    event.target.classList.add('active');
    document.getElementById('tab' + tab.charAt(0).toUpperCase() + tab.slice(1)).classList.add('active');
}

// === ORDER ===
function setOrderType(type) {
    currentOrderType = type;

    // 1. Tab Active 처리
    document.querySelectorAll('.trade-tab').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.trim() === type) {
            btn.classList.add('active');
        }
    });

    // 2. 실행 버튼 스타일 변경
    const execBtn = document.getElementById('btnExecute');
    execBtn.classList.remove('buy', 'sell');
    execBtn.classList.add(type === 'BUY' ? 'buy' : 'sell');

    const action = type === 'BUY' ? '매수' : '매도';
    execBtn.textContent = `${selectedStock.name} ${action}`;

    // 3. 현금/미수 토글 UI 표시 여부 (매수일 때만 표시)
    const toggleBox = document.querySelector('.margin-toggle-box');
    if (toggleBox) {
        toggleBox.style.display = (type === 'BUY') ? 'flex' : 'none';
    }
}

// 퍼센트 주식 수 계산
function setQtyPct(pct) {
    if (!selectedStock) return;

    // A. 매도(SELL) 로직: 보유 수량 기준
    if (currentOrderType === 'SELL') {
        if (!portfolioData) {
            alert('보유 종목 정보를 불러오는 중입니다.');
            return;
        }
        // portfolioData에서 현재 종목 찾기 (코드로 매칭)
        const holding = portfolioData.find(p => p.stock_code === selectedStock.code);

        if (!holding) {
            alert('현재 보유하고 있지 않은 종목입니다.');
            document.getElementById('orderQty').value = 0;
            return;
        }

        // 보유 수량 가져오기 (문자열일 수 있으므로 파싱)
        const holdingQty = parseInt(holding.quantity);
        const targetQty = Math.floor(holdingQty * pct);

        const qtyInput = document.getElementById('orderQty');
        if (qtyInput) qtyInput.value = targetQty;
        return;
    }

    // B. 매수(BUY) 로직: 현금/미수 기준
    if (!accountData) return;

    // 현재가 가져오기 (오더 패널의 가격 입력값이 있으면 우선 사용)
    const priceInput = document.getElementById('orderPrice');
    let currentPrice = priceInput && priceInput.value ? parseInt(priceInput.value) : selectedStock.price;

    if (!currentPrice || currentPrice <= 0) {
        // Fallback to screen text if input is empty
        let currentPriceText = document.getElementById('currentPrice').textContent.replace(/,/g, '');
        currentPrice = parseInt(currentPriceText);
    }

    if (!currentPrice || isNaN(currentPrice)) {
        alert('현재가 정보를 불러올 수 없습니다.');
        return;
    }

    // 현금/미수 선택 확인
    const mode = document.querySelector('input[name="orderBase"]:checked')?.value || 'cash';

    // 기준 금액 설정
    let baseAmount = 0;
    if (mode === 'margin') {
        baseAmount = accountData.max_buy || 0;
    } else {
        baseAmount = accountData.cash || 0; // default cash
    }

    // 이미 수수료/증거금 고려된 금액이므로 단순 계산
    const amountToUse = Math.floor(baseAmount * pct);
    const qty = Math.floor(amountToUse / currentPrice);

    const qtyInput = document.getElementById('orderQty');
    if (qtyInput) qtyInput.value = qty;
}

async function executeOrder() {
    const qty = document.getElementById('orderQty').value;
    let price = document.getElementById('orderPrice').value;

    if (!qty || qty <= 0) {
        alert('수량을 입력해주세요.');
        return;
    }

    // 가격이 비어있으면 0 (시장가)으로 처리
    if (!price) price = 0;

    const actionVal = currentOrderType === 'BUY' ? '매수' : '매도';
    if (!confirm(`${selectedStock.name} ${qty}주를 ${actionVal}하시겠습니까?`)) {
        return;
    }

    try {
        const res = await fetch(
            `/api/trading/manual_order?stock_code=${selectedStock.code}&order_type=${currentOrderType}&quantity=${qty}&price=${price}&market=${currentMarket}`,
            { method: 'POST' }
        );

        if (res.status === 422) {
            alert('❌ 주문 오류: 입력값이 올바르지 않습니다. (가격/수량 확인)');
            return;
        }

        const data = await res.json();

        if (data.status === 'ok') {
            alert('✅ 주문이 정상적으로 접수되었습니다!');
            document.getElementById('orderQty').value = '';
            document.getElementById('orderPrice').value = '';
            refreshAccountInfo();
            loadPortfolio();
            loadOrders(); // 미체결 목록도 갱신
        } else {
            alert('❌ 주문 실패: ' + data.message);
        }
    } catch (e) {
        alert('❌ 통신 오류: ' + e.message);
    }
}

// ... (AI Analysis) ...

async function reviseOrder(id, oldQty, oldPrice) {
    const newPrice = prompt('정정할 가격을 입력하세요:', oldPrice);
    if (newPrice === null) return; // 취소 시
    const newQty = prompt('정정할 수량을 입력하세요:', oldQty);
    if (newQty === null) return;

    try {
        const res = await fetch(`/api/trading/revise_cancel?order_id=${id}&type=revise&price=${newPrice}&quantity=${newQty}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
            alert('주문이 정정되었습니다.');
            loadOrders();
            refreshAccountInfo(); // 잔고 갱신
        } else {
            alert('정정 실패: ' + data.message);
        }
    } catch (e) {
        alert('통신 오류');
    }
}

async function cancelOrder(id) {
    if (!confirm(`주문번호 ${id}를 취소하시겠습니까?`)) return;

    try {
        const res = await fetch(`/api/trading/revise_cancel?order_id=${id}&type=cancel`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
            alert('주문이 취소되었습니다.');
            loadOrders(); // 리스트 갱신
            refreshAccountInfo(); // 잔고 갱신 (예수금 반환 등)
            loadPortfolio(); // 경우에 따라 포트폴리오 영향
        } else {
            alert('취소 실패: ' + data.message);
        }
    } catch (e) {
        alert('통신 오류');
    }
}

// === OPEN ORDERS ===
async function loadOrders() {
    // 탭 UI 처리
    document.querySelectorAll('.panel-tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.panel-tab')[1].classList.add('active'); // 2번째 탭 (미체결)

    const thead = document.querySelector('.pro-table thead tr');
    if (thead) {
        thead.innerHTML = '<th>주문번호</th><th>종목명</th><th>구분</th><th>주문수량</th><th>주문가격</th><th>관리</th>';
    }

    const tbody = document.getElementById('portfolioTableBody'); // 재사용
    tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px;">로딩 중...</td></tr>';

    try {
        const res = await fetch('/api/trading/orders');
        let orders = [];
        if (res.ok) {
            orders = await res.json();
        }

        if (!orders || orders.length === 0) {
            // 프리뷰용 더미 데이터 주입
            orders = [
                { order_id: "1001", stock_name: "삼성전자", stock_code: "005930", type: "BUY", quantity: 10, price: 70000 },
                { order_id: "1002", stock_name: "SK하이닉스", stock_code: "000660", type: "SELL", quantity: 5, price: 120000 }
            ];
        }

        tbody.innerHTML = orders.map(o => `
            <tr>
                <td style="font-family:var(--font-mono); color:#848e9c;">${o.order_id}</td>
                <td style="font-weight:700;">${o.stock_name}<br><span style="font-size:10px; font-weight:400; color:#5e6673;">${o.stock_code}</span></td>
                <td style="color:${o.type === 'BUY' ? '#00e676' : '#ff3b69'};">${o.type === 'BUY' ? '매수' : '매도'}</td>
                <td style="font-family:var(--font-mono);">${o.quantity.toLocaleString()}주</td>
                <td style="font-family:var(--font-mono);">${o.price.toLocaleString()}원</td>
                <td>
                    <button onclick="reviseOrder('${o.order_id}', ${o.quantity}, ${o.price})" style="background:#2b3139; color:#eaecef; border:1px solid #434c56; padding:4px 8px; border-radius:2px; font-size:11px; cursor:pointer; margin-right:4px;">정정</button>
                    <button onclick="cancelOrder('${o.order_id}')" style="background:#2b3139; color:#ff3b69; border:1px solid #434c56; padding:4px 8px; border-radius:2px; font-size:11px; cursor:pointer;">취소</button>
                </td>
            </tr>
        `).join('');

    } catch (e) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; padding:20px; color:#ff3b69;">불러오기 실패</td></tr>';
    }
}

async function reviseOrder(id, oldQty, oldPrice) {
    const newPrice = prompt('정정할 가격을 입력하세요:', oldPrice);
    if (!newPrice) return;
    const newQty = prompt('정정할 수량을 입력하세요:', oldQty);
    if (!newQty) return;

    try {
        const res = await fetch(`/api/trading/revise_cancel?order_id=${id}&type=revise&price=${newPrice}&quantity=${newQty}`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
            alert('주문이 정정되었습니다.');
            loadOrders();
        } else {
            alert('정정 실패: ' + data.message);
        }
    } catch (e) {
        alert('통신 오류');
    }
}

async function cancelOrder(id) {
    if (!confirm(`주문번호 ${id}를 취소하시겠습니까?`)) return;

    try {
        const res = await fetch(`/api/trading/revise_cancel?order_id=${id}&type=cancel`, { method: 'POST' });
        const data = await res.json();
        if (data.status === 'ok') {
            alert('주문이 취소되었습니다.');
            loadOrders();
        } else {
            alert('취소 실패: ' + data.message);
        }
    } catch (e) {
        alert('통신 오류');
    }
}
