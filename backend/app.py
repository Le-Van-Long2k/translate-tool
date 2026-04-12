import os
import numpy as np
import cv2
import glob
import gradio as gr
import time


# Optional: chọn folder bằng GUI Windows
try:
    import tkinter as tk
    from tkinter import filedialog

    TK_AVAILABLE = True
except:
    TK_AVAILABLE = False


from ocr_engine.ocr_engine import OCREngine
from text_renderer.text_renderer import TextRenderer
from translator.translator import ITranslator
from bubble_detector.bubble_detector import BubbleDetector

# from bubble_detector.yolo_v8_bubble_detector import YOLOv8BubbleDetector
from bubble_detector.yolo_v8_bubble_detector_tensorRT import YOLOv8TensorRT
from ocr_engine.paddle_ocr_engine import PaddleOCREngine
from text_renderer.pil_centered_text import PILCenteredTextRenderer

# from translator.google_translator import GoogleTranslatorEngine
# from translator.tencent_translator import TencentTranslatorEngine
# from translator.NLLBTranslator import NLLBTranslator
from translator.gemma_4_e2b_translator import (
    Gemma4E2BLlamaCppPythonTranslator,
    Gemma4E2BClientTranslator,
)

from inpainting.lama_inpainting import LamaInpainting

# ── INIT ENGINE ─────────────────────────────────────────────
detector: BubbleDetector = YOLOv8TensorRT()
ocr_engine: OCREngine = PaddleOCREngine()
translator: ITranslator = Gemma4E2BClientTranslator()
inpainter = LamaInpainting()
renderer: TextRenderer = PILCenteredTextRenderer()


# ── UTILS ──────────────────────────────────────────────────
def normalize_path(path):
    """Convert Windows path → WSL path"""
    if not path:
        return ""

    if isinstance(path, list):
        path = path[0]

    if hasattr(path, "name"):
        path = path.name

    path = str(path).strip().strip('"')

    # Windows → WSL
    if ":" in path and "\\" in path:
        drive = path[0].lower()
        rest = path[2:].replace("\\", "/")
        path = f"/mnt/{drive}/{rest}"

    return path


def browse_folder():
    """Mở dialog chọn folder (Windows GUI)"""
    if not TK_AVAILABLE:
        return "❌ tkinter không khả dụng trên hệ thống này"

    root = tk.Tk()
    root.withdraw()
    folder_selected = filedialog.askdirectory()
    root.destroy()

    return folder_selected


