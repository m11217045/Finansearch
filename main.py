"""
主程式 - 那斯達克權重前十股票分析與指數投資建議系統
"""

import pandas as pd
import logging
import os
from datetime import datetime
import json
import yfinance as yf

# 導入自訂模組
from src.utils import setup_logging, load_env_variables, create_output_directory, save_dataframe, DateTimeEncoder
from src.data_fetcher import NasdaqDataFetcher
from src.screener import ValueScreener
from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate  # 使用增強版分析器
from config.settings import OUTPUT_SETTINGS, MULTI_AGENT_SETTINGS


def analyze_nasdaq_index_recommendation() -> dict:
    """分析那斯達克指數的投資建議"""
    try:
        # 獲取那斯達克100指數數據 (QQQ ETF作為代理)
        qqq = yf.Ticker("QQQ")
        
        # 獲取歷史價格數據 (1年)
        hist_data = qqq.history(period="1y")
        current_price = hist_data['Close'].iloc[-1]
        
        # 獲取技術指標
        sma_50 = hist_data['Close'].rolling(50).mean().iloc[-1]
        sma_200 = hist_data['Close'].rolling(200).mean().iloc[-1]
        
        # 計算價格變化
        price_change_1m = ((current_price - hist_data['Close'].iloc[-22]) / hist_data['Close'].iloc[-22]) * 100
        price_change_3m = ((current_price - hist_data['Close'].iloc[-66]) / hist_data['Close'].iloc[-66]) * 100
        price_change_1y = ((current_price - hist_data['Close'].iloc[0]) / hist_data['Close'].iloc[0]) * 100
        
        # 獲取基本資訊
        info = qqq.info
        
        # 分析邏輯
        signals = []
        score = 0
        
        # 技術面分析
        if current_price > sma_50:
            signals.append("價格高於50日移動平均線（正面）")
            score += 1
        else:
            signals.append("價格低於50日移動平均線（負面）")
            score -= 1
            
        if current_price > sma_200:
            signals.append("價格高於200日移動平均線（正面）")
            score += 1
        else:
            signals.append("價格低於200日移動平均線（負面）")
            score -= 1
        
        if sma_50 > sma_200:
            signals.append("50日均線高於200日均線（正面）")
            score += 1
        else:
            signals.append("50日均線低於200日均線（負面）")
            score -= 1
        
        # 趨勢分析
        if price_change_1m > 0:
            signals.append(f"近1個月上漲 {price_change_1m:.1f}%（正面）")
            score += 1
        else:
            signals.append(f"近1個月下跌 {abs(price_change_1m):.1f}%（負面）")
            score -= 1
        
        # 決定建議
        if score >= 2:
            recommendation = "買入"
            reasoning = "技術指標顯示多數正面信號，建議買入那斯達克指數"
        elif score <= -2:
            recommendation = "賣出"
            reasoning = "技術指標顯示多數負面信號，建議賣出或等待更好時機"
        else:
            recommendation = "持有"
            reasoning = "技術指標混合，建議持有並觀察後續發展"
        
        return {
            'recommendation': recommendation,
            'reasoning': reasoning,
            'score': score,
            'current_price': float(current_price),
            'sma_50': float(sma_50),
            'sma_200': float(sma_200),
            'price_changes': {
                '1_month': float(price_change_1m),
                '3_month': float(price_change_3m),
                '1_year': float(price_change_1y)
            },
            'signals': signals,
            'analysis_date': datetime.now().isoformat()
        }
        
    except Exception as e:
        logging.error(f"分析那斯達克指數時發生錯誤: {e}")
        return {
            'recommendation': '無法分析',
            'reasoning': f'數據獲取失敗: {str(e)}',
            'error': True
        }


