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
import time
from datetime import datetime
import logging

# 導入自訂模組
from src.data_fetcher import SP500DataFetcher, MultiMarketDataFetcher, STOCK_PORTFOLIOS
from src.screener import ValueScreener
from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate
from src.stock_individual_analyzer import StockIndividualAnalyzer
from src.utils import setup_logging, load_env_variables, format_currency, format_percentage, format_ratio, DateTimeEncoder
from src.portfolio_db import PortfolioDatabase, portfolio_db, format_currency as format_portfolio_currency, get_currency_symbol
from src.analysis_status import AnalysisStatusManager, MultiStockAnalysisStatus, analysis_status, portfolio_analysis_status
from config.settings import SCREENING_CRITERIA, OUTPUT_SETTINGS, MULTI_AGENT_SETTINGS


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
    tab1, tab2, tab3 = st.tabs([
        "🔍 股票篩選與AI分析", 
        "💼 持股管理", 
        "📊 持股AI分析"
    ])
    
    with tab1:
        combined_screening_ai_interface()
    
    with tab2:
        portfolio_management_interface()
    
    with tab3:
        portfolio_analysis_interface()


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
    
    # 檢查多 API Key 系統狀態
    try:
        from src.gemini_key_manager import get_gemini_keys_status, get_current_gemini_key
        key_status = get_gemini_keys_status()
        available_keys = key_status.get('total_keys', 0)
        
        if available_keys > 0:
            st.sidebar.success(f"✅ Gemini API 已設置 ({available_keys} 個 Key)")
            
            # 顯示 Key 管理器狀態
            with st.sidebar.expander("🔑 API Key 狀態"):
                for key_info in key_status.get('keys_status', []):
                    status_icon = "🔴" if key_info.get('is_blocked') else "🟢"
                    current_icon = "👉" if key_info.get('is_current') else "  "
                    st.write(f"{current_icon} {status_icon} Key {key_info['index']}: {key_info['request_count']} 次請求")
                    
                    # 顯示分配的代理人
                    if key_info.get('assigned_agents'):
                        agents_text = ", ".join(key_info['assigned_agents'])
                        st.caption(f"   分配給: {agents_text}")
        else:
            st.sidebar.error("⚠️ 請設置 Gemini API Key")
            st.sidebar.info("請在 .env 檔案中設置 GEMINI_API_KEY 或 GEMINI_API_KEY_1 到 GEMINI_API_KEY_5")
            
    except Exception as e:
        # 回退到原有檢查
        if not gemini_key or gemini_key == 'your_gemini_api_key_here':
            st.sidebar.error("⚠️ 請設置 Gemini API Key")
            st.sidebar.info("請在 .env 檔案中設置 GEMINI_API_KEY")
        else:
            st.sidebar.success("✅ Gemini API 已設置")
    
    # 其他設置
    st.sidebar.markdown("## 🔧 其他設置")
    
    max_stocks = st.sidebar.number_input(
        "最多分析股票數量",
        min_value=5,
        max_value=600,  # 提高限制以支援完整SP500分析
        value=min(OUTPUT_SETTINGS['max_stocks_to_analyze'], 500),  # 預設500或配置值中較小者
        help="分析的股票數量。SP500約有500支成分股"
    )
    
    # 多代理人辯論設置
    st.sidebar.markdown("## 🤖 AI 多代理人分析")
    
    enable_debate = st.sidebar.checkbox(
        "啟用多代理人辯論分析",
        value=MULTI_AGENT_SETTINGS.get('enable_debate', False),
        help="啟用5位AI投資專家的辯論分析，提供更全面的投資觀點"
    )
    
    if enable_debate:
        st.sidebar.info("🎯 **投資專家團隊：**")
        st.sidebar.markdown("• 巴菲特派價值投資師")
        st.sidebar.markdown("• 葛拉漢派防御型投資師")
        st.sidebar.markdown("• 成長價值投資師")
        st.sidebar.markdown("• 市場時機分析師")
        st.sidebar.markdown("• 風險管理專家")
        
        max_analysis = st.sidebar.slider(
            "多代理人分析股票數量",
            min_value=1,
            max_value=min(10, max_stocks),
            value=min(5, max_stocks),
            help="進行多代理人辯論分析的股票數量（建議5-10支）"
        )
        
        st.session_state['max_analysis'] = max_analysis
    else:
        st.session_state['max_analysis'] = min(10, max_stocks)
    
    # 將設置存儲到 session state
    st.session_state['enable_debate'] = enable_debate
    st.session_state['max_stocks'] = max_stocks


def combined_screening_ai_interface():
    """股票篩選與AI分析合併介面"""
    st.markdown('<h2 class="sub-header">🔍 股票篩選與AI分析</h2>', unsafe_allow_html=True)
    
    # 顯示當前選擇的投資組合
    if 'selected_portfolio' in st.session_state:
        portfolio_config = STOCK_PORTFOLIOS[st.session_state['selected_portfolio']]
        st.info(f"📊 當前投資組合：{portfolio_config['name']} - {portfolio_config['description']}")
    
    # 檢查 API 設置
    env_vars = load_env_variables()
    api_available = env_vars.get('gemini_api_key') and env_vars.get('gemini_api_key') != 'your_gemini_api_key_here'
    
    if not api_available:
        st.warning("⚠️ 未設置 Gemini API Key，僅能進行基本篩選，無法執行 AI 分析")
    
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
                for key in ['raw_data', 'current_portfolio', 'top_stocks', 'ai_analysis_results']:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()
        
        # 步驟 2: 價值投資篩選
        if st.button("2️⃣ 價值投資篩選", use_container_width=True, help="進行價值投資篩選和排名"):
            if 'raw_data' not in st.session_state:
                st.error(f"請先獲取 {portfolio_name} 數據")
            else:
                with st.spinner("正在進行價值投資排名分析..."):
                    apply_screening()
        
        # 步驟 3: AI 分析
        if api_available and 'top_stocks' in st.session_state:
            if st.button("3️⃣ AI 深度分析", use_container_width=True, help="執行多代理人AI深度分析"):
                with st.spinner("正在執行 AI 分析..."):
                    run_ai_analysis()
        elif not api_available and 'top_stocks' in st.session_state:
            st.info("ℹ️ 需要設置 Gemini API Key 才能執行 AI 分析")
        elif 'top_stocks' not in st.session_state:
            st.info("ℹ️ 請先完成價值投資篩選才能執行 AI 分析")
    
    with col2:
        st.markdown("### 設置")
        
        # AI 分析設置（僅在 API 可用時顯示）
        if api_available:
            max_analysis = st.number_input(
                "AI 分析股票數量",
                min_value=1,
                max_value=10,
                value=st.session_state.get('max_analysis', 5),
                help="選擇要進行 AI 分析的股票數量"
            )
            st.session_state['max_analysis'] = max_analysis
            
            # 多代理人辯論設置顯示
            enable_debate = st.session_state.get('enable_debate', False)
            if enable_debate:
                st.success("🤖 多代理人辯論已啟用")
            else:
                st.info("ℹ️ 多代理人辯論已關閉")
        
        st.markdown("---")
        st.markdown("### 📈 流程狀態")
        
        # 步驟 1 狀態
        if 'raw_data' in st.session_state:
            st.success("✅ 1. 數據已獲取")
        else:
            st.warning("⏳ 1. 待獲取數據")
        
        # 步驟 2 狀態
        if 'top_stocks' in st.session_state:
            st.success("✅ 2. 價值篩選完成")
        else:
            st.warning("⏳ 2. 待執行篩選")
        
        # 步驟 3 狀態
        if 'ai_analysis_results' in st.session_state:
            st.success("✅ 3. AI分析完成")
        elif 'top_stocks' in st.session_state and api_available:
            st.warning("⏳ 3. 待執行AI分析")
        elif not api_available:
            st.error("❌ 3. 無API Key")
        else:
            st.warning("⏳ 3. 待執行AI分析")
        
        st.markdown("---")
        st.markdown("**📋 操作說明:**")
        st.markdown("1. 🔄 獲取投資組合數據")
        st.markdown("2. 📊 執行價值投資篩選")
        st.markdown("3. 🤖 進行AI深度分析")
        st.markdown("4. 📈 查看詳細結果")
    
    # 顯示篩選結果
    if 'top_stocks' in st.session_state:
        st.markdown("---")
        st.markdown("### 📊 篩選結果")
        display_screening_results()
    
    # 顯示AI分析結果
    if 'ai_analysis_results' in st.session_state:
        st.markdown("---")
        st.markdown("### 🤖 AI 分析結果")
        display_ai_analysis_results()


