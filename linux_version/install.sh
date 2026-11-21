#!/bin/bash

cd "$(dirname "$0")" || exit

echo "[1/4] Обновление системы и установка системных пакетов (скриншоты)..."
sudo apt update
sudo apt install -y python3 python3-pip python3-venv scrot pulseaudio-utils

echo "[2/4] Создание виртуального окружения..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

echo "[3/4] Установка Python-библиотек..."
source venv/bin/activate
sudo apt install -y gnome-screenshot scrot
pip install --upgrade pip
pip install pygame-ce keyboard watchdog Pillow psutil

echo "[4/4] Настройка прав и запуск..."
xhost +SI:localuser:root > /dev/null 2>&1

sudo XDG_RUNTIME_DIR=/run/user/$(id -u) venv/bin/python linux_main.py