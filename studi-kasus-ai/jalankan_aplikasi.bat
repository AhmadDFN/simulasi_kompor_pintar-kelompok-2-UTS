@echo off
title Kompor Pintar - Server Flask
chcp 65001 >nul
echo ============================================================
echo   Memulai Aplikasi Web Fuzzifikasi Kompor Pintar...
echo ============================================================
echo.

:: Pindah ke folder src (lokasi aplikasi_web.py dan solusi.py)
cd /d "%~dp0src"

:: Set PYTHONPATH agar Flask dapat menemukan modul solusi.py
set PYTHONPATH=.

echo [1/2] Menjalankan server Flask di http://127.0.0.1:5000 ...
echo [2/2] Browser akan terbuka otomatis dalam 3 detik.
echo.
echo Tekan CTRL+C di jendela ini untuk menghentikan server.
echo.

:: Buka browser setelah 3 detik (menggunakan proses terpisah)
start "" cmd /c "timeout /t 3 /nobreak >nul && start http://127.0.0.1:5000"

:: Jalankan Flask (blokir terminal ini selama server aktif)
"%~dp0.venv\Scripts\python.exe" aplikasi_web.py

pause
