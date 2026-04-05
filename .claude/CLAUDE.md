# Stock Analysis — 專案概述與架構

## 專案目的

對台股與美股 ETF/個股進行多策略回測，定期執行後將結果同步至 Firebase，並透過 Telegram 發送通知。

## 技術堆疊

- **語言**：Python 3
- **資料來源**：FinMind API（台股）、Tiingo API（美股）
- **本地快取**：CSV 檔 + SQLite
- **雲端同步**：Firebase Realtime Database
- **通知**：Telegram Bot
- **排程**：Windows 工作排程器（台股 14:00、美股 06:00）

---

## 目錄結構

```
stock-analysis/
├── app/
│   ├── configs/              # API 金鑰與憑證（不進版控）
│   │   ├── tiingo.json
│   │   ├── firebase-cred.json
│   │   └── telegram_notify.json
│   ├── repositories/         # 核心商業邏輯
│   │   ├── base_strategy.py      # 策略引擎（BaseStrategy / TwStrategy / UsStrategy）
│   │   ├── base_trade_record.py  # 資料擷取與快取（TaiwanTradeRecord / USTradeRecord）
│   │   ├── base_report.py        # 報表產生（TWReport / USReport）
│   │   ├── tw_dividend_record.py # 台股股息資料（DividendRecord）
│   │   ├── web_data_sync.py      # Firebase 同步（TWWebData / USWebData）
│   │   ├── recent_transcation.py # 近期交易通知
│   │   ├── listed_company.py     # 上市公司清單
│   │   └── bt_plot.py            # 回測圖表輔助
│   └── services/             # 外部服務整合
│       ├── firebase.py
│       ├── telegram_notify.py
│       ├── line_notify.py        # 保留但未使用
│       └── twse.py
├── data/
│   ├── tw/                   # 台股快取（CSV + db.sqlite）
│   └── us/                   # 美股快取（CSV + db.sqlite）
├── output/                   # 產出圖表（PNG）
├── tw_update.py              # 台股回測入口
├── us_update.py              # 美股回測入口
├── tw_notify.py              # 台股通知入口
├── us_notify.py              # 美股通知入口
└── summary_table.py          # 彙總報表產生入口
```

---

## 回測策略

所有策略繼承 `BaseStrategy`，透過 `bt_strategy(df, method_name)` 執行。

| method_name | 策略說明 |
|---|---|
| `bt_dividend` | 每次除息後買入 |
| `bt_signals` | MACD 負轉正 且 RSI ≤ 50 |
| `bt_ma_pullback` | 收盤價跌破 120MA 後反彈穿回時買入 |
| `bt_monthly_dca` | 每月第一個交易日買入（定期定額） |

### 資金分配

- **回測起始日**：2020-01-01（台股與美股皆同）
- **台股**：每年 NT$100,000，平均分配至當年所有買入訊號
- **美股**：每年 USD$3,500，平均分配至當年所有買入訊號
- `bt_monthly_dca` 每年約 12 次，台股每月約 NT$8,333，美股約 USD$292

### 持倉計算

- 平均成本法（加權平均）
- 股息累積至 `broker_dividend`
- 資產價值 = 持股市值 + 累積股息
- 回傳指標：ROI、IRR（年化報酬率）

---

## 資料庫 Schema（SQLite）

### `transaction_logs`
| 欄位 | 說明 |
|---|---|
| stock_id | 股票代碼 |
| date | 交易日期 |
| method | 策略名稱 |
| position_size | 持股量 |
| position_price | 持股單價 |
| position_value | 持股成本 |
| date_closed_price | 當日收盤價 |
| broker_dividend | 累積股息 |
| asset_value | 資產價值 |

### `bt_summaries`
| 欄位 | 說明 |
|---|---|
| stock_id | 股票代碼 |
| date | 回測執行日期 |
| method | 策略名稱 |
| close | 最後收盤價 |
| position_value | 持股成本 |
| broker_dividend | 累積股息 |
| asset_value | 資產價值 |
| roi | 投資報酬率 |
| irr | 年化報酬率 |

---

## 追蹤標的

**台股（13 支）**：0050、006208、00922、00923、00692、00733、00926、0056、00878、00915、00713、00919、00929

**美股（11 支）**：VOO、QQQ、VT、VTI、XLF、XLP、XLV、IJH、IJR、IWM、NVDA

---

## 檔案職責

| 檔案 | 用途 |
|------|------|
| `Todo.md` | 未完成項目，含做法說明與優先序 |
| `Task.md` | 已完成項目的歷史紀錄，依日期分段 |
| `CLAUDE.md` | 專案規範，本身的變動也需記錄至 `Task.md` |

> 已完成的項目**不留在 `Todo.md`**，一律移至 `Task.md`。

---

## 任務管理規則

每次工作階段遵循以下流程：

1. **開始前** — 讀取 `Todo.md` 了解待辦項目，讀取 `Task.md` 了解已完成的歷史
2. **進行中** — 完成的項目從 `Todo.md` 移除
3. **結束時** — 將本次完成的項目整理後**移入 `Task.md`**，標註日期與分類

---

## 開發規則

1. 新策略只需在 `base_strategy.py` 新增 `calculate_*()` 方法與 `bt_strategy()` 的 elif 分支，並在 `tw_update.py`、`us_update.py`、`summary_table.py` 加入對應呼叫。
2. `web_data_sync.py` 動態查詢 `DISTINCT method`，新策略自動同步，**無需修改**。
3. 資料快取：股價 1 天、股息 7 天過期；快取存於 `data/tw/` 與 `data/us/`，不進版控。
4. `app/configs/` 內的金鑰檔不進版控（已加入 `.gitignore`）。
5. 函式保持 < 50 行，檔案保持 < 800 行；不可直接 mutate DataFrame，使用 `assign()` 回傳新物件。
