# src/tabs/base_tab.py
import tkinter as tk
from tkinter import ttk, filedialog
import threading
import queue
import json
from datetime import datetime

class BaseTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.log_queue = queue.Queue()
        
        self.last_msg_was_replace = False

        self.main_container = ttk.Frame(self)
        self.main_container.pack(fill="both", expand=True, padx=0, pady=0)
        
        self._setup_console()
        self.after(100, self._process_log_queue)

    def _setup_console(self):
        console_container = ttk.Frame(self.main_container)
        console_container.pack(side="bottom", fill="both", expand=True, pady=0)

        # Header Frame (Title Left, Buttons Right)
        header_frame = ttk.Frame(console_container)
        header_frame.pack(side="top", fill="x", padx=10, pady=(5, 2))

        # Title Left
        ttk.Label(header_frame, text="Console Output", font=("Segoe UI", 9, "bold"), foreground="#666666").pack(side="left")

        # Buttons Right
        btn_frame = ttk.Frame(header_frame)
        btn_frame.pack(side="right")
        
        self.create_icon_button(btn_frame, "🗑️", self._clear_console).pack(side="left", padx=1)
        self.create_icon_button(btn_frame, "📋", self._copy_console).pack(side="left", padx=1)
        self.create_icon_button(btn_frame, "💾", self._export_console).pack(side="left", padx=1)

        # Text Area (No scrollbar widget, scroll via mouse/keys)
        self.console_text = tk.Text(console_container, height=8, 
                                    bg="#ffffff", fg="#333333", 
                                    font=("Consolas", 10), 
                                    relief="flat", 
                                    highlightthickness=0,
                                    state="disabled")
        self.console_text.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 10))

    def create_icon_button(self, parent, text, command):
        return ttk.Button(parent, text=text, command=command, style="Icon.TButton", width=3)

    # --- Common Actions ---
    def open_folder_dialog(self, entry_widget):
        folder = filedialog.askdirectory()
        if folder:
            entry_widget.delete(0, tk.END)
            entry_widget.insert(0, folder)

    def paste_to_entry(self, entry_widget):
        try:
            text = self.clipboard_get()
            entry_widget.insert(tk.INSERT, text)
        except tk.TclError: pass

    def clear_entry(self, entry_widget):
        entry_widget.delete(0, tk.END)

    def copy_from_entry(self, entry_widget):
        try:
            text = entry_widget.get()
            self.clipboard_clear()
            self.clipboard_append(text)
            self.update()
        except: pass

    # --- Console Logic ---
    def log(self, message, replace=False):
        # Не вижу смысла в логи добавлять время, ведь никакой обработки после мы не ведем. Но если нравится, можете включить.
        # timestamp = f"[{datetime.now().strftime('%H:%M:%S')}] " if not replace else ""
        # full_msg = f"{timestamp}{message}" 
        
        self.log_queue.put((message, replace))

    def _process_log_queue(self):
        while not self.log_queue.empty():
            msg, replace = self.log_queue.get()
            self.console_text.config(state="normal")

            if replace:
                # Если предыдущее сообщение тоже было "заменяемым", удаляем его
                if self.last_msg_was_replace:
                    # Удаляем последнюю строку (от start of line-1 до end-1c)
                    # "end-1c linestart" находит начало последней строки
                    self.console_text.delete("end-2l", "end-1c") 
            
            # Вставляем новое сообщение
            self.console_text.insert(tk.END, msg + "\n")
            self.console_text.see(tk.END)
            self.console_text.config(state="disabled")
            
            # Обновляем флаг
            self.last_msg_was_replace = replace

        self.after(50, self._process_log_queue)

    def _clear_console(self):
        self.console_text.config(state="normal")
        self.console_text.delete("1.0", tk.END)
        self.console_text.config(state="disabled")

    def _copy_console(self):
        text = self.console_text.get("1.0", tk.END)
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()

    def _export_console(self):
        f = filedialog.asksaveasfile(mode='w', defaultextension=".json")
        if f is None: return
        content = self.console_text.get("1.0", tk.END)
        json.dump({"logs": content.split('\n')}, f, indent=4)
        f.close()

    def run_async(self, target, *args):
        threading.Thread(target=target, args=args, daemon=True).start()