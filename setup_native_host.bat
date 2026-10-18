@echo off
chcp 65001 >nul
echo ============================================
echo   SETUP NATIVE HOST - GEMINI TOOL
echo ============================================
echo.
echo 1. Mo Chrome
echo 2. Vao: chrome://extensions
echo 3. Tim "Gemini Auto Activator"
echo 4. Copy cai ID dai (vi du: abcdefghijklmnopabcdefghijklmnop)
echo.
set /p EXT_ID="Dan ID vao day roi bam Enter: "

if "%EXT_ID%"=="" (
    echo Khong co ID, thoat.
    pause
    exit /b 1
)

echo.
echo Dang cai dat native host voi ID: %EXT_ID%

set TOOL_DIR=%~dp0
set PYTHON=C:\Users\k5a3h\AppData\Local\Programs\Python\Python312\python.exe
set HOST_SCRIPT=%TOOL_DIR%gemini_native_host.py
set MANIFEST_PATH=%TOOL_DIR%gemini_native_host_manifest.json

REM Tao file manifest
(
echo {
echo   "name": "com.gemini.tool",
echo   "description": "Gemini Tool Native Host",
echo   "path": "%PYTHON:\=\\%",
echo   "type": "stdio",
echo   "args": ["%HOST_SCRIPT:\=\\%"],
echo   "allowed_origins": [
echo     "chrome-extension://%EXT_ID%/"
echo   ]
echo }
) > "%MANIFEST_PATH%"

REM Dang ky vao Windows Registry
reg add "HKCU\SOFTWARE\Google\Chrome\NativeMessagingHosts\com.gemini.tool" /ve /t REG_SZ /d "%MANIFEST_PATH%" /f >nul

echo.
echo ============================================
echo   XONG! Reload extension trong Chrome:
echo   chrome://extensions -> Reload
echo ============================================
pause
