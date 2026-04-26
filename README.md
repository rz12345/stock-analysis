# Stock Analysis

對台股與美股 ETF/個股進行多策略回測，定期執行後同步至 Firebase，並透過 Telegram 發送通知。

## 功能特色

- 4 種回測策略：除息買入、MACD+RSI、120MA 回檔、月定期定額
- 台股（FinMind）/ 美股（Tiingo）雙市場
- Firebase Realtime Database 雲端同步（含失敗重試）
- Telegram 通知（執行結果 / 錯誤告警）
- 互動式 HTML 彙總報表（4 策略 × 2 市場 × 跨策略比較）

---

## 快速開始

### 1. 安裝依賴

```bash
pip install -r requirements.txt
```

### 2. 設定 API 金鑰（不進版控）

於 `app/configs/` 放置三個 JSON 檔：

| 檔案 | 用途 |
|---|---|
| `tiingo.json` | 美股資料 API |
| `firebase-cred.json` | Firebase 服務帳號 |
| `telegram_notify.json` | Telegram Bot Token / Chat ID |

### 3. 設定追蹤標的

編輯專案根目錄的 `stocks.json`（已預設 13 支台股、11 支美股）。

### 4. 執行

| 入口腳本 | 用途 | 建議排程 |
|---|---|---|
| `python tw_update.py` | 台股回測 + Firebase 同步 | 每日 14:00 |
| `python us_update.py` | 美股回測 + Firebase 同步 | 每日 06:00 |
| `python tw_notify.py` | 台股近期交易 Telegram 通知 | 視需求 |
| `python us_notify.py` | 美股近期交易 Telegram 通知 | 視需求 |
| `python summary_table.py` | 產生 `output/summary_report.html` | 視需求 |

---

## 目錄結構（簡版）

```
stock-analysis/
├── app/
│   ├── configs/        # API 金鑰（不進版控）
│   ├── repositories/   # 核心商業邏輯（策略、資料、報表、同步）
│   ├── services/       # 外部服務（Firebase、Telegram、TWSE、Logger）
│   └── utils/          # 共用 utility（formatting）
├── data/               # 本地快取（CSV + SQLite，不進版控）
├── output/             # 產出（PNG 圖表、HTML 報表）
├── tests/              # pytest 單元測試（48 cases）
├── logs/               # 應用日誌
├── stocks.json         # 追蹤標的清單
├── pytest.ini          # pytest 設定
└── requirements.txt    # Python 相依套件
```

詳細架構與策略規則請見 [`CLAUDE.md`](./CLAUDE.md)。

---

## 測試

```bash
pytest
```

目前 48 tests / 48 passed，涵蓋策略訊號計算、股票分割偵測、格式化 utility。

---

## 文件導覽

| 檔案 | 用途 |
|---|---|
| [`CLAUDE.md`](./CLAUDE.md) | 專案完整規範：架構、回測策略、DB schema、開發規則 |
| [`Task.md`](./Task.md) | 已完成任務歷史（依日期分段） |
| [`Todo.md`](./Todo.md) | 待辦清單 |

---

## 開發規則摘要

- 函式 < 50 行，檔案 < 800 行
- 使用 `df.assign()` 回傳新物件，不直接 mutate DataFrame
- 完成任務從 `Todo.md` 移至 `Task.md`
- 新增策略只需改 `base_strategy.py` + 各 update 入口（詳見 `CLAUDE.md` §開發規則）
