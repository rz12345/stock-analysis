# 待辦任務

## 高優先

- [ ] **補充單元測試**（pytest）
  - `calculate_monthly_dca()` 訊號正確性
  - `calculate_ma_pullback()` 邊界條件
  - `calculate_macd_and_rsi()` 數值驗證
  - `_detect_split()` 分割偵測邏輯
  - 目標覆蓋率：80%+

- [ ] **`summary_table.py` 納入 `bt_ma_pullback` 彙總表**
  - 目前 `methods` 只有 `bt_dividend`、`bt_signals`、`bt_monthly_dca`，缺少 `bt_ma_pullback`

## 中優先

- [ ] **策略參數化**
  - `bt_ma_pullback` 的均線天數（目前硬編碼 120）改為可設定
  - `bt_signals` 的 RSI 門檻（目前硬編碼 50）改為可設定

- [ ] **停損/停利機制**
  - 目前策略為純買入，無出場邏輯
  - 評估加入固定比例停損（如 -20%）或移動停利

- [ ] **回測起始日期彈性化**
  - 目前 `tw_update.py` / `us_update.py` hardcode `start_date = '2020-01-01'`
  - 改為 CLI 參數或設定檔驅動

- [ ] **新增美股股息資料來源**
  - 目前美股股息依賴 Tiingo `adjClose` 隱含，考慮明確分離配息欄位

## 低優先

- [ ] **Firebase 同步失敗重試機制**
  - 目前 `web_data_sync.py` 無錯誤處理

- [ ] **報表美化**
  - `base_report.py` 的 PDF 產生功能已被 comment out，評估是否恢復或移除

- [ ] **追蹤標的管理**
  - 台股/美股清單目前 hardcode 在 runner 腳本，考慮抽到設定檔（YAML/JSON）
