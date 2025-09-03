"""
增強版分析模組 - 整合新聞、情緒分析、多代理人辯論和綜合判斷
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
from config.settings import GEMINI_SETTINGS, API_SETTINGS, NEWS_SETTINGS, MULTI_AGENT_SETTINGS
from src.utils import load_env_variables, retry_on_failure

try:
    from .gemini_news_search import GeminiNewsSearcher
    from .gemini_key_manager import (get_gemini_keys_status, get_current_gemini_key, 
                                    get_agent_gemini_key, report_gemini_error, report_gemini_success)
except ImportError:
    GeminiNewsSearcher = None
    get_gemini_keys_status = None
    get_current_gemini_key = None
    get_agent_gemini_key = None
    report_gemini_error = None
    report_gemini_success = None
    logging.warning("無法導入 GeminiNewsSearcher 或 Key 管理器，Gemini 新聞搜尋功能將不可用")


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
            if get_current_gemini_key:
                api_key = get_current_gemini_key()
                if not api_key:
                    raise ValueError("無法獲取有效的 Gemini API Key，請檢查 .env 檔案中的 GEMINI_API_KEY 設定")
            else:
                # 回退到環境變數
                api_key = self.env_vars.get('gemini_api_key')
                if not api_key or api_key == 'your_gemini_api_key_here':
                    raise ValueError("請在 .env 檔案中設置正確的 GEMINI_API_KEY")
            
            genai.configure(api_key=api_key)
            # 使用更便宜的模型或調整配額設定
            self.model = genai.GenerativeModel('gemini-1.5-flash')  # 使用較便宜的模型
            logging.info("Gemini AI 初始化成功，使用 Key 管理器" if get_current_gemini_key else "Gemini AI 初始化成功，使用環境變數")
            
        except Exception as e:
            logging.error(f"Gemini AI 初始化失敗: {e}")
            if report_gemini_error:
                report_gemini_error(f"Gemini AI 初始化失敗: {e}")
            self.model = None

    def translate_to_chinese(self, text: str) -> str:
        """使用 Gemini AI 將英文翻譯成繁體中文"""
        if not text or not self.model:
            return text
            
        try:
            # 如果已經包含中文字符，直接返回
            if any('\u4e00' <= char <= '\u9fff' for char in text):
                return text
                
            prompt = f"""
            請將以下英文新聞標題翻譯成繁體中文，保持原意和專業性：
            
            英文標題：{text}
            
            要求：
            1. 使用繁體中文
            2. 保持財經術語的準確性
            3. 語言自然流暢
            4. 直接返回翻譯結果，不要加任何說明
            """
            
            response = self.model.generate_content(prompt)
            translated_text = response.text.strip()
            
            # 報告成功使用 API
            if report_gemini_success:
                report_gemini_success()
            
            # 移除可能的引號或多餘文字
            if translated_text.startswith('"') and translated_text.endswith('"'):
                translated_text = translated_text[1:-1]
            if translated_text.startswith('「') and translated_text.endswith('」'):
                translated_text = translated_text[1:-1]
                
            return translated_text
            
        except Exception as e:
            logging.warning(f"翻譯失敗: {e}, 返回原文")
            # 報告錯誤並嘗試切換 Key
            if report_gemini_error:
                report_gemini_error(f"翻譯失敗: {e}")
                
            # 嘗試重新初始化 Gemini 以使用新的 Key
            try:
                self._setup_gemini()
                logging.info("已切換到新的 API Key，重新嘗試翻譯")
                if self.model:
                    response = self.model.generate_content(prompt)
                    if report_gemini_success:
                        report_gemini_success()
                    translated_text = response.text.strip()
                    
                    # 移除可能的引號或多餘文字
                    if translated_text.startswith('"') and translated_text.endswith('"'):
                        translated_text = translated_text[1:-1]
                    if translated_text.startswith('「') and translated_text.endswith('」'):
                        translated_text = translated_text[1:-1]
                        
                    return translated_text
            except Exception as retry_error:
                logging.error(f"重試翻譯失敗: {retry_error}")
            
            return text

    def batch_translate_titles(self, titles: List[str]) -> List[str]:
        """批量翻譯新聞標題"""
        if not titles or not self.model:
            return titles
            
        try:
            # 過濾掉空標題
            non_empty_titles = [title for title in titles if title and title.strip()]
            if not non_empty_titles:
                return titles
                
            # 構建批量翻譯請求
            titles_text = "\n".join([f"{i+1}. {title}" for i, title in enumerate(non_empty_titles)])
            
            prompt = f"""
            請將以下英文新聞標題翻譯成繁體中文，保持原意和專業性：
            
            {titles_text}
            
            要求：
            1. 使用繁體中文
            2. 保持財經術語的準確性
            3. 語言自然流暢
            4. 按照相同的編號順序返回翻譯結果
            5. 每行一個翻譯，格式：1. 翻譯結果
            """
            
            response = self.model.generate_content(prompt)
            translated_lines = response.text.strip().split('\n')
            
            # 解析翻譯結果
            translated_titles = []
            for line in translated_lines:
                line = line.strip()
                if line and '. ' in line:
                    # 移除編號
                    translated_title = line.split('. ', 1)[1] if '. ' in line else line
                    # 移除可能的引號
                    if translated_title.startswith('"') and translated_title.endswith('"'):
                        translated_title = translated_title[1:-1]
                    if translated_title.startswith('「') and translated_title.endswith('」'):
                        translated_title = translated_title[1:-1]
                    translated_titles.append(translated_title)
            
            # 確保翻譯結果數量匹配
            if len(translated_titles) == len(non_empty_titles):
                # 重新組合，保持原始列表結構（包括空值）
                result = []
                translated_index = 0
                for original_title in titles:
                    if original_title and original_title.strip():
                        result.append(translated_titles[translated_index])
                        translated_index += 1
                    else:
                        result.append(original_title)
                return result
            else:
                # 如果批量翻譯失敗，回退到單個翻譯
                logging.warning("批量翻譯結果數量不匹配，回退到單個翻譯")
                return [self.translate_to_chinese(title) for title in titles]
                
        except Exception as e:
            logging.warning(f"批量翻譯失敗: {e}, 回退到單個翻譯")
            return [self.translate_to_chinese(title) for title in titles]

    def get_stock_news(self, ticker: str, days: int = 7) -> List[Dict]:
        """獲取股票相關新聞（支持多種來源，確保至少5條成功爬取內容的新聞）"""
        try:
            # 主要來源：yfinance
            news_list = self._get_yahoo_news(ticker)
            
            # 設定目標：至少5條成功爬取內容的新聞
            target_successful_news = 5
            max_attempts = 3
            attempt = 0
            
            while attempt < max_attempts:
                attempt += 1
                
                # 如果需要更多新聞，使用 Gemini 補充
                if not news_list or len(news_list) < 10:  # 確保有足夠的候選新聞
                    if not news_list:
                        logging.warning(f"未找到 {ticker} 的新聞，嘗試使用 Gemini 備用搜尋...")
                    else:
                        logging.info(f"新聞數量不足，使用 Gemini 補充更多新聞...")
                    
                    gemini_news = self._get_gemini_news(ticker, days, max_results=10)
                    if gemini_news:
                        if not news_list:
                            news_list = gemini_news
                        else:
                            # 合併新聞，避免重複
                            existing_titles = {news.get('title', '') for news in news_list}
                            for new_news in gemini_news:
                                if new_news.get('title', '') not in existing_titles:
                                    news_list.append(new_news)
                        
                        logging.info(f"✅ Gemini 搜尋到 {len(gemini_news)} 條新聞，總計 {len(news_list)} 條")
                
                if not news_list:
                    logging.warning(f"❌ 第 {attempt} 次嘗試未找到 {ticker} 的新聞")
                    continue
                
                # 爬取新聞內容並計算成功數量
                successful_scrapes = 0
                failed_scrapes = 0
                
                if NEWS_SETTINGS.get('scrape_full_content', True):
                    for i, news_item in enumerate(news_list):
                        try:
                            url = news_item.get('url', '')
                            
                            # 檢查 URL 有效性
                            if not url or url in ['#', ''] or not url.startswith(('http://', 'https://')):
                                logging.info(f"跳過第 {i+1} 條新聞：無效的 URL ({url})")
                                news_item['content'] = news_item.get('summary', '')
                                # 如果摘要足夠長，也算作成功
                                if len(news_item.get('summary', '')) > 50:
                                    successful_scrapes += 1
                                else:
                                    failed_scrapes += 1
                                continue
                            
                            logging.info(f"正在爬取第 {i+1}/{len(news_list)} 條新聞內容...")
                            content = self._scrape_news_content(url)
                            
                            if content and len(content) > NEWS_SETTINGS.get('min_content_length', 50):
                                news_item['content'] = content
                                successful_scrapes += 1
                                logging.info(f"✅ 成功爬取新聞內容 ({len(content)} 字元)")
                            else:
                                news_item['content'] = news_item.get('summary', '')
                                # 如果摘要足夠長，也算作成功
                                if len(news_item.get('summary', '')) > 50:
                                    successful_scrapes += 1
                                else:
                                    failed_scrapes += 1
                                logging.warning(f"❌ 新聞內容爬取失敗，使用摘要代替")
                                
                        except Exception as e:
                            news_item['content'] = news_item.get('summary', '')
                            if len(news_item.get('summary', '')) > 50:
                                successful_scrapes += 1
                            else:
                                failed_scrapes += 1
                            logging.warning(f"❌ 爬取新聞內容時發生錯誤: {e}")
                            continue
                    
                    logging.info(f"新聞內容處理完成: 成功 {successful_scrapes} 條，失敗 {failed_scrapes} 條")
                    
                    # 檢查是否達到目標
                    if successful_scrapes >= target_successful_news:
                        logging.info(f"✅ 已獲得 {successful_scrapes} 條有效新聞，達到目標！")
                        break
                    elif attempt < max_attempts:
                        logging.warning(f"⚠️ 只有 {successful_scrapes} 條有效新聞，需要 {target_successful_news} 條，嘗試第 {attempt + 1} 次搜尋...")
                        # 清空現有新聞列表，重新搜尋
                        news_list = []
                else:
                    # 如果不爬取內容，直接使用摘要
                    for news_item in news_list:
                        news_item['content'] = news_item.get('summary', '')
                    successful_scrapes = len(news_list)
                    break
            
            if not news_list:
                logging.error(f"❌ 經過 {max_attempts} 次嘗試，仍無法獲取 {ticker} 的新聞")
                return []
            
            # 翻譯新聞標題
            if NEWS_SETTINGS.get('translate_titles', True) and news_list:
                logging.info("正在翻譯新聞標題...")
                try:
                    # 提取所有標題
                    titles = [news.get('title', '') for news in news_list]
                    
                    # 批量翻譯
                    translated_titles = self.batch_translate_titles(titles)
                    
                    # 更新新聞項目的標題
                    for i, news in enumerate(news_list):
                        if i < len(translated_titles):
                            news['original_title'] = news.get('title', '')  # 保存原始英文標題
                            news['title'] = translated_titles[i]  # 使用翻譯後的中文標題
                    
                    logging.info(f"成功翻譯 {len(translated_titles)} 個新聞標題")
                    
                except Exception as e:
                    logging.warning(f"翻譯新聞標題失敗: {e}")
            
            self.news_cache[ticker] = news_list
            logging.info(f"成功獲取 {ticker} 的 {len(news_list)} 條新聞")
            return news_list
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 新聞時發生錯誤: {e}")
            return []
            logging.info(f"成功獲取 {ticker} 的 {len(news_list)} 條新聞")
            return news_list
            
        except Exception as e:
            logging.error(f"獲取 {ticker} 新聞失敗: {e}")
            return []
    
    def _get_yahoo_news(self, ticker: str) -> List[Dict]:
        """從 Yahoo Finance 獲取新聞，專注於一週內的短線投資新聞"""
        try:
            stock = yf.Ticker(ticker)
            news = stock.news
            
            if not news:
                logging.warning(f"未找到 {ticker} 的新聞")
                return []
            
            # 計算時間閾值（使用 UTC 時間避免時區問題）
            from datetime import timezone
            now = datetime.now(timezone.utc)
            one_week_ago = now - timedelta(days=NEWS_SETTINGS.get('news_days_back', 7))
            priority_hours_ago = now - timedelta(hours=NEWS_SETTINGS.get('priority_recent_hours', 24))
            
            processed_news = []
            priority_news = []  # 24小時內的優先新聞
            
            for item in news[:NEWS_SETTINGS.get('max_news_per_stock', 8) * 2]:  # 多獲取一些，然後篩選
                try:
                    # 處理新版本 yfinance 的數據結構
                    if 'content' in item and isinstance(item['content'], dict):
                        content_data = item['content']
                        title = content_data.get('title', '')
                        summary = content_data.get('summary', '')
                        
                        # 獲取發布時間
                        pub_date = content_data.get('pubDate', '') or content_data.get('displayTime', '')
                        publish_timestamp = None
                        if pub_date:
                            try:
                                if pub_date.endswith('Z'):
                                    # 處理 Z 結尾的 UTC 時間
                                    publish_timestamp = datetime.fromisoformat(pub_date.replace('Z', '+00:00'))
                                else:
                                    # 嘗試解析 ISO 格式時間
                                    publish_timestamp = datetime.fromisoformat(pub_date)
                                    # 如果沒有時區資訊，假設為 UTC
                                    if publish_timestamp.tzinfo is None:
                                        publish_timestamp = publish_timestamp.replace(tzinfo=timezone.utc)
                                
                                publish_time = publish_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                            except Exception as e:
                                logging.warning(f"解析時間失敗 {pub_date}: {e}")
                                publish_time = pub_date
                                publish_timestamp = None
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
                        publish_timestamp = None
                        if 'providerPublishTime' in item:
                            # Unix 時間戳轉換為 UTC datetime
                            publish_timestamp = datetime.fromtimestamp(item['providerPublishTime'], tz=timezone.utc)
                            publish_time = publish_timestamp.strftime('%Y-%m-%d %H:%M:%S')
                        else:
                            publish_time = ''
                    
                    # 時間過濾：只保留一週內的新聞
                    if publish_timestamp:
                        if publish_timestamp < one_week_ago:
                            continue  # 跳過超過一週的新聞
                    
                    # 檢查新聞相關性（基本過濾）
                    if not self._is_news_relevant(title, summary, ticker):
                        continue
                    
                    news_item = {
                        'title': title,
                        'summary': summary,
                        'publisher': publisher,
                        'publish_time': publish_time,
                        'publish_timestamp': publish_timestamp,  # 保持為 datetime 物件
                        'url': url,
                        'source': 'Yahoo Finance',
                        'content': '',  # 將在後續填充
                        'is_recent': publish_timestamp and publish_timestamp >= priority_hours_ago if publish_timestamp else False
                    }
                    
                    if title and url:  # 確保有標題和URL
                        if news_item['is_recent']:
                            priority_news.append(news_item)
                        else:
                            processed_news.append(news_item)
                    
                except Exception as e:
                    logging.warning(f"處理新聞項目時出錯: {e}")
                    continue
            
            # 組合新聞：優先顯示最近24小時的新聞，然後是一週內的其他新聞
            final_news = priority_news + processed_news
            
            # 限制新聞數量
            max_news = NEWS_SETTINGS.get('max_news_per_stock', 8)
            final_news = final_news[:max_news]
            
            # 按時間排序（最新的在前）
            final_news.sort(key=lambda x: x.get('publish_timestamp') or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
            
            logging.info(f"獲取到 {ticker} 的 {len(final_news)} 條一週內新聞（其中 {len(priority_news)} 條為24小時內）")
            return final_news
            
        except Exception as e:
            logging.error(f"從 Yahoo Finance 獲取新聞失敗: {e}")
            return []

    def _get_gemini_news(self, ticker: str, days: int = 7, max_results: int = 8) -> List[Dict]:
        """使用 Gemini grounding 搜尋股票新聞作為備用方案"""
        if not GeminiNewsSearcher:
            logging.warning("GeminiNewsSearcher 不可用")
            return []
            
        try:
            # 初始化 Gemini 搜尋器
            gemini_searcher = GeminiNewsSearcher()
            
            if not gemini_searcher.is_available():
                logging.warning("Gemini 服務不可用")
                return []
            
            # 獲取公司名稱用於搜尋
            company_name = self._get_company_name(ticker)
            
            # 使用 Gemini 搜尋新聞
            news_results = gemini_searcher.search_stock_news(
                ticker=ticker,
                company_name=company_name,
                days=days,
                max_results=max_results
            )
            
            # 轉換格式以符合系統預期
            formatted_news = []
            for news in news_results:
                # 處理時間戳，確保是數值而非 datetime 對象
                time_str = news.get('published_time', '')
                timestamp = None
                if time_str:
                    try:
                        dt = self._parse_time_string(time_str)
                        if dt:
                            timestamp = dt.timestamp()  # 轉換為時間戳
                    except:
                        timestamp = None
                
                formatted_item = {
                    'title': news.get('title', ''),
                    'summary': news.get('summary', ''),
                    'publisher': news.get('source', 'Gemini Search'),
                    'publish_time': time_str,
                    'publish_timestamp': timestamp,
                    'url': news.get('url', ''),
                    'source': 'Gemini Grounding',
                    'content': news.get('content', ''),
                    'is_recent': True  # Gemini 結果通常是最新的
                }
                
                if formatted_item['title']:  # 確保有標題
                    formatted_news.append(formatted_item)
            
            logging.info(f"Gemini 搜尋到 {len(formatted_news)} 條 {ticker} 新聞")
            return formatted_news
            
        except Exception as e:
            logging.error(f"Gemini 新聞搜尋失敗: {e}")
            return []
    
    def _get_company_name(self, ticker: str) -> Optional[str]:
        """獲取公司名稱用於新聞搜尋"""
        try:
            # 嘗試從 yfinance 獲取公司名稱
            stock = yf.Ticker(ticker)
            info = stock.info
            company_name = info.get('longName') or info.get('shortName')
            
            if company_name:
                return company_name
                
            # 對於台股，提供一些常見的中文名稱映射
            if ticker.endswith('.TW'):
                common_names = {
                    '2330.TW': '台積電',
                    '2317.TW': '鴻海',
                    '2454.TW': '聯發科',
                    '2881.TW': '富邦金',
                    '6505.TW': '台塑化',
                    '2412.TW': '中華電',
                    '2303.TW': '聯電',
                    '3008.TW': '大立光',
                    '2002.TW': '中鋼',
                    '1301.TW': '台塑'
                }
                return common_names.get(ticker)
                
        except Exception as e:
            logging.warning(f"無法獲取 {ticker} 的公司名稱: {e}")
            
        return None
    
    def _parse_time_string(self, time_str: str) -> Optional[datetime]:
        """解析時間字串為 datetime 物件"""
        if not time_str:
            return None
            
        try:
            # 嘗試不同的時間格式
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%d %H:%M:%S',
                '%Y/%m/%d',
                '%Y/%m/%d %H:%M:%S',
                '%m/%d/%Y',
                '%d/%m/%Y'
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(time_str, fmt)
                except ValueError:
                    continue
                    
            # 如果都不匹配，返回當前時間
            return datetime.now()
            
        except Exception as e:
            logging.warning(f"解析時間字串失敗: {time_str}, {e}")
            return datetime.now()

    def _scrape_news_content(self, url: str) -> str:
        """使用 requests + BeautifulSoup4 智能爬取新聞內容，加強反反爬蟲機制"""
        if not url:
            return ""
            
        # 多個 User-Agent 輪換
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        ]
        
        import random
        selected_ua = random.choice(user_agents)
        
        # 加強版 headers
        headers = {
            'User-Agent': selected_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9,zh-TW;q=0.8,zh;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
            'DNT': '1',
            'Pragma': 'no-cache'
        }
        
        # 如果是特定網站，加入 Referer
        if 'yahoo.com' in url:
            headers['Referer'] = 'https://finance.yahoo.com/'
        elif 'reuters.com' in url:
            headers['Referer'] = 'https://www.reuters.com/'
        elif 'marketwatch.com' in url:
            headers['Referer'] = 'https://www.marketwatch.com/'
        elif 'cnbc.com' in url:
            headers['Referer'] = 'https://www.cnbc.com/'
        elif 'bloomberg.com' in url:
            headers['Referer'] = 'https://www.bloomberg.com/'
        
        # 重試機制
        max_retries = NEWS_SETTINGS.get('max_retries', 3)
        retry_delay_base = NEWS_SETTINGS.get('retry_delay', 5)
        min_content_length = NEWS_SETTINGS.get('min_content_length', 50)
        use_random_delay = NEWS_SETTINGS.get('use_random_delay', True)
        random_delay_range = NEWS_SETTINGS.get('random_delay_range', [1, 3])
        
        for attempt in range(max_retries):
            try:
                # 隨機延遲 (如果啟用)
                if use_random_delay:
                    delay = random.uniform(random_delay_range[0], random_delay_range[1])
                    time.sleep(delay)
                
                # 使用 session 來保持連接
                session = requests.Session()
                session.headers.update(headers)
                
                response = session.get(
                    url, 
                    timeout=NEWS_SETTINGS.get('request_timeout', 15),
                    allow_redirects=True,
                    verify=True
                )
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
                
                session.close()
                return content
                
            except requests.exceptions.HTTPError as e:
                if e.response.status_code in [403, 401, 429]:
                    # 被封鎖，增加延遲後重試
                    if attempt < max_retries - 1:
                        wait_time = (attempt + 1) * retry_delay_base  # 使用配置的重試延遲
                        logging.warning(f"收到 {e.response.status_code} 錯誤，等待 {wait_time} 秒後重試... (嘗試 {attempt + 1}/{max_retries})")
                        time.sleep(wait_time)
                        continue
                    else:
                        logging.warning(f"多次重試後仍失敗 {url}: {e}")
                        return ""
                else:
                    logging.warning(f"HTTP 錯誤 {url}: {e}")
                    return ""
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logging.warning(f"網路請求失敗，重試中... (嘗試 {attempt + 1}/{max_retries}): {e}")
                    time.sleep(2)
                    continue
                else:
                    logging.warning(f"網路請求失敗 {url}: {e}")
                    return ""
            except Exception as e:
                logging.warning(f"爬取新聞內容失敗 {url}: {e}")
                return ""
        
        return ""

    def _is_news_relevant(self, title: str, summary: str, ticker: str) -> bool:
        """檢查新聞是否與股票相關且適合短線投資分析"""
        if not title:
            return False
        
        # 組合文本進行檢查
        text = f"{title} {summary}".lower()
        
        # 排除不相關的新聞類型
        exclude_keywords = [
            'weather', 'sports', 'entertainment', 'celebrity',
            '天氣', '體育', '娛樂', '明星', '電影', '音樂',
            'horoscope', '星座', 'recipe', '食譜'
        ]
        
        for keyword in exclude_keywords:
            if keyword in text:
                return False
        
        # 檢查是否包含股票代碼或公司相關詞語
        ticker_lower = ticker.lower()
        if ticker_lower in text:
            return True
        
        # 檢查是否包含財經相關關鍵詞
        finance_keywords = [
            'stock', 'shares', 'earnings', 'revenue', 'profit', 'financial',
            'market', 'trading', 'investment', 'analysis', 'forecast',
            '股票', '股價', '股份', '營收', '獲利', '財報', '市場', '交易',
            '投資', '分析', '預測', '財務', '業績'
        ]
        
        for keyword in finance_keywords:
            if keyword in text:
                return True
        
        return False
    
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
            'Terms of Service',
            'Read more:',
            'Continue reading',
            'Click here',
            'Learn more'
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
            # 構建新聞標題列表
            title_list = "\n".join([f"• {title}" for title in news_titles if title])
            
            prompt = f"""
            請作為專業的短線投資分析師，對股票 {ticker} 的以下【一週內最新新聞】進行深度分析，並生成一份完整的短線投資新聞面情報報告：

            【本次分析的新聞標題概覽】
            {title_list}

            【詳細新聞內容】
            {all_news_content}

            **重要說明：本分析專注於短線投資機會（1-4週內），請特別關注最新24小時內的新聞對股價的即時影響。**

            請提供一份專業的短線投資新聞面分析報告，**請務必在報告開頭顯示完整的新聞標題列表**，然後包含以下內容：

            1. 【最新新聞標題一覽】
            - 列出所有分析的新聞標題，特別標注24小時內的最新消息
            - 快速識別短線投資的關鍵信息

            2. 【短線新聞面總體評估】
            - 整體市場情緒傾向與強度（針對1-4週內）
            - 新聞的即時影響力和市場關注度
            - 消息面對短線交易的影響評估

            3. 【關鍵事件與短線機會分析】
            - 識別最重要的3-5個短線投資相關事件
            - 分析每個事件對股價的潛在即時影響
            - 事件的時效性和緊急程度評估

            4. 【短線市場影響評估】
            - **短期反應預期（1-7天）** - 重點分析
            - 中短期影響（1-4週）
            - 新聞催化劑對股價波動的預期

            5. 【短線風險與機會識別】
            - 短線潛在風險因素（1-4週內）
            - 短線投資機會點和催化劑
            - 需要密切關注的後續發展和時間點

            6. 【短線投資策略建議】
            - 基於最新新聞面的短線投資建議
            - **進場時機建議**（關鍵！）
            - **出場策略和止損點**
            - 短線風險控制要點

            請用繁體中文撰寫，生成一份完整且專業的短線投資報告。同時提供JSON格式的結構化數據：

            {{
                "sentiment": "positive/negative/neutral",
                "confidence": 信心度(1-10),
                "sentiment_strength": 情緒強度(1-10),
                "news_titles": {news_titles},
                "key_themes": ["主要議題1", "主要議題2", "主要議題3"],
                "market_impact": {{
                    "immediate": "即時影響描述（1-3天）",
                    "short_term": "短期影響描述（1-2週）",
                    "medium_term": "中短期影響描述（2-4週）"
                }},
                "short_term_catalysts": ["短線催化劑1", "短線催化劑2"],
                "risk_factors": ["短線風險1", "短線風險2"],
                "opportunities": ["短線機會1", "短線機會2"],
                "entry_timing": "進場時機建議",
                "exit_strategy": "出場策略建議",
                "investment_strategy": "短線投資策略建議",
                "news_intelligence_report": "完整的短線投資新聞面情報分析報告（詳細文字版）",
                "attention_points": ["短線關注要點1", "短線關注要點2"]
            }}
            """
            
            # 添加延遲以避免配額限制
            time.sleep(GEMINI_SETTINGS.get('rate_limit_delay', 3))
            
            response = self.model.generate_content(prompt)
            
            # 報告成功使用 API
            if report_gemini_success:
                report_gemini_success()
            
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
            # 報告錯誤並嘗試切換 Key
            if report_gemini_error:
                report_gemini_error(f"分析新聞情緒失敗: {e}")
                
            # 嘗試重新初始化 Gemini 以使用新的 Key
            try:
                self._setup_gemini()
                logging.info("已切換到新的 API Key，重新嘗試新聞情緒分析")
                if self.model:
                    response = self.model.generate_content(prompt)
                    if report_gemini_success:
                        report_gemini_success()
                    
                    if response and response.text:
                        try:
                            result = json.loads(response.text.strip())
                            return result
                        except json.JSONDecodeError:
                            return {
                                'sentiment': 'neutral',
                                'confidence': 5,
                                'news_intelligence_report': response.text,
                                'summary': '新聞分析已生成，但格式解析失敗'
                            }
            except Exception as retry_error:
                logging.error(f"重試新聞情緒分析失敗: {retry_error}")
            
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
            ticker = stock_data.get('symbol', 'Unknown')
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
            logging.error(f"綜合分析 {stock_data.get('symbol', 'Unknown')} 失敗: {e}")
            return {'error': str(e), 'ticker': stock_data.get('symbol', 'Unknown')}

    def generate_comprehensive_report(self, stock_data: Dict, news_data: List[Dict], 
                                    sentiment_data: Dict, news_sentiment: Dict) -> Dict[str, Any]:
        """生成綜合分析報告"""
        try:
            ticker = stock_data.get('symbol', 'Unknown')
            company_name = stock_data.get('name', 'Unknown Company')
            
            # 基本面評分
            fundamental_score = self._calculate_fundamental_score(stock_data)
            
            # 技術面評分
            technical_score = self._calculate_technical_score(sentiment_data)
            
            # 新聞面評分
            news_score = self._calculate_news_score(news_sentiment)
            
            # 綜合評分 (使用新的權重: 基本面25%, 技術面25%, 新聞面50%)
            from config.settings import ANALYSIS_SETTINGS
            
            fundamental_weight = ANALYSIS_SETTINGS.get('fundamental_weight', 0.25)
            technical_weight = ANALYSIS_SETTINGS.get('technical_weight', 0.25)
            news_weight = ANALYSIS_SETTINGS.get('news_weight', 0.5)
            
            overall_score = (
                fundamental_score * fundamental_weight + 
                technical_score * technical_weight + 
                news_score * news_weight
            )
            
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
                    'sentiment_strength': news_sentiment.get('sentiment_strength', 0),
                    'news_titles': news_sentiment.get('news_titles', []),
                    'key_themes': news_sentiment.get('key_themes', []),
                    'market_impact': news_sentiment.get('market_impact', {}),
                    'risk_factors': news_sentiment.get('risk_factors', []),
                    'opportunities': news_sentiment.get('opportunities', []),
                    'investment_strategy': news_sentiment.get('investment_strategy', ''),
                    'attention_points': news_sentiment.get('attention_points', []),
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
            return {'error': str(e), 'ticker': stock_data.get('symbol', 'Unknown')}

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

    def batch_analyze_stocks(self, stock_list: List[Dict], max_analysis: int = 10, include_debate: bool = None) -> Dict[str, Any]:
        """批量分析股票"""
        results = {}
        successful_analyses = 0
        
        # 如果沒有指定 include_debate，使用實例的設定
        if include_debate is None:
            include_debate = getattr(self, 'enable_debate', False)
        
        for i, stock_data in enumerate(stock_list[:max_analysis]):
            ticker = stock_data.get('symbol', f'Unknown_{i}')
            
            try:
                if include_debate:
                    logging.info(f"多代理人辯論分析 {ticker} ({i+1}/{min(len(stock_list), max_analysis)})")
                else:
                    logging.info(f"分析 {ticker} ({i+1}/{min(len(stock_list), max_analysis)})")
                
                # 調用綜合分析方法，傳遞 include_debate 參數
                if hasattr(self, 'analyze_stock_comprehensive'):
                    # 如果是 EnhancedStockAnalyzerWithDebate 類別，使用新的方法簽名
                    if hasattr(self, 'conduct_multi_agent_debate'):
                        result = self.analyze_stock_comprehensive(stock_data, include_debate=include_debate)
                    else:
                        # 如果是原始的 EnhancedStockAnalyzer，使用原有的方法簽名
                        result = self.analyze_stock_comprehensive(stock_data)
                else:
                    result = {'error': 'analyze_stock_comprehensive 方法不存在', 'ticker': ticker}
                
                results[ticker] = result
                
                if 'error' not in result:
                    successful_analyses += 1
                
                # 添加延遲以避免API限制
                if i < len(stock_list) - 1:  # 不是最後一個
                    delay_time = 5 if include_debate else 3  # 多代理人分析需要更長延遲
                    time.sleep(delay_time)
                    
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
            'include_debate': include_debate,
            'timestamp': datetime.now().isoformat()
        }
        
        return summary
    
    def save_analysis_results(self, results: Dict, filename_prefix: str = "analysis"):
        """保存分析結果到文件"""
        try:
            import os
            import json
            from src.utils import DateTimeEncoder
            
            output_dir = "data/output"
            os.makedirs(output_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{filename_prefix}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(results, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
            
            logging.info(f"分析結果已保存到: {filepath}")
            return filepath
            
        except Exception as e:
            logging.error(f"保存分析結果失敗: {e}")
            return None


class ValueInvestmentAgent:
    """價值投資代理人 - 整合到增強分析器中"""
    
    def __init__(self, name: str, role: str, expertise: str, investment_style: str):
        self.name = name
        self.role = role
        self.expertise = expertise
        self.investment_style = investment_style
        self.env_vars = load_env_variables()
        self.logger = logging.getLogger(__name__)
        
        # 設置 Gemini AI - 使用 Key 管理器
        self._setup_agent_gemini()
    
    def _setup_agent_gemini(self):
        """為 Agent 設置 Gemini AI"""
        try:
            if get_agent_gemini_key:
                # 為此代理人獲取專用的 API Key
                api_key = get_agent_gemini_key(self.name)
                if not api_key:
                    raise ValueError(f"{self.name} 無法獲取有效的 Gemini API Key")
            else:
                # 回退到環境變數
                api_key = self.env_vars['gemini_api_key']
                
            genai.configure(api_key=api_key)
            self.llm = genai.GenerativeModel(GEMINI_SETTINGS['model'])
            self.logger.info(f"{self.name} Gemini AI 初始化成功，使用專用 API Key")
        except Exception as e:
            self.logger.error(f"{self.name} 初始化 Gemini AI 失敗: {e}")
            if report_gemini_error:
                report_gemini_error(f"{self.name} 初始化失敗: {e}", self.name)
            self.llm = None
    
    def analyze(self, stock_data: Dict, context: str = "", round_type: str = "initial") -> Dict[str, Any]:
        """分析股票數據並提供觀點"""
        if not self.llm:
            return {
                'agent': self.name,
                'analysis': "AI 模型初始化失敗，無法進行分析",
                'recommendation': "HOLD",
                'confidence': 0,
                'target_price': None,
                'risk_level': "UNKNOWN"
            }
        
        prompt = self._create_analysis_prompt(stock_data, context, round_type)
        
        try:
            response = self.llm.generate_content(prompt)
            analysis_text = response.text
            
            # 報告成功使用 API（代理人特定）
            if report_gemini_success:
                report_gemini_success(self.name)
            
            # 解析分析結果
            parsed_result = self._parse_analysis_result(analysis_text)
            parsed_result['agent'] = self.name
            parsed_result['role'] = self.role
            parsed_result['timestamp'] = datetime.now().isoformat()
            
            return parsed_result
                
        except Exception as e:
            self.logger.error(f"{self.name} 分析失敗: {e}")
            # 報告錯誤並嘗試切換 Key（代理人特定）
            if report_gemini_error:
                report_gemini_error(f"{self.name} 分析失敗: {e}", self.name)
                
            # 嘗試重新初始化 Gemini 以使用新的 Key
            try:
                self._setup_agent_gemini()
                self.logger.info(f"{self.name} 已切換到新的 API Key，重新嘗試分析")
                if self.llm:
                    response = self.llm.generate_content(prompt)
                    if report_gemini_success:
                        report_gemini_success(self.name)
                    analysis_text = response.text
                    
                    # 解析分析結果
                    parsed_result = self._parse_analysis_result(analysis_text)
                    parsed_result['agent'] = self.name
                    parsed_result['role'] = self.role
                    parsed_result['timestamp'] = datetime.now().isoformat()
                    
                    return parsed_result
            except Exception as retry_error:
                self.logger.error(f"{self.name} 重試分析失敗: {retry_error}")
            
            return {
                'agent': self.name,
                'analysis': f"分析過程中發生錯誤: {str(e)}",
                'recommendation': "HOLD",
                'confidence': 0,
                'target_price': None,
                'risk_level': "HIGH"
            }
    
    def _create_analysis_prompt(self, stock_data: Dict, context: str, round_type: str) -> str:
        """創建分析提示詞"""
        base_prompt = f"""
