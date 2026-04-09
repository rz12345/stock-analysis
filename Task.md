# 已完成任務

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
