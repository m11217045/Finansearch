"""
數據抓取模組 - 負責獲取 S&P 500 成分股列表和財務數據
"""

import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from config.settings import API_SETTINGS, DATA_SOURCES, FINANCIAL_METRICS
from src.utils import retry_on_failure, progress_bar, clean_financial_data


class RateLimiter:
    """速率限制器，確保不超過 Yahoo Finance API 限制"""
    
    def __init__(self, max_calls_per_second: int = 20):
        self.max_calls_per_second = max_calls_per_second
        self.min_interval = 1.0 / max_calls_per_second
        self.last_call_time = 0
        self.call_count = 0
        self.start_time = time.time()
    
    def wait_if_needed(self):
        """如果需要，等待以符合速率限制"""
        current_time = time.time()
        
        # 檢查是否需要重置計數器（每秒重置）
        if current_time - self.start_time >= 1.0:
            self.call_count = 0
            self.start_time = current_time
        
        # 如果已達到每秒限制，等待到下一秒
        if self.call_count >= self.max_calls_per_second:
            sleep_time = 1.0 - (current_time - self.start_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
                self.call_count = 0
                self.start_time = time.time()
        
        # 確保最小間隔
        time_since_last_call = current_time - self.last_call_time
        if time_since_last_call < self.min_interval:
            time.sleep(self.min_interval - time_since_last_call)
        
        self.last_call_time = time.time()
        self.call_count += 1


class SP500DataFetcher:
    """S&P 500 數據抓取器"""
    
    def __init__(self):
        self.tickers = []
        self.financial_data = {}
        self.rate_limiter = RateLimiter(max_calls_per_second=API_SETTINGS['safe_rate_per_second'])
        
    @retry_on_failure(max_retries=3, delay=2.0)
    def get_sp500_tickers(self) -> List[str]:
        """從多個來源獲取 S&P 500 成分股列表"""
        try:
            # 嘗試方法1: 使用 yfinance 直接獲取
            logging.info("嘗試從 yfinance 獲取 S&P 500 成分股...")
            sp500_ticker = yf.Ticker("^GSPC")
            
            # 方法2: 使用備用的 API 或網站
            logging.info("嘗試從備用來源獲取 S&P 500 成分股...")
            
            # 使用不同的 User-Agent 來避免 403 錯誤
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            url = DATA_SOURCES['sp500_url']
            response = requests.get(url, headers=headers, timeout=API_SETTINGS['timeout'])
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'class': 'wikitable sortable'})
            
            if not table:
                # 嘗試其他可能的表格選擇器
                table = soup.find('table', {'id': 'constituents'})
            
            if not table:
                logging.warning("在 Wikipedia 頁面找不到成分股表格，使用備用列表")
                return self._get_fallback_tickers()
            
            tickers = []
            for row in table.find_all('tr')[1:]:  # 跳過標題行
                cells = row.find_all('td')
                if len(cells) >= 1:
                    ticker = cells[0].text.strip()
                    # 處理特殊字符（如 BRK.B 中的點號）
                    ticker = ticker.replace('.', '-')
                    # 移除可能的額外空白字符
                    ticker = ''.join(ticker.split())
                    if ticker and len(ticker) <= 5:  # 確保是有效的股票代碼
                        tickers.append(ticker)
            
            if len(tickers) < 400:  # S&P 500 應該有接近 500 支股票
                logging.warning(f"獲取的股票數量異常 ({len(tickers)})，使用備用列表")
                return self._get_fallback_tickers()
            
            logging.info(f"成功獲取 {len(tickers)} 個 S&P 500 成分股代碼")
            self.tickers = tickers
            return tickers
            
        except requests.exceptions.RequestException as e:
            logging.error(f"網路請求失敗: {e}")
            return self._get_fallback_tickers()
        except Exception as e:
            logging.error(f"獲取 S&P 500 成分股列表失敗: {e}")
            return self._get_fallback_tickers()
    
    def _get_fallback_tickers(self) -> List[str]:
        """備用的 S&P 500 主要成分股列表"""
        fallback_tickers = [
            # 科技股
            'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'ADBE', 'CRM',
            'ORCL', 'CSCO', 'AVGO', 'TXN', 'QCOM', 'IBM', 'AMD', 'INTC', 'PYPL', 'UBER',
            
            # 金融股
            'BRK-B', 'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'USB', 'PNC',
            'TFC', 'COF', 'SCHW', 'BLK', 'CB', 'MMC', 'ICE', 'CME', 'SPGI', 'MCO',
            
            # 醫療保健
            'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'LLY', 'BMY', 'AMGN',
            'GILD', 'MDT', 'ISRG', 'DHR', 'SYK', 'BSX', 'REGN', 'VRTX', 'BIIB', 'ZTS',
            
            # 消費品
            'PG', 'KO', 'PEP', 'WMT', 'COST', 'HD', 'MCD', 'SBUX', 'NKE', 'LOW',
            'TGT', 'CVS', 'WBA', 'KMB', 'CL', 'GIS', 'K', 'CAG', 'CPB', 'CLX',
            
            # 工業股
            'BA', 'HON', 'UPS', 'CAT', 'MMM', 'GE', 'LMT', 'RTX', 'DE', 'FDX',
            'UNP', 'CSX', 'NSC', 'LUV', 'DAL', 'AAL', 'UAL', 'WM', 'RSG', 'EMR',
            
            # 能源股
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'VLO', 'PSX', 'OXY', 'HAL',
            
            # 公用事業
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'XEL', 'SRE', 'D', 'PEG', 'EIX',
            
            # 材料股
            'LIN', 'APD', 'ECL', 'DD', 'DOW', 'PPG', 'SHW', 'FCX', 'NUE', 'VMC',
            
            # 房地產
            'AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'O', 'WELL', 'DLR', 'PSA', 'EQR',
            
            # 其他重要股票
            'V', 'MA', 'BKNG', 'DIS', 'CMCSA', 'VZ', 'T', 'PM', 'MO', 'TMUS'
        ]
        logging.warning(f"使用備用股票列表，包含 {len(fallback_tickers)} 個主要 S&P 500 成分股")
        self.tickers = fallback_tickers
        return fallback_tickers
    
    def save_tickers_to_csv(self, filepath: str = "data/sp500_tickers.csv") -> None:
        """將股票代碼列表儲存為 CSV"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        df = pd.DataFrame({'ticker': self.tickers})
        df.to_csv(filepath, index=False)
        logging.info(f"S&P 500 成分股列表已儲存到: {filepath}")
    
    def load_tickers_from_csv(self, filepath: str = "data/sp500_tickers.csv") -> List[str]:
        """從 CSV 檔案載入股票代碼列表"""
        try:
            df = pd.read_csv(filepath)
            self.tickers = df['ticker'].tolist()
            logging.info(f"從 {filepath} 載入了 {len(self.tickers)} 個股票代碼")
            return self.tickers
        except FileNotFoundError:
            logging.warning(f"找不到檔案 {filepath}，將重新獲取股票列表")
            return self.get_sp500_tickers()
    
    @retry_on_failure(max_retries=3, delay=1.0)
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """獲取單一股票的詳細資訊"""
        # 應用速率限制
        self.rate_limiter.wait_if_needed()
        
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            # 獲取歷史數據來計算額外指標
            hist = stock.history(period="1y")
            
            # 提取關鍵財務指標
            financial_data = {
                'ticker': ticker,
                'company_name': info.get('longName', info.get('shortName', ticker)),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                
                # 估值指標
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'price_to_book': info.get('priceToBook'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                
                # 股息指標
                'dividend_yield': info.get('dividendYield'),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                
                # 獲利能力指標
                'profit_margins': info.get('profitMargins'),
                'gross_margins': info.get('grossMargins'),
                'operating_margins': info.get('operatingMargins'),
                'return_on_equity': info.get('returnOnEquity'),
                'return_on_assets': info.get('returnOnAssets'),
                
                # 財務健康度指標
                'total_cash': info.get('totalCash'),
                'total_debt': info.get('totalDebt'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'quick_ratio': info.get('quickRatio'),
                
                # 現金流指標
                'free_cashflow': info.get('freeCashflow'),
                'operating_cashflow': info.get('operatingCashflow'),
                
                # 成長指標
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                
                # 其他指標
                'beta': info.get('beta'),
                'book_value': info.get('bookValue'),
                'price_to_book': info.get('priceToBook'),
                
                # 當前股價資訊
                'current_price': info.get('currentPrice', info.get('regularMarketPrice')),
                'previous_close': info.get('previousClose'),
                '52_week_high': info.get('fiftyTwoWeekHigh'),
                '52_week_low': info.get('fiftyTwoWeekLow'),
                
                # 額外計算的指標
                'average_volume': hist['Volume'].mean() if not hist.empty else None,
                'price_volatility': hist['Close'].pct_change().std() * (252**0.5) if not hist.empty else None,
            }
            
            return clean_financial_data(financial_data)
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 股票資訊失敗: {e}")
            return {'ticker': ticker, 'error': str(e)}
    
    def batch_fetch_stock_data(self, tickers: Optional[List[str]] = None, 
                              max_stocks: Optional[int] = None) -> pd.DataFrame:
        """批量獲取股票數據"""
        if tickers is None:
            tickers = self.tickers
        
        if max_stocks:
            tickers = tickers[:max_stocks]
        
        logging.info(f"開始獲取 {len(tickers)} 個股票的財務數據...")
        logging.info(f"速率限制：每秒最多 {API_SETTINGS['safe_rate_per_second']} 次請求")
        
        all_data = []
        failed_tickers = []
        batch_size = API_SETTINGS['batch_size']  # 使用配置文件中的批次大小
        
        # 估算總時間
        estimated_time = len(tickers) * (1.0 / API_SETTINGS['safe_rate_per_second'])
        logging.info(f"預計完成時間：{estimated_time:.1f} 秒")
        
        for i, ticker in enumerate(tickers):
            try:
                stock_data = self.get_stock_info(ticker)
                
                if 'error' not in stock_data:
                    all_data.append(stock_data)
                else:
                    failed_tickers.append(ticker)
                
                # 進度顯示
                progress_bar(i + 1, len(tickers), f"獲取數據")
                
                # 每處理一批後額外休息
                if (i + 1) % batch_size == 0:
                    logging.info(f"已處理 {i + 1}/{len(tickers)} 個股票，休息 {API_SETTINGS['batch_delay']} 秒...")
                    time.sleep(API_SETTINGS['batch_delay'])
                
            except Exception as e:
                logging.error(f"處理 {ticker} 時發生錯誤: {e}")
                failed_tickers.append(ticker)
                continue
        
        if failed_tickers:
            logging.warning(f"以下 {len(failed_tickers)} 個股票獲取失敗: {failed_tickers}")
        
        df = pd.DataFrame(all_data)
        logging.info(f"成功獲取 {len(df)} 個股票的數據")
        
        return df
    
    def get_financial_statements(self, ticker: str) -> Dict[str, pd.DataFrame]:
        """獲取財務報表（損益表、資產負債表、現金流量表）"""
        try:
            stock = yf.Ticker(ticker)
            
            statements = {
                'income_statement': stock.financials,
                'balance_sheet': stock.balance_sheet,
                'cash_flow': stock.cashflow
            }
            
            return statements
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 財務報表失敗: {e}")
            return {}
    
    def get_key_statistics(self, ticker: str) -> Dict[str, Any]:
        """獲取關鍵統計數據"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            key_stats = {
                'market_cap': info.get('marketCap'),
                'enterprise_value': info.get('enterpriseValue'),
                'trailing_pe': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'peg_ratio': info.get('pegRatio'),
                'price_to_sales': info.get('priceToSalesTrailing12Months'),
                'price_to_book': info.get('priceToBook'),
                'enterprise_to_revenue': info.get('enterpriseToRevenue'),
                'enterprise_to_ebitda': info.get('enterpriseToEbitda'),
                'beta': info.get('beta'),
                'dividend_yield': info.get('dividendYield'),
                'ex_dividend_date': info.get('exDividendDate'),
                'payout_ratio': info.get('payoutRatio')
            }
            
            return clean_financial_data(key_stats)
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 關鍵統計數據失敗: {e}")
            return {}
