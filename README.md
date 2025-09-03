# 財務投資分析系統 (Finansearch)

## 專案描述
這是一個功能完整的財務投資分析系統，整合了價值投資法、AI分析與個股綜合分析功能。系統提供從價值投資篩選到個股深度分析的完整解決方案。

## 核心功能

### 🎯 價值投資篩選
- 自動獲取 S&P 500 成分股列表
- 抓取股票財務數據（P/E、P/B、股息殖利率、自由現金流等）
- 運用價值投資指標進行初步篩選
- 增強價值投資指標分析（成長性、現金流、效率、估值、財務健康）

### 📊 個股綜合分析（新功能）
- **新聞面分析（權重50%）**：實時新聞情感分析、影響力評估
- **技術面分析（權重30%）**：技術指標、趨勢分析、支撐阻力
- **籌碼面分析（權重20%）**：機構持股、內部人交易、股權結構

### 🤖 AI 驅動分析
- 使用 Gemini AI 進行深度分析和報告生成
- 智能投資建議與風險評估

### 🌐 多元介面
- Streamlit 網頁介面
- 命令列操作模式
- 批量分析功能

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

### 🚀 快速啟動

#### 網頁介面模式（推薦）
```bash
run.bat
```
在 http://localhost:5678 開啟網頁介面

#### 傳統價值投資分析
```bash
python main.py
```

#### 增強價值投資分析
```bash
python enhanced_analysis_main.py
```

#### 個股綜合分析（新功能）
```bash
python individual_stock_main.py
```
## 功能詳細說明

### 📈 個股綜合分析功能
這是系統的最新功能，提供全方位的個股分析：

#### 新聞面分析（權重 50%）
- **實時新聞抓取**：從 Yahoo Finance、Google News 等來源獲取最新新聞
- **情感分析**：基於關鍵詞和語義分析評估新聞情感
- **影響力評估**：根據新聞數量、來源可靠性、時效性計算影響力
- **趨勢判斷**：positive/negative/neutral 情感趨勢分析

#### 技術面分析（權重 30%）
- **移動平均線**：5日、10日、20日、50日均線分析
- **技術指標**：RSI、MACD、布林通道等
- **支撐阻力位**：關鍵價格水平識別
- **成交量分析**：量價關係和趨勢確認
- **趨勢判斷**：強弱多空趨勢識別

#### 籌碼面分析（權重 20%）
- **機構持股**：機構投資者持股比例分析
- **內部人交易**：公司內部人買賣情況
- **做空比例**：市場做空情緒指標
- **股權結構**：流通股本和股權集中度

### 🎯 增強價值投資分析
包含傳統價值投資指標的進階版本：

#### 成長性指標
- 營收成長率（1年、3年、5年CAGR）
- 每股盈餘成長率
- PEG比率（價格/盈餘/成長率）

#### 現金流指標
- 自由現金流分析
- FCF轉換率
- 營業現金流對淨利比

#### 效率與回報指標
- 資產報酬率（ROA）
- 投入資本回報率（ROIC）
- 資產周轉率

#### 估值乘數
- 企業價值倍數（EV/EBITDA）
- 股價/自由現金流（P/FCF）
- 企業價值/營收比

#### 財務健康指標
- 流動比率
- 速動比率
- 債務健康評估

## 專案結構
```
Finansearch/
├── main.py                           # 傳統價值投資分析
├── enhanced_analysis_main.py         # 增強價值投資分析
├── individual_stock_main.py          # 個股綜合分析（新功能）
├── streamlit_app.py                  # Streamlit 網頁應用
├── config/
│   ├── settings.py                   # 基本設定檔
│   └── individual_analysis_config.py # 個股分析設定
├── src/
│   ├── data_fetcher.py               # 數據抓取模組
│   ├── screener.py                   # 股票篩選模組（含個股分析整合）
│   ├── analyzer.py                   # Gemini AI 分析模組
│   ├── enhanced_value_analyzer.py    # 增強價值投資分析器
│   ├── stock_individual_analyzer.py  # 個股綜合分析器（新功能）
│   └── utils.py                      # 工具函數
├── data/
│   ├── sp500_tickers.csv             # S&P 500 成分股列表
│   └── output/                       # 輸出結果目錄
│       ├── reports/                  # 分析報告
│       ├── analysis/                 # 分析結果
│       └── news/                     # 新聞數據
├── test_enhanced_features.py         # 增強功能測試
├── test_individual_analysis.py       # 個股分析測試（新功能）
├── requirements.txt                  # 依賴套件
└── README.md                        # 說明文件
```

## 使用範例

### 個股分析範例
```python
from src.screener import ValueScreener

# 初始化篩選器
screener = ValueScreener()

# 分析單一股票
result = screener.analyze_individual_stock_comprehensive('AAPL')
print(f"綜合評分: {result['综合評分']}/100")
print(f"投資建議: {result['投資建議']}")

# 新聞重點分析
news_result = screener.get_news_focused_analysis('AAPL')
print(f"新聞情感: {news_result['sentiment_trend']}")
print(f"新聞評分: {news_result['news_focused_score']}/100")

# 批量比較分析
comparison = screener.compare_stocks_comprehensive(['AAPL', 'MSFT', 'GOOGL'])
print(comparison[['ticker', '综合評分', '投資建議']].head())
```

