import logging
import sqlite3
from datetime import date
from pathlib import Path

import pandas as pd
from app.repositories.base_report import USReport, TWReport
from app.services.app_logger import get_logger
from app.utils.formatting import format_float

logger = get_logger("summary_table", "summary_table.log", "summary_chat_id")

METHODS = ['bt_dividend', 'bt_signals', 'bt_ma_pullback', 'bt_monthly_dca']
METHOD_LABELS = {
    'bt_dividend': 'Dividend',
    'bt_signals': 'MACD Signals',
    'bt_ma_pullback': 'MA Pullback',
    'bt_monthly_dca': 'Monthly DCA',
}

TW_DB = Path('data/tw/db.sqlite')
US_DB = Path('data/us/db.sqlite')
OUTPUT_HTML = Path('output/summary_report.html')

_LOAD_QUERY = """
    SELECT bs.stock_id, bs.method, bs.close, bs.position_value,
           bs.broker_dividend, bs.asset_value, bs.roi, bs.irr
    FROM bt_summaries bs
    INNER JOIN (
        SELECT stock_id, method, MAX(date) AS latest_date
        FROM bt_summaries GROUP BY stock_id, method
    ) latest ON bs.stock_id = latest.stock_id
           AND bs.method = latest.method
           AND bs.date = latest.latest_date
"""


def load_summaries(db_path: Path, market_label: str) -> pd.DataFrame:
    with sqlite3.connect(db_path) as conn:
        df = pd.read_sql_query(_LOAD_QUERY, conn)
    return df.assign(market=market_label)


def _roi_cell(roi_raw: float) -> str:
    pct = round(roi_raw * 100, 2)
    css = 'pos' if pct >= 0 else 'neg'
    return f'<td class="{css}">{pct:.2f}%</td>'


def _irr_cell(irr_raw: float, best: bool = False) -> str:
    pct = round(irr_raw * 100, 2)
    css = 'pos best' if (pct >= 0 and best) else ('pos' if pct >= 0 else ('neg best' if best else 'neg'))
    return f'<td class="{css}">{pct:.2f}%</td>'


def build_strategy_table(df: pd.DataFrame, method: str) -> str:
    method_df = df[df['method'] == method].sort_values('roi', ascending=False)
    active = 'active' if method == METHODS[0] else ''

    if method_df.empty:
        return f'<div class="strat-table {active}" data-method="{method}"><p>No data</p></div>'

    rows_html = []
    for _, row in method_df.iterrows():
        rows_html.append(f'''        <tr data-market="{row['market']}">
          <td>{row['stock_id']}</td>
          <td>{row['market']}</td>
          <td>{format_float(row['close'])}</td>
          <td>{format_float(row['position_value'])}</td>
          <td>{format_float(row['broker_dividend'])}</td>
          <td>{format_float(row['asset_value'])}</td>
          {_roi_cell(row['roi'])}
          {_irr_cell(row['irr'])}
        </tr>''')

    return f'''    <div class="strat-table {active}" data-method="{method}">
      <table>
        <thead>
          <tr>
            <th>Stock</th><th>Market</th><th>Close</th>
            <th>Position Value</th><th>Dividend</th><th>Asset Value</th>
            <th>ROI%</th><th>IRR%</th>
          </tr>
        </thead>
        <tbody>
{''.join(rows_html)}
        </tbody>
      </table>
    </div>'''


def build_cross_strategy_table(df: pd.DataFrame) -> str:
    stocks = (
        df[['stock_id', 'market']]
        .drop_duplicates()
        .sort_values(['market', 'stock_id'])
    )

    method_headers = ''.join(
        f'<th colspan="2">{METHOD_LABELS[m]}</th>' for m in METHODS
    )
    sub_headers = ''.join('<th>ROI%</th><th>IRR%</th>' for _ in METHODS)

    rows_html = []
    for _, stock_row in stocks.iterrows():
        sid = stock_row['stock_id']
        mkt = stock_row['market']
        stock_data = df[(df['stock_id'] == sid) & (df['market'] == mkt)]

        best_method = max(
            (m for m in METHODS if not stock_data[stock_data['method'] == m].empty),
            key=lambda m: stock_data[stock_data['method'] == m].iloc[0]['irr'],
            default=None,
        )

        cells = []
        for m in METHODS:
            m_row = stock_data[stock_data['method'] == m]
            if m_row.empty:
                cells.append('<td>—</td><td>—</td>')
            else:
                r = m_row.iloc[0]
                cells.append(_roi_cell(r['roi']) + _irr_cell(r['irr'], best=(m == best_method)))

        rows_html.append(f'''        <tr>
          <td>{sid}</td><td>{mkt}</td>
          {''.join(cells)}
        </tr>''')

    return f'''    <table>
      <thead>
        <tr>
          <th rowspan="2">Stock</th><th rowspan="2">Market</th>
          {method_headers}
        </tr>
        <tr>{sub_headers}</tr>
      </thead>
      <tbody>
{''.join(rows_html)}
      </tbody>
    </table>'''


