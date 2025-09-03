"""
Streamlit 網頁應用介面 - S&P 500 價值投資股票篩選系統
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import os
from datetime import datetime
import logging

# 導入自訂模組
from src.data_fetcher import SP500DataFetcher, MultiMarketDataFetcher, STOCK_PORTFOLIOS
from src.screener import ValueScreener
from src.enhanced_analyzer import EnhancedStockAnalyzer
from src.stock_individual_analyzer import StockIndividualAnalyzer
from src.utils import setup_logging, load_env_variables, format_currency, format_percentage, format_ratio
from config.settings import SCREENING_CRITERIA, OUTPUT_SETTINGS


# 設置頁面配置
st.set_page_config(
    page_title="多市場價值投資分析系統",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 設置樣式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin: 1rem 0;
    }
    .metric-box {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """主應用程式"""
    # 標題
    st.markdown('<h1 class="main-header">📈 多市場價值投資分析系統</h1>', unsafe_allow_html=True)
    
    # 側邊欄 - 系統控制
    setup_sidebar()
    
    # 主要內容區域
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🔍 股票篩選", "📊 數據分析", "🎯 個股分析", "🤖 AI 分析", "📋 結果報告"])
    
    with tab1:
        screening_interface()
    
    with tab2:
        data_analysis_interface()
    
    with tab3:
        individual_stock_analysis_interface()
    
    with tab4:
        ai_analysis_interface()
    
    with tab5:
        report_interface()


def setup_sidebar():
    """設置側邊欄"""
    st.sidebar.markdown("## 📊 投資組合選擇")
    
    # 投資組合選擇
    portfolio_options = {
        'sp500': f"🇺🇸 {STOCK_PORTFOLIOS['sp500']['name']} - {STOCK_PORTFOLIOS['sp500']['description']}",
        'faang_plus': f"💻 {STOCK_PORTFOLIOS['faang_plus']['name']} - {STOCK_PORTFOLIOS['faang_plus']['description']}",
        'taiwan_top50': f"🇹🇼 {STOCK_PORTFOLIOS['taiwan_top50']['name']} - {STOCK_PORTFOLIOS['taiwan_top50']['description']}"
    }
    
    selected_portfolio = st.sidebar.selectbox(
        "選擇投資組合",
        options=list(portfolio_options.keys()),
        format_func=lambda x: portfolio_options[x],
        index=0,
        help="選擇要分析的股票組合"
    )
    
    # 將選擇的投資組合存儲到 session state
    st.session_state['selected_portfolio'] = selected_portfolio
    
    # 顯示投資組合詳細信息
    portfolio_config = STOCK_PORTFOLIOS[selected_portfolio]
    st.sidebar.markdown(f"**📋 當前組合：** {portfolio_config['name']}")
    
    if portfolio_config['source'] == 'predefined':
        ticker_count = len(portfolio_config['tickers'])
        st.sidebar.markdown(f"**📊 股票數量：** {ticker_count} 支")
        
        # 顯示部分股票代碼作為預覽
        if selected_portfolio == 'faang_plus':
            st.sidebar.markdown("**💻 包含股票：**")
            for ticker in portfolio_config['tickers']:
                st.sidebar.markdown(f"• {ticker}")
        elif selected_portfolio == 'taiwan_top50':
            st.sidebar.markdown("**🏢 包含台灣前50大公司**")
    else:
        st.sidebar.markdown("**📊 股票數量：** ~500 支")
    
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("## ⚙️ 系統設置")
    
    # API 設置檢查
    env_vars = load_env_variables()
    gemini_key = env_vars.get('gemini_api_key')
    
    if not gemini_key or gemini_key == 'your_gemini_api_key_here':
        st.sidebar.error("⚠️ 請設置 Gemini API Key")
        st.sidebar.info("請在 .env 檔案中設置 GEMINI_API_KEY")
    else:
        st.sidebar.success("✅ Gemini API 已設置")
    
    # 篩選參數設置
    st.sidebar.markdown("## 📋 篩選標準")
    
    # 允許用戶自訂篩選標準
    custom_criteria = {}
    
    custom_criteria['pe_ratio_max'] = st.sidebar.slider(
        "本益比上限", 
        min_value=5.0, 
        max_value=50.0, 
        value=float(SCREENING_CRITERIA['pe_ratio_max']),
        step=1.0,
        help="較低的本益比通常表示股票可能被低估"
    )
    
    custom_criteria['pb_ratio_max'] = st.sidebar.slider(
        "市淨率上限", 
        min_value=0.5, 
        max_value=5.0, 
        value=float(SCREENING_CRITERIA['pb_ratio_max']),
        step=0.1,
        help="市淨率低於1表示股價低於帳面價值"
    )
    
    # 移除股息相關設定，專注成長性指標
    st.sidebar.markdown("---")
    st.sidebar.markdown("**💡 評分重點 (複委託適用)**")
    st.sidebar.markdown("• 專注資本利得而非股息")
    st.sidebar.markdown("• 重視估值與財務健康度")
    st.sidebar.markdown("• 適合成長型投資策略")
    
    custom_criteria['debt_to_equity_max'] = st.sidebar.slider(
        "債務權益比上限", 
        min_value=0.1, 
        max_value=3.0, 
        value=float(SCREENING_CRITERIA['debt_to_equity_max']),
        step=0.1,
        help="較低的債務水平表示財務風險較小"
    )
    
    # 其他設置
    st.sidebar.markdown("## 🔧 其他設置")
    
    max_stocks = st.sidebar.number_input(
        "最多分析股票數量",
        min_value=5,
        max_value=600,  # 提高限制以支援完整SP500分析
        value=min(OUTPUT_SETTINGS['max_stocks_to_analyze'], 500),  # 預設500或配置值中較小者
        help="分析的股票數量。SP500約有500支成分股"
    )
    
    # 將自訂標準存儲到 session state
    st.session_state['custom_criteria'] = custom_criteria
    st.session_state['max_stocks'] = max_stocks


def screening_interface():
    """股票篩選介面"""
    st.markdown('<h2 class="sub-header">🔍 股票篩選</h2>', unsafe_allow_html=True)
    
    # 顯示當前選擇的投資組合
    if 'selected_portfolio' in st.session_state:
        portfolio_config = STOCK_PORTFOLIOS[st.session_state['selected_portfolio']]
        st.info(f"📊 當前投資組合：{portfolio_config['name']} - {portfolio_config['description']}")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 分析流程")
        
        # 獲取當前選擇的投資組合名稱
        portfolio_name = "股票數據"
        if 'selected_portfolio' in st.session_state:
            portfolio_config = STOCK_PORTFOLIOS[st.session_state['selected_portfolio']]
            portfolio_name = portfolio_config['name']
        
        # 顯示當前數據狀態
        if 'current_portfolio' in st.session_state and 'raw_data' in st.session_state:
            current_portfolio_config = STOCK_PORTFOLIOS[st.session_state['current_portfolio']]
            st.info(f"📊 目前已載入: {current_portfolio_config['name']} ({len(st.session_state['raw_data'])} 支股票)")
        
        # 步驟 1: 獲取數據
        col1_1, col1_2 = st.columns([3, 1])
        with col1_1:
            if st.button(f"1️⃣ 獲取 {portfolio_name} 數據", use_container_width=True):
                with st.spinner(f"正在獲取 {portfolio_name} 成分股數據..."):
                    fetch_portfolio_data()
        
        with col1_2:
            if st.button("🔄", help="重新獲取數據", use_container_width=True):
                # 清除現有數據以強制重新獲取
                for key in ['raw_data', 'current_portfolio', 'top_stocks', 'ai_analysis_result']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # 步驟 2: 價值投資排名
        if st.button("2️⃣ 價值投資排名分析", use_container_width=True):
            if 'raw_data' not in st.session_state:
                st.error(f"請先獲取 {portfolio_name} 數據")
            else:
                with st.spinner("正在進行價值投資排名分析..."):
                    apply_screening()
        
        # 步驟 3: 查看評分詳情
        if st.button("3️⃣ 查看評分分析", use_container_width=True):
            if 'top_stocks' not in st.session_state:
                st.error("請先執行價值投資排名")
            else:
                with st.spinner("正在生成評分分析..."):
                    calculate_scores()
    
    with col2:
        st.markdown("### 排名評分標準")
        st.markdown("""
        **多因子價值評分系統 (適合複委託投資者):**
        - 📊 本益比 (P/E) - 30%權重 - 越低越好
        - 📈 市淨率 (P/B) - 25%權重 - 越低越好
        - 🏛️ 債務權益比 - 20%權重 - 越低越好
        - 💪 股東權益報酬率 - 15%權重 - 越高越好
        - 📋 利潤率 - 10%權重 - 越高越好
        
        **專注成長性**: 不考慮股息配發，適合追求股價成長的投資策略
        **結果**: 被低估程度前10名股票
        """)
    
    # 顯示篩選結果
    if 'top_stocks' in st.session_state:
        st.markdown("### 🏆 價值投資排名結果 - 前 10 名")
        display_screening_results()


def data_analysis_interface():
    """數據分析介面"""
    st.markdown('<h2 class="sub-header">📊 數據分析</h2>', unsafe_allow_html=True)
    
    if 'top_stocks' not in st.session_state:
        st.info("請先在「股票篩選」頁面完成篩選流程")
        return
    
    # 顯示當前分析的投資組合
    if 'current_portfolio' in st.session_state:
        portfolio_config = STOCK_PORTFOLIOS[st.session_state['current_portfolio']]
        st.info(f"📊 分析對象：{portfolio_config['name']} - {portfolio_config['description']}")
    
    df = st.session_state['top_stocks']
    
    # 總覽統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("篩選出股票數", len(df))
    
    with col2:
        avg_pe = df['pe_ratio'].mean() if 'pe_ratio' in df.columns else df['trailing_pe'].mean() if 'trailing_pe' in df.columns else None
        st.metric("平均本益比", f"{avg_pe:.2f}" if pd.notna(avg_pe) else "N/A")
    
    with col3:
        avg_pb = df['pb_ratio'].mean() if 'pb_ratio' in df.columns else df['price_to_book'].mean() if 'price_to_book' in df.columns else None
        st.metric("平均市淨率", f"{avg_pb:.2f}" if pd.notna(avg_pb) else "N/A")
    
    with col4:
        avg_score = df['value_score'].mean() if 'value_score' in df.columns else None
        st.metric("平均評分", f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A")
    
    # 根據投資組合類型顯示特定統計
    if 'current_portfolio' in st.session_state:
        portfolio_type = st.session_state['current_portfolio']
        
        if portfolio_type == 'faang_plus':
            st.markdown("### 💻 科技巨頭分析")
            st.markdown("專注於美國科技龍頭公司的價值分析，這些公司通常具有強大的護城河和成長潛力。")
        elif portfolio_type == 'taiwan_top50':
            st.markdown("### 🇹🇼 台股前50分析")
            st.markdown("專注於台灣證券交易所市值前50大公司，包含半導體、金融、傳統產業等多元領域。")
        else:  # sp500
            st.markdown("### 🇺🇸 S&P 500分析")
            st.markdown("美國最具代表性的500家大型企業，涵蓋各行各業的領導公司。")
    
    # 視覺化圖表
    create_visualization_charts(df)
    
    # 詳細數據表格
    st.markdown("### 📋 詳細數據")
    display_detailed_table(df)


def ai_analysis_interface():
    """AI 分析介面"""
    st.markdown('<h2 class="sub-header">🤖 AI 分析</h2>', unsafe_allow_html=True)
    
    if 'top_stocks' not in st.session_state:
        st.info("請先在「股票篩選」頁面完成篩選流程")
        return
    
    # 檢查 API 設置
    env_vars = load_env_variables()
    if not env_vars.get('gemini_api_key') or env_vars.get('gemini_api_key') == 'your_gemini_api_key_here':
        st.error("請先設置 Gemini API Key 才能使用 AI 分析功能")
        return
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        if st.button("🚀 開始 Gemini AI 分析", use_container_width=True):
            run_ai_analysis()
    
    with col2:
        max_analysis = st.number_input(
            "分析股票數量",
            min_value=1,
            max_value=10,
            value=min(5, len(st.session_state['top_stocks'])),
            help="選擇要進行 AI 分析的股票數量"
        )
        st.session_state['max_analysis'] = max_analysis
    
    # 顯示分析結果
    if 'ai_analysis_results' in st.session_state:
        display_ai_analysis_results()


def report_interface():
    """報告介面"""
    st.markdown('<h2 class="sub-header">📋 結果報告</h2>', unsafe_allow_html=True)
    
    if 'top_stocks' not in st.session_state:
        st.info("請先完成股票篩選")
        return
    
    # 生成報告按鈕
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📄 生成投資報告", use_container_width=True):
            generate_investment_report()
    
    with col2:
        if st.button("💾 下載結果數據", use_container_width=True):
            create_download_files()
    
    # 顯示報告內容
    if 'investment_report' in st.session_state:
        st.markdown("### 📋 投資分析報告")
        st.markdown(st.session_state['investment_report'])
    
    # 顯示下載連結
    if 'download_data' in st.session_state:
        st.markdown("### 💾 下載文件")
        for filename, data in st.session_state['download_data'].items():
            st.download_button(
                label=f"下載 {filename}",
                data=data,
                file_name=filename,
                mime="text/csv" if filename.endswith('.csv') else "application/json"
            )


def fetch_portfolio_data():
    """獲取選定投資組合的數據"""
    try:
        # 獲取選定的投資組合類型
        selected_portfolio = st.session_state.get('selected_portfolio', 'sp500')
        
        # 檢查是否已經獲取過相同投資組合的數據
        if ('raw_data' in st.session_state and 
            'current_portfolio' in st.session_state and 
            st.session_state['current_portfolio'] == selected_portfolio):
            st.info(f"已有 {STOCK_PORTFOLIOS[selected_portfolio]['name']} 的數據，如需重新獲取請重新選擇投資組合")
            return
        
        # 創建多市場數據獲取器
        fetcher = MultiMarketDataFetcher(selected_portfolio)
        portfolio_config = STOCK_PORTFOLIOS[selected_portfolio]
        
        # 獲取股票列表
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text(f"正在獲取 {portfolio_config['name']} 成分股列表...")
        progress_bar.progress(20)
        
        tickers = fetcher.get_tickers()
        
        status_text.text(f"正在獲取 {portfolio_config['name']} 股票財務數據...")
        progress_bar.progress(40)
        
        # 根據投資組合類型設置最大股票數量
        max_stocks_limit = st.session_state.get('max_stocks', 50)  # 提高預設值
        
        # 對於科技7巨頭，獲取所有股票
        if selected_portfolio == 'faang_plus':
            max_stocks_limit = None  # 獲取所有7支股票
        elif selected_portfolio == 'taiwan_top50':
            max_stocks_limit = min(max_stocks_limit, 50)  # 限制台股數量  
        else:  # sp500
            max_stocks_limit = max_stocks_limit  # 移除SP500的額外限制，使用用戶設定的數量
        
        raw_data = fetcher.fetch_financial_data(max_stocks_limit)
        
        progress_bar.progress(100)
        status_text.text("數據獲取完成！")
        
        # 清除舊的分析結果
        if 'top_stocks' in st.session_state:
            del st.session_state['top_stocks']
        if 'ai_analysis_result' in st.session_state:
            del st.session_state['ai_analysis_result']
        
        st.session_state['raw_data'] = raw_data
        st.session_state['tickers'] = tickers
        st.session_state['current_portfolio'] = selected_portfolio
        
        st.success(f"成功獲取 {portfolio_config['name']} 中 {len(raw_data)} 支股票的數據")
        
        # 顯示獲取到的股票預覽
        if len(raw_data) > 0:
            st.info(f"包含股票: {', '.join(raw_data['symbol'].head(10).tolist())}" + 
                   (f" ... 等 {len(raw_data)} 支股票" if len(raw_data) > 10 else ""))
        
    except Exception as e:
        st.error(f"數據獲取失敗: {e}")
        logging.error(f"投資組合數據獲取錯誤: {e}")


def fetch_sp500_data():
    """獲取 S&P 500 數據 - 向後兼容函數"""
    # 設置為 SP500 並調用通用函數
    st.session_state['selected_portfolio'] = 'sp500'
    fetch_portfolio_data()


def apply_screening():
    """應用價值投資排名分析"""
    try:
        raw_data = st.session_state['raw_data']
        max_stocks = st.session_state.get('max_stocks', 50)  # 提高預設值
        
        screener = ValueScreener()
        
        # 直接獲取被低估程度前N名的股票
        top_undervalued_stocks = screener.get_top_undervalued_stocks(raw_data, top_n=max_stocks)
        
        st.session_state['top_stocks'] = top_undervalued_stocks
        st.session_state['screener'] = screener
        
        if len(top_undervalued_stocks) > 0:
            st.success(f"價值投資排名完成！從 {len(raw_data)} 支股票中選出前 {len(top_undervalued_stocks)} 名被低估股票")
            
            # 顯示排名摘要
            avg_score = top_undervalued_stocks['value_score'].mean()
            st.info(f"平均價值評分: {avg_score:.1f}")
            
        else:
            st.warning("沒有找到可排名的股票，請檢查數據質量")
            
    except Exception as e:
        st.error(f"價值投資排名過程發生錯誤: {e}")


def calculate_scores():
    """顯示已計算的價值評分"""
    try:
        if 'top_stocks' in st.session_state and not st.session_state['top_stocks'].empty:
            top_stocks = st.session_state['top_stocks']
            st.success(f"價值評分已計算完成！共有 {len(top_stocks)} 支被低估股票")
            
            # 顯示評分分佈
            if 'value_score' in top_stocks.columns:
                st.subheader("📊 價值評分分佈")
                import plotly.express as px
                fig = px.histogram(top_stocks, x='value_score', nbins=10, 
                                 title="價值評分分佈圖")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("請先進行股票篩選")
        
    except Exception as e:
        st.error(f"評分顯示發生錯誤: {e}")


def display_screening_results():
    """顯示篩選結果"""
    if 'top_stocks' not in st.session_state or st.session_state['top_stocks'].empty:
        st.warning("請先進行股票篩選")
        return
        
    df = st.session_state['top_stocks'].head(10)
    
    st.markdown("### 🏆 被低估股票排名前10名")
    
    # 準備顯示用的資料 - 使用新的欄位名稱
    available_columns = df.columns.tolist()
    display_columns = []
    
    # 基本資訊欄位
    if 'value_rank' in available_columns:
        display_columns.append('value_rank')
    if 'ticker' in available_columns:
        display_columns.append('ticker')
    if 'company_name' in available_columns:
        display_columns.append('company_name')
    if 'sector' in available_columns:
        display_columns.append('sector')
    
    # 財務指標欄位
    if 'trailing_pe' in available_columns:
        display_columns.append('trailing_pe')
    if 'price_to_book' in available_columns:
        display_columns.append('price_to_book')
    if 'debt_to_equity' in available_columns:
        display_columns.append('debt_to_equity')
    if 'value_score' in available_columns:
        display_columns.append('value_score')
    
    display_df = df[display_columns].copy()
    
    # 格式化數值
    if 'trailing_pe' in display_df.columns:
        display_df['trailing_pe'] = display_df['trailing_pe'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    if 'price_to_book' in display_df.columns:
        display_df['price_to_book'] = display_df['price_to_book'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    if 'debt_to_equity' in display_df.columns:
        display_df['debt_to_equity'] = display_df['debt_to_equity'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    if 'value_score' in display_df.columns:
        display_df['value_score'] = display_df['value_score'].apply(lambda x: f"{x:.1f}" if pd.notna(x) else "N/A")
    
    # 添加評等
    if 'value_score' in df.columns:
        def get_rating(score):
            if pd.isna(score): return "N/A"
            if score >= 80: return "⭐⭐⭐⭐⭐"
            elif score >= 70: return "⭐⭐⭐⭐"
            elif score >= 60: return "⭐⭐⭐"
            elif score >= 50: return "⭐⭐"
            else: return "⭐"
        
        display_df['評等'] = df['value_score'].apply(get_rating)
    
    # 重新命名欄位
    column_mapping = {
        'value_rank': '排名',
        'ticker': '代碼', 
        'company_name': '公司名稱',
        'sector': '行業',
        'trailing_pe': '本益比',
        'price_to_book': '市淨率',
        'debt_to_equity': '債務權益比',
        'value_score': '評分'
    }
    
    # 只重命名存在的欄位
    new_column_names = []
    for col in display_df.columns:
        if col in column_mapping:
            new_column_names.append(column_mapping[col])
        else:
            new_column_names.append(col)
    
    display_df.columns = new_column_names
    
    st.dataframe(display_df, use_container_width=True)


def create_visualization_charts(df):
    """建立視覺化圖表"""
    st.markdown("### 📈 視覺化分析")
    
    # 檢查可用的列名並映射到標準名稱
    column_mapping = {
        'pe_ratio': 'trailing_pe',
        'pb_ratio': 'price_to_book',
        'symbol': 'ticker',
        'name': 'company_name'
    }
    
    # 創建一個標準化的數據框
    df_viz = df.copy()
    for old_col, new_col in column_mapping.items():
        if old_col in df.columns and new_col not in df.columns:
            df_viz[new_col] = df[old_col]
    
    # 建立圖表
    tab1, tab2, tab3 = st.tabs(["估值指標分布", "行業分析", "評分分析"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # 本益比分布
            pe_col = 'trailing_pe' if 'trailing_pe' in df_viz.columns else 'pe_ratio'
            if pe_col in df_viz.columns and df_viz[pe_col].notna().any():
                # 過濾異常值 (PE > 100 的股票)
                pe_data = df_viz[df_viz[pe_col] <= 100][pe_col].dropna()
                if len(pe_data) > 0:
                    fig_pe = px.histogram(pe_data, title='本益比分布', 
                                        nbins=20, labels={pe_col: '本益比', 'count': '股票數量'})
                    st.plotly_chart(fig_pe, use_container_width=True)
                else:
                    st.info("無可用的本益比數據")
            else:
                st.info("本益比數據不可用")
        
        with col2:
            # 市淨率分布
            pb_col = 'price_to_book' if 'price_to_book' in df_viz.columns else 'pb_ratio'
            if pb_col in df_viz.columns and df_viz[pb_col].notna().any():
                # 過濾異常值 (PB > 10 的股票)
                pb_data = df_viz[df_viz[pb_col] <= 10][pb_col].dropna()
                if len(pb_data) > 0:
                    fig_pb = px.histogram(pb_data, title='市淨率分布',
                                        nbins=20, labels={pb_col: '市淨率', 'count': '股票數量'})
                    st.plotly_chart(fig_pb, use_container_width=True)
                else:
                    st.info("無可用的市淨率數據")
            else:
                st.info("市淨率數據不可用")
    
    with tab2:
        if 'sector' in df_viz.columns and df_viz['sector'].notna().any():
            # 行業分布
            sector_counts = df_viz['sector'].value_counts()
            if len(sector_counts) > 0:
                fig_sector = px.pie(values=sector_counts.values, names=sector_counts.index, 
                                  title='行業分布')
                st.plotly_chart(fig_sector, use_container_width=True)
                
                # 各行業平均評分
                if 'value_score' in df_viz.columns and df_viz['value_score'].notna().any():
                    sector_scores = df_viz.groupby('sector')['value_score'].mean().sort_values(ascending=False)
                    if len(sector_scores) > 0:
                        fig_sector_score = px.bar(x=sector_scores.index, y=sector_scores.values,
                                                title='各行業平均評分',
                                                labels={'x': '行業', 'y': '平均評分'})
                        st.plotly_chart(fig_sector_score, use_container_width=True)
            else:
                st.info("無行業分類數據")
        else:
            st.info("行業數據不可用")
    
    with tab3:
        # 評分散布圖
        pe_col = 'trailing_pe' if 'trailing_pe' in df_viz.columns else 'pe_ratio'
        pb_col = 'price_to_book' if 'price_to_book' in df_viz.columns else 'pb_ratio'
        
        if ('value_score' in df_viz.columns and 
            pe_col in df_viz.columns and 
            pb_col in df_viz.columns):
            
            # 準備散布圖數據 (過濾異常值)
            scatter_df = df_viz[
                (df_viz[pe_col] <= 100) & 
                (df_viz[pb_col] <= 10) & 
                df_viz[pe_col].notna() & 
                df_viz[pb_col].notna() & 
                df_viz['value_score'].notna()
            ].copy()
            
            if len(scatter_df) > 0:
                # 準備懸停數據
                hover_cols = []
                if 'ticker' in scatter_df.columns:
                    hover_cols.append('ticker')
                elif 'symbol' in scatter_df.columns:
                    hover_cols.append('symbol')
                
                if 'company_name' in scatter_df.columns:
                    hover_cols.append('company_name')
                elif 'name' in scatter_df.columns:
                    hover_cols.append('name')
                
                fig_scatter = px.scatter(scatter_df, x=pe_col, y=pb_col, 
                                       size='value_score', color='value_score',
                                       hover_data=hover_cols if hover_cols else None,
                                       title='估值指標與評分關係',
                                       labels={pe_col: '本益比', pb_col: '市淨率'})
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.info("無足夠的數據繪製散布圖")
        else:
            st.info("評分散布圖數據不足")


def display_detailed_table(df):
    """顯示詳細數據表格"""
    # 建立列名映射
    column_mapping = {
        'symbol': 'ticker',
        'name': 'company_name',
        'pe_ratio': 'trailing_pe',
        'pb_ratio': 'price_to_book',
        'roe': 'return_on_equity'
    }
    
    # 創建顯示用的數據框
    display_df = df.copy()
    
    # 應用列名映射
    for old_col, new_col in column_mapping.items():
        if old_col in display_df.columns and new_col not in display_df.columns:
            display_df[new_col] = display_df[old_col]
    
    # 選擇要顯示的欄位 (移除股息相關)
    columns_to_show = [
        'value_rank', 'ticker', 'company_name', 'sector', 'market_cap',
        'trailing_pe', 'price_to_book', 'debt_to_equity', 'return_on_equity',
        'profit_margins', 'value_score'
    ]
    
    # 備用列名
    alternative_columns = {
        'ticker': 'symbol',
        'company_name': 'name',
        'trailing_pe': 'pe_ratio',
        'price_to_book': 'pb_ratio',
        'return_on_equity': 'roe'
    }
    
    # 選擇可用的列
    available_columns = []
    for col in columns_to_show:
        if col in display_df.columns:
            available_columns.append(col)
        elif col in alternative_columns and alternative_columns[col] in display_df.columns:
            available_columns.append(alternative_columns[col])
    
    if not available_columns:
        st.warning("無可顯示的數據列")
        return
    
    # 選擇要顯示的數據
    final_df = display_df[available_columns].copy()
    
    # 格式化顯示
    for col in final_df.columns:
        if 'market_cap' in col:
            final_df[col] = final_df[col].apply(lambda x: format_currency(x) if pd.notna(x) else "N/A")
        elif any(name in col for name in ['return_on_equity', 'roe', 'profit_margin']):
            final_df[col] = final_df[col].apply(lambda x: format_percentage(x) if pd.notna(x) else "N/A")
        elif any(name in col for name in ['pe_ratio', 'trailing_pe', 'pb_ratio', 'price_to_book', 'debt_to_equity']):
            final_df[col] = final_df[col].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    # 重新命名列以便顯示
    column_display_names = {
        'value_rank': '排名',
        'ticker': '股票代號',
        'symbol': '股票代號',
        'company_name': '公司名稱',
        'name': '公司名稱',
        'sector': '行業',
        'market_cap': '市值',
        'trailing_pe': '本益比',
        'pe_ratio': '本益比',
        'price_to_book': '市淨率',
        'pb_ratio': '市淨率',
        'debt_to_equity': '負債股權比',
        'return_on_equity': '股東權益報酬率',
        'roe': '股東權益報酬率',
        'profit_margins': '利潤率',
        'profit_margin': '利潤率',
        'value_score': '價值評分'
    }
    
    # 應用顯示名稱
    new_column_names = []
    for col in final_df.columns:
        if col in column_display_names:
            new_column_names.append(column_display_names[col])
        else:
            new_column_names.append(col)
    
    final_df.columns = new_column_names
    
    st.dataframe(final_df, use_container_width=True)


def run_ai_analysis():
    """執行 AI 分析"""
    try:
        analyzer = EnhancedStockAnalyzer()
        top_stocks = st.session_state['top_stocks']
        max_analysis = st.session_state.get('max_analysis', 5)
        
        # 轉換為字典列表
        stock_list = top_stocks.head(max_analysis).to_dict('records')
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("正在進行 Gemini AI 分析...")
        
        # 執行分析
        analysis_results = []
        for i, stock_data in enumerate(stock_list):
            ticker = stock_data['ticker']
            status_text.text(f"正在分析 {ticker}... ({i+1}/{len(stock_list)})")
            
            result = analyzer.analyze_stock_comprehensive(stock_data)
            analysis_results.append(result)
            
            progress_bar.progress((i + 1) / len(stock_list))
        
        st.session_state['ai_analysis_results'] = analysis_results
        
        status_text.text("AI 分析完成！")
        st.success(f"成功完成 {len([r for r in analysis_results if 'error' not in r])} 支股票的 AI 分析")
        
    except Exception as e:
        st.error(f"AI 分析過程發生錯誤: {e}")


def display_ai_analysis_results():
    """顯示 AI 分析結果"""
    results = st.session_state['ai_analysis_results']
    
    st.markdown("### 🤖 綜合投資分析結果")
    
    for result in results:
        if 'error' not in result:
            ticker = result['ticker']
            company_name = result.get('company_name', 'Unknown')
            overall_score = result.get('overall_score', 0)
            recommendation = result.get('investment_recommendation', '無建議')
            
            # 根據評分設定顏色
            if overall_score >= 70:
                score_color = "🟢"
            elif overall_score >= 50:
                score_color = "🟡"
            else:
                score_color = "🔴"
            
            with st.expander(f"{score_color} {ticker} - {company_name} (評分: {overall_score})"):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("#### 📊 評分概況")
                    st.metric("綜合評分", f"{overall_score}/100")
                    st.write(f"**投資建議**: {recommendation}")
                    
                    # 基本面分析
                    fundamental = result.get('fundamental_analysis', {})
                    st.markdown("##### 💰 基本面分析")
                    st.write(f"- 評分: {fundamental.get('score', 'N/A')}/100")
                    st.write(f"- P/E比率: {fundamental.get('pe_ratio', 'N/A')}")
                    st.write(f"- P/B比率: {fundamental.get('pb_ratio', 'N/A')}")
                    st.write(f"- ROE: {fundamental.get('roe', 'N/A')}")
                
                with col2:
                    # 技術面分析
                    technical = result.get('technical_analysis', {})
                    st.markdown("##### 📈 技術面分析")
                    st.write(f"- 評分: {technical.get('score', 'N/A')}/100")
                    st.write(f"- 趨勢方向: {technical.get('trend', 'N/A')}")
                    st.write(f"- RSI: {technical.get('rsi', 'N/A')}")
                    st.write(f"- 成交量信號: {technical.get('volume_signal', 'N/A')}")
                    
                # 新聞情緒分析
                news_sentiment = result.get('news_sentiment_analysis', {})
                st.markdown("##### 📰 新聞情緒分析")
                st.write(f"- 評分: {news_sentiment.get('score', 'N/A')}/100")
                st.write(f"- 情緒: {news_sentiment.get('sentiment', 'N/A')}")
                st.write(f"- 信心度: {news_sentiment.get('confidence', 'N/A')}")
                st.write(f"- 新聞數量: {news_sentiment.get('news_count', 'N/A')}")
                
                # 新聞面情報報告
                news_report = news_sentiment.get('news_intelligence_report', '')
                if news_report and news_report != '無新聞數據或AI不可用':
                    with st.expander("📋 新聞面情報分析報告"):
                        st.markdown(news_report)                # 風險評估
                risk = result.get('risk_assessment', {})
                if risk:
                    st.markdown("##### ⚠️ 風險評估")
                    st.write(f"- 整體風險: {risk.get('overall_risk', 'N/A')}")
                    st.write(f"- 波動風險: {risk.get('volatility_risk', 'N/A')}")
                    st.write(f"- 估值風險: {risk.get('valuation_risk', 'N/A')}")
                
                # 關鍵主題
                key_themes = news_sentiment.get('key_themes', [])
                if key_themes:
                    st.markdown("##### 🔍 關鍵主題")
                    for theme in key_themes:
                        st.write(f"- {theme}")
                
                # 移除個別新聞顯示，改為只顯示綜合分析
                # 新聞數量統計
                if 'news_data' in result and result['news_data']:
                    news_count = len(result['news_data'])
                    st.markdown(f"##### 📊 新聞統計")
                    st.write(f"- 共分析 {news_count} 條新聞")
                    st.write(f"- 新聞來源涵蓋多個財經媒體")
                    st.write(f"- 已進行完整內容分析和情緒評估")
        else:
            st.error(f"❌ {result['ticker']}: {result.get('error', '未知錯誤')}")


def generate_investment_report():
    """生成投資報告"""
    if 'top_stocks' not in st.session_state:
        st.error("請先完成股票篩選")
        return
    
    df = st.session_state['top_stocks']
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
# S&P 500 價值投資分析報告
**生成時間**: {timestamp}

## 📋 執行摘要
本次分析從 S&P 500 指數成分股中，運用價值投資排名系統選出前 {len(df)} 支被低估股票。

## 🎯 評分標準 (適合複委託投資者)
- **本益比 (P/E)**: 30%權重 - 越低越好
- **市淨率 (P/B)**: 25%權重 - 越低越好
- **債務權益比**: 20%權重 - 越低越好
- **股東權益報酬率**: 15%權重 - 越高越好
- **利潤率**: 10%權重 - 越高越好

**投資策略**: 專注資本利得，不考慮股息配發

## 🏆 前 5 名被低估股票
"""
    
    for i, row in df.head(5).iterrows():
        pe = f"{row['trailing_pe']:.2f}" if pd.notna(row['trailing_pe']) else "N/A"
        pb = f"{row['price_to_book']:.2f}" if pd.notna(row['price_to_book']) else "N/A"
        debt_ratio = f"{row.get('debt_to_equity', 0):.2f}" if pd.notna(row.get('debt_to_equity')) else "N/A"
        score = f"{row['value_score']:.1f}" if pd.notna(row['value_score']) else "N/A"
        
        report += f"""
### 第{int(row.get('value_rank', i+1))}名. {row['ticker']} - {row.get('company_name', 'Unknown')}
- **行業**: {row.get('sector', 'Unknown')}
- **本益比**: {pe}
- **市淨率**: {pb}
- **債務權益比**: {debt_ratio}
- **價值評分**: {score}/100
"""
    
    report += """
## ⚠️ 免責聲明
本報告僅供教育和參考用途，不構成投資建議。投資前請諮詢專業財務顧問並進行充分的盡職調查。股票投資涉及風險，過去表現不代表未來結果。
"""
    
    st.session_state['investment_report'] = report


