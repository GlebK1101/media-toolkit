# src/tabs/merger_tab.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os

from tabs.base_tab import BaseTab
from core.merger_logic import MergerLogic

class MergerTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.logic = MergerLogic(self.log)
        self.files_queue = [] 
        
        self.setup_ui()

    def setup_ui(self):
        # QUEUE MANAGEMENT
        q_frame = ttk.Labelframe(self.main_container, text=" Merger Queue ", padding=5)
        q_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        
        # List Area
        list_frame = ttk.Frame(q_frame)
        list_frame.pack(side="left", fill="both", expand=True)
        
        columns = ("#", "File", "Type", "Duration", "Size")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        self.tree.heading("#", text="#")
        self.tree.column("#", width=30, stretch=False)
        self.tree.heading("File", text="Filename")
        self.tree.column("File", width=250)
        self.tree.heading("Type", text="Type")
        self.tree.column("Type", width=60, stretch=False)
        self.tree.heading("Duration", text="Duration")
        self.tree.column("Duration", width=70, stretch=False)
        self.tree.heading("Size", text="Size")
        self.tree.column("Size", width=70, stretch=False)
        
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons Area
        btn_frame = ttk.Frame(q_frame)
        btn_frame.pack(side="right", fill="y", padx=5)
        
        ttk.Button(btn_frame, text="➕ Add Files", command=self._add_files).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="➖ Remove", command=self._remove_selected).pack(fill="x", pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="🔼 Up", command=self._move_up).pack(fill="x", pady=2)
        ttk.Button(btn_frame, text="🔽 Down", command=self._move_down).pack(fill="x", pady=2)
        ttk.Separator(btn_frame, orient="horizontal").pack(fill="x", pady=5)
        ttk.Button(btn_frame, text="🗑 Clear All", command=self._clear_all).pack(fill="x", pady=2)

        #  SETTINGS
        self.opts_frame = ttk.Labelframe(self.main_container, text=" Settings ", padding=5)
        self.opts_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        # --- Mode Selection ---
        mode_box = ttk.Frame(self.opts_frame)
        mode_box.pack(fill="x", pady=2)
        
        self.var_mode = tk.StringVar(value="video")
        r_vid = ttk.Radiobutton(mode_box, text="Video Mode (Merge A+V)", variable=self.var_mode, value="video", command=self._on_mode_change)
        r_vid.pack(side="left", padx=5)
        
        r_aud = ttk.Radiobutton(mode_box, text="Audio Mode (Audio Only)", variable=self.var_mode, value="audio", command=self._on_mode_change)
        r_aud.pack(side="left", padx=5)

        # --- Video Specific Settings ---
        self.vid_settings_frame = ttk.Frame(self.opts_frame)
        self.vid_settings_frame.pack(fill="x", pady=(5, 0))
        
        # Resolution, FPS, CRF
        row1 = ttk.Frame(self.vid_settings_frame)
        row1.pack(fill="x", pady=2)
        
        ttk.Label(row1, text="Res:").pack(side="left")
        self.cb_res = ttk.Combobox(row1, values=["1920x1080", "1280x720", "3840x2160", "1080x1920", "720x1280"], width=10)
        self.cb_res.set("1920x1080")
        self.cb_res.pack(side="left", padx=(2, 10))
        
        ttk.Label(row1, text="FPS:").pack(side="left")
        self.cb_fps = ttk.Combobox(row1, values=["24", "25", "30", "50", "60"], width=5)
        self.cb_fps.set("30")
        self.cb_fps.pack(side="left", padx=(2, 10))

        ttk.Label(row1, text="CRF:").pack(side="left")
        self.spin_crf = ttk.Spinbox(row1, from_=0, to=51, width=5)
        self.spin_crf.set(23)
        self.spin_crf.pack(side="left", padx=2)
        ttk.Label(row1, text="(Quality: 0-51, Lower=Better)").pack(side="left", padx=2)

        # Background Image
        row2 = ttk.Frame(self.vid_settings_frame)
        row2.pack(fill="x", pady=5)
        
        ttk.Label(row2, text="Background (Optional):").pack(side="left")
        self.entry_bg = ttk.Entry(row2)
        self.entry_bg.pack(side="left", fill="x", expand=True, padx=5)
        
        self.create_icon_button(row2, "📂", lambda: self._browse_file(self.entry_bg, [("Images", "*.jpg *.png *.jpeg")])).pack(side="left", padx=1)
        self.create_icon_button(row2, "📋", lambda: (self.clear_entry(self.entry_bg), self.paste_to_entry(self.entry_bg))).pack(side="left", padx=1)
        self.create_icon_button(row2, "❌", lambda: self.clear_entry(self.entry_bg)).pack(side="left", padx=1)
        self.create_icon_button(row2, "📑", lambda: self.copy_from_entry(self.entry_bg)).pack(side="left", padx=1)


        # BOTTOM: EXPORT
        self.ctrl_frame = ttk.Frame(self.main_container)
        self.ctrl_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        exp_frame = ttk.Labelframe(self.ctrl_frame, text=" Export ", padding=5)
        exp_frame.pack(fill="x")
        
        # Name
        ef1 = ttk.Frame(exp_frame)
        ef1.pack(fill="x", pady=2)
        ttk.Label(ef1, text="Name:", width=6).pack(side="left")
        self.entry_out_name = ttk.Entry(ef1)
        self.entry_out_name.pack(side="left", fill="x", expand=True, padx=5)
        self.entry_out_name.insert(0, "merged_output.mp4")
        
        self.create_icon_button(ef1, "📋", lambda: (self.clear_entry(self.entry_out_name), self.paste_to_entry(self.entry_out_name))).pack(side="left", padx=1)
        self.create_icon_button(ef1, "❌", lambda: self.clear_entry(self.entry_out_name)).pack(side="left", padx=1)
        self.create_icon_button(ef1, "📑", lambda: self.copy_from_entry(self.entry_out_name)).pack(side="left", padx=1)
        
        # Folder
        ef2 = ttk.Frame(exp_frame)
        ef2.pack(fill="x", pady=2)
        ttk.Label(ef2, text="Folder:", width=6).pack(side="left")
        self.entry_out_folder = ttk.Entry(ef2)
        self.entry_out_folder.pack(side="left", fill="x", expand=True, padx=5)
        
        self.create_icon_button(ef2, "📂", lambda: self.open_folder_dialog(self.entry_out_folder)).pack(side="left", padx=1)
        self.create_icon_button(ef2, "📋", lambda: (self.clear_entry(self.entry_out_folder), self.paste_to_entry(self.entry_out_folder))).pack(side="left", padx=1)
        self.create_icon_button(ef2, "❌", lambda: self.clear_entry(self.entry_out_folder)).pack(side="left", padx=1)
        self.create_icon_button(ef2, "📑", lambda: self.copy_from_entry(self.entry_out_folder)).pack(side="left", padx=1)

        # Action Buttons
        ef3 = ttk.Frame(exp_frame)
        ef3.pack(fill="x", pady=5)
        self.var_overwrite = tk.BooleanVar(value=False)
        ttk.Checkbutton(ef3, text="Overwrite", variable=self.var_overwrite).pack(side="right", padx=5)
        
        # Cancel Button
        ttk.Button(ef3, text="🚫 CANCEL", command=self._cancel_merge).pack(side="right", padx=5)
        ttk.Button(ef3, text="🔗 MERGE FILES", command=self._start_merge).pack(side="right", padx=5)

        self._on_mode_change()

    # ================= UI LOGIC =================
    
    def _browse_file(self, entry, filetypes):
        f = filedialog.askopenfilename(filetypes=filetypes)
        if f:
            entry.delete(0, tk.END)
            entry.insert(0, f)

    def _add_files(self):
        files = filedialog.askopenfilenames(title="Select Media Files")
        if not files: return
        
        for f in files:
            if not os.path.exists(f): continue
            
            info = self.logic.probe_file(f)
            if not info: continue
            
            dur_str = self._fmt_dur(info['duration'])
            size_str = self._fmt_size(info.get('size', 0))
            
            type_labels = []
            if info['has_video']: type_labels.append("Vid")
            if info['has_audio']: type_labels.append("Aud")
            type_str = "+".join(type_labels) if type_labels else "Unk"
            
            self.files_queue.append(f)
            
            idx = len(self.files_queue)
            name = os.path.basename(f)
            self.tree.insert("", "end", values=(idx, name, type_str, dur_str, size_str))

    def _remove_selected(self):
        selected = self.tree.selection()
        if not selected: return
        
        indices = sorted([self.tree.index(item) for item in selected], reverse=True)
        
        for idx in indices:
            del self.files_queue[idx]
            
        self._refresh_tree()

    def _move_up(self):
        selected = self.tree.selection()
        if not selected: return
        
        rows = [self.tree.index(item) for item in selected]
        rows.sort()
        
        if rows[0] == 0: return 
        
        for r in rows:
            self.files_queue[r], self.files_queue[r-1] = self.files_queue[r-1], self.files_queue[r]
            
        self._refresh_tree()
        new_sel = []
        children = self.tree.get_children()
        for r in rows:
            new_sel.append(children[r-1])
        self.tree.selection_set(new_sel)

    def _move_down(self):
        selected = self.tree.selection()
        if not selected: return
        
        rows = [self.tree.index(item) for item in selected]
        rows.sort(reverse=True)
        
        if rows[0] == len(self.files_queue) - 1: return 
        
        for r in rows:
            self.files_queue[r], self.files_queue[r+1] = self.files_queue[r+1], self.files_queue[r]
            
        self._refresh_tree()
        new_sel = []
        children = self.tree.get_children()
        for r in rows:
            new_sel.append(children[r+1])
        self.tree.selection_set(new_sel)

    def _clear_all(self):
        self.files_queue.clear()
        self._refresh_tree()

    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for i, f in enumerate(self.files_queue):
            info = self.logic.probe_file(f) 
            name = os.path.basename(f)
            
            type_str = "Unknown"
            dur_str = "--:--"
            size_str = "0 B"
            if info:
                t = []
                if info['has_video']: t.append("Vid")
                if info['has_audio']: t.append("Aud")
                type_str = "+".join(t)
                dur_str = self._fmt_dur(info['duration'])
                size_str = self._fmt_size(info.get('size', 0))
                
            self.tree.insert("", "end", values=(i+1, name, type_str, dur_str, size_str))

    def _fmt_dur(self, s):
        m, sec = divmod(s, 60)
        h, m = divmod(m, 60)
        if h > 0: return f"{int(h)}:{int(m):02d}:{int(sec):02d}"
        return f"{int(m):02d}:{int(sec):02d}"
        
    def _fmt_size(self, size_bytes):
        if size_bytes < 1024: return f"{size_bytes} B"
        elif size_bytes < 1024**2: return f"{size_bytes/1024:.2f} KB"
        elif size_bytes < 1024**3: return f"{size_bytes/(1024**2):.2f} MB"
        else: return f"{size_bytes/(1024**3):.2f} GB"

    def _on_mode_change(self):
        mode = self.var_mode.get()
        current_name = self.entry_out_name.get()
        base, _ = os.path.splitext(current_name)
        if not base: base = "merged_output"
        
        if mode == "video":
            self.entry_out_name.delete(0, tk.END)
            self.entry_out_name.insert(0, base + ".mp4")
        else:
            self.entry_out_name.delete(0, tk.END)
            self.entry_out_name.insert(0, base + ".mp3")

    def _cancel_merge(self):
        self.logic.cancel()
        self.log("🛑 Cancel requested...")

    def _start_merge(self):
        if not self.files_queue:
            self.log("⚠️ Queue is empty.")
            self.log("-"*80, replace=False)
            return

        folder = self.entry_out_folder.get().strip()
        if not folder:
            folder = os.path.join(os.getcwd(), '_output\\merged')
            if not os.path.exists(folder):
                try: os.makedirs(folder)
                except: pass
                
            # Легендарная автоматическая вставка
            self.entry_out_folder.delete(0, tk.END)
            self.entry_out_folder.insert(0, folder)
            
        name = self.entry_out_name.get().strip()
        
        if not name:
            self.log("⚠️ Please specify output name.")
            self.log("-"*80, replace=False)
            return

        full_out_path = os.path.join(folder, name)
        
        # Проверяем, не совпадает ли выходной файл с одним из входных
        abs_out = os.path.abspath(full_out_path)
        for f in self.files_queue:
            if os.path.abspath(f) == abs_out:
                if self.var_overwrite.get():
                    self.log(f"""❌ Critical Error
    You cannot overwrite a source file while reading from it!
    Conflict with input file: {os.path.basename(f)}
    Please change the Output Name.""")
                    self.log("-" * 80, replace=False)
                    return
        
        
        params = {
            'files': self.files_queue,
            'output_path': full_out_path,
            'mode': self.var_mode.get(),
            'overwrite': self.var_overwrite.get(),
            'fps': self.cb_fps.get(),
            'resolution': self.cb_res.get(),
            'crf': self.spin_crf.get(),
            'bg_image': self.entry_bg.get().strip()
        }
        
        self.run_async(self.logic.run_merge, params)