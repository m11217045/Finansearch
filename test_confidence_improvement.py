#!/usr/bin/env python3
"""
測試信心度改善功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_confidence_improvement():
    """測試信心度改善功能"""
    
    print("🧪 開始測試信心度改善功能...")
    
    # 創建測試用的股票數據
    test_stock_data = {
        'symbol': 'AAPL',
        'company_name': 'Apple Inc.',
        'pe_ratio': 25.5,
        'pb_ratio': 3.2,
        'dividend_yield': 0.6,
        'debt_to_equity': 0.4,
        'free_cash_flow': 80000000000,
        'roe': 0.15,
        'roa': 0.12,
        'current_price': 175.50,
        'fifty_two_week_high': 199.62,
        'fifty_two_week_low': 124.17
    }
    
    # 使用較少的分析師進行測試，以便快速驗證
    selected_agents = [
        "巴菲特價值投資師",
        "成長價值投資師",
        "風險管理專家"
    ]
    
    try:
        # 創建增強分析器（啟用辯論）
        analyzer = EnhancedStockAnalyzerWithDebate(
            enable_debate=True,
            selected_agents=selected_agents
        )
        
        print(f"✅ 成功創建分析器，選擇了 {len(selected_agents)} 位分析師")
        
        # 進行多代理人辯論分析
        print("\n🔄 開始多代理人辯論分析...")
        result = analyzer.conduct_multi_agent_debate(test_stock_data, rounds=2)
        
        # 顯示結果
        print("\n📊 辯論分析結果:")
        print("=" * 60)
        
        # 顯示基本資訊
        print(f"股票: {result['symbol']} ({result['company_name']})")
        print(f"總辯論輪次: {len(result['debate_rounds'])}")
        
        # 顯示信心度改善統計
        confidence_improvements = result.get('confidence_improvement_log', [])
        low_confidence_agents = result.get('low_confidence_agents', [])
        
        print(f"\n🎯 信心度改善統計:")
        print(f"初始低信心度分析師: {len(low_confidence_agents)} 位")
        
        if low_confidence_agents:
            print("初始低信心度分析師詳情:")
            for agent in low_confidence_agents:
                print(f"  • {agent['agent_name']}: {agent['confidence']}/10")
        
        if confidence_improvements:
            print(f"成功改善信心度: {len(confidence_improvements)} 位")
            print("改善詳情:")
            for improvement in confidence_improvements:
                print(f"  • {improvement['agent_name']}: "
                      f"{improvement['old_confidence']} → {improvement['new_confidence']} "
                      f"(+{improvement['improvement']}, 第{improvement['round']}輪)")
        
        # 顯示最終分析師狀態
        print(f"\n👥 最終分析師狀態:")
        final_low_confidence = []
        
        for agent_name, agent_data in result['agents_analysis'].items():
            confidence = agent_data.get('confidence', 5)
            recommendation = agent_data.get('recommendation', 'HOLD')
            confidence_history = agent_data.get('confidence_history', [confidence])
            
            status = "✅" if confidence >= 5 else "⚠️"
            print(f"  {status} {agent_name}: {recommendation} (信心度: {confidence}/10)")
            
            if len(confidence_history) > 1:
                print(f"    信心度變化: {' → '.join(map(str, confidence_history))}")
            
            if confidence < 5:
                final_low_confidence.append(agent_name)
        
        # 顯示最終共識
        final_consensus = result['final_consensus']
        print(f"\n🏆 最終共識:")
        print(f"  建議: {final_consensus['final_recommendation']}")
        print(f"  共識度: {final_consensus['consensus_level']:.1%}")
        print(f"  平均信心度: {final_consensus['average_confidence']:.1f}/10")
        
        # 顯示辯論摘要
        print(f"\n📝 辯論摘要:")
        print(result['debate_summary'])
        
        # 測試結果評估
        print(f"\n🔍 測試結果評估:")
        if not final_low_confidence:
            print("✅ 測試成功：所有分析師信心度均達到5分以上")
        else:
            print(f"⚠️ 測試部分成功：仍有 {len(final_low_confidence)} 位分析師信心度不足")
            print(f"   未達標分析師: {', '.join(final_low_confidence)}")
        
        return result
        
    except Exception as e:
        print(f"❌ 測試失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    result = test_confidence_improvement()
    
    if result:
        print("\n🎉 信心度改善功能測試完成！")
    else:
        print("\n💥 測試失敗，請檢查配置和錯誤信息")