def main():
    """主執行函數"""
    # 設置日誌
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("=" * 60)
    logger.info("那斯達克權重前十股票分析與指數投資建議系統啟動")
    logger.info("=" * 60)
    
    try:
        # 載入環境變數
        env_vars = load_env_variables()
        max_stocks_to_analyze = env_vars.get('max_stocks', OUTPUT_SETTINGS['max_stocks_to_analyze'])
        
        # 建立輸出目錄
        output_dir = create_output_directory()
        logger.info(f"輸出目錄: {output_dir}")
        
        # 階段 1: 獲取那斯達克權重前十股票數據
        logger.info("\n階段 1: 獲取那斯達克權重前十股票數據")
        logger.info("-" * 40)
        
        fetcher = NasdaqDataFetcher()
        
        # 獲取股票代碼列表
        tickers = fetcher.get_nasdaq_top10_tickers()
        fetcher.save_tickers_to_csv(f"{output_dir}/nasdaq_top10_tickers.csv")
        
        # 批量獲取股票數據（全部10支股票）
        logger.info(f"獲取那斯達克權重前10支股票的財務數據...")
        raw_data = fetcher.batch_fetch_stock_data(tickers, max_stocks=10)
        
        if raw_data.empty:
            logger.error("無法獲取股票數據，程式結束")
            return
        
        # 保存原始數據
        save_dataframe(raw_data, f"{output_dir}/raw_stock_data", ['csv', 'json'])
        logger.info(f"原始數據已保存，包含 {len(raw_data)} 支股票")
        
        # 階段 2: 那斯達克前十股票基本分析
        logger.info("\n階段 2: 那斯達克前十股票基本分析")
        logger.info("-" * 40)
        
        screener = ValueScreener()
        
        # 直接分析這10支股票，不進行價值篩選
        if raw_data.empty:
            logger.warning("沒有獲取到股票數據")
            return
        
        # 為每支股票加上排名資訊（基於權重）
        raw_data['weight_rank'] = range(1, len(raw_data) + 1)
        raw_data['analysis_type'] = '那斯達克權重前十'
        
        # 保存基本數據分析結果
        save_dataframe(raw_data, f"{output_dir}/nasdaq_top10_analysis", ['csv', 'json'])
        logger.info(f"那斯達克前十股票基本分析已保存，包含以下股票：")
        
        # 顯示股票簡要信息
        for _, stock in raw_data.iterrows():
            company_name = stock.get('company_name', stock.get('shortName', 'N/A'))
            logger.info(f"  第{int(stock['weight_rank'])}名: {stock['ticker']} ({company_name})")
        
        # 使用原始數據進行後續分析
        screened_data = raw_data
        
        # 建立分析摘要
        analysis_summary = {
            'analysis_type': '那斯達克權重前十股票分析',
            'total_stocks': len(screened_data),
            'analysis_date': datetime.now().isoformat(),
            'stocks_included': screened_data['ticker'].tolist()
        }
        with open(f"{output_dir}/analysis_summary.json", 'w', encoding='utf-8') as f:
            json.dump(analysis_summary, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        logger.info(f"那斯達克權重前十股票分析完成，包含 {len(screened_data)} 支股票")
        
        # 階段 2.5: 那斯達克指數投資建議分析
        logger.info("\n階段 2.5: 那斯達克指數投資建議分析")
        logger.info("-" * 40)
        
        nasdaq_recommendation = analyze_nasdaq_index_recommendation()
        
        # 保存指數建議
        with open(f"{output_dir}/nasdaq_index_recommendation.json", 'w', encoding='utf-8') as f:
            json.dump(nasdaq_recommendation, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        
        logger.info(f"那斯達克指數投資建議: {nasdaq_recommendation['recommendation']}")
        logger.info(f"建議理由: {nasdaq_recommendation['reasoning']}")
        
        # 顯示前 5 支股票
        logger.info("\n那斯達克權重前 5 支股票:")
        for i, row in screened_data.head().iterrows():
            company_name = row.get('company_name', row.get('shortName', 'N/A'))
            logger.info(f"{int(row['weight_rank'])}. {row['ticker']} ({company_name})")
        
        # 階段 3: 增強版 AI 綜合分析（可選）
        logger.info("\n階段 3: 增強版 AI 綜合分析")
        logger.info("-" * 40)
        
        # 檢查是否啟用 AI 分析
        env_vars = load_env_variables()
        enable_ai_analysis = env_vars.get('enable_ai_analysis', 'true').lower() == 'true'
        
        if not enable_ai_analysis:
            logger.info("AI 分析已停用，跳過此階段")
        else:
            try:
                # 啟用多代理人辯論（在命令列版本中預設關閉，可通過設定檔調整）
                enable_debate = MULTI_AGENT_SETTINGS.get('enable_debate', False)
                analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=enable_debate)
                
                # 將 DataFrame 轉換為字典列表
                stock_list = screened_data.to_dict('records')
                
                # 執行綜合分析（包含新聞、情緒、技術面，以及多代理人辯論）
                if enable_debate:
                    logger.info("開始執行多代理人辯論分析...")
                else:
                    logger.info("開始執行多維度綜合分析...")
                
                analysis_results = analyzer.batch_analyze_stocks(
                    stock_list, 
                    max_analysis=min(5, len(screened_data)),
                    include_debate=enable_debate
                )
                
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
        create_summary_report(screened_data, nasdaq_recommendation, output_dir)
        
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


def create_summary_report(nasdaq_stocks: pd.DataFrame, index_recommendation: dict, output_dir: str) -> None:
    """建立簡要摘要報告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
那斯達克權重前十股票分析與指數投資建議報告
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
   股息率: {div_yield} | 分析類型: {row.get('analysis_type', 'N/A')}
"""
    
    # 添加技術分析信號
    if 'signals' in index_recommendation:
        report += f"""

=== 技術分析信號 ===
"""
        for signal in index_recommendation['signals']:
            report += f"• {signal}\n"
    
    report += f"""

=== 投資策略建議 ===
基於那斯達克權重前十股票的分析，這些公司代表了美國科技股的核心力量。
建議投資者可以通過那斯達克100指數ETF (如QQQ) 來投資這個組合。

風險提醒:
- 科技股波動性較大，適合風險承受能力較強的投資者
- 建議分批投資，降低市場時機風險
- 定期檢視並調整投資組合

免責聲明:
本報告僅供教育和參考用途，不構成投資建議。
投資前請諮詢專業財務顧問並進行充分的盡職調查。
股票投資涉及風險，過去表現不代表未來結果。
"""
    
    with open(f"{output_dir}/summary_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)


if __name__ == "__main__":
    main()
