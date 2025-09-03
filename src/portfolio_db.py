"""
持股資料庫模組 - 管理用戶的股票持倉
"""

import sqlite3
import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import pandas as pd


def format_currency(amount: float, currency: str) -> str:
    """格式化貨幣顯示"""
    if amount is None:
        return "N/A"
    
    if currency == "TWD":
        return f"NT${amount:,.0f}"
    elif currency == "USD":
        return f"${amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def get_currency_symbol(currency: str) -> str:
    """獲取貨幣符號"""
    currency_symbols = {
        "TWD": "NT$",
        "USD": "$"
    }
    return currency_symbols.get(currency, currency)


class PortfolioDatabase:
    """持股資料庫管理類"""
    
    def __init__(self, db_path: str = None):
        """初始化資料庫"""
        if db_path is None:
            # 使用絕對路徑確保數據持久化
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            db_path = os.path.join(project_root, "data", "portfolio.db")
        
        self.db_path = db_path
        
        # 確保資料夾存在
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # 初始化資料庫
        self._init_database()
    
    def _init_database(self):
        """初始化資料庫表格"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 檢查表格是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='holdings'")
            table_exists = cursor.fetchone()
            
            if not table_exists:
                # 創建持股表
                cursor.execute('''
                    CREATE TABLE holdings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        name TEXT NOT NULL,
                        market TEXT NOT NULL,
                        currency TEXT NOT NULL,
                        shares REAL,
                        avg_cost REAL,
                        notes TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        UNIQUE(symbol, market)
                    )
                ''')
                
                # 創建分析歷史記錄表
                cursor.execute('''
                    CREATE TABLE analysis_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        symbol TEXT NOT NULL,
                        market TEXT NOT NULL,
                        analysis_type TEXT NOT NULL,
                        analysis_result TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logging.info(f"資料庫初始化完成: {self.db_path}")
            else:
                # 檢查是否有currency欄位
                cursor.execute("PRAGMA table_info(holdings)")
                columns = [col[1] for col in cursor.fetchall()]
                
                if 'currency' not in columns:
                    # 添加currency欄位
                    cursor.execute('ALTER TABLE holdings ADD COLUMN currency TEXT')
                    
                    # 更新現有記錄的貨幣
                    cursor.execute('''
                        UPDATE holdings 
                        SET currency = CASE 
                            WHEN market = 'TW' THEN 'TWD' 
                            ELSE 'USD' 
                        END
                        WHERE currency IS NULL
                    ''')
                    
                    conn.commit()
                    logging.info("已更新資料庫結構，添加currency欄位")
                
                logging.info(f"使用現有資料庫: {self.db_path}")
    
    def add_stock(self, symbol: str, name: str, market: str = None, 
                  shares: float = None, avg_cost: float = None, notes: str = "") -> bool:
        """新增股票到持股，如果已存在則合併平均"""
        try:
            # 處理台股代號
            symbol = symbol.upper().strip()
            if market is None:
                # 自動判斷市場
                if symbol.isdigit() and len(symbol) == 4:
                    # 台股代號（四位數字）
                    symbol = f"{symbol}.TW"
                    market = "TW"
                elif '.TW' in symbol or '.TWO' in symbol:
                    market = "TW"
                else:
                    market = "US"
            elif market.upper() == "TW" and not symbol.endswith('.TW'):
                # 如果指定台股但沒有.TW後綴，自動添加
                if symbol.isdigit():
                    symbol = f"{symbol}.TW"
            
            market = market.upper()
            
            # 判斷貨幣
            currency = "TWD" if market == "TW" else "USD"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 檢查是否已存在
                cursor.execute('''
                    SELECT shares, avg_cost, currency FROM holdings 
                    WHERE symbol = ? AND market = ?
                ''', (symbol, market))
                
                existing = cursor.fetchone()
                
                if existing and existing[0] is not None and existing[1] is not None:
                    # 如果已存在且有數量和成本資料，進行平均計算
                    old_shares, old_cost, old_currency = existing
                    
                    if shares is not None and avg_cost is not None:
                        # 計算加權平均成本
                        total_shares = old_shares + shares
                        total_cost = (old_shares * old_cost) + (shares * avg_cost)
                        new_avg_cost = total_cost / total_shares
                        
                        cursor.execute('''
                            UPDATE holdings 
                            SET shares = ?, avg_cost = ?, currency = ?, notes = ?, updated_at = ?
                            WHERE symbol = ? AND market = ?
                        ''', (total_shares, new_avg_cost, currency, notes, datetime.now(), symbol, market))
                    else:
                        # 只更新備註和貨幣
                        cursor.execute('''
                            UPDATE holdings 
                            SET currency = ?, notes = ?, updated_at = ?
                            WHERE symbol = ? AND market = ?
                        ''', (currency, notes, datetime.now(), symbol, market))
                else:
                    # 新增或替換
                    cursor.execute('''
                        INSERT OR REPLACE INTO holdings 
                        (symbol, name, market, currency, shares, avg_cost, notes, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (symbol, name, market, currency, shares, avg_cost, notes, datetime.now()))
                
                conn.commit()
                return True
        except Exception as e:
            print(f"新增股票失敗: {e}")
            return False
    
    def remove_stock(self, symbol: str, market: str = None) -> bool:
        """從持股中移除股票"""
        try:
            # 處理台股代號
            symbol = symbol.upper().strip()
            if market is None:
                # 自動判斷市場
                if symbol.isdigit() and len(symbol) == 4:
                    symbol = f"{symbol}.TW"
                    market = "TW"
                elif '.TW' in symbol or '.TWO' in symbol:
                    market = "TW"
                else:
                    market = "US"
            elif market and market.upper() == "TW" and not symbol.endswith('.TW'):
                if symbol.isdigit():
                    symbol = f"{symbol}.TW"
            
            if market:
                market = market.upper()
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if market:
                    cursor.execute('''
                        DELETE FROM holdings WHERE symbol = ? AND market = ?
                    ''', (symbol, market))
                else:
                    # 如果沒有指定市場，刪除所有匹配的symbol
                    cursor.execute('''
                        DELETE FROM holdings WHERE symbol = ?
                    ''', (symbol,))
                
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            print(f"移除股票失敗: {e}")
            return False
    
    def batch_remove_stocks(self, symbols_and_markets: List[tuple]) -> Dict[str, bool]:
        """批量移除股票"""
        results = {}
        for symbol, market in symbols_and_markets:
            results[f"{symbol}_{market}"] = self.remove_stock(symbol, market)
        return results
    
    def update_holding(self, symbol: str, market: str, 
                      shares: float = None, avg_cost: float = None, notes: str = None) -> bool:
        """更新持股資訊"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 構建更新語句
                updates = []
                params = []
                
                if shares is not None:
                    updates.append("shares = ?")
                    params.append(shares)
                
                if avg_cost is not None:
                    updates.append("avg_cost = ?")
                    params.append(avg_cost)
                
                if notes is not None:
                    updates.append("notes = ?")
                    params.append(notes)
                
                # 更新貨幣（確保正確）
                currency = "TWD" if market.upper() == "TW" else "USD"
                updates.append("currency = ?")
                params.append(currency)
                
                if updates:
                    updates.append("updated_at = ?")
                    params.append(datetime.now())
                    
                    params.extend([symbol.upper(), market.upper()])
                    
                    sql = f"UPDATE holdings SET {', '.join(updates)} WHERE symbol = ? AND market = ?"
                    cursor.execute(sql, params)
                    conn.commit()
                    return cursor.rowcount > 0
                
                return False
        except Exception as e:
            print(f"更新持股失敗: {e}")
            return False
    
    def get_all_holdings(self) -> List[Dict]:
        """獲取所有持股"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT symbol, name, market, currency, shares, avg_cost, notes, created_at, updated_at
                    FROM holdings
                    ORDER BY market, symbol
                ''')
                
                columns = ['symbol', 'name', 'market', 'currency', 'shares', 'avg_cost', 'notes', 'created_at', 'updated_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"獲取持股失敗: {e}")
            return []
    
    def get_holdings_by_market(self, market: str) -> List[Dict]:
        """按市場獲取持股"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT symbol, name, market, currency, shares, avg_cost, notes, created_at, updated_at
                    FROM holdings
                    WHERE market = ?
                    ORDER BY symbol
                ''', (market.upper(),))
                
                columns = ['symbol', 'name', 'market', 'currency', 'shares', 'avg_cost', 'notes', 'created_at', 'updated_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"獲取持股失敗: {e}")
            return []
    
    def get_holding(self, symbol: str, market: str) -> Optional[Dict]:
        """獲取單一持股資訊"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT symbol, name, market, currency, shares, avg_cost, notes, created_at, updated_at
                    FROM holdings
                    WHERE symbol = ? AND market = ?
                ''', (symbol.upper(), market.upper()))
                
                row = cursor.fetchone()
                if row:
                    columns = ['symbol', 'name', 'market', 'currency', 'shares', 'avg_cost', 'notes', 'created_at', 'updated_at']
                    return dict(zip(columns, row))
                return None
        except Exception as e:
            print(f"獲取持股失敗: {e}")
            return None
    
    def save_analysis_result(self, symbol: str, market: str, 
                           analysis_type: str, analysis_result: str) -> bool:
        """保存分析結果"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO analysis_history 
                    (symbol, market, analysis_type, analysis_result, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (symbol.upper(), market.upper(), analysis_type, analysis_result, datetime.now()))
                conn.commit()
                return True
        except Exception as e:
            print(f"保存分析結果失敗: {e}")
            return False
    
    def get_analysis_history(self, symbol: str = None, market: str = None, 
                           analysis_type: str = None, limit: int = 10) -> List[Dict]:
        """獲取分析歷史記錄"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 構建查詢語句
                where_conditions = []
                params = []
                
                if symbol:
                    where_conditions.append("symbol = ?")
                    params.append(symbol.upper())
                
                if market:
                    where_conditions.append("market = ?")
                    params.append(market.upper())
                
                if analysis_type:
                    where_conditions.append("analysis_type = ?")
                    params.append(analysis_type)
                
                where_clause = ""
                if where_conditions:
                    where_clause = "WHERE " + " AND ".join(where_conditions)
                
                params.append(limit)
                
                sql = f'''
                    SELECT symbol, market, analysis_type, analysis_result, created_at
                    FROM analysis_history
                    {where_clause}
                    ORDER BY created_at DESC
                    LIMIT ?
                '''
                
                cursor.execute(sql, params)
                
                columns = ['symbol', 'market', 'analysis_type', 'analysis_result', 'created_at']
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
        except Exception as e:
            print(f"獲取分析歷史失敗: {e}")
            return []
    
    def get_portfolio_summary(self) -> Dict:
        """獲取投資組合摘要"""
        try:
            holdings = self.get_all_holdings()
            
            total_holdings = len(holdings)
            us_stocks = len([h for h in holdings if h['market'] == 'US'])
            tw_stocks = len([h for h in holdings if h['market'] == 'TW'])
            
            # 分別計算各貨幣的總投資金額
            total_cost_usd = 0
            total_cost_twd = 0
            holdings_with_cost = 0
            
            for holding in holdings:
                if holding['shares'] and holding['avg_cost'] and holding.get('currency'):
                    total_cost = holding['shares'] * holding['avg_cost']
                    
                    if holding['currency'] == 'USD':
                        total_cost_usd += total_cost
                    elif holding['currency'] == 'TWD':
                        total_cost_twd += total_cost
                    
                    holdings_with_cost += 1
            
            return {
                'total_holdings': total_holdings,
                'us_stocks': us_stocks,
                'tw_stocks': tw_stocks,
                'total_cost_usd': total_cost_usd if total_cost_usd > 0 else None,
                'total_cost_twd': total_cost_twd if total_cost_twd > 0 else None,
                'holdings_with_cost': holdings_with_cost,
                'last_updated': max([h['updated_at'] for h in holdings]) if holdings else None
            }
        except Exception as e:
            print(f"獲取投資組合摘要失敗: {e}")
            return {}


# 全域資料庫實例
portfolio_db = PortfolioDatabase()
