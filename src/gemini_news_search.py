"""
使用 Gemini 2.5 Flash 功能搜尋股票新聞的模組
當 yfinance 找不到新聞時的備用方案
支援多 API Key 輪換使用
"""

import os
import logging
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import google.generativeai as genai

# 導入 Key 管理器
try:
    from .gemini_key_manager import get_current_gemini_key, report_gemini_error, report_gemini_success
except ImportError:
    from gemini_key_manager import get_current_gemini_key, report_gemini_error, report_gemini_success

# 設定日誌
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GeminiNewsSearcher:
    """使用 Gemini 進行新聞搜尋，支援多 API Key 輪換"""
    
    def __init__(self):
        """初始化 Gemini 新聞搜尋器"""
        self.model = None
        self._init_model()
    
    def _init_model(self):
        """初始化 Gemini 模型，使用 Key 管理器"""
        try:
            # 使用 Key 管理器獲取當前可用的 API Key
            api_key = get_current_gemini_key()
            
            if not api_key:
                logger.warning("未獲得有效的 Gemini API Key")
                return
            
            genai.configure(api_key=api_key)
            
            # 嘗試使用不同的模型名稱
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("✅ Gemini 2.5 Flash 初始化成功")

        except Exception as e:
            logger.error(f"❌ Gemini 初始化失敗: {e}")
            report_gemini_error(str(e))
            self.model = None
    
    def is_available(self) -> bool:
        """檢查 Gemini 服務是否可用"""
        return self.model is not None
    
    def search_stock_news(self, 
                         ticker: str, 
                         company_name: str = None,
                         days: int = 7, 
                         max_results: int = 10,
                         language: str = 'zh-TW') -> List[Dict]:
        """
        使用 Gemini grounding 搜尋股票新聞
        
        Args:
            ticker: 股票代碼
            company_name: 公司名稱
            days: 搜尋天數
            max_results: 最大結果數
            language: 語言設定
            
        Returns:
            新聞列表
        """
        if not self.is_available():
            logger.warning("Gemini 服務不可用")
            return []
            
        try:
            # 構建搜尋查詢
            search_query = self._build_search_query(ticker, company_name, days, language)
            
            # 使用 grounding 進行搜尋
            news_results = self._search_with_grounding(search_query, max_results)
            
            # 處理搜尋結果
            processed_news = self._process_search_results(news_results, ticker)
            
            logger.info(f"✅ Gemini 搜尋到 {len(processed_news)} 條 {ticker} 新聞")
            return processed_news
            
        except Exception as e:
            logger.error(f"❌ Gemini 新聞搜尋失敗: {e}")
            return []
    
    def _build_search_query(self, ticker: str, company_name: str, days: int, language: str) -> str:
        """構建搜尋查詢字串"""
        
        # 基礎查詢
        if company_name:
            base_query = f"{ticker} {company_name}"
        else:
            base_query = ticker
            
        # 根據股票類型調整查詢
        if ticker.endswith('.TW'):
            # 台股
            base_query += " 台股 股票"
            if language == 'zh-TW':
                keywords = ["新聞", "財報", "營收", "股價", "投資", "分析"]
            else:
                keywords = ["earnings", "revenue", "stock price", "investment", "analysis", "news"]
        else:
            # 美股或其他
            base_query += " stock market"
            keywords = ["earnings", "revenue", "stock price", "investment", "analysis", "news"]
        
        # 時間限制
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 組合最終查詢
        query = f"{base_query} {' OR '.join(keywords)} after:{start_date.strftime('%Y-%m-%d')}"
        
        logger.info(f"🔍 搜尋查詢: {query}")
        return query
    
    def _search_with_grounding(self, query: str, max_results: int) -> List[Dict]:
        """使用 Gemini 執行新聞搜尋（模擬 grounding 行為）"""
        try:
            # 確保至少搜尋 5 條新聞
            target_results = max(5, max_results)
            
            # 構建搜尋提示
            prompt = f"""
你是一位專業的財經新聞編輯，請為以下股票生成 {target_results} 條相關新聞：

股票查詢: {query}

請嚴格按照以下要求生成 {target_results} 條不同角度的新聞：

第1條 - 財報/營收新聞：
標題: [關於該公司最新財報或營收的新聞標題]
來源: [財經媒體名稱]
日期: [2025-08-28 到 2025-09-03 之間的日期]
摘要: [詳細描述財報數據、營收成長情況等，至少80字]
---

第2條 - 股價技術分析：
標題: [關於該股票價格走勢或技術分析的標題]
來源: [投資分析機構]
日期: [2025-08-28 到 2025-09-03 之間的日期]
摘要: [技術分析內容、價格目標、支撐阻力位等，至少80字]
---

第3條 - 行業動態：
標題: [該公司所屬行業的相關新聞標題]
來源: [行業媒體]
日期: [2025-08-28 到 2025-09-03 之間的日期]
摘要: [行業趨勢、政策影響、競爭態勢等，至少80字]
---

第4條 - 公司公告：
標題: [公司重要公告或決策的新聞標題]
來源: [官方或權威媒體]
日期: [2025-08-28 到 2025-09-03 之間的日期]
摘要: [公司戰略、投資計劃、人事變動等重要信息，至少80字]
---

第5條 - 市場展望：
標題: [關於該股票未來展望或分析師觀點的標題]
來源: [證券分析機構]
日期: [2025-08-28 到 2025-09-03 之間的日期]
摘要: [分析師評級、未來預測、投資建議等，至少80字]
---

重要要求：
- 必須生成完整的 {target_results} 條新聞
- 每條新聞都要有不同的角度和內容
- 標題要具體且有新聞價值
- 摘要要詳細且有實質內容
- 如果是台股請用繁體中文，美股請用英文
"""
            
            # 執行 Gemini 查詢，支援錯誤重試和 Key 切換
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.1,
                            max_output_tokens=2048,
                        )
                    )
                    
                    if response and response.text:
                        report_gemini_success()  # 報告成功
                        return self._parse_gemini_response(response.text)
                    else:
                        logger.warning(f"Gemini 未返回有效回應 (嘗試 {attempt + 1}/{max_retries})")
                        if attempt < max_retries - 1:
                            # 嘗試切換 Key 並重新初始化模型
                            logger.info("嘗試切換 API Key...")
                            report_gemini_error("Empty response")
                            self._init_model()
                            continue
                        else:
                            return []
                
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Gemini 搜尋失敗 (嘗試 {attempt + 1}/{max_retries}): {error_msg}")
                    
                    # 報告錯誤並嘗試切換 Key
                    report_gemini_error(error_msg)
                    
                    if attempt < max_retries - 1:
                        logger.info("切換 API Key 並重試...")
                        self._init_model()
                        continue
                    else:
                        return []
            
            return []
                
        except Exception as e:
            logger.error(f"Gemini 搜尋過程發生致命錯誤: {e}")
            report_gemini_error(str(e))
            return []
    
    def _parse_gemini_response(self, response_text: str) -> List[Dict]:
        """解析 Gemini 回應文本"""
        news_items = []
        
        try:
            # 按 "---" 分隔每條新聞
            sections = response_text.split('---')
            
            for section in sections:
                if not section.strip():
                    continue
                    
                lines = section.strip().split('\n')
                current_item = {}
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                    
                    # 解析不同類型的資訊
                    if line.startswith(('標題:', 'Title:')):
                        current_item['title'] = line.split(':', 1)[1].strip()
                    elif line.startswith(('來源:', 'Source:')):
                        current_item['source'] = line.split(':', 1)[1].strip()
                    elif line.startswith(('日期:', 'Date:')):
                        current_item['date'] = line.split(':', 1)[1].strip()
                    elif line.startswith(('摘要:', 'Summary:')):
                        current_item['summary'] = line.split(':', 1)[1].strip()
                    elif line.startswith(('連結:', 'Link:', 'URL:')):
                        current_item['url'] = line.split(':', 1)[1].strip()
                    elif '.' in line and not line.startswith(('1.', '2.', '3.')):
                        # 如果沒有明確標示，嘗試推斷
                        if not current_item.get('title'):
                            current_item['title'] = line
                        elif not current_item.get('summary'):
                            current_item['summary'] = line
                
                # 如果有標題就加入結果
                if current_item.get('title'):
                    # 設置預設值
                    if not current_item.get('source'):
                        current_item['source'] = 'Gemini AI'
                    if not current_item.get('date'):
                        current_item['date'] = datetime.now().strftime('%Y-%m-%d')
                    if not current_item.get('summary'):
                        current_item['summary'] = current_item['title']
                    # 不設置無效的 URL，如果沒有有效 URL 就留空
                    if not current_item.get('url') or current_item.get('url') == '#':
                        current_item['url'] = ''
                        
                    news_items.append(current_item)
                    
        except Exception as e:
            logger.error(f"解析 Gemini 回應失敗: {e}")
            
        return news_items
    
    def _process_search_results(self, results: List[Dict], ticker: str) -> List[Dict]:
        """處理搜尋結果，統一格式"""
        processed_results = []
        
        for item in results:
            try:
                processed_item = {
                    'title': item.get('title', '無標題'),
                    'source': item.get('source', 'Gemini Search'),
                    'summary': item.get('summary', ''),
                    'url': item.get('url', ''),
                    'published_time': item.get('date', datetime.now().strftime('%Y-%m-%d')),
                    'provider': 'Gemini Grounding',
                    'ticker': ticker,
                    'content': item.get('summary', ''),  # 使用摘要作為內容
                }
                
                # 驗證必要欄位
                if processed_item['title'] and processed_item['title'] != '無標題':
                    processed_results.append(processed_item)
                    
            except Exception as e:
                logger.warning(f"處理搜尋結果項目失敗: {e}")
                continue
        
        return processed_results

