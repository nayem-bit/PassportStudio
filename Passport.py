import cv2
import os
import sys
import numpy as np
import tkinter as tk
from tkinter import ttk
from tkinter import Label, Button, Scale, Checkbutton, IntVar, Spinbox, filedialog, messagebox
from tkinter import colorchooser
from PIL import Image, ImageTk
from rembg import remove
from fpdf import FPDF
import webbrowser
import threading
import queue
import math
from tkinterdnd2 import TkinterDnD, DND_FILES
import subprocess
import tempfile

APP_NAME = "Passport Photo Maker Studio"
APP_VERSION = "1.0"
APP_BG = "#e0e0e0"
FRAME_BG = "#f0f0f0"
BUTTON_BG = "#d0d0d0"
ACCENT_COLOR = "#0078d4"
TEXT_COLOR = "#1c1c1c"
ERROR_COLOR = "red"
PASSPORT_SIZE_PX = (413, 531)
APP_SIZE_200_PX = (200, 200)
APP_SIZE_300_PX = (300, 300)
STAMP_SIZE_PX = (236, 295)
PDF_DPI = 300
HAAR_CASCADE_FILE = 'haarcascade_frontalface_default.xml'
LOGO_FILE_PNG = 'icon.png'
ICON_FILE_ICO = 'icon.ico'

PREDEFINED_COLORS_RGB = {
    "White": (255, 255, 255),
    "Off-White": (245, 245, 245),
    "Light Grey": (220, 220, 220),
    "Light Blue": (173, 216, 230),
    "Sky Blue": (135, 206, 235),
    "Royal Blue": (65, 105, 225),
}
DEFAULT_BG_COLOR_RGB = PREDEFINED_COLORS_RGB["Royal Blue"]

PAGE_SIZES_MM = {
    "A4": (210, 297),
    "Letter": (215.9, 279.4),
    "4R": (101.6, 152.4),
    "5R": (127, 177.8),
    "6R": (152.4, 203.2),
    "8R": (203.2, 254),
    "2R": (63.5, 88.9),
    "3R": (88.9, 127),
}
DEFAULT_PAGE_SIZE = "A4"
DEFAULT_PHOTO_COUNT = 4

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

