"""
測試多市場數據獲取器功能
"""

from src.data_fetcher import MultiMarketDataFetcher, STOCK_PORTFOLIOS

def test_portfolio_configs():
    """測試投資組合配置"""
    print("=== 投資組合配置測試 ===")
    
    for portfolio_type, config in STOCK_PORTFOLIOS.items():
        print(f"\n📊 {portfolio_type}:")
        print(f"  名稱: {config['name']}")
        print(f"  描述: {config['description']}")
        print(f"  來源: {config['source']}")
        
        if config['source'] == 'predefined':
            print(f"  股票數量: {len(config['tickers'])}")
            print(f"  前5支股票: {config['tickers'][:5]}")

def test_multi_market_fetcher():
    """測試多市場數據獲取器"""
    print("\n=== 多市場數據獲取器測試 ===")
    
    # 測試美國科技7巨頭
    try:
        print("\n🧪 測試美國科技7巨頭...")
        fetcher = MultiMarketDataFetcher('faang_plus')
        print(f"  投資組合名稱: {fetcher.get_portfolio_name()}")
        print(f"  投資組合描述: {fetcher.get_portfolio_description()}")
        
        tickers = fetcher.get_tickers()
        print(f"  股票代碼: {tickers}")
        
        # 獲取少量數據進行測試（避免API限制）
        print("  正在獲取財務數據...")
        df = fetcher.fetch_financial_data(max_stocks=3)
        print(f"  成功獲取 {len(df)} 支股票的數據")
        
        if len(df) > 0:
            print(f"  樣本股票: {df['symbol'].tolist()}")
            
    except Exception as e:
        print(f"  錯誤: {e}")

def test_taiwan_stocks():
    """測試台灣股票配置"""
    print("\n🧪 測試台灣股市前50配置...")
    
    try:
        fetcher = MultiMarketDataFetcher('taiwan_top50')
        print(f"  投資組合名稱: {fetcher.get_portfolio_name()}")
        print(f"  投資組合描述: {fetcher.get_portfolio_description()}")
        
        tickers = fetcher.get_tickers()
        print(f"  股票數量: {len(tickers)}")
        print(f"  前10支股票: {tickers[:10]}")
        
    except Exception as e:
        print(f"  錯誤: {e}")

if __name__ == "__main__":
    test_portfolio_configs()
    test_multi_market_fetcher()
    test_taiwan_stocks()
    print("\n✅ 測試完成！")