def create_download_files():
    """建立下載檔案"""
    if 'top_stocks' not in st.session_state:
        st.error("請先完成股票篩選")
        return
    
    df = st.session_state['top_stocks']
    
    # CSV 格式
    csv_data = df.to_csv(index=False, encoding='utf-8-sig')
    
    # JSON 格式
    json_data = df.to_json(orient='records', indent=2)
    
    st.session_state['download_data'] = {
        'screening_results.csv': csv_data,
        'screening_results.json': json_data
    }
    
    st.success("下載檔案已準備完成！")


def individual_stock_analysis_interface():
    """個股綜合分析介面"""
    st.markdown('<h2 class="sub-header">🎯 個股綜合分析</h2>', unsafe_allow_html=True)
    
    # 股票輸入
    col1, col2 = st.columns([2, 1])
    
    with col1:
        stock_symbol = st.text_input(
            "請輸入股票代碼",
            placeholder="例如：AAPL, TSLA, MSFT",
            help="輸入美股股票代碼進行綜合分析"
        )
    
    with col2:
        analysis_mode = st.selectbox(
            "分析模式",
            ["標準分析", "深度分析", "快速分析"],
            help="選擇分析深度"
        )
    
    if st.button("🔍 開始分析", type="primary"):
        if not stock_symbol:
            st.error("請輸入股票代碼")
            return
            
        # 顯示分析進度
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        try:
            # 初始化分析器
            status_text.text("初始化分析系統...")
            progress_bar.progress(10)
            
            individual_analyzer = StockIndividualAnalyzer()
            screener = ValueScreener()
            
            # 執行分析
            status_text.text("獲取股票數據...")
            progress_bar.progress(30)
            
            # 執行個股綜合分析
            analysis_result = screener.analyze_individual_stock_comprehensive(
                stock_symbol.upper()
            )
            
            if not analysis_result:
                st.error(f"無法獲取 {stock_symbol} 的數據，請檢查股票代碼是否正確")
                return
            
            progress_bar.progress(100)
            status_text.text("分析完成！")
            
            # 顯示分析結果
            display_individual_analysis_results(analysis_result, stock_symbol.upper())
            
        except Exception as e:
            st.error(f"分析過程中發生錯誤：{str(e)}")
            st.info("請稍後重試或檢查股票代碼是否正確")
    
    # 顯示分析說明
    with st.expander("📖 分析說明"):
        st.markdown("""
        ### 個股綜合分析包含三大維度：
        
        **🗞️ 新聞面分析 (權重 50%)**
        - 收集最新30篇相關新聞
        - 進行情感分析和關鍵詞提取
        - 評估市場情緒和投資者關注度
        
        **📈 技術面分析 (權重 30%)**
        - RSI 相對強弱指標
        - MACD 移動平均收斂發散
        - 移動平均線趨勢分析
        - 成交量分析
        
        **💰 籌碼面分析 (權重 20%)**
        - 機構持股比例
        - 內部人持股情況
        - 空頭比率分析
        - 股權集中度評估
        
        ### 評分標準：
        - **90-100分**: 極佳，強烈建議買入
        - **70-89分**: 良好，建議買入
        - **50-69分**: 中性，建議持有
        - **30-49分**: 較差，建議觀望
        - **0-29分**: 差，建議賣出
        """)


