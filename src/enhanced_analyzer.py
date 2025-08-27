"""
增強版分析模組 - 整合新聞、情緒分析和綜合判斷
"""

import google.generativeai as genai
import pandas as pd
import logging
import time
import json
import requests
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import yfinance as yf
from bs4 import BeautifulSoup
from config.settings import GEMINI_SETTINGS, API_SETTINGS, NEWS_SETTINGS
from src.utils import load_env_variables, retry_on_failure


class EnhancedStockAnalyzer:
    """增強版股票分析器 - 整合技術面、基本面、新聞面和情緒面"""
    
    def __init__(self):
        self.env_vars = load_env_variables()
        self._setup_gemini()
        self.news_cache = {}
        self.analysis_results = {}
        
    def _setup_gemini(self) -> None:
        """設置 Gemini API"""
        try:
            api_key = self.env_vars.get('gemini_api_key')
            if not api_key or api_key == 'your_gemini_api_key_here':
                raise ValueError("請在 .env 檔案中設置正確的 GEMINI_API_KEY")
            
            genai.configure(api_key=api_key)
            # 使用更便宜的模型或調整配額設定
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # 使用較便宜的模型
            logging.info("Gemini AI 初始化成功")
            
        except Exception as e:
            logging.error(f"Gemini AI 初始化失敗: {e}")
            self.model = None

    def get_stock_news(self, ticker: str, days: int = 7) -> List[Dict]:
        """獲取股票相關新聞（支持多種來源）"""
        try:
            # 主要來源：yfinance
            news_list = self._get_yahoo_news(ticker)
            
            # 爬取新聞內容
            if NEWS_SETTINGS.get('scrape_full_content', True):
                for news_item in news_list:
                    content = self._scrape_news_content(news_item['url'])
                    news_item['content'] = content
            
            self.news_cache[ticker] = news_list
            logging.info(f"成功獲取 {ticker} 的 {len(news_list)} 條新聞")
            return news_list
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 新聞失敗: {e}")
            return []
    
    def _get_yahoo_news(self, ticker: str) -> List[Dict]:
        """從 Yahoo Finance 獲取新聞"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                logging.warning(f"未找到 {ticker} 的新聞")
                return []
            
            processed_news = []
            for item in news[:NEWS_SETTINGS.get('max_news_per_stock', 10)]:
                try:
                    # 處理新版本 yfinance 的數據結構
                    if 'content' in item and isinstance(item['content'], dict):
                        content_data = item['content']
                        title = content_data.get('title', '')
                        summary = content_data.get('summary', '')
                        
                        # 獲取發布時間
                        pub_date = content_data.get('pubDate', '') or content_data.get('displayTime', '')
                        if pub_date:
                            try:
                                if pub_date.endswith('Z'):
                                    pub_date = pub_date[:-1] + '+00:00'
                                publish_time = datetime.fromisoformat(pub_date.replace('Z', '+00:00')).strftime('%Y-%m-%d %H:%M:%S')
                            except:
                                publish_time = pub_date
                        else:
                            publish_time = ''
                        
                        # 獲取URL
                        url = ''
                        if 'canonicalUrl' in content_data and isinstance(content_data['canonicalUrl'], dict):
                            url = content_data['canonicalUrl'].get('url', '')
                        elif 'clickThroughUrl' in content_data and isinstance(content_data['clickThroughUrl'], dict):
                            url = content_data['clickThroughUrl'].get('url', '')
                        
                        # 獲取來源
                        publisher = ''
                        if 'provider' in content_data and isinstance(content_data['provider'], dict):
                            publisher = content_data['provider'].get('displayName', '')
                        
                    else:
                        # 處理舊版本格式
                        title = item.get('title', '')
                        summary = item.get('summary', '')
                        publisher = item.get('publisher', '')
                        url = item.get('link', '')
                        
                        # 處理時間戳
                        if 'providerPublishTime' in item:
                            publish_time = datetime.fromtimestamp(
                                item['providerPublishTime']
                            ).strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            publish_time = ''
                    
                    news_item = {
                        'title': title,
                        'summary': summary,
                        'publisher': publisher,
                        'publish_time': publish_time,
                        'url': url,
                        'source': 'Yahoo Finance',
                        'content': ''  # 將在後續填充
                    }
                    
                    if title and url:  # 確保有標題和URL
                        processed_news.append(news_item)
                    
                except Exception as e:
                    logging.warning(f"處理新聞項目時出錯: {e}")
                    continue
                    
            return processed_news
            
        except Exception as e:
            logging.error(f"從 Yahoo Finance 獲取新聞失敗: {e}")
            return []

    def _scrape_news_content(self, url: str) -> str:
        """智能爬取新聞內容"""
        if not url:
            return ""
            
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            
            response = requests.get(url, headers=headers, timeout=NEWS_SETTINGS.get('request_timeout', 10))
            response.raise_for_status()
            
            # 使用 BeautifulSoup 解析 HTML
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 移除不需要的標籤
            for unwanted in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 
                                 '.advertisement', '.ad', '.ads', '.sidebar', '.menu',
                                 '.social-share', '.comments', '.related-articles']):
                if hasattr(unwanted, 'decompose'):
                    unwanted.decompose()
                else:
                    for elem in soup.find_all(unwanted):
                        elem.decompose()
            
            content = self._extract_article_content(soup, url)
            
            # 清理和格式化內容
            content = self._clean_content(content)
            
            # 限制內容長度
            max_length = NEWS_SETTINGS.get('max_content_length', 3000)
            if len(content) > max_length:
                content = content[:max_length] + "..."
            
            time.sleep(NEWS_SETTINGS.get('scraping_delay', 1))
            return content
            
        except requests.exceptions.RequestException as e:
            logging.warning(f"網路請求失敗 {url}: {e}")
            return ""
        except Exception as e:
            logging.warning(f"爬取新聞內容失敗 {url}: {e}")
            return ""
    
    def _extract_article_content(self, soup: BeautifulSoup, url: str) -> str:
        """智能提取文章內容"""
        content = ""
        
        # 根據不同網站域名使用特定選擇器
        domain_selectors = {
            'yahoo.com': ['.caas-body', '[data-module="ArticleBody"]', '.article-wrap'],
            'reuters.com': ['.article-body__content__17Yit', '.PaywallBarrier-body', '.StandardArticleBody_body'],
            'marketwatch.com': ['.article__body', '.column--primary'],
            'bloomberg.com': ['.body-copy-v2', '.fence-body'],
            'cnbc.com': ['.ArticleBody-articleBody', '.InlineContent'],
            'wsj.com': ['.article-content', '.wsj-article-body'],
            'fool.com': ['.article-body', '.tailwind-article-body'],
            'seekingalpha.com': ['.article-content', '[data-module="Body"]']
        }
        
        # 通用選擇器（按優先級排序）
        generic_selectors = [
            'article',
            '.article-body',
            '.article-content', 
            '.story-body',
            '.entry-content',
            '.post-content',
            '.content-body',
            '.main-content',
            '.article-text',
            '.body-content',
            '[data-module="ArticleBody"]',
            '.caas-body',
            '.article-wrap'
        ]
        
        # 嘗試域名特定選擇器
        for domain, selectors in domain_selectors.items():
            if domain in url.lower():
                for selector in selectors:
                    elements = soup.select(selector)
                    if elements:
                        content = ' '.join([elem.get_text(strip=True) for elem in elements])
                        if len(content) > 100:  # 確保內容有意義
                            return content
        
        # 嘗試通用選擇器
        for selector in generic_selectors:
            elements = soup.select(selector)
            if elements:
                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                if len(content) > 100:
                    return content
        
        # 最後嘗試：提取所有段落
        paragraphs = soup.find_all('p')
        if paragraphs:
            content = ' '.join([p.get_text(strip=True) for p in paragraphs 
                              if len(p.get_text(strip=True)) > 30])
        
        return content
    
    def _clean_content(self, content: str) -> str:
        """清理文章內容"""
        if not content:
            return ""
        
        # 移除多餘的空白字符
        content = ' '.join(content.split())
        
        # 移除常見的垃圾文字
        garbage_phrases = [
            'Subscribe to our newsletter',
            'Sign up for our newsletter',
            'Follow us on',
            'Share this article',
            'Related articles',
            'Advertisement',
            'Sponsored content',
            'Cookie Policy',
            'Privacy Policy',
            'Terms of Service'
        ]
        
        for phrase in garbage_phrases:
            content = content.replace(phrase, '')
        
        # 移除過短的句子（可能是導航或垃圾文字）
        sentences = content.split('.')
        meaningful_sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        content = '. '.join(meaningful_sentences)
        
        return content.strip()

    def analyze_news_sentiment(self, news_list: List[Dict], ticker: str) -> Dict[str, Any]:
        """分析新聞情緒並生成綜合新聞面報告"""
        if not news_list or not self.model:
            return {
                'sentiment': 'neutral', 
                'confidence': 0, 
                'news_intelligence_report': '無新聞數據或AI不可用',
                'summary': '無新聞數據或AI不可用'
            }
        
        try:
            # 準備所有新聞內容進行綜合分析
            all_news_content = ""
            news_titles = []
            news_sources = []
            
            for i, news in enumerate(news_list[:5], 1):  # 分析前5條新聞
                news_titles.append(news.get('title', ''))
                news_sources.append(news.get('publisher', ''))
                
                # 建立完整的新聞信息
                news_info = f"\n=== 新聞 {i} ===\n"
                news_info += f"標題: {news.get('title', 'N/A')}\n"
                news_info += f"來源: {news.get('publisher', 'N/A')}\n"
                news_info += f"時間: {news.get('publish_time', 'N/A')}\n"
                
                if news.get('summary'):
                    news_info += f"摘要: {news['summary']}\n"
                
                if news.get('content'):
                    # 取前1000字符進行分析
                    content_preview = news['content'][:1000]
                    news_info += f"內容: {content_preview}\n"
                
                all_news_content += news_info
            
            # 生成綜合新聞情報分析
            prompt = f"""
            請作為專業的金融分析師，對股票 {ticker} 的以下新聞進行深度分析，並生成一份完整的新聞面情報報告：

            {all_news_content}

            請提供一份專業的新聞面分析報告，包含以下內容：

            1. 【新聞面總體評估】
            - 整體市場情緒傾向與強度
            - 新聞覆蓋度和關注度分析
            - 消息面的一致性評估

            2. 【關鍵事件與主題分析】
            - 識別最重要的3-5個關鍵事件或主題
            - 分析每個事件的重要性和影響程度
            - 事件間的關聯性分析

            3. 【市場影響評估】
            - 短期市場反應預期（1-4週）
            - 中期影響分析（1-3個月）
            - 長期趨勢影響（6-12個月）

            4. 【風險與機會識別】
            - 潛在風險因素
            - 投資機會點
            - 需要關注的後續發展

            5. 【投資策略建議】
            - 基於新聞面的具體投資建議
            - 進場時機建議
            - 風險控制要點

            請用繁體中文撰寫，生成一份完整且專業的報告。同時提供JSON格式的結構化數據：

            {{
                "sentiment": "positive/negative/neutral",
                "confidence": 信心度(1-10),
                "sentiment_strength": 情緒強度(1-10),
                "key_themes": ["主要議題1", "主要議題2", "主要議題3"],
                "market_impact": {{
                    "short_term": "短期影響描述",
                    "medium_term": "中期影響描述", 
                    "long_term": "長期影響描述"
                }},
                "risk_factors": ["風險1", "風險2"],
                "opportunities": ["機會1", "機會2"],
                "investment_strategy": "投資策略建議",
                "news_intelligence_report": "完整的新聞面情報分析報告（詳細文字版）",
                "attention_points": ["關注要點1", "關注要點2"]
            }}
            """
            
            # 添加延遲以避免配額限制
            time.sleep(GEMINI_SETTINGS.get('rate_limit_delay', 3))
            
            response = self.model.generate_content(prompt)
            
            if response and response.text:
                # 解析JSON回應
                try:
                    result = json.loads(response.text.strip())
                    return result
                except json.JSONDecodeError:
                    # 如果無法解析JSON，返回文字分析
                    return {
                        'sentiment': 'neutral',
                        'confidence': 5,
                        'news_intelligence_report': response.text,
                        'summary': '新聞分析已生成，但格式解析失敗'
                    }
            else:
                return {
                    'sentiment': 'neutral',
                    'confidence': 0,
                    'news_intelligence_report': 'AI分析不可用',
                    'summary': 'AI分析不可用'
                }
                
        except Exception as e:
            logging.error(f"分析新聞情緒失敗: {e}")
            return {
                'sentiment': 'neutral',
                'confidence': 0,
                'error': str(e),
                'news_intelligence_report': f'分析失敗: {str(e)}',
                'summary': f'分析失敗: {str(e)}'
            }

    def get_market_sentiment(self, ticker: str) -> Dict[str, Any]:
        """分析市場情緒指標"""
        try:
            stock = yf.Ticker(ticker)
            
            # 獲取歷史數據和技術指標
            hist = stock.history(period="3mo")  # 3個月數據
            info = stock.info
            
            if hist.empty:
                return {'error': '無法獲取歷史數據'}
            
            # 計算技術指標
            current_price = hist['Close'].iloc[-1]
            sma_20 = hist['Close'].rolling(window=20).mean().iloc[-1]
            sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else None
            
            # 成交量分析
            avg_volume = hist['Volume'].mean()
            recent_volume = hist['Volume'].iloc[-5:].mean()  # 最近5天平均成交量
            volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
            
            # 價格動能
            price_change_1d = ((current_price - hist['Close'].iloc[-2]) / hist['Close'].iloc[-2]) * 100 if len(hist) >= 2 else 0
            price_change_5d = ((current_price - hist['Close'].iloc[-6]) / hist['Close'].iloc[-6]) * 100 if len(hist) >= 6 else 0
            price_change_20d = ((current_price - hist['Close'].iloc[-21]) / hist['Close'].iloc[-21]) * 100 if len(hist) >= 21 else 0
            
            # 波動率
            volatility = hist['Close'].pct_change().std() * (252**0.5) * 100  # 年化波動率
            
            # RSI 簡化計算
            delta = hist['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs)).iloc[-1] if not rs.empty else 50
            
            sentiment_data = {
                'current_price': current_price,
                'sma_20': sma_20,
                'sma_50': sma_50,
                'volume_ratio': volume_ratio,
                'price_change_1d': price_change_1d,
                'price_change_5d': price_change_5d,
                'price_change_20d': price_change_20d,
                'volatility': volatility,
                'rsi': rsi,
                'week_52_high': info.get('fiftyTwoWeekHigh'),
                'week_52_low': info.get('fiftyTwoWeekLow'),
                'price_near_high': ((current_price - info.get('fiftyTwoWeekHigh', current_price)) / info.get('fiftyTwoWeekHigh', current_price) * 100) if info.get('fiftyTwoWeekHigh') else 0,
                'price_near_low': ((current_price - info.get('fiftyTwoWeekLow', current_price)) / info.get('fiftyTwoWeekLow', current_price) * 100) if info.get('fiftyTwoWeekLow') else 0
            }
            
            return sentiment_data
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 市場情緒數據失敗: {e}")
            return {'error': str(e)}

    def analyze_stock_comprehensive(self, stock_data: Dict) -> Dict[str, Any]:
        """執行股票的綜合分析"""
        try:
            ticker = stock_data.get('ticker', 'Unknown')
            logging.info(f"開始綜合分析 {ticker}...")
            
            # 1. 獲取新聞數據
            news_data = self.get_stock_news(ticker)
            
            # 2. 獲取市場情緒數據
            sentiment_data = self.get_market_sentiment(ticker)
            
            # 3. 分析新聞情緒
            news_sentiment = self.analyze_news_sentiment(news_data, ticker)
            
            # 4. 生成綜合報告
            comprehensive_report = self.generate_comprehensive_report(
                stock_data, news_data, sentiment_data, news_sentiment
            )
            
            # 5. 保存分析結果
            self.analysis_results[ticker] = {
                'stock_data': stock_data,
                'news_data': news_data,
                'sentiment_data': sentiment_data,
                'news_sentiment': news_sentiment,
                'comprehensive_report': comprehensive_report,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logging.info(f"完成 {ticker} 的綜合分析")
            
            # 將新聞數據添加到報告中
            comprehensive_report['news_data'] = news_data
            return comprehensive_report
            
        except Exception as e:
            logging.error(f"綜合分析 {stock_data.get('ticker', 'Unknown')} 失敗: {e}")
            return {'error': str(e), 'ticker': stock_data.get('ticker', 'Unknown')}

    def generate_comprehensive_report(self, stock_data: Dict, news_data: List[Dict], 
                                    sentiment_data: Dict, news_sentiment: Dict) -> Dict[str, Any]:
        """生成綜合分析報告"""
        try:
            ticker = stock_data.get('ticker', 'Unknown')
            company_name = stock_data.get('company_name', 'Unknown Company')
            
            # 基本面評分
            fundamental_score = self._calculate_fundamental_score(stock_data)
            
            # 技術面評分
            technical_score = self._calculate_technical_score(sentiment_data)
            
            # 新聞面評分
            news_score = self._calculate_news_score(news_sentiment)
            
            # 綜合評分
            overall_score = (fundamental_score * 0.4 + technical_score * 0.3 + news_score * 0.3)
            
            # 投資建議
            investment_recommendation = self._get_investment_recommendation(overall_score)
            
            report = {
                'ticker': ticker,
                'company_name': company_name,
                'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'overall_score': round(overall_score, 2),
                'investment_recommendation': investment_recommendation,
                
                # 分項評分
                'fundamental_analysis': {
                    'score': round(fundamental_score, 2),
                    'pe_ratio': stock_data.get('trailing_pe'),
                    'pb_ratio': stock_data.get('price_to_book'),
                    'debt_ratio': stock_data.get('debt_to_equity'),
                    'roe': stock_data.get('return_on_equity'),
                    'profit_margin': stock_data.get('profit_margins')
                },
                
                'technical_analysis': {
                    'score': round(technical_score, 2),
                    'trend': self._get_trend_direction(sentiment_data),
                    'rsi': sentiment_data.get('rsi'),
                    'volume_signal': self._get_volume_signal(sentiment_data.get('volume_ratio', 1)),
                    'price_momentum': sentiment_data.get('price_change_20d'),
                    'volatility': sentiment_data.get('volatility')
                },
                
                'news_sentiment_analysis': {
                    'score': round(news_score, 2),
                    'sentiment': news_sentiment.get('sentiment', 'neutral'),
                    'confidence': news_sentiment.get('confidence', 0),
                    'key_themes': news_sentiment.get('key_themes', []),
                    'short_term_impact': news_sentiment.get('short_term_impact', ''),
                    'news_count': len(news_data),
                    'news_intelligence_report': news_sentiment.get('news_intelligence_report', '')
                },
                
                # 風險評估
                'risk_assessment': {
                    'volatility_risk': self._assess_volatility_risk(sentiment_data.get('volatility', 0)),
                    'valuation_risk': self._assess_valuation_risk(stock_data),
                    'news_risk': self._assess_news_risk(news_sentiment),
                    'overall_risk': self._calculate_overall_risk(sentiment_data, stock_data, news_sentiment)
                },
                
                # 關鍵指標摘要
                'key_metrics': {
                    'current_price': sentiment_data.get('current_price'),
                    'market_cap': stock_data.get('market_cap'),
                    'pe_ratio': stock_data.get('trailing_pe'),
                    'pb_ratio': stock_data.get('price_to_book'),
                    'rsi': sentiment_data.get('rsi'),
                    '52w_position': sentiment_data.get('price_near_high'),
                    'volume_trend': sentiment_data.get('volume_ratio')
                }
            }
            
            return report
            
        except Exception as e:
            logging.error(f"生成綜合報告失敗: {e}")
            return {'error': str(e), 'ticker': stock_data.get('ticker', 'Unknown')}

    def _calculate_fundamental_score(self, stock_data: Dict) -> float:
        """計算基本面評分 (0-100)"""
        score = 50  # 基準分數
        
        # P/E評分
        pe = stock_data.get('trailing_pe')
        if pe and 0 < pe < 15:
            score += 15
        elif pe and 15 <= pe < 25:
            score += 10
        elif pe and pe >= 30:
            score -= 10
        
        # P/B評分
        pb = stock_data.get('price_to_book')
        if pb and 0 < pb < 1.5:
            score += 15
        elif pb and 1.5 <= pb < 3:
            score += 10
        elif pb and pb >= 5:
            score -= 10
        
        # ROE評分
        roe = stock_data.get('return_on_equity')
        if roe and roe > 0.15:
            score += 10
        elif roe and roe > 0.10:
            score += 5
        elif roe and roe < 0.05:
            score -= 10
        
        # 債務比評分
        debt_ratio = stock_data.get('debt_to_equity')
        if debt_ratio and debt_ratio < 0.3:
            score += 10
        elif debt_ratio and debt_ratio < 0.6:
            score += 5
        elif debt_ratio and debt_ratio > 1.5:
            score -= 15
        
        # 毛利率評分
        profit_margin = stock_data.get('profit_margins')
        if profit_margin and profit_margin > 0.20:
            score += 10
        elif profit_margin and profit_margin > 0.10:
            score += 5
        elif profit_margin and profit_margin < 0.05:
            score -= 10
        
        return max(0, min(100, score))

    def _calculate_technical_score(self, sentiment_data: Dict) -> float:
        """計算技術面評分 (0-100)"""
        score = 50  # 基準分數
        
        # RSI評分
        rsi = sentiment_data.get('rsi', 50)
        if 30 < rsi < 70:
            score += 10
        elif rsi <= 30:
            score += 15  # 超賣可能反彈
        elif rsi >= 80:
            score -= 15  # 超買風險
        
        # 價格動能評分
        price_20d = sentiment_data.get('price_change_20d', 0)
        if price_20d > 10:
            score += 15
        elif price_20d > 5:
            score += 10
        elif price_20d > 0:
            score += 5
        elif price_20d < -10:
            score -= 15
        elif price_20d < -5:
            score -= 10
        
        # 成交量評分
        volume_ratio = sentiment_data.get('volume_ratio', 1)
        if volume_ratio > 1.5:
            score += 10  # 成交量放大
        elif volume_ratio > 1.2:
            score += 5
        elif volume_ratio < 0.7:
            score -= 5  # 成交量萎縮
        
        # 相對52週位置
        near_high = sentiment_data.get('price_near_high', 0)
        if near_high > -5:  # 接近52週高點
            score += 5
        elif near_high < -30:  # 遠離52週高點
            score += 10  # 可能被低估
        
        return max(0, min(100, score))

    def _calculate_news_score(self, news_sentiment: Dict) -> float:
        """計算新聞面評分 (0-100)"""
        sentiment = news_sentiment.get('sentiment', 'neutral')
        confidence = news_sentiment.get('confidence', 0)
        
        if sentiment == 'positive':
            score = 50 + (confidence * 5)  # 50-100分
        elif sentiment == 'negative':
            score = 50 - (confidence * 5)  # 0-50分
        else:
            score = 50  # 中性50分
        
        return max(0, min(100, score))

    def _get_investment_recommendation(self, overall_score: float) -> str:
        """根據綜合評分給出投資建議"""
        if overall_score >= 80:
            return "強烈買入"
        elif overall_score >= 70:
            return "買入"
        elif overall_score >= 60:
            return "謹慎買入"
        elif overall_score >= 40:
            return "持有觀望"
        elif overall_score >= 30:
            return "謹慎減持"
        else:
            return "建議賣出"

    def _get_trend_direction(self, sentiment_data: Dict) -> str:
        """判斷趨勢方向"""
        price_20d = sentiment_data.get('price_change_20d', 0)
        if price_20d > 5:
            return "強勢上漲"
        elif price_20d > 0:
            return "溫和上漲"
        elif price_20d > -5:
            return "橫盤整理"
        else:
            return "下跌趨勢"

    def _get_volume_signal(self, volume_ratio: float) -> str:
        """判斷成交量信號"""
        if volume_ratio > 1.5:
            return "成交放大"
        elif volume_ratio > 1.2:
            return "成交活躍"
        elif volume_ratio < 0.7:
            return "成交萎縮"
        else:
            return "成交正常"

    def _assess_volatility_risk(self, volatility: float) -> str:
        """評估波動風險"""
        if volatility > 40:
            return "高風險"
        elif volatility > 25:
            return "中風險"
        else:
            return "低風險"

    def _assess_valuation_risk(self, stock_data: Dict) -> str:
        """評估估值風險"""
        pe = stock_data.get('trailing_pe', 0)
        if pe > 30:
            return "估值偏高"
        elif pe > 20:
            return "估值合理偏高"
        elif pe > 10:
            return "估值合理"
        else:
            return "估值偏低"

    def _assess_news_risk(self, news_sentiment: Dict) -> str:
        """評估新聞風險"""
        sentiment = news_sentiment.get('sentiment', 'neutral')
        if sentiment == 'negative':
            return "新聞面負面"
        elif sentiment == 'positive':
            return "新聞面正面"
        else:
            return "新聞面中性"

    def _calculate_overall_risk(self, sentiment_data: Dict, stock_data: Dict, news_sentiment: Dict) -> str:
        """計算整體風險"""
        risk_score = 0
        
        # 波動風險
        volatility = sentiment_data.get('volatility', 0)
        if volatility > 40:
            risk_score += 3
        elif volatility > 25:
            risk_score += 2
        else:
            risk_score += 1
        
        # 估值風險
        pe = stock_data.get('trailing_pe', 0)
        if pe > 30:
            risk_score += 3
        elif pe > 20:
            risk_score += 2
        else:
            risk_score += 1
        
        # 新聞風險
        sentiment = news_sentiment.get('sentiment', 'neutral')
        if sentiment == 'negative':
            risk_score += 3
        elif sentiment == 'neutral':
            risk_score += 2
        else:
            risk_score += 1
        
        if risk_score >= 8:
            return "高風險"
        elif risk_score >= 6:
            return "中風險"
        else:
            return "低風險"

    def batch_analyze_stocks(self, stock_list: List[Dict], max_analysis: int = 10) -> Dict[str, Any]:
        """批量分析股票"""
        results = {}
        successful_analyses = 0
        
        for i, stock_data in enumerate(stock_list[:max_analysis]):
            ticker = stock_data.get('ticker', f'Unknown_{i}')
            
            try:
                logging.info(f"分析 {ticker} ({i+1}/{min(len(stock_list), max_analysis)})")
                
                result = self.analyze_stock_comprehensive(stock_data)
                results[ticker] = result
                
                if 'error' not in result:
                    successful_analyses += 1
                
                # 添加延遲以避免API限制
                if i < len(stock_list) - 1:  # 不是最後一個
                    time.sleep(3)  # 3秒延遲
                    
            except Exception as e:
                logging.error(f"分析 {ticker} 時發生錯誤: {e}")
                results[ticker] = {'error': str(e), 'ticker': ticker}
        
        # 生成批量分析摘要
        summary = {
            'total_stocks_requested': len(stock_list),
            'total_stocks_analyzed': min(len(stock_list), max_analysis),
            'successful_analyses': successful_analyses,
            'failed_analyses': min(len(stock_list), max_analysis) - successful_analyses,
            'analysis_results': results,
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def save_analysis_results(self, results: Dict, filename_prefix: str = "analysis"):
        """保存分析結果到文件"""
        try:
            import os
            import json
            
            output_dir = "data/output"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{output_dir}/{filename_prefix}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            logging.info(f"分析結果已保存到 {filename}")
            
        except Exception as e:
            logging.error(f"保存分析結果失敗: {e}")
