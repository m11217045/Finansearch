# 財務投資分析系統 (Finansearch) - 多代理人增強版

## 專案描述
這是一個功能完整的財務投資分析系統，整合了價值投資法、**多代理人AI辯論**與個股綜合分析功能。系統提供從價值投資篩選到個股深度分析的完整解決方案，**新增多位AI投資專家協作辯論功能**。

## 🆕 新功能亮點

### 🤖 多代理人投資辯論系統
- **5位AI投資專家**：巴菲特派、葛拉漢派、成長價值、市場時機、風險管理專家
- **智能辯論機制**：專家間進行多輪辯論，達成投資共識
- **投票決策系統**：基於專家投票和信心度的綜合決策
- **辯論過程透明**：完整記錄每位專家的觀點和辯論過程

### 📊 整合分析架構
- **傳統分析 + AI辭論**：結合財務指標分析與多代理人智慧
- **加權共識決策**：根據專家共識度調整最終建議權重
- **信心度評估**：提供投資建議的可信度評分
- **風險等級評估**：多維度風險分析和評級

## 核心功能

### 🎯 價值投資篩選
- 自動獲取 S&P 500 成分股列表
- 抓取股票財務數據（P/E、P/B、股息殖利率、自由現金流等）
- 運用價值投資指標進行初步篩選
- 增強價值投資指標分析（成長性、現金流、效率、估值、財務健康）

### 🤖 多代理人AI辯論分析（🆕 新功能）
- **專家團隊組成**：
  - 巴菲特派價值投資師：專注長期價值、護城河分析
  - 葛拉漢派防御型投資師：重視安全邊際、風險控制  
  - 成長價值投資師：尋找被低估的成長股
  - 市場時機分析師：判斷市場週期、進出時機
  - 風險管理專家：評估風險、資產配置建議

- **辯論流程**：
  1. 各專家獨立分析 → 提出初步觀點
  2. 多輪辯論 → 專家間相互質疑和補強論點  
  3. 投票決策 → 基於共識度產生最終建議
  4. 整合報告 → 傳統分析與AI辯論結果整合

### 📊 個股綜合分析
- **新聞面分析（權重50%）**：實時新聞情感分析、影響力評估
- **技術面分析（權重30%）**：技術指標、趨勢分析、支撐阻力
- **籌碼面分析（權重20%）**：機構持股、內部人交易、股權結構

### 🌐 多元介面
- **Streamlit 網頁介面**：包含多代理人辯論可視化
- **命令列操作模式**：支持批量多代理人分析
- **辯論過程展示**：完整呈現專家辯論過程和決策邏輯

## 安裝與設置

### 1. 克隆專案
```bash
git clone <repository-url>
cd Finansearch
```

### 2. 安裝依賴套件

#### 自動安裝（推薦）
```bash
# Windows
install_multi_agent.bat

# 或手動安裝
pip install -r requirements.txt
```

#### 主要新增套件
```bash
# 多代理人系統套件（可選）
pip install langchain-openai>=0.1.0
pip install langchain-core>=0.2.0  
pip install langchain-experimental>=0.0.60
pip install langgraph>=0.1.0
```

### 3. 環境變數設置
在專案根目錄建立 `.env` 檔案並設置：
```
# 必須：Gemini AI API (免費額度可用)
GEMINI_API_KEY=your_gemini_api_key_here

# 可選：OpenAI API (更高品質但需付費)
OPENAI_API_KEY=your_openai_api_key_here
```

