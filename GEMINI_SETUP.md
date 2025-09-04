# Gemini 新聞搜尋功能設置說明

## 功能概述

本系統整合了 Gemini 2.5 Flash 的 grounding 功能作為新聞搜尋的備用方案。當 yfinance 找不到股票新聞時，系統會自動使用 Gemini 進行 Google 搜尋來獲取相關新聞。

## 設置步驟

### 1. 獲取 Gemini API Key

1. 訪問 [Google AI Studio](https://aistudio.google.com/)
2. 登入您的 Google 帳戶
3. 點擊「Get API Key」
4. 創建新的 API Key 或使用現有的
5. 複製 API Key

### 2. 設置環境變數

#### Windows (PowerShell)
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

#### Windows (命令提示字元)
```cmd
set GEMINI_API_KEY=your_api_key_here
```

#### Linux/macOS
```bash
export GEMINI_API_KEY="your_api_key_here"
```

### 3. 永久設置（推薦）

在項目根目錄創建 `.env` 文件：
```
GEMINI_API_KEY=your_api_key_here
```

## 功能特性

### 自動備用搜尋
- 當 yfinance 無法找到新聞時自動觸發
- 支援台股和美股的新聞搜尋
- 使用 Google 搜尋獲取最新資訊

### 智能查詢構建
- 根據股票類型（台股/美股）調整搜尋策略
- 自動添加相關關鍵字（財報、營收、股價等）
- 支援時間範圍限制

### 多語言支援
- 台股：使用中文關鍵字搜尋
- 美股：使用英文關鍵字搜尋
- 自動處理公司名稱映射

## 使用方法

### 在代碼中使用
```python
from src.enhanced_analyzer import EnhancedStockAnalyzerWithDebate

# 創建分析器
analyzer = EnhancedStockAnalyzerWithDebate()

# 獲取新聞（自動使用 Gemini 備用搜尋）
news = analyzer.get_stock_news("2330.TW", days=7)
```

### 測試整合
```bash
python test_gemini_integration.py
```

## 注意事項

1. **API 配額**: Gemini API 有使用限制，請注意配額管理
2. **網路需求**: Gemini grounding 需要穩定的網路連接
3. **回應時間**: Gemini 搜尋可能比 yfinance 慢一些
4. **成本**: Gemini API 可能產生費用，請檢查 Google 的定價

## 故障排除

### 常見問題

**Q: 顯示 "Gemini 服務不可用"**
A: 檢查 GEMINI_API_KEY 是否正確設置

**Q: 搜尋結果為空**
A: 可能是網路問題或 API 配額用盡

**Q: 錯誤："API key not found"**
A: 確保環境變數正確設置並重啟應用程式

### 調試模式

設置詳細日誌：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 效能優化

1. **快取結果**: 系統會快取新聞結果避免重複請求
2. **優雅降級**: 如果 Gemini 失敗，會返回空結果而不是錯誤
3. **超時處理**: 設置合理的請求超時時間

## 支援的股票市場

- ✅ 台灣證券交易所 (.TW)
- ✅ 美國股票市場 (NYSE, NASDAQ)
- ✅ 其他主要國際市場

## 更新日誌

- v1.0.0: 初始 Gemini grounding 整合
- 支援自動備用搜尋
- 多語言新聞搜尋
- 智能查詢構建
