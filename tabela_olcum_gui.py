import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import math
import numpy as np
import cv2


class TabelaOlcumGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Tabela Ölçüm Prototipi")
        self.root.geometry("1300x850")

        self.original_image = None
        self.display_image = None
        self.tk_image = None

        self.card_points = []
        self.object_points = []
        self.mode = None

        self.card_world = None
        self.object_world = None

        self.scale_ratio = 1.0
        self.img_offset_x = 0
        self.img_offset_y = 0
        self.display_width = 0
        self.display_height = 0

        top = tk.Frame(root)
        top.pack(fill="x", padx=10, pady=10)

        tk.Button(top, text="Fotoğraf Yükle", command=self.load_image).pack(side="left", padx=5)
        tk.Button(top, text="Kart Seç", command=self.start_card_mode).pack(side="left", padx=5)
        tk.Button(top, text="Nesne Seç", command=self.start_object_mode).pack(side="left", padx=5)
        tk.Button(top, text="Alan Hesapla", command=self.calculate_area).pack(side="left", padx=5)
        tk.Button(top, text="Temizle", command=self.clear_all).pack(side="left", padx=5)

        self.info_label = tk.Label(top, text="Durum: Fotoğraf yükleyin", font=("Arial", 11, "bold"))
        self.info_label.pack(side="left", padx=20)

        self.result_label = tk.Label(top, text="Alan: -", font=("Arial", 12, "bold"))
        self.result_label.pack(side="left", padx=20)

        self.canvas = tk.Canvas(root, bg="gray")
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Button-1>", self.click_point)

    # -----------------------------
    # görüntü yükleme
    # -----------------------------
    def load_image(self):
        path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.png *.jpeg *.bmp")])
        if not path:
            return

        self.original_image = Image.open(path)
        self.card_points = []
        self.object_points = []
        self.card_world = None
        self.object_world = None
        self.mode = None
        self.result_label.config(text="Alan: -")
        self.info_label.config(text="Durum: Fotoğraf yüklendi. Önce kart seçin")
        self.show_scaled_image()

    def show_scaled_image(self):
        if self.original_image is None:
            return

        self.canvas.update_idletasks()
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()

        if cw < 100:
            cw = 1200
            ch = 700

        iw, ih = self.original_image.size
        ratio = min(cw / iw, ch / ih)
        self.scale_ratio = ratio

        new_w = int(iw * ratio)
        new_h = int(ih * ratio)
        self.display_width = new_w
        self.display_height = new_h

        self.img_offset_x = (cw - new_w) // 2
        self.img_offset_y = (ch - new_h) // 2

        self.display_image = self.original_image.resize((new_w, new_h), Image.LANCZOS)
        self.tk_image = ImageTk.PhotoImage(self.display_image)

        self.redraw()

    # -----------------------------
    # mod başlatma
    # -----------------------------
    def start_card_mode(self):
        if self.original_image is None:
            return
        self.mode = "card"
        self.card_points = []
        self.card_world = None
        self.result_label.config(text="Alan: -")
        self.info_label.config(text="Durum: Kart modu aktif. Kartın 4 köşesini seçin")
        self.redraw()

    def start_object_mode(self):
        if self.original_image is None:
            return
        if len(self.card_points) != 4:
            self.info_label.config(text="Durum: Önce kartın 4 köşesini seçin")
            return
        self.mode = "object"
        self.object_points = []
        self.object_world = None
        self.result_label.config(text="Alan: -")
        self.info_label.config(text="Durum: Nesne modu aktif. Nesnenin 4 köşesini seçin")
        self.redraw()

    # -----------------------------
    # mouse
    # -----------------------------
    def click_point(self, event):
        if self.original_image is None:
            return

        x = event.x
        y = event.y

        inside_x = self.img_offset_x <= x <= self.img_offset_x + self.display_width
        inside_y = self.img_offset_y <= y <= self.img_offset_y + self.display_height
        if not (inside_x and inside_y):
            return

        real_x = (x - self.img_offset_x) / self.scale_ratio
        real_y = (y - self.img_offset_y) / self.scale_ratio

        if self.mode == "card":
            if len(self.card_points) < 4:
                self.card_points.append((real_x, real_y))
                if len(self.card_points) == 4:
                    self.card_points = self.order_points(self.card_points)
                    self.info_label.config(text="Durum: Kart seçildi. Şimdi Nesne Seç'e basın")

        elif self.mode == "object":
            if len(self.object_points) < 4:
                self.object_points.append((real_x, real_y))
                if len(self.object_points) == 4:
                    self.object_points = self.order_points(self.object_points)
                    self.info_label.config(text="Durum: Nesne seçildi. Alan Hesapla'ya basın")

        self.redraw()

    # -----------------------------
    # çizim
    # -----------------------------
    def redraw(self):
        if self.tk_image is None:
            return

        self.canvas.delete("all")
        self.canvas.create_image(self.img_offset_x, self.img_offset_y, anchor="nw", image=self.tk_image)

        if len(self.card_points) == 4:
            self.draw_polygon_fill(self.card_points, fill="#00bcd4", stipple="gray50")
        if len(self.object_points) == 4:
            self.draw_polygon_fill(self.object_points, fill="#4caf50", stipple="gray50")

        self.draw_points(self.card_points, "cyan")
        self.draw_points(self.object_points, "lime")

    def draw_points(self, points, color):
        display = []
        for px, py in points:
            dx = self.img_offset_x + px * self.scale_ratio
            dy = self.img_offset_y + py * self.scale_ratio
            display.append((dx, dy))

        for i, (x, y) in enumerate(display):
            r = 5
            self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="red", outline="white", width=1)
            self.canvas.create_text(x + 12, y - 12, text=str(i + 1), fill="yellow", font=("Arial", 10, "bold"))

        for i in range(len(display) - 1):
            x1, y1 = display[i]
            x2, y2 = display[i + 1]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

        if len(display) == 4:
            x1, y1 = display[3]
            x2, y2 = display[0]
            self.canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

    def draw_polygon_fill(self, points, fill, stipple="gray50"):
        display = []
        for px, py in points:
            dx = self.img_offset_x + px * self.scale_ratio
            dy = self.img_offset_y + py * self.scale_ratio
            display.extend([dx, dy])
        self.canvas.create_polygon(display, fill=fill, stipple=stipple, outline="")

    # -----------------------------
    # geometri
    # -----------------------------
    def order_points(self, pts):
        pts = np.array(pts, dtype=np.float32)
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        d = np.diff(pts, axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        rect[1] = pts[np.argmin(d)]
        rect[3] = pts[np.argmax(d)]
        return [tuple(p) for p in rect]

    def distance(self, p1, p2):
        return math.sqrt((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2)

    def shoelace(self, pts):
        area = 0
        n = len(pts)
        for i in range(n):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % n]
            area += x1 * y2 - x2 * y1
        return abs(area) / 2

    # -----------------------------
    # perspektif dönüşüm
    # -----------------------------
    def image_to_world_transform(self):
        CARD_W = 8.56
        CARD_H = 5.398

        src = np.array(self.order_points(self.card_points), dtype=np.float32)
        dst = np.array([
            [0, 0],
            [CARD_W, 0],
            [CARD_W, CARD_H],
            [0, CARD_H]
        ], dtype=np.float32)

        matrix = cv2.getPerspectiveTransform(src, dst)
        return matrix

    def transform_points_to_world(self, pts):
        matrix = self.image_to_world_transform()
        arr = np.array(pts, dtype=np.float32).reshape(-1, 1, 2)
        world = cv2.perspectiveTransform(arr, matrix).reshape(-1, 2)
        return [tuple(p) for p in world]

    # -----------------------------
    # alan hesapla
    # -----------------------------
    def calculate_area(self):
        if len(self.card_points) != 4:
            self.info_label.config(text="Durum: Önce kartın 4 köşesini seçin")
            return

        if len(self.object_points) != 4:
            self.info_label.config(text="Durum: Ölçülecek nesnenin 4 köşesini seçin")
            return

        self.object_world = self.transform_points_to_world(self.object_points)
        area_cm2 = self.shoelace(self.object_world)
        area_m2 = area_cm2 / 10000.0

        p = self.object_world
        top_w = self.distance(p[0], p[1])
        bottom_w = self.distance(p[3], p[2])
        left_h = self.distance(p[0], p[3])
        right_h = self.distance(p[1], p[2])

        width_cm = (top_w + bottom_w) / 2
        height_cm = (left_h + right_h) / 2

        area_px = self.shoelace(self.object_points)

        self.result_label.config(
            text=f"Alan: {area_px:.2f} px²  |  {area_cm2:.2f} cm²  |  {area_m2:.5f} m²  |  En: {width_cm:.2f} cm  |  Boy: {height_cm:.2f} cm"
        )
        self.info_label.config(text="Durum: Perspektif düzeltmeli ölçüm tamamlandı")

    # -----------------------------
    # temizle
    # -----------------------------
    def clear_all(self):
        self.card_points = []
        self.object_points = []
        self.card_world = None
        self.object_world = None
        self.mode = None
        self.result_label.config(text="Alan: -")
        if self.original_image is not None:
            self.info_label.config(text="Durum: Temizlendi. Önce kart seçin")
            self.redraw()
        else:
            self.info_label.config(text="Durum: Fotoğraf yükleyin")
            self.canvas.delete("all")


if __name__ == "__main__":
    root = tk.Tk()
    app = TabelaOlcumGUI(root)
    root.mainloop()
