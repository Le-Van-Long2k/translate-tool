import time
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageGrab
import cv2
import numpy as np

# ================= ENGINE =================
from ocr_engine.paddle_ocr_engine import PaddleOCREngine
from text_renderer.pil_centered_text import PILCenteredTextRenderer
from translator.gemma_4_e2b_translator import Gemma4E2BClientTranslator
from bubble_detector.yolo_v8_bubble_detector import YOLOv8TensorRT
from inpainting.lama_inpainting import LamaInpainting

detector = YOLOv8TensorRT()
ocr_engine = PaddleOCREngine()
translator = Gemma4E2BClientTranslator()
inpainter = LamaInpainting()
renderer = PILCenteredTextRenderer()

current_image = None
current_translated = None


class ComicTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Comic Translator FIX DPI + 5 STEP")

        try:
            self.root.state("zoomed")
        except:
            self.root.attributes("-zoomed", True)

        self.conf_threshold = tk.DoubleVar(value=0.25)
        self.font_size = tk.IntVar(value=28)
        self.source_lang = tk.StringVar(value="en")
        self.target_lang = tk.StringVar(value="vi")

        self.build_ui()

    # ================= UI =================
    def build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill=tk.BOTH, expand=True)

        # LEFT
        left = ttk.Frame(main, width=320)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        ttk.Label(left, text="Comic Translator", font=("Arial", 16, "bold")).pack(
            pady=10
        )

        ttk.Button(left, text="Chọn vùng", command=self.select_region).pack(
            fill=tk.X, pady=10
        )

        ttk.Button(left, text="Dịch", command=self.run_pipeline, state="disabled").pack(
            fill=tk.X
        )

        self.translate_btn = left.winfo_children()[-1]

        self.log_box = tk.Text(left, height=20)
        self.log_box.pack(fill=tk.BOTH, expand=True)

        # RIGHT
        right = ttk.Frame(main)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        right.rowconfigure(0, weight=7)
        right.rowconfigure(1, weight=3)
        right.columnconfigure(0, weight=1)

        # TOP
        top = ttk.Frame(right)
        top.grid(row=0, column=0, sticky="nsew")

        top.columnconfigure(0, weight=1)
        top.columnconfigure(1, weight=1)
        top.rowconfigure(0, weight=1)

        self.orig = ttk.LabelFrame(top, text="Original")
        self.orig.grid(row=0, column=0, sticky="nsew")

        self.final = ttk.LabelFrame(top, text="Final")
        self.final.grid(row=0, column=1, sticky="nsew")

        self.orig_lbl = ttk.Label(self.orig)
        self.orig_lbl.pack(fill=tk.BOTH, expand=True)

        self.final_lbl = ttk.Label(self.final)
        self.final_lbl.pack(fill=tk.BOTH, expand=True)

        # BOTTOM 5 STEP
        bottom = ttk.LabelFrame(right, text="5 STEP PIPELINE")
        bottom.grid(row=1, column=0, sticky="nsew")

        bottom.columnconfigure((0, 1, 2, 3, 4), weight=1)

        self.steps = []
        for i in range(5):
            lbl = ttk.Label(bottom, text=f"Step {i + 1}", background="#111")
            lbl.grid(row=0, column=i, sticky="nsew", padx=2, pady=2)
            self.steps.append(lbl)

    # ================= LOG =================
    def log(self, msg):
        self.log_box.insert(tk.END, msg + "\n")
        self.log_box.see(tk.END)

    # ================= STEP SHOW =================
    def show_step(self, i, img):
        if img is None:
            return

        h, w = img.shape[:2]
        scale = min(200 / w, 150 / h, 1.0)

        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        photo = ImageTk.PhotoImage(Image.fromarray(img))
        self.steps[i].configure(image=photo)
        self.steps[i].image = photo

    # ================= FIXED REGION SELECT =================
    def select_region(self):
        self.log("Capture screen...")

        full = ImageGrab.grab()
        full_np = np.array(full)

        h, w = full_np.shape[:2]

        win = tk.Toplevel(self.root)
        win.attributes("-fullscreen", True)
        win.attributes("-topmost", True)

        canvas = tk.Canvas(win, highlightthickness=0)
        canvas.pack(fill=tk.BOTH, expand=True)

        screen_w = win.winfo_screenwidth()
        screen_h = win.winfo_screenheight()

        scale_x = w / screen_w
        scale_y = h / screen_h

        display = full.resize((screen_w, screen_h))
        photo = ImageTk.PhotoImage(display)

        canvas.create_image(0, 0, image=photo, anchor="nw")
        canvas.image = photo

        rect = None
        sx = sy = 0

        def press(e):
            nonlocal sx, sy, rect
            sx, sy = e.x, e.y
            rect = canvas.create_rectangle(sx, sy, sx, sy, outline="green")

        def drag(e):
            canvas.coords(rect, sx, sy, e.x, e.y)

        def release(e):
            global current_image

            x1 = int(min(sx, e.x) * scale_x)
            y1 = int(min(sy, e.y) * scale_y)
            x2 = int(max(sx, e.x) * scale_x)
            y2 = int(max(sy, e.y) * scale_y)

            crop = full_np[y1:y2, x1:x2]

            self.log(f"Crop shape: {crop.shape}")

            current_image = cv2.cvtColor(crop, cv2.COLOR_RGB2BGR)

            self.show_step(0, current_image)

            self.translate_btn.config(state="normal")
            win.destroy()

        canvas.bind("<Button-1>", press)
        canvas.bind("<B1-Motion>", drag)
        canvas.bind("<ButtonRelease-1>", release)

    # ================= PIPELINE =================
    def run_pipeline(self):
        global current_image

        if current_image is None:
            messagebox.showerror("Error", "No image")
            return

        self.translate_btn.config(state="disabled")

        img1 = current_image.copy()
        self.show_step(0, img1)

        # STEP 2 detect
        boxes = detector.detect(img1, self.conf_threshold.get())

        img2 = img1.copy()
        for x1, y1, x2, y2 in boxes:
            cv2.rectangle(img2, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)

        self.show_step(1, img2)

        if not boxes:
            self.log("No bubbles")
            return

        # STEP 3 OCR
        crops = [img1[int(y1) : int(y2), int(x1) : int(x2)] for x1, y1, x2, y2 in boxes]
        ocr = ocr_engine.recognize([c for c in crops if c.size > 0])

        texts = [r.get("text", "") for r in ocr]

        self.show_step(2, img1)

        # STEP 4 inpaint
        img4 = inpainter.inpaint_from_boxes(img1.copy(), boxes)
        self.show_step(3, img4)

        # STEP 5 translate
        trans = translator.translate_batch(
            texts, from_lang=self.source_lang.get(), to_lang=self.target_lang.get()
        )

        img5 = img4.copy()

        for box, txt in zip(boxes, trans):
            if txt.strip():
                img5 = renderer.draw_text_in_box(img5, txt, box, self.font_size.get())

        self.show_step(4, img5)

        self.final_show(img5)

        self.translate_btn.config(state="normal")

    # ================= FINAL =================
    def final_show(self, img):
        h, w = img.shape[:2]
        scale = min(900 / w, 600 / h, 1.0)

        img = cv2.resize(img, (int(w * scale), int(h * scale)))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        img = ImageTk.PhotoImage(Image.fromarray(img))
        self.final_lbl.configure(image=img)
        self.final_lbl.image = img


# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    ttk.Style().theme_use("clam")
    app = ComicTranslatorApp(root)
    root.mainloop()
