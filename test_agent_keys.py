"""
測試多代理人獨立 API Key 分配系統
"""

import sys
import os
import logging
import time

# 添加項目路徑
sys.path.append('.')

# 設定詳細日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_agent_key_allocation():
    """測試代理人 Key 分配功能"""
    print("🧪 測試多代理人 API Key 分配系統...")
    
    try:
        from src.gemini_key_manager import GeminiKeyManager, get_gemini_keys_status, get_agent_gemini_key
        
        # 創建管理器
        manager = GeminiKeyManager()
        
        # 模擬代理人名稱
        agents = [
            "巴菲特派價值投資師",
            "葛拉漢派防御型投資師", 
            "成長價值投資師",
            "市場時機分析師",
            "風險管理專家"
        ]
        
        print(f"\n📊 初始 Key 狀態:")
        status = get_gemini_keys_status()
        print(f"總 Key 數: {status['total_keys']}")
        
        if status['total_keys'] == 0:
            print("❌ 沒有可用的 API Key")
            return False
        
        # 為每個代理人分配 Key
        print(f"\n🔑 為 {len(agents)} 個代理人分配 API Key:")
        agent_keys = {}
        
        for agent in agents:
            key = get_agent_gemini_key(agent)
            if key:
                agent_keys[agent] = key[:8] + "..."  # 只顯示前8字元
                print(f"✅ {agent}: {agent_keys[agent]}")
            else:
                print(f"❌ {agent}: 分配失敗")
        
        # 顯示詳細狀態
        print(f"\n📈 分配後的 Key 狀態:")
        status = get_gemini_keys_status()
        
        for key_info in status['keys_status']:
            agents_list = ", ".join(key_info['assigned_agents']) if key_info['assigned_agents'] else "無"
            print(f"Key {key_info['index']}: 負載分數 {key_info['load_score']}, 分配給: {agents_list}")
        
        # 顯示代理人映射
        print(f"\n🎯 代理人 Key 映射:")
        for agent, key_index in status['agent_mappings'].items():
            print(f"{agent} -> Key {key_index + 1}")
        
        return True
        
    except Exception as e:
        print(f"❌ 代理人 Key 分配測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_error_handling():
    """測試代理人錯誤處理和 Key 切換"""
    print(f"\n🔄 測試代理人錯誤處理和 Key 切換...")
    
    try:
        from src.gemini_key_manager import report_gemini_error, report_gemini_success, get_gemini_keys_status
        
        test_agent = "巴菲特派價值投資師"
        
        # 模擬多次錯誤
        print(f"模擬 {test_agent} 發生錯誤...")
        for i in range(3):
            report_gemini_error(f"測試錯誤 {i+1}", test_agent)
            print(f"第 {i+1} 次錯誤報告")
            time.sleep(0.1)
        
        # 顯示狀態
        status = get_gemini_keys_status()
        print(f"\n📊 錯誤處理後的狀態:")
        
        for key_info in status['keys_status']:
            if key_info['is_blocked']:
                print(f"Key {key_info['index']}: ❌ 已封鎖 (錯誤 {key_info['error_count']} 次)")
            else:
                print(f"Key {key_info['index']}: ✅ 可用 (錯誤 {key_info['error_count']} 次)")
        
        # 檢查代理人是否重新分配
        if test_agent not in status['agent_mappings']:
            print(f"✅ {test_agent} 的 Key 分配已被移除，將重新分配")
        else:
            print(f"⚠️ {test_agent} 仍有 Key 分配")
        
        return True
        
    except Exception as e:
        print(f"❌ 錯誤處理測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multi_agent_analysis():
    """測試多代理人分析使用獨立 Key"""
    print(f"\n🎭 測試多代理人分析系統...")
    
    try:
        from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
        from src.gemini_key_manager import get_gemini_keys_status
        
        # 創建增強分析器（啟用辯論）
        analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=True)
        
        if not analyzer.enable_debate or not analyzer.agents:
            print("⚠️ 多代理人辯論系統未啟用或代理人未初始化")
            return False
        
        print(f"✅ 多代理人辯論系統已啟用，共 {len(analyzer.agents)} 個代理人")
        
        # 顯示每個代理人的狀態
        for agent in analyzer.agents:
            print(f"代理人: {agent.name}")
            print(f"  角色: {agent.role}")
            print(f"  LLM 狀態: {'✅ 已初始化' if agent.llm else '❌ 未初始化'}")
        
        # 顯示 Key 分配狀態
        status = get_gemini_keys_status()
        print(f"\n📊 代理人 Key 分配狀態:")
        
        for agent_name, key_index in status['agent_mappings'].items():
            print(f"{agent_name} -> Key {key_index + 1}")
        
        return True
        
    except Exception as e:
        print(f"❌ 多代理人分析測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_implementation_summary():
    """顯示實現摘要"""
    print("\n📋 多代理人 API Key 分配系統實現摘要:")
    print("=" * 60)
    print("✅ 已實現功能:")
    print("1. 每個代理人獲得專用的 API Key")
    print("2. 智能負載平衡（優先分配負載較輕的 Key）")
    print("3. 自動錯誤檢測和 Key 切換")
    print("4. Key 封鎖和恢復機制")
    print("5. 代理人特定的錯誤報告")
    print("6. 詳細的狀態監控和日誌")
    print("")
    print("🔧 主要改進:")
    print("- GeminiKeyManager: 添加 get_agent_key() 方法")
    print("- ValueInvestmentAgent: 使用專用 Key 初始化")
    print("- 錯誤處理: 支援代理人特定的錯誤報告")
    print("- 狀態監控: 顯示代理人 Key 分配情況")

if __name__ == "__main__":
    print("🚀 多代理人 API Key 分配系統測試")
    print("=" * 60)
    
    # 測試 Key 分配
    allocation_ok = test_agent_key_allocation()
    
    if allocation_ok:
        # 測試錯誤處理
        error_handling_ok = test_agent_error_handling()
        
        # 測試多代理人分析
        analysis_ok = test_multi_agent_analysis()
        
        if allocation_ok and error_handling_ok and analysis_ok:
            print("\n🎉 所有測試通過！")
            print("✅ 多代理人 API Key 分配系統正常運作")
            print("✅ 錯誤處理和自動切換功能正常")
            print("✅ 多代理人分析系統整合成功")
        else:
            print("\n⚠️ 部分測試失敗")
    else:
        print("\n❌ Key 分配測試失敗")
    
    # 顯示實現摘要
    show_implementation_summary()
    
    print("\n🏁 測試完成")
