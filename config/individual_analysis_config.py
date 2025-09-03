"""
個股分析配置文件
"""

# 新聞分析配置
NEWS_ANALYSIS_CONFIG = {
    # 新聞源權重
    'news_source_weights': {
        'Yahoo Finance': 1.0,
        'Google News': 0.8,
        'Reuters': 1.2,
        'Bloomberg': 1.2,
        'MarketWatch': 0.9,
        'CNBC': 0.9,
        'SeekingAlpha': 0.7,
        'Various': 0.6
    },
    
    # 情感關鍵詞配置
    'sentiment_keywords': {
        'positive': [
            'beat', 'exceed', 'strong', 'growth', 'profit', 'revenue', 'upgrade', 
            'buy', 'bullish', 'positive', 'gain', 'rise', 'surge', 'boost',
            'outperform', 'success', 'expand', 'increase', 'good', 'excellent',
            'breakthrough', 'milestone', 'record', 'soar', 'rally', 'momentum',
            'optimistic', 'confident', 'robust', 'solid', 'impressive'
        ],
        
        'negative': [
            'miss', 'decline', 'loss', 'drop', 'fall', 'downgrade', 'sell', 
            'bearish', 'negative', 'concern', 'risk', 'warn', 'cut', 'reduce',
            'underperform', 'challenge', 'problem', 'issue', 'bad', 'poor',
            'plunge', 'crash', 'tumble', 'slump', 'disappointing', 'weak',
            'struggle', 'pressure', 'uncertainty', 'volatile', 'decline'
        ],
        
        'neutral': [
            'stable', 'maintain', 'hold', 'unchanged', 'steady', 'neutral',
            'mixed', 'cautious', 'watchful', 'monitor', 'observe'
        ]
    },
    
    # 新聞時效性權重 (天數 -> 權重)
    'news_time_weights': {
        0: 1.0,    # 當天
        1: 0.9,    # 1天前
        2: 0.8,    # 2天前
        3: 0.7,    # 3天前
        7: 0.5,    # 1週前
        14: 0.3,   # 2週前
        30: 0.1    # 1個月前
    }
}

# 技術分析配置
TECHNICAL_ANALYSIS_CONFIG = {
    # 技術指標權重
    'indicator_weights': {
        'trend': 0.30,      # 趨勢分析
        'rsi': 0.20,        # RSI指標
        'macd': 0.25,       # MACD指標
        'volume': 0.15,     # 成交量分析
        'support_resistance': 0.10  # 支撐阻力
    },
    
    # RSI評分區間
    'rsi_zones': {
        'oversold': (0, 30),      # 超賣
        'normal_low': (30, 40),   # 正常偏低
        'normal': (40, 60),       # 正常
        'normal_high': (60, 70),  # 正常偏高
        'overbought': (70, 100)   # 超買
    },
    
    # 移動平均線配置
    'moving_averages': {
        'short': [5, 10],
        'medium': [20, 50],
        'long': [100, 200]
    }
}

# 籌碼分析配置
CHIP_ANALYSIS_CONFIG = {
    # 籌碼指標權重
    'chip_weights': {
        'institutional_ownership': 0.40,  # 機構持股
        'insider_ownership': 0.20,        # 內部人持股
        'short_ratio': 0.25,              # 做空比例
        'ownership_concentration': 0.15   # 股權集中度
    },
    
    # 機構持股評分標準
    'institutional_ownership_grades': {
        'excellent': (60, 80),    # 優秀範圍
        'good': (40, 60),         # 良好範圍
        'fair': (20, 40),         # 普通範圍
        'poor': (0, 20)           # 較差範圍
    },
    
    # 做空比例評分標準
    'short_ratio_grades': {
        'excellent': (0, 3),      # 優秀 (低做空)
        'good': (3, 5),           # 良好
        'fair': (5, 8),           # 普通
        'poor': (8, float('inf')) # 較差 (高做空)
    }
}

# 綜合評分配置
COMPREHENSIVE_SCORING_CONFIG = {
    # 主要權重分配
    'main_weights': {
        'news': 0.50,        # 新聞面權重 50%
        'technical': 0.30,   # 技術面權重 30%
        'chip': 0.20         # 籌碼面權重 20%
    },
    
    # 新聞重點模式權重分配
    'news_focused_weights': {
        'news': 0.70,        # 新聞面權重 70%
        'technical': 0.20,   # 技術面權重 20%
        'chip': 0.10         # 籌碼面權重 10%
    },
    
    # 評分等級標準
    'score_grades': {
        'A+': (85, 100),     # 強烈買入
        'A': (75, 85),       # 買入
        'B+': (65, 75),      # 適度買入
        'B': (55, 65),       # 持有
        'C+': (45, 55),      # 觀望
        'C': (35, 45),       # 謹慎
        'D': (0, 35)         # 避免
    }
}

# API請求配置
API_CONFIG = {
    # 請求間隔 (秒)
    'request_intervals': {
        'yahoo_finance': 0.5,
        'google_news': 1.0,
        'general': 0.2
    },
    
    # 超時設置 (秒)
    'timeout_settings': {
        'news_request': 10,
        'stock_data': 15,
        'general': 5
    },
    
    # 重試配置
    'retry_config': {
        'max_retries': 3,
        'retry_delay': 1.0,
        'backoff_factor': 2.0
    }
}

# 數據保存配置
DATA_SAVE_CONFIG = {
    # 輸出目錄
    'output_directories': {
        'reports': 'data/output/reports',
        'analysis': 'data/output/analysis',
        'news': 'data/output/news',
        'logs': 'logs'
    },
    
    # 文件格式
    'file_formats': {
        'csv': True,
        'json': True,
        'txt': True,
        'excel': False
    },
    
    # 數據保留期限 (天)
    'data_retention': {
        'analysis_results': 30,
        'news_data': 7,
        'logs': 14
    }
}

# 顯示配置
DISPLAY_CONFIG = {
    # 表格顯示設置
    'table_settings': {
        'max_company_name_length': 20,
        'decimal_places': 2,
        'percentage_format': '.1%'
    },
    
    # 報告設置
    'report_settings': {
        'max_news_display': 5,
        'report_width': 80,
        'preview_length': 1000
    }
}
