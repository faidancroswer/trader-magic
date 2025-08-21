@echo off
:: Script to toggle between Binance Spot and Futures mode

:: Check if .env file exists
if not exist ".env" (
    echo Error: .env file not found!
    echo Please create .env file from .env.sample first.
    pause
    exit /b 1
)

:: Check current mode
findstr /C:"BINANCE_FUTURES_MODE=true" .env >nul
if %errorlevel% == 0 (
    set CURRENT_MODE=FUTURES
    set NEW_MODE=SPOT
    set NEW_VALUE=false
) else (
    set CURRENT_MODE=SPOT
    set NEW_MODE=FUTURES
    set NEW_VALUE=true
)

echo Current mode: %CURRENT_MODE%
echo Switching to: %NEW_MODE%

:: Update the .env file
powershell -Command "(gc .env) -replace 'BINANCE_FUTURES_MODE=.*', 'BINANCE_FUTURES_MODE=%NEW_VALUE%' | sc .env"

:: Also update the base URL for futures
if "%NEW_MODE%"=="FUTURES" (
    powershell -Command "(gc .env) -replace 'BINANCE_BASE_URL=.*', 'BINANCE_BASE_URL=https://fapi.binance.com' | sc .env"
    echo Updated Binance base URL to futures API
) else (
    powershell -Command "(gc .env) -replace 'BINANCE_BASE_URL=.*', 'BINANCE_BASE_URL=https://api.binance.com' | sc .env"
    echo Updated Binance base URL to spot API
)

echo ✅ Successfully switched to %NEW_MODE% mode!
echo Please restart the services for changes to take effect:
echo   docker-compose down
echo   docker-compose up -d

pause