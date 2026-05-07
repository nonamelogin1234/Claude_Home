@echo off
cd /d "%~dp0"
python iul_pyside6.py > launch_log.txt 2>&1
if errorlevel 1 (
    echo.
    echo Ошибка запуска. Смотри launch_log.txt
    echo Нажмите любую клавишу...
    pause >nul
)
