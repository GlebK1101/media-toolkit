# src/main.py
import tkinter as tk
from tkinter import ttk
import threading

# Импорты утилит
from utils.theme import AppTheme
from utils.ffmpeg_utils import check_ffmpeg
from utils.updater import update_yt_dlp

# Импорты вкладок
from tabs.downloader_tab import DownloaderTab
from tabs.converter_tab import ConverterTab
from tabs.compressor_tab import CompressorTab
from tabs.editor_tab import EditorTab
from tabs.merger_tab import MergerTab
from tabs.about_tab import AboutTab

class YouTubeDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Media Toolkit")
        self.geometry("1050x900")
        
        # Применяем тему
        AppTheme.apply_theme(self)

        # Создаем контейнер вкладок
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Инициализируем вкладки
        self.tabs = {} # Храним ссылки на объекты вкладок
        self.init_tabs()

        # Запускаем проверки при старте (в фоне, чтобы не морозить окно)
        self.run_startup_checks()

    def init_tabs(self):
        self.tabs['downloader'] = DownloaderTab(self.notebook)
        self.notebook.add(self.tabs['downloader'], text="  Downloader  ")
        
        self.tabs['converter'] = ConverterTab(self.notebook)
        self.notebook.add(self.tabs['converter'], text="  Converter  ")
        
        self.tabs['compressor'] = CompressorTab(self.notebook)
        self.notebook.add(self.tabs['compressor'], text="  Compressor  ")
        
        self.tabs['editor'] = EditorTab(self.notebook)
        self.notebook.add(self.tabs['editor'], text="  Editor / Cutter  ")
        
        self.tabs['merger'] = MergerTab(self.notebook)
        self.notebook.add(self.tabs['merger'], text="  Merger  ")
        
        self.tabs['about'] = AboutTab(self.notebook)
        self.notebook.add(self.tabs['about'], text="  About Program  ")


    def run_startup_checks(self):
        def _checks_thread():
            logger = self.tabs['downloader'].log
            logger("-"*32+" Startup Checks "+"-"*32, replace=False)
            
            # Проверка FFmpeg
            has_ffmpeg = check_ffmpeg(log_callback=logger)
            if not has_ffmpeg:
                logger("❌ CRITICAL: FFmpeg not found in 'bin/' or PATH!", replace=False)
                logger("   Video merging and audio conversion will NOT work.", replace=False)
            
            # Проверка обновлений yt-dlp
            update_yt_dlp(log_callback=logger)
            
            logger("-"*80+"\n", replace=False)

        # Запуск потока
        threading.Thread(target=_checks_thread, daemon=True).start()

if __name__ == "__main__":
    app = YouTubeDownloaderApp()
    app.mainloop()