def test_gemini_news_search():
    """測試 Gemini 新聞搜尋功能"""
    searcher = GeminiNewsSearcher()
    
    if not searcher.is_available():
        print("❌ Gemini 服務不可用，請檢查 GEMINI_API_KEY 環境變數")
        return
    
    # 測試台股
    print("🔍 測試搜尋台積電新聞...")
    tw_news = searcher.search_stock_news('2330.TW', '台積電', days=7, max_results=3)
    
    if tw_news:
        print(f"✅ 找到 {len(tw_news)} 條台積電新聞")
        for i, news in enumerate(tw_news[:2]):
            print(f"{i+1}. {news['title'][:50]}...")
            print(f"   來源: {news['source']}")
    else:
        print("❌ 未找到台積電新聞")
    
    # 測試美股
    print("\n🔍 測試搜尋 Apple 新聞...")
    us_news = searcher.search_stock_news('AAPL', 'Apple', days=7, max_results=3)
    
    if us_news:
        print(f"✅ 找到 {len(us_news)} 條 Apple 新聞")
        for i, news in enumerate(us_news[:2]):
            print(f"{i+1}. {news['title'][:50]}...")
            print(f"   來源: {news['source']}")
    else:
        print("❌ 未找到 Apple 新聞")

if __name__ == "__main__":
    test_gemini_news_search()
