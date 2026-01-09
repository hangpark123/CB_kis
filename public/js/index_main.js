// =======================================
// MARKET EXPLORER - MAIN JAVASCRIPT
// =======================================

let currentMarket = 'KR';

// === INITIALIZATION ===
document.addEventListener('DOMContentLoaded', () => {
    loadQuickStats();
    loadRankings();
    loadAIRecommendations();
    loadNews();
    setupSearch();

    // Auto-refresh (15초)
    setInterval(loadQuickStats, 15000);
    setInterval(loadRankings, 15000);
});

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

    document.addEventListener('click', (e) => {
        if (!e.target.closest('.toolbar-center')) {
            results.style.display = 'none';
        }
    });
}

async function searchStocks(query) {
    try {
        const res = await fetch(`/api/trading/search?query=${encodeURIComponent(query)}&market=${currentMarket}`);
        const stocks = await res.json();

        const results = document.getElementById('searchResults');

        if (!stocks || stocks.length === 0) {
            results.style.display = 'none';
            return;
        }

        results.innerHTML = stocks.map(stock => `
            <div class="search-result-item" onclick="goToTrading('${stock.stock_code}', '${stock.stock_name.replace(/'/g, "\\'")}', '${stock.exchange}')">
                <div style="font-weight:700;">${stock.stock_name}</div>
                <div style="font-size:12px; color:#787b86;">${stock.stock_code} · ${stock.exchange}</div>
            </div>
        `).join('');

        results.style.display = 'block';
    } catch (e) {
        console.error('Search error:', e);
    }
}

function goToTrading(code, name, exchange) {
    // Trading Desk로 이동 (URL 파라미터로 종목 전달)
    location.href = `/trading_desk.html?code=${code}&name=${encodeURIComponent(name)}&exchange=${exchange}`;
}

// === MARKET TOGGLE ===
function toggleMarket() {
    currentMarket = currentMarket === 'KR' ? 'US' : 'KR';
    const btn = document.getElementById('marketSwitch');
    btn.textContent = currentMarket === 'KR' ? '🇰🇷 KR' : '🇺🇸 US';

    // US는 테마/랭킹 데이터가 없으므로 표시 안함
    if (currentMarket === 'US') {
        alert('US market rankings are not available yet');
        toggleMarket(); // 다시 KR로
    }
}

// === QUICK STATS ===
async function loadQuickStats() {
    try {
        const [rise, fall, volume] = await Promise.all([
            fetch('/api/trading/ranks?type=rise').then(r => r.json()),
            fetch('/api/trading/ranks?type=fall').then(r => r.json()),
            fetch('/api/trading/ranks?type=volume').then(r => r.json())
        ]);

        if (rise && rise[0]) {
            document.getElementById('topRise').innerHTML = `
                <div style="font-weight:800; font-size:16px;">${rise[0].name}</div>
                <div style="color:#00e676; font-size:14px;">+${(rise[0].rate || 0).toFixed(2)}%</div>
            `;
        } else {
            document.getElementById('topRise').textContent = '--';
        }

        if (fall && fall[0]) {
            document.getElementById('topFall').innerHTML = `
                <div style="font-weight:800; font-size:16px;">${fall[0].name}</div>
                <div style="color:#ff3b69; font-size:14px;">${(fall[0].rate || 0).toFixed(2)}%</div>
            `;
        } else {
            document.getElementById('topFall').textContent = '--';
        }

        if (volume && volume[0]) {
            document.getElementById('topVolume').innerHTML = `
                <div style="font-weight:800; font-size:16px;">${volume[0].name}</div>
                <div style="color:#787b86; font-size:12px;">${(volume[0].volume || 0).toLocaleString()}</div>
            `;
        } else {
            document.getElementById('topVolume').textContent = '--';
        }

        // AI Picks Count (Top Stats)
        const aiRes = await fetch('/api/ai/recommendations?limit=5');
        const ai = await aiRes.json();
        document.getElementById('aiPickCount').innerHTML = `
            <div style="font-weight:800; font-size:20px;">${ai.length}</div>
            <div style="color:#2962ff; font-size:12px;">Active Signals</div>
        `;
        // Header Count
        const aiCountElem = document.getElementById('aiCount');
        if (aiCountElem) aiCountElem.textContent = ai.length + ' Signals';

    } catch (e) {
        console.error('Quick stats error:', e);
    }
}

