"""
測試改進後的價值投資排名系統
"""

import pandas as pd
import sys
import os

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_fetcher import MultiMarketDataFetcher
from src.screener import ValueScreener

def test_ranking_system():
    """測試排名系統"""
    print("=== 測試價值投資排名系統 ===")
    
    try:
        # 獲取美國科技7巨頭數據進行測試
        print("1. 獲取測試數據...")
        fetcher = MultiMarketDataFetcher('faang_plus')
        df = fetcher.fetch_financial_data(max_stocks=None)  # 獲取所有7支股票
        
        if len(df) == 0:
            print("❌ 無法獲取測試數據")
            return
        
        print(f"✅ 成功獲取 {len(df)} 支股票的數據")
        print(f"📊 數據列: {list(df.columns)}")
        
        # 測試篩選器
        print("\n2. 測試價值投資排名...")
        screener = ValueScreener()
        
        # 使用新的排名方法
        ranked_stocks = screener.get_top_undervalued_stocks(df, top_n=10)
        
        if len(ranked_stocks) > 0:
            print(f"✅ 成功排名 {len(ranked_stocks)} 支股票")
            
            # 顯示排名結果
            print("\n📈 排名結果:")
            for _, row in ranked_stocks.iterrows():
                ticker = row.get('ticker', row.get('symbol', 'N/A'))
                name = row.get('company_name', row.get('name', 'N/A'))
                score = row.get('value_score', 'N/A')
                rank = row.get('value_rank', 'N/A')
                
                print(f"  #{rank}: {ticker} - {name}")
                print(f"    評分: {score:.2f}" if isinstance(score, (int, float)) else f"    評分: {score}")
                
                # 顯示各項分評分
                pe_score = row.get('pe_score', 'N/A')
                pb_score = row.get('pb_score', 'N/A')
                if isinstance(pe_score, (int, float)) and isinstance(pb_score, (int, float)):
                    print(f"    PE評分: {pe_score:.1f}, PB評分: {pb_score:.1f}")
                print()
            
            # 顯示篩選統計
            if hasattr(screener, 'screening_results'):
                results = screener.screening_results
                print("📊 篩選統計:")
                print(f"  分析股票總數: {results.get('total_stocks_analyzed', 'N/A')}")
                print(f"  參與評分股票: {results.get('valid_stocks_scored', 'N/A')}")
                print(f"  返回排名股票: {results.get('top_stocks_selected', 'N/A')}")
                print(f"  平均評分: {results.get('average_value_score', 'N/A'):.2f}" if isinstance(results.get('average_value_score'), (int, float)) else f"  平均評分: {results.get('average_value_score', 'N/A')}")
        else:
            print("❌ 排名失敗，無結果返回")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_different_portfolios():
    """測試不同投資組合的排名"""
    print("\n=== 測試不同投資組合排名 ===")
    
    portfolios = ['faang_plus']  # 先只測試一個以節省時間
    
    for portfolio_type in portfolios:
        try:
            print(f"\n🧪 測試 {portfolio_type}...")
            
            fetcher = MultiMarketDataFetcher(portfolio_type)
            df = fetcher.fetch_financial_data(max_stocks=5)  # 限制數量
            
            if len(df) > 0:
                screener = ValueScreener()
                ranked = screener.get_top_undervalued_stocks(df, top_n=3)
                
                print(f"  ✅ {fetcher.get_portfolio_name()}: {len(ranked)} 支股票排名完成")
                
                if len(ranked) > 0:
                    top_stock = ranked.iloc[0]
                    ticker = top_stock.get('ticker', top_stock.get('symbol', 'N/A'))
                    score = top_stock.get('value_score', 'N/A')
                    print(f"  🏆 第一名: {ticker} (評分: {score:.2f})" if isinstance(score, (int, float)) else f"  🏆 第一名: {ticker} (評分: {score})")
            else:
                print(f"  ❌ {portfolio_type}: 無法獲取數據")
                
        except Exception as e:
            print(f"  ❌ {portfolio_type}: 測試失敗 - {e}")

if __name__ == "__main__":
    test_ranking_system()
    test_different_portfolios()
    print("\n✅ 所有測試完成！")