class PassportPhoto:
    def __init__(self, master):
        self.master = master
        master.title(f"{APP_NAME} | V{APP_VERSION}")
        master.geometry("760x600")
        master.config(bg=APP_BG)
        master.minsize(700, 550)

        self.set_window_icon()

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('App.TFrame', background=FRAME_BG)
        style.configure('TLabel', background=FRAME_BG, foreground=TEXT_COLOR, font=('Segoe UI', 10))
        style.configure('TButton', background=BUTTON_BG, foreground=TEXT_COLOR, font=('Segoe UI', 10, 'bold'), padding=6)
        style.map('TButton', background=[('active', ACCENT_COLOR), ('disabled', '#cccccc')], foreground=[('active', 'white'), ('disabled', '#888888')])
        style.configure('TCheckbutton', background=FRAME_BG, foreground=TEXT_COLOR, font=('Segoe UI', 10))
        style.map('TCheckbutton', indicatorcolor=[('selected', ACCENT_COLOR)], background=[('active', FRAME_BG)])
        style.configure('Horizontal.TScale', background=FRAME_BG)
        style.configure('Link.TLabel', foreground="blue", font=('Segoe UI', 9, 'underline'))
        style.configure('Header.TLabel', font=('Segoe UI', 12, 'bold'))
        style.configure('SubHeader.TLabel', font=('Segoe UI', 10, 'bold'))
        style.configure('Status.TLabel', font=('Segoe UI', 9))
        style.configure('Error.Status.TLabel', font=('Segoe UI', 9), foreground=ERROR_COLOR)
        style.configure('Custom.Horizontal.TProgressbar', troughcolor='#e0e0e0', background=ACCENT_COLOR, thickness=15)
        style.configure('TCombobox', font=('Segoe UI', 10), padding=3)
        master.option_add('*TCombobox*Listbox.font', ('Segoe UI', 10))
        master.option_add('*TCombobox*Listbox.selectBackground', ACCENT_COLOR)
        master.option_add('*TCombobox*Listbox.selectForeground', 'white')
        style.configure('TSpinbox', font=('Segoe UI', 10), padding=3)

        self.output_frame = ttk.Frame(master, padding=10, style='App.TFrame')
        self.output_frame.grid(row=0, column=0, padx=(10, 5), pady=10, sticky="nsew")

        self.controls_frame = ttk.Frame(master, padding=(10,0,10,10), style='App.TFrame')
        self.controls_frame.grid(row=0, column=1, padx=(5, 10), pady=10, sticky="nsew")

        master.rowconfigure(0, weight=1)
        master.columnconfigure(0, weight=1, minsize=350)
        master.columnconfigure(1, weight=0, minsize=390)

        self.output_title_label = ttk.Label(self.output_frame, text="Image Preview:", style='Header.TLabel')
        self.output_title_label.pack(pady=(0, 10), anchor='nw')

        self.image_display_frame = ttk.Frame(self.output_frame, relief="sunken", borderwidth=1, style='App.TFrame', cursor="hand2")
        self.image_display_frame.pack(expand=True, fill="both", padx=5, pady=5)
        self.image_display_frame.pack_propagate(False)

        self.output_image_label = ttk.Label(self.image_display_frame, text="Click or Drop Image Here", anchor="center", style='TLabel', cursor="hand2")
        self.output_image_label.pack(expand=True, fill="both")

        self.output_image_label.bind("<Button-1>", self.load_image)
        self.image_display_frame.bind("<Button-1>", self.load_image)

        self.output_image_label.drop_target_register(DND_FILES)
        self.output_image_label.dnd_bind('<<Drop>>', self.on_drop)
        self.image_display_frame.drop_target_register(DND_FILES)
        self.image_display_frame.dnd_bind('<<Drop>>', self.on_drop)

        self.status_frame = ttk.Frame(self.output_frame, style='App.TFrame')
        self.status_frame.pack(fill="x", padx=5, pady=(10, 5), side='bottom')

        self.progress_label = ttk.Label(self.status_frame, text="Status: Idle", anchor="w", style='Status.TLabel')
        self.progress_label.pack(fill="x", expand=True)

        self.progress_bar = ttk.Progressbar(self.status_frame, orient='horizontal', mode='determinate', length=250, style='Custom.Horizontal.TProgressbar')
        self.progress_bar.pack(fill="x", expand=True, pady=(5, 0))


        self.options_label = ttk.Label(self.controls_frame, text="Processing Options:", style='SubHeader.TLabel')
        self.options_label.grid(row=1, column=0, columnspan=2, padx=5, pady=(5, 5), sticky="w")

        self.remove_bg_var = tk.IntVar(value=1)
        self.remove_bg_check = ttk.Checkbutton(self.controls_frame, text="Remove Background", variable=self.remove_bg_var)
        self.remove_bg_check.grid(row=2, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        self.bg_color_label = ttk.Label(self.controls_frame, text="Background Color:")
        self.bg_color_label.grid(row=3, column=0, padx=(5,2), pady=2, sticky="w")

        self.current_color_label = ttk.Label(self.controls_frame, text="  ", background="#%02x%02x%02x" % DEFAULT_BG_COLOR_RGB, relief="sunken", borderwidth=1, cursor="hand2")
        self.current_color_label.grid(row=3, column=1, padx=(0, 5), pady=2, sticky="w")
        self.current_color_label.bind("<Button-1>", lambda e: self.open_color_picker())

        self.denoise_var = tk.IntVar(value=0)
        self.denoise_check = ttk.Checkbutton(self.controls_frame, text="Remove Grain / Denoise", variable=self.denoise_var, command=self.toggle_denoise_slider)
        self.denoise_check.grid(row=4, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        self.denoise_level_label = ttk.Label(self.controls_frame, text="Denoise Level:")
        self.denoise_level_var = tk.IntVar(value=3)
        self.denoise_level_slider = ttk.Scale(self.controls_frame, from_=1, to=10, orient="horizontal", variable=self.denoise_level_var, command=lambda v: self.denoise_level_var.set(int(float(v))))

        self.scale_label = ttk.Label(self.controls_frame, text="Upscale Level (1x-8x):")
        self.scale_label.grid(row=6, column=0, padx=5, pady=(10,0), sticky="w")
        self.scale_var = tk.IntVar(value=2)
        self.scale_slider = ttk.Scale(self.controls_frame, from_=1, to=8, orient="horizontal", variable=self.scale_var, command=lambda v: self.scale_var.set(int(float(v))))
        self.scale_slider.grid(row=7, column=0, columnspan=2, padx=5, pady=(0,10), sticky="ew")

        self.passport_size_var = tk.IntVar(value=1)
        self.passport_size_check = ttk.Checkbutton(self.controls_frame, text=f"Passport ({PASSPORT_SIZE_PX[0]}x{PASSPORT_SIZE_PX[1]}px)", variable=self.passport_size_var, command=lambda: self.handle_size_selection(self.passport_size_var))
        self.passport_size_check.grid(row=9, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        self.stamp_size_var = tk.IntVar(value=0)
        self.stamp_size_check = ttk.Checkbutton(self.controls_frame, text=f"Stamp ({STAMP_SIZE_PX[0]}x{STAMP_SIZE_PX[1]}px)", variable=self.stamp_size_var, command=lambda: self.handle_size_selection(self.stamp_size_var))
        self.stamp_size_check.grid(row=10, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        self.resize_300px_var = tk.IntVar(value=0)
        self.resize_300px_check = ttk.Checkbutton(self.controls_frame, text=f"App 300 ({APP_SIZE_300_PX[0]}x{APP_SIZE_300_PX[1]}px)", variable=self.resize_300px_var, command=lambda: self.handle_size_selection(self.resize_300px_var))
        self.resize_300px_check.grid(row=11, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        self.resize_200px_var = tk.IntVar(value=0)
        self.resize_200px_check = ttk.Checkbutton(self.controls_frame, text=f"App 200 ({APP_SIZE_200_PX[0]}x{APP_SIZE_200_PX[1]}px)", variable=self.resize_200px_var, command=lambda: self.handle_size_selection(self.resize_200px_var))
        self.resize_200px_check.grid(row=12, column=0, columnspan=2, padx=5, pady=2, sticky="w")

        self.size_vars = [self.passport_size_var, self.stamp_size_var, self.resize_300px_var, self.resize_200px_var]
        self.size_options = [
            (self.passport_size_var, PASSPORT_SIZE_PX, "Passport Size"),
            (self.stamp_size_var, STAMP_SIZE_PX, "Stamp Size"),
            (self.resize_300px_var, APP_SIZE_300_PX, "App Size 300px"),
            (self.resize_200px_var, APP_SIZE_200_PX, "App Size 200px"),
        ]

        self.pdf_num_photos_label = ttk.Label(self.controls_frame, text="Photos per Page:")
        self.pdf_num_photos_label.grid(row=14, column=0, padx=5, pady=2, sticky="w")
        self.pdf_num_photos_var = tk.IntVar(value=DEFAULT_PHOTO_COUNT)
        self.pdf_num_photos_spinbox = ttk.Spinbox(self.controls_frame, from_=1, to=48, textvariable=self.pdf_num_photos_var, width=6, wrap=True)
        self.pdf_num_photos_spinbox.grid(row=14, column=1, padx=5, pady=2, sticky="w")

        self.pdf_page_size_label = ttk.Label(self.controls_frame, text="Page Size:")
        self.pdf_page_size_label.grid(row=15, column=0, padx=5, pady=2, sticky="w")
        self.pdf_page_size_var = tk.StringVar(value=DEFAULT_PAGE_SIZE)
        page_size_names = list(PAGE_SIZES_MM.keys())
        self.pdf_page_size_combo = ttk.Combobox(self.controls_frame, textvariable=self.pdf_page_size_var, values=page_size_names, width=12, state="readonly")
        self.pdf_page_size_combo.grid(row=15, column=1, padx=5, pady=2, sticky="ew")

        self.process_button = ttk.Button(self.controls_frame, text="Process Image", command=self.start_process_thread, state="disabled")
        self.process_button.grid(row=17, column=0, columnspan=2, padx=5, pady=3, sticky="ew")

        self.save_button = ttk.Button(self.controls_frame, text="Save Processed Image", command=self.save_image, state="disabled")
        self.save_button.grid(row=18, column=0, columnspan=2, padx=5, pady=3, sticky="ew")

        self.save_pdf_button = ttk.Button(self.controls_frame, text="Save Photos to PDF", command=self.save_pdf, state="disabled")
        self.save_pdf_button.grid(row=19, column=0, columnspan=2, padx=5, pady=3, sticky="ew")

        self.copyright_label = ttk.Label(
            self.controls_frame, text=f"© Nayem Uddin Chowdhury | V{APP_VERSION}",
            style="Link.TLabel", cursor="hand2"
        )
        self.controls_frame.rowconfigure(20, weight=1)
        self.copyright_label.grid(row=21, column=0, columnspan=2, padx=5, pady=(3, 2), sticky="s")
        self.copyright_label.bind("<Button-1>", lambda e: self.open_link("https://github.com/nayem121"))

        self.controls_frame.columnconfigure(0, weight=0)
        self.controls_frame.columnconfigure(1, weight=1)

        self.face_cascade = None
        self.load_haarcascade()
        self.original_image = None
        self.original_image_bgr = None
        self.processed_image = None
        self.processing_thread = None
        self.progress_queue = queue.Queue()
        self.app_logo_tk = None

        self.background_color_rgb = DEFAULT_BG_COLOR_RGB
        self.set_background_color(self.background_color_rgb)

        self.toggle_denoise_slider()


    def set_window_icon(self):
        try:
            icon_path_ico = resource_path(ICON_FILE_ICO)
            if os.path.exists(icon_path_ico):
                try:
                    pil_icon = Image.open(icon_path_ico)
                    tk_icon = ImageTk.PhotoImage(pil_icon)
                    self.master.iconphoto(True, tk_icon)
                    self.app_logo_tk = tk_icon
                    return
                except Exception:
                    pass
        except Exception:
            pass

        try:
            icon_path_png = resource_path(LOGO_FILE_PNG)
            if os.path.exists(icon_path_png):
                 img = tk.PhotoImage(file=icon_path_png)
                 self.master.iconphoto(True, img)
                 self.app_logo_tk = img
        except Exception:
             pass


    def on_drop(self, event):
        try:
            data = event.data.strip()
            if data.startswith('{') and data.endswith('}'):
                data = data[1:-1]

            file_paths = data.split()
            file_path_to_load = None
            for potential_path in file_paths:
                if os.path.exists(potential_path):
                    file_path_to_load = potential_path
                    break

            if file_path_to_load:
                self.load_image_from_path(file_path_to_load)
            elif data:
                err_msg = f"Error: Dropped file path not found or invalid: '{data}'"
                self.update_progress(0, err_msg, is_error=True)
                messagebox.showerror("File Not Found", f"The dropped file could not be found or the path is invalid:\n{data}")
            else:
                self.update_progress(0, "Error: Invalid drop data received.", is_error=True)
        except Exception as e:
            self.update_progress(0, "Error during file drop processing.", is_error=True)
            messagebox.showerror("Drop Error", f"Could not process the dropped file(s):\n{e}")

    def load_image(self, event=None):
        file_path = filedialog.askopenfilename(
            title="Select an image file",
            filetypes=(("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"), ("All files", "*.*"))
        )
        if file_path:
            self.load_image_from_path(file_path)

    def load_image_from_path(self, file_path):
        try:
            img = cv2.imread(file_path, cv2.IMREAD_UNCHANGED)

            if img is None:
                try:
                    pil_img = Image.open(file_path)
                    if pil_img.mode == 'RGBA':
                        img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)
                    elif pil_img.mode == 'RGB':
                         img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                    elif pil_img.mode == 'L':
                         img = cv2.cvtColor(np.array(pil_img), cv2.COLOR_GRAY2BGR)
                    elif pil_img.mode == 'P':
                        pil_img_converted = pil_img.convert('RGBA')
                        img = cv2.cvtColor(np.array(pil_img_converted), cv2.COLOR_RGBA2BGRA)
                    else:
                        raise ValueError(f"Unsupported PIL image mode: {pil_img.mode}")
                except Exception as pil_err:
                    raise ValueError(f"OpenCV and PIL failed to read the image file: {os.path.basename(file_path)}. PIL Error: {pil_err}")

            if img is None:
                 raise ValueError("Image data is None after loading attempts.")

            self.original_image = img

            if len(img.shape) == 3 and img.shape[2] == 4:
                 self.original_image_bgr = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
            elif len(img.shape) == 2:
                 self.original_image_bgr = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
            elif len(img.shape) == 3 and img.shape[2] == 3:
                 self.original_image_bgr = img.copy()
            else:
                 raise ValueError(f"Unsupported image shape after loading: {img.shape}")

            self.display_image(self.original_image_bgr, self.output_image_label, parent_widget=self.image_display_frame)
            self.processed_image = None
            self.enable_processing_controls()
            self.update_progress(0, f"Loaded: {os.path.basename(file_path)}")

        except FileNotFoundError:
            error_msg = f"Error: Image file not found at '{file_path}'"
            self.update_progress(0, error_msg, is_error=True)
            messagebox.showerror("Load Error", f"File not found:\n{file_path}")
            self.disable_processing_controls()
        except ValueError as ve:
             error_msg = f"Error loading image '{os.path.basename(file_path)}': {ve}"
             self.update_progress(0, error_msg, is_error=True)
             messagebox.showerror("Load Error", f"Could not load or process the image:\n{os.path.basename(file_path)}\n\nError: {ve}")
             self.disable_processing_controls()
        except Exception as e:
            error_msg = f"An unexpected error occurred loading '{os.path.basename(file_path)}': {e}"
            self.update_progress(0, error_msg, is_error=True)
            messagebox.showerror("Load Error", f"Failed to load image:\n{os.path.basename(file_path)}\n\nUnexpected error: {e}")
            self.disable_processing_controls()

        if self.original_image_bgr is None:
            self.output_image_label.config(image='', text="Failed to load image.")
            self.output_image_label.image = None

    def toggle_denoise_slider(self):
        if self.denoise_var.get():
            self.denoise_level_label.grid(row=5, column=0, padx=5, pady=2, sticky="w")
            self.denoise_level_slider.grid(row=5, column=1, padx=5, pady=2, sticky="ew")
        else:
            self.denoise_level_label.grid_remove()
            self.denoise_level_slider.grid_remove()

    def handle_size_selection(self, selected_var):
        if selected_var.get() == 1:
            for var in self.size_vars:
                if var is not selected_var:
                    var.set(0)
        elif not any(var.get() for var in self.size_vars):
             self.passport_size_var.set(1)

    def open_link(self, url):
        try:
            webbrowser.open_new(url)
        except Exception as e:
            messagebox.showerror("Link Error", f"Could not open the link:\n{url}\nError: {e}")

    def load_haarcascade(self):
        try:
            haarcascade_path = resource_path(HAAR_CASCADE_FILE)
            if not os.path.exists(haarcascade_path):
                messagebox.showerror("Error - Missing File", f"Required face detection file not found:\n{HAAR_CASCADE_FILE}\n\nPlease ensure this file exists in the application directory or reinstall.")
                self.update_progress(0, "Error: Face detector file missing!", is_error=True)
                self.face_cascade = None
                return
            self.face_cascade = cv2.CascadeClassifier(haarcascade_path)
            if self.face_cascade.empty():
                messagebox.showerror("Error - Load Failed", f"Failed to load the face detector model from:\n{haarcascade_path}\n\nThe file might be corrupted or incompatible.")
                self.update_progress(0, "Error: Failed to load face detector!", is_error=True)
                self.face_cascade = None
        except Exception as e:
            messagebox.showerror("Error - Cascade Load", f"An unexpected error occurred while loading the face detector:\n{e}")
            self.update_progress(0, "Error loading face detector!", is_error=True)
            self.face_cascade = None

    def set_background_color(self, rgb_tuple):
        if isinstance(rgb_tuple, (list, tuple)) and len(rgb_tuple) == 3:
            self.background_color_rgb = tuple(max(0, min(255, int(c))) for c in rgb_tuple)
            hex_color = '#%02x%02x%02x' % self.background_color_rgb
            self.current_color_label.config(background=hex_color)
        else:
            self.background_color_rgb = DEFAULT_BG_COLOR_RGB
            hex_color = '#%02x%02x%02x' % self.background_color_rgb
            self.current_color_label.config(background=hex_color)


    def open_color_picker(self):
        picker_window = tk.Toplevel(self.master)
        picker_window.title("Select Background Color")
        picker_window.transient(self.master)
        picker_window.grab_set()
        picker_window.resizable(False, False)
        picker_window.config(bg=APP_BG)

        self.master.update_idletasks()
        main_x = self.master.winfo_x()
        main_y = self.master.winfo_y()
        main_w = self.master.winfo_width()
        main_h = self.master.winfo_height()
        picker_window.update_idletasks()
        picker_w = picker_window.winfo_width()
        picker_h = picker_window.winfo_height()
        x_pos = main_x + (main_w // 2) - (picker_w // 2)
        y_pos = main_y + (main_h // 2) - (picker_h // 2)
        picker_window.geometry(f"+{x_pos}+{y_pos}")


        picker_frame = ttk.Frame(picker_window, padding=15, style='App.TFrame')
        picker_frame.pack(padx=10, pady=10, expand=True, fill="both")

        ttk.Label(picker_frame, text="Predefined Colors:", style='SubHeader.TLabel').grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 10))

        row = 1
        col = 0
        max_cols_per_row = 3

        for name, rgb in PREDEFINED_COLORS_RGB.items():
            hex_color = '#%02x%02x%02x' % rgb

            swatch_frame = ttk.Frame(picker_frame, style='App.TFrame')
            swatch_frame.grid(row=row, column=col, padx=5, pady=3, sticky='ew')

            color_label = ttk.Label(swatch_frame, text=" " * 4, background=hex_color, relief="raised", borderwidth=1, style='TLabel', cursor="hand2")
            color_label.pack(side=tk.LEFT, padx=(0, 5))
            color_label.bind("<Button-1>", lambda e, c=rgb, win=picker_window: self.handle_predefined_color_click(win, c))

            name_label = ttk.Label(swatch_frame, text=name, style='TLabel')
            name_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

            col += 1
            if col >= max_cols_per_row:
                col = 0
                row += 1

        ttk.Separator(picker_frame, orient='horizontal').grid(row=row + 1, column=0, columnspan=max_cols_per_row, pady=15, sticky='ew')

        custom_button = ttk.Button(picker_frame, text="Choose Custom Color...", command=lambda: self.choose_custom_color(picker_window))
        custom_button.grid(row=row+2, column=0, columnspan=max_cols_per_row, padx=5, pady=5, sticky="ew")

        for i in range(max_cols_per_row):
             picker_frame.columnconfigure(i, weight=1)


    def handle_predefined_color_click(self, picker_toplevel, color_rgb):
        self.set_background_color(color_rgb)
        picker_toplevel.destroy()

    def choose_custom_color(self, picker_toplevel):
        initial_hex = '#%02x%02x%02x' % self.background_color_rgb
        color_code = colorchooser.askcolor(title="Choose background color", initialcolor=initial_hex, parent=picker_toplevel)

        if color_code and color_code[0] is not None:
            self.set_background_color(color_code[0])
            picker_toplevel.destroy()


    def enable_processing_controls(self):
        self.process_button.config(state="normal")
        self.save_button.config(state="disabled")
        self.save_pdf_button.config(state="disabled")

    def disable_processing_controls(self):
        self.process_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.save_pdf_button.config(state="disabled")

    def set_ui_busy(self):
        self.process_button.config(state="disabled")
        self.save_button.config(state="disabled")
        self.save_pdf_button.config(state="disabled")
        self.remove_bg_check.config(state="disabled")
        self.bg_color_label.config(state="disabled")
        self.current_color_label.config(state="disabled", cursor="")
        self.current_color_label.unbind("<Button-1>")
        self.denoise_check.config(state="disabled")
        self.denoise_level_slider.config(state="disabled")
        self.scale_slider.config(state="disabled")
        for check in [self.passport_size_check, self.stamp_size_check, self.resize_300px_check, self.resize_200px_check]:
             check.config(state="disabled")
        self.pdf_num_photos_spinbox.config(state="disabled")
        self.pdf_page_size_combo.config(state="disabled")

        self.output_image_label.unbind("<Button-1>")
        self.image_display_frame.unbind("<Button-1>")
        try:
            self.output_image_label.drop_target_unregister()
            self.image_display_frame.drop_target_unregister()
        except Exception: pass
        self.output_image_label.config(cursor="")
        self.image_display_frame.config(cursor="")
        self.master.config(cursor="watch")

    def set_ui_idle(self):
        self.remove_bg_check.config(state="normal")
        self.bg_color_label.config(state="normal")
        self.current_color_label.config(state="normal", cursor="hand2")
        self.current_color_label.bind("<Button-1>", lambda e: self.open_color_picker())
        self.denoise_check.config(state="normal")
        self.toggle_denoise_slider()
        self.denoise_level_slider.config(state="normal" if self.denoise_var.get() else "disabled")
        self.scale_slider.config(state="normal")
        for check in [self.passport_size_check, self.stamp_size_check, self.resize_300px_check, self.resize_200px_check]:
             check.config(state="normal")
        self.pdf_num_photos_spinbox.config(state="readonly")
        self.pdf_page_size_combo.config(state="readonly")

        self.output_image_label.bind("<Button-1>", self.load_image)
        self.image_display_frame.bind("<Button-1>", self.load_image)
        try:
            self.output_image_label.drop_target_register(DND_FILES)
            self.image_display_frame.drop_target_register(DND_FILES)
        except Exception: pass
        self.output_image_label.config(cursor="hand2")
        self.image_display_frame.config(cursor="hand2")

        self.process_button.config(state="normal" if self.original_image_bgr is not None else "disabled")
        if self.processed_image is not None and self.processed_image.size > 0 :
            self.save_button.config(state="normal")
            self.save_pdf_button.config(state="normal")
        else:
            self.save_button.config(state="disabled")
            self.save_pdf_button.config(state="disabled")
        self.master.config(cursor="")


    def start_process_thread(self):
        if self.original_image_bgr is None:
            messagebox.showwarning("No Image", "Please load or drop an image first before processing.", parent=self.master)
            return
        if self.processing_thread and self.processing_thread.is_alive():
            messagebox.showinfo("Busy", "An image processing task is already running. Please wait for it to complete.", parent=self.master)
            return
        # if not self.face_cascade: # Keep this check if you want to optionally warn
        #     pass

        self.set_ui_busy()
        self.update_progress(0, "Starting image processing...")
        self.processed_image = None

        self.processing_thread = threading.Thread(target=self.process_image, name="ProcessingThread", daemon=True)
        self.processing_thread.start()
        self.master.after(100, self.check_queue)

    def check_queue(self):
        final_state_reached = False
        try:
            while True:
                progress_data = self.progress_queue.get_nowait()
                step = progress_data.get("step", 0)
                message = progress_data.get("message", "")
                is_error = progress_data.get("is_error", False)
                self.update_progress(step, message, is_error)
                if step >= 100 or is_error or "complete" in message.lower() or "cancel" in message.lower() or "fail" in message.lower():
                    final_state_reached = True
        except queue.Empty:
            pass
        except Exception as e:
             final_state_reached = True

        if self.processing_thread and self.processing_thread.is_alive():
            self.master.after(100, self.check_queue)
        else:
            self.set_ui_idle()
            current_progress = self.progress_bar['value']
            current_message = self.progress_label['text']
            # Use the corrected cget call here
            is_current_error = self.progress_label.cget('style') == 'Error.Status.TLabel'

            if not final_state_reached and current_progress < 100 :
                 if not is_current_error:
                     self.update_progress(current_progress, "Process finished unexpectedly.", is_error=True)
            elif current_progress == 100 and not is_current_error and "complete" not in current_message.lower():
                 self.update_progress(100, "Processing complete!", is_error=False)


    def update_progress(self, step, message, is_error=False):
        try:
            step = max(0, min(100, int(step)))
            self.progress_bar['value'] = step

            max_len = 80
            display_message = message if len(message) <= max_len else message[:max_len-3] + "..."

            status_text = f"{display_message} ({step}%)"

            if is_error:
                self.progress_label.config(text=status_text, style='Error.Status.TLabel')
            else:
                self.progress_label.config(text=status_text, style='Status.TLabel')
            self.master.update_idletasks()
        except Exception as e:
             pass

    def _put_progress(self, step, message, is_error=False):
        try:
            self.progress_queue.put({"step": step, "message": message, "is_error": is_error})
        except Exception as e:
            pass


    def process_image(self):
        if self.original_image_bgr is None:
            self._put_progress(-1, "Error: No valid BGR image data for processing", is_error=True)
            return

        try:
            current_img = self.original_image_bgr.copy()
            total_steps = 6
            step_increment = 100.0 / total_steps
            current_step_num = 0

            progress = int(current_step_num * step_increment)
            face_cropped = False
            if self.face_cascade:
                self._put_progress(progress, f"Step {current_step_num+1}/{total_steps}: Detecting face...")
                gray = cv2.cvtColor(current_img, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(60, 60))

                if len(faces) > 0:
                    x, y, w, h = max(faces, key=lambda rect: rect[2] * rect[3])

                    pad_w = int(w * 0.6)
                    pad_h_top = int(h * 0.7)
                    pad_h_bottom = int(h * 0.9)

                    img_h_orig, img_w_orig = current_img.shape[:2]

                    crop_x1 = max(0, x - pad_w)
                    crop_y1 = max(0, y - pad_h_top)
                    crop_x2 = min(img_w_orig, x + w + pad_w)
                    crop_y2 = min(img_h_orig, y + h + pad_h_bottom)

                    if crop_x2 > crop_x1 and crop_y2 > crop_y1:
                        current_img = current_img[crop_y1:crop_y2, crop_x1:crop_x2]
                        self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Cropped around largest face")
                        face_cropped = True
                    else:
                        self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Face crop skipped (invalid dimensions)")
                else:
                    self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: No face detected, skipping crop.")
            else:
                 self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Skipping face detection (detector not loaded).")
            current_step_num += 1


            progress = int(current_step_num * step_increment)
            if self.remove_bg_var.get():
                self._put_progress(progress, f"Step {current_step_num+1}/{total_steps}: Removing background...")
                try:
                    pil_img = Image.fromarray(cv2.cvtColor(current_img, cv2.COLOR_BGR2RGB))
                    transparent_bg_img = remove(pil_img)

                    bg_color_rgba = (*self.background_color_rgb, 255)
                    new_bg_img = Image.new("RGBA", transparent_bg_img.size, bg_color_rgba)

                    final_pil_img = Image.alpha_composite(new_bg_img, transparent_bg_img).convert("RGB")

                    current_img = cv2.cvtColor(np.array(final_pil_img), cv2.COLOR_RGB2BGR)
                    self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Background replaced")
                except ImportError:
                     error_msg = "Error: 'rembg' library not found. Cannot remove background."
                     self._put_progress(progress + step_increment, error_msg, is_error=True)
                except Exception as bg_err:
                    error_msg = f"Background removal failed: {bg_err}"
                    self._put_progress(progress + step_increment, error_msg, is_error=True)
            else:
                self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Background removal skipped")
            current_step_num += 1


            progress = int(current_step_num * step_increment)
            self._put_progress(progress, f"Step {current_step_num+1}/{total_steps}: Applying enhancements...")
            try:
                alpha = 1.05
                beta = 5
                enhanced_img = cv2.convertScaleAbs(current_img, alpha=alpha, beta=beta)

                sharpen_strength = 0.6
                blurred_img = cv2.GaussianBlur(enhanced_img, (0, 0), 3.0)
                current_img = cv2.addWeighted(enhanced_img, 1.0 + sharpen_strength, blurred_img, -sharpen_strength, 0)
                self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Enhanced contrast/sharpness")
            except cv2.error as cv_err:
                self._put_progress(progress + step_increment, f"Enhancement failed (OpenCV Error): {cv_err}", is_error=True)
            except Exception as enhance_err:
                self._put_progress(progress + step_increment, f"Enhancement failed: {enhance_err}", is_error=True)
            current_step_num += 1


            progress = int(current_step_num * step_increment)
            if self.denoise_var.get():
                self._put_progress(progress, f"Step {current_step_num+1}/{total_steps}: Applying denoise filter...")
                try:
                    denoise_level = float(self.denoise_level_var.get())
                    if current_img.dtype != np.uint8:
                         current_img = cv2.convertScaleAbs(current_img)

                    current_img = cv2.fastNlMeansDenoisingColored(current_img, None, h=denoise_level, hColor=denoise_level, templateWindowSize=7, searchWindowSize=21)
                    self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Denoising applied (Level {denoise_level})")
                except cv2.error as cv_err:
                     self._put_progress(progress + step_increment, f"Denoising failed (OpenCV Error): {cv_err}", is_error=True)
                except Exception as denoise_err:
                     self._put_progress(progress + step_increment, f"Denoising failed: {denoise_err}", is_error=True)
            else:
                self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Denoising skipped")
            current_step_num += 1


            progress = int(current_step_num * step_increment)
            scale_factor = self.scale_var.get()
            if scale_factor > 1:
                self._put_progress(progress, f"Step {current_step_num+1}/{total_steps}: Upscaling {scale_factor}x...")
                try:
                    if current_img.dtype != np.uint8:
                         current_img = cv2.convertScaleAbs(current_img)

                    new_width = int(current_img.shape[1] * scale_factor)
                    new_height = int(current_img.shape[0] * scale_factor)
                    current_img = cv2.resize(current_img, (new_width, new_height), interpolation=cv2.INTER_LANCZOS4)
                    self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Upscaled {scale_factor}x")
                except cv2.error as cv_err:
                     self._put_progress(progress + step_increment, f"Upscaling failed (OpenCV Error): {cv_err}", is_error=True)
                except Exception as upscale_err:
                     self._put_progress(progress + step_increment, f"Upscaling failed: {upscale_err}", is_error=True)
            else:
                self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Upscaling skipped (1x)")
            current_step_num += 1


            progress = int(current_step_num * step_increment)
            self._put_progress(progress, f"Step {current_step_num+1}/{total_steps}: Resizing to target dimensions...")
            target_size_px = None
            target_size_name = "Unknown Size"
            for var, size, name in self.size_options:
                if var.get():
                    target_size_px = size
                    target_size_name = name
                    break
            if target_size_px is None:
                target_size_px = PASSPORT_SIZE_PX
                target_size_name = "Passport Size (Default)"
                self.passport_size_var.set(1)

            if target_size_px:
                try:
                    h, w = current_img.shape[:2]
                    target_w, target_h = target_size_px

                    if not (target_w > 0 and target_h > 0):
                        raise ValueError("Target dimensions must be positive.")
                    if not (w > 0 and h > 0):
                        raise ValueError("Current image dimensions are invalid before resize.")

                    interpolation = cv2.INTER_AREA if (target_w * target_h < w * h) else cv2.INTER_LANCZOS4

                    if current_img.dtype != np.uint8:
                         current_img = cv2.convertScaleAbs(current_img)

                    current_img = cv2.resize(current_img, target_size_px, interpolation=interpolation)
                    self._put_progress(progress + step_increment * 0.5, f"Step {current_step_num+1}/{total_steps}: Resized to {target_size_name}")

                except ValueError as ve:
                    self._put_progress(progress + step_increment, f"Final resize skipped: {ve}", is_error=True)
                except cv2.error as cv_err:
                    self._put_progress(progress + step_increment, f"Final resize failed (OpenCV Error): {cv_err}", is_error=True)
                except Exception as resize_err:
                    self._put_progress(progress + step_increment, f"Final resize failed: {resize_err}", is_error=True)
            else:
                 self._put_progress(progress + step_increment, "Resize skipped (no target size defined)", is_error=True)


            self.processed_image = current_img
            self.master.after(0, self.display_image, self.processed_image, self.output_image_label, self.image_display_frame)
            self._put_progress(100, "Processing complete!")

        except Exception as e:
            self.processed_image = None
            if self.original_image_bgr is not None:
                 try:
                     self.master.after(0, self.display_image, self.original_image_bgr, self.output_image_label, self.image_display_frame)
                 except Exception: pass

            current_progress = 50
            try: current_progress = self.progress_bar['value']
            except Exception: pass
            error_type = type(e).__name__
            self._put_progress(current_progress, f"Error: Processing failed ({error_type}: {e})", is_error=True)


    def save_image(self):
        if self.processed_image is None or self.processed_image.size == 0:
            messagebox.showwarning("Save Error", "No processed image available to save. Please process an image first.", parent=self.master)
            return

        try:
            selected_size_name = "processed"
            for var, size, name in self.size_options:
                if var.get():
                    selected_size_name = name.lower().replace(" ", "_").replace("/", "").replace("(", "").replace(")", "")
                    break

            default_filename = f"{selected_size_name}_photo.png"

            save_path = filedialog.asksaveasfilename(
                title="Save Processed Image As",
                initialfile=default_filename,
                defaultextension=".png",
                filetypes=(("PNG files", "*.png"),
                           ("JPEG files", "*.jpg;*.jpeg"),
                           ("BMP files", "*.bmp"),
                           ("TIFF files", "*.tif;*.tiff"),
                           ("WebP files", "*.webp"),
                           ("All files", "*.*")),
                parent=self.master
            )

            if not save_path:
                self.update_progress(self.progress_bar['value'], "Save cancelled.")
                return

            params = []
            ext = os.path.splitext(save_path)[1].lower()

            if ext in ['.jpg', '.jpeg']:
                params = [cv2.IMWRITE_JPEG_QUALITY, 95]
            elif ext == '.png':
                params = [cv2.IMWRITE_PNG_COMPRESSION, 3]
            elif ext == '.webp':
                 params = [cv2.IMWRITE_WEBP_QUALITY, 101]

            self.update_progress(90, f"Saving to {os.path.basename(save_path)}...")
            success = cv2.imwrite(save_path, self.processed_image, params)

            if success:
                self.update_progress(100, f"Image saved: {os.path.basename(save_path)}")
                if messagebox.askyesno("Open Folder?", f"Image saved successfully to:\n{os.path.dirname(save_path)}\n\nDo you want to open this folder?", parent=self.master):
                    self.open_containing_folder(save_path)
            else:
                messagebox.showerror("Save Error", f"Failed to save image to:\n{save_path}\n\nPlease check file permissions, path validity, and available disk space.", parent=self.master)
                self.update_progress(100, "Error: Failed to save image.", is_error=True)

        except cv2.error as cv_err:
             messagebox.showerror("Save Error", f"An OpenCV error occurred while saving:\n{cv_err}\n\nCheck if the file format is supported or if the image data is valid.", parent=self.master)
             self.update_progress(100, "Error saving image (OpenCV).", is_error=True)
        except Exception as e:
            messagebox.showerror("Save Error", f"An unexpected error occurred while saving the image:\n{e}", parent=self.master)
            self.update_progress(100, "Error saving image.", is_error=True)

    def save_pdf(self):
        if self.processed_image is None or self.processed_image.size == 0:
            messagebox.showwarning("Save PDF Error", "No processed image available to place on the PDF. Please process an image first.", parent=self.master)
            return

        try:
            num_photos_str = self.pdf_num_photos_var.get()
            num_photos = int(num_photos_str)
            if not (1 <= num_photos <= 100):
                raise ValueError("Number of photos must be between 1 and 100.")
        except (tk.TclError, ValueError) as e:
            err_msg = f"Invalid number of photos entered: {e}\nPlease enter a whole number between 1 and 100."
            messagebox.showerror("PDF Settings Error", err_msg, parent=self.master)
            return

        selected_page_name = self.pdf_page_size_var.get()
        if selected_page_name not in PAGE_SIZES_MM:
            err_msg = f"Invalid page size selected: {selected_page_name}"
            messagebox.showerror("PDF Settings Error", err_msg, parent=self.master)
            return

        default_filename = f"{selected_page_name}_{num_photos}photos.pdf"
        save_path = filedialog.asksaveasfilename(
            title=f"Save {num_photos} Photos on {selected_page_name} PDF",
            initialfile=default_filename,
            defaultextension=".pdf",
            filetypes=(("PDF files", "*.pdf"), ("All files", "*.*")),
            parent=self.master
        )
        if not save_path:
            self.update_progress(self.progress_bar['value'], "PDF save cancelled.")
            return

        temp_file_path = None
        try:
            self.set_ui_busy()
            self.update_progress(0, f"Preparing PDF generation...")
            self.master.update_idletasks()

            pixel_h, pixel_w = self.processed_image.shape[:2]
            if pixel_w <= 0 or pixel_h <= 0:
                raise ValueError("Processed image has invalid dimensions (0 or negative).")

            if PDF_DPI <= 0:
                raise ValueError("PDF_DPI constant must be positive.")
            mm_per_pixel = (1.0 / PDF_DPI) * 25.4
            photo_width_mm = pixel_w * mm_per_pixel
            photo_height_mm = pixel_h * mm_per_pixel

            page_width_mm, page_height_mm = PAGE_SIZES_MM[selected_page_name]

            base_margin_mm = 3
            if photo_width_mm > (page_width_mm - 2 * base_margin_mm) or photo_height_mm > (page_height_mm - 2 * base_margin_mm):
                err_msg = (f"The selected photo size ({photo_width_mm:.1f} x {photo_height_mm:.1f} mm @{PDF_DPI} DPI) "
                           f"is too large to fit on a {selected_page_name} page ({page_width_mm:.1f} x {page_height_mm:.1f} mm) "
                           f"with reasonable margins.\n\nTry reducing the 'Photos per Page', choosing a larger "
                           f"page size, or ensure the individual photo size is appropriate.")
                messagebox.showerror("Layout Error", err_msg, parent=self.master)
                self.update_progress(50, "Error: Photo too large for page.", is_error=True)
                self.set_ui_idle()
                return

            self.update_progress(20, "Calculating optimal layout...")
            self.master.update_idletasks()

            h_spacing_mm = 3
            v_spacing_mm = 3

            best_layout = {'cols': 0, 'rows': 0, 'total_width': 0, 'total_height': 0, 'fits': False}

            for cols_try in range(num_photos, 0, -1):
                rows_needed = math.ceil(num_photos / cols_try)

                total_w = (cols_try * photo_width_mm) + (max(0, cols_try - 1) * h_spacing_mm)
                total_h = (rows_needed * photo_height_mm) + (max(0, rows_needed - 1) * v_spacing_mm)

                if total_w <= (page_width_mm - 2 * base_margin_mm) and total_h <= (page_height_mm - 2 * base_margin_mm):
                    best_layout = {'cols': cols_try, 'rows': rows_needed, 'total_width': total_w, 'total_height': total_h, 'fits': True}
                    break

            if not best_layout['fits']:
                err_msg = (f"Could not determine a suitable layout to fit {num_photos} photos "
                           f"({photo_width_mm:.1f}x{photo_height_mm:.1f} mm) on a {selected_page_name} page.\n\n"
                           f"Try reducing the number of photos or using a larger page size.")
                messagebox.showerror("Layout Error", err_msg, parent=self.master)
                self.update_progress(50, "Error: Cannot fit photos.", is_error=True)
                self.set_ui_idle()
                return

            margin_x_mm = max(base_margin_mm, (page_width_mm - best_layout['total_width']) / 2)
            margin_y_mm = max(base_margin_mm, (page_height_mm - best_layout['total_height']) / 2)

            self.update_progress(40, "Setting up PDF document...")
            self.master.update_idletasks()

            orientation = 'L' if page_width_mm > page_height_mm else 'P'
            pdf = FPDF(orientation=orientation, unit="mm", format=(page_width_mm, page_height_mm))
            pdf.set_auto_page_break(auto=False, margin=0)
            pdf.set_margins(0, 0, 0)
            pdf.add_page()

            self.update_progress(50, "Saving temporary image for PDF...")
            self.master.update_idletasks()

            pid = os.getpid()
            tid = threading.get_ident()
            temp_file_name = f"temp_pdf_img_{pid}_{tid}.png"
            temp_file_path = os.path.join(temp_dir(), temp_file_name)

            success = cv2.imwrite(temp_file_path, self.processed_image, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            if not success:
                raise IOError(f"Failed to write temporary image file to: {temp_file_path}")

            self.update_progress(60, f"Placing {num_photos} photos onto PDF...")
            self.master.update_idletasks()

            photo_count = 0
            for r in range(best_layout['rows']):
                if photo_count >= num_photos: break
                current_y = margin_y_mm + r * (photo_height_mm + v_spacing_mm)

                for c in range(best_layout['cols']):
                    if photo_count >= num_photos: break
                    current_x = margin_x_mm + c * (photo_width_mm + h_spacing_mm)

                    pdf.image(temp_file_path, x=current_x, y=current_y, w=photo_width_mm, h=photo_height_mm, type='PNG')
                    photo_count += 1

                    prog = 60 + int(35 * photo_count / num_photos)
                    if photo_count % 5 == 0 or photo_count == num_photos:
                        self.update_progress(prog, f"Placing photo {photo_count}/{num_photos}...")
                        self.master.update_idletasks()

            self.update_progress(95, "Saving final PDF file...")
            self.master.update_idletasks()
            pdf.output(save_path, "F")

            self.update_progress(100, f"PDF saved: {os.path.basename(save_path)}")

            if messagebox.askyesno("Open Folder?", f"PDF saved successfully to:\n{os.path.dirname(save_path)}\n\nDo you want to open this folder?", parent=self.master):
                self.open_containing_folder(save_path)

        except ValueError as ve:
            error_msg = f"PDF Settings Error: {ve}"
            messagebox.showerror("PDF Error", error_msg, parent=self.master)
            self.update_progress(100, "Error generating PDF.", is_error=True)
        except IOError as ioe:
            error_msg = f"File Error during PDF generation: {ioe}\n\nCheck permissions and disk space, especially for temporary files."
            messagebox.showerror("PDF File Error", error_msg, parent=self.master)
            self.update_progress(100, "Error generating PDF (File IO).", is_error=True)
        except Exception as e:
            error_msg = f"An unexpected error occurred while saving the PDF:\n{type(e).__name__}: {e}"
            messagebox.showerror("Save PDF Error", error_msg, parent=self.master)
            self.update_progress(100, "Error generating PDF.", is_error=True)

        finally:
            self.set_ui_idle()
            if temp_file_path and os.path.exists(temp_file_path):
                try:
                    os.remove(temp_file_path)
                except OSError as e:
                    pass


    def open_containing_folder(self, path):
        try:
            dir_path = os.path.dirname(os.path.abspath(path))
            if not os.path.isdir(dir_path):
                messagebox.showerror("Open Folder Error", f"Could not find the directory:\n{dir_path}", parent=self.master)
                return

            if sys.platform == 'win32':
                os.startfile(dir_path)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', '--', dir_path])
            else:
                subprocess.Popen(['xdg-open', '--', dir_path])

        except FileNotFoundError:
            messagebox.showerror("Open Folder Error", f"Could not find the directory:\n{dir_path}", parent=self.master)
        except Exception as e:
            messagebox.showerror("Open Folder Error", f"An error occurred while trying to open the folder:\n{e}", parent=self.master)


    def display_image(self, cv_image, tk_label, parent_widget):
        if cv_image is None or cv_image.size == 0:
            tk_label.config(image='', text="Click or Drop Image Here")
            tk_label.image = None
            return

        try:
            display_cv_image = None
            if len(cv_image.shape) == 2:
                display_cv_image = cv2.cvtColor(cv_image, cv2.COLOR_GRAY2BGR)
            elif len(cv_image.shape) == 3 and cv_image.shape[2] == 4:
                display_cv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGRA2BGR)
            elif len(cv_image.shape) == 3 and cv_image.shape[2] == 3:
                display_cv_image = cv_image
            else:
                err_msg = f"Unsupported image format for display. Shape: {cv_image.shape}"
                tk_label.config(image='', text=f"Cannot display:\n{err_msg}")
                tk_label.image = None
                return

            parent_widget.update_idletasks()
            padding = 10
            disp_w = parent_widget.winfo_width() - padding
            disp_h = parent_widget.winfo_height() - padding

            if disp_w <= 1 or disp_h <= 1:
                disp_w, disp_h = 300, 400

            img_h, img_w = display_cv_image.shape[:2]

            if img_w <= 0 or img_h <= 0:
                err_msg = f"Invalid image dimensions after conversion: {img_w}x{img_h}"
                tk_label.config(image='', text=err_msg)
                tk_label.image = None
                return

            scale = min(1.0, disp_w / img_w, disp_h / img_h)

            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))

            interpolation = cv2.INTER_AREA if scale < 0.95 else cv2.INTER_LINEAR
            resized_img = cv2.resize(display_cv_image, (new_w, new_h), interpolation=interpolation)

            img_rgb = cv2.cvtColor(resized_img, cv2.COLOR_BGR2RGB)
            img_pil = Image.fromarray(img_rgb)
            imgtk = ImageTk.PhotoImage(image=img_pil)

            tk_label.config(image=imgtk, text="")
            tk_label.image = imgtk

        except Exception as e:
            try:
                parent_width = parent_widget.winfo_width() if parent_widget.winfo_exists() else 300
                wrap_len = max(100, parent_width - padding * 2)
                tk_label.config(image='', text=f"Display Error:\n{e}", wraplength=wrap_len)
                tk_label.image = None
            except Exception as display_err:
                 tk_label.config(image='', text="Display Error")
                 tk_label.image = None

def temp_dir():
    tdir = tempfile.gettempdir()
    app_temp_dir = os.path.join(tdir, "passport_photo_studio_temp")
    try:
        os.makedirs(app_temp_dir, exist_ok=True)
        return app_temp_dir
    except OSError:
        return tdir

if __name__ == "__main__":
    missing_critical_files = []
    try:
        hc_path = resource_path(HAAR_CASCADE_FILE)
        if not os.path.exists(hc_path):
            missing_critical_files.append(HAAR_CASCADE_FILE)
    except Exception as e:
        missing_critical_files.append(f"{HAAR_CASCADE_FILE} (Error checking path: {e})")

    if missing_critical_files:
        files_str = "\n - ".join(missing_critical_files)
        error_title = "Critical File Missing"
        error_message = (f"A required file needed for core functionality is missing:\n\n"
                         f" - {files_str}\n\n"
                         f"The application cannot start without this file. Please ensure it exists "
                         f"in the correct location (usually alongside the executable) or reinstall the application.")
        try:
            root_err = tk.Tk()
            root_err.withdraw()
            messagebox.showerror(error_title, error_message)
        except Exception:
            pass
        sys.exit(1)

    missing_libraries = []
    library_install_hints = {
        "cv2": "opencv-python",
        "PIL": "Pillow",
        "rembg": "rembg",
        "fpdf": "fpdf2",
        "tkinterdnd2": "tkinterdnd2",
        "numpy": "numpy"
    }
    try: import cv2
    except ImportError: missing_libraries.append("cv2")
    try: from PIL import Image, ImageTk
    except ImportError: missing_libraries.append("PIL")
    try: import rembg
    except ImportError: missing_libraries.append("rembg")
    try: from fpdf import FPDF
    except ImportError: missing_libraries.append("fpdf")
    try: from tkinterdnd2 import TkinterDnD, DND_FILES
    except ImportError: missing_libraries.append("tkinterdnd2")
    try: import numpy
    except ImportError: missing_libraries.append("numpy")

    if missing_libraries:
        libs_str = ", ".join(missing_libraries)
        pip_packages = " ".join(library_install_hints.get(lib, lib) for lib in missing_libraries)
        error_title = "Dependency Error"
        error_message = (f"One or more required Python libraries are not installed:\n\n"
                         f" - {libs_str}\n\nPlease install them, for example using pip:\n\n"
                         f"   pip install {pip_packages}\n\n"
                         f"Note: 'rembg' might require additional setup (like downloading models) "
                         f"after installation. See 'rembg' documentation if background removal fails.")
        try:
            root_err = tk.Tk()
            root_err.withdraw()
            messagebox.showerror(error_title, error_message)
        except Exception:
            pass
        sys.exit(1)

    root = TkinterDnD.Tk()
    app = PassportPhoto(root)

    def on_closing():
        if app.processing_thread and app.processing_thread.is_alive():
            if messagebox.askyesno("Confirm Exit", "An image processing task is still running. Exiting now might lead to incomplete results.\n\nAre you sure you want to exit?", parent=root):
                root.destroy()
            else:
                return
        else:
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()
