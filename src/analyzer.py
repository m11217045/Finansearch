"""
Gemini 分析模組 - 使用 Google Gemini AI 進行股票深度分析
"""

import google.generativeai as genai
import pandas as pd
import logging
import time
import json
from typing import Dict, List, Any, Optional
from config.settings import GEMINI_SETTINGS
from src.utils import load_env_variables, retry_on_failure, format_currency, format_percentage, format_ratio
from src.gemini_key_manager import get_current_gemini_key, report_gemini_error, report_gemini_success


class GeminiAnalyzer:
    """Gemini AI 股票分析器"""
    
    def __init__(self):
        self.env_vars = load_env_variables()
        self._setup_gemini()
        self.analysis_results = {}
    
    def _setup_gemini(self) -> None:
        """設置 Gemini API"""
        try:
            api_key = get_current_gemini_key()
            if not api_key:
                raise ValueError("無法獲取有效的 Gemini API Key，請檢查 .env 檔案中的 GEMINI_API_KEY 設定")
            
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(GEMINI_SETTINGS['model'])
            logging.info("Gemini AI 初始化成功，使用 Key 管理器")
            
        except Exception as e:
            logging.error(f"Gemini AI 初始化失敗: {e}")
            report_gemini_error(f"Gemini AI 初始化失敗: {e}")
            raise
    
    def create_analysis_prompt(self, stock_data: Dict[str, Any]) -> str:
        """建立股票分析提示詞"""
        ticker = stock_data.get('ticker', 'Unknown')
        company_name = stock_data.get('company_name') or stock_data.get('name', ticker)
        sector = stock_data.get('sector', '未分類')
        industry = stock_data.get('industry', '未分類')
        
        # 格式化財務數據
        market_cap = format_currency(stock_data.get('market_cap'))
        pe_ratio = format_ratio(stock_data.get('trailing_pe'))
        pb_ratio = format_ratio(stock_data.get('price_to_book'))
        dividend_yield = format_percentage(stock_data.get('dividend_yield'))
        debt_to_equity = format_ratio(stock_data.get('debt_to_equity'))
        free_cashflow = format_currency(stock_data.get('free_cashflow'))
        roe = format_percentage(stock_data.get('return_on_equity'))
        profit_margins = format_percentage(stock_data.get('profit_margins'))
        
        prompt = f"""
請以專業財務分析師的角度，對以下股票進行價值投資分析：

**公司基本資訊：**
- 股票代碼：{ticker}
- 公司名稱：{company_name}
- 行業別：{sector} - {industry}

**關鍵財務指標：**
- 市值：{market_cap}
- 本益比 (P/E)：{pe_ratio}
- 市淨率 (P/B)：{pb_ratio}
- 股息殖利率：{dividend_yield}
- 債務權益比：{debt_to_equity}
- 自由現金流：{free_cashflow}
- 股東權益報酬率 (ROE)：{roe}
- 淨利潤率：{profit_margins}

**分析要求：**
請提供以下結構化分析（請保持簡潔，每個部分不超過150字）：

1. **估值分析**：基於 P/E、P/B 等指標，評估當前估值是否合理

2. **財務健康度**：分析債務水平、現金流狀況和獲利能力

3. **投資亮點**：指出該股票的主要投資優勢和競爭優勢

4. **潛在風險**：識別可能的投資風險和需要關注的問題

5. **價值投資觀點**：從價值投資角度總結投資建議

6. **綜合評等**：給出 1-10 分的投資評分（10分為最佳），並說明評分理由

請使用繁體中文回應，並保持客觀、專業的分析語調。
"""
        return prompt
    
    @retry_on_failure(max_retries=3, delay=2.0)
    def analyze_stock(self, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """使用 Gemini 分析單一股票"""
        ticker = stock_data.get('ticker', 'Unknown')
        
        try:
            prompt = self.create_analysis_prompt(stock_data)
            
            # 生成分析
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=GEMINI_SETTINGS['max_tokens'],
                    temperature=GEMINI_SETTINGS['temperature'],
                )
            )
            
            # 報告成功使用 API
            report_gemini_success()
            
            analysis_result = {
                'ticker': ticker,
                'company_name': stock_data.get('company_name') or stock_data.get('name', ticker),
                'analysis_text': response.text,
                'analysis_timestamp': pd.Timestamp.now().isoformat(),
                'model_used': GEMINI_SETTINGS['model']
            }
            
            # 嘗試從分析文本中提取結構化信息
            structured_analysis = self._parse_analysis_text(response.text)
            analysis_result.update(structured_analysis)
            
            logging.info(f"完成 {ticker} 的 Gemini 分析")
            return analysis_result
            
        except Exception as e:
            logging.error(f"分析 {ticker} 時發生錯誤: {e}")
            # 報告錯誤並嘗試切換 Key
            report_gemini_error(f"分析 {ticker} 失敗: {e}")
            
            # 嘗試重新初始化 Gemini 以使用新的 Key
            try:
                self._setup_gemini()
                logging.info(f"已切換到新的 API Key，重新嘗試分析 {ticker}")
            except Exception as setup_error:
                logging.error(f"重新初始化 Gemini 失敗: {setup_error}")
            
            return {
                'ticker': ticker,
                'error': str(e),
                'analysis_timestamp': pd.Timestamp.now().isoformat()
            }
    
    def _parse_analysis_text(self, analysis_text: str) -> Dict[str, str]:
        """從分析文本中提取結構化信息"""
        sections = {}
        
        # 定義章節關鍵詞
        section_keywords = {
            'valuation_analysis': ['估值分析', '估值評估', '1.'],
            'financial_health': ['財務健康度', '財務狀況', '2.'],
            'investment_highlights': ['投資亮點', '投資優勢', '3.'],
            'potential_risks': ['潛在風險', '投資風險', '4.'],
            'value_perspective': ['價值投資觀點', '價值投資', '5.'],
            'overall_rating': ['綜合評等', '投資評分', '6.']
        }
        
        # 分割文本
        lines = analysis_text.split('\n')
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 檢查是否為新章節
            section_found = False
            for section_key, keywords in section_keywords.items():
                if any(keyword in line for keyword in keywords):
                    # 保存前一個章節
                    if current_section and current_content:
                        sections[current_section] = '\n'.join(current_content).strip()
                    
                    current_section = section_key
                    current_content = [line]
                    section_found = True
                    break
            
            if not section_found and current_section:
                current_content.append(line)
        
        # 保存最後一個章節
        if current_section and current_content:
            sections[current_section] = '\n'.join(current_content).strip()
        
        return sections
    
    def batch_analyze_stocks(self, stock_list: List[Dict[str, Any]], 
                           max_analysis: Optional[int] = None) -> List[Dict[str, Any]]:
        """批量分析股票"""
        if max_analysis:
            stock_list = stock_list[:max_analysis]
        
        logging.info(f"開始使用 Gemini 分析 {len(stock_list)} 支股票...")
        
        analysis_results = []
        
        for i, stock_data in enumerate(stock_list):
            ticker = stock_data.get('ticker', f'Stock_{i}')
            
            try:
                analysis = self.analyze_stock(stock_data)
                analysis_results.append(analysis)
                
                logging.info(f"已完成 {i+1}/{len(stock_list)}: {ticker}")
                
                # API 請求間隔（避免超過速率限制）
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"分析 {ticker} 失敗: {e}")
                analysis_results.append({
                    'ticker': ticker,
                    'error': str(e),
                    'analysis_timestamp': pd.Timestamp.now().isoformat()
                })
                continue
        
        logging.info(f"Gemini 批量分析完成，成功分析 {len([r for r in analysis_results if 'error' not in r])} 支股票")
        return analysis_results
    
    def create_investment_report(self, stock_data: Dict[str, Any], 
                               analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        """建立綜合投資報告"""
        ticker = stock_data.get('ticker', 'Unknown')
        company_name = stock_data.get('company_name') or stock_data.get('name', ticker)
        
        # 基本資訊
        basic_info = {
            'ticker': ticker,
            'company_name': company_name,
            'sector': stock_data.get('sector', '未分類'),
            'industry': stock_data.get('industry', '未分類'),
            'market_cap': stock_data.get('market_cap'),
            'current_price': stock_data.get('current_price'),
        }
        
        # 關鍵指標
        key_metrics = {
            'pe_ratio': stock_data.get('trailing_pe'),
            'pb_ratio': stock_data.get('price_to_book'),
            'dividend_yield': stock_data.get('dividend_yield'),
            'debt_to_equity': stock_data.get('debt_to_equity'),
            'free_cashflow': stock_data.get('free_cashflow'),
            'roe': stock_data.get('return_on_equity'),
            'profit_margins': stock_data.get('profit_margins'),
            'value_score': stock_data.get('total_value_score'),
            'value_rating': stock_data.get('value_rating')
        }
        
        # Gemini 分析
        gemini_analysis = {
            'analysis_text': analysis_data.get('analysis_text', '分析不可用'),
            'valuation_analysis': analysis_data.get('valuation_analysis', ''),
            'financial_health': analysis_data.get('financial_health', ''),
            'investment_highlights': analysis_data.get('investment_highlights', ''),
            'potential_risks': analysis_data.get('potential_risks', ''),
            'value_perspective': analysis_data.get('value_perspective', ''),
            'overall_rating': analysis_data.get('overall_rating', ''),
            'analysis_timestamp': analysis_data.get('analysis_timestamp')
        }
        
        investment_report = {
            'basic_info': basic_info,
            'key_metrics': key_metrics,
            'gemini_analysis': gemini_analysis,
            'report_generated': pd.Timestamp.now().isoformat()
        }
        
        return investment_report
    
    def generate_summary_report(self, analysis_results: List[Dict[str, Any]], 
                              top_n: int = 5) -> str:
        """生成投資摘要報告"""
        successful_analyses = [r for r in analysis_results if 'error' not in r]
        
        if not successful_analyses:
            return "無可用的分析結果"
        
        # 取前 N 名
        top_stocks = successful_analyses[:top_n]
        
        summary_prompt = f"""
基於以下 {len(top_stocks)} 支股票的分析結果，請撰寫一份簡潔的投資組合建議報告：

{json.dumps([{
    'ticker': stock.get('ticker'),
    'company_name': stock.get('company_name'),
    'analysis_summary': stock.get('analysis_text', '')[:500] + '...'
} for stock in top_stocks], ensure_ascii=False, indent=2)}

請提供：
1. **投資組合概況**：這些股票的共同特點和行業分布
2. **核心推薦理由**：為什麼這些股票值得關注
3. **風險提醒**：投資時需要注意的主要風險
4. **配置建議**：建議的投資比重和策略

請用繁體中文回應，保持專業且實用的建議。
"""
        
        try:
            response = self.model.generate_content(summary_prompt)
            return response.text
        except Exception as e:
            logging.error(f"生成摘要報告失敗: {e}")
            return f"摘要報告生成失敗: {e}"
    
    def save_analysis_results(self, analysis_results: List[Dict[str, Any]], 
                            filepath: str) -> None:
        """保存分析結果"""
        import os
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 轉換為 DataFrame
        df = pd.DataFrame(analysis_results)
        
        # 保存為多種格式
        base_path = filepath.rsplit('.', 1)[0]
        
        # CSV 格式
        df.to_csv(f"{base_path}.csv", index=False, encoding='utf-8-sig')
        
        # JSON 格式（保持結構）
        with open(f"{base_path}.json", 'w', encoding='utf-8') as f:
            from src.utils import DateTimeEncoder
            json.dump(analysis_results, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        logging.info(f"分析結果已保存到: {base_path}.csv 和 {base_path}.json")
