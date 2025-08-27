# S&P 500 價值投資股票篩選系統

## 專案描述
這是一個運用價值投資法與 Gemini AI 來從標普500成分股中尋找被低估股票的自動化系統。

## 主要功能
- 自動獲取 S&P 500 成分股列表
- 抓取股票財務數據（P/E、P/B、股息殖利率、自由現金流等）
- 運用價值投資指標進行初步篩選
- 使用 Gemini AI 進行深度分析和報告生成
- 提供 Streamlit 網頁介面

## 安裝與設置

### 1. 克隆專案
```bash
git clone <repository-url>
cd Finansearch
```

### 2. 安裝依賴套件
```bash
pip install -r requirements.txt
```

### 3. 環境變數設置
在專案根目錄建立 `.env` 檔案並設置：
```
GEMINI_API_KEY=your_gemini_api_key_here
```

### 4. 獲取 Gemini API Key
1. 訪問 [Google AI Studio](https://aistudio.google.com/)
2. 建立新的 API Key
3. 將 API Key 加入 `.env` 檔案

## 使用方法

### 快速啟動（推薦）

#### 網頁介面模式（預設）
```bash
run.bat
```
這會直接啟動網頁介面，在 http://localhost:5678 開啟

#### 命令列模式
```bash
run_cli.bat
```

#### PowerShell 腳本（完整選項）
```powershell
.\run.ps1
```

### 手動啟動

#### 命令列模式
```bash
"D:/Finansearch/.venv/Scripts/python.exe" main.py
```

#### 網頁介面模式
```bash
"D:/Finansearch/.venv/Scripts/streamlit.exe" run streamlit_app.py --server.port 5678
```

## 專案結構
```
Finansearch/
├── main.py                 # 主要執行腳本
├── streamlit_app.py         # Streamlit 網頁應用
├── config/
│   └── settings.py          # 設定檔
├── src/
│   ├── data_fetcher.py      # 數據抓取模組
│   ├── screener.py          # 股票篩選模組
│   ├── analyzer.py          # Gemini 分析模組
│   └── utils.py             # 工具函數
├── data/
│   ├── sp500_tickers.csv    # S&P 500 成分股列表
│   └── output/              # 輸出結果目錄
├── requirements.txt         # 依賴套件
└── README.md               # 說明文件
```

## 價值投資篩選指標
- **本益比 (P/E Ratio)**: < 15-20
- **市淨率 (P/B Ratio)**: < 1-2
- **股息殖利率 (Dividend Yield)**: > 3-5%
- **自由現金流 (FCF)**: 正值且穩定
- **債務權益比 (D/E Ratio)**: < 1-2

## 輸出結果
系統會產生包含以下內容的分析報告：
- 符合篩選條件的股票列表
- 關鍵財務指標
- Gemini AI 的深度分析
- 投資建議與風險評估

## 注意事項
- 本系統僅供學習和參考用途
- 投資決策請諮詢專業財務顧問
- 數據來源為 Yahoo Finance，可能存在延遲或不準確性
- 請定期更新 API Key 和相關設定

## 授權
MIT License
