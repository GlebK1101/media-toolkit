# src/tabs/database_tab.py
import tkinter as tk
from tkinter import ttk, filedialog
import os
from tabs.base_tab import BaseTab
from core.database_logic import DatabaseConfig

class DatabaseTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        
        # Полный список всех возможных полей для логики UI
        self.fields_layout = [
            ("Video Title", "title"),
            ("Input Filename", "input_filename"),
            ("Video URL", "video_url"),
            ("Channel Name", "channel_name"),
            ("Channel Handle (@)", "channel_handle"),
            ("Channel URL (Direct)", "channel_url"),
            ("Download Time (Local)", "download_time"),
            ("Absolute Path", "absolute_path"), 
            ("Relative Path", "relative_path"),
            ("Final File Size", "file_size"),
            ("Selected Quality", "input_quality"),
            ("Upload Date (YYYYMMDD)", "upload_date"),
            ("Duration (sec)", "duration"),
            ("View Count", "view_count"),
            ("Like Count", "like_count"),
            ("Dislike Count", "dislike_count"),
            ("Comment Count", "comment_count"),
            ("Thumbnail URL", "thumbnail_url"),
            ("Description", "description"),
            ("Tags", "tags"),
            ("Resolution", "resolution"),
            ("FPS", "fps"),
            ("File Extension", "extension")
        ]
        self.ordered_keys = []
        
        self.setup_ui()

    def setup_ui(self):
        content_frame = ttk.Frame(self.main_container)
        content_frame.pack(side="top", fill="both", expand=False, padx=20, pady=10)

        # ГЛАВНЫЙ ПЕРЕКЛЮЧАТЕЛЬ
        top_frame = ttk.Frame(content_frame)
        top_frame.pack(fill="x", pady=(0, 10))
        
        self.var_enabled = tk.BooleanVar(value=False)
        self.chk_enable = ttk.Checkbutton(
            top_frame, text="Enable SQLite Metadata Logging for Downloads (Only for YouTube)", 
            variable=self.var_enabled, command=self._sync_settings
        )
        self.chk_enable.pack(side="left")

        # НАСТРОЙКИ БД
        db_frame = ttk.Labelframe(content_frame, text=" Database Configuration ", padding=10)
        db_frame.pack(fill="x", pady=(0, 10))

        # --- Path ---
        ttk.Label(db_frame, text="DB File Path:\n(Leave blank for default)").grid(row=0, column=0, sticky="w", pady=2)
        self.entry_path = ttk.Entry(db_frame, width=35)
        self.entry_path.grid(row=0, column=1, sticky="ew", padx=10, pady=2)
        self.entry_path.bind("<KeyRelease>", lambda e: self._sync_settings())
        
        btn_box1 = ttk.Frame(db_frame)
        btn_box1.grid(row=0, column=2, sticky="w")
        self.create_icon_button(btn_box1, "📁", self._browse_db_folder).pack(side="left", padx=1) 
        self.create_icon_button(btn_box1, "📄", self._browse_db_file).pack(side="left", padx=1)   
        self.create_icon_button(btn_box1, "📋", lambda: (self.clear_entry(self.entry_path), self.paste_to_entry(self.entry_path))).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "❌", lambda: self.clear_entry(self.entry_path)).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "📑", lambda: self.copy_from_entry(self.entry_path)).pack(side="left", padx=1)

        # --- Table Name ---
        ttk.Label(db_frame, text="Table Name:\n(Leave blank for auto-generation)").grid(row=1, column=0, sticky="w", pady=2)
        self.entry_table = ttk.Entry(db_frame, width=35)
        self.entry_table.grid(row=1, column=1, sticky="ew", padx=10, pady=2)
        self.entry_table.bind("<KeyRelease>", lambda e: self._sync_settings())

        btn_box2 = ttk.Frame(db_frame)
        btn_box2.grid(row=1, column=2, sticky="w")
        self.create_icon_button(btn_box2, "📋", lambda: (self.clear_entry(self.entry_table), self.paste_to_entry(self.entry_table))).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "❌", lambda: self.clear_entry(self.entry_table)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📑", lambda: self.copy_from_entry(self.entry_table)).pack(side="left", padx=1)

        # --- Time Format ---
        ttk.Label(db_frame, text="Time Format:\n(e.g., %Y-%m-%d %I:%M:%S %p)").grid(row=2, column=0, sticky="w", pady=2)
        self.entry_time_fmt = ttk.Entry(db_frame, width=35)
        self.entry_time_fmt.insert(0, "%Y-%m-%d %H:%M:%S")
        self.entry_time_fmt.grid(row=2, column=1, sticky="ew", padx=10, pady=2)
        self.entry_time_fmt.bind("<KeyRelease>", lambda e: self._sync_settings())

        btn_box3 = ttk.Frame(db_frame)
        btn_box3.grid(row=2, column=2, sticky="w")
        self.create_icon_button(btn_box3, "📋", lambda: (self.clear_entry(self.entry_time_fmt), self.paste_to_entry(self.entry_time_fmt))).pack(side="left", padx=1)
        self.create_icon_button(btn_box3, "❌", lambda: self.clear_entry(self.entry_time_fmt)).pack(side="left", padx=1)
        self.create_icon_button(btn_box3, "📑", lambda: self.copy_from_entry(self.entry_time_fmt)).pack(side="left", padx=1)

        db_frame.columnconfigure(1, weight=1)

        # ДОПОЛНИТЕЛЬНЫЕ НАСТРОЙКИ
        extra_frame = ttk.Labelframe(content_frame, text=" Additional Features ", padding=10)
        extra_frame.pack(fill="x", pady=(0, 10))
        
        self.var_check_dupes = tk.BooleanVar(value=False)
        ttk.Checkbutton(extra_frame, text="Prevent Database Duplicates (checks 'video_url' in table before saving)", variable=self.var_check_dupes, command=self._sync_settings).pack(anchor="w", pady=(0, 5))
        
        note_box = ttk.Frame(extra_frame)
        note_box.pack(fill="x")
        
        self.var_custom_note = tk.BooleanVar(value=False)
        ttk.Checkbutton(note_box, text="Add Custom Note:", variable=self.var_custom_note, command=self._sync_settings).pack(side="left")
        
        self.entry_note = ttk.Entry(note_box)
        self.entry_note.pack(side="left", fill="x", expand=True, padx=10)
        self.entry_note.bind("<KeyRelease>", lambda e: self._sync_settings())
        
        btn_box4 = ttk.Frame(note_box)
        btn_box4.pack(side="left")
        self.create_icon_button(btn_box4, "📋", lambda: (self.clear_entry(self.entry_note), self.paste_to_entry(self.entry_note))).pack(side="left", padx=1)
        self.create_icon_button(btn_box4, "❌", lambda: self.clear_entry(self.entry_note)).pack(side="left", padx=1)
        self.create_icon_button(btn_box4, "📑", lambda: self.copy_from_entry(self.entry_note)).pack(side="left", padx=1)


        # МЕТАДАННЫЕ И СОРТИРОВКА 
        meta_split = ttk.Frame(content_frame)
        meta_split.pack(fill="x", expand=False)
        
        # Левая часть: Галочки
        meta_frame = ttk.Labelframe(meta_split, text=" Metadata Fields ", padding=10)
        meta_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))
        
        self.field_vars = {}
        row, col = 0, 0
        for label_text, key in self.fields_layout:
            var = tk.BooleanVar(value=DatabaseConfig.selected_fields.get(key, False))
            self.field_vars[key] = var
            chk = ttk.Checkbutton(meta_frame, text=label_text, variable=var, command=self._sync_settings)
            chk.grid(row=row, column=col, sticky="w", padx=10, pady=2)
            
            col += 1
            if col > 2:  # 3 столбца для компактности
                col = 0
                row += 1

        # Правая часть: Сортировка столбцов
        sort_frame = ttk.Labelframe(meta_split, text=" Column Database Order ", padding=10)
        sort_frame.pack(side="right", fill="both")

        self.listbox_order = tk.Listbox(sort_frame, height=8, width=30, selectmode=tk.SINGLE, activestyle="none")
        self.listbox_order.pack(side="left", fill="y", padx=(0, 5))
        
        btn_sort_box = ttk.Frame(sort_frame)
        btn_sort_box.pack(side="left", fill="y")
        ttk.Button(btn_sort_box, text="▲ Up", width=8, command=self._move_col_up).pack(pady=2)
        ttk.Button(btn_sort_box, text="▼ Down", width=8, command=self._move_col_down).pack(pady=2)

        self._sync_settings()

    # --- UI Logic ---
    def _browse_db_folder(self):
        folder = filedialog.askdirectory(title="Select Folder for Database")
        if folder:
            full_path = os.path.join(folder, "database.db")
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, full_path)
            self._sync_settings()

    def _browse_db_file(self):
        f = filedialog.asksaveasfilename(
            defaultextension=".db", 
            filetypes=[("SQLite Database", "*.db"), ("All Files", "*.*")],
            title="Select or Create Database File"
        )
        if f:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, f)
            self._sync_settings()

    def _move_col_up(self):
        sel = self.listbox_order.curselection()
        if not sel: return
        idx = sel[0]
        if idx == 0: return
        
        self.ordered_keys[idx], self.ordered_keys[idx-1] = self.ordered_keys[idx-1], self.ordered_keys[idx]
        self._sync_settings()
        self.listbox_order.selection_set(idx-1)

    def _move_col_down(self):
        sel = self.listbox_order.curselection()
        if not sel: return
        idx = sel[0]
        if idx == len(self.ordered_keys) - 1: return
        
        self.ordered_keys[idx], self.ordered_keys[idx+1] = self.ordered_keys[idx+1], self.ordered_keys[idx]
        self._sync_settings()
        self.listbox_order.selection_set(idx+1)

    def _sync_settings(self):
        # Синхронизируем базовые данные
        DatabaseConfig.is_enabled = self.var_enabled.get()
        DatabaseConfig.db_path = self.entry_path.get().strip()
        DatabaseConfig.table_name = self.entry_table.get().strip()
        
        fmt = self.entry_time_fmt.get().strip()
        DatabaseConfig.datetime_format = fmt if fmt else "%Y-%m-%d %H:%M:%S"
        
        DatabaseConfig.check_duplicates = self.var_check_dupes.get()
        DatabaseConfig.custom_note_text = self.entry_note.get().strip()
        
        for key, var in self.field_vars.items():
            DatabaseConfig.selected_fields[key] = var.get()
        DatabaseConfig.selected_fields["custom_note"] = self.var_custom_note.get()

        # Логика Сортировки Столбцов
        current_selected = [key for l_text, key in self.fields_layout if self.field_vars[key].get()]
        if self.var_custom_note.get():
            current_selected.append("custom_note")
            
        # Удаляем ключи, с которых сняли галочки
        self.ordered_keys = [k for k in self.ordered_keys if k in current_selected]
        
        # Добавляем новые ключи в конец списка
        for k in current_selected:
            if k not in self.ordered_keys:
                self.ordered_keys.append(k)
                
        # Перерисовываем Listbox
        self.listbox_order.delete(0, tk.END)
        key_to_label = {k: l for l, k in self.fields_layout}
        key_to_label["custom_note"] = "Custom Note"
        
        for k in self.ordered_keys:
            self.listbox_order.insert(tk.END, f"≡ {key_to_label[k]}")
            
        # Сохраняем итоговый порядок в логику
        DatabaseConfig.column_order = self.ordered_keys.copy()