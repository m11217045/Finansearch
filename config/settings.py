"""
設定檔 - 包含所有系統設定參數
"""

# API 設定 - 基於 Yahoo Finance 每秒最多 30 次請求的限制
API_SETTINGS = {
    'request_delay': 0.05,            # API 請求間隔 (秒) - 50ms，約每秒20次請求 (低於30次限制)
    'batch_delay': 2.0,               # 批次間隔 (秒) - 每處理一批後的額外等待
    'max_retries': 3,                 # 最大重試次數
    'timeout': 30,                    # 請求超時時間 (秒)
    'max_concurrent_requests': 5,     # 最大並發請求數
    'backoff_factor': 2,              # 重試時的退避因子
    'rate_limit_per_second': 30,      # Yahoo Finance 每秒請求限制
    'safe_rate_per_second': 20,       # 安全的每秒請求數 (留有緩衝)
    'batch_size': 10,                 # 每批處理的股票數量
}

# Gemini 設定
GEMINI_SETTINGS = {
    'model': 'gemini-2.5-flash',  # 使用較便宜的模型
    'max_tokens': 2048,
    'temperature': 0.3,
    'rate_limit_delay': 3,  # API 請求間隔 (秒)
    'max_retries': 2,       # 減少重試次數以節省配額
}

# 多代理人辯論系統設定
MULTI_AGENT_SETTINGS = {
    'use_openai': False,          # 是否使用 OpenAI API (備選 Gemini)
    'debate_rounds': 2,           # 辯論輪數
    'max_agents': 5,              # 最大代理人數量
    'consensus_threshold': 0.7,   # 共識閾值
    'debate_timeout': 300,        # 辯論超時時間（秒）
    'enable_debate': True,        # 是否啟用多代理人辯論
    'max_concurrent_analysis': 5, # 最大並發分析數（Agent 並發）
    'enable_concurrent': True,    # 是否啟用並發分析
}

# 新聞和情緒分析設定
NEWS_SETTINGS = {
    'max_news_per_stock': 8,      # 每支股票最多獲取新聞數 (減少以提高質量)
    'news_days_back': 7,          # 獲取7天內的新聞 (短線投資重點)
    'news_hours_back': 168,       # 獲取168小時內的新聞 (7天)
    'priority_recent_hours': 24,  # 優先顯示24小時內的新聞
    'sentiment_analysis': True,    # 是否進行情緒分析
    'cache_news': True,           # 是否快取新聞數據
    'scrape_full_content': True,  # 是否爬取完整新聞內容
    'content_analysis': True,     # 是否分析新聞內容
    'max_content_length': 3000,   # 新聞內容最大長度
    'scraping_delay': 1,          # 爬取間隔（秒）
    'request_timeout': 15,        # 請求超時時間（秒）- 增加到15秒
    'max_retries': 3,             # 最大重試次數
    'retry_delay': 5,             # 重試延遲基數（秒）
    'skip_failed_scrapes': True,  # 跳過失敗的爬取並繼續
    'min_content_length': 50,     # 最小內容長度（低於此值視為失敗）
    'use_random_delay': True,     # 使用隨機延遲
    'random_delay_range': [1, 3], # 隨機延遲範圍（秒）
    'rotate_user_agents': True,   # 輪換 User-Agent
    'use_session': True,          # 使用 session 保持連接
    'translate_titles': True,     # 自動翻譯新聞標題為中文
    'filter_by_relevance': True,  # 根據相關性過濾新聞
    'short_term_focus': True,     # 專注短線分析
}

# 綜合分析設定
ANALYSIS_SETTINGS = {
    'fundamental_weight': 0.4,    # 基本面權重 (40%)
    'technical_weight': 0.3,      # 技術面權重 (30%)
    'news_weight': 0.3,           # 新聞面權重 (30%)
    'enable_ai_analysis': True,   # 是否啟用AI分析
    'max_concurrent_analysis': 3, # 最大並發分析數
}

# 輸出設定
OUTPUT_SETTINGS = {
    'max_stocks_to_analyze': 500,   # 最多分析股票數量（提高以支援完整SP500分析）
    'output_directory': 'data/output',
    'save_format': ['csv', 'json'], # 輸出格式
}

# 數據來源設定
DATA_SOURCES = {
    'sp500_url': 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies',
    'yahoo_finance_base': 'https://finance.yahoo.com',
}

# 財務指標設定
FINANCIAL_METRICS = {
    'required_metrics': [
        'marketCap',
        'trailingPE',
        'priceToBook',
        'dividendYield',
        'debtToEquity',
        'freeCashflow',
        'totalRevenue',
        'grossMargins',
        'operatingMargins',
        'returnOnEquity'
    ],
    'optional_metrics': [
        'beta',
        'bookValue',
        'earningsGrowth',
        'revenueGrowth',
        'currentRatio',
        'quickRatio'
    ]
}
