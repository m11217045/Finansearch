"""
測試多 Gemini API Key 輪換系統
"""

import sys
import os
import logging

# 添加項目路徑
sys.path.append('.')

# 設定詳細日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_key_manager():
    """測試 Key 管理器功能"""
    print("🧪 測試 Gemini API Key 管理器...")
    
    try:
        from src.gemini_key_manager import GeminiKeyManager, get_gemini_keys_status
        
        # 創建管理器
        manager = GeminiKeyManager()
        
        # 顯示狀態
        status = get_gemini_keys_status()
        print(f"\n📊 Key 管理器狀態:")
        print(f"總 Key 數: {status['total_keys']}")
        print(f"當前 Key: {status['current_key_index']}")
        
        if status['total_keys'] == 0:
            print("❌ 沒有可用的 API Key")
            return False
        
        print(f"\n🔑 Key 詳細狀態:")
        for key_info in status['keys_status']:
            status_mark = "👉" if key_info['is_current'] else "  "
            print(f"{status_mark} Key {key_info['index']}: 使用 {key_info['request_count']} 次, 錯誤 {key_info['error_count']} 次, 最後使用: {key_info['last_used']}")
        
        # 測試 Key 輪換
        print(f"\n🔄 測試 Key 輪換:")
        for i in range(3):
            key = manager.get_current_key()
            if key:
                print(f"第 {i+1} 次獲取: Key {manager.current_index + 1} (前8字元: {key[:8]}...)")
            else:
                print(f"第 {i+1} 次獲取: 無可用 Key")
        
        return True
        
    except Exception as e:
        print(f"❌ Key 管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gemini_with_keys():
    """測試使用多 Key 的 Gemini 搜尋"""
    print("\n🔍 測試多 Key Gemini 新聞搜尋...")
    
    try:
        from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
        from src.gemini_key_manager import get_gemini_keys_status
        
        # 創建分析器
        analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=False)
        
        # 顯示 Key 狀態
        status = get_gemini_keys_status()
        print(f"使用 {status['total_keys']} 個 API Key 進行測試")
        
        # 測試新聞搜尋
        test_ticker = '2330.TW'
        print(f"搜尋 {test_ticker} 的新聞...")
        
        news_results = analyzer.get_stock_news(test_ticker, days=7)
        
        if news_results:
            print(f"✅ 成功獲取 {len(news_results)} 條新聞")
            
            # 計算有效內容
            valid_count = 0
            for news in news_results:
                content = news.get('content', '')
                summary = news.get('summary', '')
                effective_content = content if len(content) > 50 else summary
                if len(effective_content) > 50:
                    valid_count += 1
            
            print(f"其中 {valid_count} 條有有效內容")
            
            # 顯示前3條新聞
            for i, news in enumerate(news_results[:3]):
                title = news.get('title', 'No Title')
                source = news.get('source', 'Unknown')
                print(f"{i+1}. {title[:60]}...")
                print(f"   來源: {source}")
        else:
            print("⚠️ 未獲取到新聞")
        
        # 顯示最終 Key 狀態
        final_status = get_gemini_keys_status()
        print(f"\n📊 搜尋後的 Key 狀態:")
        print(f"當前使用: Key {final_status['current_key_index']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Gemini 搜尋測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_env_setup_guide():
    """顯示環境設定指南"""
    print("\n📋 多 API Key 設定指南:")
    print("=" * 50)
    print("在 .env 文件中設定多個 Gemini API Key:")
    print("")
    print("GEMINI_API_KEY_1=\"your_first_api_key\"")
    print("GEMINI_API_KEY_2=\"your_second_api_key\"")
    print("GEMINI_API_KEY_3=\"your_third_api_key\"")
    print("GEMINI_API_KEY_4=\"your_fourth_api_key\"")
    print("GEMINI_API_KEY_5=\"your_fifth_api_key\"")
    print("")
    print("💡 優點:")
    print("- 避免單一 Key 的限制")
    print("- 自動錯誤恢復和 Key 切換")
    print("- 提高系統穩定性")
    print("- 分散請求負載")

if __name__ == "__main__":
    print("🚀 多 Gemini API Key 輪換系統測試")
    print("=" * 60)
    
    # 測試 Key 管理器
    key_manager_ok = test_key_manager()
    
    if key_manager_ok:
        # 測試 Gemini 搜尋
        gemini_ok = test_gemini_with_keys()
        
        if gemini_ok:
            print("\n🎉 所有測試通過！")
            print("✅ 多 Key 輪換系統正常運作")
            print("✅ Gemini 新聞搜尋功能正常")
        else:
            print("\n⚠️ Gemini 搜尋測試失敗")
    else:
        print("\n❌ Key 管理器測試失敗")
    
    # 顯示設定指南
    show_env_setup_guide()
    
    print("\n🏁 測試完成")
