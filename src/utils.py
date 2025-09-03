"""
工具函數模組 - 包含通用的輔助函數
"""

import os
import logging
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Any, Optional
import json


class DateTimeEncoder(json.JSONEncoder):
    """自定義 JSON 編碼器，處理 datetime 物件"""
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        elif isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        elif isinstance(obj, np.datetime64):
            return pd.Timestamp(obj).isoformat()
        elif hasattr(obj, 'isoformat'):  # 其他有 isoformat 方法的日期時間物件
            return obj.isoformat()
        return super().default(obj)


def setup_logging(log_level: str = "INFO") -> None:
    """設置日誌記錄"""
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('finansearch.log'),
            logging.StreamHandler()
        ]
    )


def load_env_variables() -> Dict[str, str]:
    """載入環境變數"""
    from dotenv import load_dotenv
    load_dotenv()
    
    # 首先嘗試載入主要的 GEMINI_API_KEY
    gemini_key = os.getenv('GEMINI_API_KEY')
    
    # 如果主要 key 不存在，嘗試載入第一個編號 key
    if not gemini_key:
        gemini_key = os.getenv('GEMINI_API_KEY_1')
        if gemini_key:
            logging.info("使用 GEMINI_API_KEY_1 作為主要 API Key")
    
    # 如果仍然沒有 key，記錄警告
    if not gemini_key:
        logging.warning("未找到任何 Gemini API Key，請檢查 .env 檔案設定")
    
    return {
        'gemini_api_key': gemini_key,
        'debug': os.getenv('DEBUG', 'False').lower() == 'true',
        'max_stocks': int(os.getenv('MAX_STOCKS_TO_ANALYZE', '10'))
    }


def create_output_directory() -> str:
    """建立輸出目錄"""
    output_dir = f"data/output/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def save_dataframe(df: pd.DataFrame, filepath: str, formats: List[str] = ['csv']) -> None:
    """儲存 DataFrame 到多種格式"""
    base_path = filepath.rsplit('.', 1)[0]
    
    for fmt in formats:
        if fmt == 'csv':
            df.to_csv(f"{base_path}.csv", index=False, encoding='utf-8-sig')
        elif fmt == 'excel':
            df.to_excel(f"{base_path}.xlsx", index=False)
        elif fmt == 'json':
            df.to_json(f"{base_path}.json", orient='records', indent=2)
    
    logging.info(f"數據已儲存到: {base_path}.{formats}")


def format_currency(value: float) -> str:
    """格式化貨幣數值"""
    if pd.isna(value) or value is None:
        return "N/A"
    
    if value >= 1e12:
        return f"${value/1e12:.2f}T"
    elif value >= 1e9:
        return f"${value/1e9:.2f}B"
    elif value >= 1e6:
        return f"${value/1e6:.2f}M"
    elif value >= 1e3:
        return f"${value/1e3:.2f}K"
    else:
        return f"${value:.2f}"


def format_percentage(value: float) -> str:
    """格式化百分比"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value*100:.2f}%"


def format_ratio(value: float) -> str:
    """格式化比率"""
    if pd.isna(value) or value is None:
        return "N/A"
    return f"{value:.2f}"


def clean_financial_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """清理財務數據"""
    cleaned_data = {}
    
    for key, value in data.items():
        if isinstance(value, (int, float)):
            # 處理無限大和NaN值
            if pd.isna(value) or np.isinf(value):
                cleaned_data[key] = None
            else:
                cleaned_data[key] = value
        else:
            cleaned_data[key] = value
    
    return cleaned_data


def validate_ticker(ticker: str) -> bool:
    """驗證股票代碼格式"""
    if not ticker or not isinstance(ticker, str):
        return False
    
    # 基本格式檢查：只包含字母、數字和點號，長度在1-5之間
    import re
    pattern = r'^[A-Z0-9.]{1,5}$'
    return bool(re.match(pattern, ticker.upper()))


def calculate_score(metrics: Dict[str, float], weights: Dict[str, float]) -> float:
    """計算綜合評分"""
    score = 0
    total_weight = 0
    
    for metric, weight in weights.items():
        if metric in metrics and metrics[metric] is not None:
            score += metrics[metric] * weight
            total_weight += weight
    
    return score / total_weight if total_weight > 0 else 0


def create_summary_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """建立摘要統計"""
    numeric_columns = df.select_dtypes(include=['number']).columns
    
    stats = {
        'total_stocks': len(df),
        'columns': list(df.columns),
        'numeric_summary': {}
    }
    
    for col in numeric_columns:
        stats['numeric_summary'][col] = {
            'mean': df[col].mean(),
            'median': df[col].median(),
            'std': df[col].std(),
            'min': df[col].min(),
            'max': df[col].max(),
            'null_count': df[col].isnull().sum()
        }
    
    return stats


def retry_on_failure(max_retries: int = 3, delay: float = 1.0):
    """重試裝飾器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logging.error(f"函數 {func.__name__} 在 {max_retries} 次重試後仍然失敗: {e}")
                        raise
                    else:
                        logging.warning(f"函數 {func.__name__} 第 {attempt + 1} 次嘗試失敗: {e}，{delay} 秒後重試...")
                        time.sleep(delay)
            
        return wrapper
    return decorator


def progress_bar(current: int, total: int, prefix: str = "進度", length: int = 50) -> None:
    """顯示進度條"""
    percent = (current / total) * 100
    filled_length = int(length * current // total)
    bar = '█' * filled_length + '-' * (length - filled_length)
    print(f'\r{prefix}: |{bar}| {percent:.1f}% ({current}/{total})', end='', flush=True)
    
    if current == total:
        print()  # 完成時換行
