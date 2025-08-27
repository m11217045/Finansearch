"""
主程式 - S&P 500 價值投資股票篩選與分析系統
"""

import pandas as pd
import logging
import os
from datetime import datetime
import json

# 導入自訂模組
from src.utils import setup_logging, load_env_variables, create_output_directory, save_dataframe
from src.data_fetcher import SP500DataFetcher
from src.screener import ValueScreener
from src.enhanced_analyzer import EnhancedStockAnalyzer  # 使用增強版分析器
from config.settings import OUTPUT_SETTINGS


def main():
    """主執行函數"""
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("S&P 500 價值投資股票篩選與分析系統啟動")
    logger.info("=" * 60)
    
    try:
        # 載入環境變數
        env_vars = load_env_variables()
        max_stocks_to_analyze = env_vars.get('max_stocks', OUTPUT_SETTINGS['max_stocks_to_analyze'])
        
        # 建立輸出目錄
        output_dir = create_output_directory()
        logger.info(f"輸出目錄: {output_dir}")
        
        # 階段 1: 獲取 S&P 500 成分股數據
        logger.info("\n階段 1: 獲取 S&P 500 成分股數據")
        logger.info("-" * 40)
        
        fetcher = SP500DataFetcher()
        
        # 獲取股票代碼列表
        tickers = fetcher.get_sp500_tickers()
        fetcher.save_tickers_to_csv(f"{output_dir}/sp500_tickers.csv")
        
        # 批量獲取股票數據（限制數量以節省時間）
        logger.info(f"獲取前 {min(100, len(tickers))} 支股票的財務數據...")
        raw_data = fetcher.batch_fetch_stock_data(tickers, max_stocks=100)
        
        if raw_data.empty:
            logger.error("無法獲取股票數據，程式結束")
            return
        
        # 保存原始數據
        save_dataframe(raw_data, f"{output_dir}/raw_stock_data", ['csv', 'json'])
        logger.info(f"原始數據已保存，包含 {len(raw_data)} 支股票")
        
        # 階段 2: 價值投資排名分析
        logger.info("\n階段 2: 價值投資排名分析")
        logger.info("-" * 40)
        
        screener = ValueScreener()
        
        # 直接獲取被低估程度前10名的股票
        top_undervalued_stocks = screener.get_top_undervalued_stocks(raw_data, top_n=10)
        
        if top_undervalued_stocks.empty:
            logger.warning("沒有找到可排名的股票")
            return
        
        # 保存被低估股票排名結果
        save_dataframe(top_undervalued_stocks, f"{output_dir}/top_undervalued_stocks", ['csv', 'json'])
        logger.info(f"被低估股票排名已保存，前10名股票如下：")
        
        # 顯示前10名簡要信息
        for _, stock in top_undervalued_stocks.head(10).iterrows():
            logger.info(f"  第{int(stock['value_rank'])}名: {stock['ticker']} ({stock.get('company_name', 'N/A')}) - 評分: {stock['value_score']:.1f}")
        
        # 使用排名結果進行後續分析
        screened_data = top_undervalued_stocks
        
        # 建立篩選摘要
        screening_summary = screener.screening_results
        with open(f"{output_dir}/screening_summary.json", 'w', encoding='utf-8') as f:
            json.dump(screening_summary, f, ensure_ascii=False, indent=2)
        
        logger.info(f"價值投資排名完成，獲得前 {len(screened_data)} 支被低估股票")
        
        # 顯示前 5 名股票
        logger.info("\n前 5 名被低估股票:")
        for i, row in screened_data.head().iterrows():
            logger.info(f"{int(row['value_rank'])}. {row['ticker']} ({row.get('company_name', 'N/A')}) - 評分: {row['value_score']:.2f}")
        
        # 階段 3: 增強版 AI 綜合分析
        logger.info("\n階段 3: 增強版 AI 綜合分析")
        logger.info("-" * 40)
        
        try:
            analyzer = EnhancedStockAnalyzer()
            
            # 將 DataFrame 轉換為字典列表
            stock_list = screened_data.to_dict('records')
            
            # 執行綜合分析（包含新聞、情緒、技術面）
            logger.info("開始執行多維度綜合分析...")
            analysis_results = analyzer.batch_analyze_stocks(stock_list, max_analysis=min(5, len(screened_data)))
            
            # 保存分析結果
            analyzer.save_analysis_results(analysis_results, f"{output_dir}/enhanced_analysis")
            
            # 顯示分析摘要
            successful_count = analysis_results.get('successful_analyses', 0)
            total_count = analysis_results.get('total_stocks_requested', 0)
            logger.info(f"綜合分析完成: {successful_count}/{total_count} 支股票分析成功")
            
            # 顯示前3名股票的投資建議
            if analysis_results.get('analysis_results'):
                logger.info("\n📊 前3名股票投資建議:")
                count = 0
                for ticker, result in analysis_results['analysis_results'].items():
                    if 'error' not in result and count < 3:
                        logger.info(f"  {ticker}: {result.get('investment_recommendation', 'N/A')} "
                                  f"(綜合評分: {result.get('overall_score', 0):.1f})")
                        logger.info(f"    風險等級: {result.get('risk_assessment', {}).get('overall_risk', 'N/A')}")
                        logger.info(f"    新聞情緒: {result.get('news_sentiment_analysis', {}).get('sentiment', 'N/A')}")
                        count += 1
            
            # 生成投資報告
            investment_reports = []
            if analysis_results.get('analysis_results'):
                for ticker, result in analysis_results['analysis_results'].items():
                    if 'error' not in result:
                        investment_reports.append({
                            'ticker': ticker,
                            'recommendation': result.get('investment_recommendation', ''),
                            'overall_score': result.get('overall_score', 0),
                            'risk_level': result.get('risk_assessment', {}).get('overall_risk', ''),
                            'sentiment': result.get('news_sentiment_analysis', {}).get('sentiment', '')
                        })
            
            # 保存投資報告
            if investment_reports:
                reports_df = pd.DataFrame(investment_reports)
                save_dataframe(reports_df, f"{output_dir}/investment_reports", ['csv'])
            
            logger.info(f"增強版分析完成，生成 {len(investment_reports)} 份綜合投資報告")
            
        except Exception as e:
            logger.error(f"增強版分析過程發生錯誤: {e}")
            logger.info("將跳過 AI 分析，僅提供篩選結果")
        
        # 階段 4: 生成最終報告
        logger.info("\n階段 4: 生成最終報告")
        logger.info("-" * 40)
        
        # 建立簡要報告
        create_summary_report(screened_data, output_dir)
        
        # 生成行業分析
        if 'sector' in screened_data.columns:
            sector_analysis = screener.generate_sector_analysis(screened_data)
            if sector_analysis is not None and not sector_analysis.empty:
                save_dataframe(sector_analysis, f"{output_dir}/sector_analysis", ['csv'])
        
        logger.info(f"\n程式執行完成！")
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