def display_individual_analysis_results(analysis_result, symbol):
    """顯示個股分析結果"""
    
    # 總體評分
    overall_score = analysis_result.get('overall_score', 0)
    recommendation = analysis_result.get('recommendation', '無建議')
    
    # 評分顏色
    if overall_score >= 70:
        score_color = "green"
    elif overall_score >= 50:
        score_color = "orange"
    else:
        score_color = "red"
    
    # 顯示總體評分
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background-color: #f0f2f6; border-radius: 10px; margin: 20px 0;">
        <h2 style="color: #1f77b4; margin-bottom: 10px;">{symbol} 綜合分析報告</h2>
        <h1 style="color: {score_color}; font-size: 3em; margin: 10px 0;">{overall_score:.1f}/100</h1>
        <h3 style="color: #333; margin-top: 10px;">投資建議：{recommendation}</h3>
    </div>
    """, unsafe_allow_html=True)
    
    # 分項評分
    col1, col2, col3 = st.columns(3)
    
    with col1:
        news_score = analysis_result.get('news_score', 0)
        st.metric(
            label="🗞️ 新聞面評分 (50%)",
            value=f"{news_score:.1f}/100",
            delta=None
        )
    
    with col2:
        tech_score = analysis_result.get('technical_score', 0)
        st.metric(
            label="📈 技術面評分 (25%)",
            value=f"{tech_score:.1f}/100",
            delta=None
        )
    
    with col3:
        chip_score = analysis_result.get('chip_score', 0)
        st.metric(
            label="💰 基本面評分 (25%)",
            value=f"{chip_score:.1f}/100",
            delta=None
        )
        st.metric(
            label="📈 技術面評分 (30%)",
            value=f"{tech_score:.1f}/100",
            delta=None
        )
    
    with col3:
        chip_score = analysis_result.get('chip_score', 0)
        st.metric(
            label="💰 籌碼面評分 (20%)",
            value=f"{chip_score:.1f}/100",
            delta=None
        )
    
    # 詳細分析結果
    tab1, tab2, tab3, tab4 = st.tabs(["📊 總體概覽", "🗞️ 新聞分析", "📈 技術分析", "💰 籌碼分析"])
    
    with tab1:
        display_overview_tab(analysis_result, symbol)
    
    with tab2:
        display_news_analysis_tab(analysis_result)
    
    with tab3:
        display_technical_analysis_tab(analysis_result)
    
    with tab4:
        display_chip_analysis_tab(analysis_result)


def display_overview_tab(analysis_result, symbol):
    """顯示總體概覽標籤"""
    st.subheader("📊 投資概覽")
    
    # 基本資訊
    if 'basic_info' in analysis_result:
        basic_info = analysis_result['basic_info']
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**基本資訊**")
            if 'current_price' in basic_info:
                st.write(f"當前股價: ${basic_info['current_price']:.2f}")
            if 'market_cap' in basic_info:
                market_cap = basic_info['market_cap']
                if market_cap > 1e9:
                    st.write(f"市值: ${market_cap/1e9:.1f}B")
                else:
                    st.write(f"市值: ${market_cap/1e6:.1f}M")
            if 'pe_ratio' in basic_info:
                st.write(f"本益比: {basic_info['pe_ratio']:.2f}")
        
        with col2:
            st.write("**風險指標**")
            if 'beta' in basic_info:
                st.write(f"Beta係數: {basic_info['beta']:.2f}")
            if 'volatility' in basic_info:
                st.write(f"波動率: {basic_info['volatility']:.2f}%")
    
    # 各維度評分雷達圖
    if all(key in analysis_result for key in ['news_score', 'technical_score', 'chip_score']):
        create_radar_chart(analysis_result)


def display_news_analysis_tab(analysis_result):
    """顯示新聞分析標籤 - 專注短線投資機會"""
    st.subheader("🗞️ 短線新聞情感分析 (權重: 50%) - 專注一週内投資機會")
    
    # 添加短線投資說明
    st.info("📈 **短線投資重點**: 本分析專注於一週內的新聞，特別關注24小時內的最新消息對股價的即時影響。")
    
    news_analysis = analysis_result.get('news_analysis', {})
    
    if news_analysis:
        # 情感分析總覽
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sentiment = news_analysis.get('sentiment', 'neutral')
            sentiment_color = {
                'positive': '🟢',
                'negative': '🔴', 
                'neutral': '🟡'
            }.get(sentiment, '🟡')
            st.metric("整體情緒", f"{sentiment_color} {sentiment.title()}")
        
        with col2:
            confidence = news_analysis.get('confidence', 0)
            st.metric("信心度", f"{confidence}/10")
        
        with col3:
            sentiment_strength = news_analysis.get('sentiment_strength', 0)
            st.metric("情緒強度", f"{sentiment_strength}/10")
        
        with col4:
            news_count = len(news_analysis.get('news_titles', []))
            st.metric("分析新聞數", f"{news_count}")
        
        # 最新新聞標題概覽
        if 'news_titles' in news_analysis and news_analysis['news_titles']:
            st.subheader("📰 最新新聞標題概覽")
            
            # 顯示新聞標題的可展開區域
            with st.expander("📋 查看所有新聞標題", expanded=True):
                for i, title in enumerate(news_analysis['news_titles'], 1):
                    st.write(f"**{i}.** {title}")
        
        # 如果有原始新聞數據，顯示詳細的中英文對照
        if 'news_data' in analysis_result and analysis_result['news_data']:
            st.subheader("📰 詳細新聞標題 (中英對照) - 專注一週內短線機會")
            
            with st.expander("🌐 查看中英文新聞標題對照", expanded=False):
                recent_count = 0
                for i, news_item in enumerate(analysis_result['news_data'][:5], 1):  # 顯示前5條
                    # 檢查是否為最近24小時內的新聞
                    is_recent = news_item.get('is_recent', False)
                    if is_recent:
                        recent_count += 1
                    
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        # 如果是24小時內的新聞，加上特殊標記
                        title_prefix = "🔥 **[最新]** " if is_recent else ""
                        
                        # 顯示中文標題（主要顯示）
                        chinese_title = news_item.get('title', '')
                        st.markdown(f"**{i}. {title_prefix}{chinese_title}**")
                        
                        # 顯示原文標題（如果有的話）
                        original_title = news_item.get('original_title', '')
                        if original_title and original_title != chinese_title:
                            st.caption(f"🔤 原文: {original_title}")
                        
                        # 顯示發布者和時間
                        publisher = news_item.get('publisher', 'N/A')
                        publish_time = news_item.get('publish_time', 'N/A')
                        
                        # 如果是最新新聞，用不同的顏色顯示時間
                        if is_recent:
                            st.caption(f"📅 **{publisher}** • **{publish_time}** ⚡")
                        else:
                            st.caption(f"📅 {publisher} • {publish_time}")
                    
                    with col2:
                        # 顯示新聞連結
                        news_url = news_item.get('url', '')
                        if news_url:
                            st.markdown(f"[🔗 閱讀原文]({news_url})")
                    
                    st.divider()
                
                # 顯示統計資訊
                if recent_count > 0:
                    st.info(f"🔥 找到 {recent_count} 條24小時內的最新新聞，適合短線投資分析")
        
        # 關鍵主題分析
        if 'key_themes' in news_analysis and news_analysis['key_themes']:
            st.subheader("� 關鍵主題分析")
            
            # 使用列來顯示關鍵主題
            themes = news_analysis['key_themes']
            if len(themes) > 0:
                theme_cols = st.columns(min(len(themes), 3))  # 最多3列
                for i, theme in enumerate(themes[:3]):  # 顯示前3個主題
                    with theme_cols[i % 3]:
                        st.info(f"🎯 {theme}")
                
                # 如果有更多主題，顯示在下面
                if len(themes) > 3:
                    for theme in themes[3:]:
                        st.write(f"• {theme}")
        
        # 市場影響評估
        if 'market_impact' in news_analysis and news_analysis['market_impact']:
            st.subheader("📊 市場影響評估")
            
            market_impact = news_analysis['market_impact']
            
            impact_col1, impact_col2, impact_col3 = st.columns(3)
            
            with impact_col1:
                st.markdown("**短期影響 (1-4週)**")
                st.write(market_impact.get('short_term', 'N/A'))
            
            with impact_col2:
                st.markdown("**中期影響 (1-3個月)**")
                st.write(market_impact.get('medium_term', 'N/A'))
            
            with impact_col3:
                st.markdown("**長期影響 (6-12個月)**")
                st.write(market_impact.get('long_term', 'N/A'))
        
        # 風險與機會分析
        risk_opp_col1, risk_opp_col2 = st.columns(2)
        
        with risk_opp_col1:
            if 'risk_factors' in news_analysis and news_analysis['risk_factors']:
                st.subheader("⚠️ 潛在風險因素")
                for risk in news_analysis['risk_factors']:
                    st.write(f"🔸 {risk}")
        
        with risk_opp_col2:
            if 'opportunities' in news_analysis and news_analysis['opportunities']:
                st.subheader("� 投資機會點")
                for opportunity in news_analysis['opportunities']:
                    st.write(f"🔹 {opportunity}")
        
        # 投資策略建議
        if 'investment_strategy' in news_analysis and news_analysis['investment_strategy']:
            st.subheader("💡 投資策略建議")
            st.info(news_analysis['investment_strategy'])
        
        # 關注要點
        if 'attention_points' in news_analysis and news_analysis['attention_points']:
            st.subheader("👀 需要關注的後續發展")
            attention_points = news_analysis['attention_points']
            if len(attention_points) <= 2:
                for point in attention_points:
                    st.write(f"📌 {point}")
            else:
                for point in attention_points:
                    st.write(f"• {point}")
        
        # 完整新聞面情報報告
        if 'news_intelligence_report' in news_analysis and news_analysis['news_intelligence_report']:
            with st.expander("📋 完整新聞面情報分析報告", expanded=False):
                report = news_analysis['news_intelligence_report']
                st.markdown(report)
    
    else:
        st.info("暫無新聞分析數據")
        st.write("請先在 AI 分析標籤中執行股票分析以獲取新聞數據。")


def display_technical_analysis_tab(analysis_result):
    """顯示技術分析標籤"""
    st.subheader("📈 技術指標分析")
    
    tech_analysis = analysis_result.get('technical_analysis', {})
    
    if tech_analysis:
        # 技術指標概覽
        col1, col2, col3 = st.columns(3)
        
        with col1:
            rsi = tech_analysis.get('rsi', 0)
            st.metric("RSI", f"{rsi:.1f}")
            if rsi > 70:
                st.caption("🔴 超買區域")
            elif rsi < 30:
                st.caption("🟢 超賣區域")
            else:
                st.caption("🟡 正常區域")
        
        with col2:
            macd = tech_analysis.get('macd', 0)
            st.metric("MACD", f"{macd:.3f}")
            if macd > 0:
                st.caption("🟢 多頭訊號")
            else:
                st.caption("🔴 空頭訊號")
        
        with col3:
            ma_signal = tech_analysis.get('ma_signal', 'neutral')
            signal_text = {"bullish": "多頭", "bearish": "空頭", "neutral": "中性"}
            st.metric("移動平均", signal_text.get(ma_signal, "中性"))
        
        # 移動平均線分析
        if 'moving_averages' in tech_analysis:
            st.subheader("📊 移動平均線")
            ma_data = tech_analysis['moving_averages']
            
            col1, col2 = st.columns(2)
            with col1:
                if 'ma_20' in ma_data:
                    st.write(f"20日均線: ${ma_data['ma_20']:.2f}")
                if 'ma_50' in ma_data:
                    st.write(f"50日均線: ${ma_data['ma_50']:.2f}")
            
            with col2:
                if 'ma_200' in ma_data:
                    st.write(f"200日均線: ${ma_data['ma_200']:.2f}")
                if 'current_price' in ma_data:
                    st.write(f"當前價格: ${ma_data['current_price']:.2f}")
    else:
        st.info("暫無技術分析數據")


def display_chip_analysis_tab(analysis_result):
    """顯示籌碼分析標籤"""
    st.subheader("💰 籌碼結構分析")
    
    chip_analysis = analysis_result.get('chip_analysis', {})
    
    if chip_analysis:
        # 持股結構
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**機構持股**")
            institutional = chip_analysis.get('institutional_ownership', 0)
            st.metric("機構持股比例", f"{institutional:.1f}%")
            
            insider = chip_analysis.get('insider_ownership', 0)
            st.metric("內部人持股", f"{insider:.1f}%")
        
        with col2:
            st.write("**市場指標**")
            short_ratio = chip_analysis.get('short_ratio', 0)
            st.metric("空頭比率", f"{short_ratio:.2f}")
            
            float_short = chip_analysis.get('percent_held_by_institutions', 0)
            st.metric("機構持有比例", f"{float_short:.1f}%")
        
        # 籌碼評估
        st.subheader("📋 籌碼評估")
        ownership_score = chip_analysis.get('ownership_score', 0)
        
        if ownership_score >= 80:
            st.success(f"籌碼結構優良 (評分: {ownership_score:.1f})")
        elif ownership_score >= 60:
            st.info(f"籌碼結構一般 (評分: {ownership_score:.1f})")
        else:
            st.warning(f"籌碼結構需關注 (評分: {ownership_score:.1f})")
    else:
        st.info("暫無籌碼分析數據")


def create_radar_chart(analysis_result):
    """創建評分雷達圖"""
    import plotly.graph_objects as go
    
    categories = ['新聞面', '技術面', '籌碼面']
    scores = [
        analysis_result.get('news_score', 0),
        analysis_result.get('technical_score', 0),
        analysis_result.get('chip_score', 0)
    ]
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatterpolar(
        r=scores,
        theta=categories,
        fill='toself',
        name='評分',
        line_color='rgb(31, 119, 180)'
    ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 100]
            )),
        showlegend=False,
        title="三維度評分雷達圖",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
