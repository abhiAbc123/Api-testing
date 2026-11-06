@echo off
chcp 65001 > nul
echo [api-test-E10] Finding and stopping process on port 12138
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :12138 ^| findstr LISTENING') do (
    echo [api-test-E10] Stopping PID=%%a
    taskkill /PID %%a /F
)
echo [api-test-E10] Finished
