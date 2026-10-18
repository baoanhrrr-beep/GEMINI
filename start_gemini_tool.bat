@echo off
cd /d "c:\Users\k5a3h\Downloads\GEMINI jino Tool"

REM Tat process cu neu con chay
taskkill /f /im python.exe /fi "WINDOWTITLE eq extension_bridge_server*" >nul 2>&1

REM Khoi dong Bridge Server (an, khong hien cua so)
start "" /min cmd /c "python extension_bridge_server.py > bridge_server.log 2>&1"

REM Doi 2 giay cho server khoi dong xong
timeout /t 2 /nobreak >nul

REM Khoi dong Jio Scanner (an, khong hien cua so)
start "" /min cmd /c "python -u jio_gemini_share.py > scanner.log 2>&1"

exit
