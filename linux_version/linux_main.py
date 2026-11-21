# linux_main.py
import os
import threading
import time
import psutil
from watchdog.observers import Observer
import linux_monitor as monitor
import linux_alert as alert
import linux_config as config

class FastCreateHandler(monitor.FastCreateHandler):
    pass # Используем класс из monitor

if __name__ == "__main__":
    print("[ЗАПУСК] Скрипт запущен (Linux версия).")
    
    try:
        monitor.known_pids = {p.info['pid'] for p in psutil.process_iter(['pid'])}
    except Exception:
        monitor.known_pids = set()

    # 1. Мониторим ТОЛЬКО Рабочий стол (чтобы ловить папки с матом, но не жрать ОЗУ)
    observer = Observer()
    # Пробуем найти папку Рабочего стола (русскую или английскую)
    desktop_paths = [
        os.path.expanduser("~/Desktop"),
        os.path.expanduser("~/Рабочий стол")
    ]
    for path in desktop_paths:
        if os.path.exists(path):
            try:
                observer.schedule(monitor.FastCreateHandler(), path, recursive=True)
                print(f"[МОНИТОРИНГ ФАЙЛОВ] Слежу за: {path}")
            except Exception as e:
                print(f"[ОШИБКА] {e}")
    
    observer.start()

    # 2. Мониторим процессы (игры/ВПН)
    print("[МОНИТОРИНГ ПРОЦЕССОВ] Слежу за играми...")
    threading.Thread(target=monitor.check_running_processes, daemon=True).start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()