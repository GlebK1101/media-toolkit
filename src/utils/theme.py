import tkinter as tk
from tkinter import ttk

class AppTheme:
    @staticmethod
    def apply_theme(root):
        style = ttk.Style(root)
        style.theme_use('clam')

        # Colors
        bg_color = "#f8f9fa"
        fg_color = "#202020"
        accent_color = "#0078d7"
        btn_fg_color = "#ffffff"
        input_bg = "#ffffff"
        
        root.configure(background=bg_color)

        # Global settings
        style.configure(".", 
                        background=bg_color, 
                        foreground=fg_color, 
                        borderwidth=0, 
                        font=("Segoe UI", 10))

        #  Notebook (Tabs)
        style.configure("TNotebook", background=bg_color, borderwidth=0, padding=0)
        style.configure("TNotebook.Tab", 
                        background="#e0e0e0", 
                        foreground=fg_color, 
                        padding=[15, 5], 
                        borderwidth=0)
        style.map("TNotebook.Tab", 
                  background=[("selected", bg_color)], 
                  foreground=[("selected", accent_color)])

        # Frames
        style.configure("TFrame", background=bg_color, borderwidth=0)

        # Buttons
        style.configure("TButton",
                        background=accent_color,
                        foreground=btn_fg_color,
                        relief="flat",
                        borderwidth=0,
                        padding=6)
        style.map("TButton", background=[('active', "#005a9e")])

        # Icon Buttons
        style.configure("Icon.TButton",
                        background="#e9ecef",
                        foreground="#000000",
                        padding=2,
                        width=3)
        style.map("Icon.TButton", background=[('active', "#ced4da")])

        # Entry
        style.configure("TEntry", 
                        fieldbackground=input_bg,
                        foreground=fg_color,
                        borderwidth=1,
                        relief="solid",
                        bordercolor="#ced4da")
        
        # Combobox
        style.map('TCombobox', 
                  fieldbackground=[('readonly', input_bg)], 
                  selectbackground=[('readonly', input_bg)], 
                  selectforeground=[('readonly', fg_color)])
        
        return style