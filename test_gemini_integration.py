"""
測試 Gemini 新聞搜尋整合的腳本
"""

import os
import sys
import logging

# 添加項目路徑
sys.path.append('.')

# 設定日誌
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_gemini_integration():
    """測試 Gemini 新聞搜尋整合"""
    
    print("🧪 測試 Gemini 新聞搜尋整合...")
    
    # 檢查環境變數
    if not os.getenv('GEMINI_API_KEY'):
        print("❌ 未設定 GEMINI_API_KEY 環境變數")
        print("請先設定環境變數: export GEMINI_API_KEY=your_api_key")
        return False
    
    try:
        # 測試獨立的 Gemini 搜尋器
        print("\n1️⃣ 測試獨立 Gemini 搜尋器...")
        from src.gemini_news_search import GeminiNewsSearcher
        
        searcher = GeminiNewsSearcher()
        if searcher.is_available():
            print("✅ Gemini 搜尋器初始化成功")
            
            # 測試搜尋一個可能沒有 yfinance 新聞的股票
            test_ticker = "2330.TW"
            print(f"🔍 測試搜尋 {test_ticker} 新聞...")
            
            results = searcher.search_stock_news(test_ticker, "台積電", days=7, max_results=3)
            
            if results:
                print(f"✅ 搜尋到 {len(results)} 條新聞")
                for i, news in enumerate(results[:2]):
                    print(f"   {i+1}. {news['title'][:50]}...")
            else:
                print("⚠️ 未搜尋到新聞")
        else:
            print("❌ Gemini 搜尋器不可用")
            return False
        
        # 測試整合的分析器
        print("\n2️⃣ 測試整合的分析器...")
        from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
        
        analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=False)
        print("✅ 分析器初始化成功")
        
        # 測試新聞獲取（會嘗試 yfinance 然後回退到 Gemini）
        test_ticker = "UNKNOWN_STOCK"  # 故意使用不存在的股票代碼來觸發 Gemini 備用搜尋
        print(f"🔍 測試獲取 {test_ticker} 新聞（應該觸發 Gemini 備用搜尋）...")
        
        news_results = analyzer.get_stock_news(test_ticker, days=7)
        
        if news_results:
            print(f"✅ 新聞獲取成功，共 {len(news_results)} 條")
            for i, news in enumerate(news_results[:2]):
                print(f"   {i+1}. {news['title'][:50]}...")
                print(f"      來源: {news.get('source', 'Unknown')}")
        else:
            print("⚠️ 未獲取到新聞")
        
        # 測試真實股票（台積電）
        print(f"\n3️⃣ 測試真實股票 2330.TW 新聞獲取...")
        real_news = analyzer.get_stock_news("2330.TW", days=7)
        
        if real_news:
            print(f"✅ 獲取到 {len(real_news)} 條台積電新聞")
            for i, news in enumerate(real_news[:3]):
                print(f"   {i+1}. {news['title'][:50]}...")
                print(f"      來源: {news.get('source', 'Unknown')}")
        else:
            print("⚠️ 未獲取到台積電新聞")
        
        print("\n🎉 Gemini 新聞搜尋整合測試完成！")
        return True
        
    except Exception as e:
        print(f"❌ 測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def setup_environment():
    """設置測試環境"""
    print("🔧 設置測試環境...")
    
    # 檢查必要的依賴
    required_packages = ['google-generativeai']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '.'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"❌ 缺少必要套件: {', '.join(missing_packages)}")
        print("請安裝: pip install " + " ".join(missing_packages))
        return False
    
    print("✅ 環境檢查完成")
    return True

if __name__ == "__main__":
    print("🚀 Gemini 新聞搜尋整合測試")
    print("=" * 50)
    
    # 設置環境
    if not setup_environment():
        exit(1)
    
    # 執行測試
    success = test_gemini_integration()
    
    if success:
        print("\n✅ 所有測試通過！")
        print("現在可以在 yfinance 找不到新聞時自動使用 Gemini 搜尋")
    else:
        print("\n❌ 測試失敗，請檢查配置")
        exit(1)
