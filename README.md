# 📈 台股掃描器 (TW Stock Scanner)

自動篩選 **「剛剛站上 20 日均線（月線）」** 的強勢台股標的，幫助投資人快速找出技術面轉強的潛力股。

## ✨ 專案特色

* **技術面選股**：精準捕捉當日收盤價剛突破 20 日均線 (20MA) 的股票。
* **每日自動化執行**：結合 GitHub Actions (`.github/workflows`)，達成每日自動盤後爬取與分析，免手動操作。
* **結果匯出**：每日的掃描結果會自動更新並儲存於 `result.csv` 檔案中，方便二次分析與追蹤。
* **Web 介面 / 輕量應用**：內建 `app.py`，可透過簡單的介面或 API 快速檢視當日選股結果。

## 📁 專案結構

- `.github/workflows/`：GitHub Actions 自動化執行腳本 (定時盤後掃描)
- `src/`：核心模組原始碼
- `app.py`：應用程式主程式 (Web UI 或 API)
- `config.py`：參數與環境變數設定檔
- `daily_scan.py`：每日執行掃描與資料處理腳本
- `requirements.txt`：Python 依賴套件清單
- `result.csv`：每日掃描輸出的結果清單

## 🚀 本地端安裝與執行

若你想在自己的電腦上運行此專案，請確保已安裝 Python 3.8 或以上版本。

### 1. 複製儲存庫
```bash
git clone [https://github.com/as92012222as/tw-stock-scanner.git](https://github.com/as92012222as/tw-stock-scanner.git)
cd tw-stock-scanner

2. 安裝依賴套件
建議使用虛擬環境 (Virtual Environment) 進行安裝：
pip install -r requirements.txt

3. 執行每日掃描
手動執行盤後掃描腳本，這將會抓取最新股市資料並更新 result.csv：
python daily_scan.py

4. 啟動應用程式
若要開啟檢視介面或服務，請執行：
python app.py

⚙️ 自動化 (GitHub Actions)
本專案已配置 GitHub Actions。系統會根據 .github/workflows 內的 cron 設定，在台灣時間的每個交易日盤後自動觸發 daily_scan.py，並將最新篩選出的股票名單 commit 更新至 result.csv。

查看最新結果：直接點擊本儲存庫的 result.csv 即可查看今日剛站上月線的股票清單。

⚠️ 免責聲明
本專案提供的程式碼與掃描結果 僅供學術研究與程式開發參考，不構成任何投資建議。股市有風險，投資人應自行評估風險並自負盈虧。

🤝 貢獻與問題回報
歡迎發起 Issue 討論或是提交 Pull Request 來讓這個專案變得更好！
