@echo off
REM ============================================
REM BAMSec Transcript Downloader - Run Script
REM ============================================
REM Usage:
REM   run.bat RH        (downloads 8 transcripts for RH)
REM   run.bat AAPL      (downloads 8 transcripts for Apple)
REM   run.bat MSFT 4    (downloads 4 transcripts for Microsoft)
REM ============================================

if "%1"=="" (
    echo BAMSec Transcript Downloader
    echo.
    echo Usage:  run.bat TICKER [count]
    echo.
    echo Examples:
    echo   run.bat RH         Download 8 most recent transcripts for RH
    echo   run.bat AAPL       Download 8 most recent transcripts for Apple
    echo   run.bat MSFT 4     Download only 4 transcripts for Microsoft
    echo.
    pause
    exit /b
)

set TICKER=%1
set COUNT=%2
if "%COUNT%"=="" set COUNT=8

python main.py %TICKER% --count %COUNT%
pause
