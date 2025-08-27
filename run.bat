@echo off
chcp 65001 >nul
echo ====================================
echo S^&P 500 價值投資分析系統
echo ====================================
echo.

REM 檢查 Python 是否安裝
python --version >nul 2>&1
if errorlevel 1 (
    echo 錯誤: 未找到 Python，請先安裝 Python 3.8 或以上版本
    pause
    exit /b 1
)

REM 檢查 .env 檔案是否存在
if not exist ".env" (
    echo 警告: 未找到 .env 檔案
    echo 正在從 .env.example 建立 .env 檔案...
    copy .env.example .env
    echo.
    echo 請編輯 .env 檔案並設定您的 Gemini API Key
    echo 按任意鍵繼續...
    pause >nul
)

echo 正在檢查套件安裝...
pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo 警告: 部分套件安裝失敗，嘗試逐個安裝核心套件...
    pip install yfinance pandas requests beautifulsoup4 python-dotenv --quiet
    pip install google-generativeai streamlit plotly --quiet
)

echo.
echo 啟動網頁介面模式...
echo 網頁將在瀏覽器中自動開啟 (端口: 5678)...
echo 請稍候片刻...
echo.

"D:/Finansearch/.venv/Scripts/streamlit.exe" run streamlit_app.py --server.port 5678

echo.
echo 程式執行完成
pause
