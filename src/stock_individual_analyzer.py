"""
個股綜合分析器 - 專注於新聞面、技術面、籌碼面分析
"""

import pandas as pd
import numpy as np
import yfinance as yf
import requests
from bs4 import BeautifulSoup
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import re
import urllib.parse


class StockIndividualAnalyzer:
    """個股綜合分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def analyze_stock_comprehensive(self, ticker: str) -> Dict[str, Any]:
        """
        對單一股票進行全面分析
        
        Args:
            ticker: 股票代號
            
        Returns:
            包含新聞面、技術面、籌碼面分析的綜合結果
        """
        self.logger.info(f"開始分析股票: {ticker}")
        
        # 獲取基本股票信息
        stock = yf.Ticker(ticker)
        info = stock.info
        
        result = {
            'ticker': ticker,
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'current_price': info.get('currentPrice', 0),
            'market_cap': info.get('marketCap', 0)
        }
        
        # 1. 新聞面分析 (權重: 50%)
        self.logger.info(f"分析 {ticker} 新聞面...")
        news_analysis = self.analyze_news_sentiment(ticker, info.get('longName', ticker))
        result.update(news_analysis)
        
        # 2. 技術面分析 (權重: 30%)
        self.logger.info(f"分析 {ticker} 技術面...")
        technical_analysis = self.analyze_technical_indicators(ticker)
        result.update(technical_analysis)
        
        # 3. 籌碼面分析 (權重: 20%)
        self.logger.info(f"分析 {ticker} 籌碼面...")
        chip_analysis = self.analyze_chip_distribution(ticker, stock)
        result.update(chip_analysis)
        
        # 4. 綜合評分計算
        comprehensive_score = self.calculate_comprehensive_score(result)
        recommendation = self.get_investment_recommendation_by_score(comprehensive_score, result)
        
        # 更新結果字典，使用英文鍵名以配合 Streamlit 應用
        result.update({
            'overall_score': comprehensive_score,
            'recommendation': recommendation,
            'news_score': result.get('news_sentiment_score', 0),
            'technical_score': result.get('technical_score', 0),
            'chip_score': result.get('chip_score', 0),
            'news_analysis': {
                'sentiment_score': result.get('news_sentiment_score', 0),
                'analyzed_articles': result.get('news_volume', 0),
                'average_sentiment': result.get('average_sentiment', 0),
                'keywords': result.get('key_topics', []),
                'recent_headlines': result.get('recent_headlines', [])
            },
            'technical_analysis': {
                'rsi': result.get('rsi', 0),
                'macd': result.get('macd', 0),
                'ma_signal': result.get('trend_direction', 'neutral'),
                'moving_averages': {
                    'ma_20': result.get('ma_20', 0),
                    'ma_50': result.get('ma_50', 0),
                    'ma_200': result.get('ma_200', 0),
                    'current_price': result.get('current_price', 0)
                }
            },
            'chip_analysis': {
                'institutional_ownership': result.get('institutional_ownership', 0),
                'insider_ownership': result.get('insider_ownership', 0),
                'short_ratio': result.get('short_ratio', 0),
                'percent_held_by_institutions': result.get('institutional_ownership', 0),
                'ownership_score': result.get('chip_score', 0)
            },
            'basic_info': {
                'current_price': result.get('current_price', 0),
                'market_cap': result.get('market_cap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'beta': info.get('beta', 0),
                'volatility': result.get('volatility', 0)
            }
        })
        
        self.logger.info(f"完成 {ticker} 綜合分析，總分: {comprehensive_score}")
        return result
    
    def analyze_news_sentiment(self, ticker: str, company_name: str) -> Dict[str, Any]:
        """
        分析新聞情感和重要性
        
        Returns:
            Dict containing:
            - news_sentiment_score: 新聞情感評分 (0-100)
            - news_volume: 新聞數量
            - recent_news: 最近新聞列表
            - sentiment_trend: 情感趨勢
            - news_impact_score: 新聞影響力評分
        """
        news_data = {
            'news_sentiment_score': 50,  # 預設中性
            'news_volume': 0,
            'recent_news': [],
            'sentiment_trend': 'neutral',
            'news_impact_score': 50,
            'positive_news_count': 0,
            'negative_news_count': 0,
            'neutral_news_count': 0
        }
        
        try:
            # 1. 從Yahoo Finance獲取新聞
            yahoo_news = self.get_yahoo_finance_news(ticker)
            
            # 2. 從Google News獲取新聞
            google_news = self.get_google_news(ticker, company_name)
            
            # 3. 合併新聞源
            all_news = yahoo_news + google_news
            
            if all_news:
                # 分析新聞情感
                sentiment_analysis = self.analyze_news_sentiment_detailed(all_news)
                news_data.update(sentiment_analysis)
                
                # 保存最近新聞
                news_data['recent_news'] = all_news[:10]  # 最近10條新聞
                news_data['news_volume'] = len(all_news)
                
                self.logger.info(f"分析了 {len(all_news)} 條 {ticker} 相關新聞")
            else:
                self.logger.warning(f"未找到 {ticker} 相關新聞")
                
        except Exception as e:
            self.logger.error(f"新聞分析出錯: {e}")
        
        return news_data
    
    def get_yahoo_finance_news(self, ticker: str) -> List[Dict]:
        """從Yahoo Finance獲取新聞"""
        news_list = []
        
        try:
            # 使用yfinance獲取新聞
            stock = yf.Ticker(ticker)
            news_data = stock.news
            
            for news_item in news_data[:15]:  # 取前15條新聞
                news_list.append({
                    'title': news_item.get('title', ''),
                    'summary': news_item.get('summary', ''),
                    'url': news_item.get('link', ''),
                    'publish_time': datetime.fromtimestamp(news_item.get('providerPublishTime', 0)),
                    'source': 'Yahoo Finance',
                    'publisher': news_item.get('publisher', 'Unknown')
                })
                
        except Exception as e:
            self.logger.error(f"Yahoo Finance新聞獲取失敗: {e}")
        
        return news_list
    
    def get_google_news(self, ticker: str, company_name: str) -> List[Dict]:
        """從Google News獲取新聞"""
        news_list = []
        
        try:
            # 構建搜索查詢
            search_terms = [ticker, company_name.split()[0]]  # 使用股票代號和公司名稱第一個詞
            
            for term in search_terms:
                if not term:
                    continue
                    
                # Google News RSS feed
                query = urllib.parse.quote(f'{term} stock')
                url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
                
                try:
                    response = self.session.get(url, timeout=10)
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'xml')
                        items = soup.find_all('item')[:10]  # 取前10條
                        
                        for item in items:
                            title = item.title.text if item.title else ''
                            description = item.description.text if item.description else ''
                            link = item.link.text if item.link else ''
                            pub_date = item.pubDate.text if item.pubDate else ''
                            
                            # 解析發布時間
                            try:
                                publish_time = datetime.strptime(pub_date, '%a, %d %b %Y %H:%M:%S %Z')
                            except:
                                publish_time = datetime.now() - timedelta(days=1)
                            
                            news_list.append({
                                'title': title,
                                'summary': description,
                                'url': link,
                                'publish_time': publish_time,
                                'source': 'Google News',
                                'publisher': 'Various'
                            })
                    
                    time.sleep(1)  # 避免請求過快
                    
                except Exception as e:
                    self.logger.error(f"Google News請求失敗: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Google News獲取失敗: {e}")
        
        return news_list
    
    def analyze_news_sentiment_detailed(self, news_list: List[Dict]) -> Dict[str, Any]:
        """詳細分析新聞情感"""
        if not news_list:
            return {
                'news_sentiment_score': 50,
                'sentiment_trend': 'neutral',
                'news_impact_score': 50,
                'positive_news_count': 0,
                'negative_news_count': 0,
                'neutral_news_count': 0
            }
        
        sentiment_scores = []
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        # 情感關鍵詞定義
        positive_keywords = [
            'beat', 'exceed', 'strong', 'growth', 'profit', 'revenue', 'upgrade', 
            'buy', 'bullish', 'positive', 'gain', 'rise', 'surge', 'boost',
            'outperform', 'success', 'expand', 'increase', 'good', 'excellent'
        ]
        
        negative_keywords = [
            'miss', 'decline', 'loss', 'drop', 'fall', 'downgrade', 'sell', 
            'bearish', 'negative', 'concern', 'risk', 'warn', 'cut', 'reduce',
            'underperform', 'challenge', 'problem', 'issue', 'bad', 'poor'
        ]
        
        for news in news_list:
            text = f"{news.get('title', '')} {news.get('summary', '')}"
            text_lower = text.lower()
            
            # 基於關鍵詞的情感分析
            positive_score = sum(1 for keyword in positive_keywords if keyword in text_lower)
            negative_score = sum(1 for keyword in negative_keywords if keyword in text_lower)
            
            # 計算情感評分 (0-100)
            if positive_score > negative_score:
                sentiment = 70 + min(positive_score * 5, 30)  # 70-100
                positive_count += 1
            elif negative_score > positive_score:
                sentiment = 30 - min(negative_score * 5, 30)  # 0-30
                negative_count += 1
            else:
                sentiment = 50  # 中性
                neutral_count += 1
            
            # 根據新聞時效性調整權重
            days_old = (datetime.now() - news.get('publish_time', datetime.now())).days
            time_weight = max(0.1, 1 - (days_old / 7))  # 7天內權重較高
            
            sentiment_scores.append(sentiment * time_weight)
        
        # 計算平均情感評分
        avg_sentiment = np.mean(sentiment_scores) if sentiment_scores else 50
        
        # 計算情感趨勢
        if avg_sentiment > 60:
            trend = 'positive'
        elif avg_sentiment < 40:
            trend = 'negative'
        else:
            trend = 'neutral'
        
        # 計算新聞影響力評分 (基於新聞數量和情感強度)
        news_volume_factor = min(len(news_list) / 20, 1)  # 20條新聞為滿分
        sentiment_intensity = abs(avg_sentiment - 50) / 50  # 情感強度
        impact_score = 50 + (sentiment_intensity * news_volume_factor * 50)
        
        # 提取關鍵主題
        key_topics = self.extract_key_topics(news_list)
        
        # 收集新聞標題
        recent_headlines = [news.get('title', '')[:100] for news in news_list[:5]]  # 前5個標題，限制長度
        
        return {
            'news_sentiment_score': round(avg_sentiment, 1),
            'sentiment_trend': trend,
            'news_impact_score': round(impact_score, 1),
            'positive_news_count': positive_count,
            'negative_news_count': negative_count,
            'neutral_news_count': neutral_count,
            'average_sentiment': round((avg_sentiment - 50) / 50, 3),  # 標準化到 -1 到 1
            'key_topics': key_topics,
            'recent_headlines': recent_headlines
        }
    
    def extract_key_topics(self, news_list: List[Dict]) -> List[str]:
        """提取新聞關鍵主題"""
        # 簡單的關鍵詞提取
        topic_keywords = []
        important_words = [
            'earnings', 'revenue', 'profit', 'loss', 'acquisition', 'merger',
            'product', 'launch', 'partnership', 'investment', 'expansion',
            'lawsuit', 'regulation', 'approval', 'dividend', 'stock split',
            'guidance', 'forecast', 'outlook', 'upgrade', 'downgrade'
        ]
        
        for news in news_list:
            text = f"{news.get('title', '')} {news.get('summary', '')}".lower()
            for word in important_words:
                if word in text and word not in topic_keywords:
                    topic_keywords.append(word)
                    
                if len(topic_keywords) >= 10:  # 限制關鍵詞數量
                    break
        
        return topic_keywords
    
    def analyze_technical_indicators(self, ticker: str) -> Dict[str, Any]:
        """
        分析技術指標
        
        Returns:
            Dict containing technical analysis results
        """
        technical_data = {
            'technical_score': 50,
            'trend_direction': 'neutral',
            'support_level': 0,
            'resistance_level': 0,
            'rsi': 50,
            'macd_signal': 'neutral',
            'volume_trend': 'neutral',
            'price_momentum': 'neutral'
        }
        
        try:
            # 獲取歷史數據
            stock = yf.Ticker(ticker)
            hist = stock.history(period="3mo")  # 3個月數據
            
            if hist.empty:
                return technical_data
            
            # 計算技術指標
            close_prices = hist['Close']
            volumes = hist['Volume']
            
            # 1. 移動平均線分析
            ma_analysis = self.calculate_moving_averages(close_prices)
            technical_data.update(ma_analysis)
            
            # 2. RSI計算
            rsi = self.calculate_rsi(close_prices)
            technical_data['rsi'] = round(rsi, 2)
            
            # 3. MACD分析
            macd_analysis = self.calculate_macd(close_prices)
            technical_data.update(macd_analysis)
            
            # 4. 支撐阻力位
            support_resistance = self.calculate_support_resistance(close_prices)
            technical_data.update(support_resistance)
            
            # 5. 成交量分析
            volume_analysis = self.analyze_volume_trend(volumes, close_prices)
            technical_data.update(volume_analysis)
            
            # 6. 綜合技術評分
            technical_data['technical_score'] = self.calculate_technical_score(technical_data)
            
        except Exception as e:
            self.logger.error(f"技術分析出錯: {e}")
        
        return technical_data
    
    def calculate_moving_averages(self, prices: pd.Series) -> Dict[str, Any]:
        """計算移動平均線"""
        current_price = prices.iloc[-1]
        
        # 計算不同週期的移動平均
        ma5 = prices.rolling(window=5).mean().iloc[-1]
        ma10 = prices.rolling(window=10).mean().iloc[-1]
        ma20 = prices.rolling(window=20).mean().iloc[-1]
        ma50 = prices.rolling(window=50).mean().iloc[-1] if len(prices) >= 50 else ma20
        ma200 = prices.rolling(window=200).mean().iloc[-1] if len(prices) >= 200 else ma50
        
        # 判斷趨勢
        if current_price > ma5 > ma10 > ma20:
            trend = 'strong_bullish'
        elif current_price > ma5 and ma5 > ma20:
            trend = 'bullish'
        elif current_price < ma5 < ma10 < ma20:
            trend = 'strong_bearish'
        elif current_price < ma5 and ma5 < ma20:
            trend = 'bearish'
        else:
            trend = 'neutral'
        
        return {
            'ma5': round(ma5, 2),
            'ma10': round(ma10, 2),
            'ma20': round(ma20, 2),
            'ma50': round(ma50, 2),
            'ma200': round(ma200, 2),
            'trend_direction': trend,
            'price_vs_ma20': round((current_price - ma20) / ma20 * 100, 2),
            'current_price': round(current_price, 2)
        }
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> float:
        """計算RSI指標"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi.iloc[-1] if not pd.isna(rsi.iloc[-1]) else 50
    
    def calculate_macd(self, prices: pd.Series) -> Dict[str, Any]:
        """計算MACD指標"""
        exp1 = prices.ewm(span=12).mean()
        exp2 = prices.ewm(span=26).mean()
        macd_line = exp1 - exp2
        signal_line = macd_line.ewm(span=9).mean()
        histogram = macd_line - signal_line
        
        # 判斷MACD信號
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        prev_macd = macd_line.iloc[-2] if len(macd_line) > 1 else current_macd
        prev_signal = signal_line.iloc[-2] if len(signal_line) > 1 else current_signal
        
        if current_macd > current_signal and prev_macd <= prev_signal:
            macd_signal = 'bullish_crossover'
        elif current_macd < current_signal and prev_macd >= prev_signal:
            macd_signal = 'bearish_crossover'
        elif current_macd > current_signal:
            macd_signal = 'bullish'
        elif current_macd < current_signal:
            macd_signal = 'bearish'
        else:
            macd_signal = 'neutral'
        
        return {
            'macd': round(current_macd, 4),  # 添加這個鍵供 Streamlit 使用
            'macd_line': round(current_macd, 4),
            'macd_signal_line': round(current_signal, 4),
            'macd_histogram': round(histogram.iloc[-1], 4),
            'macd_signal': macd_signal
        }
    
    def calculate_support_resistance(self, prices: pd.Series) -> Dict[str, Any]:
        """計算支撐阻力位"""
        current_price = prices.iloc[-1]
        
        # 尋找近期高低點
        recent_prices = prices.tail(20)  # 最近20個交易日
        
        # 簡單的支撐阻力計算
        resistance = recent_prices.max()
        support = recent_prices.min()
        
        # 更精確的支撐阻力（基於價格聚集度）
        price_levels = {}
        for price in recent_prices:
            rounded_price = round(price, 1)
            price_levels[rounded_price] = price_levels.get(rounded_price, 0) + 1
        
        # 找出出現頻率較高的價格水平
        if price_levels:
            sorted_levels = sorted(price_levels.items(), key=lambda x: x[1], reverse=True)
            
            # 找支撐位（低於當前價格的最高頻價位）
            support_candidates = [level for level, count in sorted_levels if level < current_price]
            if support_candidates:
                support = max(support_candidates)
            
            # 找阻力位（高於當前價格的最高頻價位）
            resistance_candidates = [level for level, count in sorted_levels if level > current_price]
            if resistance_candidates:
                resistance = min(resistance_candidates)
        
        return {
            'support_level': round(support, 2),
            'resistance_level': round(resistance, 2),
            'distance_to_support': round((current_price - support) / current_price * 100, 2),
            'distance_to_resistance': round((resistance - current_price) / current_price * 100, 2)
        }
    
    def analyze_volume_trend(self, volumes: pd.Series, prices: pd.Series) -> Dict[str, Any]:
        """分析成交量趨勢"""
        # 計算平均成交量
        avg_volume = volumes.rolling(window=20).mean()
        current_volume = volumes.iloc[-1]
        recent_avg_volume = avg_volume.iloc[-1]
        
        # 計算價量關係
        price_change = (prices.iloc[-1] - prices.iloc[-5]) / prices.iloc[-5]  # 5日價格變化
        volume_change = (current_volume - volumes.iloc[-5:-1].mean()) / volumes.iloc[-5:-1].mean()  # 成交量變化
        
        # 判斷成交量趨勢
        if current_volume > recent_avg_volume * 1.5:
            if price_change > 0:
                volume_trend = 'bullish_breakout'
            else:
                volume_trend = 'bearish_selloff'
        elif current_volume > recent_avg_volume * 1.2:
            volume_trend = 'above_average'
        elif current_volume < recent_avg_volume * 0.7:
            volume_trend = 'below_average'
        else:
            volume_trend = 'normal'
        
        return {
            'current_volume': int(current_volume),
            'avg_volume_20d': int(recent_avg_volume),
            'volume_ratio': round(current_volume / recent_avg_volume, 2),
            'volume_trend': volume_trend,
            'price_volume_correlation': 'positive' if price_change * volume_change > 0 else 'negative'
        }
    
    def calculate_technical_score(self, technical_data: Dict) -> float:
        """計算綜合技術評分"""
        score = 50  # 基礎分數
        
        # 趨勢評分 (權重: 30%)
        trend = technical_data.get('trend_direction', 'neutral')
        if trend == 'strong_bullish':
            score += 15
        elif trend == 'bullish':
            score += 10
        elif trend == 'strong_bearish':
            score -= 15
        elif trend == 'bearish':
            score -= 10
        
        # RSI評分 (權重: 20%)
        rsi = technical_data.get('rsi', 50)
        if 30 <= rsi <= 70:  # 正常範圍
            score += 10
        elif rsi < 30:  # 超賣
            score += 5  # 可能反彈
        elif rsi > 70:  # 超買
            score -= 5  # 可能回調
        
        # MACD評分 (權重: 25%)
        macd_signal = technical_data.get('macd_signal', 'neutral')
        if macd_signal == 'bullish_crossover':
            score += 12
        elif macd_signal == 'bullish':
            score += 8
        elif macd_signal == 'bearish_crossover':
            score -= 12
        elif macd_signal == 'bearish':
            score -= 8
        
        # 成交量評分 (權重: 15%)
        volume_trend = technical_data.get('volume_trend', 'normal')
        if volume_trend == 'bullish_breakout':
            score += 8
        elif volume_trend == 'above_average':
            score += 4
        elif volume_trend == 'bearish_selloff':
            score -= 8
        
        # 支撐阻力評分 (權重: 10%)
        distance_to_support = technical_data.get('distance_to_support', 0)
        distance_to_resistance = technical_data.get('distance_to_resistance', 0)
        
        if distance_to_support < 2:  # 接近支撐
            score += 3
        if distance_to_resistance > 5:  # 遠離阻力
            score += 2
        
        return max(0, min(100, round(score, 1)))
    
    def analyze_chip_distribution(self, ticker: str, stock_obj) -> Dict[str, Any]:
        """
        分析籌碼面 (股權結構、機構持股、內部人交易等)
        
        Returns:
            Dict containing chip analysis results
        """
        chip_data = {
            'chip_score': 50,
            'institutional_ownership': 0,
            'insider_ownership': 0,
            'short_ratio': 0,
            'shares_outstanding': 0,
            'float_shares': 0,
            'ownership_concentration': 'medium'
        }
        
        try:
            info = stock_obj.info
            
            # 1. 機構持股分析
            institutional_ownership = info.get('heldPercentInstitutions', 0)
            if institutional_ownership:
                chip_data['institutional_ownership'] = round(institutional_ownership * 100, 2)
            
            # 2. 內部人持股
            insider_ownership = info.get('heldPercentInsiders', 0)
            if insider_ownership:
                chip_data['insider_ownership'] = round(insider_ownership * 100, 2)
            
            # 3. 做空比例
            short_ratio = info.get('shortRatio', 0)
            chip_data['short_ratio'] = short_ratio
            
            # 4. 股本結構
            shares_outstanding = info.get('sharesOutstanding', 0)
            float_shares = info.get('floatShares', 0)
            
            chip_data['shares_outstanding'] = shares_outstanding
            chip_data['float_shares'] = float_shares
            
            # 5. 分析股權集中度
            if institutional_ownership > 0.7:  # 70%以上機構持股
                concentration = 'high'
            elif institutional_ownership > 0.4:  # 40-70%機構持股
                concentration = 'medium'
            else:
                concentration = 'low'
            
            chip_data['ownership_concentration'] = concentration
            
            # 6. 獲取大股東信息
            major_holders = self.get_major_holders_info(stock_obj)
            chip_data.update(major_holders)
            
            # 7. 添加更多籌碼指標
            additional_metrics = self.get_additional_chip_metrics(info)
            chip_data.update(additional_metrics)
            
            # 8. 計算籌碼評分
            chip_data['chip_score'] = self.calculate_chip_score(chip_data)
            
        except Exception as e:
            self.logger.error(f"籌碼分析出錯: {e}")
        
        return chip_data
    
    def get_major_holders_info(self, stock_obj) -> Dict[str, Any]:
        """獲取大股東信息"""
        holders_info = {
            'top_institutional_holders': [],
            'insider_transactions': [],
            'institutional_ownership_trend': 'stable'
        }
        
        try:
            # 獲取機構持股信息
            institutional_holders = stock_obj.institutional_holders
            if institutional_holders is not None and not institutional_holders.empty:
                top_holders = institutional_holders.head(5)
                holders_list = []
                
                for idx, holder in top_holders.iterrows():
                    holders_list.append({
                        'holder': holder.get('Holder', 'Unknown'),
                        'shares': holder.get('Shares', 0),
                        'percentage': holder.get('% Out', 0),
                        'value': holder.get('Value', 0)
                    })
                
                holders_info['top_institutional_holders'] = holders_list
            
            # 獲取內部人交易信息
            insider_purchases = stock_obj.insider_purchases
            if insider_purchases is not None and not insider_purchases.empty:
                recent_transactions = insider_purchases.head(5)
                transactions_list = []
                
                for idx, transaction in recent_transactions.iterrows():
                    transactions_list.append({
                        'insider': transaction.get('Insider', 'Unknown'),
                        'position': transaction.get('Position', 'Unknown'),
                        'transaction': transaction.get('Transaction', 'Unknown'),
                        'shares': transaction.get('#Shares', 0),
                        'value': transaction.get('Value ($)', 0)
                    })
                
                holders_info['insider_transactions'] = transactions_list
            
        except Exception as e:
            self.logger.error(f"獲取股東信息出錯: {e}")
        
        return holders_info
    
    def get_additional_chip_metrics(self, info: Dict) -> Dict[str, Any]:
        """獲取額外的籌碼指標"""
        additional_metrics = {}
        
        try:
            # 市值相關
            market_cap = info.get('marketCap', 0)
            if market_cap > 0:
                if market_cap > 200e9:  # 大於2000億
                    cap_category = '大型股'
                elif market_cap > 10e9:  # 100-2000億
                    cap_category = '中型股'
                else:
                    cap_category = '小型股'
                additional_metrics['market_cap_category'] = cap_category
            
            # 流動性指標
            avg_volume = info.get('averageVolume', 0)
            additional_metrics['average_daily_volume'] = avg_volume
            
            # 股息相關
            dividend_yield = info.get('dividendYield', 0)
            if dividend_yield:
                additional_metrics['dividend_yield'] = round(dividend_yield * 100, 2)
            
            # Beta 值
            beta = info.get('beta', 1.0)
            additional_metrics['beta'] = beta
            
            # 52週高低點
            fifty_two_week_high = info.get('fiftyTwoWeekHigh', 0)
            fifty_two_week_low = info.get('fiftyTwoWeekLow', 0)
            current_price = info.get('currentPrice', 0)
            
            if fifty_two_week_high and fifty_two_week_low and current_price:
                price_position = (current_price - fifty_two_week_low) / (fifty_two_week_high - fifty_two_week_low)
                additional_metrics['price_position_52w'] = round(price_position * 100, 1)
            
            # 員工數量（如果有）
            full_time_employees = info.get('fullTimeEmployees', 0)
            if full_time_employees:
                additional_metrics['employee_count'] = full_time_employees
                
        except Exception as e:
            self.logger.error(f"獲取額外籌碼指標失敗: {e}")
        
        return additional_metrics
    
    def calculate_chip_score(self, chip_data: Dict) -> float:
        """計算籌碼評分"""
        score = 50  # 基礎分數
        
        # 機構持股評分 (權重: 40%)
        institutional_ownership = chip_data.get('institutional_ownership', 0)
        if 40 <= institutional_ownership <= 80:  # 理想範圍
            score += 20
        elif 20 <= institutional_ownership < 40 or 80 < institutional_ownership <= 90:
            score += 10
        elif institutional_ownership > 90:  # 過度集中
            score -= 10
        
        # 內部人持股評分 (權重: 20%)
        insider_ownership = chip_data.get('insider_ownership', 0)
        if 5 <= insider_ownership <= 25:  # 適度內部人持股
            score += 10
        elif 1 <= insider_ownership < 5:
            score += 5
        elif insider_ownership > 25:  # 過度集中可能缺乏流動性
            score -= 5
        
        # 做空比例評分 (權重: 25%)
        short_ratio = chip_data.get('short_ratio', 0)
        if short_ratio < 3:  # 低做空比例
            score += 12
        elif 3 <= short_ratio <= 5:
            score += 5
        elif short_ratio > 10:  # 高做空比例
            score -= 10
        elif short_ratio > 5:
            score -= 5
        
        # 股權集中度評分 (權重: 15%)
        concentration = chip_data.get('ownership_concentration', 'medium')
        if concentration == 'medium':
            score += 8
        elif concentration == 'high':
            score += 3  # 穩定但流動性可能較差
        else:  # low
            score -= 3  # 散戶較多，波動可能較大
        
        return max(0, min(100, round(score, 1)))
    
    def calculate_comprehensive_score(self, analysis_result: Dict) -> float:
        """
        計算綜合評分
        
        權重分配：
        - 新聞面: 50%
        - 技術面: 30%
        - 籌碼面: 20%
        """
        news_score = analysis_result.get('news_sentiment_score', 50)
        news_impact = analysis_result.get('news_impact_score', 50)
        technical_score = analysis_result.get('technical_score', 50)
        chip_score = analysis_result.get('chip_score', 50)
        
        # 新聞面綜合評分 (情感評分 + 影響力評分)
        news_comprehensive = (news_score * 0.7 + news_impact * 0.3)
        
        # 加權平均
        comprehensive_score = (
            news_comprehensive * 0.5 +
            technical_score * 0.3 +
            chip_score * 0.2
        )
        
        return round(comprehensive_score, 1)
    
    def get_investment_recommendation(self, analysis_result: Dict) -> str:
        """根據綜合評分給出投資建議"""
        score = analysis_result.get('综合評分', 50)
        news_trend = analysis_result.get('sentiment_trend', 'neutral')
        technical_trend = analysis_result.get('trend_direction', 'neutral')
        
        if score >= 80:
            recommendation = "強烈買入"
        elif score >= 70:
            recommendation = "買入"
        elif score >= 60:
            recommendation = "適度買入"
        elif score >= 50:
            recommendation = "持有"
        elif score >= 40:
            recommendation = "觀望"
        elif score >= 30:
            recommendation = "減持"
        else:
            recommendation = "賣出"
        
        # 根據趨勢調整建議
        if news_trend == 'negative' and technical_trend in ['bearish', 'strong_bearish']:
            if recommendation in ['強烈買入', '買入']:
                recommendation = '適度買入'
            elif recommendation == '適度買入':
                recommendation = '觀望'
        
        return recommendation
    
    def get_investment_recommendation_by_score(self, score: float, analysis_result: Dict) -> str:
        """根據綜合評分給出投資建議（用於新版本）"""
        news_trend = analysis_result.get('sentiment_trend', 'neutral')
        technical_trend = analysis_result.get('trend_direction', 'neutral')
        
        if score >= 80:
            recommendation = "強烈買入"
        elif score >= 70:
            recommendation = "買入"
        elif score >= 60:
            recommendation = "適度買入"
        elif score >= 50:
            recommendation = "持有"
        elif score >= 40:
            recommendation = "觀望"
        elif score >= 30:
            recommendation = "減持"
        else:
            recommendation = "賣出"
        
        # 根據趨勢調整建議
        if news_trend == 'negative' and technical_trend in ['bearish', 'strong_bearish']:
            if recommendation in ['強烈買入', '買入']:
                recommendation = '適度買入'
            elif recommendation == '適度買入':
                recommendation = '觀望'
        
        return recommendation
    
    def generate_analysis_report(self, analysis_result: Dict) -> str:
        """生成分析報告"""
        ticker = analysis_result.get('ticker', 'N/A')
        company_name = analysis_result.get('company_name', 'N/A')
        
        report = []
        report.append("=" * 80)
        report.append(f"個股綜合分析報告 - {ticker}")
        report.append("=" * 80)
        report.append(f"公司名稱: {company_name}")
        report.append(f"分析時間: {analysis_result.get('analysis_time', 'N/A')}")
        report.append(f"當前股價: ${analysis_result.get('current_price', 0):.2f}")
        report.append(f"綜合評分: {analysis_result.get('综合評分', 0):.1f}/100")
        report.append(f"投資建議: {analysis_result.get('投資建議', 'N/A')}")
        report.append("")
        
        # 新聞面分析
        report.append("【新聞面分析】(權重: 50%)")
        report.append("-" * 40)
        report.append(f"新聞情感評分: {analysis_result.get('news_sentiment_score', 0):.1f}/100")
        report.append(f"情感趨勢: {analysis_result.get('sentiment_trend', 'N/A')}")
        report.append(f"新聞影響力: {analysis_result.get('news_impact_score', 0):.1f}/100")
        report.append(f"分析新聞數量: {analysis_result.get('news_volume', 0)} 條")
        report.append(f"正面新聞: {analysis_result.get('positive_news_count', 0)} 條")
        report.append(f"負面新聞: {analysis_result.get('negative_news_count', 0)} 條")
        report.append("")
        
        # 技術面分析
        report.append("【技術面分析】(權重: 30%)")
        report.append("-" * 40)
        report.append(f"技術評分: {analysis_result.get('technical_score', 0):.1f}/100")
        report.append(f"趨勢方向: {analysis_result.get('trend_direction', 'N/A')}")
        report.append(f"RSI指標: {analysis_result.get('rsi', 0):.1f}")
        report.append(f"MACD信號: {analysis_result.get('macd_signal', 'N/A')}")
        report.append(f"支撐位: ${analysis_result.get('support_level', 0):.2f}")
        report.append(f"阻力位: ${analysis_result.get('resistance_level', 0):.2f}")
        report.append(f"成交量趨勢: {analysis_result.get('volume_trend', 'N/A')}")
        report.append("")
        
        # 籌碼面分析
        report.append("【籌碼面分析】(權重: 20%)")
        report.append("-" * 40)
        report.append(f"籌碼評分: {analysis_result.get('chip_score', 0):.1f}/100")
        report.append(f"機構持股: {analysis_result.get('institutional_ownership', 0):.1f}%")
        report.append(f"內部人持股: {analysis_result.get('insider_ownership', 0):.1f}%")
        report.append(f"做空比例: {analysis_result.get('short_ratio', 0):.1f}")
        report.append(f"股權集中度: {analysis_result.get('ownership_concentration', 'N/A')}")
        report.append("")
        
        # 最近新聞
        recent_news = analysis_result.get('recent_news', [])
        if recent_news:
            report.append("【最近相關新聞】")
            report.append("-" * 40)
            for i, news in enumerate(recent_news[:5], 1):
                report.append(f"{i}. {news.get('title', 'N/A')}")
                report.append(f"   來源: {news.get('source', 'N/A')} | 時間: {news.get('publish_time', 'N/A')}")
                report.append("")
        
        return "\n".join(report)
