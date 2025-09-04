"""
測試環境變數和 API Key 檢測
"""

import sys
import os
sys.path.append('.')

def test_env_loading():
    """測試環境變數載入"""
    print("🧪 測試環境變數載入...")
    
    try:
        from src.utils import load_env_variables
        
        env_vars = load_env_variables()
        print(f"載入的環境變數: {list(env_vars.keys())}")
        
        gemini_key = env_vars.get('gemini_api_key')
        if gemini_key:
            print(f"✅ 主要 API Key: {gemini_key[:8]}...")
        else:
            print("❌ 未找到主要 API Key")
        
        return bool(gemini_key)
        
    except Exception as e:
        print(f"❌ 環境變數載入失敗: {e}")
        return False

def test_key_manager():
    """測試 Key 管理器"""
    print("\n🔑 測試 Key 管理器...")
    
    try:
        from src.gemini_key_manager import get_gemini_keys_status, get_current_gemini_key
        
        # 測試狀態
        status = get_gemini_keys_status()
        print(f"總 Key 數: {status.get('total_keys', 0)}")
        
        # 測試獲取當前 Key
        current_key = get_current_gemini_key()
        if current_key:
            print(f"✅ 當前可用 Key: {current_key[:8]}...")
        else:
            print("❌ 無法獲取當前 Key")
        
        return bool(current_key)
        
    except Exception as e:
        print(f"❌ Key 管理器測試失敗: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_env():
    """直接測試 .env 檔案"""
    print("\n📄 直接測試 .env 檔案...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        # 檢查所有相關的環境變數
        keys_to_check = ['GEMINI_API_KEY'] + [f'GEMINI_API_KEY_{i}' for i in range(1, 6)]
        
        found_keys = []
        for key_name in keys_to_check:
            value = os.getenv(key_name)
            if value and value not in ['', 'your_gemini_api_key_here']:
                found_keys.append(key_name)
                print(f"✅ {key_name}: {value[:8]}...")
        
        if not found_keys:
            print("❌ 未找到任何有效的 API Key")
            
            # 檢查 .env 檔案是否存在
            if os.path.exists('.env'):
                print("✅ .env 檔案存在")
                with open('.env', 'r', encoding='utf-8') as f:
                    content = f.read()
                    print(f"檔案內容長度: {len(content)} 字元")
                    if 'GEMINI_API_KEY' in content:
                        print("✅ .env 檔案包含 GEMINI_API_KEY")
                    else:
                        print("❌ .env 檔案不包含 GEMINI_API_KEY")
            else:
                print("❌ .env 檔案不存在")
        
        return len(found_keys) > 0
        
    except Exception as e:
        print(f"❌ 直接 .env 測試失敗: {e}")
        return False

if __name__ == "__main__":
    print("🚀 API Key 檢測測試")
    print("=" * 50)
    
    # 測試直接 .env 載入
    direct_ok = test_direct_env()
    
    # 測試工具函數
    env_ok = test_env_loading()
    
    # 測試 Key 管理器
    manager_ok = test_key_manager()
    
    print(f"\n📊 測試結果:")
    print(f"直接 .env 檢測: {'✅ 通過' if direct_ok else '❌ 失敗'}")
    print(f"環境變數載入: {'✅ 通過' if env_ok else '❌ 失敗'}")
    print(f"Key 管理器: {'✅ 通過' if manager_ok else '❌ 失敗'}")
    
    if all([direct_ok, env_ok, manager_ok]):
        print("\n🎉 所有測試通過！API Key 檢測正常")
    else:
        print("\n⚠️ 部分測試失敗，請檢查配置")
    
    print("\n🏁 測試完成")