### 增強價值投資分析範例
```python
from src.enhanced_value_analyzer import EnhancedValueAnalyzer

analyzer = EnhancedValueAnalyzer()

# 綜合分析
result = analyzer.analyze_stock_comprehensive('AAPL')
print(f"綜合評分: {result['comprehensive_score']}/100")
print(f"PEG比率: {result['peg_ratio']}")
print(f"ROIC: {result['roic']:.1%}")
print(f"自由現金流殖利率: {result['fcf_yield']:.1%}")

# 批量分析
tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA']
batch_results = analyzer.batch_analyze_stocks(tickers)
print(batch_results[['ticker', 'comprehensive_score', 'investment_grade']].head())
```

## 測試功能

### 測試增強價值投資功能
```bash
python test_enhanced_features.py
```

### 測試個股綜合分析功能
```bash
python test_individual_analysis.py
```

## 評分系統

### 個股綜合評分（新功能）
- **0-100分制**，分數越高表示投資價值越高
- **新聞面權重50%**：基於最新新聞情感和影響力
- **技術面權重30%**：技術指標和趨勢分析
- **籌碼面權重20%**：機構持股和股權結構

### 投資建議等級
- **A+ (85-100分)**：強烈買入
- **A (75-84分)**：買入
- **B+ (65-74分)**：適度買入
- **B (55-64分)**：持有
- **C+ (45-54分)**：觀望
- **C (35-44分)**：謹慎
- **D (0-34分)**：避免

## 主要特色

### 🆕 個股綜合分析
- **實時新聞監控**：自動抓取和分析最新相關新聞
- **情感分析引擎**：基於關鍵詞和語義的智能情感識別
- **技術指標整合**：RSI、MACD、移動平均線等全面技術分析
- **籌碼結構透視**：機構持股、內部人交易、做空情況分析

### 📊 多維度分析
- **傳統價值投資**：P/E、P/B、股息率等經典指標
- **增強價值指標**：PEG、ROIC、FCF等進階分析
- **AI智能分析**：Gemini AI 提供深度投資洞察

### 🔄 實時更新
- 支援實時數據獲取和分析
- 新聞數據自動更新和情感評估
- 技術指標即時計算

## 應用場景

### 適用於以下投資策略
- **價值投資者**：尋找被低估的優質股票
- **成長投資者**：識別具有成長潛力的公司
- **新聞交易者**：基於新聞面進行短期投資決策
- **技術分析師**：結合基本面和技術面的綜合分析

## 價值投資篩選指標
- **本益比 (P/E Ratio)**: < 15-20
- **市淨率 (P/B Ratio)**: < 1-2
- **股息殖利率 (Dividend Yield)**: > 3-5%
- **自由現金流 (FCF)**: 正值且穩定
- **債務權益比 (D/E Ratio)**: < 1-2
- **PEG比率**: < 1.0 (成長合理價格)
- **ROIC**: > 15% (高效率運營)

## 輸出結果
系統會產生包含以下內容的分析報告：
- 符合篩選條件的股票列表
- 關鍵財務指標和增強指標
- 個股綜合分析報告（新聞面、技術面、籌碼面）
- Gemini AI 的深度分析
- 投資建議與風險評估

## 技術架構

### 數據來源
- **Yahoo Finance**：股票基本數據、財務報表、新聞
- **Google News**：新聞數據補充
- **yfinance API**：實時股價和技術指標

### 分析引擎
- **新聞情感分析**：自然語言處理和關鍵詞分析
- **技術指標計算**：移動平均、RSI、MACD等
- **價值投資評分**：多因子模型評分系統
- **Gemini AI**：深度分析和報告生成

## 系統需求
- Python 3.8+
- 網路連接（用於數據獲取）
- Gemini API Key（用於AI分析）

## 注意事項
- 本系統僅供學習和參考用途
- 投資決策請諮詢專業財務顧問
- 數據來源為第三方平台，可能存在延遲或不準確性
- 新聞分析基於程式邏輯，不代表絕對準確的情感判斷
- 請定期更新 API Key 和相關設定
- 頻繁請求可能受到API限制，建議適度使用

## 更新日誌

### v2.0.0 (最新)
- ✅ 新增個股綜合分析功能
- ✅ 實時新聞情感分析
- ✅ 技術面指標整合
- ✅ 籌碼面結構分析
- ✅ 增強價值投資指標
- ✅ 批量比較分析功能

### v1.0.0
- ✅ 基礎價值投資篩選
- ✅ S&P 500 數據獲取
- ✅ Gemini AI 分析整合
- ✅ Streamlit 網頁介面

## 授權
MIT License
