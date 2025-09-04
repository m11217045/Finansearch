"""
分析狀態管理模組 - 用於顯示當前AI分析進度和Agent狀態
"""

import streamlit as st
from typing import Dict, Any, Optional
from datetime import datetime
import threading
import time


class AnalysisStatusManager:
    """分析狀態管理器"""
    
    def __init__(self):
        """初始化狀態管理器"""
        self.current_status = {
            'is_analyzing': False,
            'current_agent': None,
            'current_stock': None,
            'progress': 0,
            'step': None,
            'message': None,
            'start_time': None,
            'last_update': None
        }
        self.agents_info = {
            'market_analyst': '📊 市場分析師',
            'fundamentals_analyst': '📈 基本面分析師', 
            'news_analyst': '📰 新聞分析師',
            'social_media_analyst': '💬 社群媒體分析師',
            'bull_researcher': '🐂 多頭研究員',
            'bear_researcher': '🐻 空頭研究員',
            'risk_manager': '⚠️ 風險管理師',
            'research_manager': '🎯 研究經理',
            'conservative_debator': '🛡️ 保守派辯論者',
            'neutral_debator': '⚖️ 中性派辯論者',
            'aggressive_debator': '⚡ 激進派辯論者',
            'trader': '💼 交易員'
        }
    
    def start_analysis(self, stock_symbol: str, analysis_type: str = "single"):
        """開始分析"""
        self.current_status.update({
            'is_analyzing': True,
            'current_stock': stock_symbol,
            'progress': 0,
            'step': f'初始化{analysis_type}分析',
            'message': f'正在為 {stock_symbol} 準備分析環境...',
            'start_time': datetime.now(),
            'last_update': datetime.now()
        })
    
    def update_status(self, agent: str, step: str, message: str = None, progress: int = None):
        """更新分析狀態"""
        self.current_status.update({
            'current_agent': agent,
            'step': step,
            'message': message or f'{self.agents_info.get(agent, agent)} 正在進行 {step}',
            'last_update': datetime.now()
        })
        
        if progress is not None:
            self.current_status['progress'] = min(progress, 100)
    
    def finish_analysis(self, success: bool = True):
        """結束分析"""
        self.current_status.update({
            'is_analyzing': False,
            'current_agent': None,
            'progress': 100 if success else self.current_status['progress'],
            'step': '分析完成' if success else '分析中斷',
            'message': '所有分析已完成！' if success else '分析過程中發生錯誤'
        })
    
    def get_status(self) -> Dict[str, Any]:
        """獲取當前狀態"""
        return self.current_status.copy()
    
    def display_status_widget(self, container=None):
        """顯示狀態小工具"""
        if container is None:
            container = st
        
        if self.current_status['is_analyzing']:
            # 計算已經分析的時間
            if self.current_status['start_time']:
                elapsed_time = datetime.now() - self.current_status['start_time']
                elapsed_seconds = int(elapsed_time.total_seconds())
                elapsed_str = f"{elapsed_seconds // 60}分{elapsed_seconds % 60}秒"
            else:
                elapsed_str = "未知"
            
            # 顯示進度條
            progress_bar = container.progress(self.current_status['progress'] / 100)
            
            # 顯示當前狀態
            status_col1, status_col2 = container.columns([3, 1])
            
            with status_col1:
                if self.current_status['current_agent']:
                    agent_display = self.agents_info.get(
                        self.current_status['current_agent'], 
                        self.current_status['current_agent']
                    )
                    container.info(f"🤖 **當前Agent:** {agent_display}")
                
                if self.current_status['step']:
                    container.info(f"📋 **執行步驟:** {self.current_status['step']}")
                
                if self.current_status['message']:
                    container.info(f"💭 **狀態訊息:** {self.current_status['message']}")
            
            with status_col2:
                container.metric("⏱️ 已耗時", elapsed_str)
                container.metric("📊 進度", f"{self.current_status['progress']}%")
            
            return progress_bar
        
        return None
    
    def create_status_placeholder(self):
        """創建狀態顯示占位符"""
        return st.empty()


class MultiStockAnalysisStatus(AnalysisStatusManager):
    """多股票分析狀態管理器"""
    
    def __init__(self):
        super().__init__()
        self.portfolio_status = {
            'total_stocks': 0,
            'completed_stocks': 0,
            'current_stock_index': 0,
            'stock_list': [],
            'stock_results': {}
        }
    
    def start_portfolio_analysis(self, stock_list: list):
        """開始投資組合分析"""
        self.portfolio_status.update({
            'total_stocks': len(stock_list),
            'completed_stocks': 0,
            'current_stock_index': 0,
            'stock_list': stock_list,
            'stock_results': {}
        })
        
        self.start_analysis(
            f"投資組合 ({len(stock_list)} 檔股票)", 
            "portfolio"
        )
    
    def start_stock_analysis(self, stock_symbol: str, stock_index: int):
        """開始單一股票分析"""
        self.portfolio_status['current_stock_index'] = stock_index
        self.current_status.update({
            'current_stock': stock_symbol,
            'step': f'分析第 {stock_index + 1}/{self.portfolio_status["total_stocks"]} 檔股票',
            'message': f'正在分析 {stock_symbol}...',
            'progress': int((stock_index / self.portfolio_status['total_stocks']) * 100)
        })
    
    def complete_stock_analysis(self, stock_symbol: str, result: Dict):
        """完成單一股票分析"""
        self.portfolio_status['completed_stocks'] += 1
        self.portfolio_status['stock_results'][stock_symbol] = result
        
        progress = int((self.portfolio_status['completed_stocks'] / self.portfolio_status['total_stocks']) * 100)
        self.current_status['progress'] = progress
    
    def display_portfolio_status(self, container=None):
        """顯示投資組合分析狀態"""
        if container is None:
            container = st
        
        if self.current_status['is_analyzing']:
            # 顯示總體進度
            container.subheader("📊 投資組合分析進度")
            
            col1, col2, col3 = container.columns(3)
            with col1:
                container.metric("總股票數", self.portfolio_status['total_stocks'])
            with col2:
                container.metric("已完成", self.portfolio_status['completed_stocks'])
            with col3:
                container.metric("剩餘", 
                               self.portfolio_status['total_stocks'] - self.portfolio_status['completed_stocks'])
            
            # 顯示當前分析狀態
            self.display_status_widget(container)
            
            # 顯示股票清單進度
            if self.portfolio_status['stock_list']:
                container.subheader("📋 股票分析清單")
                
                for i, stock in enumerate(self.portfolio_status['stock_list']):
                    if i < self.portfolio_status['completed_stocks']:
                        container.success(f"✅ {stock} - 已完成")
                    elif i == self.portfolio_status['current_stock_index']:
                        container.info(f"🔄 {stock} - 分析中...")
                    else:
                        container.info(f"⏳ {stock} - 等待中")


# 全域狀態管理器實例
analysis_status = AnalysisStatusManager()
portfolio_analysis_status = MultiStockAnalysisStatus()
