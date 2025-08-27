"""
測試 Streamlit 應用的列名映射功能
"""

import pandas as pd
import sys
import os

# 添加項目根目錄到路徑
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.data_fetcher import MultiMarketDataFetcher

def test_column_mapping():
    """測試列名映射是否正確"""
    print("=== 測試列名映射 ===")
    
    try:
        # 測試美國科技7巨頭
        fetcher = MultiMarketDataFetcher('faang_plus')
        
        # 獲取少量測試數據
        print("正在獲取測試數據...")
        df = fetcher.fetch_financial_data(max_stocks=2)
        
        if len(df) > 0:
            print(f"✅ 成功獲取 {len(df)} 支股票的數據")
            print(f"📊 數據列名: {list(df.columns)}")
            
            # 檢查關鍵列是否存在
            key_columns = ['symbol', 'name', 'pe_ratio', 'pb_ratio', 'sector']
            missing_columns = [col for col in key_columns if col not in df.columns]
            
            if missing_columns:
                print(f"⚠️  缺少的列: {missing_columns}")
            else:
                print("✅ 所有關鍵列都存在")
            
            # 顯示樣本數據
            print("\n📈 樣本數據:")
            for _, row in df.head(2).iterrows():
                print(f"  {row.get('symbol', 'N/A')}: {row.get('name', 'N/A')}")
                print(f"    PE: {row.get('pe_ratio', 'N/A')}, PB: {row.get('pb_ratio', 'N/A')}")
                print(f"    行業: {row.get('sector', 'N/A')}")
                print()
        else:
            print("❌ 無法獲取測試數據")
            
    except Exception as e:
        print(f"❌ 測試失敗: {e}")

def test_data_types():
    """測試數據類型"""
    print("\n=== 測試數據類型 ===")
    
    try:
        fetcher = MultiMarketDataFetcher('faang_plus')
        df = fetcher.fetch_financial_data(max_stocks=1)
        
        if len(df) > 0:
            print("數據類型檢查:")
            for col in ['pe_ratio', 'pb_ratio', 'market_cap']:
                if col in df.columns:
                    dtype = df[col].dtype
                    sample_value = df[col].iloc[0]
                    print(f"  {col}: {dtype} (樣本值: {sample_value})")
        
    except Exception as e:
        print(f"❌ 數據類型測試失敗: {e}")

if __name__ == "__main__":
    test_column_mapping()
    test_data_types()
    print("\n✅ 測試完成！")
