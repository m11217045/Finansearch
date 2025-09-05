"""
股票篩選模組 - 根據價值投資標準篩選股票
包含增強的價值投資指標分析和個股綜合分析
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Any
from src.utils import format_currency, format_percentage, format_ratio, DateTimeEncoder
from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
from src.stock_individual_analyzer import StockIndividualAnalyzer


class ValueScreener:
    """價值投資股票篩選器"""
    
    def __init__(self):
        pass
        self.enhanced_analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=False)
        self.individual_analyzer = StockIndividualAnalyzer()
    
    def enhanced_analysis(self, tickers: List[str], use_enhanced_metrics: bool = True) -> pd.DataFrame:
        """
        使用增強價值投資指標進行全面分析
        
        Args:
            tickers: 股票代號列表
            use_enhanced_metrics: 是否使用增強指標
            
        Returns:
            包含增強指標的分析結果DataFrame
        """
        logging.info(f"開始對 {len(tickers)} 支股票進行增強價值投資分析...")
        
        if use_enhanced_metrics:
            # 將 tickers 轉換為股票數據字典列表
            stock_list = [{'ticker': ticker, 'symbol': ticker} for ticker in tickers]
            
            # 使用增強分析器進行全面分析
            batch_results = self.enhanced_analyzer.batch_analyze_stocks(stock_list, max_analysis=len(tickers))
            
            # 從批量分析結果中提取個別股票結果
            analysis_results = batch_results.get('analysis_results', {})
            
            if analysis_results:
                # 轉換結果為 DataFrame 格式
                results_data = []
                for ticker, result in analysis_results.items():
                    if 'error' not in result:
                        # 提取關鍵指標
                        row_data = {
                            'ticker': ticker,
                            'symbol': ticker,
                            'comprehensive_score': result.get('overall_score', 0),
                            'investment_grade': result.get('investment_recommendation', 'N/A'),
                            'fundamental_score': result.get('fundamental_analysis', {}).get('score', 0),
                            'technical_score': result.get('technical_analysis', {}).get('score', 0),
                            'sentiment_score': result.get('news_sentiment_analysis', {}).get('score', 0),
                            'risk_level': result.get('risk_assessment', {}).get('overall_risk', 'MEDIUM')
                        }
                        results_data.append(row_data)
                
                if results_data:
                    results_df = pd.DataFrame(results_data)
                    
                    # 添加傳統價值投資評分以便比較
                    basic_score_df = self.calculate_basic_value_scores(results_df)
                    
                    # 合併結果
                    enhanced_df = pd.merge(results_df, basic_score_df[['ticker', 'basic_value_score']], 
                                         on='ticker', how='left')
                    
                    logging.info(f"完成增強分析，共 {len(enhanced_df)} 支股票")
                    return enhanced_df
        
        # 如果不使用增強指標或增強分析失敗，回退到基本分析
        logging.info("使用基本分析方法...")
        return self.basic_analysis(tickers)
    
    def calculate_basic_value_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算基本價值投資評分（用於與增強指標比較）
        """
        basic_df = df.copy()
        
        # 基本評分權重
        weights = {
            'pe_weight': 0.25,
            'pb_weight': 0.20,
            'dividend_weight': 0.15,
            'debt_weight': 0.20,
            'growth_weight': 0.20
        }
        
        basic_df['basic_value_score'] = 0
        
        # PE評分 (越低越好)
        pe_col = 'trailing_pe' if 'trailing_pe' in df.columns else 'trailingPE'
        if pe_col in df.columns:
            pe_valid = basic_df[basic_df[pe_col].between(5, 50, inclusive='both')]
            if len(pe_valid) > 0:
                pe_rank = pe_valid[pe_col].rank(ascending=True, pct=True)
                basic_df.loc[pe_valid.index, 'basic_value_score'] += pe_rank * weights['pe_weight'] * 100
        
        # PB評分 (越低越好)
        pb_col = 'price_to_book' if 'price_to_book' in df.columns else 'priceToBook'
        if pb_col in df.columns:
            pb_valid = basic_df[basic_df[pb_col].between(0.1, 10, inclusive='both')]
            if len(pb_valid) > 0:
                pb_rank = pb_valid[pb_col].rank(ascending=True, pct=True)
                basic_df.loc[pb_valid.index, 'basic_value_score'] += pb_rank * weights['pb_weight'] * 100
        
        # 股息評分
        dividend_col = 'dividend_yield' if 'dividend_yield' in df.columns else 'dividendYield'
        if dividend_col in df.columns:
            div_valid = basic_df[basic_df[dividend_col].notna()]
            if len(div_valid) > 0:
                div_rank = div_valid[dividend_col].rank(ascending=False, pct=True)
                basic_df.loc[div_valid.index, 'basic_value_score'] += div_rank * weights['dividend_weight'] * 100
        
        # 債務評分 (越低越好)
        debt_col = 'debt_to_equity' if 'debt_to_equity' in df.columns else 'debtToEquity'
        if debt_col in df.columns:
            debt_valid = basic_df[basic_df[debt_col].between(0, 5, inclusive='both')]
            if len(debt_valid) > 0:
                debt_rank = debt_valid[debt_col].rank(ascending=True, pct=True)
                basic_df.loc[debt_valid.index, 'basic_value_score'] += debt_rank * weights['debt_weight'] * 100
        
        # 成長評分
        growth_col = 'revenue_growth_3y_cagr' if 'revenue_growth_3y_cagr' in df.columns else None
        if growth_col and growth_col in df.columns:
            growth_valid = basic_df[basic_df[growth_col].notna()]
            if len(growth_valid) > 0:
                growth_rank = growth_valid[growth_col].rank(ascending=False, pct=True)
                basic_df.loc[growth_valid.index, 'basic_value_score'] += growth_rank * weights['growth_weight'] * 100
        
        return basic_df[['ticker', 'basic_value_score']]
    
    def basic_analysis(self, tickers: List[str]) -> pd.DataFrame:
        """基本分析方法（向後兼容）"""
        # 這裡可以實現基本的分析邏輯
        # 暫時返回空DataFrame
        return pd.DataFrame()
    
    def get_enhanced_top_stocks(self, tickers: List[str], top_n: int = 10, 
                              analysis_type: str = 'comprehensive') -> pd.DataFrame:
        """
        獲取增強分析的頂級股票
        
        Args:
            tickers: 股票代號列表
            top_n: 返回前N名
            analysis_type: 分析類型 ('comprehensive', 'growth', 'value', 'quality')
            
        Returns:
            排序後的頂級股票DataFrame
        """
        logging.info(f"開始 {analysis_type} 分析，目標前 {top_n} 名股票...")
        
        # 進行增強分析
        analysis_df = self.enhanced_analysis(tickers, use_enhanced_metrics=True)
        
        if analysis_df.empty:
            logging.warning("增強分析未返回結果")
            return pd.DataFrame()
        
        # 根據分析類型選擇排序標準
        if analysis_type == 'comprehensive':
            sort_column = 'comprehensive_score'
        elif analysis_type == 'growth':
            # 創建成長評分
            analysis_df['growth_score'] = self._calculate_growth_score(analysis_df)
            sort_column = 'growth_score'
        elif analysis_type == 'value':
            # 創建純價值評分
            analysis_df['pure_value_score'] = self._calculate_pure_value_score(analysis_df)
            sort_column = 'pure_value_score'
        elif analysis_type == 'quality':
            # 創建品質評分
            analysis_df['quality_score'] = self._calculate_quality_score(analysis_df)
            sort_column = 'quality_score'
        else:
            sort_column = 'comprehensive_score'
        
        # 排序並取前N名
        if sort_column in analysis_df.columns:
            top_stocks = analysis_df.nlargest(top_n, sort_column).reset_index(drop=True)
            top_stocks['rank'] = range(1, len(top_stocks) + 1)
        else:
            logging.warning(f"排序欄位 {sort_column} 不存在，使用綜合評分")
            top_stocks = analysis_df.nlargest(top_n, 'comprehensive_score').reset_index(drop=True)
            top_stocks['rank'] = range(1, len(top_stocks) + 1)
        
        logging.info(f"完成 {analysis_type} 分析，返回 {len(top_stocks)} 支股票")
        return top_stocks
    
    def _calculate_growth_score(self, df: pd.DataFrame) -> pd.Series:
        """計算成長評分"""
        score = pd.Series(0.0, index=df.index)
        
        # PEG比率評分
        peg_mask = df['peg_ratio'].between(0.1, 2.0)
        if peg_mask.any():
            score[peg_mask] += (2.0 - df.loc[peg_mask, 'peg_ratio']) * 25
        
        # 營收成長評分
        revenue_growth = df['revenue_growth_3y_cagr'].fillna(0)
        score += np.clip(revenue_growth * 200, 0, 25)  # 最高25分
        
        # EPS成長評分
        eps_growth = df['eps_growth_3y_cagr'].fillna(0)
        score += np.clip(eps_growth * 150, 0, 25)  # 最高25分
        
        # FCF成長評分
        fcf_yield = df['fcf_yield'].fillna(0)
        score += np.clip(fcf_yield * 250, 0, 25)  # 最高25分
        
        return score
    
    def _calculate_pure_value_score(self, df: pd.DataFrame) -> pd.Series:
        """計算純價值評分"""
        score = pd.Series(0.0, index=df.index)
        
        # P/E評分 (越低越好)
        pe_data = df['trailing_pe'] if 'trailing_pe' in df.columns else df.get('trailingPE', pd.Series())
        if not pe_data.empty:
            pe_valid = pe_data.between(5, 30)
            if pe_valid.any():
                score[pe_valid] += (30 - pe_data[pe_valid]) / 25 * 25  # 最高25分
        
        # P/B評分 (越低越好)
        pb_data = df['price_to_book'] if 'price_to_book' in df.columns else df.get('priceToBook', pd.Series())
        if not pb_data.empty:
            pb_valid = pb_data.between(0.1, 5)
            if pb_valid.any():
                score[pb_valid] += (5 - pb_data[pb_valid]) / 4.9 * 25  # 最高25分
        
        # EV/EBITDA評分 (越低越好)
        ev_ebitda = df['ev_ebitda'].fillna(100)
        ev_valid = ev_ebitda.between(5, 25)
        if ev_valid.any():
            score[ev_valid] += (25 - ev_ebitda[ev_valid]) / 20 * 25  # 最高25分
        
        # FCF殖利率評分 (越高越好)
        fcf_yield = df['fcf_yield'].fillna(0)
        score += np.clip(fcf_yield * 250, 0, 25)  # 最高25分
        
        return score
    
    def _calculate_quality_score(self, df: pd.DataFrame) -> pd.Series:
        """計算品質評分"""
        score = pd.Series(0.0, index=df.index)
        
        # ROIC評分
        roic = df['roic'].fillna(0)
        score += np.clip(roic * 100, 0, 25)  # 最高25分
        
        # ROA評分
        roa = df['roa'].fillna(0)
        score += np.clip(roa * 125, 0, 25)  # 最高25分
        
        # 流動比率評分
        current_ratio = df['current_ratio'].fillna(0)
        optimal_ratio = 1.5
        score += 25 - np.abs(current_ratio - optimal_ratio) * 10  # 最佳為1.5
        score = np.clip(score, 0, 100)
        
        # 債務健康評分
        debt_to_assets = df['debt_to_assets'].fillna(0.5)
        score += (1 - debt_to_assets) * 25  # 債務越低越好
        
        return np.clip(score, 0, 100)
    
    def analyze_individual_stock_comprehensive(self, ticker: str) -> Dict[str, Any]:
        """
        對單一股票進行綜合分析 (新聞面、技術面、籌碼面)
        
        Args:
            ticker: 股票代號
            
        Returns:
            包含綜合分析結果的字典
        """
        logging.info(f"開始對 {ticker} 進行個股綜合分析...")
        
        try:
            # 使用個股分析器進行全面分析
            result = self.individual_analyzer.analyze_stock_comprehensive(ticker)
            
            if result:
                # 添加價值投資評分以便比較
                stock_data = {'ticker': ticker, 'symbol': ticker}
                enhanced_result = self.enhanced_analyzer.analyze_stock_comprehensive(stock_data)
                if enhanced_result and 'error' not in enhanced_result:
                    result['value_investment_score'] = enhanced_result.get('overall_score', 0)
                    result['value_investment_grade'] = enhanced_result.get('investment_recommendation', 'N/A')
                
                logging.info(f"完成 {ticker} 的個股綜合分析")
                return result
            else:
                logging.warning(f"無法獲取 {ticker} 的分析數據")
                return {}
                
        except Exception as e:
            logging.error(f"分析 {ticker} 時發生錯誤: {e}")
            return {}
    
    def compare_stocks_comprehensive(self, tickers: List[str]) -> pd.DataFrame:
        """
        對多支股票進行綜合比較分析
        
        Args:
            tickers: 股票代號列表
            
        Returns:
            包含比較結果的DataFrame
        """
        logging.info(f"開始對 {len(tickers)} 支股票進行比較分析...")
        
        results = []
        
        for i, ticker in enumerate(tickers):
            logging.info(f"分析進度: {i+1}/{len(tickers)} - {ticker}")
            
            try:
                result = self.analyze_individual_stock_comprehensive(ticker)
                if result:
                    results.append(result)
                
                # 避免API限制
                if i < len(tickers) - 1:
                    import time
                    time.sleep(1)
                    
            except Exception as e:
                logging.error(f"比較分析 {ticker} 時發生錯誤: {e}")
                continue
        
        if results:
            df = pd.DataFrame(results)
            
            # 按綜合評分排序
            if '综合評分' in df.columns:
                df = df.sort_values('综合評分', ascending=False).reset_index(drop=True)
                df['rank'] = range(1, len(df) + 1)
            
            logging.info(f"完成 {len(results)} 支股票的比較分析")
            return df
        else:
            logging.warning("比較分析未返回有效結果")
            return pd.DataFrame()
    
    def get_news_focused_analysis(self, ticker: str) -> Dict[str, Any]:
        """
        以新聞面為重點的股票分析
        
        Args:
            ticker: 股票代號
            
        Returns:
            重點關注新聞面的分析結果
        """
        logging.info(f"開始對 {ticker} 進行新聞重點分析...")
        
        try:
            # 獲取完整分析
            full_analysis = self.analyze_individual_stock_comprehensive(ticker)
            
            if not full_analysis:
                return {}
            
            # 提取新聞相關信息
            news_analysis = {
                'ticker': ticker,
                'company_name': full_analysis.get('company_name', 'N/A'),
                'current_price': full_analysis.get('current_price', 0),
                'analysis_time': full_analysis.get('analysis_time', ''),
                
                # 新聞面指標 (主要關注)
                'news_sentiment_score': full_analysis.get('news_sentiment_score', 50),
                'sentiment_trend': full_analysis.get('sentiment_trend', 'neutral'),
                'news_impact_score': full_analysis.get('news_impact_score', 50),
                'news_volume': full_analysis.get('news_volume', 0),
                'positive_news_count': full_analysis.get('positive_news_count', 0),
                'negative_news_count': full_analysis.get('negative_news_count', 0),
                'recent_news': full_analysis.get('recent_news', []),
                
                # 輔助指標
                'technical_score': full_analysis.get('technical_score', 50),
                'chip_score': full_analysis.get('chip_score', 50),
                'comprehensive_score': full_analysis.get('综合評分', 0),
                'investment_advice': full_analysis.get('投資建議', 'N/A')
            }
            
            # 重新計算以新聞為主的評分 (新聞面權重提高到70%)
            news_focused_score = (
                news_analysis['news_sentiment_score'] * 0.7 +
                news_analysis['technical_score'] * 0.2 +
                news_analysis['chip_score'] * 0.1
            )
            
            news_analysis['news_focused_score'] = round(news_focused_score, 1)
            news_analysis['news_focused_grade'] = self._get_news_focused_grade(news_focused_score)
            
            logging.info(f"完成 {ticker} 的新聞重點分析")
            return news_analysis
            
        except Exception as e:
            logging.error(f"新聞重點分析 {ticker} 時發生錯誤: {e}")
            return {}
    
    def _get_news_focused_grade(self, score: float) -> str:
        """根據新聞重點評分獲取等級"""
        if score >= 85:
            return "新聞極度正面"
        elif score >= 75:
            return "新聞明顯正面"
        elif score >= 65:
            return "新聞偏向正面"
        elif score >= 55:
            return "新聞中性偏正"
        elif score >= 45:
            return "新聞中性"
        elif score >= 35:
            return "新聞偏向負面"
        elif score >= 25:
            return "新聞明顯負面"
        else:
            return "新聞極度負面"
    
    def batch_news_analysis(self, tickers: List[str]) -> pd.DataFrame:
        """
        批量進行新聞面分析
        
        Args:
            tickers: 股票代號列表
            
        Returns:
            新聞分析結果DataFrame
        """
        logging.info(f"開始批量新聞分析 {len(tickers)} 支股票...")
        
        results = []
        
        for i, ticker in enumerate(tickers):
            logging.info(f"新聞分析進度: {i+1}/{len(tickers)} - {ticker}")
            
            try:
                news_result = self.get_news_focused_analysis(ticker)
                if news_result:
                    results.append(news_result)
                
                # 避免API限制
                if i < len(tickers) - 1:
                    import time
                    time.sleep(1.5)  # 新聞獲取需要更多等待時間
                    
            except Exception as e:
                logging.error(f"批量新聞分析 {ticker} 時發生錯誤: {e}")
                continue
        
        if results:
            df = pd.DataFrame(results)
            
            # 按新聞重點評分排序
            if 'news_focused_score' in df.columns:
                df = df.sort_values('news_focused_score', ascending=False).reset_index(drop=True)
                df['news_rank'] = range(1, len(df) + 1)
            
            logging.info(f"完成 {len(results)} 支股票的批量新聞分析")
            return df
        else:
            logging.warning("批量新聞分析未返回有效結果")
            return pd.DataFrame()
    
    def generate_individual_analysis_report(self, ticker: str) -> str:
        """
        生成個股分析報告
        
        Args:
            ticker: 股票代號
            
        Returns:
            格式化的分析報告字符串
        """
        analysis_result = self.analyze_individual_stock_comprehensive(ticker)
        
        if not analysis_result:
            return f"無法生成 {ticker} 的分析報告"
        
        return self.individual_analyzer.generate_analysis_report(analysis_result)
    
    def calculate_value_score(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        計算價值投資評分，評分越高表示越被低估
        
        評分標準：
        1. 低本益比 (P/E Ratio) - 越低越好 (30%權重)
        2. 低市淨率 (P/B Ratio) - 越低越好 (25%權重)  
        3. 低債務權益比 (Debt to Equity) - 越低越好 (20%權重)
        4. 高股東權益報酬率 (ROE) - 越高越好 (15%權重)
        5. 高利潤率 (Profit Margins) - 越高越好 (10%權重)
        """
        logging.info("開始計算價值投資評分...")
        
        # 建立評分用的數據副本
        scored_df = df.copy()
        
        # 列名映射 - 處理不同的列名
        column_mapping = {
            'pe_ratio': 'trailing_pe',
            'pb_ratio': 'price_to_book', 
            'roe': 'return_on_equity',
            'symbol': 'ticker',
            'name': 'company_name'
        }
        
        # 應用列名映射
        for old_col, new_col in column_mapping.items():
            if old_col in scored_df.columns and new_col not in scored_df.columns:
                scored_df[new_col] = scored_df[old_col]
        
        # 確保必要的數值列存在且為數值型
        required_columns = ['trailing_pe', 'price_to_book', 'debt_to_equity', 'return_on_equity', 'profit_margins']
        
        # 備用列名
        alternative_columns = {
            'trailing_pe': 'pe_ratio',
            'price_to_book': 'pb_ratio',
            'return_on_equity': 'roe',
            'profit_margins': 'profit_margin'
        }
        
        for col in required_columns:
            if col not in scored_df.columns:
                # 嘗試使用備用列名
                alt_col = alternative_columns.get(col)
                if alt_col and alt_col in scored_df.columns:
                    scored_df[col] = scored_df[alt_col]
                else:
                    scored_df[col] = np.nan
            scored_df[col] = pd.to_numeric(scored_df[col], errors='coerce')
        
        # 確保基本列存在
        if 'ticker' not in scored_df.columns and 'symbol' in scored_df.columns:
            scored_df['ticker'] = scored_df['symbol']
        if 'company_name' not in scored_df.columns and 'name' in scored_df.columns:
            scored_df['company_name'] = scored_df['name']
        
        # 初始化評分
        scored_df['value_score'] = 0.0
        scored_df['pe_score'] = 0.0
        scored_df['pb_score'] = 0.0
        scored_df['debt_score'] = 0.0
        scored_df['roe_score'] = 0.0
        scored_df['margin_score'] = 0.0
        
        # 過濾有效數據 - 放寬條件，只要有基本市值信息即可
        valid_stocks = scored_df[
            (scored_df['market_cap'].notna()) | 
            (scored_df['current_price'].notna() & scored_df['current_price'] > 0)
        ].copy()
        
        if len(valid_stocks) == 0:
            logging.warning("沒有有效的股票數據進行評分，將對所有股票給予基礎評分")
            valid_stocks = scored_df.copy()
        
        logging.info(f"對 {len(valid_stocks)} 支股票進行價值評分")
        
        # 評分權重 - 總和為100
        weights = {
            'pe': 30,
            'pb': 25, 
            'debt': 20,
            'roe': 15,
            'margin': 10
        }
        
        # 1. 本益比評分 (權重: 30%)
        pe_col = 'trailing_pe'
        pe_valid = valid_stocks[
            (valid_stocks[pe_col].notna()) & 
            (valid_stocks[pe_col] > 0) & 
            (valid_stocks[pe_col] < 100)
        ]
        
        if len(pe_valid) > 1:
            # 使用反向百分位排名 (越低的PE排名越高)
            pe_percentile = pe_valid[pe_col].rank(pct=True, ascending=False)
            valid_stocks.loc[pe_valid.index, 'pe_score'] = pe_percentile * weights['pe']
            logging.info(f"為 {len(pe_valid)} 支股票計算本益比評分")
        else:
            # 如果數據不足，給所有股票平均分
            valid_stocks['pe_score'] = weights['pe'] * 0.5
            logging.info("本益比數據不足，給予平均評分")
        
        # 2. 市淨率評分 (權重: 25%)
        pb_col = 'price_to_book'
        pb_valid = valid_stocks[
            (valid_stocks[pb_col].notna()) & 
            (valid_stocks[pb_col] > 0) & 
            (valid_stocks[pb_col] < 20)
        ]
        
        if len(pb_valid) > 1:
            pb_percentile = pb_valid[pb_col].rank(pct=True, ascending=False)
            valid_stocks.loc[pb_valid.index, 'pb_score'] = pb_percentile * weights['pb']
            logging.info(f"為 {len(pb_valid)} 支股票計算市淨率評分")
        else:
            valid_stocks['pb_score'] = weights['pb'] * 0.5
            logging.info("市淨率數據不足，給予平均評分")
        
        # 3. 債務權益比評分 (權重: 20%)
        debt_col = 'debt_to_equity'
        debt_valid = valid_stocks[
            (valid_stocks[debt_col].notna()) & 
            (valid_stocks[debt_col] >= 0) &
            (valid_stocks[debt_col] < 10)
        ]
        
        if len(debt_valid) > 1:
            debt_percentile = debt_valid[debt_col].rank(pct=True, ascending=False)
            valid_stocks.loc[debt_valid.index, 'debt_score'] = debt_percentile * weights['debt']
            logging.info(f"為 {len(debt_valid)} 支股票計算債務權益比評分")
        else:
            valid_stocks['debt_score'] = weights['debt'] * 0.5
            logging.info("債務權益比數據不足，給予平均評分")
        
        # 4. 股東權益報酬率評分 (權重: 15%)
        roe_col = 'return_on_equity'
        roe_valid = valid_stocks[
            (valid_stocks[roe_col].notna()) & 
            (valid_stocks[roe_col] > -1) &
            (valid_stocks[roe_col] < 2)
        ]
        
        if len(roe_valid) > 1:
            roe_percentile = roe_valid[roe_col].rank(pct=True, ascending=True)  # 越高越好
            valid_stocks.loc[roe_valid.index, 'roe_score'] = roe_percentile * weights['roe']
            logging.info(f"為 {len(roe_valid)} 支股票計算ROE評分")
        else:
            valid_stocks['roe_score'] = weights['roe'] * 0.5
            logging.info("ROE數據不足，給予平均評分")
        
        # 5. 利潤率評分 (權重: 10%)
        margin_col = 'profit_margins'
        margin_valid = valid_stocks[
            (valid_stocks[margin_col].notna()) & 
            (valid_stocks[margin_col] > -1) &
            (valid_stocks[margin_col] < 1)
        ]
        
        if len(margin_valid) > 1:
            margin_percentile = margin_valid[margin_col].rank(pct=True, ascending=True)  # 越高越好
            valid_stocks.loc[margin_valid.index, 'margin_score'] = margin_percentile * weights['margin']
            logging.info(f"為 {len(margin_valid)} 支股票計算利潤率評分")
        else:
            valid_stocks['margin_score'] = weights['margin'] * 0.5
            logging.info("利潤率數據不足，給予平均評分")
        
        # 計算總評分
        valid_stocks['value_score'] = (
            valid_stocks['pe_score'] + 
            valid_stocks['pb_score'] + 
            valid_stocks['debt_score'] + 
            valid_stocks['roe_score'] + 
            valid_stocks['margin_score']
        )
        
        # 將評分結果合併回原DataFrame
        scored_df.loc[valid_stocks.index, ['value_score', 'pe_score', 'pb_score', 
                                          'debt_score', 'roe_score', 'margin_score']] = valid_stocks[['value_score', 'pe_score', 'pb_score', 
                                                                          'debt_score', 'roe_score', 'margin_score']]
        
        logging.info(f"完成 {len(valid_stocks)} 支股票的價值評分")
        return scored_df
    
    def get_top_undervalued_stocks(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """
        獲取所有股票的價值投資排名，不設硬性篩選標準
        
        Args:
            df: 包含股票數據的DataFrame
            top_n: 返回前N名股票，默認10
            
        Returns:
            按價值評分排序的前N名股票DataFrame
        """
        logging.info(f"開始計算所有股票的價值投資評分並排名...")
        
        if len(df) == 0:
            logging.warning("輸入數據為空")
            return pd.DataFrame()
        
        # 計算價值評分
        scored_df = self.calculate_value_score(df)
        
        # 對於沒有評分的股票，給予基礎評分以確保都能被排名
        scored_df['value_score'] = scored_df['value_score'].fillna(0)
        
        # 確保基本信息完整性
        for col in ['ticker', 'symbol']:
            if col in scored_df.columns:
                break
        else:
            # 如果沒有股票代號，創建一個
            scored_df['ticker'] = scored_df.index.astype(str)
        
        # 確保有公司名稱欄位
        for col in ['company_name', 'name']:
            if col in scored_df.columns:
                # 填補空值
                ticker_col = 'ticker' if 'ticker' in scored_df.columns else 'symbol'
                scored_df[col] = scored_df[col].fillna(scored_df[ticker_col])
                break
        else:
            # 如果沒有公司名稱，使用股票代號
            ticker_col = 'ticker' if 'ticker' in scored_df.columns else 'symbol'
            scored_df['company_name'] = scored_df[ticker_col]
        
        # 按價值評分降序排列（所有股票都參與排名）
        ranked_stocks = scored_df.sort_values('value_score', ascending=False).copy()
        
        # 如果要求的數量超過可用股票數量，返回所有股票
        actual_n = min(top_n, len(ranked_stocks))
        top_stocks = ranked_stocks.head(actual_n).copy()
        
        # 添加排名
        top_stocks = top_stocks.reset_index(drop=True)
        top_stocks['value_rank'] = range(1, len(top_stocks) + 1)
        
        # 選擇要顯示的欄位 - 使用靈活的列名選擇
        potential_columns = [
            ('value_rank', 'value_rank'),
            ('ticker', 'symbol'), 
            ('company_name', 'name'),
            ('sector', 'sector'),
            ('industry', 'industry'),
            ('current_price', 'current_price'),
            ('market_cap', 'market_cap'),
            ('value_score', 'value_score'),
            ('trailing_pe', 'pe_ratio'),
            ('price_to_book', 'pb_ratio'),
            ('debt_to_equity', 'debt_to_equity'),
            ('return_on_equity', 'roe'),
            ('profit_margins', 'profit_margin'),
            ('pe_score', 'pe_score'),
            ('pb_score', 'pb_score'),
            ('debt_score', 'debt_score'),
            ('roe_score', 'roe_score'),
            ('margin_score', 'margin_score')
        ]
        
        # 選擇實際存在的列
        available_columns = []
        for primary_col, alt_col in potential_columns:
            if primary_col in top_stocks.columns:
                available_columns.append(primary_col)
            elif alt_col in top_stocks.columns:
                available_columns.append(alt_col)
        
        if available_columns:
            result_df = top_stocks[available_columns].copy()
        else:
            # 如果沒有找到預期的列，至少返回基本信息
            basic_columns = [col for col in top_stocks.columns if col in ['value_rank', 'value_score']]
            result_df = top_stocks[basic_columns + [top_stocks.columns[0]]].copy()
        
        logging.info(f"成功排名 {len(ranked_stocks)} 支股票，返回前 {len(result_df)} 名")
        
        # 記錄篩選結果
        self.screening_results = {
            'total_stocks_analyzed': len(df),
            'valid_stocks_scored': len(ranked_stocks),
            'top_stocks_selected': len(result_df),
            'average_value_score': result_df['value_score'].mean() if 'value_score' in result_df.columns and len(result_df) > 0 else 0,
            'selection_criteria': 'Value Investment Ranking (價值投資排名)',
            'ranking_method': 'Multi-factor Value Score (多因子價值評分)',
            'min_score': result_df['value_score'].min() if 'value_score' in result_df.columns and len(result_df) > 0 else 0,
            'max_score': result_df['value_score'].max() if 'value_score' in result_df.columns and len(result_df) > 0 else 0
        }
        
        return result_df

    def apply_basic_screening(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        [已廢棄] 保留原有的基本篩選功能以向後兼容
        
        注意：此方法已不推薦使用，建議使用 get_top_undervalued_stocks 方法
        新系統採用動態排名制度，不使用固定閾值篩選
        """
        import warnings
        warnings.warn(
            "apply_basic_screening 方法已廢棄，請使用 get_top_undervalued_stocks",
            DeprecationWarning,
            stacklevel=2
        )
        
        logging.warning("使用已廢棄的基本篩選標準（建議使用 get_top_undervalued_stocks 方法）...")
        
        # 簡單的基本篩選，主要是排除無效數據
        screened_df = df.copy()
        initial_count = len(screened_df)
        
        # 基本有效性篩選
        screened_df = screened_df[
            (screened_df['market_cap'].notna()) & 
            (screened_df['market_cap'] > 1_000_000_000) &  # 市值至少10億美元
            (screened_df['current_price'].notna()) &
            (screened_df['current_price'] > 0)
        ]
        
        final_count = len(screened_df)
        logging.info(f"基本篩選完成: {initial_count} -> {final_count} ({final_count/initial_count*100:.1f}% 通過)")
        
        return screened_df
    
    def calculate_value_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        [已廢棄] 計算價值投資評分
        
        注意：此方法使用固定評分標準，已被動態排名系統取代
        請使用 calculate_value_score() 方法（無s）
        """
        import warnings
        warnings.warn(
            "calculate_value_scores 方法已廢棄，請使用 calculate_value_score",
            DeprecationWarning,
            stacklevel=2
        )
        df = df.copy()
        
        # 定義評分權重
        scoring_weights = {
            'pe_score': 0.25,      # 本益比評分
            'pb_score': 0.20,      # 市淨率評分
            'dividend_score': 0.20, # 股息評分
            'debt_score': 0.15,    # 債務評分
            'cashflow_score': 0.20 # 現金流評分
        }
        
        # 1. 本益比評分（越低越好，滿分10分）
        df['pe_score'] = self._calculate_pe_score(df['trailing_pe'])
        
        # 2. 市淨率評分（越低越好，滿分10分）
        df['pb_score'] = self._calculate_pb_score(df['price_to_book'])
        
        # 3. 股息殖利率評分（適中為佳，滿分10分）
        df['dividend_score'] = self._calculate_dividend_score(df['dividend_yield'])
        
        # 4. 債務評分（低債務高分，滿分10分）
        df['debt_score'] = self._calculate_debt_score(df['debt_to_equity'])
        
        # 5. 現金流評分（基於自由現金流與市值比，滿分10分）
        df['cashflow_score'] = self._calculate_cashflow_score(df['free_cashflow'], df['market_cap'])
        
        # 計算總評分
        df['total_value_score'] = 0
        for score_col, weight in scoring_weights.items():
            df['total_value_score'] += df[score_col].fillna(0) * weight
        
        # 添加評等
        df['value_rating'] = df['total_value_score'].apply(self._get_value_rating)
        
        return df
    
    def _calculate_pe_score(self, pe_series: pd.Series) -> pd.Series:
        """計算本益比評分"""
        def pe_score(pe):
            if pd.isna(pe) or pe <= 0:
                return 0
            elif pe <= 10:
                return 10
            elif pe <= 15:
                return 8
            elif pe <= 20:
                return 6
            elif pe <= 25:
                return 4
            elif pe <= 30:
                return 2
            else:
                return 1
        
        return pe_series.apply(pe_score)
    
    def _calculate_pb_score(self, pb_series: pd.Series) -> pd.Series:
        """計算市淨率評分"""
        def pb_score(pb):
            if pd.isna(pb) or pb <= 0:
                return 0
            elif pb <= 1:
                return 10
            elif pb <= 1.5:
                return 8
            elif pb <= 2:
                return 6
            elif pb <= 3:
                return 4
            elif pb <= 5:
                return 2
            else:
                return 1
        
        return pb_series.apply(pb_score)
    
    def _calculate_dividend_score(self, dividend_series: pd.Series) -> pd.Series:
        """計算股息殖利率評分"""
        def dividend_score(dividend_yield):
            if pd.isna(dividend_yield):
                return 0
            elif dividend_yield == 0:
                return 2  # 不配息但可能有成長潛力
            elif 0.02 <= dividend_yield <= 0.08:  # 2% - 8% 理想範圍
                return 10
            elif 0.01 <= dividend_yield < 0.02:
                return 6
            elif 0.08 < dividend_yield <= 0.12:
                return 8  # 高股息但要小心
            elif dividend_yield > 0.12:
                return 4  # 過高的股息可能有風險
            else:
                return 3
        
        return dividend_series.apply(dividend_score)
    
    def _calculate_debt_score(self, debt_series: pd.Series) -> pd.Series:
        """計算債務評分"""
        def debt_score(debt_ratio):
            if pd.isna(debt_ratio):
                return 5  # 中性評分
            elif debt_ratio <= 0.3:
                return 10
            elif debt_ratio <= 0.6:
                return 8
            elif debt_ratio <= 1.0:
                return 6
            elif debt_ratio <= 1.5:
                return 4
            elif debt_ratio <= 2.0:
                return 2
            else:
                return 1
        
        return debt_series.apply(debt_score)
    
    def _calculate_cashflow_score(self, fcf_series: pd.Series, mcap_series: pd.Series) -> pd.Series:
        """計算現金流評分"""
        def cashflow_score(fcf, market_cap):
            if pd.isna(fcf) or pd.isna(market_cap) or market_cap <= 0:
                return 0
            
            if fcf <= 0:
                return 0
            
            # 計算自由現金流殖利率
            fcf_yield = fcf / market_cap
            
            if fcf_yield >= 0.08:  # 8% 以上
                return 10
            elif fcf_yield >= 0.06:  # 6-8%
                return 8
            elif fcf_yield >= 0.04:  # 4-6%
                return 6
            elif fcf_yield >= 0.02:  # 2-4%
                return 4
            else:  # < 2%
                return 2
        
        return pd.Series([cashflow_score(fcf, mcap) for fcf, mcap in zip(fcf_series, mcap_series)])
    
    def _get_value_rating(self, score: float) -> str:
        """根據評分獲取評等"""
        if pd.isna(score):
            return 'N/A'
        elif score >= 8:
            return '優秀'
        elif score >= 6:
            return '良好'
        elif score >= 4:
            return '普通'
        elif score >= 2:
            return '較差'
        else:
            return '差'
    
    def rank_stocks(self, df: pd.DataFrame, sort_by: str = 'total_value_score') -> pd.DataFrame:
        """根據指定標準對股票進行排名"""
        if sort_by not in df.columns:
            logging.warning(f"排序欄位 '{sort_by}' 不存在，使用預設排序")
            sort_by = 'total_value_score'
        
        # 按評分排序
        ranked_df = df.sort_values(by=sort_by, ascending=False).reset_index(drop=True)
        
        # 添加排名
        ranked_df['rank'] = range(1, len(ranked_df) + 1)
        
        return ranked_df
    
    def get_top_stocks(self, df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
        """獲取評分最高的前 N 支股票"""
        ranked_df = self.rank_stocks(df)
        return ranked_df.head(top_n)
    
    def create_screening_summary(self) -> Dict[str, Any]:
        """建立篩選摘要報告"""
        if not self.screening_results:
            return {"error": "尚未執行篩選"}
        
        summary = {
            "篩選標準": self.criteria,
            "篩選結果": self.screening_results,
            "通過率": f"{self.screening_results['final_count'] / self.screening_results['initial_count'] * 100:.1f}%"
        }
        
        return summary
    
    def export_screening_criteria(self, filepath: str) -> None:
        """匯出篩選標準到 JSON 檔案"""
        import json
        import os
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        export_data = {
            "篩選標準": self.criteria,
            "說明": {
                "market_cap_min": "最小市值（美元）",
                "pe_ratio_max": "最大本益比",
                "pb_ratio_max": "最大市淨率",
                "dividend_yield_min": "最小股息殖利率",
                "debt_to_equity_max": "最大債務權益比"
            }
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        logging.info(f"篩選標準已匯出到: {filepath}")
    
    def generate_sector_analysis(self, df: pd.DataFrame) -> pd.DataFrame:
        """產生各行業的分析統計"""
        if 'sector' not in df.columns:
            logging.warning("數據中缺少行業資訊")
            return pd.DataFrame()
        
        sector_stats = df.groupby('sector').agg({
            'ticker': 'count',
            'trailing_pe': ['mean', 'median'],
            'price_to_book': ['mean', 'median'],
            'dividend_yield': ['mean', 'median'],
            'debt_to_equity': ['mean', 'median'],
            'total_value_score': ['mean', 'median'],
            'market_cap': 'mean'
        }).round(2)
        
        # 簡化欄位名稱
        sector_stats.columns = [
            '股票數量', 'PE平均', 'PE中位數', 'PB平均', 'PB中位數',
            '股息率平均', '股息率中位數', '債務比平均', '債務比中位數',
            '評分平均', '評分中位數', '平均市值'
        ]
        
        # 按評分平均值排序
        sector_stats = sector_stats.sort_values('評分平均', ascending=False)
        
        return sector_stats
