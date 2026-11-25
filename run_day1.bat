@echo off
setlocal
cd /d "%~dp0"
echo Installing the project's recorded dependencies...
uv sync --locked
if errorlevel 1 goto failed
echo.
echo Creating a website briefing with Gemini...
uv run --locked python summarizer.py --output outputs\website_summary.md
if errorlevel 1 goto failed
echo.
echo Finished. Your briefing is in outputs\website_summary.md
pause
exit /b 0

:failed
echo.
echo The program stopped. Read the error above; your .env should contain GEMINI_API_KEY.
pause
exit /b 1
