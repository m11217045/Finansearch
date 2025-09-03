"""
Gemini API Key 管理器 - 支援多個 API Key 輪換使用
避免單一 Key 的限制問題，支援多代理人獨立分配
"""

import os
import logging
import threading
from typing import List, Optional, Dict
from datetime import datetime, timedelta
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

logger = logging.getLogger(__name__)

class GeminiKeyManager:
    """Gemini API Key 管理器，支援多 Key 輪換和獨立分配"""
    
    def __init__(self):
        """初始化 API Key 管理器"""
        self.api_keys = self._load_api_keys()
        self.current_index = 0
        self.key_usage = {}  # 記錄每個 Key 的使用情況
        self.agent_key_mapping = {}  # 代理人與 Key 的映射
        self.lock = threading.Lock()
        
        # 初始化使用記錄
        for i, key in enumerate(self.api_keys):
            self.key_usage[i] = {
                'key': key,
                'request_count': 0,
                'last_used': None,
                'error_count': 0,
                'is_blocked': False,
                'block_until': None,
                'assigned_agents': []  # 分配給此 Key 的代理人列表
            }
        
        logger.info(f"✅ Gemini Key 管理器初始化完成，共載入 {len(self.api_keys)} 個 API Key")
    
    def _load_api_keys(self) -> List[str]:
        """從環境變數載入所有 API Key"""
        keys = []
        
        # 載入編號的 API Key
        for i in range(1, 6):  # GEMINI_API_KEY_1 到 GEMINI_API_KEY_5
            key_name = f"GEMINI_API_KEY_{i}"
            key_value = os.getenv(key_name)
            
            if key_value and key_value != "your_second_api_key_here" and key_value != "your_third_api_key_here" and key_value != "your_fourth_api_key_here" and key_value != "your_fifth_api_key_here":
                keys.append(key_value.strip('"'))
                logger.info(f"✅ 載入 {key_name}")
            else:
                logger.warning(f"⚠️ {key_name} 未設定或為預設值")
        
        # 如果沒有編號的 Key，嘗試載入原始的 GEMINI_API_KEY
        if not keys:
            original_key = os.getenv("GEMINI_API_KEY")
            if original_key and original_key not in ["your_gemini_api_key_here", ""]:
                keys.append(original_key.strip('"'))
                logger.info("✅ 載入原始 GEMINI_API_KEY")
        
        if not keys:
            logger.error("❌ 未找到任何有效的 Gemini API Key")
            logger.error("請在 .env 檔案中設置 GEMINI_API_KEY 或 GEMINI_API_KEY_1 到 GEMINI_API_KEY_5")
        
        return keys
    
    def get_current_key(self) -> Optional[str]:
        """獲取當前可用的 API Key"""
        if not self.api_keys:
            logger.error("❌ 沒有可用的 API Key")
            return None
        
        with self.lock:
            # 尋找可用的 Key
            attempts = 0
            while attempts < len(self.api_keys):
                current_usage = self.key_usage[self.current_index]
                
                # 檢查 Key 是否被暫時封鎖
                if current_usage['is_blocked'] and current_usage['block_until']:
                    if datetime.now() < current_usage['block_until']:
                        logger.warning(f"Key {self.current_index + 1} 仍在封鎖期內，切換到下一個")
                        self._switch_to_next_key()
                        attempts += 1
                        continue
                    else:
                        # 封鎖期已結束，解除封鎖
                        current_usage['is_blocked'] = False
                        current_usage['block_until'] = None
                        current_usage['error_count'] = 0
                        logger.info(f"Key {self.current_index + 1} 封鎖期結束，重新啟用")
                
                # 檢查是否需要切換（避免單一 Key 過度使用）
                if current_usage['request_count'] > 50:  # 每個 Key 最多連續使用 50 次
                    logger.info(f"Key {self.current_index + 1} 使用次數達到限制，切換到下一個")
                    self._switch_to_next_key()
                    attempts += 1
                    continue
                
                # 返回當前可用的 Key
                key = self.api_keys[self.current_index]
                current_usage['request_count'] += 1
                current_usage['last_used'] = datetime.now()
                
                logger.debug(f"使用 Key {self.current_index + 1}，已使用 {current_usage['request_count']} 次")
                return key
            
            # 如果所有 Key 都有問題，返回第一個
            logger.warning("所有 Key 都有問題，返回第一個 Key")
            return self.api_keys[0]
    
    def get_agent_key(self, agent_name: str) -> Optional[str]:
        """為特定代理人獲取專用的 API Key"""
        if not self.api_keys:
            logger.error("❌ 沒有可用的 API Key")
            return None
        
        with self.lock:
            # 檢查是否已經為此代理人分配了 Key
            if agent_name in self.agent_key_mapping:
                key_index = self.agent_key_mapping[agent_name]
                current_usage = self.key_usage[key_index]
                
                # 檢查分配的 Key 是否可用
                if not current_usage['is_blocked'] or (
                    current_usage['block_until'] and datetime.now() >= current_usage['block_until']
                ):
                    # 如果封鎖期已結束，解除封鎖
                    if current_usage['is_blocked'] and current_usage['block_until'] and datetime.now() >= current_usage['block_until']:
                        current_usage['is_blocked'] = False
                        current_usage['block_until'] = None
                        current_usage['error_count'] = 0
                        logger.info(f"代理人 {agent_name} 的 Key {key_index + 1} 封鎖期結束，重新啟用")
                    
                    # 更新使用記錄
                    current_usage['request_count'] += 1
                    current_usage['last_used'] = datetime.now()
                    
                    logger.debug(f"代理人 {agent_name} 使用專用 Key {key_index + 1}")
                    return self.api_keys[key_index]
                else:
                    logger.warning(f"代理人 {agent_name} 的專用 Key {key_index + 1} 被封鎖，重新分配")
                    # 移除舊的分配並重新分配
                    del self.agent_key_mapping[agent_name]
                    self.key_usage[key_index]['assigned_agents'].remove(agent_name)
            
            # 為代理人分配新的 Key（優先選擇負載較輕的）
            best_key_index = self._find_best_available_key()
            if best_key_index is not None:
                self.agent_key_mapping[agent_name] = best_key_index
                self.key_usage[best_key_index]['assigned_agents'].append(agent_name)
                
                # 更新使用記錄
                usage = self.key_usage[best_key_index]
                usage['request_count'] += 1
                usage['last_used'] = datetime.now()
                
                logger.info(f"為代理人 {agent_name} 分配專用 Key {best_key_index + 1}")
                return self.api_keys[best_key_index]
            
            # 如果沒有可用的專用 Key，使用輪換機制
            logger.warning(f"無法為代理人 {agent_name} 分配專用 Key，使用輪換機制")
            return self.get_current_key()
    
    def _find_best_available_key(self) -> Optional[int]:
        """找到最適合分配的 Key（負載最輕且未被封鎖）"""
        available_keys = []
        
        for i, usage in self.key_usage.items():
            # 跳過被封鎖的 Key
            if usage['is_blocked'] and usage['block_until'] and datetime.now() < usage['block_until']:
                continue
            
            # 計算負載分數（考慮分配的代理人數量和請求次數）
            load_score = len(usage['assigned_agents']) * 10 + usage['request_count']
            available_keys.append((i, load_score))
        
        if not available_keys:
            return None
        
        # 返回負載最輕的 Key 索引
        best_key = min(available_keys, key=lambda x: x[1])
        return best_key[0]
    
    def _switch_to_next_key(self):
        """切換到下一個 Key"""
        # 重置當前 Key 的使用計數
        self.key_usage[self.current_index]['request_count'] = 0
        
        # 切換到下一個
        self.current_index = (self.current_index + 1) % len(self.api_keys)
        logger.info(f"切換到 Key {self.current_index + 1}")
    
    def report_error(self, error_message: str = "", agent_name: str = None):
        """報告 Key 的錯誤（支援代理人特定報告）"""
        with self.lock:
            if agent_name and agent_name in self.agent_key_mapping:
                # 報告特定代理人的 Key 錯誤
                key_index = self.agent_key_mapping[agent_name]
                current_usage = self.key_usage[key_index]
                logger.warning(f"代理人 {agent_name} 的 Key {key_index + 1} 發生錯誤: {error_message}")
            else:
                # 報告當前輪換 Key 的錯誤
                key_index = self.current_index
                current_usage = self.key_usage[self.current_index]
                logger.warning(f"Key {self.current_index + 1} 發生錯誤: {error_message}")
            
            current_usage['error_count'] += 1
            
            # 如果錯誤次數太多，暫時封鎖這個 Key
            if current_usage['error_count'] >= 3:
                current_usage['is_blocked'] = True
                current_usage['block_until'] = datetime.now() + timedelta(minutes=10)
                logger.warning(f"Key {key_index + 1} 錯誤次數過多，暫時封鎖 10 分鐘")
                
                # 如果是代理人專用 Key，移除分配
                if agent_name and agent_name in self.agent_key_mapping:
                    del self.agent_key_mapping[agent_name]
                    current_usage['assigned_agents'].remove(agent_name)
                    logger.info(f"移除代理人 {agent_name} 的 Key 分配，將重新分配")
                elif not agent_name:
                    # 如果是輪換 Key，切換到下一個
                    self._switch_to_next_key()
    
    def report_success(self, agent_name: str = None):
        """報告 Key 的成功使用（支援代理人特定報告）"""
        with self.lock:
            if agent_name and agent_name in self.agent_key_mapping:
                # 報告特定代理人的 Key 成功
                key_index = self.agent_key_mapping[agent_name]
                self.key_usage[key_index]['error_count'] = 0
                logger.debug(f"代理人 {agent_name} 的 Key {key_index + 1} 使用成功")
            else:
                # 報告當前輪換 Key 的成功
                self.key_usage[self.current_index]['error_count'] = 0
                logger.debug(f"Key {self.current_index + 1} 使用成功")
    
    def force_switch_key(self):
        """強制切換到下一個 Key"""
        with self.lock:
            old_index = self.current_index
            self._switch_to_next_key()
            logger.info(f"強制切換 Key：{old_index + 1} -> {self.current_index + 1}")
    
    def get_status(self) -> dict:
        """獲取所有 Key 的使用狀態"""
        with self.lock:
            status = {
                'total_keys': len(self.api_keys),
                'current_key_index': self.current_index + 1,
                'keys_status': []
            }
            
            for i, usage in self.key_usage.items():
                key_status = {
                    'index': i + 1,
                    'request_count': usage['request_count'],
                    'error_count': usage['error_count'],
                    'is_blocked': usage['is_blocked'],
                    'last_used': usage['last_used'].strftime('%H:%M:%S') if usage['last_used'] else 'Never',
                    'is_current': i == self.current_index,
                    'assigned_agents': usage['assigned_agents'].copy(),  # 顯示分配的代理人
                    'load_score': len(usage['assigned_agents']) * 10 + usage['request_count']
                }
                status['keys_status'].append(key_status)
            
            # 添加代理人映射狀態
            status['agent_mappings'] = self.agent_key_mapping.copy()
            
            return status
    
    def reset_all_counters(self):
        """重置所有計數器"""
        with self.lock:
            for usage in self.key_usage.values():
                usage['request_count'] = 0
                usage['error_count'] = 0
                usage['is_blocked'] = False
                usage['block_until'] = None
            
            logger.info("✅ 重置所有 Key 的使用計數器")

