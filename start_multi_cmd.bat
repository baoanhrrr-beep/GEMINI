@echo off
chcp 65001 >nul
title TRÌNH KHỞI CHẠY NHIỀU CỬA SỔ QUÉT JIO GEMINI

echo ======================================================================
echo           HỆ THỐNG KHỞI CHẠY ĐA CỬA SỔ (MULTI-CMD SCANNER)
echo ======================================================================
echo Máy của bạn: 8 Nhân / 12 Luồng - 16 GB RAM
echo Khuyến nghị: Chạy 4 đến 6 cửa sổ để đạt tốc độ bắt link tối đa
echo ======================================================================
echo.
echo [1] Mở 4 cửa sổ CMD (Khuyến nghị - Rất mượt, an toàn IP)
echo [2] Mở 6 cửa sổ CMD (Tốc độ cực nhanh)
echo [3] Mở 8 cửa sổ CMD (Mức tải tối đa)
echo [4] Tùy chỉnh số lượng cửa sổ
echo.
set /p choice="Nhập lựa chọn của bạn (1-4): "

set NUM_WINDOWS=4
if "%choice%"=="1" set NUM_WINDOWS=4
if "%choice%"=="2" set NUM_WINDOWS=6
if "%choice%"=="3" set NUM_WINDOWS=8
if "%choice%"=="4" (
    set /p NUM_WINDOWS="Nhập số cửa sổ bạn muốn mở (1-10): "
)

echo.
echo Đang khởi chạy %NUM_WINDOWS% cửa sổ CMD quét độc lập...
for /L %%i in (1,1,%NUM_WINDOWS%) do (
    start "Jio Gemini Scanner #%%i" cmd /k "cd /d %~dp0 && python jio_gemini_share.py"
    timeout /t 2 /nobreak >nul
)

echo.
echo ======================================================================
echo ĐÃ MỞ XONG %NUM_WINDOWS% CỬA SỔ!
echo Các cửa sổ sẽ tự động chia ngẫu nhiên 345 panel và thu thập link.
echo Bạn có thể thu nhỏ các cửa sổ xuống thanh taskbar để nó chạy ngầm.
echo ======================================================================
pause