def portfolio_management_interface():
    """持股管理介面 - 新增、刪除、更新持股"""
    st.markdown('<h2 class="sub-header">💼 持股管理</h2>', unsafe_allow_html=True)
    
    # 初始化資料庫
    db = portfolio_db
    
    # 上方按鈕區域
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 重新整理", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 查看投資組合摘要", use_container_width=True):
            show_portfolio_summary = True
        else:
            show_portfolio_summary = False
    
    # 顯示投資組合摘要
    if show_portfolio_summary:
        summary = db.get_portfolio_summary()
        if summary:
            st.markdown("### 📊 投資組合摘要")
            col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
            
            with col_sum1:
                st.metric("總持股數", summary.get('total_holdings', 0))
            
            with col_sum2:
                st.metric("美股", summary.get('us_stocks', 0))
            
            with col_sum3:
                st.metric("台股", summary.get('tw_stocks', 0))
            
            with col_sum4:
                # 顯示投資額
                usd_amount = summary.get('total_cost_usd')
                twd_amount = summary.get('total_cost_twd')
                
                if usd_amount and twd_amount:
                    st.metric("美股投資額", f"${usd_amount:,.2f}")
                    st.metric("台股投資額", f"NT${twd_amount:,.0f}")
                elif usd_amount:
                    st.metric("總投資額", f"${usd_amount:,.2f}")
                elif twd_amount:
                    st.metric("總投資額", f"NT${twd_amount:,.0f}")
                else:
                    st.metric("總投資額", "未設定")
            
            # 如果同時有美股和台股投資，分別顯示
            if summary.get('total_cost_usd') and summary.get('total_cost_twd'):
                st.markdown("#### 💰 分市場投資額")
                col_invest1, col_invest2 = st.columns(2)
                
                with col_invest1:
                    st.info(f"🇺🇸 美股投資: **${summary['total_cost_usd']:,.2f}**")
                
                with col_invest2:
                    st.info(f"🇹🇼 台股投資: **NT${summary['total_cost_twd']:,.0f}**")
    
    # 分為兩欄：新增持股 和 持股列表
    col_left, col_right = st.columns([1, 1])
    
    with col_left:
        st.markdown("### ➕ 新增持股")
        
        with st.form("add_stock_form"):
            # 股票基本資訊
            symbol = st.text_input(
                "股票代碼", 
                placeholder="例如：AAPL 或 2330 (台股自動加.TW)",
                help="台股只需輸入4位數字代碼，系統會自動添加.TW"
            ).strip()
            
            name = st.text_input("公司名稱", placeholder="例如：Apple Inc. 或 台積電")
            
            # 市場選擇（自動判斷）
            if symbol:
                if symbol.isdigit() and len(symbol) == 4:
                    detected_market = "TW (自動偵測)"
                    actual_market = "TW"
                elif '.TW' in symbol.upper() or '.TWO' in symbol.upper():
                    detected_market = "TW (自動偵測)"
                    actual_market = "TW"
                else:
                    detected_market = "US (自動偵測)"
                    actual_market = "US"
                
                st.info(f"🔍 偵測到市場: {detected_market}")
            else:
                actual_market = "US"
            
            # 持股詳細資訊（選填）
            st.markdown("**持股詳細資訊（選填）**")
            col_shares, col_cost = st.columns(2)
            
            with col_shares:
                shares = st.number_input("持股數量", min_value=0.0, value=0.0, step=1.0)
            
            with col_cost:
                if symbol:
                    if symbol.isdigit() and len(symbol) == 4:
                        cost_label = "平均成本 (新台幣)"
                    elif '.TW' in symbol.upper():
                        cost_label = "平均成本 (新台幣)"
                    else:
                        cost_label = "平均成本 (美元)"
                else:
                    cost_label = "平均成本"
                
                avg_cost = st.number_input(cost_label, min_value=0.0, value=0.0, step=0.01)
            
            notes = st.text_area("備註", placeholder="投資理由或其他備註...")
            
            submitted = st.form_submit_button("➕ 新增股票", use_container_width=True)
            
            if submitted:
                if symbol and name:
                    # 設置shares和avg_cost為None如果為0
                    shares_val = shares if shares > 0 else None
                    cost_val = avg_cost if avg_cost > 0 else None
                    
                    # 檢查是否已存在（用於顯示合併訊息）
                    existing = db.get_holding(symbol, actual_market)
                    
                    success = db.add_stock(symbol, name, actual_market, shares_val, cost_val, notes)
                    
                    if success:
                        if existing and existing.get('shares') and existing.get('avg_cost') and shares_val and cost_val:
                            st.success(f"✅ 成功合併持股 {symbol} - {name} (已進行加權平均)")
                        else:
                            st.success(f"✅ 成功新增 {symbol} - {name}")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ 新增失敗")
                else:
                    st.error("❌ 請填寫股票代碼和公司名稱")
    
    with col_right:
        st.markdown("### 📋 我的持股")
        
        # 市場篩選和批量操作
        col_filter, col_batch = st.columns(2)
        
        with col_filter:
            market_filter = st.selectbox("篩選市場", ["全部", "US", "TW"], key="market_filter")
        
        with col_batch:
            if st.button("🗑️ 批量刪除", use_container_width=True):
                st.session_state['show_batch_delete'] = True
        
        # 獲取持股
        if market_filter == "全部":
            holdings = db.get_all_holdings()
        else:
            holdings = db.get_holdings_by_market(market_filter)
        
        # 批量刪除介面
        if st.session_state.get('show_batch_delete', False):
            st.markdown("#### 🗑️ 批量刪除持股")
            
            if holdings:
                # 選擇要刪除的股票
                delete_options = []
                for holding in holdings:
                    delete_options.append({
                        'label': f"{holding['symbol']} - {holding['name']} ({holding['market']})",
                        'value': (holding['symbol'], holding['market'])
                    })
                
                selected_to_delete = st.multiselect(
                    "選擇要刪除的股票",
                    options=[opt['value'] for opt in delete_options],
                    format_func=lambda x: next(opt['label'] for opt in delete_options if opt['value'] == x)
                )
                
                col_confirm, col_cancel = st.columns(2)
                
                with col_confirm:
                    if st.button("⚠️ 確認刪除", use_container_width=True, type="primary"):
                        if selected_to_delete:
                            results = db.batch_remove_stocks(selected_to_delete)
                            success_count = sum(1 for success in results.values() if success)
                            
                            if success_count > 0:
                                st.success(f"✅ 成功刪除 {success_count} 檔股票")
                                st.session_state['show_batch_delete'] = False
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ 刪除失敗")
                        else:
                            st.warning("⚠️ 請選擇要刪除的股票")
                
                with col_cancel:
                    if st.button("❌ 取消", use_container_width=True):
                        st.session_state['show_batch_delete'] = False
                        st.rerun()
            else:
                st.info("📝 沒有股票可以刪除")
                if st.button("❌ 關閉", use_container_width=True):
                    st.session_state['show_batch_delete'] = False
                    st.rerun()
        
        if holdings:
            for i, holding in enumerate(holdings):
                with st.expander(f"{holding['symbol']} - {holding['name']}", expanded=False):
                    col_info1, col_info2 = st.columns(2)
                    
                    with col_info1:
                        market_flag = "🇺🇸" if holding['market'] == 'US' else "🇹🇼"
                        st.write(f"**市場：** {market_flag} {holding['market']}")
                        
                        if holding['shares']:
                            st.write(f"**持股數量：** {holding['shares']:,.0f}")
                        
                        if holding['avg_cost'] and holding.get('currency'):
                            currency_symbol = get_currency_symbol(holding['currency'])
                            st.write(f"**平均成本：** {currency_symbol}{holding['avg_cost']:,.2f}")
                        
                        if holding['shares'] and holding['avg_cost'] and holding.get('currency'):
                            total_cost = holding['shares'] * holding['avg_cost']
                            currency_symbol = get_currency_symbol(holding['currency'])
                            st.write(f"**總投資額：** {currency_symbol}{total_cost:,.2f}")
                    
                    with col_info2:
                        if holding['notes']:
                            st.write(f"**備註：** {holding['notes']}")
                        st.write(f"**創建時間：** {holding['created_at'][:16]}")
                        st.write(f"**更新時間：** {holding['updated_at'][:16]}")
                    
                    # 操作按鈕
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    
                    with col_btn1:
                        if st.button("✏️ 編輯", key=f"edit_{holding['symbol']}_{holding['market']}"):
                            st.session_state[f'editing_{holding["symbol"]}_{holding["market"]}'] = True
                    
                    with col_btn2:
                        if st.button("🗑️ 刪除", key=f"delete_{holding['symbol']}_{holding['market']}"):
                            if db.remove_stock(holding['symbol'], holding['market']):
                                st.success(f"✅ 已刪除 {holding['symbol']}")
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error("❌ 刪除失敗")
                    
                    # 編輯模式
                    if st.session_state.get(f'editing_{holding["symbol"]}_{holding["market"]}'):
                        st.markdown("---")
                        st.markdown("**編輯持股資訊**")
                        
                        with st.form(f"edit_form_{holding['symbol']}_{holding['market']}"):
                            new_shares = st.number_input(
                                "新的持股數量", 
                                value=float(holding['shares']) if holding['shares'] else 0.0,
                                min_value=0.0, step=1.0
                            )
                            
                            # 根據市場顯示適當的貨幣標籤
                            currency = holding.get('currency', 'USD')
                            currency_name = "新台幣" if currency == "TWD" else "美元"
                            
                            new_cost = st.number_input(
                                f"新的平均成本 ({currency_name})",
                                value=float(holding['avg_cost']) if holding['avg_cost'] else 0.0,
                                min_value=0.0, step=0.01
                            )
                            new_notes = st.text_area(
                                "新的備註",
                                value=holding['notes'] if holding['notes'] else ""
                            )
                            
                            col_form_btn1, col_form_btn2 = st.columns(2)
                            
                            with col_form_btn1:
                                if st.form_submit_button("💾 儲存", use_container_width=True):
                                    shares_val = new_shares if new_shares > 0 else None
                                    cost_val = new_cost if new_cost > 0 else None
                                    
                                    if db.update_holding(
                                        holding['symbol'], holding['market'],
                                        shares_val, cost_val, new_notes
                                    ):
                                        st.success("✅ 更新成功")
                                        del st.session_state[f'editing_{holding["symbol"]}_{holding["market"]}']
                                        time.sleep(1)
                                        st.rerun()
                                    else:
                                        st.error("❌ 更新失敗")
                            
                            with col_form_btn2:
                                if st.form_submit_button("❌ 取消", use_container_width=True):
                                    del st.session_state[f'editing_{holding["symbol"]}_{holding["market"]}']
                                    st.rerun()
        else:
            st.info("📝 還沒有持股資料，請先新增股票")


