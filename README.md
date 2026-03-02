# 📈 台股掃描器 (TW Stock Scanner)

自動篩選 **「剛剛站上 20 日均線（月線）」** 的強勢台股標的，幫助投資人快速找出技術面轉強的潛力股。

## ✨ 專案特色

* **技術面選股**：精準捕捉當日收盤價剛突破 20 日均線 (20MA) 的股票。
* **每日自動化執行**：結合 GitHub Actions (`.github/workflows`)，達成每日自動盤後爬取與分析，免手動操作。
* **結果匯出**：每日的掃描結果會自動更新並儲存於 `result.csv` 檔案中，方便二次分析與追蹤。
* **Web 介面 / 輕量應用**：內建 `app.py`，可透過簡單的介面或 API 快速檢視當日選股結果。

## 📁 專案結構

```text
tw-stock-scanner/
├── .github/workflows/   # GitHub Actions 自動化執行腳本 (定時盤後掃描)
├── src/                 # 核心模組原始碼
├── app.py               # 應用程式主程式 (Web UI 或 API)
├── config.py            # 參數與環境變數設定檔
├── daily_scan.py        # 每日執行掃描與資料處理腳本
├── requirements.txt     # Python 依賴套件清單
└── result.csv           # 每日掃描輸出的結果清單