def generate_html_report(tw_df: pd.DataFrame, us_df: pd.DataFrame) -> None:
    df = pd.concat([tw_df, us_df], ignore_index=True)

    strat_tab_buttons = ''.join(
        f'<button class="tab-btn{" active" if m == METHODS[0] else ""}" data-method="{m}">'
        f'{METHOD_LABELS[m]}</button>'
        for m in METHODS
    )
    strat_tables = '\n'.join(build_strategy_table(df, m) for m in METHODS)
    cross_table = build_cross_strategy_table(df)

    generated = date.today().isoformat()
    html = f'''<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Stock Analysis Summary</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2937; }}
    h1 {{ color: #111827; margin-bottom: 4px; }}
    p.generated {{ color: #6b7280; font-size: 0.85em; margin-bottom: 20px; }}
    .main-tabs {{ display: flex; gap: 8px; margin-bottom: 20px; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }}
    .main-tab {{ padding: 8px 20px; border: 1px solid #d1d5db; background: white; cursor: pointer; border-radius: 4px; font-size: 1em; }}
    .main-tab.active {{ background: #1d4ed8; color: white; border-color: #1d4ed8; }}
    .view {{ display: none; }}
    .view.active {{ display: block; }}
    .controls {{ display: flex; gap: 16px; align-items: center; margin-bottom: 12px; flex-wrap: wrap; }}
    .strat-tabs, .mkt-filter {{ display: flex; gap: 6px; }}
    .tab-btn {{ padding: 6px 14px; border: 1px solid #d1d5db; background: white; cursor: pointer; border-radius: 4px; }}
    .tab-btn.active {{ background: #374151; color: white; border-color: #374151; }}
    .strat-table {{ display: none; }}
    .strat-table.active {{ display: block; }}
    table {{ border-collapse: collapse; width: 100%; margin-top: 4px; }}
    th {{ background: #374151; color: white; padding: 8px 14px; text-align: left; white-space: nowrap; }}
    td {{ padding: 7px 14px; border-bottom: 1px solid #e5e7eb; white-space: nowrap; }}
    tr:hover td {{ background: #f3f4f6; }}
    .pos {{ color: #16a34a; font-weight: 600; }}
    .neg {{ color: #dc2626; font-weight: 600; }}
    .best {{ background: #fef9c3 !important; }}
  </style>
</head>
<body>
  <h1>Stock Analysis Summary</h1>
  <p class="generated">Generated: {generated}</p>

  <div class="main-tabs">
    <button class="main-tab active" data-view="by-strategy">By Strategy</button>
    <button class="main-tab" data-view="cross-strategy">Cross Strategy</button>
  </div>

  <div id="by-strategy" class="view active">
    <div class="controls">
      <div class="strat-tabs">
        {strat_tab_buttons}
      </div>
      <div class="mkt-filter">
        <button class="tab-btn active" data-market="all">All</button>
        <button class="tab-btn" data-market="TW">TW</button>
        <button class="tab-btn" data-market="US">US</button>
      </div>
    </div>
{strat_tables}
  </div>

  <div id="cross-strategy" class="view">
    <p style="color:#6b7280;font-size:0.85em">IRR 最高策略欄位以黃色標示。</p>
{cross_table}
  </div>

  <script>
    // Main view tabs
    document.querySelectorAll('.main-tab').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.main-tab').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.view').forEach(v => v.classList.remove('active'));
        btn.classList.add('active');
        document.getElementById(btn.dataset.view).classList.add('active');
      }});
    }});

    // Strategy tabs
    document.querySelectorAll('.strat-tabs .tab-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.strat-tabs .tab-btn').forEach(b => b.classList.remove('active'));
        document.querySelectorAll('.strat-table').forEach(t => t.classList.remove('active'));
        btn.classList.add('active');
        document.querySelector('.strat-table[data-method="' + btn.dataset.method + '"]').classList.add('active');
      }});
    }});

    // Market filter
    let currentMarket = 'all';
    document.querySelectorAll('.mkt-filter .tab-btn').forEach(btn => {{
      btn.addEventListener('click', () => {{
        document.querySelectorAll('.mkt-filter .tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentMarket = btn.dataset.market;
        filterRows();
      }});
    }});

    function filterRows() {{
      document.querySelectorAll('.strat-table tr[data-market]').forEach(row => {{
        row.style.display = (currentMarket === 'all' || row.dataset.market === currentMarket) ? '' : 'none';
      }});
    }}
  </script>
</body>
</html>'''

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_HTML.write_text(html, encoding='utf-8')
    logger.info("HTML 報表已產出：%s", OUTPUT_HTML)


if __name__ == "__main__":
    try:
        tw_report = TWReport()
        us_report = USReport()

        us_report.run()
        tw_report.run()

        tw_df = load_summaries(TW_DB, 'TW')
        us_df = load_summaries(US_DB, 'US')
        generate_html_report(tw_df, us_df)

        logger.info("summary_table 完成")
    except Exception:
        logger.exception("summary_table 執行失敗")
        raise SystemExit(1)
    finally:
        logging.shutdown()
