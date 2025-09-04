"""
測試新增的指標功能
"""

from src.stock_individual_analyzer import StockIndividualAnalyzer

def test_enhanced_indicators():
    print("=== 測試新增指標功能 ===\n")
    
    analyzer = StockIndividualAnalyzer()
    ticker = "AAPL"
    
    try:
        print(f"開始分析 {ticker}...")
        result = analyzer.analyze_stock_comprehensive(ticker)
        
        print(f"✅ 分析完成，共獲得 {len(result.keys())} 個指標\n")
        
        # 測試新增的技術指標
        print("📈 新增技術指標:")
        print(f"  • 50日移動平均線: ${result.get('ma_50', 'N/A')}")
        print(f"  • 200日移動平均線: ${result.get('ma_200', 'N/A')}")
        print(f"  • 價格相對50日線: {result.get('price_vs_ma50', 'N/A')}%")
        print(f"  • 價格相對200日線: {result.get('price_vs_ma200', 'N/A')}%")
        print(f"  • 移動平均線趨勢: {result.get('ma_trend', 'N/A')}")
        print(f"  • 距離52週高點: {result.get('distance_from_52w_high', 'N/A')}%")
        print()
        
        # 測試分析師數據
        print("👔 分析師共識指標:")
        print(f"  • 分析師共識: {result.get('analyst_consensus', 'N/A')}")
        print(f"  • 分析師數量: {result.get('analyst_count', 'N/A')}")
        print(f"  • 上漲潛力: {result.get('upside_potential', 'N/A')}%")
        print(f"  • 最高目標價: ${result.get('target_high', 'N/A')}")
        print(f"  • 最低目標價: ${result.get('target_low', 'N/A')}")
        print()
        
        # 測試財務健康指標
        print("💰 財務健康指標:")
        print(f"  • 毛利率: {result.get('gross_margins', 'N/A')}%")
        print(f"  • 營業利率: {result.get('operating_margins', 'N/A')}%")
        print(f"  • 總現金: ${result.get('total_cash', 'N/A'):,}" if result.get('total_cash') else "  • 總現金: N/A")
        print(f"  • 總債務: ${result.get('total_debt', 'N/A'):,}" if result.get('total_debt') else "  • 總債務: N/A")
        print(f"  • 現金債務比: {result.get('cash_to_debt_ratio', 'N/A')}")
        print(f"  • 速動比率: {result.get('quick_ratio', 'N/A')}")
        print()
        
        # 測試做空分析
        print("📊 做空分析增強:")
        print(f"  • 做空股數: {result.get('shares_short', 'N/A'):,}" if result.get('shares_short') else "  • 做空股數: N/A")
        print(f"  • 做空比例: {result.get('short_percent_of_float', 'N/A')}%")
        print(f"  • 做空趨勢: {result.get('short_trend', 'N/A')}")
        print(f"  • 做空壓力: {result.get('short_pressure', 'N/A')}")
        print()
        
        # 測試風險評估
        print("⚠️ 風險評估指標:")
        print(f"  • 審計風險: {result.get('audit_risk', 'N/A')}")
        print(f"  • 董事會風險: {result.get('board_risk', 'N/A')}")
        print(f"  • 薪酬風險: {result.get('compensation_risk', 'N/A')}")
        print(f"  • 整體風險: {result.get('overall_risk', 'N/A')}")
        print(f"  • 風險評級: {result.get('risk_level', 'N/A')}")
        print(f"  • 波動性等級: {result.get('volatility_level', 'N/A')}")
        print()
        
        # 測試財務報表分析
        print("📋 財務報表分析:")
        print(f"  • 有季度財報: {result.get('has_quarterly_financials', 'N/A')}")
        print(f"  • 營收季度成長: {result.get('revenue_growth_qoq', 'N/A')}%")
        print(f"  • 淨利季度成長: {result.get('income_growth_qoq', 'N/A')}%")
        print(f"  • 現金季度變化: {result.get('cash_change_qoq', 'N/A')}%")
        print()
        
        # 測試股息分析
        print("💸 股息分析:")
        print(f"  • 有股息歷史: {result.get('has_dividend_history', 'N/A')}")
        print(f"  • 年度股息成長: {result.get('annual_dividend_growth', 'N/A')}%")
        print(f"  • 最新股息: ${result.get('latest_dividend', 'N/A')}")
        print(f"  • 五年平均殖利率: {result.get('five_year_avg_dividend_yield', 'N/A')}%")
        print()
        
        # 測試分析師建議
        print("📈 分析師建議詳細:")
        print(f"  • 有建議歷史: {result.get('has_recommendations', 'N/A')}")
        print(f"  • 強烈買入比例: {result.get('latest_strong_buy_pct', 'N/A')}%")
        print(f"  • 買入比例: {result.get('latest_buy_pct', 'N/A')}%")
        print(f"  • 持有比例: {result.get('latest_hold_pct', 'N/A')}%")
        print(f"  • 總分析師數: {result.get('total_analysts', 'N/A')}")
        print()
        
        # 測試綜合評分
        print("🎯 綜合評分:")
        print(f"  • 總評分: {result.get('overall_score', 'N/A')}/100")
        print(f"  • 投資建議: {result.get('recommendation', 'N/A')}")
        print(f"  • 新聞評分: {result.get('news_score', 'N/A')}/100")
        print(f"  • 技術評分: {result.get('technical_score', 'N/A')}/100")
        print(f"  • 籌碼評分: {result.get('chip_score', 'N/A')}/100")
        
        print("\n✅ 所有新增指標測試完成！")
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_indicators()
