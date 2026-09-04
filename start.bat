@echo off
cd /d "%~dp0"

start "Converter server" python run.py
timeout /t 2 >nul
start "" http://127.0.0.1:5000
