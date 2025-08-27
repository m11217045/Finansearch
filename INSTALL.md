# 安裝與設定指南

## 快速開始

### 1. 安裝 Python 套件
在專案目錄中執行：

```powershell
pip install -r requirements.txt
```

### 2. 設定 Gemini API Key

1. 訪問 [Google AI Studio](https://aistudio.google.com/)
2. 建立免費帳號並獲取 API Key
3. 複製 `.env.example` 為 `.env`：
   ```powershell
   Copy-Item .env.example .env
   ```
4. 編輯 `.env` 檔案，填入您的 API Key：
   ```
   GEMINI_API_KEY=your_actual_api_key_here
   ```

### 3. 執行程式

#### 方法一：快速啟動網頁介面（推薦）
```powershell
run.bat
```
直接啟動網頁介面，在 http://localhost:5678 開啟

#### 方法二：命令列模式
```powershell
run_cli.bat
```

#### 方法三：完整選項（PowerShell）
```powershell
.\run.ps1
```

#### 方法四：手動安裝套件（如果自動安裝失敗）
```powershell
install_packages.bat
```

## 系統需求

- Python 3.8 或以上版本
- 網路連線（用於獲取股票數據）
- Gemini API Key（免費）

## 預期執行時間

- 獲取 S&P 500 成分股列表：約 30 秒
- 獲取 100 支股票財務數據：約 3-5 分鐘
- 篩選和評分：約 10 秒
- Gemini AI 分析 10 支股票：約 2-3 分鐘

## 輸出檔案說明

執行完成後，結果會保存在 `data/output/` 目錄下：

- `sp500_tickers.csv` - S&P 500 成分股列表
- `raw_stock_data.csv` - 原始股票數據
- `screened_stocks.csv` - 篩選後的股票
- `gemini_analysis.json` - AI 分析結果
- `summary_report.txt` - 摘要報告

## 故障排除

### 常見問題

1. **ImportError: No module named 'xxx'**
   - 解決方案：確保已執行 `pip install -r requirements.txt`

2. **Gemini API 錯誤**
   - 檢查 API Key 是否正確設置
   - 確認有網路連線

3. **Yahoo Finance 數據獲取失敗**
   - 網路連線問題，稍後重試
   - 部分股票可能暫時無法獲取數據，這是正常的

4. **程式執行緩慢**
   - 可以減少分析的股票數量
   - 確保網路連線穩定

### 日誌檔案

程式執行時會產生 `finansearch.log` 檔案，包含詳細的執行日誌，有助於問題診斷。
