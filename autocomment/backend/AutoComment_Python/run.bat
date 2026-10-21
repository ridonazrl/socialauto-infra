@echo off
cd /d "%~dp0"

echo [*] Mengaktifkan virtual environment...
call venv\Scripts\activate.bat

echo [*] Menjalankan AutoComment...
python auto.py

pause
