
// === AI ANALYSIS ===
async function loadAIAnalysis(code) {
    const container = document.getElementById('aiContent');
    if (!container) return;
    container.innerHTML = 'Analyzing...';

    try {
        const res = await fetch(`/api/trading/analyze?stock_code=${code}`, { method: 'POST' });
        const data = await res.json();

        if (data.error) {
            container.innerHTML = `<span style="color:#ff3b69;">${data.error}</span>`;
            return;
        }

        let color = '#787b86';
        if (data.opinion === '긍정적') color = '#00e676';
        if (data.opinion === '부정적') color = '#ff3b69';

        container.innerHTML = `
            <div style="margin-bottom:8px;">
                <span style="color:${color}; font-weight:700;">${data.opinion}</span>
                <span style="float:right; color:#00e676; font-weight:700;">${data.confidence}% Confidence</span>
            </div>
            <div style="font-size:12px; color:#d1d4dc;">
                ${data.reason.map(r => `• ${r}`).join('<br>')}
            </div>
        `;
    } catch (e) {
        container.innerHTML = 'Analysis unavailable';
    }
}