def portfolio_analysis_interface():
    """持股AI分析介面"""
    st.markdown('<h2 class="sub-header">📊 持股AI分析</h2>', unsafe_allow_html=True)
    
    # 檢查 API 設置
    env_vars = load_env_variables()
    api_available = env_vars.get('gemini_api_key') and env_vars.get('gemini_api_key') != 'your_gemini_api_key_here'
    
    if not api_available:
        st.error("⚠️ 請先設置 Gemini API Key 才能使用AI分析功能")
        return
    
    # 獲取持股資料
    db = portfolio_db
    holdings = db.get_all_holdings()
    
    if not holdings:
        st.warning("📝 還沒有持股資料，請先到「持股管理」新增股票")
        return
    
    # 初始化分析列表（如果不存在）
    if 'analysis_list' not in st.session_state:
        st.session_state['analysis_list'] = [
            {
                'symbol': h['symbol'],
                'name': h['name'],
                'market': h['market'],
                'included': True
            }
            for h in holdings
        ]
    else:
        # 更新分析列表（處理新增或刪除的股票）
        existing_symbols = {f"{item['symbol']}_{item['market']}" for item in st.session_state['analysis_list']}
        current_symbols = {f"{h['symbol']}_{h['market']}" for h in holdings}
        
        # 移除已經不存在的股票
        st.session_state['analysis_list'] = [
            item for item in st.session_state['analysis_list']
            if f"{item['symbol']}_{item['market']}" in current_symbols
        ]
        
        # 添加新增的股票
        for h in holdings:
            key = f"{h['symbol']}_{h['market']}"
            if key not in existing_symbols:
                st.session_state['analysis_list'].append({
                    'symbol': h['symbol'],
                    'name': h['name'],
                    'market': h['market'],
                    'included': True
                })
    
    # 顯示持股選擇列表
    st.markdown("### 🎯 選擇要分析的股票")
    st.markdown("✅ 表示將被分析，❌ 表示將被剔除")
    
    # 按市場分組顯示
    us_stocks = [item for item in st.session_state['analysis_list'] if item['market'] == 'US']
    tw_stocks = [item for item in st.session_state['analysis_list'] if item['market'] == 'TW']
    
    # 美股區域
    if us_stocks:
        st.markdown("#### 🇺🇸 美股")
        for i, stock in enumerate(us_stocks):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                status = "✅" if stock['included'] else "❌"
                st.write(f"{status} **{stock['symbol']}** - {stock['name']}")
            
            with col2:
                if stock['included']:
                    if st.button("❌ 剔除", key=f"remove_us_{i}", use_container_width=True):
                        # 直接修改analysis_list
                        for item in st.session_state['analysis_list']:
                            if item['symbol'] == stock['symbol'] and item['market'] == stock['market']:
                                item['included'] = False
                                break
                        st.rerun()
                else:
                    if st.button("✅ 加入", key=f"add_us_{i}", use_container_width=True):
                        # 直接修改analysis_list
                        for item in st.session_state['analysis_list']:
                            if item['symbol'] == stock['symbol'] and item['market'] == stock['market']:
                                item['included'] = True
                                break
                        st.rerun()
    
    # 台股區域
    if tw_stocks:
        st.markdown("#### 🇹🇼 台股")
        for i, stock in enumerate(tw_stocks):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                status = "✅" if stock['included'] else "❌"
                st.write(f"{status} **{stock['symbol']}** - {stock['name']}")
            
            with col2:
                if stock['included']:
                    if st.button("❌ 剔除", key=f"remove_tw_{i}", use_container_width=True):
                        # 直接修改analysis_list
                        for item in st.session_state['analysis_list']:
                            if item['symbol'] == stock['symbol'] and item['market'] == stock['market']:
                                item['included'] = False
                                break
                        st.rerun()
                else:
                    if st.button("✅ 加入", key=f"add_tw_{i}", use_container_width=True):
                        # 直接修改analysis_list
                        for item in st.session_state['analysis_list']:
                            if item['symbol'] == stock['symbol'] and item['market'] == stock['market']:
                                item['included'] = True
                                break
                        st.rerun()
    
    # 快速操作按鈕
    st.markdown("---")
    col_quick1, col_quick2, col_quick3, col_quick4 = st.columns(4)
    
    with col_quick1:
        if st.button("✅ 全選", use_container_width=True):
            for item in st.session_state['analysis_list']:
                item['included'] = True
            st.rerun()
    
    with col_quick2:
        if st.button("❌ 全部剔除", use_container_width=True):
            for item in st.session_state['analysis_list']:
                item['included'] = False
            st.rerun()
    
    with col_quick3:
        if st.button("🇺🇸 僅選美股", use_container_width=True):
            for item in st.session_state['analysis_list']:
                item['included'] = (item['market'] == 'US')
            st.rerun()
    
    with col_quick4:
        if st.button("🇹🇼 僅選台股", use_container_width=True):
            for item in st.session_state['analysis_list']:
                item['included'] = (item['market'] == 'TW')
            st.rerun()
    
    # 統計選中的股票
    selected_stocks = [item for item in st.session_state['analysis_list'] if item['included']]
    selected_tickers = [item['symbol'] for item in selected_stocks]
    
    if selected_stocks:
        st.success(f"✅ 已選擇 {len(selected_stocks)} 檔股票進行分析")
        
        # 顯示選中的股票列表
        with st.expander("📋 查看選中的股票", expanded=False):
            for stock in selected_stocks:
                market_flag = "🇺🇸" if stock['market'] == 'US' else "🇹🇼"
                st.write(f"{market_flag} {stock['symbol']} - {stock['name']}")
        
        # 分析選項
        col_opt1, col_opt2 = st.columns(2)
        
        with col_opt1:
            enable_debate = st.checkbox(
                "🗣️ 啟用多代理人辯論",
                value=True,
                help="啟用多代理人辯論可獲得更全面的分析，但會耗費較多時間"
            )
        
        with col_opt2:
            save_results = st.checkbox(
                "💾 儲存分析結果",
                value=True,
                help="將分析結果儲存到資料庫中"
            )
        
        # 開始分析按鈕
        if st.button("🚀 開始AI分析", use_container_width=True, type="primary"):
            analyze_selected_portfolio(selected_tickers, enable_debate, save_results)
    else:
        st.info("請選擇要分析的股票")
    
    # 顯示分析結果
    if 'portfolio_ai_results' in st.session_state:
        st.markdown("---")
        st.markdown("### 🤖 AI分析結果")
        display_portfolio_ai_results()


