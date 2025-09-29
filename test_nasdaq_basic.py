"""
測試程式 - 那斯達克權重前十股票基本分析（不含AI分析）
"""

import pandas as pd
import logging
import os
from datetime import datetime
import json

# 導入自訂模組
from src.utils import setup_logging, load_env_variables, create_output_directory, save_dataframe, DateTimeEncoder
from src.data_fetcher import NasdaqDataFetcher
from main import analyze_nasdaq_index_recommendation


def test_nasdaq_basic():
    """測試基本的那斯達克分析功能"""
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("那斯達克權重前十股票基本測試啟動")
    logger.info("=" * 60)
    
    try:
        # 建立輸出目錄
        output_dir = create_output_directory()
        logger.info(f"輸出目錄: {output_dir}")
        
        # 階段 1: 獲取那斯達克權重前十股票數據
        logger.info("\n階段 1: 獲取那斯達克權重前十股票數據")
        logger.info("-" * 40)
        
        fetcher = NasdaqDataFetcher()
        
        # 獲取股票代碼列表
        tickers = fetcher.get_nasdaq_top10_tickers()
        logger.info(f"那斯達克權重前十股票: {tickers}")
        
        fetcher.save_tickers_to_csv(f"{output_dir}/nasdaq_top10_tickers.csv")
        
        # 批量獲取股票數據
        logger.info(f"開始獲取 {len(tickers)} 支股票的財務數據...")
        raw_data = fetcher.batch_fetch_stock_data(tickers, max_stocks=10)
        
        if raw_data.empty:
            logger.error("無法獲取股票數據，程式結束")
            return
        
        # 保存原始數據
        save_dataframe(raw_data, f"{output_dir}/nasdaq_raw_data", ['csv', 'json'])
        logger.info(f"原始數據已保存，包含 {len(raw_data)} 支股票")
        
        # 為每支股票加上排名資訊
        raw_data['weight_rank'] = range(1, len(raw_data) + 1)
        raw_data['analysis_type'] = '那斯達克權重前十'
        
        # 顯示股票簡要信息
        logger.info("\n那斯達克權重前十股票詳情:")
        for _, stock in raw_data.iterrows():
            company_name = stock.get('company_name', stock.get('shortName', 'N/A'))
            market_cap = f"${stock['market_cap']/1e9:.0f}B" if pd.notna(stock['market_cap']) else "N/A"
            logger.info(f"  第{int(stock['weight_rank'])}名: {stock['ticker']} ({company_name}) - 市值: {market_cap}")
        
        # 階段 2: 那斯達克指數投資建議分析
        logger.info("\n階段 2: 那斯達克指數投資建議分析")
        logger.info("-" * 40)
        
        nasdaq_recommendation = analyze_nasdaq_index_recommendation()
        
        # 保存指數建議
        with open(f"{output_dir}/nasdaq_index_recommendation.json", 'w', encoding='utf-8') as f:
            json.dump(nasdaq_recommendation, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        logger.info(f"那斯達克指數投資建議: {nasdaq_recommendation['recommendation']}")
        logger.info(f"建議理由: {nasdaq_recommendation['reasoning']}")
        logger.info(f"分析評分: {nasdaq_recommendation.get('score', 0)}/4")
        
        # 顯示技術分析信號
        if 'signals' in nasdaq_recommendation:
            logger.info("\n技術分析信號:")
            for signal in nasdaq_recommendation['signals']:
                logger.info(f"  • {signal}")
        
        # 建立簡要報告
        create_basic_report(raw_data, nasdaq_recommendation, output_dir)
        
        logger.info(f"\n測試程式執行完成！")
        logger.info(f"所有結果已保存到: {output_dir}")
        logger.info("=" * 60)
        
        # 顯示輸出檔案列表
        output_files = [f for f in os.listdir(output_dir) if os.path.isfile(os.path.join(output_dir, f))]
        logger.info("輸出檔案:")
        for file in sorted(output_files):
            logger.info(f"  - {file}")
        
    except Exception as e:
        logger.error(f"程式執行過程中發生錯誤: {e}")
        raise


def create_basic_report(nasdaq_stocks: pd.DataFrame, index_recommendation: dict, output_dir: str) -> None:
    """建立基本測試報告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
那斯達克權重前十股票基本測試報告
生成時間: {timestamp}

=== 那斯達克指數投資建議 ===
投資建議: {index_recommendation.get('recommendation', '未知')}
建議理由: {index_recommendation.get('reasoning', '無資料')}
分析評分: {index_recommendation.get('score', 0)}/4

技術分析指標:
- 當前價格: ${index_recommendation.get('current_price', 0):.2f}
- 50日均線: ${index_recommendation.get('sma_50', 0):.2f}
- 200日均線: ${index_recommendation.get('sma_200', 0):.2f}

價格變化:
- 近1個月: {index_recommendation.get('price_changes', {}).get('1_month', 0):.1f}%
- 近3個月: {index_recommendation.get('price_changes', {}).get('3_month', 0):.1f}%
- 近1年: {index_recommendation.get('price_changes', {}).get('1_year', 0):.1f}%

=== 那斯達克權重前十股票詳情 ===
"""
    
    for i, row in nasdaq_stocks.iterrows():
        pe = f"{row['trailing_pe']:.2f}" if pd.notna(row['trailing_pe']) else "N/A"
        pb = f"{row['price_to_book']:.2f}" if pd.notna(row['price_to_book']) else "N/A"
        div_yield = f"{row['dividend_yield']*100:.2f}%" if pd.notna(row['dividend_yield']) and row['dividend_yield'] > 0 else "N/A"
        market_cap = f"${row['market_cap']/1e9:.1f}B" if pd.notna(row['market_cap']) else "N/A"
        company_name = row.get('company_name', row.get('shortName', 'Unknown'))
        
        report += f"""
第{int(row['weight_rank'])}名: {row['ticker']} - {company_name}
   行業: {row.get('sector', 'Unknown')}
   市值: {market_cap} | 本益比: {pe} | 市淨率: {pb}
   股息率: {div_yield}
"""
    
    # 添加技術分析信號
    if 'signals' in index_recommendation:
        report += f"""

=== 技術分析信號 ===
"""
        for signal in index_recommendation['signals']:
            report += f"• {signal}\n"
    
    report += f"""

=== 測試結果 ===
✓ 成功獲取那斯達克權重前十股票資料
✓ 成功分析那斯達克指數技術指標
✓ 成功生成投資建議

測試完成，系統運作正常！
"""
    
    with open(f"{output_dir}/basic_test_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    test_nasdaq_basic()