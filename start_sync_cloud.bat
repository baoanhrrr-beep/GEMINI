@echo off
chcp 65001 >nul
title ĐỒNG BỘ LINK TỪ 5 MÁY CHỦ CLOUD GITHUB VỀ MÁY TÍNH
cd /d "%~dp0"
python sync_cloud_links.py
pause
