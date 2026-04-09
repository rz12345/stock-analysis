# 待辦任務

## 中優先

- [ ] **策略參數化**
  - `bt_ma_pullback` 的均線天數（目前硬編碼 120）改為可設定
  - `bt_signals` 的 RSI 門檻（目前硬編碼 50）改為可設定

- [ ] **回測起始日期彈性化**
  - 目前 `tw_update.py` / `us_update.py` hardcode `start_date = '2020-01-01'`
  - 改為設定檔驅動

- [ ] **新增美股股息資料來源**
  - 目前美股股息依賴 Tiingo `adjClose` 隱含，考慮明確分離配息欄位

## 低優先

- [ ] **報表美化**
  - `base_report.py` 的 PDF 產生功能已被 comment out，評估是否恢復或移除
