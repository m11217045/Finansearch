"""
測試 yfinance 完整功能，檢查未使用的指標
"""

import yfinance as yf
import pandas as pd
import json
from datetime import datetime

def test_yfinance_complete_features(ticker="AAPL"):
    """測試 yfinance 的所有功能"""
    print(f"=== 測試股票: {ticker} ===\n")
    
    stock = yf.Ticker(ticker)
    
    # 1. 基本信息 (info)
    print("=== 1. 基本信息 (stock.info) ===")
    info = stock.info
    
    # 打印所有可用的info鍵
    print("所有可用的info鍵:")
    for key in sorted(info.keys()):
        print(f"  '{key}': {info.get(key)}")
    print()
    
    # 2. 歷史數據
    print("=== 2. 歷史數據功能 ===")
    try:
        # 不同時間週期的歷史數據
        periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        print("可用的歷史數據週期:")
        for period in periods:
            try:
                hist = stock.history(period=period)
                print(f"  {period}: {len(hist)} 個數據點, 最早: {hist.index[0] if len(hist) > 0 else 'N/A'}")
            except Exception as e:
                print(f"  {period}: 錯誤 - {e}")
    except Exception as e:
        print(f"歷史數據錯誤: {e}")
    print()
    
    # 3. 財務報表
    print("=== 3. 財務報表 ===")
    try:
        # 損益表
        print("損益表 (Income Statement):")
        income_stmt = stock.financials
        if income_stmt is not None and not income_stmt.empty:
            print(f"  年度損益表: {income_stmt.shape}")
            print(f"  可用欄位: {list(income_stmt.index)[:10]}...")  # 只顯示前10個
        
        quarterly_income = stock.quarterly_financials
        if quarterly_income is not None and not quarterly_income.empty:
            print(f"  季度損益表: {quarterly_income.shape}")
        
        # 資產負債表
        print("\n資產負債表 (Balance Sheet):")
        balance_sheet = stock.balance_sheet
        if balance_sheet is not None and not balance_sheet.empty:
            print(f"  年度資產負債表: {balance_sheet.shape}")
            print(f"  可用欄位: {list(balance_sheet.index)[:10]}...")
        
        quarterly_balance = stock.quarterly_balance_sheet
        if quarterly_balance is not None and not quarterly_balance.empty:
            print(f"  季度資產負債表: {quarterly_balance.shape}")
        
        # 現金流量表
        print("\n現金流量表 (Cash Flow):")
        cashflow = stock.cashflow
        if cashflow is not None and not cashflow.empty:
            print(f"  年度現金流量表: {cashflow.shape}")
            print(f"  可用欄位: {list(cashflow.index)[:10]}...")
        
        quarterly_cashflow = stock.quarterly_cashflow
        if quarterly_cashflow is not None and not quarterly_cashflow.empty:
            print(f"  季度現金流量表: {quarterly_cashflow.shape}")
            
    except Exception as e:
        print(f"財務報表錯誤: {e}")
    print()
    
    # 4. 機構和內部人持股
    print("=== 4. 機構和內部人持股 ===")
    try:
        # 機構持股
        institutional_holders = stock.institutional_holders
        if institutional_holders is not None and not institutional_holders.empty:
            print(f"機構持股: {institutional_holders.shape}")
            print(f"欄位: {list(institutional_holders.columns)}")
        
        # 主要持股人
        major_holders = stock.major_holders
        if major_holders is not None and not major_holders.empty:
            print(f"主要持股人: {major_holders.shape}")
            print(f"欄位: {list(major_holders.columns)}")
        
        # 內部人持股
        insider_holdings = stock.insider_roster_holders
        if insider_holdings is not None and not insider_holdings.empty:
            print(f"內部人持股: {insider_holdings.shape}")
            print(f"欄位: {list(insider_holdings.columns)}")
        
        # 內部人交易
        insider_purchases = stock.insider_purchases
        if insider_purchases is not None and not insider_purchases.empty:
            print(f"內部人交易: {insider_purchases.shape}")
            print(f"欄位: {list(insider_purchases.columns)}")
            
    except Exception as e:
        print(f"持股數據錯誤: {e}")
    print()
    
    # 5. 分析師數據
    print("=== 5. 分析師數據 ===")
    try:
        # 分析師建議
        recommendations = stock.recommendations
        if recommendations is not None and not recommendations.empty:
            print(f"分析師建議: {recommendations.shape}")
            print(f"欄位: {list(recommendations.columns)}")
        
        # 分析師價格目標
        analyst_price_target = stock.analyst_price_target
        if analyst_price_target is not None:
            print(f"分析師價格目標: {analyst_price_target}")
        
        # 收益預測
        earnings_forecast = stock.earnings_forecasts
        if earnings_forecast is not None and not earnings_forecast.empty:
            print(f"收益預測: {earnings_forecast.shape}")
            print(f"欄位: {list(earnings_forecast.columns)}")
            
    except Exception as e:
        print(f"分析師數據錯誤: {e}")
    print()
    
    # 6. 收益和股息數據
    print("=== 6. 收益和股息數據 ===")
    try:
        # 收益數據
        earnings = stock.earnings
        if earnings is not None and not earnings.empty:
            print(f"年度收益: {earnings.shape}")
            print(f"欄位: {list(earnings.columns)}")
        
        quarterly_earnings = stock.quarterly_earnings
        if quarterly_earnings is not None and not quarterly_earnings.empty:
            print(f"季度收益: {quarterly_earnings.shape}")
            print(f"欄位: {list(quarterly_earnings.columns)}")
        
        # 股息數據
        dividends = stock.dividends
        if dividends is not None and not dividends.empty:
            print(f"股息歷史: {len(dividends)} 個數據點")
        
        # 股票分割
        splits = stock.splits
        if splits is not None and not splits.empty:
            print(f"股票分割歷史: {len(splits)} 個數據點")
            
    except Exception as e:
        print(f"收益股息數據錯誤: {e}")
    print()
    
    # 7. 選擇權數據
    print("=== 7. 選擇權數據 ===")
    try:
        # 獲取選擇權到期日
        options_dates = stock.options
        if options_dates:
            print(f"可用選擇權到期日: {len(options_dates)} 個")
            print(f"最近幾個到期日: {options_dates[:5]}")
            
            # 獲取第一個到期日的選擇權鏈
            if options_dates:
                option_chain = stock.option_chain(options_dates[0])
                if hasattr(option_chain, 'calls') and option_chain.calls is not None:
                    print(f"Call選擇權: {option_chain.calls.shape}")
                if hasattr(option_chain, 'puts') and option_chain.puts is not None:
                    print(f"Put選擇權: {option_chain.puts.shape}")
                    
    except Exception as e:
        print(f"選擇權數據錯誤: {e}")
    print()
    
    # 8. 新聞數據
    print("=== 8. 新聞數據 ===")
    try:
        news = stock.news
        if news:
            print(f"可用新聞: {len(news)} 條")
            if news:
                first_news = news[0]
                print(f"新聞欄位: {list(first_news.keys())}")
                
    except Exception as e:
        print(f"新聞數據錯誤: {e}")
    print()
    
    # 9. 其他數據
    print("=== 9. 其他可用數據 ===")
    try:
        # 日曆事件
        calendar = stock.calendar
        if calendar is not None and not calendar.empty:
            print(f"日曆事件: {calendar.shape}")
            print(f"欄位: {list(calendar.columns)}")
        
        # 可持續性數據
        sustainability = stock.sustainability
        if sustainability is not None and not sustainability.empty:
            print(f"ESG數據: {sustainability.shape}")
            print(f"欄位: {list(sustainability.index)}")
        
    except Exception as e:
        print(f"其他數據錯誤: {e}")
    print()

