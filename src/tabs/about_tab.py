# src/tabs/about_tab.py
import tkinter as tk
from tkinter import ttk
import webbrowser
import sys
import os
from datetime import datetime
from tabs.base_tab import BaseTab

class AboutTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        
        children = self.main_container.pack_slaves()
        if children:
            children[-1].pack_forget()

        # Настройка шрифтов
        self.fonts = {
            "h1": ("Segoe UI", 24, "bold"),
            "h2": ("Segoe UI", 14, "bold"),
            "body": ("Segoe UI", 11),
            "bold": ("Segoe UI", 11, "bold"),
            "mono": ("Consolas", 10),
            "link": ("Segoe UI", 11, "underline"),
            "caption": ("Segoe UI", 9, "italic")
        }
        
        self.setup_ui()
        self._fill_content() 
        self.text_widget.config(state="disabled") 

    def setup_ui(self):
        # --- HEADER (Верхняя панель) ---
        header_frame = ttk.Frame(self.main_container)
        header_frame.pack(side="top", fill="x", padx=20, pady=20)

        info_frame = ttk.Frame(header_frame)
        info_frame.pack(side="left")
        
        # Название и Версия
        ttk.Label(info_frame, text="Media Toolkit", font=("Segoe UI", 20, "bold"), foreground="#0078d7").pack(anchor="w")
        ver_str = f"Version 1.0.1 | 04.02.2026"
        ttk.Label(info_frame, text=ver_str, font=("Segoe UI", 10), foreground="#666666").pack(anchor="w")

        # Правая часть хедера (Python version + GitHub btn)
        meta_frame = ttk.Frame(header_frame)
        meta_frame.pack(side="right", anchor="e")

        py_ver = f"Python {sys.version.split()[0]}"
        lbl_py = ttk.Label(meta_frame, text=f"🐍 {py_ver}", font=("Consolas", 10, "bold"), 
                           background="#ffe873", foreground="#306998", padding=(5, 2))
        lbl_py.pack(side="top", anchor="e", pady=(0, 5))

        btn_gh = ttk.Button(meta_frame, text="GitHub Repository ↗", style="TButton",
                            command=lambda: webbrowser.open("https://github.com/GlebK1101/media-toolkit"))
        btn_gh.pack(side="top", anchor="e")

        ttk.Separator(self.main_container, orient="horizontal").pack(fill="x", padx=20, pady=(0, 10))

        # --- CONTENT AREA (Текстовое поле) ---
        content_frame = ttk.Frame(self.main_container)
        content_frame.pack(side="top", fill="both", expand=True, padx=20, pady=(0, 20))

        self.text_widget = tk.Text(content_frame, wrap="word", relief="flat", padx=10, pady=10,
                                   font=self.fonts["body"], bg="#f8f9fa", fg="#202020",
                                   highlightthickness=0)
        
        self.text_widget.pack(side="left", fill="both", expand=True)

        # Конфигурация тегов
        self.text_widget.tag_config("h1", font=self.fonts["h1"], foreground="#202020", spacing3=10)
        self.text_widget.tag_config("h2", font=self.fonts["h2"], foreground="#0078d7", spacing1=15, spacing3=5)
        self.text_widget.tag_config("body", font=self.fonts["body"], spacing1=2, spacing3=2)
        self.text_widget.tag_config("bold", font=self.fonts["bold"])
        self.text_widget.tag_config("mono", font=self.fonts["mono"], background="#e9ecef", foreground="#d63384")
        self.text_widget.tag_config("link", font=self.fonts["link"], foreground="#0078d7")
        self.text_widget.tag_config("bullet", lmargin1=20, lmargin2=40, spacing1=3)
        self.text_widget.tag_config("center", justify="center")

        # Курсор руки для ссылок
        self.text_widget.tag_bind("link", "<Enter>", lambda e: self.text_widget.config(cursor="hand2"))
        self.text_widget.tag_bind("link", "<Leave>", lambda e: self.text_widget.config(cursor=""))

    # ==========================================
    #      МЕТОДЫ-ПОМОЩНИКИ
    # ==========================================
    def add_title(self, text):
        self.text_widget.insert(tk.END, text + "\n", "h1")

    def add_heading(self, text):
        self.text_widget.insert(tk.END, text + "\n", "h2")

    def add_text(self, text, bold=False, code=False):
        tags = ["body"]
        if bold: tags.append("bold")
        if code: tags.append("mono")
        self.text_widget.insert(tk.END, text, tuple(tags))

    def add_newline(self, count=1):
        self.text_widget.insert(tk.END, "\n" * count)

    def add_list_item(self, text):
        self.text_widget.insert(tk.END, f"• {text}\n", "bullet")

    def add_link(self, text, url):
        tag_name = f"link_{len(self.text_widget.tag_names())}"
        self.text_widget.tag_config(tag_name, foreground="#0078d7", underline=True)
        self.text_widget.tag_bind(tag_name, "<Button-1>", lambda e: webbrowser.open(url))
        self.text_widget.insert(tk.END, text, ("body", tag_name, "link"))

    def add_separator(self):
        self.text_widget.insert(tk.END, "─" * 40 + "\n", ("body", "color_#cccccc"))

    def add_centered_text(self, text, bold=False):
        tags = ["body", "center"]
        if bold: tags.append("bold")
        self.text_widget.insert(tk.END, text + "\n", tuple(tags))

    # ==========================================
    def _fill_content(self):
        
        self.add_title("About Media Toolkit")
        
        # Общее описание
        self.add_text("Media Toolkit is a lightweight, open-source desktop application designed to simplify media processing tasks.\n")
        self.add_newline()
        self.add_text("It acts as a graphical bridge for two industry-standard tools: ")
        self.add_text("yt-dlp", code=True)
        self.add_text(" (media downloading) and ")
        self.add_text("FFmpeg", code=True)
        self.add_text(" (processing/conversion).")
        
        self.add_newline(2)
        self.add_separator()

        # Технологии
        self.add_heading("Powered By")
        self.add_list_item("Python 3 & Tkinter (GUI)")
        self.add_list_item("yt-dlp (Network Engine)")
        self.add_list_item("FFmpeg (Processing Engine)")

        self.add_newline()
        self.add_separator()

        # Лицензия и ссылки
        self.add_heading("License & Source")
        self.add_text("This software is distributed under the ")
        self.add_text("MIT License", bold=True)
        self.add_text(".\n")
        
        self.add_text("You can view the source code, documentation, and contribute on GitHub:\n")
        self.add_link("Open GitHub Repository", "https://github.com/GlebK1101/media-toolkit") 
        