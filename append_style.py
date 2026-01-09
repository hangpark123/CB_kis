
import os

css_path = r"c:\Project\CB_kis\public\css\tradingview_style.css"
new_css = """
/* === DASHBOARD STYLE (index.html) === */
.dashboard-layout { display: grid; grid-template-areas: "header" "ticker" "hero" "main"; grid-template-rows: 50px 40px 100px 1fr; height: 100vh; background-color: var(--bg-dark); overflow-y: auto; }
.news-ticker-wrap { grid-area: ticker; background: #1e222d; border-bottom: 1px solid var(--border-color); line-height: 40px; position: relative; overflow: hidden; }
.news-label { position: absolute; left: 0; top: 0; background: var(--accent-blue); color: white; padding: 0 16px; height: 100%; font-weight: 700; font-size: 13px; z-index: 10; }
.hero-stats { grid-area: hero; display: flex; gap: 16px; padding: 16px; justify-content: center; }
.stat-card { flex: 1; max-width: 240px; background: var(--bg-panel-trans); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px 16px; display: flex; flex-direction: column; justify-content: center; backdrop-filter: blur(10px); }
.stat-label { font-size: 12px; color: var(--text-secondary); margin-bottom: 4px; }
.stat-value { font-size: 20px; font-weight: 700; color: var(--text-primary); font-family: var(--font-mono); }
.stat-value.up { color: var(--up-color); } .stat-value.down { color: var(--down-color); }
.dashboard-grid { grid-area: main; display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px; padding: 0 16px 32px 16px; max-width: 1400px; margin: 0 auto; width: 100%; }
.dashboard-col { background: var(--bg-panel-trans); border: 1px solid var(--border-color); border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; max-height: 600px; }
.col-header { padding: 12px 16px; border-bottom: 1px solid var(--border-color); background: rgba(255,255,255,0.02); display: flex; justify-content: space-between; align-items: center; }
.col-header h2 { font-size: 15px; font-weight: 700; color: var(--text-primary); display: flex; align-items: center; gap: 8px; }
.refresh-btn { background: none; border: none; color: var(--text-secondary); cursor: pointer; font-size: 14px; transition: color 0.2s; }
.refresh-btn:hover { color: var(--accent-blue); }
.rank-list { flex: 1; overflow-y: auto; padding: 4px 0; }
.rank-item { display: flex; justify-content: space-between; align-items: center; padding: 8px 16px; border-bottom: 1px solid rgba(255,255,255,0.03); cursor: pointer; transition: background 0.2s; }
.rank-item:hover { background: rgba(255,255,255,0.05); }
.rank-idx { width: 24px; font-size: 12px; color: var(--text-secondary); font-weight: 700; }
.rank-info { flex: 1; }
.rank-name { font-weight: 600; margin-bottom: 2px; display: flex; align-items: center; gap: 6px; }
.rank-code { font-size: 11px; color: var(--text-secondary); }
.rank-price-area { text-align: right; }
.rank-price { font-family: var(--font-mono); font-weight: 600; font-size: 13px; }
.rank-rate { font-family: var(--font-mono); font-size: 11px; }
.comment-badge { font-size: 10px; padding: 2px 6px; border-radius: 4px; font-weight: 700; margin-left: 6px; display: inline-block; }
.badge-yellow { background: rgba(255, 215, 0, 0.15); color: #ffd700; border: 1px solid rgba(255, 215, 0, 0.3); }
.badge-blue { background: rgba(41, 98, 255, 0.15); color: #448aff; border: 1px solid rgba(41, 98, 255, 0.3); }
.rank-list::-webkit-scrollbar { width: 6px; }
.rank-list::-webkit-scrollbar-thumb { background: #2a2e39; border-radius: 3px; }
"""

try:
    with open(css_path, "a", encoding="utf-8") as f:
        f.write(new_css)
    print("CSS appended.")
except Exception as e:
    print(f"Error: {e}")
