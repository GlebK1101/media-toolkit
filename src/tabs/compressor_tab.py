# src/tabs/compressor_tab.py
import tkinter as tk
from tkinter import ttk, filedialog
import os
from tabs.base_tab import BaseTab
from core.compressor_logic import CompressorLogic

class CompressorTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.active_tasks = []
        self.setup_ui()

    def setup_ui(self):
        split_container = ttk.Frame(self.main_container)
        split_container.pack(side="top", fill="both", expand=True, padx=10, pady=10)

        # --- LEFT SIDE: Single File ---
        left_frame = ttk.Labelframe(split_container, text=" Single File Compression (CRF) ", padding=10)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        self._setup_single_ui(left_frame)

        # --- RIGHT SIDE: Batch Folder ---
        right_frame = ttk.Labelframe(split_container, text=" Batch Folder Compression ", padding=10)
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
        self.create_icon_button(btn_box1, "📑", lambda: self.copy_from_entry(self.single_in_entry)).pack(side="left", padx=1)

        # 2. Output Folder
        ttk.Label(content_frame, text="Output Folder:").pack(anchor="w", pady=(0, 2))
        self.single_out_entry = ttk.Entry(content_frame)
        self.single_out_entry.pack(fill="x", pady=(0, 5))
        
        btn_box2 = ttk.Frame(content_frame)
        btn_box2.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box2, "📂", lambda: self.open_folder_dialog(self.single_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📋", lambda: (self.clear_entry(self.single_out_entry), self.paste_to_entry(self.single_out_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "❌", lambda: self.clear_entry(self.single_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📑", lambda: self.copy_from_entry(self.single_out_entry)).pack(side="left", padx=1)

        # 3. Output Filename
        ttk.Label(content_frame, text="Output Name (no ext):").pack(anchor="w", pady=(0, 2))
        self.single_name_entry = ttk.Entry(content_frame)
        self.single_name_entry.pack(fill="x", pady=(0, 5))

        btn_box3 = ttk.Frame(content_frame)
        btn_box3.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box3, "📋", lambda: (self.clear_entry(self.single_name_entry), self.paste_to_entry(self.single_name_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box3, "❌", lambda: self.clear_entry(self.single_name_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box3, "📑", lambda: self.copy_from_entry(self.single_name_entry)).pack(side="left", padx=1)

        # 4. Settings (Resolution + CRF)
        settings_frame = ttk.Frame(content_frame)
        settings_frame.pack(fill="x", pady=(0, 15))
        
        # Resolution (Расширенный список)
        res_frame = ttk.Frame(settings_frame)
        res_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(res_frame, text="Target Res:").pack(anchor="w", pady=(0, 2))
        self.single_res_var = tk.StringVar(value="Original")
        resolutions = ["Original", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
        ttk.Combobox(res_frame, textvariable=self.single_res_var, values=resolutions, state="readonly", width=10).pack(fill="x")

        # CRF Slider
        crf_frame = ttk.Frame(settings_frame)
        crf_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        self.single_crf_label = ttk.Label(crf_frame, text="CRF: 23 (Balanced)", width=22)
        self.single_crf_label.pack(anchor="w", pady=(0, 0))
        
        self.single_crf_scale = ttk.Scale(crf_frame, from_=0, to=51, orient="horizontal", command=self._update_single_crf_label)
        self.single_crf_scale.set(23)
        self.single_crf_scale.pack(fill="x")

        # Overwrite
        self.single_overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(content_frame, text="Overwrite", variable=self.single_overwrite_var).pack(anchor="e", pady=(0, 10))

        # 5. Actions
        self.btn_single_start = ttk.Button(buttons_frame, text="COMPRESS FILE", command=self.start_single).pack(fill="x", pady=(0, 5))
        self.btn_single_cancel = ttk.Button(buttons_frame, text="CANCEL", command=self.cancel_single).pack(fill="x")

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
        self.create_icon_button(btn_box1, "📑", lambda: self.copy_from_entry(self.batch_in_entry)).pack(side="left", padx=1)

        # 2. Output Folder
        ttk.Label(content_frame, text="Output Folder:").pack(anchor="w", pady=(0, 2))
        self.batch_out_entry = ttk.Entry(content_frame)
        self.batch_out_entry.pack(fill="x", pady=(0, 5))
        
        btn_box2 = ttk.Frame(content_frame)
        btn_box2.pack(fill="x", pady=(0, 10))
        self.create_icon_button(btn_box2, "📂", lambda: self.open_folder_dialog(self.batch_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📋", lambda: (self.clear_entry(self.batch_out_entry), self.paste_to_entry(self.batch_out_entry))).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "❌", lambda: self.clear_entry(self.batch_out_entry)).pack(side="left", padx=1)
        self.create_icon_button(btn_box2, "📑", lambda: self.copy_from_entry(self.batch_out_entry)).pack(side="left", padx=1)

        # 3. SPACER (Invisible widgets for alignment)
        lbl_dummy = ttk.Label(content_frame, text=" ") .pack(anchor="w", pady=(0, 2))
        entry_dummy = ttk.Frame(content_frame, height=22) .pack(fill="x", pady=(0, 5))
        btn_dummy = ttk.Frame(content_frame, height=28) .pack(fill="x", pady=(0, 4))

        # 4. Settings
        settings_frame = ttk.Frame(content_frame)
        settings_frame.pack(fill="x", pady=(0, 15))
        
        res_frame = ttk.Frame(settings_frame)
        res_frame.pack(side="left", fill="x", expand=True, padx=(0, 5))
        ttk.Label(res_frame, text="Target Res:").pack(anchor="w", pady=(0, 2))
        self.batch_res_var = tk.StringVar(value="Original")
        resolutions = ["Original", "2160p", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"]
        ttk.Combobox(res_frame, textvariable=self.batch_res_var, values=resolutions, state="readonly", width=10).pack(fill="x")

        crf_frame = ttk.Frame(settings_frame)
        crf_frame.pack(side="left", fill="x", expand=True, padx=(5, 0))
        
        self.batch_crf_label = ttk.Label(crf_frame, text="CRF: 23 (Balanced)", width=22)
        self.batch_crf_label.pack(anchor="w", pady=(0, 0))
        
        self.batch_crf_scale = ttk.Scale(crf_frame, from_=0, to=51, orient="horizontal", command=self._update_batch_crf_label)
        self.batch_crf_scale.set(23)
        self.batch_crf_scale.pack(fill="x")

        # Overwrite
        self.batch_overwrite_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(content_frame, text="Overwrite", variable=self.batch_overwrite_var).pack(anchor="e", pady=(0, 10))

        # 5. Actions
        self.btn_batch_start = ttk.Button(buttons_frame, text="COMPRESS FOLDER", command=self.start_batch).pack(fill="x", pady=(0, 5))
        
        self.btn_batch_cancel = ttk.Button(buttons_frame, text="CANCEL", command=self.cancel_batch).pack(fill="x")

    # --- UI Helpers ---
    def _update_single_crf_label(self, val):
        v = int(float(val))
        desc = self._get_crf_desc(v)
        self.single_crf_label.config(text=f"CRF: {v} ({desc})")

    def _update_batch_crf_label(self, val):
        v = int(float(val))
        desc = self._get_crf_desc(v)
        self.batch_crf_label.config(text=f"CRF: {v} ({desc})")

    def _get_crf_desc(self, v):
        if v == 0: return "Lossless"
        if v < 18: return "High Quality"
        if 18 <= v <= 28: return "Balanced"
        if v > 28: return "Low Quality"
        return ""

    # --- Logic ---

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
            # тут далее до конца блока if дописанная мною логика. По аналогии для bath
            out_folder = os.path.join(out_folder, "compressed")
            try:
                os.makedirs(out_folder, exist_ok=True)
                # То самое легендарное автозаполнение
                self.single_out_entry.delete(0, tk.END)
                self.single_out_entry.insert(0, out_folder)
            except:
                self.log("❌ Error: Cannot create output folder.", replace=False)
                self.log("-" * 80, replace=False)
                return
            
        params = {
            'input_path': path,
            'output_folder': out_folder,
            'output_name': out_name, 
            'crf': int(self.single_crf_scale.get()),
            'resolution': self.single_res_var.get(),
            'overwrite': overwrite
        }
        
        logic = CompressorLogic(self.log)
        self.active_tasks.append(logic)
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
            # Создаем папку 'compressed' по умолчанию, если не указано
            out_dir = os.path.join(in_dir, "compressed")
            try:
                os.makedirs(out_dir, exist_ok=True)
                # То самое легендарное автозаполнение
                self.batch_out_entry.delete(0, tk.END)
                self.batch_out_entry.insert(0, out_dir)
            except:
                self.log("❌ Error: Cannot create output folder.", replace=False)
                self.log("-" * 80, replace=False)
                return

        params = {
            'input_folder': in_dir,
            'output_folder': out_dir,
            'crf': int(self.batch_crf_scale.get()),
            'resolution': self.batch_res_var.get(),
            'overwrite': overwrite
        }

        logic = CompressorLogic(self.log)
        self.active_tasks.append(logic)
        self.last_batch_logic = logic

        self.run_async(self._run_wrapper, logic, params, 'batch')

    def _run_wrapper(self, logic, params, mode):
        try:
            if mode == 'single':
                logic.run_compress(params)
            else:
                logic.run_batch(params)
        finally:
            if logic in self.active_tasks:
                self.active_tasks.remove(logic)

    def cancel_single(self):
        if hasattr(self, 'last_single_logic') and self.last_single_logic in self.active_tasks:
            self.last_single_logic.stop_process()
        else:
            self.log("⚠️ Nothing to cancel.", replace=False)
            self.log("-" * 80, replace=False)

    def cancel_batch(self):
        if hasattr(self, 'last_batch_logic') and self.last_batch_logic in self.active_tasks:
            self.last_batch_logic.stop_process()
        else:
            self.log("⚠️ Nothing to cancel.", replace=False)
            self.log("-" * 80, replace=False)