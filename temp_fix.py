def display_single_stock_screening_analysis(ticker, analysis, stock_data):
    """以類似MD檔案的格式顯示單一股票的篩選AI分析結果"""
    
    st.markdown(f"## 📈 {ticker} - 股票分析報告")
    
    analysis_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # 基本資訊
    company_name = stock_data.get('company_name') or stock_data.get('longName') or stock_data.get('shortName') or ticker
    current_price = stock_data.get('current_price') or stock_data.get('regularMarketPrice')
    sector = stock_data.get('sector', '未分類')
    industry = stock_data.get('industry', '未分類')
    
    st.markdown("### 📊 公司基本資訊")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**公司名稱**: {company_name}")
        st.markdown(f"**股票代號**: {ticker}")
        st.markdown(f"**行業**: {sector}")
        st.markdown(f"**子行業**: {industry}")
    
    with col2:
        if current_price:
            st.markdown(f"**當前股價**: ${current_price:.2f}")
        market_cap = stock_data.get('market_cap')
        if market_cap and market_cap > 0:
            st.markdown(f"**市值**: ${market_cap/1e9:.1f}B")
        pe_ratio = stock_data.get('pe_ratio') or stock_data.get('trailing_pe')
        if pe_ratio:
            st.markdown(f"**本益比**: {pe_ratio:.1f}")
    
    # 財務指標表格
    st.markdown("### 📊 關鍵財務指標")
    
    metrics_data = []
    
    # 估值指標
    pe_ratio = stock_data.get('pe_ratio') or stock_data.get('trailing_pe')
    pb_ratio = stock_data.get('pb_ratio') or stock_data.get('price_to_book')
    peg_ratio = stock_data.get('peg_ratio')
    ev_ebitda = stock_data.get('ev_ebitda')
    
    if pe_ratio:
        metrics_data.append(["本益比 (P/E)", f"{pe_ratio:.2f}"])
    if pb_ratio:
        metrics_data.append(["市淨率 (P/B)", f"{pb_ratio:.2f}"])
    if peg_ratio:
        metrics_data.append(["PEG 比率", f"{peg_ratio:.2f}"])
    if ev_ebitda:
        metrics_data.append(["EV/EBITDA", f"{ev_ebitda:.2f}"])
    
    # 獲利能力指標
    profit_margin = stock_data.get('profit_margin')
    roe = stock_data.get('roe') or stock_data.get('return_on_equity')
    roa = stock_data.get('roa') or stock_data.get('return_on_assets')
    
    if profit_margin:
        metrics_data.append(["利潤率", f"{profit_margin:.2%}"])
    if roe:
        metrics_data.append(["股東權益報酬率 (ROE)", f"{roe:.2%}"])
    if roa:
        metrics_data.append(["資產報酬率 (ROA)", f"{roa:.2%}"])
    
    # 財務健康指標
    debt_ratio = stock_data.get('debt_to_equity')
    current_ratio = stock_data.get('current_ratio')
    dividend_yield = stock_data.get('dividend_yield')
    
    if debt_ratio:
        metrics_data.append(["負債權益比", f"{debt_ratio:.2f}"])
    if current_ratio:
        metrics_data.append(["流動比率", f"{current_ratio:.2f}"])
    if dividend_yield:
        metrics_data.append(["股息率", f"{dividend_yield:.2%}"])
    
    if metrics_data:
        df_metrics = pd.DataFrame(metrics_data, columns=["指標", "數值"])
        st.table(df_metrics)
    
    # 專家分析展開區塊
    if 'agents_analysis' in analysis:
        agents = analysis['agents_analysis']
        
        # 基本面分析師
        if 'fundamental_analyst' in agents:
            with st.expander("📊 基本面分析師觀點", expanded=False):
                fundamental = agents['fundamental_analyst']
                if 'analysis' in fundamental:
                    st.markdown("**分析結果:**")
                    st.markdown(fundamental['analysis'])
                if 'recommendation' in fundamental:
                    st.markdown(f"**建議**: {fundamental['recommendation']}")
                if 'confidence' in fundamental:
                    st.markdown(f"**信心度**: {fundamental['confidence']}/10")
        
        # 技術分析師
        if 'technical_analyst' in agents:
            with st.expander("📈 技術分析師觀點", expanded=False):
                technical = agents['technical_analyst']
                if 'analysis' in technical:
                    st.markdown("**分析結果:**")
                    st.markdown(technical['analysis'])
                if 'recommendation' in technical:
                    st.markdown(f"**建議**: {technical['recommendation']}")
                if 'confidence' in technical:
                    st.markdown(f"**信心度**: {technical['confidence']}/10")
        
        # 風險評估師
        if 'risk_analyst' in agents:
            with st.expander("⚠️ 風險評估師觀點", expanded=False):
                risk = agents['risk_analyst']
                if 'analysis' in risk:
                    st.markdown("**分析結果:**")
                    st.markdown(risk['analysis'])
                if 'recommendation' in risk:
                    st.markdown(f"**建議**: {risk['recommendation']}")
                if 'confidence' in risk:
                    st.markdown(f"**信心度**: {risk['confidence']}/10")
    
    # 投票結果與共識
    if 'multi_agent_debate' in analysis:
        debate = analysis['multi_agent_debate']
        
        st.markdown("### 🗳️ 專家投票結果")
        
        if 'voting_results' in debate:
            voting = debate['voting_results']
            
            # 顯示投票統計
            final_votes = voting.get('final_votes', {})
            if final_votes:
                vote_data = []
                for position, count in final_votes.items():
                    if count > 0:
                        vote_data.append([position, count])
                
                if vote_data:
                    df_votes = pd.DataFrame(vote_data, columns=["立場", "票數"])
                    st.table(df_votes)
            
            # 顯示各專家最終立場
            agent_positions = voting.get('agent_final_positions', {})
            if agent_positions:
                st.markdown("**各專家最終立場:**")
                position_data = []
                for agent_name, position in agent_positions.items():
                    recommendation = position.get('recommendation', 'HOLD')
                    confidence = position.get('confidence', 5)
                    position_data.append([agent_name, recommendation, f"{confidence}/10"])
                
                if position_data:
                    df_positions = pd.DataFrame(position_data, columns=["專家", "建議", "信心度"])
                    st.table(df_positions)
            
            # 顯示共識程度
            consensus_level = voting.get('consensus_level', 0)
            st.markdown(f"**共識程度**: {consensus_level:.1%}")
        
        # 最終共識
        if 'final_consensus' in debate:
            consensus = debate['final_consensus']
            st.markdown("### 🎯 最終共識")
            
            final_recommendation = consensus.get('final_recommendation', 'N/A')
            if final_recommendation.upper() == 'BUY':
                st.success(f"🟢 **最終建議**: {final_recommendation}")
            elif final_recommendation.upper() == 'SELL':
                st.error(f"🔴 **最終建議**: {final_recommendation}")
            elif final_recommendation.upper() == 'HOLD':
                st.warning(f"🟡 **最終建議**: {final_recommendation}")
            else:
                st.info(f"ℹ️ **最終建議**: {final_recommendation}")
            
            if 'reasoning' in consensus:
                st.markdown("**推理過程:**")
                st.markdown(consensus['reasoning'])
    
    # 風險評估
    if 'risk_assessment' in analysis:
        risk = analysis['risk_assessment']
        st.markdown("### ⚠️ 風險評估")
        
        risk_level = risk.get('overall_risk_level', '未知')
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
    
    # 新聞情緒分析
    if 'news_sentiment' in analysis:
        news_sentiment = analysis['news_sentiment']
        
        st.markdown("### 📰 新聞情緒分析")
        
        overall_sentiment = news_sentiment.get('overall_sentiment')
        if overall_sentiment is not None:
            if overall_sentiment > 0.1:
                st.success(f"🟢 **整體情緒**: 正面 ({overall_sentiment:.2f})")
            elif overall_sentiment < -0.1:
                st.error(f"🔴 **整體情緒**: 負面 ({overall_sentiment:.2f})")
            else:
                st.warning(f"🟡 **整體情緒**: 中性 ({overall_sentiment:.2f})")
        
        if 'news_summary' in news_sentiment:
            st.markdown("**新聞摘要:**")
            st.markdown(news_sentiment['news_summary'])
    
    # 生成並提供下載 MD 檔案
    try:
        analyzer = st.session_state.enhanced_analyzer
        md_content = analyzer._generate_agents_analysis_markdown(ticker, analysis, stock_data)
        
        st.markdown("### 📄 下載報告")
        st.download_button(
            label="📥 下載詳細MD報告",
            data=md_content,
            file_name=f"agents_analysis_{ticker}_{analysis_date.replace(':', '').replace('-', '').replace(' ', '_')}.md",
            mime="text/markdown",
            use_container_width=True
        )
    except Exception as e:
        st.warning(f"無法生成專家分析報告: {e}")