def analyze_selected_portfolio(tickers, enable_debate=True, save_results=True):
    """分析選定的持股組合"""
    if not tickers:
        st.error("沒有選擇任何股票")
        return
    
    # 初始化狀態管理器
    portfolio_status = portfolio_analysis_status
    portfolio_status.start_portfolio_analysis(tickers)
    
    # 創建狀態顯示區域
    status_container = st.empty()
    
    try:
        # 初始化數據獲取器和分析器
        fetcher = MultiMarketDataFetcher()
        analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=enable_debate, status_manager=portfolio_status)
        
        results = {}
        
        # 分析每一檔股票
        for i, ticker in enumerate(tickers):
            # 更新狀態
            portfolio_status.start_stock_analysis(ticker, i)
            
            # 在狀態容器中顯示進度
            with status_container.container():
                portfolio_status.display_portfolio_status()
            
            try:
                # 獲取股票數據
                stock_data = fetcher.get_stock_data(ticker)
                
                if stock_data and 'error' not in stock_data:
                    # 執行AI分析
                    analysis_result = analyzer.analyze_stock_comprehensive(stock_data, include_debate=enable_debate)
                    
                    # 儲存結果
                    results[ticker] = {
                        'stock_data': stock_data,
                        'analysis': analysis_result,
                        'status': 'success'
                    }
                    
                    # 儲存到資料庫
                    if save_results:
                        db = portfolio_db
                        market = 'TW' if '.TW' in ticker else 'US'
                        db.save_analysis_result(
                            ticker, market, 'portfolio',
                            json.dumps(analysis_result, ensure_ascii=False, cls=DateTimeEncoder)
                        )
                    
                else:
                    results[ticker] = {
                        'error': f"無法獲取 {ticker} 的數據",
                        'status': 'error'
                    }
                
                # 完成單一股票分析
                portfolio_status.complete_stock_analysis(ticker, results[ticker])
                
            except Exception as e:
                logging.error(f"分析 {ticker} 時發生錯誤: {e}")
                results[ticker] = {
                    'error': str(e),
                    'status': 'error'
                }
        
        # 完成所有分析
        portfolio_status.finish_analysis(True)
        
        # 儲存結果到session state
        st.session_state['portfolio_ai_results'] = results
        st.session_state['portfolio_ai_summary'] = generate_portfolio_ai_summary(results)
        
        # 清除狀態顯示
        status_container.empty()
        
        st.success(f"🎉 完成 {len(tickers)} 檔股票的AI分析！")
        st.rerun()
        
    except Exception as e:
        portfolio_status.finish_analysis(False)
        status_container.empty()
        st.error(f"分析過程中發生錯誤: {e}")
        logging.error(f"持股組合分析錯誤: {e}")


