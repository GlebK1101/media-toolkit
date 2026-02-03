# src/tabs/editor_tab.py
import tkinter as tk
from tkinter import ttk, filedialog
import os
import math
import numpy as np
import time

from tabs.base_tab import BaseTab
from core.editor_logic import EditorLogic

class EditorTab(BaseTab):
    def __init__(self, parent):
        super().__init__(parent)
        self.logic = EditorLogic(self.log)
        self.current_file = None
        
        # --- Audio Data ---
        self.duration = 0.0
        self.waveform_data = np.array([])
        self.sample_rate = 10000 
        
        # --- View State ---
        self.zoom_level = 50.0
        self.view_offset_x = -50.0
        self.side_margin = 50
        
        # --- Selection State ---
        self.sel_start = 0.0
        self.sel_end = 0.0
        
        # --- Playback State ---
        self.is_playing = False
        self.is_paused = False  
        self.playhead_time = -1.0 
        self.playback_anchor_start = 0.0
        self.playback_anchor_end = 0.0
        self.playback_start_realtime = 0.0
        
        # --- Interaction ---
        self.last_mouse_x = 0
        self.drag_mode = None 
        
        self.setup_ui()

    def setup_ui(self):
        # FILE INPUT
        top_frame = ttk.Frame(self.main_container)
        top_frame.pack(side="top", fill="x", padx=10, pady=10)
        
        ttk.Label(top_frame, text="Audio/Video File:").pack(side="left")
        self.entry_path = ttk.Entry(top_frame)
        self.entry_path.pack(side="left", fill="x", expand=True, padx=5)
        
        self.create_icon_button(top_frame, "📂", self._select_file).pack(side="left", padx=1)
        self.create_icon_button(top_frame, "📋", lambda: (self.clear_entry(self.entry_path), self.paste_to_entry(self.entry_path))).pack(side="left", padx=1)
        self.create_icon_button(top_frame, "❌", lambda: self.clear_entry(self.entry_path)).pack(side="left", padx=1)
        self.create_icon_button(top_frame, "📑", lambda: self.copy_from_entry(self.entry_path)).pack(side="left", padx=1)
        ttk.Button(top_frame, text="LOAD", command=self._load_file, width=8).pack(side="left", padx=(5, 0))

        # VISUALIZATION
        self.viz_frame = ttk.Labelframe(self.main_container, text=" Waveform ", padding=2)
        self.viz_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(self.viz_frame, bg="#1e1e1e", height=220, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bindings
        self.canvas.bind("<Configure>", self._draw)
        self.canvas.bind("<Motion>", self._on_hover)
        
        self.canvas.bind("<ButtonPress-1>", self._on_lmb_down)
        self.canvas.bind("<B1-Motion>", self._on_lmb_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_lmb_up)
        
        self.canvas.bind("<MouseWheel>", self._on_zoom)
        self.canvas.bind("<Button-4>", self._on_zoom)
        self.canvas.bind("<Button-5>", self._on_zoom)
        
        self.canvas.bind("<ButtonPress-3>", self._start_pan)
        self.canvas.bind("<B3-Motion>", self._do_pan)
        self.canvas.bind("<ButtonRelease-3>", self._end_pan)

        # INFO LABELS
        info_frame = ttk.Frame(self.viz_frame)
        info_frame.pack(fill="x", pady=(2, 0))
        
        self.lbl_sel_start = ttk.Label(info_frame, text="Start: 00:00.00", width=18)
        self.lbl_sel_start.pack(side="left", padx=5)
        self.lbl_sel_end = ttk.Label(info_frame, text="End: 00:00.00", width=18)
        self.lbl_sel_end.pack(side="left", padx=5)
        self.lbl_sel_len = ttk.Label(info_frame, text="Len: 00:00.00", width=18, foreground="#0078d7")
        self.lbl_sel_len.pack(side="left", padx=5)
        
        self.lbl_curr_time = ttk.Label(info_frame, text="Now: --:--.--", width=18, foreground="#00aaff")
        self.lbl_curr_time.pack(side="left", padx=5)
        
        self.lbl_cursor = ttk.Label(info_frame, text="Cursor: --", font=("Consolas", 9))
        self.lbl_cursor.pack(side="right", padx=5)

        # BOTTOM: CONTROLS & EXPORT
        self.ctrl_frame = ttk.Frame(self.main_container)
        self.ctrl_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # --- Playback & Volume Controls ---
        p_frame = ttk.Labelframe(self.ctrl_frame, text=" Controls ", padding=5)
        p_frame.pack(side="left", fill="both", expand=True, padx=(0, 5))
        
        # Upper Row: Playback
        btn_box = ttk.Frame(p_frame)
        btn_box.pack(fill="x", pady=2)
        ttk.Button(btn_box, text="▶ PLAY", command=self._play_preview, width=8).pack(side="left", padx=2)
        ttk.Button(btn_box, text="⏸ PAUSE", command=self._toggle_pause, width=10).pack(side="left", padx=2)
        ttk.Button(btn_box, text="⏹ STOP", command=self._stop_preview, width=8).pack(side="left", padx=2)
        
        self.var_loop = tk.BooleanVar(value=False)
        ttk.Checkbutton(btn_box, text="Loop", variable=self.var_loop).pack(side="left", padx=10)
        
        ttk.Label(btn_box, text="Start:").pack(side="left", padx=(10, 2))
        self.entry_manual_start = ttk.Entry(btn_box, width=12)
        self.entry_manual_start.pack(side="left", padx=2)
        self.entry_manual_start.bind('<Return>', self._on_manual_time_change)
        self.entry_manual_start.bind('<FocusOut>', self._on_manual_time_change)

        ttk.Label(btn_box, text="End:").pack(side="left", padx=(5, 2))
        self.entry_manual_end = ttk.Entry(btn_box, width=12)
        self.entry_manual_end.pack(side="left", padx=2)
        self.entry_manual_end.bind('<Return>', self._on_manual_time_change)
        self.entry_manual_end.bind('<FocusOut>', self._on_manual_time_change)
        
        ttk.Button(btn_box, text="Reset Range", command=self._reset_selection).pack(side="right", padx=5)

        # Lower Row: Volume
        sl_box = ttk.Frame(p_frame)
        sl_box.pack(fill="x", pady=5)
        
        f_vol = ttk.Frame(sl_box)
        f_vol.pack(side="left", fill="x", expand=True)
        
        ttk.Label(f_vol, text="Volume:").pack(side="left")
        
        self.scale_vol = ttk.Scale(f_vol, from_=0.0, to=2.0, value=1.0, command=self._on_scale_move)
        self.scale_vol.pack(side="left", fill="x", expand=True, padx=5)
        
        self.entry_vol = ttk.Entry(f_vol, width=6)
        self.entry_vol.insert(0, "1.00")
        self.entry_vol.pack(side="left")
        self.entry_vol.bind('<Return>', self._on_entry_enter)
        
        ttk.Button(f_vol, text="↺", width=3, command=self._reset_volume).pack(side="left", padx=2)
        self.var_apply_vol = tk.BooleanVar(value=False)
        ttk.Checkbutton(f_vol, text="Apply to Export", variable=self.var_apply_vol).pack(side="left", padx=10)

        # --- Export Controls ---
        exp_frame = ttk.Labelframe(self.ctrl_frame, text=" Export ", padding=5)
        exp_frame.pack(side="right", fill="both", expand=True, padx=(5, 0))
        
        # Name
        ef1 = ttk.Frame(exp_frame)
        ef1.pack(fill="x", pady=2)
        ttk.Label(ef1, text="Name:", width=6).pack(side="left")
        self.entry_out_name = ttk.Entry(ef1)
        self.entry_out_name.pack(side="left", fill="x", expand=True, padx=5)
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


        # Save and cancel
        ef3 = ttk.Frame(exp_frame)
        ef3.pack(fill="x", pady=5)
        self.var_overwrite = tk.BooleanVar(value=False)
        ttk.Checkbutton(ef3, text="Overwrite", variable=self.var_overwrite).pack(side="right", padx=5)
        ttk.Button(ef3, text="🚫 CANCEL", command=self._cancel_cut).pack(side="right", padx=5)
        ttk.Button(ef3, text="💾 SAVE CUT", command=self._save_cut).pack(side="right", padx=5)
        
        
        
    # ================= UTILS: TIME FORMATTING =================
    def _format_time(self, seconds, force_format=None):
        if seconds < 0: seconds = 0
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        
        show_hours = (self.duration >= 3600)
        
        if show_hours or h > 0:
            return f"{int(h):d}:{int(m):02d}:{s:06.3f}"
        else:
            return f"{int(m):02d}:{s:06.3f}"

    
    def _parse_input_time(self, time_str):
        try:
            parts = time_str.split(':')
            if len(parts) == 3: # HH:MM:SS
                return int(parts[0])*3600 + int(parts[1])*60 + float(parts[2])
            elif len(parts) == 2: # MM:SS
                return int(parts[0])*60 + float(parts[1])
            else: # SS
                return float(parts[0])
        except:
            return -1.0

    def _on_manual_time_change(self, event=None):
        s_str = self.entry_manual_start.get()
        e_str = self.entry_manual_end.get()
        
        s_val = self._parse_input_time(s_str)
        e_val = self._parse_input_time(e_str)
        
        # Если ввод некорректный, возвращаем старые значения
        if s_val < 0 or e_val < 0:
            self._update_info() 
            return

        # Валидация границ
        if s_val > self.duration: s_val = self.duration
        if e_val > self.duration: e_val = self.duration
        if s_val > e_val: s_val = e_val 
        
        self.sel_start = s_val
        self.sel_end = e_val
        
        self._update_info(update_entries=False) # Не обновляем поля, так как мы в них пишем
        self._draw()
    
    
    
    
    
    def _on_scale_move(self, val):
        v = float(val)
        self.entry_vol.delete(0, tk.END)
        self.entry_vol.insert(0, f"{v:.2f}")

    def _on_entry_enter(self, event):
        try:
            val = float(self.entry_vol.get())
            val = max(0.0, min(val, 2.0))
            self.scale_vol.set(val)
            self.entry_vol.delete(0, tk.END)
            self.entry_vol.insert(0, f"{val:.2f}")
        except:
            pass

    def _reset_volume(self):
        self.scale_vol.set(1.0)
        self.entry_vol.delete(0, tk.END)
        self.entry_vol.insert(0, "1.00")

    # ================= LOGIC: LOADING =================
    def _select_file(self):
        f = filedialog.askopenfilename()
        if f:
            self.entry_path.delete(0, tk.END)
            self.entry_path.insert(0, f)

    def _load_file(self):
        self._stop_preview()

        path = self.entry_path.get().strip()
        if not path or not os.path.exists(path):
            self.log("❌ Error: File not found.")
            self.log("-"*80, replace=False)
            return
        
        self.current_file = path
        self.canvas.delete("all")
        self.canvas.create_text(self.canvas.winfo_width()//2, 100, text="Analyzing waveform...", fill="white")
        
        self.run_async(self._async_load, path)

    def _async_load(self, path):
        data, dur = self.logic.get_waveform_exact(path)
        self.after(0, lambda: self._on_loaded(dur, data))

    def _on_loaded(self, dur, data):
        self.duration = dur
        self.waveform_data = data
        self.sel_start = 0.0
        self.sel_end = dur
        self.playhead_time = -1.0
        self.is_paused = False
        
        w = self.canvas.winfo_width()
        avail = w - (self.side_margin * 2)
        if avail <= 0: avail = 100
        
        self.zoom_level = avail / dur
        self.view_offset_x = -self.side_margin
        
        dir_name = os.path.dirname(self.current_file)
        base = os.path.basename(self.current_file)
        name, ext = os.path.splitext(base)
        
        self.entry_out_folder.delete(0, tk.END)
        self.entry_out_folder.insert(0, dir_name)
        self.entry_out_name.delete(0, tk.END)
        self.entry_out_name.insert(0, f"{name}_cut{ext}")
        
        self._update_info()
        self._draw()
        self.log(f"Loaded: {base} ({self._format_time(dur)})")

    # ================= LOGIC: DRAWING =================
    def _time_to_x(self, t):
        return (t * self.zoom_level) - self.view_offset_x

    def _x_to_time(self, x):
        return (x + self.view_offset_x) / self.zoom_level

    def _draw(self, event=None):
        if len(self.waveform_data) == 0: return

        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        ruler_h = 30
        wave_h = h - ruler_h
        cy = wave_h / 2
        
        x_track_start = self._time_to_x(0)
        x_track_end = self._time_to_x(self.duration)
        
        # Draw track background
        self.canvas.create_rectangle(x_track_start, 0, x_track_end, wave_h, fill="#252525", outline="")
        
        start_x = max(0, int(x_track_start))
        end_x = min(w, int(x_track_end))
        
        if end_x > start_x:
            samples_per_pixel = self.sample_rate / self.zoom_level
            for x in range(start_x, end_x):
                t_start = self._x_to_time(x)
                if t_start < 0: continue
                if t_start > self.duration: break
                
                idx_start = int(t_start * self.sample_rate)
                
                if samples_per_pixel >= 1.0:
                    idx_end = int(idx_start + samples_per_pixel)
                    if idx_start >= len(self.waveform_data): break
                    if idx_end > len(self.waveform_data): idx_end = len(self.waveform_data)
                    
                    if idx_end > idx_start:
                        chunk = self.waveform_data[idx_start:idx_end]
                        val = np.max(chunk) if len(chunk) > 0 else 0
                    else:
                        val = self.waveform_data[idx_start]
                else:
                    if idx_start < len(self.waveform_data):
                        val = self.waveform_data[idx_start]
                    else:
                        val = 0
                
                if val > 0:
                    h_bar = val * (wave_h * 0.9)
                    self.canvas.create_line(x, cy - h_bar/2, x, cy + h_bar/2, fill="#00aaff", width=1)

        x_sel_start = self._time_to_x(self.sel_start)
        x_sel_end = self._time_to_x(self.sel_end)
        
        # Left darkening area: From Track Start to Selection Start
        left_dark_start = max(x_track_start, -10000) # -10000 to catch panning
        left_dark_end = x_sel_start
        # Clamp to visible window for performance/logic
        if left_dark_end > 0 and x_track_start < w:
            # Draw only if there is an intersection
            d_x1 = max(left_dark_start, 0) # Clip to screen left
            d_x2 = min(left_dark_end, w)   # Clip to screen right
            
            # Ensure we don't draw if the track hasn't started yet or selection is before track
            real_x1 = max(d_x1, x_track_start)
            
            if d_x2 > real_x1:
                self.canvas.create_rectangle(real_x1, 0, d_x2, wave_h, fill="black", stipple="gray50", width=0)

        # Right darkening area: From Selection End to Track End
        right_dark_start = x_sel_end
        right_dark_end = x_track_end
        if right_dark_start < w and right_dark_end > 0:
            d_x1 = max(right_dark_start, 0)
            d_x2 = min(right_dark_end, w)
            
            if d_x2 > d_x1:
                self.canvas.create_rectangle(d_x1, 0, d_x2, wave_h, fill="black", stipple="gray50", width=0)

        # Draw Selection Lines
        if -10 < x_sel_start < w+10:
            self.canvas.create_line(x_sel_start, 0, x_sel_start, wave_h, fill="#00ff00", width=2)
            self.canvas.create_polygon(x_sel_start, 0, x_sel_start+8, 0, x_sel_start, 10, fill="#00ff00")
        
        if -10 < x_sel_end < w+10:
            self.canvas.create_line(x_sel_end, 0, x_sel_end, wave_h, fill="#ff3333", width=2)
            self.canvas.create_polygon(x_sel_end, wave_h, x_sel_end-8, wave_h, x_sel_end, wave_h-10, fill="#ff3333")
    
        if self.is_playing or self.is_paused:
            x_ghost = self._time_to_x(self.playback_anchor_end)
            # Рисуем только если она не совпадает с красной линией (с небольшим допуском)
            if abs(x_ghost - x_sel_end) > 2:
                if -10 < x_ghost < w+10:
                    self.canvas.create_line(x_ghost, 0, x_ghost, wave_h, fill="#aa00ff", width=2, dash=(4, 2))
                    # Маленький маркер сверху
                    self.canvas.create_polygon(x_ghost, 0, x_ghost+6, 0, x_ghost, 6, fill="#aa00ff")
        
        # Playhead
        if self.playhead_time >= 0:
            xp = self._time_to_x(self.playhead_time)
            if 0 <= xp <= w:
                self.canvas.create_line(xp, 0, xp, h, fill="white", width=2)
            
            self.lbl_curr_time.config(text=f"Now: {self._format_time(self.playhead_time)}")
        else:
             self.lbl_curr_time.config(text=f"Now: --:--.--")

        self._draw_ruler(w, h, ruler_h)

    def _draw_ruler(self, w, h, rh):
        self.canvas.create_rectangle(0, h-rh, w, h, fill="#333333", outline="")
        target_step = 100
        step_sec = target_step / self.zoom_level
        
        if step_sec < 0.001: rstep = 0.001
        elif step_sec < 0.01: rstep = 0.01
        elif step_sec < 0.1: rstep = 0.1
        elif step_sec < 1.0: rstep = 1.0
        elif step_sec < 5.0: rstep = 5.0
        elif step_sec < 10.0: rstep = 10.0
        else: rstep = 30.0
        
        start_t = self._x_to_time(0)
        t = math.floor(start_t / rstep) * rstep
        end_t = self._x_to_time(w)
        
        while t <= end_t:
            x = self._time_to_x(t)
            self.canvas.create_line(x, h-rh, x, h, fill="#888888")
            
            txt = self._format_time(t)
            
            self.canvas.create_text(x+3, h-rh+5, text=txt, anchor="nw", fill="#ccc", font=("Arial", 8))
            t += rstep

    # ================= INTERACTION =================
    
    def _clamp_view(self):
        min_off = -self.side_margin
        w = self.canvas.winfo_width()
        max_off = (self.duration * self.zoom_level) - w + self.side_margin
        if max_off < min_off: self.view_offset_x = min_off
        else: self.view_offset_x = max(min_off, min(self.view_offset_x, max_off))

    def _on_zoom(self, event):
        if self.duration == 0: return
        mouse_time = self._x_to_time(event.x)
        scale = 1.1
        if (event.num == 5) or (event.delta < 0): self.zoom_level /= scale
        else: self.zoom_level *= scale
        
        w = self.canvas.winfo_width()
        min_zoom = (w - self.side_margin*2) / self.duration
        self.zoom_level = max(min_zoom, min(self.zoom_level, 50000.0))
        
        self.view_offset_x = (mouse_time * self.zoom_level) - event.x
        self._clamp_view()
        self._draw()

    def _start_pan(self, event):
        self.drag_mode = 'pan'
        self.last_mouse_x = event.x
        self.canvas.config(cursor="fleur")

    def _do_pan(self, event):
        if self.drag_mode == 'pan':
            dx = event.x - self.last_mouse_x
            self.view_offset_x -= dx
            self.last_mouse_x = event.x
            self._clamp_view()
            self._draw()

    def _end_pan(self, event):
        self.drag_mode = None
        self.canvas.config(cursor="")

    def _on_lmb_down(self, event):
        x = event.x
        x_s = self._time_to_x(self.sel_start)
        x_e = self._time_to_x(self.sel_end)
        tol = 10
        if abs(x - x_s) < tol: self.drag_mode = 'start'
        elif abs(x - x_e) < tol: self.drag_mode = 'end'
        else: self.drag_mode = None

    def _on_lmb_drag(self, event):
        if not self.drag_mode: return
        t = self._x_to_time(event.x)
        t = max(0, min(t, self.duration))
        
        if self.drag_mode == 'start':
            if t < self.sel_end - 0.01: self.sel_start = t
        elif self.drag_mode == 'end':
            if t > self.sel_start + 0.01: self.sel_end = t
        self._update_info()
        self._draw()

    def _on_lmb_up(self, event):
        self.drag_mode = None

    def _on_hover(self, event):
        if self.duration > 0:
            t = self._x_to_time(event.x)
            t = max(0, min(t, self.duration))
            self.lbl_cursor.config(text=f"Cursor: {self._format_time(t)}")

    def _update_info(self, update_entries=True):
        self.lbl_sel_start.config(text=f"Start: {self._format_time(self.sel_start)}")
        self.lbl_sel_end.config(text=f"End:   {self._format_time(self.sel_end)}")
        self.lbl_sel_len.config(text=f"Len:   {self._format_time(self.sel_end - self.sel_start)}")
        
        if update_entries:
            self.entry_manual_start.delete(0, tk.END)
            self.entry_manual_start.insert(0, self._format_time(self.sel_start))
            
            self.entry_manual_end.delete(0, tk.END)
            self.entry_manual_end.insert(0, self._format_time(self.sel_end))

    # ================= PLAYBACK =================
    def _toggle_pause(self):
        if self.is_playing:
            self._pause_preview()
        elif self.is_paused:
            self._play_preview()
        
    def _pause_preview(self):
        if not self.is_playing: return
        # Stop the actual process but keep the UI state
        self.is_playing = False
        self.is_paused = True
        self.logic.stop_preview()
        # Playhead time is preserved in self.playhead_time
        self.log(f"ℹ️Paused at {self._format_time(self.playhead_time)}")

    def _play_preview(self):
        if not self.current_file: return
        
        if self.is_paused and self.playhead_time >= 0:
            start_time = self.playhead_time
        else:
            self._stop_preview() 
            start_time = self.sel_start
        
        try: vol = float(self.entry_vol.get())
        except: vol = 1.0
        
        self.is_playing = True
        self.is_paused = False
        
        self.playback_anchor_start = start_time
        self.playback_anchor_end = self.sel_end 
        self.playback_start_realtime = time.time()
        
        # Если мы возобновляем почти в конце, сбрасываем в начало
        if start_time >= self.playback_anchor_end:
            start_time = self.sel_start
            self.playback_anchor_start = start_time
            self.playback_anchor_end = self.sel_end
            self.playback_start_realtime = time.time()

        self.logic.start_preview(
            self.current_file, start_time, self.playback_anchor_end,
            volume=vol, loop=self.var_loop.get()
        )
        self._playback_loop()

    def _playback_loop(self):
        if not self.is_playing: return
        
        elapsed_real = time.time() - self.playback_start_realtime
        curr = self.playback_anchor_start + elapsed_real
        
        if curr > self.playback_anchor_end:
            if self.var_loop.get():
                # Полностью перезапускаем превью, чтобы ffplay запустился заново и был звук
                self._play_preview() 
                return
            else:
                self._stop_preview()
                return
        
        self.playhead_time = curr
        
        # --- Auto-Scroll Logic ---
        w = self.canvas.winfo_width()
        view_end_t = self._x_to_time(w)
        
        if self.playhead_time > view_end_t:
            self.view_offset_x = (self.playhead_time * self.zoom_level) - self.side_margin
            self._clamp_view()

        self._draw()
        self.after(30, self._playback_loop)

    def _stop_preview(self):
        self.is_playing = False
        self.is_paused = False 
        self.logic.stop_preview()
        self.playhead_time = -1.0
        self._draw()

    def _reset_selection(self):
        self.sel_start = 0.0
        self.sel_end = self.duration
        
        w = self.canvas.winfo_width()
        avail = w - (self.side_margin * 2)
        if avail <= 0: avail = 100
        
        if self.duration > 0:
            self.zoom_level = avail / self.duration
        self.view_offset_x = -self.side_margin
        
        self._update_info()
        self._draw()

    # ================= EXPORT =================
    def _save_cut(self):
        if not self.current_file: return
        folder = self.entry_out_folder.get().strip()
        name = self.entry_out_name.get().strip()
        if not folder or not name: return
        
        full_out_path = os.path.join(folder, name)
        
        # Проверяем, пытаемся ли мы перезаписать САМ ЖЕ исходный файл
        if os.path.abspath(self.current_file) == os.path.abspath(full_out_path):
            if self.var_overwrite.get():
                self.log("""❌ Critical Error
    You cannot overwrite the source file while reading from it!
    "FFmpeg cannot read and write to the same file simultaneously.
    Please change the Output Name.""")
                self.log("-"*80+"\n", replace=False)
                return
        
        if self.var_apply_vol.get():
            try: vol = float(self.entry_vol.get())
            except: vol = 1.0
        else:
            vol = 1.0
        
        params = {
            'input_path': self.current_file,
            'output_path': os.path.join(folder, name),
            'start': self.sel_start,
            'end': self.sel_end,
            'volume': vol,
            'overwrite': self.var_overwrite.get()
        }
        self.run_async(self.logic.run_cut, params)
        
    def _cancel_cut(self):
        self.logic.cancel()
        