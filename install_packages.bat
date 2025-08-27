@echo off
chcp 65001 >nul
echo ====================================
echo 手動安裝 Python 套件
echo ====================================
echo.

echo 正在安裝基礎套件...
echo.

echo [1/11] 安裝 requests...
pip install requests
if errorlevel 1 echo 警告: requests 安裝失敗

echo [2/11] 安裝 beautifulsoup4...
pip install beautifulsoup4
if errorlevel 1 echo 警告: beautifulsoup4 安裝失敗

echo [3/11] 安裝 python-dotenv...
pip install python-dotenv
if errorlevel 1 echo 警告: python-dotenv 安裝失敗

echo [4/11] 安裝 pandas (可能需要較長時間)...
pip install pandas
if errorlevel 1 echo 警告: pandas 安裝失敗

echo [5/11] 安裝 numpy...
pip install numpy
if errorlevel 1 echo 警告: numpy 安裝失敗

echo [6/11] 安裝 yfinance...
pip install yfinance
if errorlevel 1 echo 警告: yfinance 安裝失敗

echo [7/11] 安裝 openpyxl...
pip install openpyxl
if errorlevel 1 echo 警告: openpyxl 安裝失敗

echo [8/11] 安裝 google-generativeai...
pip install google-generativeai
if errorlevel 1 echo 警告: google-generativeai 安裝失敗

echo [9/11] 安裝 streamlit...
pip install streamlit
if errorlevel 1 echo 警告: streamlit 安裝失敗

echo [10/11] 安裝 plotly...
pip install plotly
if errorlevel 1 echo 警告: plotly 安裝失敗

echo [11/11] 安裝 lxml (可選)...
pip install lxml
if errorlevel 1 echo 注意: lxml 安裝失敗，但不影響主要功能

echo.
echo ====================================
echo 套件安裝完成！
echo ====================================
echo.
echo 接下來您可以：
echo 1. 執行 run.bat 啟動系統
echo 2. 執行 run.ps1 (PowerShell版本)
echo.
pause