你是一位專業的{self.role}，專精於{self.expertise}，投資風格為{self.investment_style}。

股票基本資訊：
- 股票代碼: {stock_data.get('symbol', 'N/A')}
- 公司名稱: {stock_data.get('company_name', 'N/A')}

財務指標：
- 本益比 (P/E): {stock_data.get('pe_ratio', 'N/A')}
- 市淨率 (P/B): {stock_data.get('pb_ratio', 'N/A')}
- 股息殖利率: {stock_data.get('dividend_yield', 'N/A')}%
- 負債權益比: {stock_data.get('debt_to_equity', 'N/A')}
- 自由現金流: {stock_data.get('free_cash_flow', 'N/A')}
- ROE: {stock_data.get('roe', 'N/A')}%
- ROA: {stock_data.get('roa', 'N/A')}%

價格資訊：
- 當前股價: ${stock_data.get('current_price', 'N/A')}
- 52週高點: ${stock_data.get('fifty_two_week_high', 'N/A')}
- 52週低點: ${stock_data.get('fifty_two_week_low', 'N/A')}

{context}
"""
        
        if round_type == "initial":
            task_prompt = f"""
請從{self.investment_style}的角度進行首次分析，提供：

1. 詳細分析（200-300字）
2. 投資建議：BUY/HOLD/SELL
3. 信心程度：1-10分
4. 目標價格區間（如適用）
5. 風險等級：LOW/MEDIUM/HIGH
6. 主要論點（3-5點）

