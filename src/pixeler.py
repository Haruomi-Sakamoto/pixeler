import tkinter as tk
from tkinter import filedialog, colorchooser
from PIL import Image, ImageTk
import numpy as np
import json
import os

import config

class PixelArtApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pixel Art Converter")

        self.pixel_size = config.PIXEL_SIZE_DEFAULT
        self.palette = []
        self.processed_image = None
        self.display_image = None

        self.button_frame = tk.Frame(root)
        self.button_frame.pack()

        self.btn_select = tk.Button(self.button_frame, text="Select Image", command=self.select_image)
        self.btn_select.pack(side=tk.LEFT)

        self.btn_add_color = tk.Button(self.button_frame, text="Add Color", command=self.add_color)
        self.btn_add_color.pack(side=tk.LEFT)

        self.btn_clear_palette = tk.Button(self.button_frame, text="Clear Palette", command=self.clear_palette)
        self.btn_clear_palette.pack(side=tk.LEFT)

        self.btn_save_palette = tk.Button(self.button_frame, text="Save Palette", command=self.save_palette)
        self.btn_save_palette.pack(side=tk.LEFT)

        self.btn_load_palette = tk.Button(self.button_frame, text="Load Palette", command=self.load_palette)
        self.btn_load_palette.pack(side=tk.LEFT)

        self.btn_save = tk.Button(self.button_frame, text="Save Image", command=self.save_image, state=tk.DISABLED)
        self.btn_save.pack(side=tk.LEFT)

        self.btn_reload = tk.Button(self.button_frame, text="Reload Image", command=self.reload_image, state=tk.DISABLED)
        self.btn_reload.pack(side=tk.LEFT)

        self.pixel_slider_label = tk.Label(self.button_frame, text="Pixel Size")
        self.pixel_slider_label.pack(side=tk.LEFT)
        self.pixel_slider = tk.Scale(
            self.button_frame,
            from_=config.PIXEL_SIZE_MIN,
            to=config.PIXEL_SIZE_MAX,
            orient=tk.HORIZONTAL
        )
        self.pixel_slider.set(config.PIXEL_SIZE_DEFAULT)
        self.pixel_slider.pack(side=tk.LEFT)

        self.color_frame = tk.Frame(root)
        self.color_frame.pack(fill=tk.X, padx=10, pady=5)

        self.canvas = tk.Canvas(root, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.last_file_path = None

        self.load_palette_from_default()

    def select_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg;*.png;*.bmp")])
        if file_path:
            self.last_file_path = file_path
            self.process_image(file_path)
            self.btn_reload.config(state=tk.NORMAL)
            self.btn_save.config(state=tk.NORMAL)

    def reload_image(self):
        if self.last_file_path:
            self.process_image(self.last_file_path)

    def add_color(self):
        color_code = colorchooser.askcolor()[0]
        if color_code:
            color_tuple = tuple(map(int, color_code))
            if color_tuple not in self.palette:
                self.palette.append(color_tuple)
                self.update_palette_display()

    def clear_palette(self):
        self.palette = []
        self.update_palette_display()

    def remove_color(self, color):
        self.palette.remove(color)
        self.update_palette_display()

    def update_palette_display(self):
        for widget in self.color_frame.winfo_children():
            widget.destroy()

        for color in self.palette:
            color_label = tk.Label(
                self.color_frame,
                bg=self.rgb_to_hex(color),
                width=6,
                height=2,
                bd=2,
                relief="solid",
                anchor="center"
            )
            color_label.bind("<Button-1>", lambda e, c=color: self.remove_color(c))
            color_label.pack(side=tk.LEFT, padx=2, pady=2)

    def save_palette(self):
        os.makedirs("palette", exist_ok=True)
        existing_files = [f for f in os.listdir("palette") if f.startswith("palette") and f.endswith(".json")]
        numbers = []
        for f in existing_files:
            try:
                num = int(f[7:-5])
                numbers.append(num)
            except ValueError:
                continue
        next_number = max(numbers) + 1 if numbers else 1

        filename = f"palette{next_number}.json"
        file_path = os.path.join("palette", filename)

        with open(file_path, "w") as f:
            json.dump(self.palette, f)

    def load_palette(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json")]
        )
        if file_path:
            with open(file_path, "r") as f:
                self.palette = json.load(f)
            self.update_palette_display()

    def load_palette_from_default(self):
        if os.path.exists(config.DEFAULT_PALETTE_FILE):
            with open(config.DEFAULT_PALETTE_FILE, 'r') as f:
                self.palette = json.load(f)
            self.update_palette_display()
        else:
            self.palette = []

    def process_image(self, file_path):
        pixel_size = int(self.pixel_slider.get())
        img = Image.open(file_path).convert("RGB")
        img = img.resize((img.width // pixel_size, img.height // pixel_size), Image.NEAREST)

        if self.palette:
            img = self.apply_palette(img)

        img = img.resize((img.width * pixel_size, img.height * pixel_size), Image.NEAREST)
        self.processed_image = img
        self.display_resized_image(img)

    def apply_palette(self, img):
        pixels = np.array(img)
        for i in range(pixels.shape[0]):
            for j in range(pixels.shape[1]):
                pixels[i, j] = self.get_nearest_color(tuple(pixels[i, j]))
        return Image.fromarray(pixels.astype('uint8'))

    def get_nearest_color(self, pixel):
        return min(self.palette, key=lambda c: sum((p - c[i])**2 for i, p in enumerate(pixel)))

    def display_resized_image(self, img):
        max_width = config.DISPLAY_MAX_WIDTH
        max_height = config.DISPLAY_MAX_HEIGHT
        img_width, img_height = img.size
        scale = min(max_width / img_width, max_height / img_height)
        new_size = (int(img_width * scale), int(img_height * scale))

        img_resized = img.resize(new_size, Image.NEAREST)
        self.display_image = ImageTk.PhotoImage(img_resized)

        self.canvas.delete("all")
        self.canvas.create_image(10, 10, anchor=tk.NW, image=self.display_image)
        self.canvas.config(scrollregion=self.canvas.bbox("all"))

    def save_image(self):
        if self.processed_image:
            os.makedirs("img", exist_ok=True)
            existing_files = [f for f in os.listdir("img") if f.startswith("img") and f.endswith(".png")]
            numbers = []
            for f in existing_files:
                try:
                    num = int(f[3:-4])
                    numbers.append(num)
                except ValueError:
                    continue
            next_number = max(numbers) + 1 if numbers else 1

            filename = f"img{next_number}.png"
            file_path = os.path.join("img", filename)
            self.processed_image.save(file_path)

    def rgb_to_hex(self, rgb):
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'

root = tk.Tk()
root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
app = PixelArtApp(root)
root.mainloop()
