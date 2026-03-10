@echo off
REM ============================================
REM BAMSec Transcript Downloader - Setup Script
REM ============================================
REM Run this ONCE to install everything needed.
REM After this, you only need to use run.bat
REM ============================================

echo Setting up BAMSec Transcript Downloader...
echo.

echo 1/3  Installing Python packages...
python -m pip install -r requirements.txt

echo.
echo 2/3  Installing browser for automation...
python -m playwright install chromium

echo.
echo 3/3  Checking for .env file...
if not exist .env (
    echo.
    echo IMPORTANT: You need to create a .env file with your BAMSec login.
    echo.
    echo Create a file called '.env' in this folder with:
    echo.
    echo   BAMSEC_EMAIL=your_email@example.com
    echo   BAMSEC_PASSWORD=your_password
    echo.
    echo Replace with your actual BAMSec email and password.
) else (
    echo .env file found!
)

echo.
echo Setup complete! You can now use run.bat to download transcripts.
echo.
echo Example:  run.bat RH
pause