請以 JSON 格式回應：
{{
    "analysis": "詳細分析內容",
    "recommendation": "BUY/HOLD/SELL",
    "confidence": 7,
    "target_price_low": 150.0,
    "target_price_high": 180.0,
    "risk_level": "MEDIUM",
    "key_points": ["論點1", "論點2", "論點3"]
}}
"""
        else:
            task_prompt = f"""
基於其他專家的分析，請重新評估並提供辯論觀點：

1. 針對其他專家意見的反駁或支持
2. 補強或修正你的原始觀點
3. 更新後的投資建議和理由
4. 對爭議點的明確立場

請以 JSON 格式回應：
{{
    "analysis": "辯論分析內容",
    "recommendation": "BUY/HOLD/SELL",
    "confidence": 7,
    "target_price_low": 150.0,
    "target_price_high": 180.0,
    "risk_level": "MEDIUM",
    "rebuttal_points": ["反駁點1", "反駁點2"],
    "support_points": ["支持點1", "支持點2"]
}}
"""
        
        return base_prompt + task_prompt
    
    def _parse_analysis_result(self, analysis_text: str) -> Dict[str, Any]:
        """解析 AI 分析結果"""
        try:
            # 嘗試從文本中提取 JSON
            start_idx = analysis_text.find('{')
            end_idx = analysis_text.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = analysis_text[start_idx:end_idx]
                result = json.loads(json_str)
                
                # 確保必要欄位存在
                if 'analysis' not in result:
                    result['analysis'] = analysis_text
                if 'recommendation' not in result:
                    result['recommendation'] = 'HOLD'
                if 'confidence' not in result:
                    result['confidence'] = 5
                if 'risk_level' not in result:
                    result['risk_level'] = 'MEDIUM'
                
                return result
            else:
                # 如果無法解析 JSON，則手動提取關鍵資訊
                return self._extract_key_info(analysis_text)
                
        except json.JSONDecodeError:
            return self._extract_key_info(analysis_text)
    
    def _extract_key_info(self, text: str) -> Dict[str, Any]:
        """從文本中提取關鍵資訊"""
        text_upper = text.upper()
        
        # 提取投資建議
        if 'BUY' in text_upper or '買入' in text:
            recommendation = 'BUY'
        elif 'SELL' in text_upper or '賣出' in text:
            recommendation = 'SELL'
        else:
            recommendation = 'HOLD'
        
        # 提取風險等級
        if 'HIGH' in text_upper or '高風險' in text:
            risk_level = 'HIGH'
        elif 'LOW' in text_upper or '低風險' in text:
            risk_level = 'LOW'
        else:
            risk_level = 'MEDIUM'
        
        return {
            'analysis': text,
            'recommendation': recommendation,
            'confidence': 5,
            'target_price_low': None,
            'target_price_high': None,
            'risk_level': risk_level,
            'key_points': []
        }


# 新增多代理人辯論功能到增強分析器
class EnhancedStockAnalyzerWithDebate(EnhancedStockAnalyzer):
    """增強版股票分析器 - 包含多代理人辯論功能"""
    
    def __init__(self, enable_debate: bool = None, status_manager=None):
        super().__init__()
        
        # 設置狀態管理器
        self.status_manager = status_manager
        
        # 判斷是否啟用多代理人辯論
        if enable_debate is None:
            enable_debate = MULTI_AGENT_SETTINGS.get('enable_debate', True)
        self.enable_debate = enable_debate
        
        # 如果啟用辯論，初始化多代理人系統
        if self.enable_debate:
            try:
                self.agents = self._initialize_agents()
                logging.info("多代理人辯論系統初始化成功")
            except Exception as e:
                logging.error(f"多代理人辯論系統初始化失敗: {e}")
                self.agents = []
                self.enable_debate = False
        else:
            self.agents = []
    
    def _initialize_agents(self) -> List[ValueInvestmentAgent]:
        """初始化代理人團隊"""
        agents = [
            ValueInvestmentAgent(
                name="巴菲特派價值投資師",
                role="長期價值投資分析師",
                expertise="基本面分析、護城河評估、長期價值挖掘",
                investment_style="長期持有、尋找具有競爭優勢的優質企業"
            ),
            ValueInvestmentAgent(
                name="葛拉漢派防御型投資師",
                role="防御型價值投資分析師", 
                expertise="安全邊際評估、財務穩健性分析、風險控制",
                investment_style="重視安全邊際、偏好低估值穩健企業"
            ),
            ValueInvestmentAgent(
                name="成長價值投資師",
                role="成長價值投資分析師",
                expertise="成長性評估、未來盈利預測、估值模型",
                investment_style="尋找被低估的成長股、關注未來潛力"
            ),
            ValueInvestmentAgent(
                name="市場時機分析師",
                role="市場週期分析師",
                expertise="市場時機判斷、技術面分析、資金流向",
                investment_style="關注市場週期、適時進出場"
            ),
            ValueInvestmentAgent(
                name="風險管理專家",
                role="投資風險評估師",
                expertise="風險識別、投組管理、資產配置",
                investment_style="嚴格風控、分散投資、資產保護"
            )
        ]
        return agents
    
    def _map_agent_to_key(self, agent_name: str) -> str:
        """將代理人名稱映射到狀態管理器的鍵值"""
        agent_mapping = {
            '巴菲特派價值投資師': 'fundamentals_analyst',
            '葛拉漢派防御型投資師': 'conservative_debator',
            '成長價值投資師': 'bull_researcher',
            '市場時機分析師': 'market_analyst',
            '風險管理專家': 'risk_manager'
        }
        return agent_mapping.get(agent_name, 'research_manager')
    
    def analyze_stock_comprehensive(self, stock_data: Dict, include_debate: bool = None) -> Dict[str, Any]:
        """執行股票的綜合分析，包含多代理人辯論（如果啟用）"""
        stock_symbol = stock_data.get('symbol', 'Unknown')
        
        # 更新狀態：開始綜合分析
        if self.status_manager:
            self.status_manager.update_status(
                agent='market_analyst',
                step='綜合分析',
                message=f'正在為 {stock_symbol} 執行綜合分析...',
                progress=10
            )
        
        # 先執行原有的綜合分析
        base_analysis = super().analyze_stock_comprehensive(stock_data)
        
        # 如果啟用辯論且沒有錯誤，則進行多代理人分析
        if include_debate is None:
            include_debate = self.enable_debate
        
        if include_debate and self.enable_debate and 'error' not in base_analysis:
            try:
                logging.info(f"開始對 {stock_data.get('symbol')} 進行多代理人辯論分析")
                
                # 更新狀態：開始多代理人辯論
                if self.status_manager:
                    self.status_manager.update_status(
                        agent='research_manager',
                        step='多代理人辯論',
                        message=f'正在召集專家團隊分析 {stock_symbol}...',
                        progress=50
                    )
                
                debate_result = self.conduct_multi_agent_debate(stock_data)
                
                # 整合辯論結果到基礎分析中
                base_analysis['multi_agent_debate'] = debate_result
                base_analysis['integrated_recommendation'] = self._integrate_analyses(
                    base_analysis, debate_result
                )
                
                # 更新狀態：完成分析
                if self.status_manager:
                    self.status_manager.update_status(
                        agent='research_manager',
                        step='整合結果',
                        message=f'{stock_symbol} 的綜合分析已完成',
                        progress=90
                    )
                
            except Exception as e:
                logging.error(f"多代理人辯論分析失敗: {e}")
                base_analysis['multi_agent_debate'] = {'error': str(e)}
        
        return base_analysis
    
    def conduct_multi_agent_debate(self, stock_data: Dict, rounds: int = None) -> Dict[str, Any]:
        """進行多代理人辯論分析"""
        if rounds is None:
            rounds = MULTI_AGENT_SETTINGS.get('debate_rounds', 2)
        
        stock_symbol = stock_data.get('symbol', 'Unknown')
        
        debate_result = {
            'symbol': stock_data.get('symbol'),
            'company_name': stock_data.get('company_name'),
            'agents_analysis': {},
            'debate_rounds': [],
            'final_consensus': {},
            'voting_results': {},
            'debate_summary': "",
            'timestamp': datetime.now().isoformat()
        }
        
        # 第一輪：各代理人獨立分析
        logging.info("第一輪：各代理人獨立分析")
        
        if self.status_manager:
            self.status_manager.update_status(
                agent='research_manager',
                step='專家獨立分析',
                message=f'各領域專家正在獨立分析 {stock_symbol}...',
                progress=55
            )
        
        for i, agent in enumerate(self.agents):
            try:
                # 更新當前分析的專家
                if self.status_manager:
                    agent_key = agent.name.replace('派', '').replace('投資師', '').replace('分析師', '').replace('專家', '')
                    self.status_manager.update_status(
                        agent=self._map_agent_to_key(agent.name),
                        step=f'專家分析 ({i+1}/{len(self.agents)})',
                        message=f'{agent.name} 正在分析 {stock_symbol}...',
                        progress=55 + (i * 5)
                    )
                
                analysis = agent.analyze(stock_data, "", "initial")
                debate_result['agents_analysis'][agent.name] = analysis
                time.sleep(GEMINI_SETTINGS.get('rate_limit_delay', 3))  # API 限制
            except Exception as e:
                logging.error(f"{agent.name} 分析失敗: {e}")
        
        # 進行辯論輪次
        context = self._build_context_from_analyses(debate_result['agents_analysis'])
        
        for round_num in range(1, rounds + 1):
            logging.info(f"第{round_num + 1}輪：辯論與反駁")
            
            if self.status_manager:
                self.status_manager.update_status(
                    agent='research_manager',
                    step=f'辯論輪次 {round_num}',
                    message=f'專家團隊正在進行第 {round_num} 輪辯論...',
                    progress=70 + (round_num * 5)
                )
            
            round_result = self._conduct_debate_round(stock_data, context, round_num)
            debate_result['debate_rounds'].append(round_result)
            context = self._update_context(context, round_result)
        
        # 統計投票結果
        if self.status_manager:
            self.status_manager.update_status(
                agent='research_manager',
                step='統計投票結果',
                message=f'正在統計專家投票結果...',
                progress=85
            )
        
        debate_result['voting_results'] = self._calculate_voting_results(
            debate_result['agents_analysis'], debate_result['debate_rounds']
        )
        
        # 生成最終共識
        debate_result['final_consensus'] = self._generate_final_consensus(
            stock_data, debate_result['agents_analysis'], 
            debate_result['debate_rounds'], debate_result['voting_results']
        )
        
        # 生成辯論摘要
        debate_result['debate_summary'] = self._generate_debate_summary(debate_result)
        
        return debate_result
    
    def _build_context_from_analyses(self, analyses: Dict) -> str:
        """從各代理人分析中建構背景資訊"""
        context = "=== 各專家的初步分析觀點 ===\n\n"
        for agent_name, analysis_data in analyses.items():
            context += f"【{agent_name}】({analysis_data.get('role', 'N/A')}):\n"
            context += f"投資建議: {analysis_data.get('recommendation', 'N/A')}\n"
            context += f"信心程度: {analysis_data.get('confidence', 'N/A')}/10\n"
            context += f"風險等級: {analysis_data.get('risk_level', 'N/A')}\n"
            context += f"分析要點: {analysis_data.get('analysis', 'N/A')[:200]}...\n\n"
        return context
    
    def _conduct_debate_round(self, stock_data: Dict, context: str, round_num: int) -> Dict:
        """進行一輪辯論"""
        round_result = {
            'round': round_num,
            'timestamp': datetime.now().isoformat(),
            'agent_responses': {}
        }
        
        debate_context = f"""
{context}