def generate_portfolio_ai_summary(results):
    """生成投資組合AI分析摘要"""
    if not results:
        return {}
    
    total_stocks = len(results)
    successful_analyses = len([r for r in results.values() if r.get('status') == 'success'])
    failed_analyses = total_stocks - successful_analyses
    
    # 統計建議分布
    recommendations = {}
    risk_levels = {}
    
    for ticker, result in results.items():
        if result.get('status') == 'success' and 'analysis' in result:
            analysis = result['analysis']
            
            # 提取風險等級
            if 'risk_assessment' in analysis:
                risk = analysis['risk_assessment'].get('overall_risk_level', 'Unknown')
                risk_levels[risk] = risk_levels.get(risk, 0) + 1
    
    return {
        'total_stocks': total_stocks,
        'successful_analyses': successful_analyses,
        'failed_analyses': failed_analyses,
        'recommendations': recommendations,
        'risk_levels': risk_levels,
        'analysis_timestamp': datetime.now().isoformat()
    }


def display_portfolio_ai_results():
    """顯示投資組合AI分析結果"""
    if 'portfolio_ai_results' not in st.session_state:
        return
    
    results = st.session_state['portfolio_ai_results']
    summary = st.session_state.get('portfolio_ai_summary', {})
    
    # 顯示摘要
    if summary:
        st.markdown("#### 📊 分析摘要")
        
        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
        
        with col_sum1:
            st.metric("總股票數", summary['total_stocks'])
        
        with col_sum2:
            st.metric("成功分析", summary['successful_analyses'])
        
        with col_sum3:
            st.metric("分析失敗", summary['failed_analyses'])
        
        with col_sum4:
            success_rate = (summary['successful_analyses'] / summary['total_stocks']) * 100
            st.metric("成功率", f"{success_rate:.1f}%")
    
    # 顯示詳細結果
    st.markdown("#### 📋 詳細分析結果")
    
    for ticker, result in results.items():
        with st.expander(f"📈 {ticker} - 詳細分析", expanded=False):
            if result.get('status') == 'success':
                display_single_stock_ai_analysis(ticker, result)
            else:
                st.error(f"❌ 分析失敗: {result.get('error', '未知錯誤')}")