def create_summary_report(top_stocks: pd.DataFrame, output_dir: str) -> None:
    """建立簡要摘要報告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
S&P 500 價值投資股票篩選結果摘要
生成時間: {timestamp}

篩選標準:
- 本益比 (P/E) ≤ 20
- 市淨率 (P/B) ≤ 2
- 股息殖利率 ≥ 3%
- 債務權益比 ≤ 1.5
- 自由現金流 > 0

前 {min(10, len(top_stocks))} 名推薦股票:
"""
    
    for i, row in top_stocks.head(10).iterrows():
        pe = f"{row['trailing_pe']:.2f}" if pd.notna(row['trailing_pe']) else "N/A"
        pb = f"{row['price_to_book']:.2f}" if pd.notna(row['price_to_book']) else "N/A"
        div_yield = f"{row['dividend_yield']*100:.2f}%" if pd.notna(row['dividend_yield']) else "N/A"
        score = f"{row['total_value_score']:.2f}" if pd.notna(row['total_value_score']) else "N/A"
        
        report += f"""
{row['rank']}. {row['ticker']} - {row.get('company_name', 'Unknown')}
   行業: {row.get('sector', 'Unknown')}
   本益比: {pe} | 市淨率: {pb} | 股息率: {div_yield}
   價值評分: {score} | 評等: {row.get('value_rating', 'N/A')}
"""
    
    report += f"""

免責聲明:
本報告僅供教育和參考用途，不構成投資建議。
投資前請諮詢專業財務顧問並進行充分的盡職調查。
股票投資涉及風險，過去表現不代表未來結果。
"""
    
    with open(f"{output_dir}/summary_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    main()
