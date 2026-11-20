# monitor.py
import os
import time
import psutil
from watchdog.events import FileSystemEventHandler
import config
from alert import trigger_alert

known_pids = set()

class FastCreateHandler(FileSystemEventHandler):
    def check_new_file(self, filepath):
        path_lower = filepath.lower()
        for ignored in config.IGNORE_PARTS:
            if ignored in path_lower: return

        filename_orig = os.path.basename(filepath)
        filename_lower = filename_orig.lower()

        for bad_root in config.BAD_WORDS_ROOTS:
            if bad_root in filename_lower:
                trigger_alert(
                    timer_key=f"__profanity__::{filepath}",
                    subject="Обнаружена ненормативная лексика в названии файла",
                    body_text=f"Нарушение: Мат\nСлово: {bad_root}\nФайл: {filepath}",
                    show_warning=True
                )
                return

        for keyword, program_name in config.KEYWORDS.items():
            if keyword in filename_lower:
                trigger_alert(
                    timer_key=f"{keyword}::{filepath}",
                    subject=f"Обнаружен {program_name}: {filename_orig}",
                    body_text=f"Программа: {program_name}\nФайл: {filepath}",
                    show_warning=True
                )
                break

    def on_created(self, event):
        self.check_new_file(event.src_path)

    def on_moved(self, event):
        self.check_new_file(event.dest_path)

def kill_process(proc):
    try:
        proc.kill()
        print(f"[УБИЙСТВО] Процесс {proc.name()} (PID: {proc.pid}) успешно завершен.")
    except Exception:
        pass

def check_running_processes():
    global known_pids
    while True:
        try:
            current_pids = set()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    current_pids.add(proc.info['pid'])
                    
                    if proc.info['pid'] not in known_pids:
                        proc_name = proc.info['name'].lower()
                        if not proc_name:
                            continue

                        if "svchost" in proc_name or "system" in proc_name or "python" in proc_name or "conhost" in proc_name:
                            continue

                        for keyword, program_name in config.KEYWORDS.items():
                            if keyword in proc_name:
                                kill_process(proc)
                                trigger_alert(
                                    timer_key=f"proc_{keyword}_{proc.info['pid']}",
                                    subject=f"Запущена и УБИТА программа: {program_name}",
                                    body_text=f"Обнаружен запуск процесса: {proc_name}\nПроцесс был принудительно завершен.",
                                    show_warning=True
                                )
                                break

                        for bad_root in config.BAD_WORDS_ROOTS:
                            if bad_root in proc_name:
                                kill_process(proc)
                                trigger_alert(
                                    timer_key=f"proc_prof_{proc.info['pid']}",
                                    subject="Обнаружен мат в названии процесса",
                                    body_text=f"Нарушение: Мат в процессе\nПроцесс: {proc_name}\nПроцесс был принудительно завершен.",
                                    show_warning=True
                                )
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            known_pids = current_pids
        except Exception:
            pass

        time.sleep(1)