def display_single_stock_ai_analysis(ticker, result):
    """顯示單一股票的AI分析結果"""
    if 'analysis' not in result:
        st.error("沒有分析結果")
        return
    
    analysis = result['analysis']
    
    # 基本資訊
    if 'stock_data' in result:
        stock_data = result['stock_data']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("當前價格", f"${stock_data.get('current_price', 'N/A')}")
        
        with col2:
            market_cap = stock_data.get('market_cap')
            if market_cap:
                st.metric("市值", f"${market_cap/1e9:.1f}B")
            else:
                st.metric("市值", "N/A")
        
        with col3:
            pe_ratio = stock_data.get('pe_ratio')
            if pe_ratio:
                st.metric("本益比", f"{pe_ratio:.1f}")
            else:
                st.metric("本益比", "N/A")
        
        with col4:
            dividend_yield = stock_data.get('dividend_yield')
            if dividend_yield:
                st.metric("股息率", f"{dividend_yield:.2%}")
            else:
                st.metric("股息率", "N/A")
    
    # 多代理人辯論結果
    if 'multi_agent_debate' in analysis:
        debate = analysis['multi_agent_debate']
        
        st.markdown("##### 🗣️ 多代理人辯論結果")
        
        if 'voting_results' in debate:
            voting = debate['voting_results']
            
            # 顯示投票結果
            col_vote1, col_vote2, col_vote3 = st.columns(3)
            
            with col_vote1:
                st.metric("買入票數", voting.get('buy_votes', 0))
            
            with col_vote2:
                st.metric("持有票數", voting.get('hold_votes', 0))
            
            with col_vote3:
                st.metric("賣出票數", voting.get('sell_votes', 0))
            
            # 顯示共識度
            consensus_level = voting.get('consensus_level', 0)
            st.progress(consensus_level, text=f"專家共識度: {consensus_level:.1%}")
        
        # 專家最終立場摘要
        if 'voting_results' in debate and 'agent_final_positions' in debate['voting_results']:
            st.markdown("**🎯 專家最終立場:**")
            
            positions = debate['voting_results']['agent_final_positions']
            
            # 按建議分類顯示
            buy_agents = []
            hold_agents = []
            sell_agents = []
            
            for agent_name, position in positions.items():
                agent_display = agent_name.replace('派', '').replace('投資師', '').replace('分析師', '').replace('專家', '')
                rec = position.get('recommendation', 'UNKNOWN')
                confidence = position.get('confidence', 0)
                
                agent_info = f"**{agent_display}** (信心度: {confidence}/10)"
                
                if rec == 'BUY':
                    buy_agents.append(agent_info)
                elif rec == 'HOLD':
                    hold_agents.append(agent_info)
                elif rec == 'SELL':
                    sell_agents.append(agent_info)
            
            col_buy, col_hold, col_sell = st.columns(3)
            
            with col_buy:
                if buy_agents:
                    st.markdown("🟢 **看好買入:**")
                    for agent in buy_agents:
                        st.write(f"• {agent}")
                else:
                    st.markdown("🟢 **看好買入:** 無")
            
            with col_hold:
                if hold_agents:
                    st.markdown("🟡 **建議持有:**")
                    for agent in hold_agents:
                        st.write(f"• {agent}")
                else:
                    st.markdown("🟡 **建議持有:** 無")
            
            with col_sell:
                if sell_agents:
                    st.markdown("🔴 **建議賣出:**")
                    for agent in sell_agents:
                        st.write(f"• {agent}")
                else:
                    st.markdown("� **建議賣出:** 無")
        
        # 辯論重點整理
        if 'final_consensus' in debate:
            consensus = debate['final_consensus']
            
            st.markdown("##### 📝 辯論重點整理")
            
            final_rec = consensus.get('final_recommendation', 'UNKNOWN')
            avg_confidence = consensus.get('average_confidence', 0)
            
            # 最終建議
            if final_rec == 'BUY':
                st.success(f"🟢 **專家團隊最終建議: 買入** (平均信心度: {avg_confidence:.1f}/10)")
            elif final_rec == 'SELL':
                st.error(f"🔴 **專家團隊最終建議: 賣出** (平均信心度: {avg_confidence:.1f}/10)")
            elif final_rec == 'HOLD':
                st.warning(f"🟡 **專家團隊最終建議: 持有** (平均信心度: {avg_confidence:.1f}/10)")
            else:
                st.info(f"⚪ **專家團隊最終建議: {final_rec}** (平均信心度: {avg_confidence:.1f}/10)")
            
            # 主要支持論點
            if 'supporting_points' in consensus and consensus['supporting_points']:
                st.markdown("**✅ 主要支持論點:**")
                for point in consensus['supporting_points'][:3]:  # 只顯示前3個
                    st.write(f"• {point}")
            
            # 主要反對論點
            if 'opposing_points' in consensus and consensus['opposing_points']:
                st.markdown("**⚠️ 主要反對論點:**")
                for point in consensus['opposing_points'][:3]:  # 只顯示前3個
                    st.write(f"• {point}")
        
        # 辯論摘要
        if 'debate_summary' in debate and debate['debate_summary']:
            st.markdown("**📋 辯論過程摘要:**")
            st.write(debate['debate_summary'])
        
        # 詳細代理人分析過程
        if 'agents_analysis' in debate:
            with st.expander("🔍 各專家詳細分析過程", expanded=False):
                agents_data = debate['agents_analysis']
                
                for agent_name, agent_info in agents_data.items():
                    agent_display = agent_name.replace('派', '').replace('投資師', '').replace('分析師', '').replace('專家', '')
                    
                    st.markdown(f"#### 📊 {agent_display}")
                    
                    # 初期獨立分析
                    st.markdown("**🔍 初期獨立分析:**")
                    initial_rec = agent_info.get('initial_recommendation', 'N/A')
                    initial_conf = agent_info.get('initial_confidence', 0)
                    initial_reason = agent_info.get('initial_reasoning', '無資料')
                    
                    if initial_rec == 'BUY':
                        st.success(f"買入建議 (信心度: {initial_conf}/10)")
                    elif initial_rec == 'SELL':
                        st.error(f"賣出建議 (信心度: {initial_conf}/10)")
                    elif initial_rec == 'HOLD':
                        st.warning(f"持有建議 (信心度: {initial_conf}/10)")
                    else:
                        st.info(f"{initial_rec} (信心度: {initial_conf}/10)")
                    
                    st.write(f"**理由:** {initial_reason}")
                    
                    # 辯論後最終立場
                    st.markdown("**🗣️ 辯論後最終立場:**")
                    final_rec = agent_info.get('recommendation', 'N/A')
                    final_conf = agent_info.get('confidence', 0)
                    final_reason = agent_info.get('reasoning', '無資料')
                    
                    if final_rec == 'BUY':
                        st.success(f"買入建議 (信心度: {final_conf}/10)")
                    elif final_rec == 'SELL':
                        st.error(f"賣出建議 (信心度: {final_conf}/10)")
                    elif final_rec == 'HOLD':
                        st.warning(f"持有建議 (信心度: {final_conf}/10)")
                    else:
                        st.info(f"{final_rec} (信心度: {final_conf}/10)")
                    
                    st.write(f"**理由:** {final_reason}")
                    
                    # 立場變化分析
                    if initial_rec != final_rec or abs(initial_conf - final_conf) > 1:
                        st.markdown("**🔄 立場變化:**")
                        
                        if initial_rec != final_rec:
                            st.write(f"• 建議從 **{initial_rec}** 改為 **{final_rec}**")
                        
                        conf_change = final_conf - initial_conf
                        if conf_change > 0:
                            st.write(f"• 信心度提升 {conf_change:.1f} 分")
                        elif conf_change < 0:
                            st.write(f"• 信心度下降 {abs(conf_change):.1f} 分")
                        
                        # 變化原因
                        change_reason = agent_info.get('position_change_reason', '')
                        if change_reason:
                            st.write(f"• **變化原因:** {change_reason}")
                    else:
                        st.markdown("**✅ 立場保持一致**")
                    
                    st.markdown("---")
        
        # 分析要點
        if 'key_points' in rec:
            st.markdown("**關鍵分析要點:**")
            for point in rec['key_points']:
                st.write(f"• {point}")


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
    """執行 AI 分析 - 參考持股分析模式"""
    try:
        if 'top_stocks' not in st.session_state:
            st.error("請先完成價值投資篩選")
            return
        
        top_stocks = st.session_state['top_stocks']
        max_analysis = st.session_state.get('max_analysis', 5)
        enable_debate = st.session_state.get('enable_debate', False)
        
        # 準備要分析的股票列表
        stock_list = top_stocks.head(max_analysis).to_dict('records')
        tickers = [stock['ticker'] for stock in stock_list]
        
        # 初始化狀態管理器
        analysis_status_manager = analysis_status
        analysis_status_manager.start_portfolio_analysis(tickers)
        
        # 創建狀態顯示區域
        status_container = st.empty()
        
        # 初始化分析器
        analyzer = EnhancedStockAnalyzerWithDebate(
            enable_debate=enable_debate,
            status_manager=analysis_status_manager
        )
        
        results = {}
        
        # 分析每一檔股票
        for i, stock_data in enumerate(stock_list):
            ticker = stock_data['ticker']
            
            # 更新狀態
            analysis_status_manager.start_stock_analysis(ticker, i)
            
            # 在狀態容器中顯示進度
            with status_container.container():
                analysis_status_manager.display_portfolio_status()
            
            try:
                # 執行AI分析
                analysis_result = analyzer.analyze_stock_comprehensive(
                    stock_data, 
                    include_debate=enable_debate
                )
                
                # 儲存結果
                results[ticker] = {
                    'stock_data': stock_data,
                    'analysis': analysis_result,
                    'status': 'success'
                }
                
            except Exception as e:
                logging.error(f"分析 {ticker} 時發生錯誤: {e}")
                results[ticker] = {
                    'error': str(e),
                    'status': 'error'
                }
            
            # 完成單一股票分析
            analysis_status_manager.complete_stock_analysis(ticker, results[ticker])
        
        # 完成所有分析
        analysis_status_manager.finish_analysis(True)
        
        # 儲存結果到session state
        st.session_state['ai_analysis_results'] = results
        st.session_state['ai_analysis_summary'] = generate_ai_analysis_summary(results)
        
        # 清除狀態顯示
        status_container.empty()
        
        st.success(f"🎉 完成 {len(tickers)} 檔股票的AI分析！")
        st.rerun()
        
    except Exception as e:
        if 'analysis_status_manager' in locals():
            analysis_status_manager.finish_analysis(False)
        if 'status_container' in locals():
            status_container.empty()
        st.error(f"AI 分析過程發生錯誤: {e}")
        logging.error(f"AI分析錯誤: {e}")


def generate_ai_analysis_summary(results):
    """生成AI分析摘要"""
    if not results:
        return {}
    
    total_stocks = len(results)
    successful_analyses = len([r for r in results.values() if r.get('status') == 'success'])
    failed_analyses = total_stocks - successful_analyses
    
    return {
        'total_stocks': total_stocks,
        'successful_analyses': successful_analyses,
        'failed_analyses': failed_analyses
    }


def display_ai_analysis_results():
    """顯示AI分析結果 - 參考持股分析格式"""
    if 'ai_analysis_results' not in st.session_state:
        return
    
    results = st.session_state['ai_analysis_results']
    summary = st.session_state.get('ai_analysis_summary', {})
    
    # 顯示摘要
    if summary:
        st.markdown("#### 📊 分析摘要")
        
        col_sum1, col_sum2, col_sum3, col_sum4 = st.columns(4)
        
        with col_sum1:
            st.metric("總股票數", summary['total_stocks'])
        
        with col_sum2:
            st.metric("成功分析", summary['successful_analyses'])
        
        with col_sum3:
            st.metric("分析失敗", summary['failed_analyses'])
        
        with col_sum4:
            success_rate = (summary['successful_analyses'] / summary['total_stocks']) * 100 if summary['total_stocks'] > 0 else 0
            st.metric("成功率", f"{success_rate:.1f}%")
    
    # 顯示詳細結果
    st.markdown("#### 📋 詳細分析結果")
    
    for ticker, result in results.items():
        with st.expander(f"📈 {ticker} - 詳細分析", expanded=False):
            if result.get('status') == 'success':
                display_single_stock_screening_analysis(ticker, result)
            else:
                st.error(f"❌ 分析失敗: {result.get('error', '未知錯誤')}")


