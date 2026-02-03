# src/tabs/downloader_tab.py
import tkinter as tk
from tkinter import ttk
from tabs.base_tab import BaseTab
from core.downloader_logic import DownloadLogic

class DownloaderTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.active_downloads = []
        # Множество для хранения текущих URL в работе, чтобы избежать дублей
        self.processing_urls = set() 
        self.setup_ui()

    def setup_ui(self):
        content_wrapper = ttk.Frame(self.main_container)
        content_wrapper.pack(side="top", fill="both", expand=True)

        form_frame = ttk.Frame(content_wrapper)
        form_frame.place(relx=0.5, rely=0.5, anchor="center")

        # 1. URL
        ttk.Label(form_frame, text="Video URL:").grid(row=0, column=0, sticky="w", pady=5)
        self.url_entry = ttk.Entry(form_frame, width=55)
        self.url_entry.grid(row=0, column=1, sticky="ew", padx=5, pady=5)
        
        btn_frame_1 = ttk.Frame(form_frame)
        btn_frame_1.grid(row=0, column=2, sticky="w")
        self.create_icon_button(btn_frame_1, "📋", lambda: (self.clear_entry(self.url_entry), self.paste_to_entry(self.url_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_frame_1, "❌", lambda: self.clear_entry(self.url_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_frame_1, "📑", lambda: self.copy_from_entry(self.url_entry)).pack(side="left", padx=1)

        # 2. Filename
        ttk.Label(form_frame, text="Filename:").grid(row=1, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(form_frame)
        self.name_entry.grid(row=1, column=1, sticky="ew", padx=5, pady=5)
        
        btn_frame_2 = ttk.Frame(form_frame)
        btn_frame_2.grid(row=1, column=2, sticky="w")
        self.create_icon_button(btn_frame_2, "📋", lambda: (self.clear_entry(self.name_entry), self.paste_to_entry(self.name_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_frame_2, "❌", lambda: self.clear_entry(self.name_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_frame_2, "📑", lambda: self.copy_from_entry(self.name_entry)).pack(side="left", padx=1)

        # 3. Folder
        ttk.Label(form_frame, text="Save Folder:").grid(row=2, column=0, sticky="w", pady=5)
        self.folder_entry = ttk.Entry(form_frame)
        self.folder_entry.grid(row=2, column=1, sticky="ew", padx=5, pady=5)
        
        btn_frame_3 = ttk.Frame(form_frame)
        btn_frame_3.grid(row=2, column=2, sticky="w")
        self.create_icon_button(btn_frame_3, "📂", lambda: self.open_folder_dialog(self.folder_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_frame_3, "📋", lambda: (self.clear_entry(self.folder_entry), self.paste_to_entry(self.folder_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_frame_3, "❌", lambda: self.clear_entry(self.folder_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_frame_3, "📑", lambda: self.copy_from_entry(self.folder_entry)).pack(side="left", padx=1)

        # 4. Settings Line
        options_frame = ttk.Frame(form_frame)
        options_frame.grid(row=3, column=1, sticky="ew", pady=15)
        
        ttk.Label(options_frame, text="Quality:").pack(side="left")
        self.quality_var = tk.StringVar(value="Best")
        qualities = ["Best", "2160p", "1440p", "1080p", "720p", "480p", "360p", "144p"]
        ttk.Combobox(options_frame, textvariable=self.quality_var, values=qualities, width=7, state="readonly").pack(side="left", padx=5)

        ttk.Label(options_frame, text="Vid Ext:").pack(side="left", padx=(15, 0))
        self.vid_ext_var = tk.StringVar(value="mp4")
        v_exts = ["mp4", "mkv", "webm"]
        ttk.Combobox(options_frame, textvariable=self.vid_ext_var, values=v_exts, width=5, state="readonly").pack(side="left", padx=5)

        ttk.Label(options_frame, text="Aud Ext:").pack(side="left", padx=(15, 0))
        self.aud_ext_var = tk.StringVar(value="mp3")
        a_exts = ["mp3", "m4a", "wav", "flac"]
        ttk.Combobox(options_frame, textvariable=self.aud_ext_var, values=a_exts, width=5, state="readonly").pack(side="left", padx=5)

        # 5. Checkboxes (Sound + Overwrite)
        checks_frame = ttk.Frame(options_frame)
        checks_frame.pack(side="right", padx=10)

        self.overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(checks_frame, text="Overwrite", variable=self.overwrite_var).pack(side="right", padx=5)

        self.sound_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(checks_frame, text="Sound", variable=self.sound_var).pack(side="right", padx=5)

        # 6. Action Buttons
        actions_frame = ttk.Frame(form_frame)
        actions_frame.grid(row=4, column=0, columnspan=3, pady=25)
        
        self.btn_video = ttk.Button(actions_frame, text="DOWNLOAD VIDEO", command=lambda: self.start_download('video')).pack(side="left", padx=15, ipadx=15)

        self.btn_audio = ttk.Button(actions_frame, text="DOWNLOAD AUDIO", command=lambda: self.start_download('audio')).pack(side="left", padx=15, ipadx=15)
        
        self.btn_cancel = ttk.Button(actions_frame, text="CANCEL ALL", command=self.cancel_all_downloads).pack(side="left", padx=15, ipadx=5)

    def start_download(self, mode):
        url = self.url_entry.get().strip()
        if not url:
            self.log("❌ Error: URL is empty!")
            return

        # ЗАЩИТА ОТ ДВОЙНОГО НАЖАТИЯ
        if url in self.processing_urls:
            self.log("⚠️ This URL is already currently downloading. Please wait.")
            return

        self.processing_urls.add(url)

        params = {
            'url': url,
            'path': self.folder_entry.get().strip(),
            'filename': self.name_entry.get().strip(),
            'quality': self.quality_var.get(),
            'video_ext': self.vid_ext_var.get(),
            'audio_ext': self.aud_ext_var.get(),
            'keep_video_sound': self.sound_var.get(),
            'overwrite': self.overwrite_var.get(),
            'mode': mode
        }
        
        # Создаем НОВЫЙ экземпляр логики для каждой загрузки
        downloader = DownloadLogic(self.log)
        self.active_downloads.append(downloader)
        
        # Запускаем в потоке
        self.run_async(self.run_download_wrapper, downloader, params)

    def run_download_wrapper(self, downloader, params):
        url = params['url']
        try:
            downloader.run_download(params)
        finally:
            # Очистка списков после завершения (успех или ошибка)
            if downloader in self.active_downloads:
                self.active_downloads.remove(downloader)
            
            # Убираем URL из активных, разрешая качать его снова
            if url in self.processing_urls:
                self.processing_urls.remove(url)

    def cancel_all_downloads(self):
        if not self.active_downloads:
            self.log("⚠️ No active downloads to cancel.")
            self.log("-"*80, replace=False)
            return
            
        self.log(f"🛑 Stopping {len(self.active_downloads)} active download(s)...") 
        for downloader in self.active_downloads:
            downloader.stop_download()