### 4. 獲取 API Keys
- **Gemini API Key** (免費)：[Google AI Studio](https://aistudio.google.com/)
- **OpenAI API Key** (付費，可選)：[OpenAI Platform](https://platform.openai.com/)

## 使用方式

### 🚀 快速開始

#### 1. 多代理人網頁介面（🆕 推薦）
```bash
streamlit run streamlit_multi_agent_app.py
```
- 支援單股快速分析
- 觀察專家辯論過程
- 多股票比較分析
- 直觀的投票和共識視覺化

#### 2. 傳統網頁介面
```bash
streamlit run streamlit_app.py
```

#### 3. 多代理人命令列分析（🆕）
```bash
python multi_agent_main.py
```
- 批量股票篩選
- 多代理人深度分析
- 生成詳細辯論報告

#### 4. 傳統分析模式
```bash
python main.py                      # 基礎價值投資分析
python enhanced_analysis_main.py    # 增強版分析
python individual_stock_main.py     # 個股詳細分析
```

### 📋 多代理人分析流程

#### 完整分析流程
1. **初步篩選**：從 S&P 500 中篩選價值投資標的
2. **專家分析**：5位AI專家獨立分析每支股票
3. **辯論討論**：專家間進行2-3輪辯論，質疑和補強觀點
4. **投票決策**：基於辯論結果進行投票，計算共識度
5. **整合建議**：結合傳統分析與AI辯論，產出最終建議

#### 分析報告內容
- **投資建議**：買入/持有/賣出 + 信心度評分 (1-10)
- **專家共識度**：顯示專家間的一致性程度 (0-100%)
- **辯論摘要**：主要爭議點和達成共識的原因
- **風險評估**：多維度風險分析和等級評定
- **投票分佈**：各專家的投票記錄和變化

## 🔧 系統配置

### 多代理人設置
在 `config/settings.py` 中可調整：
```python
MULTI_AGENT_SETTINGS = {
    'enable_debate': True,        # 是否啟用多代理人辯論
    'debate_rounds': 2,           # 辯論輪數 (1-5)
    'max_agents': 5,              # 代理人數量
    'consensus_threshold': 0.7,   # 共識閾值
    'debate_timeout': 300,        # 辯論超時時間（秒）
}
```

### API 使用建議
- **Gemini API**：免費額度足夠日常使用，適合個人投資者
- **OpenAI API**：付費但品質更高，適合專業投資分析

## 📊 輸出結果

### 多代理人分析檔案
- `investment_ranking.csv`：投資建議排名
- `detailed_analysis_reports.json`：完整辯論記錄
- `analysis_summary.csv`：分析摘要表格

### 傳統分析檔案
- `raw_stock_data.csv`：原始股票數據
- `screened_stocks.csv`：篩選後的股票列表
- `enhanced_analysis_results.csv`：增強分析結果

### 網頁介面功能
- 實時辯論過程展示
- 專家投票視覺化
- 多股票比較分析
- 互動式圖表和報告

## 🤖 AI 專家團隊介紹

| 專家角色 | 投資風格 | 專長領域 |
|---------|---------|---------|
| 巴菲特派價值投資師 | 長期持有、尋找護城河 | 基本面分析、競爭優勢評估 |
| 葛拉漢派防御型投資師 | 重視安全邊際 | 財務穩健性、風險控制 |
| 成長價值投資師 | 被低估的成長股 | 成長性評估、未來潛力分析 |
| 市場時機分析師 | 適時進出場 | 市場週期、技術面分析 |
| 風險管理專家 | 嚴格風控 | 風險識別、資產配置建議 |

### 辯論機制
1. **獨立分析階段**：各專家基於自身投資哲學獨立分析
2. **辯論階段**：專家間相互質疑、補強論點
3. **投票階段**：基於辯論結果更新投資建議
4. **共識形成**：計算專家共識度，產出最終建議

## 💡 最佳實踐建議

### 使用策略
1. **篩選階段**：先用傳統指標篩出候選股票
2. **深度分析**：對重點股票啟用多代理人分析
3. **決策參考**：結合專家共識度和個人判斷
4. **定期更新**：市場變化時重新進行分析

### 注意事項
- ⚠️ AI 分析僅供參考，最終投資決策請審慎評估
- ⚠️ 建議結合多種分析方法，避免單一依賴
- ⚠️ 注意API使用額度，合理控制分析頻率
- ⚠️ 定期檢查市場環境變化對分析結果的影響

## 🔄 版本更新歷史

### v2.0 - 多代理人增強版 (🆕)
- ✅ 新增5位AI投資專家
- ✅ 多輪辯論決策機制  
- ✅ 專家投票和共識系統
- ✅ 辯論過程可視化
- ✅ 整合分析架構
- ✅ 專用多代理人網頁介面

### v1.0 - 基礎版本
- ✅ S&P 500 價值投資篩選
- ✅ 單一AI分析引擎
- ✅ 新聞情緒分析
- ✅ 技術指標分析
- ✅ Streamlit 網頁介面

## 🏗️ 技術架構

### 核心技術棧
- **AI模型**：Google Gemini + OpenAI GPT (可選)
- **數據來源**：Yahoo Finance + 新聞 API
- **前端介面**：Streamlit
- **數據處理**：Pandas + NumPy
- **視覺化**：Plotly + 自定義圖表

### 多代理人系統架構
```
股票數據輸入 → 價值投資篩選 → 多代理人分析系統
                                      ↓
            5位專家獨立分析 → 多輪辯論機制 → 投票決策系統
                                      ↓  
            傳統分析整合 → 加權共識計算 → 最終投資建議 → 報告生成
```

### 分析整合流程
1. **數據獲取**：Yahoo Finance API
2. **價值篩選**：傳統價值投資指標
3. **AI分析**：多代理人獨立分析
4. **辯論機制**：專家間質疑與補強
5. **共識決策**：投票與信心度計算
6. **結果整合**：傳統+AI分析權重整合
7. **報告輸出**：多格式結果展示
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
│   ├── enhanced_analyzer.py          # 增強股票分析器（含多代理人辯論功能）
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

### 增強多代理人分析範例
```python
from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate

# 啟用多代理人辯論功能
analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=True)

# 綜合分析（包含多代理人辯論）
stock_data = {'ticker': 'AAPL', 'symbol': 'AAPL'}
result = analyzer.analyze_stock_comprehensive(stock_data, include_debate=True)

# 查看分析結果
print(f"綜合評分: {result['overall_score']}/100")
print(f"投資建議: {result['investment_recommendation']}")

# 查看多代理人辯論結果
if 'multi_agent_debate' in result:
    debate = result['multi_agent_debate']
    final_consensus = debate['final_consensus']
    print(f"專家共識建議: {final_consensus['final_recommendation']}")
    print(f"專家共識度: {final_consensus['consensus_level']:.1%}")

# 批量分析
stock_list = [{'ticker': 'AAPL'}, {'ticker': 'MSFT'}, {'ticker': 'GOOGL'}]
batch_results = analyzer.batch_analyze_stocks(stock_list, include_debate=True)
print(f"分析完成: {batch_results['successful_analyses']} 支股票")
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