def display_single_stock_screening_analysis(ticker, result):
    """顯示單一股票的篩選AI分析結果"""
    if 'analysis' not in result:
        st.error("沒有分析結果")
        return
    
    analysis = result['analysis']
    stock_data = result.get('stock_data', {})
    
    # 基本資訊
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        current_price = stock_data.get('current_price') or stock_data.get('price')
        if current_price:
            st.metric("當前價格", f"${current_price:.2f}")
        else:
            st.metric("當前價格", "N/A")
    
    with col2:
        market_cap = stock_data.get('market_cap')
        if market_cap and market_cap > 0:
            st.metric("市值", f"${market_cap/1e9:.1f}B")
        else:
            st.metric("市值", "N/A")
    
    with col3:
        pe_ratio = stock_data.get('pe_ratio') or stock_data.get('trailing_pe')
        if pe_ratio:
            st.metric("本益比", f"{pe_ratio:.1f}")
        else:
            st.metric("本益比", "N/A")
    
    with col4:
        value_score = stock_data.get('value_score')
        if value_score:
            st.metric("價值評分", f"{value_score:.1f}")
        else:
            st.metric("價值評分", "N/A")
    
    # 價值投資指標
    st.markdown("##### 📊 價值投資指標")
    col_val1, col_val2, col_val3, col_val4 = st.columns(4)
    
    with col_val1:
        pb_ratio = stock_data.get('pb_ratio') or stock_data.get('price_to_book')
        if pb_ratio:
            st.metric("市淨率", f"{pb_ratio:.2f}")
        else:
            st.metric("市淨率", "N/A")
    
    with col_val2:
        dividend_yield = stock_data.get('dividend_yield')
        if dividend_yield:
            st.metric("股息率", f"{dividend_yield:.2%}")
        else:
            st.metric("股息率", "N/A")
    
    with col_val3:
        debt_ratio = stock_data.get('debt_to_equity')
        if debt_ratio:
            st.metric("負債比", f"{debt_ratio:.2f}")
        else:
            st.metric("負債比", "N/A")
    
    with col_val4:
        roe = stock_data.get('roe') or stock_data.get('return_on_equity')
        if roe:
            st.metric("股東權益報酬率", f"{roe:.2%}")
        else:
            st.metric("股東權益報酬率", "N/A")
    
    # 多代理人辯論結果（如果有）
    if 'multi_agent_debate' in analysis:
        debate = analysis['multi_agent_debate']
        
        st.markdown("##### 🗣️ 多代理人辯論結果")
        
        if 'voting_results' in debate:
            voting = debate['voting_results']
            
            # 顯示投票結果
            st.markdown("**📊 代理人投票結果:**")
            for position, details in voting.items():
                agents = details.get('agents', [])
                if agents:
                    agent_names = ', '.join(agents)
                    st.markdown(f"- **{position}**: {agent_names}")
        
        if 'final_consensus' in debate:
            consensus = debate['final_consensus']
            st.markdown("**� 最終共識:**")
            st.markdown(f"- **推薦行動**: {consensus.get('final_recommendation', 'N/A')}")
            
            if 'reasoning' in consensus:
                st.markdown("**💭 推理過程:**")
                st.markdown(consensus['reasoning'])
    
    # 綜合建議（如果沒有多代理人結果）
    # 風險評估
    if 'risk_assessment' in analysis:
        risk = analysis['risk_assessment']
        st.markdown("##### ⚠️ 風險評估")
        
        risk_level = risk.get('overall_risk_level', '未知')
        if risk_level:
            if risk_level.upper() in ['LOW', '低']:
                st.success(f"🟢 **風險等級**: {risk_level}")
            elif risk_level.upper() in ['HIGH', '高']:
                st.error(f"🔴 **風險等級**: {risk_level}")
            elif risk_level.upper() in ['MEDIUM', '中']:
                st.warning(f"🟡 **風險等級**: {risk_level}")
            else:
                st.info(f"ℹ️ **風險等級**: {risk_level}")
        
        if 'key_risks' in risk:
            st.markdown("**主要風險:**")
            for risk_item in risk['key_risks']:
                st.markdown(f"- {risk_item}")
    
    # 新聞分析（如果有）
    if 'news_sentiment' in analysis:
        news_sentiment = analysis['news_sentiment']
        
        st.markdown("##### 📰 新聞情緒分析")
        
        if 'overall_sentiment' in news_sentiment:
            sentiment = news_sentiment['overall_sentiment']
            if sentiment > 0.1:
                st.success(f"🟢 **整體情緒**: 正面 ({sentiment:.2f})")
            elif sentiment < -0.1:
                st.error(f"🔴 **整體情緒**: 負面 ({sentiment:.2f})")
            else:
                st.warning(f"🟡 **整體情緒**: 中性 ({sentiment:.2f})")
        
        if 'news_summary' in news_sentiment:
            st.markdown("**📝 新聞摘要:**")
            st.markdown(news_sentiment['news_summary'])



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
### 第{int(row.get('value_rank', i+1))}名. {row['ticker']} - {row.get('company_name') or row.get('name', row['ticker'])}
- **行業**: {row.get('sector', '未分類')}
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
        # display_technical_analysis_tab(analysis_result)  # 已簡化，在單一股票分析中顯示
        st.info("技術分析已整合到個別股票分析中")
    
    with tab4:
        # display_chip_analysis_tab(analysis_result)  # 已簡化，在單一股票分析中顯示
        st.info("籌碼分析已整合到個別股票分析中")


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
        # create_radar_chart(analysis_result)  # 已簡化
        st.info("評分雷達圖功能已簡化，詳細評分請查看個別分析結果")


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


def show_screening_results():
    """顯示篩選結果（簡化版）"""
    if 'top_stocks' not in st.session_state:
        st.warning("尚未進行股票篩選")
        return
    
    st.success(f"✅ 篩選完成！找到 {len(st.session_state['top_stocks'])} 支優質股票")
    
    # 快速統計
    df = st.session_state['top_stocks']
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        avg_score = df['value_score'].mean() if 'value_score' in df.columns else 0
        st.metric("平均評分", f"{avg_score:.1f}")
    
    with col2:
        avg_pe = df['trailing_pe'].mean() if 'trailing_pe' in df.columns else 0
        st.metric("平均本益比", f"{avg_pe:.1f}")
    
    with col3:
        avg_pb = df['price_to_book'].mean() if 'price_to_book' in df.columns else 0
        st.metric("平均市淨率", f"{avg_pb:.2f}")
    
    with col4:
        count_low_debt = (df['debt_to_equity'] < 0.5).sum() if 'debt_to_equity' in df.columns else 0
        st.metric("低負債股票", f"{count_low_debt} 支")


