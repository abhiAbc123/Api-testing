@echo off
chcp 65001 > nul
echo [api-test-E10] Restarting mitmdump, listening on port 12138
call "%~dp0stop.bat"
echo [api-test-E10] Waiting 1 second before restarting
ping 127.0.0.1 -n 2 > nul
where mitmdump >nul 2>nul
if %ERRORLEVEL% EQU 0 (
    mitmdump -s "%~dp0capture_addon.py" --listen-port 12138
) else (
    python -c "import sys; from mitmproxy.tools.main import mitmdump; sys.exit(mitmdump())" -s "%~dp0capture_addon.py" --listen-port 12138
)
