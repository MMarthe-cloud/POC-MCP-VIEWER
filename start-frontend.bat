@echo off
echo Starting Mobile Mapping Viewer Frontend...
echo.

cd frontend

REM Install dependencies if needed
if not exist node_modules (
    echo Installing dependencies...
    npm install
)

REM Start the dev server
echo Starting Vite dev server on http://localhost:5173
npm run dev

