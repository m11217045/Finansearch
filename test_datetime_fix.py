"""
測試 datetime JSON 序列化問題修復
"""

import sys
import json
from datetime import datetime
sys.path.append('.')

def test_datetime_serialization():
    """測試 datetime 物件的 JSON 序列化"""
    print("🧪 測試 datetime JSON 序列化修復...")
    
    try:
        from src.utils import DateTimeEncoder
        
        # 創建包含 datetime 物件的測試數據
        test_data = {
            'ticker': 'PDD',
            'analysis_time': datetime.now(),
            'news_data': [
                {
                    'title': '測試新聞',
                    'publish_timestamp': datetime.now(),
                    'publish_time': '2024-01-01 10:00:00',
                    'content': '測試內容'
                }
            ],
            'metrics': {
                'created_at': datetime.now(),
                'pe_ratio': 15.5
            }
        }
        
        # 測試序列化
        json_str = json.dumps(test_data, cls=DateTimeEncoder, indent=2)
        print("✅ JSON 序列化成功")
        
        # 測試反序列化
        parsed_data = json.loads(json_str)
        print("✅ JSON 反序列化成功")
        
        # 檢查 datetime 是否被正確轉換為字串
        if isinstance(parsed_data['analysis_time'], str):
            print("✅ datetime 物件已正確轉換為字串")
        else:
            print("❌ datetime 物件轉換失敗")
            return False
        
        print(f"範例時間戳: {parsed_data['analysis_time']}")
        return True
        
    except Exception as e:
        print(f"❌ datetime 序列化測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_news_data_structure():
    """測試新聞數據結構序列化"""
    print("\n📰 測試新聞數據結構序列化...")
    
    try:
        from src.enhanced_analyzer import EnhancedStockAnalyzer
        from src.utils import DateTimeEncoder
        import json
        
        # 創建分析器
        analyzer = EnhancedStockAnalyzer()
        
        # 模擬新聞數據（包含可能有問題的 datetime）
        mock_news = [
            {
                'title': '測試新聞',
                'summary': '測試摘要',
                'publisher': 'Test Publisher',
                'publish_time': '2024-01-01 10:00:00',
                'publish_timestamp': datetime.now(),
                'url': 'https://example.com',
                'source': 'Test',
                'content': '測試內容',
                'is_recent': True
            }
        ]
        
        # 測試序列化
        json_str = json.dumps(mock_news, cls=DateTimeEncoder, indent=2)
        print("✅ 新聞數據序列化成功")
        
        # 測試保存功能
        test_results = {
            'ticker': 'TEST',
            'news_data': mock_news,
            'analysis_timestamp': datetime.now()
        }
        
        filepath = analyzer.save_analysis_results(test_results, "test_datetime_fix")
        if filepath:
            print(f"✅ 分析結果保存成功: {filepath}")
            return True
        else:
            print("❌ 分析結果保存失敗")
            return False
        
    except Exception as e:
        print(f"❌ 新聞數據結構測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_comprehensive_analysis():
    """測試完整的綜合分析（模擬 PDD 的情況）"""
    print("\n🔍 測試完整綜合分析...")
    
    try:
        from src.enhanced_analyzer import EnhancedStockAnalyzer
        
        # 創建分析器
        analyzer = EnhancedStockAnalyzer()
        
        # 模擬股票數據
        mock_stock_data = {
            'symbol': 'TEST',
            'name': 'Test Company',
            'current_price': 100.0,
            'market_cap': 1000000000,
            'trailing_pe': 15.5,
            'price_to_book': 2.0
        }
        
        # 模擬分析（不實際調用 API）
        mock_result = {
            'ticker': 'TEST',
            'company_name': 'Test Company',
            'analysis_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'overall_score': 75.5,
            'news_data': [
                {
                    'title': '測試新聞',
                    'publish_timestamp': datetime.now(),
                    'source': 'Test'
                }
            ]
        }
        
        # 測試保存
        filepath = analyzer.save_analysis_results({'TEST': mock_result}, "test_comprehensive")
        if filepath:
            print(f"✅ 綜合分析結果保存成功: {filepath}")
            return True
        else:
            print("❌ 綜合分析結果保存失敗")
            return False
        
    except Exception as e:
        print(f"❌ 綜合分析測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 datetime JSON 序列化修復測試")
    print("=" * 50)
    
    # 測試基本 datetime 序列化
    basic_ok = test_datetime_serialization()
    
    # 測試新聞數據結構
    news_ok = test_news_data_structure()
    
    # 測試綜合分析
    comprehensive_ok = test_comprehensive_analysis()
    
    print(f"\n📊 測試結果:")
    print(f"基本 datetime 序列化: {'✅ 通過' if basic_ok else '❌ 失敗'}")
    print(f"新聞數據結構序列化: {'✅ 通過' if news_ok else '❌ 失敗'}")
    print(f"綜合分析序列化: {'✅ 通過' if comprehensive_ok else '❌ 失敗'}")
    
    if all([basic_ok, news_ok, comprehensive_ok]):
        print("\n🎉 所有測試通過！datetime JSON 序列化問題已修復")
        print("📝 修復摘要:")
        print("- 添加了 DateTimeEncoder 自定義 JSON 編碼器")
        print("- 更新了所有 json.dump 調用使用新編碼器")
        print("- 保持 datetime 物件在內存中的原始格式")
        print("- 只在序列化時轉換為 ISO 格式字串")
    else:
        print("\n⚠️ 部分測試失敗，請檢查修復")
    
    print("\n🏁 測試完成")
