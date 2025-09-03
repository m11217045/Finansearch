"""
增強價值投資分析主程序
使用精進的價值投資指標進行股票分析
"""

import pandas as pd
import logging
from typing import List
from src.screener import ValueScreener
from src.data_fetcher import MultiMarketDataFetcher
from src.enhanced_value_analyzer import EnhancedValueAnalyzer
from config.settings import STOCK_PORTFOLIOS
import os
from datetime import datetime


def setup_logging():
    """設置日誌配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('enhanced_analysis.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def get_sample_stocks() -> List[str]:
    """獲取樣本股票列表"""
    # 使用著名的價值投資標的作為示例
    return [
        # 科技巨頭
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META',
        # 金融股
        'BRK-B', 'JPM', 'BAC', 'WFC', 'V',
        # 消費品
        'PG', 'KO', 'PEP', 'WMT', 'HD',
        # 醫療保健
        'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK',
        # 工業股
        'MMM', 'CAT', 'HON', 'BA', 'GE'
    ]


def analyze_comprehensive_metrics():
    """進行綜合指標分析"""
    print("=" * 80)
    print("增強價值投資分析系統")
    print("=" * 80)
    
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # 初始化組件
    screener = ValueScreener()
    analyzer = EnhancedValueAnalyzer()
    
    # 獲取樣本股票
    sample_stocks = get_sample_stocks()
    print(f"\\n準備分析 {len(sample_stocks)} 支股票:")
    print(", ".join(sample_stocks))
    
    try:
        # 1. 綜合分析
        print("\\n" + "=" * 50)
        print("1. 綜合價值投資分析")
        print("=" * 50)
        
        comprehensive_results = screener.get_enhanced_top_stocks(
            sample_stocks, 
            top_n=10, 
            analysis_type='comprehensive'
        )
        
        if not comprehensive_results.empty:
            print("\\n【前10名綜合評分股票】")
            display_results(comprehensive_results, 'comprehensive_score')
            
            # 保存結果
            save_results(comprehensive_results, 'comprehensive_analysis.csv')
        
        # 2. 成長性分析
        print("\\n" + "=" * 50)
        print("2. 成長性指標分析")
        print("=" * 50)
        
        growth_results = screener.get_enhanced_top_stocks(
            sample_stocks, 
            top_n=10, 
            analysis_type='growth'
        )
        
        if not growth_results.empty:
            print("\\n【前10名成長性股票】")
            display_growth_metrics(growth_results)
            
            # 保存結果
            save_results(growth_results, 'growth_analysis.csv')
        
        # 3. 純價值分析
        print("\\n" + "=" * 50)
        print("3. 純價值指標分析")
        print("=" * 50)
        
        value_results = screener.get_enhanced_top_stocks(
            sample_stocks, 
            top_n=10, 
            analysis_type='value'
        )
        
        if not value_results.empty:
            print("\\n【前10名價值股票】")
            display_value_metrics(value_results)
            
            # 保存結果
            save_results(value_results, 'value_analysis.csv')
        
        # 4. 品質分析
        print("\\n" + "=" * 50)
        print("4. 品質指標分析")
        print("=" * 50)
        
        quality_results = screener.get_enhanced_top_stocks(
            sample_stocks, 
            top_n=10, 
            analysis_type='quality'
        )
        
        if not quality_results.empty:
            print("\\n【前10名品質股票】")
            display_quality_metrics(quality_results)
            
            # 保存結果
            save_results(quality_results, 'quality_analysis.csv')
        
        # 5. 生成詳細報告
        print("\\n" + "=" * 50)
        print("5. 生成詳細分析報告")
        print("=" * 50)
        
        if not comprehensive_results.empty:
            report = analyzer.generate_analysis_report(comprehensive_results, top_n=5)
            print(report)
            
            # 保存報告
            with open('data/output/enhanced_analysis_report.txt', 'w', encoding='utf-8') as f:
                f.write(report)
            print("\\n✅ 詳細報告已保存至: data/output/enhanced_analysis_report.txt")
        
    except Exception as e:
        logger.error(f"分析過程中發生錯誤: {e}")
        print(f"❌ 分析失敗: {e}")


def display_results(df: pd.DataFrame, score_column: str):
    """顯示分析結果"""
    if df.empty:
        print("沒有可顯示的結果")
        return
    
    print(f"{'排名':<4} {'股票代號':<8} {'公司名稱':<25} {'評分':<8} {'投資等級':<15}")
    print("-" * 70)
    
    for idx, row in df.head(10).iterrows():
        rank = row.get('rank', idx + 1)
        ticker = row.get('ticker', 'N/A')
        name = row.get('company_name', 'N/A')[:20]  # 限制長度
        score = row.get(score_column, 0)
        grade = row.get('investment_grade', 'N/A')
        
        print(f"{rank:<4} {ticker:<8} {name:<25} {score:<8.1f} {grade:<15}")


def display_growth_metrics(df: pd.DataFrame):
    """顯示成長性指標"""
    if df.empty:
        print("沒有可顯示的結果")
        return
    
    print(f"{'排名':<4} {'股票':<8} {'PEG':<8} {'營收3年CAGR':<12} {'EPS3年CAGR':<12} {'FCF殖利率':<10}")
    print("-" * 65)
    
    for idx, row in df.head(10).iterrows():
        rank = row.get('rank', idx + 1)
        ticker = row.get('ticker', 'N/A')
        peg = row.get('peg_ratio', np.nan)
        rev_growth = row.get('revenue_growth_3y_cagr', np.nan)
        eps_growth = row.get('eps_growth_3y_cagr', np.nan)
        fcf_yield = row.get('fcf_yield', np.nan)
        
        peg_str = f"{peg:.2f}" if not pd.isna(peg) else "N/A"
        rev_str = f"{rev_growth:.1%}" if not pd.isna(rev_growth) else "N/A"
        eps_str = f"{eps_growth:.1%}" if not pd.isna(eps_growth) else "N/A"
        fcf_str = f"{fcf_yield:.1%}" if not pd.isna(fcf_yield) else "N/A"
        
        print(f"{rank:<4} {ticker:<8} {peg_str:<8} {rev_str:<12} {eps_str:<12} {fcf_str:<10}")


def display_value_metrics(df: pd.DataFrame):
    """顯示價值指標"""
    if df.empty:
        print("沒有可顯示的結果")
        return
    
    print(f"{'排名':<4} {'股票':<8} {'P/E':<8} {'P/B':<8} {'EV/EBITDA':<10} {'P/FCF':<8}")
    print("-" * 50)
    
    for idx, row in df.head(10).iterrows():
        rank = row.get('rank', idx + 1)
        ticker = row.get('ticker', 'N/A')
        pe = row.get('trailing_pe', row.get('trailingPE', np.nan))
        pb = row.get('price_to_book', row.get('priceToBook', np.nan))
        ev_ebitda = row.get('ev_ebitda', np.nan)
        p_fcf = row.get('price_to_fcf', np.nan)
        
        pe_str = f"{pe:.1f}" if not pd.isna(pe) else "N/A"
        pb_str = f"{pb:.1f}" if not pd.isna(pb) else "N/A"
        ev_str = f"{ev_ebitda:.1f}" if not pd.isna(ev_ebitda) else "N/A"
        fcf_str = f"{p_fcf:.1f}" if not pd.isna(p_fcf) else "N/A"
        
        print(f"{rank:<4} {ticker:<8} {pe_str:<8} {pb_str:<8} {ev_str:<10} {fcf_str:<8}")


def display_quality_metrics(df: pd.DataFrame):
    """顯示品質指標"""
    if df.empty:
        print("沒有可顯示的結果")
        return
    
    print(f"{'排名':<4} {'股票':<8} {'ROIC':<8} {'ROA':<8} {'流動比率':<10} {'債務/資產':<10}")
    print("-" * 55)
    
    for idx, row in df.head(10).iterrows():
        rank = row.get('rank', idx + 1)
        ticker = row.get('ticker', 'N/A')
        roic = row.get('roic', np.nan)
        roa = row.get('roa', np.nan)
        current_ratio = row.get('current_ratio', np.nan)
        debt_to_assets = row.get('debt_to_assets', np.nan)
        
        roic_str = f"{roic:.1%}" if not pd.isna(roic) else "N/A"
        roa_str = f"{roa:.1%}" if not pd.isna(roa) else "N/A"
        cr_str = f"{current_ratio:.2f}" if not pd.isna(current_ratio) else "N/A"
        debt_str = f"{debt_to_assets:.1%}" if not pd.isna(debt_to_assets) else "N/A"
        
        print(f"{rank:<4} {ticker:<8} {roic_str:<8} {roa_str:<8} {cr_str:<10} {debt_str:<10}")


def save_results(df: pd.DataFrame, filename: str):
    """保存分析結果"""
    try:
        # 確保輸出目錄存在
        os.makedirs('data/output', exist_ok=True)
        
        # 保存CSV文件
        filepath = f'data/output/{filename}'
        df.to_csv(filepath, index=False, encoding='utf-8-sig')
        print(f"✅ 結果已保存至: {filepath}")
        
    except Exception as e:
        print(f"❌ 保存結果時發生錯誤: {e}")


def analyze_single_stock(ticker: str):
    """分析單一股票"""
    print(f"\\n分析股票: {ticker}")
    print("=" * 40)
    
    analyzer = EnhancedValueAnalyzer()
    
    try:
        result = analyzer.analyze_stock_comprehensive(ticker)
        
        if result:
            print(f"\\n公司名稱: {result.get('company_name', 'N/A')}")
            print(f"行業: {result.get('sector', 'N/A')} / {result.get('industry', 'N/A')}")
            print(f"綜合評分: {result.get('comprehensive_score', 0):.1f}/100")
            print(f"投資等級: {result.get('investment_grade', 'N/A')}")
            
            print("\\n【成長性指標】")
            print(f"PEG比率: {result.get('peg_ratio', 'N/A')}")
            print(f"3年營收CAGR: {result.get('revenue_growth_3y_cagr', 'N/A')}")
            print(f"3年EPS CAGR: {result.get('eps_growth_3y_cagr', 'N/A')}")
            
            print("\\n【現金流指標】")
            print(f"自由現金流: {result.get('free_cash_flow', 'N/A'):,.0f}" if not pd.isna(result.get('free_cash_flow')) else "自由現金流: N/A")
            print(f"FCF轉換率: {result.get('fcf_conversion_rate', 'N/A')}")
            print(f"FCF殖利率: {result.get('fcf_yield', 'N/A')}")
            
            print("\\n【效率指標】")
            print(f"ROIC: {result.get('roic', 'N/A')}")
            print(f"ROA: {result.get('roa', 'N/A')}")
            
            print("\\n【估值指標】")
            print(f"EV/EBITDA: {result.get('ev_ebitda', 'N/A')}")
            print(f"P/FCF: {result.get('price_to_fcf', 'N/A')}")
            
            print("\\n【財務健康】")
            print(f"流動比率: {result.get('current_ratio', 'N/A')}")
            print(f"速動比率: {result.get('quick_ratio', 'N/A')}")
            print(f"債務/資產: {result.get('debt_to_assets', 'N/A')}")
            
        else:
            print(f"無法獲取 {ticker} 的分析數據")
            
    except Exception as e:
        print(f"分析 {ticker} 時發生錯誤: {e}")


if __name__ == "__main__":
    import numpy as np
    import pandas as pd
    
    while True:
        print("\\n" + "=" * 60)
        print("增強價值投資分析系統")
        print("=" * 60)
        print("1. 綜合批量分析")
        print("2. 單股詳細分析")
        print("3. 退出")
        
        choice = input("\\n請選擇功能 (1-3): ").strip()
        
        if choice == '1':
            analyze_comprehensive_metrics()
        elif choice == '2':
            ticker = input("請輸入股票代號 (例如: AAPL): ").strip().upper()
            if ticker:
                analyze_single_stock(ticker)
            else:
                print("請輸入有效的股票代號")
        elif choice == '3':
            print("感謝使用！")
            break
        else:
            print("無效選擇，請重新輸入")
