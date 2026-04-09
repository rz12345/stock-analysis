# 已完成任務

## 2026-04-09（本 session — Firebase 重試 & 追蹤標的設定檔）

- [x] **Firebase 同步失敗重試機制**
  - `app/repositories/web_data_sync.py`：新增 `_sync_with_retry()` helper（3 次重試、指數退避 2/4/8 秒），取代原本裸露的 `DB.updateNodeByDict` 呼叫

- [x] **追蹤標的管理**
  - 新增 `stocks.json`（專案根目錄）：集中管理台股 13 支、美股 11 支清單
  - `tw_update.py`：改從 `stocks.json` 讀取 `tw` 清單，移除 hardcode
  - `us_update.py`：改從 `stocks.json` 讀取 `us` 清單，移除 hardcode

---

## 2026-04-09（本 session — 單元測試）

- [x] **補充單元測試**（pytest），48 tests / 48 passed
  - `tests/test_base_strategy.py`：
    - `calculate_monthly_dca()` — 每月第一個交易日訊號正確性（5 cases）
    - `calculate_ma_pullback()` — 資料不足、永不跌破均線、回檔穿越、多次穿越、自訂 window（6 cases）
    - `calculate_macd_and_rsi()` — 欄位存在、RSI 範圍、RSI_signal、MACD crossover、MACD 已正無訊號、下跌使 RSI < 50（6 cases）
    - `calculate_annualized_return()` — 零成長、翻倍 1 年/2 年、初始值為零（4 cases）
    - `calculate_asset_value_and_ratio()` — 基本計算、零投資、虧損（3 cases）
  - `tests/test_base_trade_record.py`：
    - `_detect_split()` — 正常波動、減半、翻倍、閾值邊界、自訂欄位、未排序日期（10 cases）
  - `tests/test_formatting.py`：
    - `format_float()` 與 `format_pct()` 各情境（14 cases）
  - 新增 `pytest.ini`

---

## 2026-04-09（本 session）

- [x] **重新設計 `summary_table.py`：PNG → 互動式 HTML 報表**
  - `app/utils/__init__.py`：新增（空檔，使 utils 成為 package）
  - `app/utils/formatting.py`：新增 `format_float()` + `format_pct()` 共用 utility，整合原先散落三處的重複定義
  - `app/repositories/base_report.py`：移除本地 `format_float()`，改 import；`applymap()` → `.map()`（pandas deprecation 修正）
  - `app/repositories/web_data_sync.py`：移除本地 `format_float()`，改 import；修正 `__class__.format_float` 殘留參照；`applymap()` → `.map()`
  - `summary_table.py`：全面重寫，產出 `output/summary_report.html`，含：
    - 4 個策略 tab（Dividend / MACD Signals / MA Pullback / Monthly DCA），補齊原本缺少的 `bt_ma_pullback`
    - TW / US / All 市場篩選
    - 跨策略比較分頁（每股票並列 4 策略 ROI% & IRR%，IRR 最高者黃色標示）
    - ROI 正值綠色、負值紅色
    - 修正舊版 `tw_report = TWReport()` 覆蓋類別名稱的 bug

---

## 2026-04-05（本 session）

- [x] **新增 `bt_monthly_dca` 每月定期定額策略**
  - `app/repositories/base_strategy.py`：新增 `calculate_monthly_dca()` 方法與 `bt_strategy()` elif 分支
  - `tw_update.py`：新增 `bt_monthly_dca` 呼叫
  - `us_update.py`：新增 `bt_monthly_dca` 呼叫
  - `summary_table.py`：`methods` 與 `output_files` 新增對應項目

- [x] **建立 `.claude/CLAUDE.md`**：專案概述、架構、策略說明、DB schema、開發規則

- [x] **建立 `.claude/Task.md`**：已完成任務清單

- [x] **建立 `.claude/Todo.md`**：待辦任務清單

---

## 2026-04-05（git commits）

- [x] `feat: 初始版本`（commit `73b9e7e`）
  - 台股/美股歷史股價爬蟲（FinMind / Tiingo）
  - 股票分割自動偵測與前複權調整
  - 三種回測策略：`bt_dividend`、`bt_signals`、`bt_ma_pullback`（120 日均線回檔）
  - Telegram 通知（取代 LINE Notify / Discord）
  - Windows 工作排程：台股 14:00、美股 06:00
  - 報表產生：個股折線圖 + 彙總表（PNG）
  - Firebase Realtime Database 同步

- [x] `chore: 移除 ETF成分.ipynb`（commit `8863a3e`）
  - 清除探索性 Jupyter Notebook
