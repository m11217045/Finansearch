#!/usr/bin/env python3
"""
使用信心度改善功能的示例腳本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
from src.screener import ValueScreener
import logging

# 設置日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_stock_with_confidence_requirement(symbol: str):
    """
    使用信心度要求進行股票分析
    
    Args:
        symbol: 股票代號
    """
    
    print(f"🔍 開始分析股票 {symbol}（要求所有分析師信心度≥5分）...")
    
    try:
        # 創建增強分析器，啟用辯論功能
        analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=True)
        
        # 創建測試用股票數據（實際使用時可從yfinance等獲取）
        stock_data = {
            'symbol': symbol,
            'company_name': f'{symbol} Company',
            'pe_ratio': 22.5,
            'pb_ratio': 2.8,
            'dividend_yield': 1.2,
            'debt_to_equity': 0.5,
            'free_cash_flow': 50000000000,
            'roe': 0.18,
            'roa': 0.10,
            'current_price': 150.00,
            'fifty_two_week_high': 180.00,
            'fifty_two_week_low': 120.00
        }
        
        print(f"✅ 成功創建分析器，共有 {len(analyzer.agents)} 位分析師")
        
        # 進行完整的綜合分析
        result = analyzer.analyze_stock_comprehensive(stock_data, include_debate=True)
        
        # 顯示分析結果
        display_comprehensive_analysis_result(result)
        
        return result
        
    except Exception as e:
        print(f"❌ 分析失敗: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

def display_comprehensive_analysis_result(result):
    """顯示綜合分析結果"""
    
    print("\n" + "="*80)
    print("📊 股票綜合分析結果")
    print("="*80)
    
    # 基本資訊
    print(f"股票代號: {result.get('symbol', 'N/A')}")
    print(f"最終評分: {result.get('overall_score', 0):.1f}/100")
    print(f"投資建議: {result.get('investment_recommendation', 'N/A')}")
    
    # 多代理人辯論結果
    if 'multi_agent_debate' in result:
        debate_result = result['multi_agent_debate']
        
        print(f"\n🏛️ 多代理人辯論結果:")
        print(f"參與分析師: {len(debate_result.get('agents_analysis', {}))}")
        print(f"辯論輪次: {len(debate_result.get('debate_rounds', []))}")
        
        # 信心度統計
        confidence_improvements = debate_result.get('confidence_improvement_log', [])
        low_confidence_agents = debate_result.get('low_confidence_agents', [])
        
        if low_confidence_agents or confidence_improvements:
            print(f"\n📈 信心度改善統計:")
            print(f"初始低信心度分析師: {len(low_confidence_agents)}")
            print(f"成功改善案例: {len(confidence_improvements)}")
            
            if confidence_improvements:
                print("改善詳情:")
                for improvement in confidence_improvements:
                    print(f"  • {improvement['agent_name']}: "
                          f"{improvement['old_confidence']} → {improvement['new_confidence']} "
                          f"(第{improvement['round']}輪)")
        
        # 最終共識
        final_consensus = debate_result.get('final_consensus', {})
        print(f"\n🎯 最終共識:")
        print(f"建議: {final_consensus.get('final_recommendation', 'N/A')}")
        print(f"共識度: {final_consensus.get('consensus_level', 0):.1%}")
        print(f"平均信心度: {final_consensus.get('average_confidence', 0):.1f}/10")
        
        # 各分析師最終狀態
        print(f"\n👥 各分析師最終狀態:")
        agents_analysis = debate_result.get('agents_analysis', {})
        
        for agent_name, agent_data in agents_analysis.items():
            confidence = agent_data.get('confidence', 5)
            recommendation = agent_data.get('recommendation', 'HOLD')
            confidence_history = agent_data.get('confidence_history', [confidence])
            
            status_icon = "✅" if confidence >= 5 else "⚠️"
            print(f"  {status_icon} {agent_name}")
            print(f"     建議: {recommendation} | 信心度: {confidence}/10")
            
            if len(confidence_history) > 1:
                print(f"     信心度歷程: {' → '.join(map(str, confidence_history))}")
        
        # 辯論摘要
        debate_summary = debate_result.get('debate_summary', '')
        if debate_summary:
            print(f"\n📝 辯論摘要:")
            for line in debate_summary.split('\n'):
                if line.strip():
                    print(f"  {line}")
    
    # 風險評估
    if 'risk_assessment' in result:
        risk = result['risk_assessment']
        print(f"\n⚠️ 風險評估:")
        print(f"整體風險: {risk.get('overall_risk', 'N/A')}")
        
        if 'specific_risks' in risk:
            print("具體風險:")
            for risk_item in risk['specific_risks'][:3]:
                print(f"  • {risk_item}")
    
    print("\n" + "="*80)

def main():
    """主函數"""
    
    print("🚀 股票分析系統 - 信心度改善功能示例")
    print("="*60)
    
    # 可以分析的股票列表
    test_stocks = ['AAPL', 'MSFT', 'GOOGL', 'TSLA', 'NVDA']
    
    print("可分析的股票:")
    for i, stock in enumerate(test_stocks, 1):
        print(f"  {i}. {stock}")
    
    try:
        choice = input("\n請選擇要分析的股票 (輸入數字1-5，或直接輸入股票代號): ").strip()
        
        if choice.isdigit() and 1 <= int(choice) <= len(test_stocks):
            symbol = test_stocks[int(choice) - 1]
        else:
            symbol = choice.upper()
        
        if not symbol:
            symbol = 'AAPL'  # 預設
        
        print(f"\n選擇分析: {symbol}")
        
        # 執行分析
        result = analyze_stock_with_confidence_requirement(symbol)
        
        if result:
            print(f"\n✅ {symbol} 分析完成！")
            
            # 詢問是否要分析另一支股票
            another = input("\n是否要分析另一支股票？(y/n): ").strip().lower()
            if another == 'y':
                main()  # 遞歸調用
        else:
            print(f"\n❌ {symbol} 分析失敗")
    
    except KeyboardInterrupt:
        print("\n\n👋 使用者中斷，程式結束")
    except Exception as e:
        print(f"\n❌ 程式發生錯誤: {e}")

if __name__ == "__main__":
    main()