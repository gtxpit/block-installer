# linux_monitor.py
import os
import time
import psutil
from watchdog.events import FileSystemEventHandler
import linux_config as config
from linux_alert import trigger_alert

known_pids = set()

# === ПРОВЕРКА ФАЙЛОВ ===
class FastCreateHandler(FileSystemEventHandler):
    def check_new_file(self, filepath):
        path_lower = filepath.lower()
        
        # Пропускаем системные папки
        ignore_linux = ("/proc/", "/sys/", "/dev/", "/run/", "/tmp/", "/.cache/", "/.local/", "/venv/", "/__pycache__/")
        for ign in ignore_linux:
            if ign in path_lower: return

        filename_orig = os.path.basename(filepath)
        filename_lower = filename_orig.lower()

        for bad_root in config.BAD_WORDS_ROOTS:
            if bad_root in filename_lower:
                trigger_alert(
                    timer_key=f"__profanity__::{filepath}",
                    subject="Обнаружена ненормативная лексика",
                    body_text=f"Мат: {bad_root}\nФайл: {filepath}",
                    show_warning=True
                )
                return

        for keyword, program_name in config.KEYWORDS.items():
            if keyword in filename_lower:
                trigger_alert(
                    timer_key=f"{keyword}::{filepath}",
                    subject=f"Обнаружен {program_name}",
                    body_text=f"Программа: {program_name}\nФайл: {filepath}",
                    show_warning=True
                )
                break

    def on_created(self, event):
        self.check_new_file(event.src_path)

    def on_moved(self, event):
        self.check_new_file(event.dest_path)

# === ПРОВЕРКА ПРОЦЕССОВ ===
def kill_process(proc):
    try:
        proc.kill()
        print(f"[УБИЙСТВО] Процесс {proc.name()} (PID: {proc.pid}) завершен.")
    except Exception:
        pass

def check_running_processes():
    global known_pids
    while True:
        try:
            current_pids = set()
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'exe']):
                try:
                    current_pids.add(proc.info['pid'])
                    
                    if proc.info['pid'] not in known_pids:
                        proc_name = proc.info['name'].lower()
                        cmdline = proc.info.get('cmdline') or []
                        exe = proc.info.get('exe') or ""
                        cmd_str = " ".join(cmdline).lower()
                        
                        if not proc_name:
                            continue

                        if "systemd" in proc_name or "kernel" in proc_name or "python" in proc_name or "gnome" in proc_name or "bash" in proc_name or "sh" in proc_name:
                            continue

                        # 1. Поиск по играм/ВПН/нейросетям
                        for keyword, program_name in config.KEYWORDS.items():
                            if keyword in proc_name or keyword in cmd_str or keyword in exe.lower():
                                kill_process(proc)
                                trigger_alert(
                                    timer_key=f"proc_{keyword}_{proc.info['pid']}",
                                    subject=f"Запущена и УБИТА программа: {program_name}",
                                    body_text=f"Процесс: {proc_name}\nКоманда: {cmd_str}",
                                    show_warning=True
                                )
                                break
                        
                        # 2. Специально для Minecraft (Java)
                        if "java" in proc_name:
                            if "minecraft" in cmd_str or "tlauncher" in cmd_str:
                                kill_process(proc)
                                trigger_alert(
                                    timer_key=f"proc_java_minecraft_{proc.info['pid']}",
                                    subject="Запущен и УБИТ Minecraft",
                                    body_text=f"Процесс: java\nКоманда: {cmd_str}",
                                    show_warning=True
                                )
                                continue

                        # 3. Мат в названии процесса
                        for bad_root in config.BAD_WORDS_ROOTS:
                            if bad_root in proc_name:
                                kill_process(proc)
                                trigger_alert(
                                    timer_key=f"proc_prof_{proc.info['pid']}",
                                    subject="Мат в названии процесса",
                                    body_text=f"Процесс: {proc_name}",
                                    show_warning=True
                                )
                                break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass

            known_pids = current_pids
        except Exception:
            pass

        time.sleep(1)