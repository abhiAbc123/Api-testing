@echo off
chcp 65001 > nul
echo [api-test-E10] Starting mitmdump, listening on port 12138
echo [api-test-E10] Press Ctrl+C to stop
where mitmdump >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    mitmdump -s "%~dp0capture_addon.py" --listen-port 12138
) else (
    python -c "import sys; from mitmproxy.tools.main import mitmdump; sys.exit(mitmdump())" -s "%~dp0capture_addon.py" --listen-port 12138
)