=== 第{round_num}輪辯論要求 ===
基於上述各專家的分析意見，請重新評估你的觀點並提供辯論回應：

1. 指出其他專家分析中你認為有問題或值得商榷的地方
2. 補強你原本分析中的論點
3. 基於討論調整你的投資建議（如果需要）
4. 提供具體的數據和邏輯支持你的觀點
5. 對主要爭議點表達明確立場

請保持專業理性，並基於價值投資原則進行分析。
"""
        
        for agent in self.agents:
            try:
                response = agent.analyze(stock_data, debate_context, "debate")
                round_result['agent_responses'][agent.name] = response
                time.sleep(GEMINI_SETTINGS.get('rate_limit_delay', 3))
            except Exception as e:
                logging.error(f"{agent.name} 第{round_num}輪辯論失敗: {e}")
        
        return round_result
    
    def _update_context(self, current_context: str, round_result: Dict) -> str:
        """更新辯論背景資訊"""
        new_context = current_context + f"\n\n=== 第{round_result['round']}輪辯論結果 ===\n"
        for agent_name, response in round_result['agent_responses'].items():
            recommendation = response.get('recommendation', 'N/A')
            confidence = response.get('confidence', 'N/A')
            new_context += f"\n【{agent_name}】更新觀點：{recommendation} (信心度: {confidence}/10)\n"
            new_context += f"主要論點: {response.get('analysis', 'N/A')[:150]}...\n"
        return new_context
    
    def _calculate_voting_results(self, initial_analyses: Dict, debate_rounds: List) -> Dict:
        """計算投票結果"""
        voting_data = {
            'buy_votes': 0,
            'hold_votes': 0,
            'sell_votes': 0,
            'initial_votes': {'BUY': 0, 'HOLD': 0, 'SELL': 0},
            'final_votes': {'BUY': 0, 'HOLD': 0, 'SELL': 0},
            'confidence_scores': {},
            'consensus_level': 0,
            'agent_final_positions': {}
        }
        
        # 統計初始投票
        for agent_name, analysis in initial_analyses.items():
            recommendation = analysis.get('recommendation', 'HOLD').upper()
            if recommendation in voting_data['initial_votes']:
                voting_data['initial_votes'][recommendation] += 1
        
        # 統計最終投票（取最後一輪的結果或初始分析）
        final_positions = {}
        
        if debate_rounds:
            # 使用最後一輪辯論結果
            final_round = debate_rounds[-1]
            for agent_name, response in final_round.get('agent_responses', {}).items():
                recommendation = response.get('recommendation', 'HOLD').upper()
                confidence = response.get('confidence', 5)
                
                final_positions[agent_name] = {
                    'recommendation': recommendation,
                    'confidence': confidence
                }
        else:
            # 如果沒有辯論輪次，使用初始分析
            for agent_name, analysis in initial_analyses.items():
                recommendation = analysis.get('recommendation', 'HOLD').upper()
                confidence = analysis.get('confidence', 5)
                
                final_positions[agent_name] = {
                    'recommendation': recommendation,
                    'confidence': confidence
                }
        
        # 統計最終票數
        for agent_name, position in final_positions.items():
            recommendation = position['recommendation']
            confidence = position['confidence']
            
            if recommendation in voting_data['final_votes']:
                voting_data['final_votes'][recommendation] += 1
                
            # 設置標準化的票數欄位（用於前端顯示）
            if recommendation == 'BUY':
                voting_data['buy_votes'] += 1
            elif recommendation == 'HOLD':
                voting_data['hold_votes'] += 1
            elif recommendation == 'SELL':
                voting_data['sell_votes'] += 1
                
            voting_data['confidence_scores'][agent_name] = confidence
            voting_data['agent_final_positions'][agent_name] = position
        
        # 計算共識程度
        total_agents = len(self.agents)
        max_votes = max(voting_data['final_votes'].values()) if voting_data['final_votes'] else 0
        voting_data['consensus_level'] = max_votes / total_agents if total_agents > 0 else 0
        
        return voting_data
    
    def _generate_final_consensus(self, stock_data: Dict, analyses: Dict, 
                                debate_rounds: List, voting_results: Dict) -> Dict:
        """生成最終投資共識"""
        # 找出最多票的建議
        final_votes = voting_results['final_votes']
        consensus_recommendation = max(final_votes, key=final_votes.get)
        
        # 計算平均信心度
        confidence_scores = voting_results['confidence_scores']
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 5
        
        # 收集支持共識的主要論點
        supporting_points = []
        opposing_points = []
        
        if debate_rounds:
            final_round = debate_rounds[-1]
            for agent_name, response in final_round['agent_responses'].items():
                if response.get('recommendation') == consensus_recommendation:
                    key_points = response.get('key_points', [])
                    supporting_points.extend(key_points)
                else:
                    key_points = response.get('key_points', [])
                    opposing_points.extend(key_points)
        
        return {
            'final_recommendation': consensus_recommendation,
            'consensus_level': voting_results['consensus_level'],
            'average_confidence': round(avg_confidence, 1),
            'vote_distribution': final_votes,
            'supporting_points': supporting_points[:5],  # 取前5個支持論點
            'opposing_points': opposing_points[:3],      # 取前3個反對論點
            'risk_assessment': self._assess_overall_risk_from_debate(analyses, debate_rounds),
            'timestamp': datetime.now().isoformat()
        }
    
    def _assess_overall_risk_from_debate(self, analyses: Dict, debate_rounds: List) -> str:
        """評估整體風險等級"""
        risk_scores = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
        total_risk = 0
        count = 0
        
        # 收集所有風險評估
        for analysis in analyses.values():
            risk_level = analysis.get('risk_level', 'MEDIUM')
            total_risk += risk_scores.get(risk_level, 2)
            count += 1
        
        if debate_rounds:
            final_round = debate_rounds[-1]
            for response in final_round['agent_responses'].values():
                risk_level = response.get('risk_level', 'MEDIUM')
                total_risk += risk_scores.get(risk_level, 2)
                count += 1
        
        if count == 0:
            return 'MEDIUM'
        
        avg_risk = total_risk / count
        if avg_risk <= 1.5:
            return 'LOW'
        elif avg_risk <= 2.5:
            return 'MEDIUM'
        else:
            return 'HIGH'
    
    def _generate_debate_summary(self, debate_result: Dict) -> str:
        """生成辯論摘要"""
        summary_parts = []
        
        # 基本資訊
        symbol = debate_result['symbol']
        final_rec = debate_result['final_consensus']['final_recommendation']
        consensus_level = debate_result['final_consensus']['consensus_level']
        
        summary_parts.append(f"股票 {symbol} 多代理人分析結果：")
        summary_parts.append(f"最終建議：{final_rec}")
        summary_parts.append(f"專家共識度：{consensus_level:.1%}")
        
        # 投票分佈
        vote_dist = debate_result['final_consensus']['vote_distribution']
        summary_parts.append(f"投票分佈：買入 {vote_dist['BUY']} 票，持有 {vote_dist['HOLD']} 票，賣出 {vote_dist['SELL']} 票")
        
        # 主要論點
        supporting_points = debate_result['final_consensus']['supporting_points']
        if supporting_points:
            summary_parts.append("主要支持論點：")
            for point in supporting_points[:3]:
                summary_parts.append(f"• {point}")
        
        # 風險評估
        risk_level = debate_result['final_consensus']['risk_assessment']
        summary_parts.append(f"整體風險等級：{risk_level}")
        
        return "\n".join(summary_parts)
    
    def _integrate_analyses(self, base_analysis: Dict, debate_analysis: Dict) -> Dict[str, Any]:
        """整合基礎分析和多代理人辯論結果"""
        integrated_result = {
            'final_recommendation': 'HOLD',
            'confidence_level': 5,
            'risk_assessment': 'MEDIUM',
            'integration_method': 'weighted_consensus',
            'reasoning': [],
            'target_price_range': {},
            'investment_horizon': 'MEDIUM_TERM',
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            # 從基礎分析提取建議
            base_rec = base_analysis.get('investment_recommendation', 'HOLD')
            base_score = base_analysis.get('overall_score', 50)
            
            # 從辯論分析提取建議
            final_consensus = debate_analysis.get('final_consensus', {})
            debate_rec = final_consensus.get('final_recommendation', 'HOLD')
            consensus_level = final_consensus.get('consensus_level', 0.5)
            avg_confidence = final_consensus.get('average_confidence', 5)
            
            # 權重設定：如果多代理人共識度高，給予更高權重
            debate_weight = 0.6 + (consensus_level * 0.3)  # 0.6-0.9
            base_weight = 1 - debate_weight
            
            # 決定最終建議
            if base_rec == debate_rec:
                # 如果兩者一致，直接採用
                integrated_result['final_recommendation'] = debate_rec
                integrated_result['confidence_level'] = min(10, avg_confidence * 1.2)  # 提高信心度
                integrated_result['reasoning'] = ['基礎分析與多代理人辯論結果一致']
            else:
                # 如果不一致，基於信心度和共識度決定
                if avg_confidence * consensus_level > base_score * 0.08:  # 標準化比較
                    integrated_result['final_recommendation'] = debate_rec
                    integrated_result['reasoning'] = ['多代理人辯論具有較高共識，採用辯論結果']
                else:
                    integrated_result['final_recommendation'] = base_rec
                    integrated_result['reasoning'] = ['基礎分析信心度較高，採用傳統分析結果']
                
                integrated_result['confidence_level'] = max(avg_confidence, base_score/10) * 0.9
            
            # 風險評估整合
            base_risk = base_analysis.get('risk_assessment', {}).get('overall_risk', 'MEDIUM')
            debate_risk = final_consensus.get('risk_assessment', 'MEDIUM')
            
            risk_levels = {'LOW': 1, 'MEDIUM': 2, 'HIGH': 3}
            avg_risk = (risk_levels.get(base_risk, 2) + risk_levels.get(debate_risk, 2)) / 2
            
            if avg_risk <= 1.5:
                integrated_result['risk_assessment'] = 'LOW'
            elif avg_risk <= 2.5:
                integrated_result['risk_assessment'] = 'MEDIUM'
            else:
                integrated_result['risk_assessment'] = 'HIGH'
            
            # 合併理由
            supporting_points = final_consensus.get('supporting_points', [])
            integrated_result['reasoning'].extend(supporting_points[:3])  # 取前3個辯論理由
            
            # 添加額外資訊
            integrated_result['consensus_level'] = consensus_level
            integrated_result['vote_distribution'] = final_consensus.get('vote_distribution', {})
            integrated_result['base_analysis_score'] = base_score
            integrated_result['debate_confidence'] = avg_confidence
            
        except Exception as e:
            logging.error(f"整合分析失敗: {e}")
            integrated_result['error'] = str(e)
        
        return integrated_result