# ── MAIN PROCESS ───────────────────────────────────────────
def process_comic_folder(
    folder_path, source_lang, target_lang, conf_threshold=0.25, font_size=28
):

    folder_path = normalize_path(folder_path)

    print("DEBUG folder_path:", folder_path)

    if not folder_path or not os.path.isdir(folder_path):
        yield f"❌ Thư mục không tồn tại: {folder_path}", folder_path or "Không có"
        return

    # ✅ Auto output folder
    output_dir = os.path.join(folder_path, "translated")
    os.makedirs(output_dir, exist_ok=True)

    image_extensions = ["*.jpg", "*.jpeg", "*.png", "*.webp", "*.bmp"]
    image_paths = []
    for ext in image_extensions:
        image_paths.extend(glob.glob(os.path.join(folder_path, ext)))

    if not image_paths:
        yield f"❌ Không có ảnh trong thư mục!", output_dir
        return

    image_paths = sorted(image_paths)

    log_lines = []
    log_lines.append(f"📁 Output: {output_dir}")

    for idx, img_path in enumerate(image_paths, 1):
        start_time = time.perf_counter()
        filename = os.path.basename(img_path)
        name_no_ext, ext = os.path.splitext(filename)
        print("##########################################")
        print("filename:", filename)

        try:
            image = cv2.imread(img_path)
            if image is None:
                log_lines.append("⚠️ Không đọc được ảnh")
                yield "\n".join(log_lines), output_dir
                continue
            h, w, c = image.shape
            print(f"Size: {w}x{h}")

            # 1. Detect bubbles
            t1 = time.perf_counter()
            boxes = detector.detect(image, conf_threshold)
            print(f"Step1 (Detection Bubbles): {time.perf_counter() - t1:.3f}s")

            # 2. OCR
            t2 = time.perf_counter()
            original_word_boxes = []
            original_texts = []
            translated_texts = []
            bubbles = []

            for box in boxes:
                x1, y1, x2, y2 = map(int, box)
                crop = image[y1:y2, x1:x2]
                bubbles.append(crop)

                if crop.size == 0:
                    continue

            ocr_results = ocr_engine.recognize(bubbles)

            for i, item in enumerate(ocr_results):
                text = item.get("text", "").strip()
                original_texts.append(text)

                for wb in item.get("boxes", []):
                    x1, y1, x2, y2 = map(int, boxes[i])
                    new_box = [[x + x1, y + y1] for x, y in wb]
                    original_word_boxes.append(new_box)
            print(f"Step2 (OCR): {time.perf_counter() - t2:.3f}s")

            # 3. Translate
            t3 = time.perf_counter()
            translated_texts = translator.translate_batch(
                original_texts, from_lang=source_lang, to_lang=target_lang
            )
            print(f"Step3 (Translate): {time.perf_counter() - t3:.3f}s")

            # 4. Remove text
            t4 = time.perf_counter()
            img_clean = image.copy()

            if original_word_boxes:
                # mask = np.zeros(img_clean.shape[:2], dtype=np.uint8)

                # for pts_list in original_word_boxes:
                #     pts = np.array(pts_list, dtype=np.int32)
                #     cv2.fillPoly(mask, [pts], 255)

                # kernel = np.ones((5, 5), np.uint8)
                # mask = cv2.dilate(mask, kernel, iterations=1)

                # cleaned = cv2.inpaint(img_clean, mask, 3, cv2.INPAINT_TELEA)
                cleaned = inpainter.inpaint_from_boxes(img_clean, original_word_boxes)
            else:
                cleaned = img_clean
            print(f"Step4 (Remove text): {time.perf_counter() - t4:.3f}s")
            # 5. Draw text
            t5 = time.perf_counter()
            final_img = cleaned.copy()

            for box, text in zip(boxes, translated_texts):
                if text.strip():
                    final_img = renderer.draw_text_in_box(
                        final_img, str(text).capitalize(), box, font_size=font_size
                    )
            print(f"Step5 (Draw text): {time.perf_counter() - t5:.3f}s")
            # Save
            t6 = time.perf_counter()
            output_path = os.path.join(output_dir, f"{name_no_ext}_vi{ext}")
            cv2.imwrite(output_path, final_img)
            end_time = time.perf_counter()
            print(f"Step6 (Save): {end_time - t6:.3f}s")

            log_lines.append(f"✅ Done ({end_time - start_time:.3f}s → {output_path})")
            yield "\n".join(log_lines), output_dir

        except Exception as e:
            log_lines.append(f"❌ ERROR: {e}")
            yield "\n".join(log_lines), output_dir

    log_lines.append("\n===== DONE =====")
    yield "\n".join(log_lines), output_dir


# ── UI ─────────────────────────────────────────────────────
with gr.Blocks(title="Comic Translator (WSL Ready)") as demo:
    gr.Markdown("# 📚 Comic Translator (WSL + Windows Folder Support)")

    with gr.Row():
        with gr.Column(scale=2):
            folder_input = gr.Textbox(
                label="📂 Thư mục ảnh",
                placeholder="D:\\Truyen\\Chapter1 hoặc /mnt/d/Truyen/Chapter1",
                lines=2,
            )

            browse_btn = gr.Button("📁 Chọn folder (Windows)")

            browse_btn.click(fn=browse_folder, outputs=folder_input)

            with gr.Row():
                src_lang = gr.Dropdown(
                    ["en", "ja", "ko", "zh-cn", "auto"], value="en", label="Source"
                )
                tgt_lang = gr.Dropdown(["vi", "en", "ja"], value="vi", label="Target")

            with gr.Row():
                conf_slider = gr.Slider(0.1, 0.6, value=0.25, step=0.05, label="Conf")
                font_size_input = gr.Slider(10, 60, value=28, step=2, label="Font size")

            btn = gr.Button("🚀 Start", variant="primary")

        with gr.Column(scale=3):
            log_output = gr.Textbox(label="Log", lines=20, max_lines=20)
            final_folder_info = gr.Textbox(label="Output folder")

    btn.click(
        fn=process_comic_folder,
        inputs=[folder_input, src_lang, tgt_lang, conf_slider, font_size_input],
        outputs=[log_output, final_folder_info],
        concurrency_limit=1,
    )


if __name__ == "__main__":
    demo.queue()
    demo.launch(server_name="0.0.0.0", server_port=7860, share=False)
