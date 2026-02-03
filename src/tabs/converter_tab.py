# src/tabs/converter_tab.py
import tkinter as tk
from tkinter import ttk, filedialog
import os
from tabs.base_tab import BaseTab
from core.converter_logic import ConverterLogic

class ConverterTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.active_converters = []
        self.last_single_logic = None
        self.last_batch_logic = None
        self.setup_ui()

    def setup_ui(self):
        split_container = ttk.Frame(self.main_container)
        split_container.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # --- LEFT SIDE: Single File ---
        left_frame = ttk.Labelframe(split_container, text=" Single File Conversion ", padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))

        self._setup_single_ui(left_frame)

        # --- RIGHT SIDE: Batch Folder ---
        right_frame = ttk.Labelframe(split_container, text=" Batch Folder Conversion ", padding=10)
        right_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))

        self._setup_batch_ui(right_frame)

    def _setup_single_ui(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(side="top", fill="both", expand=True)
        
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        # 1. Input File
        ttk.Label(content_frame, text="Input File:").pack(anchor="w", pady=(0, 2))
        self.single_in_entry = ttk.Entry(content_frame)
        self.single_in_entry.pack(fill="x", pady=(0, 5))
        
        btn_box1 = ttk.Frame(content_frame)
        btn_box1.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box1, "📂", lambda: self._select_single_file()).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "📋", lambda: (self.clear_entry(self.single_in_entry), self.paste_to_entry(self.single_in_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "❌", lambda: self.clear_entry(self.single_in_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "📄", lambda: self.copy_from_entry(self.single_in_entry)).pack(side="left", padx=1)

        # 2. Output Folder
        ttk.Label(content_frame, text="Output Folder:").pack(anchor="w", pady=(0, 2))
        self.single_out_entry = ttk.Entry(content_frame)
        self.single_out_entry.pack(fill="x", pady=(0, 5))
        
        btn_box2 = ttk.Frame(content_frame)
        btn_box2.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box2, "📂", lambda: self.open_folder_dialog(self.single_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📋", lambda: (self.clear_entry(self.single_out_entry), self.paste_to_entry(self.single_out_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "❌", lambda: self.clear_entry(self.single_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📄", lambda: self.copy_from_entry(self.single_out_entry)).pack(side="left", padx=1)

        # 3. Output Filename
        ttk.Label(content_frame, text="Output Filename (no ext):").pack(anchor="w", pady=(0, 2))
        self.single_name_entry = ttk.Entry(content_frame)
        self.single_name_entry.pack(fill="x", pady=(0, 5))

        btn_box3 = ttk.Frame(content_frame)
        btn_box3.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box3, "📋", lambda: (self.clear_entry(self.single_name_entry), self.paste_to_entry(self.single_name_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box3, "❌", lambda: self.clear_entry(self.single_name_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box3, "📄", lambda: self.copy_from_entry(self.single_name_entry)).pack(side="left", padx=1)

        # 4. Settings Line (Format + Checkbox)
        settings_frame = ttk.Frame(content_frame)
        settings_frame.pack(fill="x", pady=(0, 0))
        
        # Format
        fmt_frame = ttk.Frame(settings_frame)
        fmt_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(fmt_frame, text="Target Format:").pack(anchor="w", pady=(0, 2))
        self.single_format_var = tk.StringVar(value=".mp4")
        formats = ['.mp4', '.mkv', '.avi', '.webm', '.mov', '.mp3', '.wav', '.m4a', '.flac', '.ogg']
        ttk.Combobox(fmt_frame, textvariable=self.single_format_var, values=formats, state="readonly").pack(fill="x")

        # Overwrite Checkbox
        self.single_overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Overwrite", variable=self.single_overwrite_var).pack(side="right", anchor="s", padx=(10,0), pady=2)

        # === КНОПКИ ВНИЗУ ===
        self.btn_single_start = ttk.Button(buttons_frame, text="CONVERT FILE", command=self.start_single)
        self.btn_single_start.pack(fill="x", pady=(0, 5))
        
        self.btn_single_cancel = ttk.Button(buttons_frame, text="CANCEL", command=self.cancel_single)
        self.btn_single_cancel.pack(fill="x")

    def _setup_batch_ui(self, parent):
        content_frame = ttk.Frame(parent)
        content_frame.pack(side="top", fill="both", expand=True)
        
        buttons_frame = ttk.Frame(parent)
        buttons_frame.pack(side="bottom", fill="x", pady=(10, 0))
        
        # 1. Input Folder
        ttk.Label(content_frame, text="Input Folder:").pack(anchor="w", pady=(0, 2))
        self.batch_in_entry = ttk.Entry(content_frame)
        self.batch_in_entry.pack(fill="x", pady=(0, 5))
        
        btn_box1 = ttk.Frame(content_frame)
        btn_box1.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box1, "📂", lambda: self.open_folder_dialog(self.batch_in_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "📋", lambda: (self.clear_entry(self.batch_in_entry), self.paste_to_entry(self.batch_in_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "❌", lambda: self.clear_entry(self.batch_in_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box1, "📄", lambda: self.copy_from_entry(self.batch_in_entry)).pack(side="left", padx=1)

        # 2. Output Folder
        ttk.Label(content_frame, text="Output Folder:").pack(anchor="w", pady=(0, 2))
        self.batch_out_entry = ttk.Entry(content_frame)
        self.batch_out_entry.pack(fill="x", pady=(0, 5))
        
        btn_box2 = ttk.Frame(content_frame)
        btn_box2.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box2, "📂", lambda: self.open_folder_dialog(self.batch_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📋", lambda: (self.clear_entry(self.batch_out_entry), self.paste_to_entry(self.batch_out_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "❌", lambda: self.clear_entry(self.batch_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📄", lambda: self.copy_from_entry(self.batch_out_entry)).pack(side="left", padx=1)

        # 3. SPACER (для выравнивания с левой колонкой)
        lbl_dummy = ttk.Label(content_frame, text=" ") 
        lbl_dummy.pack(anchor="w", pady=(0, 2))
        entry_dummy = ttk.Frame(content_frame, height=22)
        entry_dummy.pack(fill="x", pady=(0, 5))
        btn_dummy = ttk.Frame(content_frame, height=28)
        btn_dummy.pack(fill="x", pady=(0, 5))

        # 4. Settings Line (Format + Checkbox)
        settings_frame = ttk.Frame(content_frame)
        settings_frame.pack(fill="x", pady=(0, 0))
        
        fmt_frame = ttk.Frame(settings_frame)
        fmt_frame.pack(side="left", fill="x", expand=True)
        ttk.Label(fmt_frame, text="Target Format:").pack(anchor="w", pady=(0, 2))
        self.batch_format_var = tk.StringVar(value=".mp3")
        formats = ['.mp4', '.mkv', '.avi', '.webm', '.mov', '.mp3', '.wav', '.m4a', '.flac', '.ogg']
        ttk.Combobox(fmt_frame, textvariable=self.batch_format_var, values=formats, state="readonly").pack(fill="x")

        # Overwrite Checkbox
        self.batch_overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(settings_frame, text="Overwrite", variable=self.batch_overwrite_var).pack(side="right", anchor="s", padx=(10,0), pady=2)

        # === КНОПКИ ВНИЗУ ===
        self.btn_batch_start = ttk.Button(buttons_frame, text="CONVERT FOLDER", command=self.start_batch)
        self.btn_batch_start.pack(fill="x", pady=(0, 5))
        
        self.btn_batch_cancel = ttk.Button(buttons_frame, text="CANCEL", command=self.cancel_batch)
        self.btn_batch_cancel.pack(fill="x")

    # --- Logic Connectors ---

    def _select_single_file(self):
        f = filedialog.askopenfilename()
        if f:
            # Легендарное автозаполнение (отлючено)
            self.single_in_entry.delete(0, tk.END)
            self.single_in_entry.insert(0, f)

    def start_single(self):
        path = self.single_in_entry.get().strip()
        out_folder = self.single_out_entry.get().strip()
        out_name = self.single_name_entry.get().strip()
        overwrite = self.single_overwrite_var.get()
        
        if not path:
            self.log("❌ Error: Select a file first.", replace=False)
            self.log("-" * 80, replace=False)
            return
            
        if not out_folder:
            out_folder = os.path.dirname(path)
            
        params = {
            'input_path': path,
            'output_folder': out_folder,
            'output_name': out_name,
            'format': self.single_format_var.get(),
            'overwrite': overwrite
        }
        
        logic = ConverterLogic(self.log)
        self.active_converters.append(logic)
        self.last_single_logic = logic 
        
        self.run_async(self._run_wrapper, logic, params, 'single')

    def start_batch(self):
        in_dir = self.batch_in_entry.get().strip()
        out_dir = self.batch_out_entry.get().strip()
        overwrite = self.batch_overwrite_var.get()
        
        if not in_dir:
            self.log("❌ Error: Select input folder.", replace=False)
            self.log("-" * 80, replace=False)
            return
            
        if not out_dir:
            out_dir = os.path.join(in_dir, "converted")
            try:
                os.makedirs(out_dir, exist_ok=True)
                # То самое легендарное автозаполнение. Можете убрать, если раздражает
                self.batch_out_entry.delete(0, tk.END)
                self.batch_out_entry.insert(0, out_dir)
            except Exception as e:
                self.log(f"❌ Error: Cannot create output folder: {e}", replace=False)
                self.log("-" * 80, replace=False)
                return

        params = {
            'input_folder': in_dir,
            'output_folder': out_dir,
            'format': self.batch_format_var.get(),
            'overwrite': overwrite
        }

        logic = ConverterLogic(self.log)
        self.active_converters.append(logic)
        self.last_batch_logic = logic

        self.run_async(self._run_wrapper, logic, params, 'batch')

    def _run_wrapper(self, logic, params, mode):
        try:
            if mode == 'single':
                logic.run_convert(params)
            else:
                logic.run_batch(params)
        finally:
            if logic in self.active_converters:
                self.active_converters.remove(logic)

    def cancel_single(self):
        if hasattr(self, 'last_single_logic') and self.last_single_logic and self.last_single_logic in self.active_converters:
            self.last_single_logic.stop_conversion()
        else:
            self.log("⚠️ Nothing to cancel.", replace=False)
            self.log("-" * 80, replace=False)

    def cancel_batch(self):
        if hasattr(self, 'last_batch_logic') and self.last_batch_logic and self.last_batch_logic in self.active_converters:
            self.last_batch_logic.stop_conversion()
        else:
            self.log("⚠️ Nothing to cancel.", replace=False)
            self.log("-" * 80, replace=False)