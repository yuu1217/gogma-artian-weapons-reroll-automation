@echo off
cd /d "%~dp0\.."
echo Starting GUI...
uv run python main.py
echo GUI closed.
pause
