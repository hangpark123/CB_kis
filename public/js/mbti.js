// MBTI Stock Recommendation - Client Logic

// Form submission handler
async function handleSubmit(event) {
    event.preventDefault();

    const mbtiInput = document.getElementById('mbtiInput');
    const mbti = mbtiInput.value.trim().toUpperCase();

    // Validate MBTI format
    if (!/^[EIST][NSF][TFP][JP]$/i.test(mbti)) {
        showError('올바른 MBTI를 입력해주세요 (예: ENTJ, INFP)');
        return;
    }

    await fetchRecommendations(mbti);
}

// Fetch recommendations from API
async function fetchRecommendations(mbti) {
    const loadingEl = document.getElementById('loading');
    const errorEl = document.getElementById('error');
    const resultsEl = document.getElementById('results');
    const submitBtn = document.getElementById('submitBtn');

    // Show loading state
    loadingEl.style.display = 'block';
    errorEl.style.display = 'none';
    resultsEl.classList.remove('show');
    submitBtn.disabled = true;

    try {
        const response = await fetch(`/api/mbti/recommendations?mbti=${mbti}`);

        if (!response.ok) {
            throw new Error('API 요청 실패');
        }

        const data = await response.json();
        displayResults(data);

    } catch (error) {
        console.error('Error:', error);
        showError('추천을 불러오는 중 오류가 발생했습니다. 다시 시도해주세요.');
    } finally {
        loadingEl.style.display = 'none';
        submitBtn.disabled = false;
    }
}

// Display recommendation results
function displayResults(data) {
    const resultsEl = document.getElementById('results');
    const mbtiTypeEl = document.getElementById('mbtiType');
    const mbtiDescEl = document.getElementById('mbtiDescription');
    const mbtiStrategyEl = document.getElementById('mbtiStrategy');
    const stockGridEl = document.getElementById('stockGrid');

    // Set MBTI info
    mbtiTypeEl.textContent = data.mbti;
    mbtiDescEl.textContent = data.description;
    mbtiStrategyEl.textContent = data.strategy;

    // Clear previous stock cards
    stockGridEl.innerHTML = '';

    // Create stock cards
    if (data.stocks && data.stocks.length > 0) {
        data.stocks.forEach(stock => {
            const card = createStockCard(stock);
            stockGridEl.appendChild(card);
        });
    }

    // Show results with animation
    setTimeout(() => {
        resultsEl.classList.add('show');
        // Scroll to results
        resultsEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
}

// Create stock card element
function createStockCard(stock) {
    const card = document.createElement('div');
    card.className = 'stock-card';

    card.innerHTML = `
    <div class="stock-header">
      <div>
        <div class="stock-name">${stock.name}</div>
        <div class="stock-code">${stock.code}</div>
      </div>
    </div>
    <div class="stock-reason">${stock.reason}</div>
  `;

    // Add click handler to open modal
    card.addEventListener('click', () => {
        openStockModal(stock.code, stock.name);
    });

    return card;
}

// Show error message
function showError(message) {
    const errorEl = document.getElementById('error');
    errorEl.textContent = message;
    errorEl.style.display = 'block';

    // Auto-hide after 5 seconds
    setTimeout(() => {
        errorEl.style.display = 'none';
    }, 5000);
}

// Auto-uppercase MBTI input
document.addEventListener('DOMContentLoaded', () => {
    const mbtiInput = document.getElementById('mbtiInput');

    mbtiInput.addEventListener('input', (e) => {
        e.target.value = e.target.value.toUpperCase();
    });

    // Focus on input
    mbtiInput.focus();
});
