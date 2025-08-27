"""
測試修改後的SP500股票列表
"""

import sys
import os

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_fetcher import MultiMarketDataFetcher, STOCK_PORTFOLIOS

def test_sp500_predefined_list():
    """測試預定義的SP500列表"""
    print("=== 測試預定義的SP500股票列表 ===")
    
    try:
        # 檢查SP500配置
        sp500_config = STOCK_PORTFOLIOS['sp500']
        print(f"✅ SP500配置:")
        print(f"  名稱: {sp500_config['name']}")
        print(f"  描述: {sp500_config['description']}")
        print(f"  來源: {sp500_config['source']}")
        print(f"  股票數量: {len(sp500_config['tickers'])}")
        
        # 顯示前20個股票代號
        print(f"\n📊 前20個股票代號:")
        for i, ticker in enumerate(sp500_config['tickers'][:20]):
            print(f"  {i+1:2d}. {ticker}")
        
        # 創建SP500數據獲取器
        print(f"\n🧪 測試SP500數據獲取器...")
        fetcher = MultiMarketDataFetcher('sp500')
        
        print(f"  投資組合名稱: {fetcher.get_portfolio_name()}")
        print(f"  投資組合描述: {fetcher.get_portfolio_description()}")
        
        # 獲取股票列表
        tickers = fetcher.get_tickers()
        print(f"  獲取到的股票數量: {len(tickers)}")
        
        # 測試獲取少量財務數據
        print(f"\n📈 測試獲取財務數據 (前5支股票)...")
        df = fetcher.fetch_financial_data(max_stocks=5)
        
        if len(df) > 0:
            print(f"✅ 成功獲取 {len(df)} 支股票的財務數據")
            print(f"📊 數據列: {list(df.columns)}")
            
            print(f"\n📋 獲取到的股票:")
            for _, row in df.iterrows():
                symbol = row.get('symbol', 'N/A')
                name = row.get('name', 'N/A')
                sector = row.get('sector', 'N/A')
                print(f"  {symbol}: {name} ({sector})")
        else:
            print(f"❌ 未能獲取財務數據")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()

def test_all_portfolios():
    """測試所有投資組合配置"""
    print(f"\n=== 測試所有投資組合配置 ===")
    
    for portfolio_type, config in STOCK_PORTFOLIOS.items():
        try:
            print(f"\n🧪 測試 {portfolio_type}:")
            print(f"  名稱: {config['name']}")
            print(f"  描述: {config['description']}")
            print(f"  來源: {config['source']}")
            
            if config['source'] == 'predefined':
                print(f"  股票數量: {len(config['tickers'])}")
                print(f"  前5支股票: {config['tickers'][:5]}")
                
                # 測試創建獲取器
                fetcher = MultiMarketDataFetcher(portfolio_type)
                tickers = fetcher.get_tickers()
                print(f"  ✅ 成功獲取 {len(tickers)} 個股票代號")
            else:
                print(f"  ❌ 未支援的來源類型: {config['source']}")
                
        except Exception as e:
            print(f"  ❌ {portfolio_type} 測試失敗: {e}")

if __name__ == "__main__":
    test_sp500_predefined_list()
    test_all_portfolios()
    print(f"\n✅ 所有測試完成！")
