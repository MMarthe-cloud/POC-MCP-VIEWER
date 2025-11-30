@echo off
echo Starting Mobile Mapping Viewer Backend...
echo.

cd backend

REM Check if .env exists in parent
if not exist ..\.env (
    echo ERROR: .env file not found in project root!
    echo Please create .env file with your GROQ_API_KEY
    pause
    exit /b 1
)

REM Install dependencies if needed
if not exist .venv (
    echo Installing dependencies with uv...
    uv sync
)

REM Start the server
echo Starting FastAPI server on http://localhost:8000
uv run uvicorn main:app --reload

