@echo off
chcp 65001 >nul
title Установка Windows Audio Service

cd /d "%~dp0"

echo [1/3] Проверка Python...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python не найден. Скачиваем...
    powershell -Command "Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.12.4/python-3.12.4-amd64.exe' -OutFile 'py_installer.exe'"
    
    echo Установка Python (подожди)...
    start /wait py_installer.exe /quiet InstallAllUsers=0 PrependPath=1 Include_test=0
    
    del py_installer.exe
) else (
    echo Python уже установлен.
)

echo.
echo [2/3] Установка библиотек...
python -m pip install --upgrade pip --quiet
python -m pip install pygame-ce keyboard watchdog Pillow psutil --quiet --disable-pip-version-check

if %errorlevel% neq 0 (
    echo.
    echo [ОШИБКА] Не удалось установить библиотеки! Проверь интернет.
    pause
    exit
)

echo.
echo [3/3] Запуск скрипта в фоне...
python "main.py"
pause

echo.
echo Скрипт запущен в фоне. Нажми любую клавишу, чтобы закрыть это окно.
pause