@echo off
title DISCORD BOT GEMINI CHECKER 24/7
color 0A
cd /d "%~dp0"
cls
echo ======================================================================
echo          BOT DISCORD CHECK LINK GEMINI PRO 18 THANG TU DONG
echo ======================================================================
echo.
echo  [*] Thu muc: %~dp0
echo  [*] Dang kiem tra Python va thu vien...
python -c "import discord, requests" 2>nul
if %errorlevel% neq 0 (
    echo  [!] Dang cai dat thu vien discord.py va requests...
    pip install discord.py requests
)
echo.
echo  [*] Dang khoi dong Bot (AUTOGEMINI#7307)...
echo  [*] Giu cua so nay de bot luon online hoat dong.
echo.
python discord_gemini_bot.py
echo.
echo ======================================================================
echo  [!] Bot da dung hoac gap su co.
echo ======================================================================
pause
