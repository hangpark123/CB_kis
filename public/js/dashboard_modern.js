// Dashboard Modern - Toss Style

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.style.display = 'none';
    });
    document.getElementById(`${tabName}Tab`).style.display = 'block';
}

// Refresh ranking
async function refreshRanking() {
    await loadRankingData();
}

// Load ranking data
async function loadRankingData() {
    const rankingList = document.getElementById('rankingList');

    // Show loading
    rankingList.innerHTML = `
    <div class="empty-state">
      <div class="empty-icon">⏳</div>
      <h3 class="empty-title">데이터를 불러오는 중...</h3>
    </div>
  `;

    try {
        const response = await fetch('/api/scanner/top_today');

        if (!response.ok) {
            throw new Error('Failed to fetch ranking data');
        }

        const data = await response.json();

        if (!data || data.length === 0) {
            rankingList.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📊</div>
          <h3 class="empty-title">데이터가 없습니다</h3>
          <p class="empty-description">나중에 다시 시도해주세요</p>
        </div>
      `;
            return;
        }

        // Create stock items
        rankingList.innerHTML = '';
        data.forEach((stock, index) => {
            const item = createStockItem(stock, index + 1);
            rankingList.appendChild(item);
        });

        // Update stats
        updateStats(data);

    } catch (error) {
        console.error('Error loading ranking:', error);
        rankingList.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">⚠️</div>
        <h3 class="empty-title">오류가 발생했습니다</h3>
        <p class="empty-description">새로고침 버튼을 눌러 다시 시도해주세요</p>
      </div>
    `;
    }
}

// Create stock list item
function createStockItem(stock, rank) {
    const item = document.createElement('div');
    item.className = 'stock-item';

    // Calculate change
    const changeRate = stock.score ? ((stock.score - 50) / 50 * 100).toFixed(2) : '0.00';
    const isPositive = parseFloat(changeRate) >= 0;

    item.innerHTML = `
    <div class="stock-info">
      <div class="stock-icon">#${rank}</div>
      <div class="stock-details">
        <div class="stock-name">${stock.corp_name_kr || stock.stock_code}</div>
        <div class="stock-code">${stock.stock_code}</div>
      </div>
    </div>
    <div class="stock-price-section">
      <div class="stock-price">Score: ${stock.score || '--'}</div>
      <div class="stock-change ${isPositive ? 'up' : 'down'}">
        ${isPositive ? '+' : ''}${changeRate}%
      </div>
    </div>
  `;

    // Add click handler
    item.addEventListener('click', () => {
        openStockModal(stock.stock_code, stock.corp_name_kr);
    });

    return item;
}

// Update dashboard stats
function updateStats(data) {
    if (data && data.length > 0) {
        const topScore = Math.max(...data.map(s => s.score || 0));
        document.getElementById('topScore').textContent = topScore.toFixed(1);
        document.getElementById('topChange').innerHTML = `<span>최고점</span>`;
    }

    // Fetch other stats
    fetchDartCount();
    fetchNewsCount();
    updateActiveCount();
}

// Fetch DART count
async function fetchDartCount() {
    try {
        const response = await fetch('/api/analytics/summary');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('dartCount').textContent = data.dart_count || '0';
        }
    } catch (error) {
        console.error('Error fetching DART count:', error);
    }
}

// Fetch news count
async function fetchNewsCount() {
    try {
        const response = await fetch('/api/analytics/summary');
        if (response.ok) {
            const data = await response.json();
            document.getElementById('newsCount').textContent = data.news_count || '0';
        }
    } catch (error) {
        console.error('Error fetching news count:', error);
    }
}

// Update active count (placeholder)
function updateActiveCount() {
    const randomCount = Math.floor(Math.random() * 50) + 10;
    document.getElementById('activeCount').textContent = randomCount;
}

// Search functionality
function setupSearch() {
    const searchInput = document.getElementById('searchInput');

    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.trim();
        if (query.length >= 2) {
            performSearch(query);
        }
    });
}

async function performSearch(query) {
    // TODO: Implement search API call
    console.log('Searching for:', query);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    loadRankingData();
    setupSearch();

    // Refresh data every 5 minutes
    setInterval(loadRankingData, 5 * 60 * 1000);
});
