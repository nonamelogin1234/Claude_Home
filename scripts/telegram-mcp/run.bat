@echo off
rem Kill any stale mcp-telegram master that might hold the lock
if exist "%USERPROFILE%\.mcp-telegram\daemon.lock" (
    set /p OLDPID=<"%USERPROFILE%\.mcp-telegram\daemon.lock"
    taskkill /PID %OLDPID% /F >nul 2>&1
    del "%USERPROFILE%\.mcp-telegram\daemon.lock" >nul 2>&1
    del "%USERPROFILE%\.mcp-telegram\daemon.sock" >nul 2>&1
)
"C:\Program Files\nodejs\node.exe" "C:\Users\no-na\Desktop\2027\Codex_Home\scripts\telegram-mcp\node_modules\@overpod\mcp-telegram\dist\index.js"
