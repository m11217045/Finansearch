"""
數據抓取模組 - 負責獲取多種股票組合列表和財務數據
支持: S&P 500、美國科技7巨頭(FAANG+)、台灣股市前50
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


# 定義不同的股票組合
STOCK_PORTFOLIOS = {
    'sp500': {
        'name': 'S&P 500',
        'description': '美國標準普爾500指數成分股',
        'source': 'predefined',
        'tickers': [
            # 科技股 - 主要大型科技公司
            'AAPL', 'MSFT', 'GOOGL', 'GOOG', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX', 'ADBE',
            'CRM', 'ORCL', 'CSCO', 'AVGO', 'TXN', 'QCOM', 'IBM', 'AMD', 'INTC', 'PYPL',
            'NOW', 'AMAT', 'MU', 'KLAC', 'LRCX', 'ADI', 'MRVL', 'FTNT', 'SNPS', 'CDNS',
            'INTU', 'WDAY', 'TEAM', 'DDOG', 'CRWD', 'ZM', 'DOCU', 'OKTA', 'TWLO', 'SPLK',
            
            # 金融股 - 銀行、保險、金融服務
            'BRK-B', 'JPM', 'BAC', 'WFC', 'GS', 'MS', 'C', 'AXP', 'USB', 'PNC',
            'TFC', 'COF', 'SCHW', 'BLK', 'CB', 'MMC', 'ICE', 'CME', 'SPGI', 'MCO',
            'AON', 'AJG', 'TRV', 'ALL', 'MET', 'PRU', 'AFL', 'AIG', 'HIG', 'PGR',
            'FIS', 'FISV', 'MA', 'V', 'DFS', 'SYF', 'WU', 'AFRM', 'LC', 'UPST',
            
            # 醫療保健 - 製藥、醫療設備、生技
            'UNH', 'JNJ', 'PFE', 'ABBV', 'MRK', 'TMO', 'ABT', 'LLY', 'BMY', 'AMGN',
            'GILD', 'MDT', 'ISRG', 'DHR', 'SYK', 'BSX', 'REGN', 'VRTX', 'BIIB', 'ZTS',
            'ILMN', 'MRNA', 'DXCM', 'ALGN', 'IQV', 'A', 'EW', 'HOLX', 'TECH', 'PKI',
            'CTLT', 'BDX', 'BAX', 'MTD', 'XRAY', 'ZBH', 'STE', 'RMD', 'PODD', 'TDOC',
            
            # 消費品 - 零售、食品飲料、消費用品
            'PG', 'KO', 'PEP', 'WMT', 'COST', 'HD', 'MCD', 'SBUX', 'NKE', 'LOW',
            'TGT', 'CVS', 'WBA', 'KMB', 'CL', 'GIS', 'K', 'CAG', 'CPB', 'CLX',
            'KHC', 'MDLZ', 'MNST', 'KDP', 'HSY', 'SJM', 'HRL', 'MKC', 'CHD', 'EL',
            'YUM', 'QSR', 'CMG', 'DPZ', 'WING', 'TXRH', 'SHAK', 'CAKE', 'BJRI', 'DRI',
            
            # 工業股 - 航空航太、運輸、機械
            'BA', 'HON', 'UPS', 'CAT', 'MMM', 'GE', 'LMT', 'RTX', 'DE', 'FDX',
            'UNP', 'CSX', 'NSC', 'LUV', 'DAL', 'AAL', 'UAL', 'WM', 'RSG', 'EMR',
            'ETN', 'PH', 'ROK', 'DOV', 'FTV', 'XYL', 'CARR', 'OTIS', 'PWR', 'GNRC',
            'ITW', 'FAST', 'PAYX', 'CHRW', 'EXPD', 'JBHT', 'KNX', 'ODFL', 'LSTR', 'HUBG',
            
            # 能源股 - 石油天然氣、煉油
            'XOM', 'CVX', 'COP', 'EOG', 'SLB', 'MPC', 'VLO', 'PSX', 'OXY', 'HAL',
            'BKR', 'DVN', 'FANG', 'APA', 'MRO', 'NOV', 'RIG', 'VAL', 'HP', 'CHK',
            'EQT', 'KNTK', 'NFG', 'CNX', 'AR', 'CLR', 'CDEV', 'SM', 'WPX', 'MTDR',
            
            # 公用事業 - 電力、天然氣、水務
            'NEE', 'DUK', 'SO', 'AEP', 'EXC', 'XEL', 'SRE', 'D', 'PEG', 'EIX',
            'PCG', 'ED', 'ETR', 'WEC', 'CMS', 'DTE', 'PPL', 'AES', 'LNT', 'NI',
            'ES', 'EVRG', 'CNP', 'ATO', 'NWE', 'POR', 'AWK', 'WTRG', 'CWT', 'AQUA',
            
            # 材料股 - 化工、鋼鐵、包裝
            'LIN', 'APD', 'ECL', 'DD', 'DOW', 'PPG', 'SHW', 'FCX', 'NUE', 'VMC',
            'MLM', 'NEM', 'GOLD', 'FMC', 'LYB', 'CE', 'CF', 'MOS', 'ALB', 'IFF',
            'PKG', 'BALL', 'CCL', 'AMCR', 'IP', 'WRK', 'SON', 'SEE', 'AVY', 'SLGN',
            
            # 房地產 - REITs、房地產開發
            'AMT', 'PLD', 'CCI', 'EQIX', 'SPG', 'O', 'WELL', 'DLR', 'PSA', 'EQR',
            'VTR', 'SBAC', 'AVB', 'EXR', 'UDR', 'ESS', 'MAA', 'CPT', 'ARE', 'HST',
            'REG', 'BXP', 'VNO', 'KIM', 'ACC', 'FRT', 'SLG', 'PEI', 'SKT', 'DEI',
            
            # 通訊服務 - 電信、媒體、娛樂
            'VZ', 'T', 'TMUS', 'CHTR', 'CMCSA', 'DIS', 'TTWO', 'EA', 'ATVI', 'ZNGA',
            'SNAP', 'PINS', 'MTCH', 'IAC', 'DISCA', 'DISCB', 'DISCK', 'FOXA', 'FOX', 'PARA',
            'WBD', 'OMC', 'IPG', 'RBLX', 'U', 'LUMN', 'SIRI', 'LYV', 'MSG', 'MSGN',
            
            # 消費者服務 - 旅遊、餐飲、電商
            'BKNG', 'MAR', 'HLT', 'MGM', 'LVS', 'WYNN', 'CZR', 'PENN', 'EXPE', 'TRIP',
            'UBER', 'LYFT', 'DASH', 'ABNB', 'EBAY', 'ETSY', 'W', 'CHWY', 'CVNA', 'CARG',
            
            # 其他重要大型股
            'BRK-A', 'TSM', 'ASML', 'BABA', 'PDD', 'JD', 'BIDU', 'NIO', 'LI', 'XPEV',
            'SHOP', 'SQ', 'COIN', 'HOOD', 'SOFI', 'UPST', 'AFRM', 'PLTR', 'SNOW', 'NET'
        ]
    },
    'faang_plus': {
        'name': '美國科技7巨頭',
        'description': 'FAANG+ 美國科技巨頭公司',
        'source': 'predefined',
        'tickers': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA']
    },
    'taiwan_top50': {
        'name': '台灣股市前50',
        'description': '台灣證券交易所市值前50大公司',
        'source': 'predefined',
        'tickers': [
            # 台積電、聯發科等大型股
            '2330.TW', '2317.TW', '2454.TW', '2308.TW',
            '2412.TW', '2303.TW', '1303.TW', '1301.TW', '2881.TW',
            '2002.TW', '2886.TW', '2207.TW', '2891.TW', '2884.TW',
            '3711.TW', '2609.TW', '2882.TW', '2892.TW', '1216.TW',
            '2357.TW', '2408.TW', '1101.TW', '2382.TW', '2395.TW',
            '2474.TW', '3008.TW', '2912.TW', '6505.TW', '2890.TW',
            '2801.TW', '3045.TW', '2888.TW', '1102.TW', '2027.TW',
            '2385.TW', '2883.TW', '2324.TW', '6669.TW', '2301.TW',
            '1326.TW', '2880.TW', '2887.TW', '2002.TW', '4938.TW',
            '2409.TW', '2347.TW', '1802.TW', '3231.TW', '2542.TW'
        ]
    }
}


class MultiMarketDataFetcher:
    """多市場數據抓取器 - 支持不同股票組合"""
    
    def __init__(self, portfolio_type: str = 'sp500'):
        self.portfolio_type = portfolio_type
        self.portfolio_config = STOCK_PORTFOLIOS.get(portfolio_type)
        if not self.portfolio_config:
            raise ValueError(f"不支援的投資組合類型: {portfolio_type}")
        
        self.tickers = []
        self.financial_data = {}
        self.rate_limiter = RateLimiter(max_calls_per_second=API_SETTINGS['safe_rate_per_second'])
        
    def get_portfolio_name(self) -> str:
        """獲取投資組合名稱"""
        return self.portfolio_config['name']
    
    def get_portfolio_description(self) -> str:
        """獲取投資組合描述"""
        return self.portfolio_config['description']
    
    def get_tickers(self) -> List[str]:
        """根據投資組合類型獲取股票代碼列表"""
        if self.portfolio_config['source'] == 'predefined':
            return self.portfolio_config['tickers']
        else:
            raise ValueError(f"不支援的數據來源: {self.portfolio_config['source']}")
    
    def fetch_financial_data(self, max_stocks: Optional[int] = None) -> pd.DataFrame:
        """獲取財務數據"""
        tickers = self.get_tickers()
        
        if max_stocks:
            tickers = tickers[:max_stocks]
        
        logging.info(f"開始獲取 {self.get_portfolio_name()} 的財務數據，共 {len(tickers)} 支股票")
        
        all_data = []
        failed_tickers = []
        
        for i, ticker in enumerate(tickers):
            try:
                self.rate_limiter.wait_if_needed()
                
                # 顯示進度
                progress = (i + 1) / len(tickers)
                logging.info(f"處理 {ticker} ({i+1}/{len(tickers)}, {progress:.1%})")
                
                stock_data = self._get_stock_data(ticker)
                if stock_data:
                    all_data.append(stock_data)
                else:
                    failed_tickers.append(ticker)
                    
            except Exception as e:
                logging.error(f"處理 {ticker} 時發生錯誤: {e}")
                failed_tickers.append(ticker)
                continue
        
        if failed_tickers:
            logging.warning(f"以下 {len(failed_tickers)} 個股票獲取失敗: {failed_tickers}")
        
        df = pd.DataFrame(all_data)
        logging.info(f"成功獲取 {len(df)} 個股票的數據")
        
        return df
    
    def get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """獲取單一股票的財務數據（公開方法）"""
        self.rate_limiter.wait_if_needed()
        return self._get_stock_data(ticker)
    
    def _get_stock_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        """獲取單一股票的財務數據"""
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            
            if not info or info.get('regularMarketPrice') is None:
                return None
            
            # 構建股票數據字典
            stock_data = {
                'symbol': ticker,
                'ticker': ticker,  # 為了向後兼容
                'name': info.get('longName', ticker),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown'),
                'market_cap': info.get('marketCap'),
                'current_price': info.get('regularMarketPrice'),
                'pe_ratio': info.get('trailingPE'),
                'forward_pe': info.get('forwardPE'),
                'pb_ratio': info.get('priceToBook'),
                'ps_ratio': info.get('priceToSalesTrailing12Months'),
                'peg_ratio': info.get('pegRatio'),
                'debt_to_equity': info.get('debtToEquity'),
                'current_ratio': info.get('currentRatio'),
                'roe': info.get('returnOnEquity'),
                'roa': info.get('returnOnAssets'),
                'profit_margin': info.get('profitMargins'),
                'revenue_growth': info.get('revenueGrowth'),
                'earnings_growth': info.get('earningsGrowth'),
                'dividend_yield': info.get('dividendYield'),
                'dividend_rate': info.get('dividendRate'),
                'payout_ratio': info.get('payoutRatio'),
                'beta': info.get('beta'),
                'fifty_two_week_high': info.get('fiftyTwoWeekHigh'),
                'fifty_two_week_low': info.get('fiftyTwoWeekLow'),
                'recommendation': info.get('recommendationKey'),
                'target_price': info.get('targetMeanPrice'),
                'enterprise_value': info.get('enterpriseValue'),
                'ebitda': info.get('ebitda'),
                'free_cash_flow': info.get('freeCashflow')
            }
            
            return clean_financial_data(stock_data)
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 數據失敗: {e}")
            return None


class SP500DataFetcher:
    """S&P 500 數據抓取器 - 向後兼容性包裝器"""
    
    def __init__(self):
        self.multi_fetcher = MultiMarketDataFetcher('sp500')
        self.tickers = []
        self.financial_data = {}
        self.rate_limiter = self.multi_fetcher.rate_limiter
        
    def get_sp500_tickers(self) -> List[str]:
        """獲取 S&P 500 成分股列表"""
        return self.multi_fetcher.get_tickers()
    
    def fetch_financial_data(self, max_stocks: Optional[int] = None) -> pd.DataFrame:
        """獲取財務數據"""
        return self.multi_fetcher.fetch_financial_data(max_stocks)
    
    def get_stock_info(self, ticker: str) -> Dict[str, Any]:
        """獲取單一股票的詳細資訊"""
        return self.multi_fetcher._get_stock_data(ticker)
    
    def batch_fetch_stock_data(self, tickers: Optional[List[str]] = None, 
                              max_stocks: Optional[int] = None) -> pd.DataFrame:
        """批量獲取股票數據"""
        return self.fetch_financial_data(max_stocks)
    
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