// === RANKINGS ===
async function loadRankings() {
    try {
        const [rise, volume, theme] = await Promise.all([
            fetch('/api/trading/ranks?type=rise').then(r => r.json()),
            fetch('/api/trading/ranks?type=volume').then(r => r.json()),
            fetch('/api/trading/ranks?type=theme').then(r => r.json())
        ]);

        // Helper to generate theme comment
        const getComment = (name, rate) => {
            if (latestNews.length > 0) {
                const related = latestNews.find(n => n.title.includes(name));
                if (related) {
                    let displayTitle = related.title.replace(/\[.*?\]/g, '').trim();
                    if (displayTitle.length > 20) displayTitle = displayTitle.substring(0, 20) + '..';
                    return displayTitle;
                }
            }

            if (name.includes('삼성') || name.includes('전자') || name.includes('SK')) return '반도체/AI';
            if (name.includes('에코') || name.includes('포스코') || name.includes('2차전지') || name.includes('엘앤에프')) return '2차전지';
            if (name.includes('현대') || name.includes('기아')) return '자동차/부품';
            if (name.includes('바이오') || name.includes('제약') || name.includes('HLB')) return '바이오/신약';
            if (name.includes('로봇') || name.includes('레인보우')) return '로봇/AI';
            if (name.includes('AI') || name.includes('솔트')) return '생성형 AI';
            if (name.includes('엔터') || name.includes('JYP') || name.includes('하이브')) return '엔터테인먼트';
            if (name.includes('금융') || name.includes('KB')) return '금융/밸류업';
            if (name.includes('전선') || name.includes('전력')) return '전력설비';
            if (name.includes('방산') || name.includes('에어로')) return '방위산업';

            if (rate >= 29.5) return '상한가';
            if (rate >= 15) return '급등주';
            if (rate <= -10) return '하락폭 확대';

            return '';
        };

        // 1. Rise Ranking
        const riseContainer = document.getElementById('riseRanking');
        riseContainer.innerHTML = (rise || []).slice(0, 15).map((stock, i) => {
            const comment = getComment(stock.name, stock.rate);
            const badgeHtml = comment ? `<span class="comment-badge badge-yellow">${comment}</span>` : '';

            return `
            <div class="rank-item" onclick="goToTrading('${stock.code}', '${stock.name}', 'KRX')">
                <div style="display:flex; align-items:center;">
                    <span class="rank-idx" style="color:#d1d4dc;">${i + 1}</span>
                    <div style="display:flex; flex-direction:column;">
                        <span class="rank-name">${stock.name} ${badgeHtml}</span>
                        <span class="rank-code">${stock.code}</span>
                    </div>
                </div>
                <div class="rank-price-area">
                    <div class="rank-price">${(stock.price || 0).toLocaleString()}</div>
                    <div class="rank-rate up">+${(stock.rate || 0).toFixed(2)}%</div>
                </div>
            </div>`;
        }).join('');

        // 2. Volume Ranking
        const volumeContainer = document.getElementById('volumeRanking');
        volumeContainer.innerHTML = (volume || []).slice(0, 15).map((stock, i) => {
            const comment = getComment(stock.name, stock.rate);
            const badgeHtml = comment ? `<span class="comment-badge badge-blue">${comment}</span>` : '';
            const rate = stock.rate || 0;
            const isUp = rate >= 0;

            return `
            <div class="rank-item" onclick="goToTrading('${stock.code}', '${stock.name}', 'KRX')">
                <div style="display:flex; align-items:center;">
                    <span class="rank-idx" style="color:#d1d4dc;">${i + 1}</span>
                    <div style="display:flex; flex-direction:column;">
                        <span class="rank-name">${stock.name} ${badgeHtml}</span>
                        <span class="rank-code">${stock.code}</span>
                    </div>
                </div>
                <div class="rank-price-area">
                    <div class="rank-price">${(stock.volume || 0).toLocaleString()}</div>
                    <div class="rank-rate ${isUp ? 'up' : 'down'}">${isUp ? '+' : ''}${rate.toFixed(2)}%</div>
                </div>
            </div>`;
        }).join('');

        // 3. Theme Ranking
        const themeContainer = document.getElementById('themeRanking');
        themeContainer.innerHTML = (theme || []).slice(0, 15).map((item, i) => {
            const rate = item.rate || 0;
            const isUp = rate >= 0;
            return `
            <div class="rank-item">
                <div style="display:flex; align-items:center;">
                    <span class="rank-idx" style="color:#d1d4dc;">${i + 1}</span>
                    <div style="display:flex; flex-direction:column;">
                        <span class="rank-name">${item.name}</span>
                        <span class="rank-code">${item.leading}</span>
                    </div>
                </div>
                <div class="rank-price-area">
                    <div class="rank-rate ${isUp ? 'up' : 'down'}" style="font-size:13px;">${isUp ? '+' : ''}${rate.toFixed(2)}%</div>
                </div>
            </div>`;
        }).join('');

    } catch (e) {
        console.error('Rankings error:', e);
    }
}

function refreshRanks() {
    loadQuickStats();
    loadRankings();
}

// === AI RECOMMENDATIONS ===
async function loadAIRecommendations() {
    try {
        const res = await fetch('/api/ai/recommendations?limit=6');
        const picks = await res.json();

        const container = document.getElementById('aiRecommendations');

        if (!picks || picks.length === 0) {
            container.innerHTML = '<div style="text-align:center; color:#787b86;">AI 추천 종목이 없습니다</div>';
            return;
        }

        container.innerHTML = picks.map(pick => `
            <div class="ai-pick-card" onclick="goToTrading('${pick.stock_code}', '${pick.stock_name}', 'KRX')">
                <div class="pick-header">
                    <div class="pick-name">${pick.stock_name}</div>
                    <div class="pick-confidence">${pick.confidence}%</div>
                </div>
                <div class="pick-code">${pick.stock_code}</div>
                <div class="pick-indicator">${pick.indicator}</div>
                <div class="pick-reasons">
                    ${(pick.reasons || []).slice(0, 2).map(r => `<div>• ${r}</div>`).join('')}
                </div>
                <div class="pick-expected">예상 수익: ${pick.expected_return}</div>
            </div>
        `).join('');
    } catch (e) {
        console.error('AI recommendations error:', e);
    }
}

function refreshAI() {
    loadAIRecommendations();
}

// Global News Data
let latestNews = [];

// === NEWS TICKER ===
async function loadNews() {
    try {
        const res = await fetch('/api/news/headlines');
        const news = await res.json();

        latestNews = news || []; // 뉴스 데이터 전역 저장

        const ticker = document.getElementById('newsTicker');

        if (!news || news.length === 0) {
            ticker.innerHTML = '<span class="news-item">No news available at the moment.</span>';
            return;
        }

        // 아이템 반복
        ticker.innerHTML = news.map(n =>
            `<a href="${n.link}" target="_blank" class="news-item">📰 ${n.title}</a>`
        ).join('');

        // 뉴스가 로드되면 랭킹도 갱신하여 코멘트 반영 (선택적)
        // loadRankings(); 

    } catch (e) {
        console.error('News load error:', e);
    }
}