# 全域 Key 管理器實例
_key_manager = None

def get_key_manager() -> GeminiKeyManager:
    """獲取全域 Key 管理器實例"""
    global _key_manager
    if _key_manager is None:
        _key_manager = GeminiKeyManager()
    return _key_manager

def get_current_gemini_key() -> Optional[str]:
    """獲取當前可用的 Gemini API Key"""
    return get_key_manager().get_current_key()

def get_agent_gemini_key(agent_name: str) -> Optional[str]:
    """為特定代理人獲取專用的 Gemini API Key"""
    return get_key_manager().get_agent_key(agent_name)

def report_gemini_error(error_message: str = "", agent_name: str = None):
    """報告 Gemini API 錯誤"""
    get_key_manager().report_error(error_message, agent_name)

def report_gemini_success(agent_name: str = None):
    """報告 Gemini API 成功"""
    get_key_manager().report_success(agent_name)

def force_switch_gemini_key():
    """強制切換 Gemini API Key"""
    get_key_manager().force_switch_key()

def get_gemini_keys_status() -> dict:
    """獲取所有 Gemini Key 的狀態"""
    return get_key_manager().get_status()

if __name__ == "__main__":
    # 測試 Key 管理器
    manager = GeminiKeyManager()
    
    print("📊 API Key 狀態:")
    status = manager.get_status()
    print(f"總 Key 數: {status['total_keys']}")
    print(f"當前 Key: {status['current_key_index']}")
    
    # 測試 Key 輪換
    print("\n🔄 測試 Key 輪換:")
    for i in range(3):
        key = manager.get_current_key()
        if key:
            print(f"第 {i+1} 次: Key {manager.current_index + 1}")
        
        # 模擬切換
        if i == 1:
            manager.force_switch_key()
    
    print("\n✅ Key 管理器測試完成")
