@echo off
chcp 65001 >nul
title ĐẨY TOOL LÊN GITHUB ACTIONS CLOUD

echo ======================================================================
echo          HƯỚNG DẪN ĐẨY TOOL LÊN GITHUB ACTIONS (FREE 100%%)
echo ======================================================================
echo.
echo Bước 1: Mở trình duyệt vào trang: https://github.com/new
echo Bước 2: Đặt tên Repository (ví dụ: gemini-tool)
echo Bước 3: CHỌN "Private" (để bảo mật mã nguồn và link của bạn)
echo Bước 4: Bấm nút xanh "Create repository"
echo.
echo Sau khi tạo xong, GitHub sẽ cho bạn 1 đường link dạng:
echo https://github.com/<tên_tài_khoản>/<tên_repo>.git
echo.
echo ======================================================================
set /p REPO_URL="Dán đường link GitHub của bạn vào đây rồi bấm Enter: "

if "%REPO_URL%"=="" (
    echo Bạn chưa nhập link GitHub! Vui lòng thử lại.
    pause
    exit /b
)

echo.
echo [1/4] Đang khởi tạo Git...
git init
git branch -M main

echo [2/4] Đang thêm các file cần thiết...
git add .

echo [3/4] Đang đóng gói bản cập nhật...
git commit -m "Khoi tao Jio Gemini Scanner cho GitHub Actions"

echo [4/4] Đang kết nối và đẩy lên Cloud GitHub...
git remote remove origin 2>nul
git remote add origin %REPO_URL%
git push -u origin main --force

echo.
echo ======================================================================
echo THÀNH CÔNG! TOOL ĐÃ ĐƯỢC ĐƯA LÊN GITHUB ACTIONS CLOUD!
echo.
echo Để bật chạy trên GitHub:
echo 1. Vào repository của bạn trên GitHub
echo 2. Bấm vào tab "Actions" ở trên cùng
echo 3. Chọn "Jio Gemini Scanner Cloud 24/7" -> Bấm "Run workflow"
echo 4. Kể từ giờ, GitHub sẽ tự động chạy định kỳ và cập nhật link mới cho bạn!
echo ======================================================================
pause
