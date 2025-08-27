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
from src.data_fetcher import SP500DataFetcher
from src.screener import ValueScreener
from src.enhanced_analyzer import EnhancedStockAnalyzer
from src.utils import setup_logging, load_env_variables, format_currency, format_percentage, format_ratio
from config.settings import SCREENING_CRITERIA, OUTPUT_SETTINGS


# 設置頁面配置
st.set_page_config(
    page_title="S&P 500 價值投資分析系統",
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
    st.markdown('<h1 class="main-header">📈 S&P 500 價值投資分析系統</h1>', unsafe_allow_html=True)
    
    # 側邊欄 - 系統控制
    setup_sidebar()
    
    # 主要內容區域
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 股票篩選", "📊 數據分析", "🤖 AI 分析", "📋 結果報告"])
    
    with tab1:
        screening_interface()
    
    with tab2:
        data_analysis_interface()
    
    with tab3:
        ai_analysis_interface()
    
    with tab4:
        report_interface()


def setup_sidebar():
    """設置側邊欄"""
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
        max_value=50,
        value=OUTPUT_SETTINGS['max_stocks_to_analyze'],
        help="限制分析的股票數量以節省時間"
    )
    
    # 將自訂標準存儲到 session state
    st.session_state['custom_criteria'] = custom_criteria
    st.session_state['max_stocks'] = max_stocks


def screening_interface():
    """股票篩選介面"""
    st.markdown('<h2 class="sub-header">🔍 股票篩選</h2>', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 分析流程")
        
        # 步驟 1: 獲取數據
        if st.button("1️⃣ 獲取 S&P 500 數據", use_container_width=True):
            with st.spinner("正在獲取 S&P 500 成分股數據..."):
                fetch_sp500_data()
        
        # 步驟 2: 價值投資排名
        if st.button("2️⃣ 價值投資排名分析", use_container_width=True):
            if 'raw_data' not in st.session_state:
                st.error("請先獲取 S&P 500 數據")
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
    
    df = st.session_state['top_stocks']
    
    # 總覽統計
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("篩選出股票數", len(df))
    
    with col2:
        avg_pe = df['trailing_pe'].mean() if 'trailing_pe' in df.columns else None
        st.metric("平均本益比", f"{avg_pe:.2f}" if pd.notna(avg_pe) else "N/A")
    
    with col3:
        avg_pb = df['price_to_book'].mean() if 'price_to_book' in df.columns else None
        st.metric("平均市淨率", f"{avg_pb:.2f}" if pd.notna(avg_pb) else "N/A")
    
    with col4:
        avg_score = df['value_score'].mean() if 'value_score' in df.columns else None
        st.metric("平均評分", f"{avg_score:.2f}" if pd.notna(avg_score) else "N/A")
    
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


@st.cache_data
def fetch_sp500_data():
    """獲取 S&P 500 數據"""
    try:
        fetcher = SP500DataFetcher()
        
        # 獲取股票列表
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.text("正在獲取 S&P 500 成分股列表...")
        progress_bar.progress(20)
        
        tickers = fetcher.get_sp500_tickers()
        
        status_text.text("正在獲取股票財務數據...")
        progress_bar.progress(40)
        
        # 限制獲取數量以提高速度
        raw_data = fetcher.batch_fetch_stock_data(tickers, max_stocks=100)
        
        progress_bar.progress(100)
        status_text.text("數據獲取完成！")
        
        st.session_state['raw_data'] = raw_data
        st.session_state['tickers'] = tickers
        
        st.success(f"成功獲取 {len(raw_data)} 支股票的數據")
        
    except Exception as e:
        st.error(f"數據獲取失敗: {e}")


def apply_screening():
    """應用價值投資排名分析"""
    try:
        raw_data = st.session_state['raw_data']
        max_stocks = st.session_state.get('max_stocks', 10)
        
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
    
    # 建立圖表
    tab1, tab2, tab3 = st.tabs(["估值指標分布", "行業分析", "評分分析"])
    
    with tab1:
        col1, col2 = st.columns(2)
        
        with col1:
            # 本益比分布
            fig_pe = px.histogram(df, x='trailing_pe', title='本益比分布', 
                                nbins=20, labels={'trailing_pe': '本益比', 'count': '股票數量'})
            st.plotly_chart(fig_pe, use_container_width=True)
        
        with col2:
            # 市淨率分布
            fig_pb = px.histogram(df, x='price_to_book', title='市淨率分布',
                                nbins=20, labels={'price_to_book': '市淨率', 'count': '股票數量'})
            st.plotly_chart(fig_pb, use_container_width=True)
    
    with tab2:
        if 'sector' in df.columns:
            # 行業分布
            sector_counts = df['sector'].value_counts()
            fig_sector = px.pie(values=sector_counts.values, names=sector_counts.index, 
                              title='行業分布')
            st.plotly_chart(fig_sector, use_container_width=True)
            
            # 各行業平均評分
            if 'value_score' in df.columns:
                sector_scores = df.groupby('sector')['value_score'].mean().sort_values(ascending=False)
                fig_sector_score = px.bar(x=sector_scores.index, y=sector_scores.values,
                                        title='各行業平均評分',
                                        labels={'x': '行業', 'y': '平均評分'})
                st.plotly_chart(fig_sector_score, use_container_width=True)
    
    with tab3:
        # 評分散布圖
        if 'value_score' in df.columns and 'trailing_pe' in df.columns and 'price_to_book' in df.columns:
            fig_scatter = px.scatter(df, x='trailing_pe', y='price_to_book', 
                                   size='value_score', color='value_score',
                                   hover_data=['ticker', 'company_name'],
                               title='估值指標與評分關係')
        st.plotly_chart(fig_scatter, use_container_width=True)


def display_detailed_table(df):
    """顯示詳細數據表格"""
    # 選擇要顯示的欄位 (移除股息相關)
    columns_to_show = [
        'value_rank', 'ticker', 'company_name', 'sector', 'market_cap',
        'trailing_pe', 'price_to_book', 'debt_to_equity', 'return_on_equity',
        'profit_margins', 'value_score'
    ]
    
    available_columns = [col for col in columns_to_show if col in df.columns]
    display_df = df[available_columns].copy()
    
    # 格式化顯示
    if 'market_cap' in display_df.columns:
        display_df['market_cap'] = display_df['market_cap'].apply(lambda x: format_currency(x) if pd.notna(x) else "N/A")
    if 'return_on_equity' in display_df.columns:
        display_df['return_on_equity'] = display_df['return_on_equity'].apply(lambda x: format_percentage(x) if pd.notna(x) else "N/A")
    if 'profit_margins' in display_df.columns:
        display_df['profit_margins'] = display_df['profit_margins'].apply(lambda x: format_percentage(x) if pd.notna(x) else "N/A")
    
    st.dataframe(display_df, use_container_width=True)


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


if __name__ == "__main__":
    main()
