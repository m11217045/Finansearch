"""
個股綜合分析主程序
重點關注新聞面、技術面、籌碼面的綜合分析
"""

import sys
import os
import logging
import time
from datetime import datetime
from typing import List
from src.stock_individual_analyzer import StockIndividualAnalyzer


def setup_logging():
    """設置日誌配置"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('individual_stock_analysis.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )


def analyze_individual_stock(ticker: str):
    """分析單一個股"""
    print(f"\\n{'='*60}")
    print(f"個股綜合分析 - {ticker.upper()}")
    print(f"{'='*60}")
    
    analyzer = StockIndividualAnalyzer()
    
    try:
        # 進行綜合分析
        print("正在進行綜合分析，請稍候...")
        print("⏳ 分析新聞面...")
        print("⏳ 分析技術面...")
        print("⏳ 分析籌碼面...")
        
        result = analyzer.analyze_stock_comprehensive(ticker)
        
        if result:
            # 顯示基本信息
            print(f"\\n📊 基本信息")
            print(f"公司名稱: {result.get('company_name', 'N/A')}")
            print(f"行業板塊: {result.get('sector', 'N/A')} / {result.get('industry', 'N/A')}")
            print(f"當前股價: ${result.get('current_price', 0):.2f}")
            print(f"市值: ${result.get('market_cap', 0):,.0f}")
            
            # 顯示綜合評分
            comprehensive_score = result.get('综合評分', 0)
            investment_advice = result.get('投資建議', 'N/A')
            
            print(f"\\n🎯 綜合評分: {comprehensive_score:.1f}/100")
            print(f"💡 投資建議: {investment_advice}")
            
            # 顯示各面向評分
            print(f"\\n📈 各面向評分:")
            print(f"📰 新聞面評分: {result.get('news_sentiment_score', 0):.1f}/100 (權重: 50%)")
            print(f"   └─ 情感趨勢: {result.get('sentiment_trend', 'N/A')}")
            print(f"   └─ 新聞影響力: {result.get('news_impact_score', 0):.1f}/100")
            print(f"   └─ 分析新聞數: {result.get('news_volume', 0)} 條")
            
            print(f"📊 技術面評分: {result.get('technical_score', 0):.1f}/100 (權重: 30%)")
            print(f"   └─ 趨勢方向: {result.get('trend_direction', 'N/A')}")
            print(f"   └─ RSI: {result.get('rsi', 0):.1f}")
            print(f"   └─ MACD信號: {result.get('macd_signal', 'N/A')}")
            
            print(f"🏛️  籌碼面評分: {result.get('chip_score', 0):.1f}/100 (權重: 20%)")
            print(f"   └─ 機構持股: {result.get('institutional_ownership', 0):.1f}%")
            print(f"   └─ 內部人持股: {result.get('insider_ownership', 0):.1f}%")
            print(f"   └─ 做空比例: {result.get('short_ratio', 0):.1f}")
            
            # 顯示詳細技術指標
            print(f"\\n📊 詳細技術指標:")
            print(f"支撐位: ${result.get('support_level', 0):.2f}")
            print(f"阻力位: ${result.get('resistance_level', 0):.2f}")
            print(f"成交量趨勢: {result.get('volume_trend', 'N/A')}")
            
            if 'ma20' in result:
                print(f"與20日均線乖離: {result.get('price_vs_ma20', 0):.2f}%")
            
            # 顯示最近新聞
            recent_news = result.get('recent_news', [])
            if recent_news:
                print(f"\\n📰 最近相關新聞 (前5條):")
                for i, news in enumerate(recent_news[:5], 1):
                    title = news.get('title', 'N/A')[:60] + "..." if len(news.get('title', '')) > 60 else news.get('title', 'N/A')
                    source = news.get('source', 'N/A')
                    publish_time = news.get('publish_time', 'N/A')
                    
                    # 格式化時間
                    if isinstance(publish_time, datetime):
                        time_str = publish_time.strftime('%m-%d %H:%M')
                    else:
                        time_str = str(publish_time)[:16]
                    
                    print(f"{i}. {title}")
                    print(f"   來源: {source} | 時間: {time_str}")
            
            # 生成詳細報告選項
            print(f"\\n" + "="*60)
            choice = input("是否生成詳細分析報告？(y/n): ").strip().lower()
            
            if choice == 'y':
                report = analyzer.generate_analysis_report(result)
                
                # 保存報告
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f'data/output/{ticker}_analysis_{timestamp}.txt'
                
                # 確保目錄存在
                os.makedirs('data/output', exist_ok=True)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                
                print(f"✅ 詳細報告已保存至: {filename}")
                print("\\n📄 報告預覽:")
                print(report[:1000] + "..." if len(report) > 1000 else report)
            
        else:
            print(f"❌ 無法獲取 {ticker} 的分析數據，請檢查股票代號是否正確")
            
    except Exception as e:
        print(f"❌ 分析過程中發生錯誤: {e}")
        logging.error(f"分析 {ticker} 時發生錯誤: {e}")


def batch_analyze_stocks(tickers: List[str]):
    """批量分析多支股票"""
    print(f"\\n{'='*60}")
    print(f"批量個股分析 - {len(tickers)} 支股票")
    print(f"{'='*60}")
    
    analyzer = StockIndividualAnalyzer()
    results = []
    
    for i, ticker in enumerate(tickers, 1):
        print(f"\\n[{i}/{len(tickers)}] 分析 {ticker}...")
        
        try:
            result = analyzer.analyze_stock_comprehensive(ticker)
            if result:
                results.append(result)
                score = result.get('综合評分', 0)
                advice = result.get('投資建議', 'N/A')
                print(f"✅ {ticker}: {score:.1f}/100 - {advice}")
            else:
                print(f"❌ {ticker}: 分析失敗")
        
        except Exception as e:
            print(f"❌ {ticker}: 錯誤 - {e}")
        
        # 避免API限制
        if i < len(tickers):
            time.sleep(2)
    
    # 顯示排名結果
    if results:
        print(f"\\n{'='*60}")
        print("批量分析結果排名")
        print(f"{'='*60}")
        
        # 按綜合評分排序
        sorted_results = sorted(results, key=lambda x: x.get('综合評分', 0), reverse=True)
        
        print(f"{'排名':<4} {'股票':<8} {'公司名稱':<20} {'評分':<8} {'投資建議':<12}")
        print("-" * 70)
        
        for i, result in enumerate(sorted_results, 1):
            ticker = result.get('ticker', 'N/A')
            name = result.get('company_name', 'N/A')[:15] + "..." if len(result.get('company_name', '')) > 15 else result.get('company_name', 'N/A')
            score = result.get('综合評分', 0)
            advice = result.get('投資建議', 'N/A')
            
            print(f"{i:<4} {ticker:<8} {name:<20} {score:<8.1f} {advice:<12}")
        
        # 保存批量結果
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'data/output/batch_analysis_{timestamp}.txt'
        
        os.makedirs('data/output', exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("批量個股分析結果\\n")
            f.write("="*50 + "\\n")
            f.write(f"分析時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\\n")
            f.write(f"分析股票數: {len(results)}\\n\\n")
            
            for i, result in enumerate(sorted_results, 1):
                f.write(f"第{i}名: {result.get('ticker', 'N/A')} - {result.get('综合評分', 0):.1f}/100\\n")
                f.write(f"公司: {result.get('company_name', 'N/A')}\\n")
                f.write(f"投資建議: {result.get('投資建議', 'N/A')}\\n")
                f.write(f"新聞面: {result.get('news_sentiment_score', 0):.1f}/100\\n")
                f.write(f"技術面: {result.get('technical_score', 0):.1f}/100\\n")
                f.write(f"籌碼面: {result.get('chip_score', 0):.1f}/100\\n")
                f.write("-" * 30 + "\\n")
        
        print(f"\\n✅ 批量分析結果已保存至: {filename}")


def get_popular_stocks() -> List[str]:
    """獲取熱門股票列表"""
    return [
        # 科技股
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'NVDA', 'NFLX',
        # 金融股
        'JPM', 'BAC', 'WFC', 'GS', 'MS',
        # 消費股
        'PG', 'KO', 'PEP', 'WMT', 'HD',
        # 醫療股
        'JNJ', 'UNH', 'PFE', 'ABBV', 'MRK'
    ]


def main():
    """主程序"""
    setup_logging()
    
    while True:
        print("\\n" + "="*60)
        print("個股綜合分析系統")
        print("重點關注: 新聞面(50%) + 技術面(30%) + 籌碼面(20%)")
        print("="*60)
        print("1. 單股深度分析")
        print("2. 批量股票比較")
        print("3. 熱門股票快速掃描")
        print("4. 退出")
        
        choice = input("\\n請選擇功能 (1-4): ").strip()
        
        if choice == '1':
            ticker = input("\\n請輸入股票代號 (例如: AAPL): ").strip().upper()
            if ticker:
                analyze_individual_stock(ticker)
            else:
                print("❌ 請輸入有效的股票代號")
        
        elif choice == '2':
            print("\\n請輸入要比較的股票代號，用空格分隔")
            print("例如: AAPL MSFT GOOGL")
            tickers_input = input("股票代號: ").strip().upper()
            
            if tickers_input:
                tickers = tickers_input.split()
                if len(tickers) >= 2:
                    batch_analyze_stocks(tickers)
                else:
                    print("❌ 請至少輸入2支股票代號")
            else:
                print("❌ 請輸入股票代號")
        
        elif choice == '3':
            popular_stocks = get_popular_stocks()
            print(f"\\n熱門股票清單: {', '.join(popular_stocks)}")
            
            count = input(f"要分析前幾支股票？(1-{len(popular_stocks)}, 預設10): ").strip()
            try:
                count = int(count) if count else 10
                count = min(count, len(popular_stocks))
            except:
                count = 10
            
            selected_stocks = popular_stocks[:count]
            batch_analyze_stocks(selected_stocks)
        
        elif choice == '4':
            print("感謝使用個股綜合分析系統！")
            break
        
        else:
            print("❌ 無效選擇，請重新輸入")


if __name__ == "__main__":
    import time
    main()