def compare_with_current_usage():
    """對比目前使用的指標與yfinance完整功能"""
    print("=== 目前使用的 yfinance 指標對比分析 ===\n")
    
    # 目前使用的指標（從程式碼中提取）
    current_usage = {
        'basic_info': [
            'longName', 'sector', 'industry', 'currentPrice', 'marketCap',
            'trailingPE', 'beta', 'heldPercentInstitutions', 'heldPercentInsiders',
            'shortRatio', 'sharesOutstanding', 'floatShares', 'averageVolume',
            'dividendYield', 'fiftyTwoWeekHigh', 'fiftyTwoWeekLow', 'fullTimeEmployees',
            'forwardPE', 'priceToBook', 'priceToSalesTrailing12Months', 'pegRatio',
            'debtToEquity', 'currentRatio', 'returnOnEquity', 'returnOnAssets',
            'profitMargins', 'revenueGrowth', 'earningsGrowth', 'dividendRate',
            'payoutRatio', 'recommendationKey', 'targetMeanPrice', 'enterpriseValue',
            'ebitda', 'freeCashflow'
        ],
        'data_methods': [
            'history()', 'news', 'institutional_holders', 'insider_purchases'
        ]
    }
    
    # yfinance完整功能
    complete_features = {
        'basic_info_unused': [
            # 估值指標
            'priceToSalesTrailing12Months', 'enterpriseToRevenue', 'enterpriseToEbitda',
            'forwardPE', 'pegRatio', 'priceToBook', 'bookValue', 'marketCap',
            
            # 財務比率 - 獲利能力
            'grossMargins', 'operatingMargins', 'profitMargins', 'returnOnEquity',
            'returnOnAssets', 'operatingCashflow', 'earningsQuarterlyGrowth',
            
            # 財務比率 - 財務健康
            'totalCash', 'totalCashPerShare', 'totalDebt', 'quickRatio',
            'currentRatio', 'debtToEquity', 'totalDebtToEquity',
            
            # 現金流
            'operatingCashflow', 'freeCashflow', 'totalCashFromOperatingActivities',
            
            # 股息相關
            'dividendRate', 'dividendYield', 'payoutRatio', 'fiveYearAvgDividendYield',
            'trailingAnnualDividendRate', 'trailingAnnualDividendYield',
            
            # 交易相關
            'volume', 'averageVolume', 'averageVolume10days', 'averageDailyVolume10Day',
            'regularMarketVolume', 'averageVolume10days',
            
            # 價格相關
            'dayHigh', 'dayLow', 'regularMarketDayHigh', 'regularMarketDayLow',
            'fiftyDayAverage', 'twoHundredDayAverage', 'fiftyTwoWeekChange',
            'SandP52WeekChange',
            
            # 分析師相關
            'recommendationMean', 'numberOfAnalystOpinions', 'targetHighPrice',
            'targetLowPrice', 'targetMeanPrice', 'targetMedianPrice',
            
            # 機構持股詳細
            'heldPercentInsiders', 'heldPercentInstitutions', 'sharesShort',
            'sharesShortPriorMonth', 'sharesShortPreviousMonthDate', 'dateShortInterest',
            'shortPercentOfFloat', 'shortRatio', 'sharesPercentSharesOut',
            
            # 股本結構
            'impliedSharesOutstanding', 'floatShares', 'sharesOutstanding',
            'sharesShort', 'sharesShortPriorMonth',
            
            # 其他
            'website', 'phone', 'address1', 'city', 'state', 'zip', 'country',
            'fullTimeEmployees', 'auditRisk', 'boardRisk', 'compensationRisk',
            'shareHolderRightsRisk', 'overallRisk', 'governanceEpochDate',
            'compensationAsOfEpochDate', 'maxAge'
        ],
        'unused_data_methods': [
            # 財務報表
            'financials', 'quarterly_financials',
            'balance_sheet', 'quarterly_balance_sheet', 
            'cashflow', 'quarterly_cashflow',
            
            # 持股詳細數據
            'major_holders', 'insider_roster_holders',
            'insider_purchases', 'insider_transactions',
            
            # 分析師數據
            'recommendations', 'analyst_price_target', 'earnings_forecasts',
            'revenue_forecasts',
            
            # 收益數據
            'earnings', 'quarterly_earnings', 'earnings_dates',
            
            # 股息和分割
            'dividends', 'splits', 'actions',
            
            # 選擇權
            'options', 'option_chain()',
            
            # ESG數據
            'sustainability',
            
            # 日曆事件
            'calendar',
            
            # 其他
            'isin', 'fast_info'
        ]
    }
    
    print("🔍 未使用的重要 info 欄位：")
    important_unused = [
        'grossMargins', 'operatingMargins', 'operatingCashflow', 'totalCash',
        'totalCashPerShare', 'totalDebt', 'quickRatio', 'earningsQuarterlyGrowth',
        'fiveYearAvgDividendYield', 'dayHigh', 'dayLow', 'fiftyDayAverage',
        'twoHundredDayAverage', 'recommendationMean', 'numberOfAnalystOpinions',
        'targetHighPrice', 'targetLowPrice', 'sharesShort', 'shortPercentOfFloat',
        'impliedSharesOutstanding', 'website', 'phone', 'address1', 'auditRisk',
        'boardRisk', 'compensationRisk', 'overallRisk'
    ]
    
    for field in important_unused:
        print(f"  • {field}")
    
    print(f"\n📊 未使用的重要數據方法：")
    important_methods = [
        'financials (年度損益表)', 'quarterly_financials (季度損益表)',
        'balance_sheet (年度資產負債表)', 'quarterly_balance_sheet (季度資產負債表)',
        'cashflow (年度現金流)', 'quarterly_cashflow (季度現金流)',
        'major_holders (主要股東)', 'recommendations (分析師建議)',
        'earnings (收益數據)', 'dividends (股息歷史)', 'splits (股票分割)',
        'options (選擇權數據)', 'sustainability (ESG數據)', 'calendar (財報日期)'
    ]
    
    for method in important_methods:
        print(f"  • {method}")
    
    print(f"\n💡 建議優先新增的功能：")
    recommendations = [
        "1. 財務報表數據 (quarterly_financials, balance_sheet, cashflow)",
        "2. 詳細獲利能力指標 (grossMargins, operatingMargins, operatingCashflow)",
        "3. 現金和債務分析 (totalCash, totalDebt, quickRatio)",
        "4. 分析師共識數據 (recommendations, targetHighPrice, targetLowPrice)",
        "5. 做空數據詳細分析 (sharesShort, shortPercentOfFloat)",
        "6. 移動平均線數據 (fiftyDayAverage, twoHundredDayAverage)",
        "7. ESG永續性評分 (sustainability)",
        "8. 選擇權數據分析 (options, option_chain)",
        "9. 股息歷史分析 (dividends)",
        "10. 財報發布日期 (calendar, earnings_dates)"
    ]
    
    for rec in recommendations:
        print(f"  {rec}")

if __name__ == "__main__":
    # 測試幾個不同的股票
    test_stocks = ["AAPL", "MSFT", "GOOGL"]
    
    for ticker in test_stocks[:1]:  # 只測試第一個以節省時間
        test_yfinance_complete_features(ticker)
        print("\n" + "="*80 + "\n")
    
    compare_with_current_usage()