def analyze_my_portfolio(tickers: list, enable_debate: bool = False):
    """分析個人持股"""
    try:
        analyzer = EnhancedStockAnalyzerWithDebate(enable_debate=enable_debate)
        
        # 將股票代碼轉換為分析器需要的格式
        stock_list = []
        for ticker in tickers:
            stock_data = {
                'ticker': ticker,
                'symbol': ticker,
                'company_name': ticker  # 簡化版，實際應該獲取公司名稱
            }
            stock_list.append(stock_data)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # 執行分析
        analysis_results = []
        for i, stock_data in enumerate(stock_list):
            ticker = stock_data['ticker']
            
            if enable_debate:
                status_text.text(f"正在進行多代理人辯論分析 {ticker}... ({i+1}/{len(stock_list)})")
            else:
                status_text.text(f"正在分析 {ticker}... ({i+1}/{len(stock_list)})")
            
            result = analyzer.analyze_stock_comprehensive(stock_data, include_debate=enable_debate)
            analysis_results.append(result)
            
            progress_bar.progress((i + 1) / len(stock_list))
        
        st.session_state['portfolio_analysis_results'] = analysis_results
        
        status_text.text("持股分析完成！")
        success_count = len([r for r in analysis_results if 'error' not in r])
        st.success(f"成功完成 {success_count}/{len(tickers)} 支股票的分析")
        
        # 生成持股摘要
        generate_portfolio_summary(analysis_results, enable_debate)
        
    except Exception as e:
        st.error(f"分析過程中發生錯誤: {e}")


def generate_portfolio_summary(analysis_results: list, enable_debate: bool):
    """生成持股分析摘要"""
    try:
        successful_results = [r for r in analysis_results if 'error' not in r]
        
        if not successful_results:
            return
        
        # 統計投資建議分佈
        recommendations = {}
        scores = []
        risk_levels = {}
        
        for result in successful_results:
            # 投資建議統計
            rec = result.get('investment_recommendation', 'HOLD')
            recommendations[rec] = recommendations.get(rec, 0) + 1
            
            # 評分統計
            score = result.get('overall_score', 0)
            scores.append(score)
            
            # 風險統計
            risk = result.get('risk_assessment', {}).get('overall_risk', 'MEDIUM')
            risk_levels[risk] = risk_levels.get(risk, 0) + 1
        
        # 將摘要存儲到 session state
        portfolio_summary = {
            'total_stocks': len(analysis_results),
            'successful_analysis': len(successful_results),
            'average_score': sum(scores) / len(scores) if scores else 0,
            'recommendations': recommendations,
            'risk_distribution': risk_levels,
            'enable_debate': enable_debate
        }
        
        st.session_state['portfolio_summary'] = portfolio_summary
        
    except Exception as e:
        st.error(f"生成摘要時發生錯誤: {e}")


def display_portfolio_analysis_results():
    """顯示持股分析結果"""
    if 'portfolio_analysis_results' not in st.session_state:
        st.warning("尚未進行持股分析")
        return
    
    results = st.session_state['portfolio_analysis_results']
    
    # 顯示摘要
    if 'portfolio_summary' in st.session_state:
        summary = st.session_state['portfolio_summary']
        
        st.markdown("#### 📊 持股分析摘要")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("總持股", f"{summary['total_stocks']} 支")
        
        with col2:
            success_rate = summary['successful_analysis'] / summary['total_stocks'] * 100 if summary['total_stocks'] > 0 else 0
            st.metric("分析成功率", f"{success_rate:.0f}%")
        
        with col3:
            st.metric("平均評分", f"{summary['average_score']:.1f}")
        
        with col4:
            enable_debate = summary.get('enable_debate', False)
            debate_status = "已啟用" if enable_debate else "未啟用"
            st.metric("多代理人辯論", debate_status)
        
        # 投資建議分佈
        if summary['recommendations']:
            st.markdown("#### 📈 投資建議分佈")
            rec_col1, rec_col2, rec_col3 = st.columns(3)
            
            with rec_col1:
                buy_count = summary['recommendations'].get('BUY', 0)
                st.metric("建議買入", f"{buy_count} 支", delta=f"{buy_count/summary['total_stocks']*100:.0f}%")
            
            with rec_col2:
                hold_count = summary['recommendations'].get('HOLD', 0)
                st.metric("建議持有", f"{hold_count} 支", delta=f"{hold_count/summary['total_stocks']*100:.0f}%")
            
            with rec_col3:
                sell_count = summary['recommendations'].get('SELL', 0)
                st.metric("建議賣出", f"{sell_count} 支", delta=f"{sell_count/summary['total_stocks']*100:.0f}%")
    
    # 顯示個別股票詳細分析
    st.markdown("#### 🔍 個別股票分析")
    
    for result in results:
        if 'error' not in result:
            ticker = result['ticker']
            overall_score = result.get('overall_score', 0)
            recommendation = result.get('investment_recommendation', '無建議')
            
            # 根據評分設定顏色
            if overall_score >= 70:
                score_color = "🟢"
            elif overall_score >= 50:
                score_color = "🟡"
            else:
                score_color = "🔴"
            
            with st.expander(f"{score_color} {ticker} (評分: {overall_score})"):
                # 使用與原有 AI 分析結果相同的顯示邏輯
                display_single_stock_analysis(result)
        else:
            ticker = result.get('ticker', '未知代碼')
            st.error(f"❌ {ticker}: {result.get('error', '未知錯誤')}")


def display_single_stock_analysis(result):
    """顯示單一股票的分析結果"""
    ticker = result['ticker']
    company_name = result.get('company_name') or result.get('name', result.get('ticker', '未知股票'))
    overall_score = result.get('overall_score', 0)
    recommendation = result.get('investment_recommendation', '無建議')
    
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
    
    # 多代理人辯論結果（如果有）
    if 'multi_agent_debate' in result:
        debate_result = result['multi_agent_debate']
        if 'error' not in debate_result:
            st.markdown("---")
            st.markdown("#### 🤖 多代理人投資辯論分析")
            
            # 最終共識
            final_consensus = debate_result.get('final_consensus', {})
            debate_col1, debate_col2, debate_col3 = st.columns(3)
            
            with debate_col1:
                st.metric(
                    "專家最終建議",
                    final_consensus.get('final_recommendation', 'N/A')
                )
            
            with debate_col2:
                consensus_level = final_consensus.get('consensus_level', 0)
                st.metric(
                    "專家共識度",
                    f"{consensus_level:.1%}"
                )
            
            with debate_col3:
                avg_confidence = final_consensus.get('average_confidence', 0)
                st.metric(
                    "平均信心度",
                    f"{avg_confidence:.1f}/10"
                )
            
            # 辯論摘要
            debate_summary = debate_result.get('debate_summary', '')
            if debate_summary:
                st.markdown("**📝 辯論摘要:**")
                st.write(debate_summary)
    
    # 風險評估
    risk = result.get('risk_assessment', {})
    if risk:
        st.markdown("##### ⚠️ 風險評估")
        st.write(f"- 整體風險: {risk.get('overall_risk', 'N/A')}")
        st.write(f"- 波動風險: {risk.get('volatility_risk', 'N/A')}")
        st.write(f"- 估值風險: {risk.get('valuation_risk', 'N/A')}")


if __name__ == "__main__":
    main()
