@echo off
chcp 65001 >nul
title Gemini Cloud Watchdog - Tu Dong Kiem Tra Va Fix Loi 24/7
cd /d "%~dp0"

:loop
cls
python cloud_watchdog.py
echo.
echo ======================================================================
echo   Da xong 1 vong kiem tra! Se tu dong chay lai sau 60 giay...
echo   (Nhan Ctrl+C de dung lai neu can)
echo ======================================================================
timeout /t 60 /nobreak >nul
goto loop
