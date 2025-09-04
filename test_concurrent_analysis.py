"""
測試並發分析功能
"""

import time
import logging
from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
from config.settings import MULTI_AGENT_SETTINGS

# 設定日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_concurrent_vs_sequential():
    """測試並發分析 vs 順序分析的效能差異"""
    
    # 測試用的股票數據
    test_stock_data = {
        'symbol': 'AAPL',
        'company_name': 'Apple Inc.',
        'ticker': 'AAPL',
        'currentPrice': 150.0,
        'marketCap': 2500000000000,
        'trailingPE': 25.0,
        'priceToBook': 8.0,
        'dividendYield': 0.005
    }
    
    print("=" * 60)
    print("Agent 並發分析測試")
    print("=" * 60)
    
    # 初始化分析器
    analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=True)
    
    if not analyzer.agents:
        print("❌ 無法初始化 Agent，請檢查設定和 API Key")
        return
    
    print(f"✅ 成功初始化 {len(analyzer.agents)} 個 Agent")
    for agent in analyzer.agents:
        print(f"   - {agent.name}")
    
    print(f"\n⚙️  並發設定:")
    print(f"   - 並發模式: {'啟用' if MULTI_AGENT_SETTINGS.get('enable_concurrent', True) else '停用'}")
    print(f"   - 最大並發數: {MULTI_AGENT_SETTINGS.get('max_concurrent_analysis', 3)}")
    
    # 測試並發分析
    print(f"\n🚀 測試並發分析...")
    start_time = time.time()
    
    try:
        concurrent_results = analyzer._analyze_agents_concurrently(
            test_stock_data, "", "initial"
        )
        concurrent_time = time.time() - start_time
        
        print(f"✅ 並發分析完成")
        print(f"   - 執行時間: {concurrent_time:.2f} 秒")
        print(f"   - 成功分析: {len([r for r in concurrent_results.values() if 'error' not in r])} / {len(concurrent_results)}")
        
        # 顯示分析結果摘要
        for agent_name, result in concurrent_results.items():
            if 'error' not in result:
                print(f"   - {agent_name}: {result.get('recommendation', 'N/A')} (信心度: {result.get('confidence', 'N/A')})")
            else:
                print(f"   - {agent_name}: ❌ 錯誤")
        
    except Exception as e:
        print(f"❌ 並發分析失敗: {e}")
        return
    
    # 測試順序分析（比較用）
    print(f"\n🐌 測試順序分析...")
    start_time = time.time()
    
    try:
        sequential_results = analyzer._analyze_agents_sequentially(
            test_stock_data, "", "initial"
        )
        sequential_time = time.time() - start_time
        
        print(f"✅ 順序分析完成")
        print(f"   - 執行時間: {sequential_time:.2f} 秒")
        print(f"   - 成功分析: {len([r for r in sequential_results.values() if 'error' not in r])} / {len(sequential_results)}")
        
    except Exception as e:
        print(f"❌ 順序分析失敗: {e}")
        sequential_time = float('inf')
    
    # 效能比較
    print(f"\n📊 效能比較:")
    if sequential_time != float('inf') and concurrent_time > 0:
        speedup = sequential_time / concurrent_time
        print(f"   - 並發模式: {concurrent_time:.2f} 秒")
        print(f"   - 順序模式: {sequential_time:.2f} 秒")
        print(f"   - 加速比: {speedup:.2f}x")
        if speedup > 1.5:
            print("   - 🎉 並發分析顯著提升效能！")
        elif speedup > 1.1:
            print("   - ✅ 並發分析有所改善")
        else:
            print("   - ⚠️  並發分析效能提升有限（可能受 API 限制影響）")
    
    print(f"\n💡 建議:")
    print(f"   - 如果 API 有速率限制，並發效果可能受限")
    print(f"   - 可以調整 max_concurrent_analysis 設定來優化效能")
    print(f"   - 在實際使用中，效能提升會更明顯")

if __name__ == "__main__":
    test_concurrent_vs_sequential()
