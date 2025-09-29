@echo off
chcp 65001 >nul
echo ====================================
echo 那斯達克權重前十股票分析系統
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
if exist ".venv\Scripts\pip.exe" (
    echo 使用虛擬環境安裝套件...
    ".venv\Scripts\pip.exe" install -r requirements.txt --quiet
    if errorlevel 1 (
        echo 警告: 部分套件安裝失敗，嘗試逐個安裝核心套件...
        ".venv\Scripts\pip.exe" install yfinance pandas requests beautifulsoup4 python-dotenv --quiet
        ".venv\Scripts\pip.exe" install google-generativeai streamlit plotly --quiet
    )
) else (
    echo 使用系統 Python 安裝套件...
    pip install -r requirements.txt --quiet
    if errorlevel 1 (
        echo 警告: 部分套件安裝失敗，嘗試逐個安裝核心套件...
        pip install yfinance pandas requests beautifulsoup4 python-dotenv --quiet
        pip install google-generativeai streamlit plotly --quiet
    )
)

echo.
echo 啟動網頁介面模式...
echo 網頁將在瀏覽器中自動開啟 (端口: 9898)...
echo 請稍候片刻...
echo.

REM 檢查虛擬環境是否存在
if exist ".venv\Scripts\streamlit.exe" (
    ".venv\Scripts\streamlit.exe" run streamlit_app.py --server.port 9898
) else (
    echo 使用系統 Python 環境啟動 Streamlit...
    streamlit run streamlit_app.py --server.port 9898
)

echo.
echo 程式執行完成
pause
