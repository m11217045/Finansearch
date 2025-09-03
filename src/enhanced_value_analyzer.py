"""
增強價值投資分析器 - 包含成長性、現金流、效率與回報、估值乘數和財務健康指標
"""

import pandas as pd
import numpy as np
import logging
import time
from typing import Dict, List, Tuple, Any, Optional
import yfinance as yf
from datetime import datetime, timedelta


class EnhancedValueAnalyzer:
    """增強價值投資分析器"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
    def calculate_cagr(self, start_value: float, end_value: float, years: float) -> float:
        """計算複合年均成長率 (CAGR)"""
        if start_value <= 0 or end_value <= 0 or years <= 0:
            return np.nan
        return ((end_value / start_value) ** (1 / years)) - 1
    
    def get_financial_data(self, ticker: str, period: str = "5y") -> Dict[str, Any]:
        """獲取股票的詳細財務數據"""
        try:
            stock = yf.Ticker(ticker)
            
            # 基本信息
            info = stock.info
            
            # 財務報表
            financials = stock.financials  # 年度損益表
            quarterly_financials = stock.quarterly_financials  # 季度損益表
            balance_sheet = stock.balance_sheet  # 年度資產負債表
            quarterly_balance_sheet = stock.quarterly_balance_sheet  # 季度資產負債表
            cash_flow = stock.cash_flow  # 年度現金流量表
            quarterly_cash_flow = stock.quarterly_cash_flow  # 季度現金流量表
            
            return {
                'info': info,
                'financials': financials,
                'quarterly_financials': quarterly_financials,
                'balance_sheet': balance_sheet,
                'quarterly_balance_sheet': quarterly_balance_sheet,
                'cash_flow': cash_flow,
                'quarterly_cash_flow': quarterly_cash_flow
            }
        except Exception as e:
            self.logger.error(f"無法獲取 {ticker} 的財務數據: {e}")
            return {}
    
    def calculate_growth_metrics(self, ticker: str, financial_data: Dict) -> Dict[str, float]:
        """
        計算成長性指標
        
        Returns:
            Dict containing:
            - revenue_growth_1y: 1年營收成長率
            - revenue_growth_3y_cagr: 3年營收CAGR
            - revenue_growth_5y_cagr: 5年營收CAGR
            - eps_growth_1y: 1年EPS成長率
            - eps_growth_3y_cagr: 3年EPS CAGR
            - eps_growth_5y_cagr: 5年EPS CAGR
            - peg_ratio: PEG比率
        """
        metrics = {}
        
        try:
            financials = financial_data.get('financials', pd.DataFrame())
            info = financial_data.get('info', {})
            
            if financials.empty:
                return {key: np.nan for key in [
                    'revenue_growth_1y', 'revenue_growth_3y_cagr', 'revenue_growth_5y_cagr',
                    'eps_growth_1y', 'eps_growth_3y_cagr', 'eps_growth_5y_cagr', 'peg_ratio'
                ]}
            
            # 確保數據按日期排序（最新在前）
            financials = financials.sort_index(axis=1, ascending=False)
            
            # 1. 營收成長率
            if 'Total Revenue' in financials.index:
                revenue_data = financials.loc['Total Revenue'].dropna()
                if len(revenue_data) >= 2:
                    # 1年成長率
                    metrics['revenue_growth_1y'] = (revenue_data.iloc[0] - revenue_data.iloc[1]) / revenue_data.iloc[1]
                    
                    # 3年CAGR
                    if len(revenue_data) >= 4:
                        metrics['revenue_growth_3y_cagr'] = self.calculate_cagr(
                            revenue_data.iloc[3], revenue_data.iloc[0], 3
                        )
                    
                    # 5年CAGR
                    if len(revenue_data) >= 5:
                        metrics['revenue_growth_5y_cagr'] = self.calculate_cagr(
                            revenue_data.iloc[4], revenue_data.iloc[0], 4
                        )
            
            # 2. EPS成長率
            if 'Basic EPS' in financials.index:
                eps_data = financials.loc['Basic EPS'].dropna()
                if len(eps_data) >= 2:
                    # 1年成長率
                    if eps_data.iloc[1] != 0:
                        metrics['eps_growth_1y'] = (eps_data.iloc[0] - eps_data.iloc[1]) / abs(eps_data.iloc[1])
                    
                    # 3年CAGR
                    if len(eps_data) >= 4 and eps_data.iloc[3] > 0:
                        metrics['eps_growth_3y_cagr'] = self.calculate_cagr(
                            eps_data.iloc[3], eps_data.iloc[0], 3
                        )
                    
                    # 5年CAGR
                    if len(eps_data) >= 5 and eps_data.iloc[4] > 0:
                        metrics['eps_growth_5y_cagr'] = self.calculate_cagr(
                            eps_data.iloc[4], eps_data.iloc[0], 4
                        )
            
            # 3. PEG比率計算
            pe_ratio = info.get('trailingPE')
            forward_pe = info.get('forwardPE')
            
            # 使用分析師預期成長率或歷史成長率
            earnings_growth_rate = info.get('earningsGrowth') or info.get('earningsQuarterlyGrowth')
            
            # 如果沒有分析師預期，使用我們計算的EPS成長率
            if not earnings_growth_rate:
                if 'eps_growth_3y_cagr' in metrics and not pd.isna(metrics['eps_growth_3y_cagr']):
                    earnings_growth_rate = metrics['eps_growth_3y_cagr']
                elif 'eps_growth_1y' in metrics and not pd.isna(metrics['eps_growth_1y']):
                    earnings_growth_rate = metrics['eps_growth_1y']
            
            if pe_ratio and earnings_growth_rate and earnings_growth_rate > 0:
                metrics['peg_ratio'] = pe_ratio / (earnings_growth_rate * 100)
            elif forward_pe and earnings_growth_rate and earnings_growth_rate > 0:
                metrics['peg_ratio'] = forward_pe / (earnings_growth_rate * 100)
            
        except Exception as e:
            self.logger.error(f"計算成長性指標時發生錯誤: {e}")
        
        # 填充缺失值
        for key in ['revenue_growth_1y', 'revenue_growth_3y_cagr', 'revenue_growth_5y_cagr',
                   'eps_growth_1y', 'eps_growth_3y_cagr', 'eps_growth_5y_cagr', 'peg_ratio']:
            if key not in metrics:
                metrics[key] = np.nan
        
        return metrics
    
    def calculate_cash_flow_metrics(self, ticker: str, financial_data: Dict) -> Dict[str, float]:
        """
        計算現金流指標
        
        Returns:
            Dict containing:
            - free_cash_flow: 自由現金流
            - fcf_conversion_rate: FCF轉換率(FCF/營收)
            - operating_cf_to_net_income: 營業現金流對淨利比
            - fcf_per_share: 每股自由現金流
            - fcf_yield: 自由現金流殖利率
        """
        metrics = {}
        
        try:
            cash_flow = financial_data.get('cash_flow', pd.DataFrame())
            financials = financial_data.get('financials', pd.DataFrame())
            info = financial_data.get('info', {})
            
            if cash_flow.empty:
                return {key: np.nan for key in [
                    'free_cash_flow', 'fcf_conversion_rate', 'operating_cf_to_net_income',
                    'fcf_per_share', 'fcf_yield'
                ]}
            
            # 確保數據按日期排序（最新在前）
            cash_flow = cash_flow.sort_index(axis=1, ascending=False)
            financials = financials.sort_index(axis=1, ascending=False)
            
            # 1. 自由現金流
            if 'Free Cash Flow' in cash_flow.index:
                fcf = cash_flow.loc['Free Cash Flow'].iloc[0] if not cash_flow.loc['Free Cash Flow'].empty else np.nan
            else:
                # 如果沒有直接的FCF，用營業現金流減去資本支出計算
                operating_cf = cash_flow.loc['Operating Cash Flow'].iloc[0] if 'Operating Cash Flow' in cash_flow.index else np.nan
                capex = cash_flow.loc['Capital Expenditures'].iloc[0] if 'Capital Expenditures' in cash_flow.index else 0
                if not pd.isna(operating_cf):
                    fcf = operating_cf - abs(capex)  # capex通常是負數
                else:
                    fcf = np.nan
            
            metrics['free_cash_flow'] = fcf
            
            # 2. FCF轉換率 (FCF/營收)
            if not pd.isna(fcf) and not financials.empty and 'Total Revenue' in financials.index:
                revenue = financials.loc['Total Revenue'].iloc[0]
                if revenue > 0:
                    metrics['fcf_conversion_rate'] = fcf / revenue
            
            # 3. 營業現金流對淨利比
            if 'Operating Cash Flow' in cash_flow.index and not financials.empty and 'Net Income' in financials.index:
                operating_cf = cash_flow.loc['Operating Cash Flow'].iloc[0]
                net_income = financials.loc['Net Income'].iloc[0]
                if not pd.isna(operating_cf) and not pd.isna(net_income) and net_income != 0:
                    metrics['operating_cf_to_net_income'] = operating_cf / net_income
            
            # 4. 每股自由現金流
            shares_outstanding = info.get('sharesOutstanding')
            if not pd.isna(fcf) and shares_outstanding:
                metrics['fcf_per_share'] = fcf / shares_outstanding
            
            # 5. 自由現金流殖利率
            market_cap = info.get('marketCap')
            if not pd.isna(fcf) and market_cap and market_cap > 0:
                metrics['fcf_yield'] = fcf / market_cap
            
        except Exception as e:
            self.logger.error(f"計算現金流指標時發生錯誤: {e}")
        
        # 填充缺失值
        for key in ['free_cash_flow', 'fcf_conversion_rate', 'operating_cf_to_net_income',
                   'fcf_per_share', 'fcf_yield']:
            if key not in metrics:
                metrics[key] = np.nan
        
        return metrics
    
    def calculate_efficiency_return_metrics(self, ticker: str, financial_data: Dict) -> Dict[str, float]:
        """
        計算效率與回報指標
        
        Returns:
            Dict containing:
            - roa: 資產報酬率 (ROA)
            - roic: 投入資本回報率 (ROIC)
            - asset_turnover: 資產周轉率
            - equity_multiplier: 權益乘數
        """
        metrics = {}
        
        try:
            financials = financial_data.get('financials', pd.DataFrame())
            balance_sheet = financial_data.get('balance_sheet', pd.DataFrame())
            info = financial_data.get('info', {})
            
            if financials.empty or balance_sheet.empty:
                return {key: np.nan for key in ['roa', 'roic', 'asset_turnover', 'equity_multiplier']}
            
            # 確保數據按日期排序（最新在前）
            financials = financials.sort_index(axis=1, ascending=False)
            balance_sheet = balance_sheet.sort_index(axis=1, ascending=False)
            
            # 1. 資產報酬率 (ROA)
            if 'Net Income' in financials.index and 'Total Assets' in balance_sheet.index:
                net_income = financials.loc['Net Income'].iloc[0]
                total_assets = balance_sheet.loc['Total Assets'].iloc[0]
                if not pd.isna(net_income) and not pd.isna(total_assets) and total_assets > 0:
                    metrics['roa'] = net_income / total_assets
            
            # 2. 投入資本回報率 (ROIC)
            # ROIC = NOPAT / Invested Capital
            # NOPAT = Operating Income * (1 - Tax Rate)
            # Invested Capital = Total Equity + Total Debt - Cash
            
            if 'Operating Income' in financials.index:
                operating_income = financials.loc['Operating Income'].iloc[0]
                
                # 計算稅率
                if 'Income Tax Expense' in financials.index and 'Pretax Income' in financials.index:
                    tax_expense = financials.loc['Income Tax Expense'].iloc[0]
                    pretax_income = financials.loc['Pretax Income'].iloc[0]
                    if not pd.isna(tax_expense) and not pd.isna(pretax_income) and pretax_income > 0:
                        tax_rate = abs(tax_expense) / pretax_income
                    else:
                        tax_rate = 0.25  # 使用估計稅率
                else:
                    tax_rate = 0.25  # 使用估計稅率
                
                nopat = operating_income * (1 - tax_rate)
                
                # 計算投入資本
                total_equity = balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0] if 'Total Equity Gross Minority Interest' in balance_sheet.index else balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else np.nan
                total_debt = balance_sheet.loc['Total Debt'].iloc[0] if 'Total Debt' in balance_sheet.index else np.nan
                cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if 'Cash And Cash Equivalents' in balance_sheet.index else 0
                
                if not pd.isna(total_equity) and not pd.isna(total_debt):
                    invested_capital = total_equity + total_debt - cash
                    if invested_capital > 0:
                        metrics['roic'] = nopat / invested_capital
            
            # 3. 資產周轉率
            if 'Total Revenue' in financials.index and 'Total Assets' in balance_sheet.index:
                revenue = financials.loc['Total Revenue'].iloc[0]
                total_assets = balance_sheet.loc['Total Assets'].iloc[0]
                if not pd.isna(revenue) and not pd.isna(total_assets) and total_assets > 0:
                    metrics['asset_turnover'] = revenue / total_assets
            
            # 4. 權益乘數
            if 'Total Assets' in balance_sheet.index:
                total_assets = balance_sheet.loc['Total Assets'].iloc[0]
                total_equity = balance_sheet.loc['Total Equity Gross Minority Interest'].iloc[0] if 'Total Equity Gross Minority Interest' in balance_sheet.index else balance_sheet.loc['Stockholders Equity'].iloc[0] if 'Stockholders Equity' in balance_sheet.index else np.nan
                
                if not pd.isna(total_assets) and not pd.isna(total_equity) and total_equity > 0:
                    metrics['equity_multiplier'] = total_assets / total_equity
            
        except Exception as e:
            self.logger.error(f"計算效率與回報指標時發生錯誤: {e}")
        
        # 填充缺失值
        for key in ['roa', 'roic', 'asset_turnover', 'equity_multiplier']:
            if key not in metrics:
                metrics[key] = np.nan
        
        return metrics
    
    def calculate_valuation_multiples(self, ticker: str, financial_data: Dict) -> Dict[str, float]:
        """
        計算估值乘數
        
        Returns:
            Dict containing:
            - ev_ebitda: 企業價值倍數 (EV/EBITDA)
            - price_to_fcf: 股價/自由現金流 (P/FCF)
            - ev_revenue: 企業價值/營收 (EV/Revenue)
            - price_to_sales: 股價營收比 (P/S)
        """
        metrics = {}
        
        try:
            info = financial_data.get('info', {})
            financials = financial_data.get('financials', pd.DataFrame())
            balance_sheet = financial_data.get('balance_sheet', pd.DataFrame())
            cash_flow = financial_data.get('cash_flow', pd.DataFrame())
            
            market_cap = info.get('marketCap')
            
            # 1. 企業價值倍數 (EV/EBITDA)
            enterprise_value = info.get('enterpriseValue')
            ebitda = info.get('ebitda')
            
            if not enterprise_value and market_cap:
                # 如果沒有直接的EV，計算：EV = Market Cap + Total Debt - Cash
                total_debt = balance_sheet.loc['Total Debt'].iloc[0] if not balance_sheet.empty and 'Total Debt' in balance_sheet.index else 0
                cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0] if not balance_sheet.empty and 'Cash And Cash Equivalents' in balance_sheet.index else 0
                enterprise_value = market_cap + total_debt - cash
            
            if enterprise_value and ebitda and ebitda > 0:
                metrics['ev_ebitda'] = enterprise_value / ebitda
            
            # 2. 股價/自由現金流 (P/FCF)
            if market_cap and not cash_flow.empty:
                if 'Free Cash Flow' in cash_flow.index:
                    fcf = cash_flow.loc['Free Cash Flow'].iloc[0]
                else:
                    operating_cf = cash_flow.loc['Operating Cash Flow'].iloc[0] if 'Operating Cash Flow' in cash_flow.index else np.nan
                    capex = cash_flow.loc['Capital Expenditures'].iloc[0] if 'Capital Expenditures' in cash_flow.index else 0
                    fcf = operating_cf - abs(capex) if not pd.isna(operating_cf) else np.nan
                
                if not pd.isna(fcf) and fcf > 0:
                    metrics['price_to_fcf'] = market_cap / fcf
            
            # 3. 企業價值/營收 (EV/Revenue)
            revenue = info.get('totalRevenue')
            if not revenue and not financials.empty and 'Total Revenue' in financials.index:
                revenue = financials.loc['Total Revenue'].iloc[0]
            
            if enterprise_value and revenue and revenue > 0:
                metrics['ev_revenue'] = enterprise_value / revenue
            
            # 4. 股價營收比 (P/S)
            price_to_sales = info.get('priceToSalesTrailing12Months')
            if price_to_sales:
                metrics['price_to_sales'] = price_to_sales
            elif market_cap and revenue and revenue > 0:
                metrics['price_to_sales'] = market_cap / revenue
            
        except Exception as e:
            self.logger.error(f"計算估值乘數時發生錯誤: {e}")
        
        # 填充缺失值
        for key in ['ev_ebitda', 'price_to_fcf', 'ev_revenue', 'price_to_sales']:
            if key not in metrics:
                metrics[key] = np.nan
        
        return metrics
    
    def calculate_financial_health_metrics(self, ticker: str, financial_data: Dict) -> Dict[str, float]:
        """
        計算財務健康與流動性指標
        
        Returns:
            Dict containing:
            - current_ratio: 流動比率
            - quick_ratio: 速動比率
            - debt_to_assets: 債務資產比
            - interest_coverage: 利息保障倍數
            - cash_ratio: 現金比率
        """
        metrics = {}
        
        try:
            balance_sheet = financial_data.get('balance_sheet', pd.DataFrame())
            financials = financial_data.get('financials', pd.DataFrame())
            
            if balance_sheet.empty:
                return {key: np.nan for key in [
                    'current_ratio', 'quick_ratio', 'debt_to_assets', 
                    'interest_coverage', 'cash_ratio'
                ]}
            
            # 確保數據按日期排序（最新在前）
            balance_sheet = balance_sheet.sort_index(axis=1, ascending=False)
            financials = financials.sort_index(axis=1, ascending=False)
            
            # 1. 流動比率
            if 'Current Assets' in balance_sheet.index and 'Current Liabilities' in balance_sheet.index:
                current_assets = balance_sheet.loc['Current Assets'].iloc[0]
                current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[0]
                if not pd.isna(current_assets) and not pd.isna(current_liabilities) and current_liabilities > 0:
                    metrics['current_ratio'] = current_assets / current_liabilities
            
            # 2. 速動比率
            if 'Current Assets' in balance_sheet.index and 'Current Liabilities' in balance_sheet.index:
                current_assets = balance_sheet.loc['Current Assets'].iloc[0]
                current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[0]
                inventory = balance_sheet.loc['Inventory'].iloc[0] if 'Inventory' in balance_sheet.index else 0
                
                if not pd.isna(current_assets) and not pd.isna(current_liabilities) and current_liabilities > 0:
                    quick_assets = current_assets - inventory
                    metrics['quick_ratio'] = quick_assets / current_liabilities
            
            # 3. 債務資產比
            if 'Total Debt' in balance_sheet.index and 'Total Assets' in balance_sheet.index:
                total_debt = balance_sheet.loc['Total Debt'].iloc[0]
                total_assets = balance_sheet.loc['Total Assets'].iloc[0]
                if not pd.isna(total_debt) and not pd.isna(total_assets) and total_assets > 0:
                    metrics['debt_to_assets'] = total_debt / total_assets
            
            # 4. 利息保障倍數
            if not financials.empty and 'Operating Income' in financials.index and 'Interest Expense' in financials.index:
                operating_income = financials.loc['Operating Income'].iloc[0]
                interest_expense = financials.loc['Interest Expense'].iloc[0]
                if not pd.isna(operating_income) and not pd.isna(interest_expense) and interest_expense > 0:
                    metrics['interest_coverage'] = operating_income / interest_expense
            
            # 5. 現金比率
            if 'Cash And Cash Equivalents' in balance_sheet.index and 'Current Liabilities' in balance_sheet.index:
                cash = balance_sheet.loc['Cash And Cash Equivalents'].iloc[0]
                current_liabilities = balance_sheet.loc['Current Liabilities'].iloc[0]
                if not pd.isna(cash) and not pd.isna(current_liabilities) and current_liabilities > 0:
                    metrics['cash_ratio'] = cash / current_liabilities
            
        except Exception as e:
            self.logger.error(f"計算財務健康指標時發生錯誤: {e}")
        
        # 填充缺失值
        for key in ['current_ratio', 'quick_ratio', 'debt_to_assets', 'interest_coverage', 'cash_ratio']:
            if key not in metrics:
                metrics[key] = np.nan
        
        return metrics
    
    def analyze_stock_comprehensive(self, ticker: str) -> Dict[str, Any]:
        """
        對單一股票進行全面的價值投資分析
        
        Args:
            ticker: 股票代號
            
        Returns:
            包含所有增強指標的字典
        """
        self.logger.info(f"開始分析股票: {ticker}")
        
        # 獲取財務數據
        financial_data = self.get_financial_data(ticker)
        
        if not financial_data:
            self.logger.warning(f"無法獲取 {ticker} 的財務數據")
            return {}
        
        # 計算各類指標
        result = {
            'ticker': ticker,
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        # 基本信息
        info = financial_data.get('info', {})
        result.update({
            'company_name': info.get('longName', ticker),
            'sector': info.get('sector', 'N/A'),
            'industry': info.get('industry', 'N/A'),
            'market_cap': info.get('marketCap'),
            'current_price': info.get('currentPrice'),
        })
        
        # 計算各類增強指標
        growth_metrics = self.calculate_growth_metrics(ticker, financial_data)
        cash_flow_metrics = self.calculate_cash_flow_metrics(ticker, financial_data)
        efficiency_metrics = self.calculate_efficiency_return_metrics(ticker, financial_data)
        valuation_metrics = self.calculate_valuation_multiples(ticker, financial_data)
        health_metrics = self.calculate_financial_health_metrics(ticker, financial_data)
        
        # 合併所有指標
        result.update(growth_metrics)
        result.update(cash_flow_metrics)
        result.update(efficiency_metrics)
        result.update(valuation_metrics)
        result.update(health_metrics)
        
        # 計算綜合評分
        result['comprehensive_score'] = self.calculate_comprehensive_score(result)
        result['investment_grade'] = self.get_investment_grade(result['comprehensive_score'])
        
        self.logger.info(f"完成 {ticker} 的分析")
        return result
    
    def calculate_comprehensive_score(self, metrics: Dict[str, Any]) -> float:
        """
        計算綜合投資評分 (0-100分)
        
        評分權重：
        - 成長性指標: 25%
        - 現金流指標: 25%
        - 效率回報指標: 20%
        - 估值指標: 20%
        - 財務健康指標: 10%
        """
        score = 0.0
        weights = {
            'growth': 0.25,
            'cash_flow': 0.25,
            'efficiency': 0.20,
            'valuation': 0.20,
            'health': 0.10
        }
        
        # 成長性評分 (0-20分)
        growth_score = 0
        peg_ratio = metrics.get('peg_ratio')
        revenue_growth_3y = metrics.get('revenue_growth_3y_cagr')
        eps_growth_3y = metrics.get('eps_growth_3y_cagr')
        
        if peg_ratio and 0 < peg_ratio < 1:
            growth_score += 7  # PEG < 1 是好信號
        elif peg_ratio and 1 <= peg_ratio <= 1.5:
            growth_score += 4
        
        if revenue_growth_3y and revenue_growth_3y > 0.1:  # 10%以上營收成長
            growth_score += 7
        elif revenue_growth_3y and revenue_growth_3y > 0.05:  # 5-10%營收成長
            growth_score += 4
        
        if eps_growth_3y and eps_growth_3y > 0.15:  # 15%以上EPS成長
            growth_score += 6
        elif eps_growth_3y and eps_growth_3y > 0.1:  # 10-15%EPS成長
            growth_score += 3
        
        score += growth_score * weights['growth'] * 5  # 轉換為100分制
        
        # 現金流評分 (0-20分)
        cash_flow_score = 0
        fcf_yield = metrics.get('fcf_yield')
        fcf_conversion_rate = metrics.get('fcf_conversion_rate')
        cf_to_income = metrics.get('operating_cf_to_net_income')
        
        if fcf_yield and fcf_yield > 0.05:  # FCF殖利率>5%
            cash_flow_score += 7
        elif fcf_yield and fcf_yield > 0.03:  # FCF殖利率3-5%
            cash_flow_score += 4
        
        if fcf_conversion_rate and fcf_conversion_rate > 0.1:  # FCF轉換率>10%
            cash_flow_score += 7
        elif fcf_conversion_rate and fcf_conversion_rate > 0.05:  # FCF轉換率5-10%
            cash_flow_score += 4
        
        if cf_to_income and cf_to_income > 1.2:  # 現金流>淨利20%
            cash_flow_score += 6
        elif cf_to_income and cf_to_income > 1:  # 現金流>淨利
            cash_flow_score += 3
        
        score += cash_flow_score * weights['cash_flow'] * 5
        
        # 效率回報評分 (0-20分)
        efficiency_score = 0
        roa = metrics.get('roa')
        roic = metrics.get('roic')
        
        if roa and roa > 0.1:  # ROA>10%
            efficiency_score += 10
        elif roa and roa > 0.05:  # ROA 5-10%
            efficiency_score += 6
        
        if roic and roic > 0.15:  # ROIC>15%
            efficiency_score += 10
        elif roic and roic > 0.1:  # ROIC 10-15%
            efficiency_score += 6
        
        score += efficiency_score * weights['efficiency'] * 5
        
        # 估值評分 (0-20分)
        valuation_score = 0
        ev_ebitda = metrics.get('ev_ebitda')
        price_to_fcf = metrics.get('price_to_fcf')
        
        if ev_ebitda and ev_ebitda < 10:  # EV/EBITDA < 10
            valuation_score += 10
        elif ev_ebitda and ev_ebitda < 15:  # EV/EBITDA 10-15
            valuation_score += 6
        
        if price_to_fcf and price_to_fcf < 15:  # P/FCF < 15
            valuation_score += 10
        elif price_to_fcf and price_to_fcf < 25:  # P/FCF 15-25
            valuation_score += 6
        
        score += valuation_score * weights['valuation'] * 5
        
        # 財務健康評分 (0-10分)
        health_score = 0
        current_ratio = metrics.get('current_ratio')
        debt_to_assets = metrics.get('debt_to_assets')
        
        if current_ratio and current_ratio > 1.5:  # 流動比率>1.5
            health_score += 5
        elif current_ratio and current_ratio > 1:  # 流動比率>1
            health_score += 3
        
        if debt_to_assets and debt_to_assets < 0.3:  # 債務資產比<30%
            health_score += 5
        elif debt_to_assets and debt_to_assets < 0.5:  # 債務資產比30-50%
            health_score += 3
        
        score += health_score * weights['health'] * 10
        
        return min(100, max(0, score))
    
    def get_investment_grade(self, score: float) -> str:
        """根據評分獲取投資等級"""
        if score >= 80:
            return 'A+ (強烈買入)'
        elif score >= 70:
            return 'A (買入)'
        elif score >= 60:
            return 'B+ (適度買入)'
        elif score >= 50:
            return 'B (持有)'
        elif score >= 40:
            return 'C+ (觀望)'
        elif score >= 30:
            return 'C (謹慎)'
        else:
            return 'D (避免)'
    
    def batch_analyze_stocks(self, tickers: List[str]) -> pd.DataFrame:
        """
        批量分析多支股票
        
        Args:
            tickers: 股票代號列表
            
        Returns:
            包含所有股票分析結果的DataFrame
        """
        results = []
        
        for i, ticker in enumerate(tickers):
            self.logger.info(f"分析進度: {i+1}/{len(tickers)} - {ticker}")
            
            try:
                result = self.analyze_stock_comprehensive(ticker)
                if result:
                    results.append(result)
                
                # 避免API限制，每次請求後稍作等待
                if i < len(tickers) - 1:
                    time.sleep(0.2)
                    
            except Exception as e:
                self.logger.error(f"分析 {ticker} 時發生錯誤: {e}")
                continue
        
        if results:
            df = pd.DataFrame(results)
            # 按綜合評分排序
            df = df.sort_values('comprehensive_score', ascending=False).reset_index(drop=True)
            df['rank'] = range(1, len(df) + 1)
            return df
        else:
            return pd.DataFrame()
    
    def generate_analysis_report(self, df: pd.DataFrame, top_n: int = 10) -> str:
        """
        生成分析報告
        
        Args:
            df: 分析結果DataFrame
            top_n: 報告前N名股票
            
        Returns:
            格式化的分析報告字符串
        """
        if df.empty:
            return "沒有可用的分析數據"
        
        report = []
        report.append("=" * 80)
        report.append("增強價值投資分析報告")
        report.append("=" * 80)
        report.append(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"總分析股票數: {len(df)}")
        report.append(f"前 {min(top_n, len(df))} 名投資標的:\n")
        
        # 顯示前N名股票的詳細信息
        top_stocks = df.head(top_n)
        
        for i, (idx, stock) in enumerate(top_stocks.iterrows()):
            report.append(f"第 {i+1} 名: {stock['ticker']} - {stock.get('company_name', 'N/A')}")
            report.append(f"綜合評分: {stock['comprehensive_score']:.1f}/100 ({stock['investment_grade']})")
            report.append(f"行業: {stock.get('sector', 'N/A')} / {stock.get('industry', 'N/A')}")
            
            # 關鍵指標
            report.append("關鍵指標:")
            report.append(f"  • PEG比率: {stock.get('peg_ratio', 'N/A'):.2f}" if not pd.isna(stock.get('peg_ratio')) else "  • PEG比率: N/A")
            report.append(f"  • 3年營收CAGR: {stock.get('revenue_growth_3y_cagr', 'N/A'):.1%}" if not pd.isna(stock.get('revenue_growth_3y_cagr')) else "  • 3年營收CAGR: N/A")
            report.append(f"  • 自由現金流殖利率: {stock.get('fcf_yield', 'N/A'):.1%}" if not pd.isna(stock.get('fcf_yield')) else "  • 自由現金流殖利率: N/A")
            report.append(f"  • ROIC: {stock.get('roic', 'N/A'):.1%}" if not pd.isna(stock.get('roic')) else "  • ROIC: N/A")
            report.append(f"  • 流動比率: {stock.get('current_ratio', 'N/A'):.2f}" if not pd.isna(stock.get('current_ratio')) else "  • 流動比率: N/A")
            report.append("")
        
        # 統計摘要
        report.append("-" * 50)
        report.append("統計摘要:")
        report.append(f"平均綜合評分: {df['comprehensive_score'].mean():.1f}")
        report.append(f"評分標準差: {df['comprehensive_score'].std():.1f}")
        report.append(f"A級以上股票: {len(df[df['comprehensive_score'] >= 70])} 支")
        report.append(f"B級以上股票: {len(df[df['comprehensive_score'] >= 50])} 支")
        
        return "\n".join(report)
