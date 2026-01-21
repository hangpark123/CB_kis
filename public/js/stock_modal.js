// Stock Detail Modal - Bottom Sheet

let currentStockCode = null;

// Open modal
async function openStockModal(stockCode, stockName = '') {
    currentStockCode = stockCode;

    const overlay = document.getElementById('stockModalOverlay');
    const modal = document.getElementById('stockModal');

    // Show overlay and modal
    overlay.classList.add('active');
    setTimeout(() => modal.classList.add('active'), 50);

    // Disable body scroll
    document.body.style.overflow = 'hidden';

    // Set initial info
    document.getElementById('modalStockName').textContent = stockName || stockCode;
    document.getElementById('modalStockCode').textContent = stockCode;

    // Show loading
    showModalLoading();

    // Fetch stock details
    await fetchStockDetail(stockCode);
}

// Close modal
function closeStockModal() {
    const overlay = document.getElementById('stockModalOverlay');
    const modal = document.getElementById('stockModal');

    modal.classList.remove('active');
    setTimeout(() => {
        overlay.classList.remove('active');
        document.body.style.overflow = '';
    }, 300);
}

// Fetch stock details from API
async function fetchStockDetail(stockCode) {
    try {
        const response = await fetch(`/api/stock/detail/${stockCode}`);

        if (!response.ok) {
            throw new Error('Failed to fetch stock details');
        }

        const data = await response.json();
        displayStockDetail(data);

    } catch (error) {
        console.error('Error fetching stock detail:', error);
        showModalError('정보를 불러오는 중 오류가 발생했습니다.');
    }
}

// Display stock details
function displayStockDetail(data) {
    hideModalLoading();

    // Update price info
    const priceEl = document.getElementById('modalCurrentPrice');
    const changeEl = document.getElementById('modalChange');

    if (data.current_price) {
        priceEl.textContent = formatPrice(data.current_price);

        if (data.change_rate !== undefined) {
            const changeRate = data.change_rate;
            const changeClass = changeRate >= 0 ? 'positive' : 'negative';
            const changeSign = changeRate >= 0 ? '+' : '';
            changeEl.textContent = `${changeSign}${changeRate.toFixed(2)}%`;
            changeEl.className = `modal-change ${changeClass}`;
        }
    }

    // Overview tab
    if (data.overview) {
        document.getElementById('modalMarketCap').textContent = data.market_cap || '-';
        document.getElementById('modalVolume').textContent = formatNumber(data.volume) || '-';
        document.getElementById('modalIndustry').textContent = data.overview.industry || '-';
        document.getElementById('modalCEO').textContent = data.overview.ceo || '-';
        document.getElementById('modalFounded').textContent = data.overview.founded || '-';
    }

    // Financials tab
    if (data.financials) {
        document.getElementById('modalRevenue').textContent = data.financials.revenue || '-';
        document.getElementById('modalOperatingProfit').textContent = data.financials.operating_profit || '-';
        document.getElementById('modalNetIncome').textContent = data.financials.net_income || '-';
    }
}

// Tab switching
function switchModalTab(tabName) {
    // Update tabs
    document.querySelectorAll('.modal-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.modal-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`${tabName}Tab`).classList.add('active');
}

// Loading state
function showModalLoading() {
    document.getElementById('modalLoading').style.display = 'block';
    document.querySelectorAll('.modal-tab-content').forEach(el => el.style.display = 'none');
}

function hideModalLoading() {
    document.getElementById('modalLoading').style.display = 'none';
    document.querySelectorAll('.modal-tab-content').forEach(el => el.style.display = 'block');
    // Show first tab
    switchModalTab('overview');
}

function showModalError(message) {
    hideModalLoading();
    // Could implement error UI here
    alert(message);
}

// Utility functions
function formatPrice(price) {
    return new Intl.NumberFormat('ko-KR').format(price) + '원';
}

function formatNumber(num) {
    if (!num) return '-';
    return new Intl.NumberFormat('ko-KR').format(num);
}

// Event listeners
document.addEventListener('DOMContentLoaded', () => {
    // Close on overlay click
    document.getElementById('stockModalOverlay')?.addEventListener('click', (e) => {
        if (e.target === e.currentTarget) {
            closeStockModal();
        }
    });

    // Close on escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && document.getElementById('stockModal')?.classList.contains('active')) {
            closeStockModal();
        }
    });
});
