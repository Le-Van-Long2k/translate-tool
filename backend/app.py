import logging
import os
import numpy as np
import cv2
import gradio as gr
import time
import re
import torch
import gc

from utils.logger import setup_logger
from bubble_detector.bubble_detector_factory import (
    BubbleDetectorType,
    BubbleDetectorFactory,
)
from ocr_engine.ocr_factory import OCREngineFactory, OCREngineType
from translator.translator_factory import TranslatorFactory, TranslatorType
from inpainting.inpainter_factory import InpainterFactory, InpainterType
from text_renderer.pil_centered_text import PILCenteredTextRenderer

setup_logger()
logger = logging.getLogger("MAIN")

# ── INIT ENGINE ─────────────────────────────────────────────
detector = BubbleDetectorFactory.create(BubbleDetectorType.YOLOV8)
ocr_engine = OCREngineFactory.create(OCREngineType.PADDLE_OCR)
translator = TranslatorFactory.create(TranslatorType.GEMMA_4_E2B_LLAMACPP_PYTHON)
inpainter = InpainterFactory.create(InpainterType.LAMA)
renderer = PILCenteredTextRenderer()

GLOBAL_STATE = {"running": False}


# ── UTILS ──────────────────────────────────────────────────
def to_rgb(bgr_img):
    if bgr_img is None:
        return None
    return cv2.cvtColor(bgr_img, cv2.COLOR_BGR2RGB)


def draw_step1(image, boxes):
    img = image.copy()
    for x1, y1, x2, y2 in boxes:
        cv2.rectangle(img, (int(x1), int(y1)), (int(x2), int(y2)), (0, 0, 255), 3)
    return img


def draw_step2(image, ocr_results, bubble_boxes):
    img = image.copy()
    for i, item in enumerate(ocr_results):
        bx1, by1, _, _ = map(int, bubble_boxes[i])
        for wb in item.get("boxes", []):
            pts = np.array(wb, np.int32)
            pts[:, 0] += bx1
            pts[:, 1] += by1
            cv2.polylines(img, [pts], True, (0, 255, 0), 2)
    return img


def clear_memory():
    # 1. Thu gom rác của Python (RAM)
    gc.collect()

    # 2. Xóa bộ nhớ đệm CUDA (VRAM)
    if torch.cuda.is_available():
        with torch.cuda.device(torch.cuda.current_device()):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    logger.info("🧹 Đã dọn dẹp sạch sẽ VRAM và RAM.")


def handle_click(running):
    new_state = not running
    GLOBAL_STATE["running"] = new_state

    if new_state:
        return new_state, gr.update(value="🛑 STOP PROCESS", variant="stop")
    else:
        return new_state, gr.update(value="🚀 RUN PROCESS", variant="primary")


def check_files(files):
    if files and len(files) > 0:
        # Nếu có file, cho phép nhấn nút
        return gr.update(interactive=True)
    else:
        # Nếu không có file, vô hiệu hóa nút
        return gr.update(interactive=False)


# ── MAIN PROCESS ───────────────────────────────────────────
def process_comic_folder(
    file_objs,
    custom_output_path,
    source_lang,
    target_lang,
    conf_threshold,
    font_size,
    sel_detector,
    sel_ocr,
    sel_translator,
    sel_inpaint,
):

    list_orig, list_detect, list_ocr, list_inpaint, list_final = [], [], [], [], []
    translate_log = ""
    time_log_table = []
    output_dir = (
        custom_output_path.strip()
        if custom_output_path
        else os.path.join(os.getcwd(), "translated_output")
    )
    os.makedirs(output_dir, exist_ok=True)

    global detector, ocr_engine, translator, inpainter, renderer

    # --- BƯỚC XÓA MODEL CŨ ---
    try:
        # Xóa các biến tham chiếu đến model cũ
        if "detector" in globals():
            del detector
        if "ocr_engine" in globals():
            del ocr_engine
        if "translator" in globals():
            del translator
        if "inpainter" in globals():
            del inpainter

        # Gọi hàm dọn dẹp chuyên sâu
        clear_memory()
    except Exception as e:
        logger.warning(f"Lỗi khi dọn dẹp: {e}")

    # --- BƯỚC KHỞI TẠO MỚI ---
    try:
        detector = BubbleDetectorFactory.create(sel_detector)
        ocr_engine = OCREngineFactory.create(sel_ocr)
        translator = TranslatorFactory.create(sel_translator)
        inpainter = InpainterFactory.create(sel_inpaint)
        renderer = PILCenteredTextRenderer()
    except Exception as e:
        yield (
            f"❌ Lỗi khởi tạo model: {str(e)}",
            [],
            [],
            [],
            [],
            "",
            [],
            "",
            [],
        )
        return

    if not file_objs:
        yield "❌ Không có file!", [], [], [], [], "", [], "", []
        return

    image_extensions = (".jpg", ".jpeg", ".png", ".webp", ".bmp")
    image_paths = [f for f in file_objs if f.lower().endswith(image_extensions)]

    def natural_sort_key(s):
        return [
            int(text) if text.isdigit() else text.lower()
            for text in re.split("([0-9]+)", os.path.basename(s))
        ]

    image_paths.sort(key=natural_sort_key)

    for idx, img_path in enumerate(image_paths, 1):
        filename = os.path.basename(img_path)
        name_no_ext, ext = os.path.splitext(filename)
        page_start_time = time.perf_counter()

        try:
            image = cv2.imread(img_path)
            if image is None:
                continue
            height, width = image.shape[:2]

            # 0. Original
            list_orig.append((to_rgb(image), f"Gốc: {filename}"))
            yield (
                f"⏳ Đang xử lý: {filename}",
                list_orig,
                list_detect,
                list_ocr,
                list_inpaint,
                translate_log,
                list_final,
                output_dir,
                time_log_table,
            )

            # 1. Detection
            t0 = time.perf_counter()
            boxes = detector.detect(image, conf_threshold)
            img_detect = draw_step1(image, boxes)
            list_detect.append((to_rgb(img_detect), f"Detect: {filename}"))
            t_detect = time.perf_counter() - t0

            # 2. OCR
            t0 = time.perf_counter()
            bubbles = [
                image[int(y1) : int(y2), int(x1) : int(x2)]
                for (x1, y1, x2, y2) in boxes
            ]
            ocr_results = ocr_engine.ocr(bubbles)
            img_ocr = draw_step2(image, ocr_results, boxes)
            list_ocr.append((to_rgb(img_ocr), f"OCR: {filename}"))
            t_ocr = time.perf_counter() - t0

            # 3. Translate
            t0 = time.perf_counter()
            original_texts = [item.get("text", "").strip() for item in ocr_results]
            translated_texts = translator.translate_batch(
                original_texts, from_lang=source_lang, to_lang=target_lang
            )
            t_translate = time.perf_counter() - t0

            # Cập nhật Text Log (Đối chiếu Line-by-Line)
            translate_log += f"--- Page: {filename} ---\n"
            for o_txt, t_txt in zip(original_texts, translated_texts):
                translate_log += f"Original  : {o_txt}\nTranslated: {t_txt}\n\n"

            # 4. Inpainting (Xóa chữ)
            t0 = time.perf_counter()
            all_word_boxes = []
            for i, item in enumerate(ocr_results):
                bx1, by1, _, _ = map(int, boxes[i])
                for wb in item.get("boxes", []):
                    all_word_boxes.append([[x + bx1, y + by1] for x, y in wb])

            cleaned_img = (
                inpainter.inpaint_from_boxes(image.copy(), all_word_boxes)
                if all_word_boxes
                else image.copy()
            )
            list_inpaint.append((to_rgb(cleaned_img), f"Inpaint: {filename}"))
            t_inpaint = time.perf_counter() - t0

            # 5. Render (Kết quả cuối)
            t0 = time.perf_counter()
            final_img = cleaned_img.copy()
            for box, text in zip(boxes, translated_texts):
                if text:
                    final_img = renderer.draw_text_in_box(
                        final_img, str(text).capitalize(), box, font_size=font_size
                    )

            out_file = os.path.join(output_dir, f"{name_no_ext}_translated{ext}")
            cv2.imwrite(out_file, final_img)
            list_final.append((to_rgb(final_img), f"Final: {filename}"))
            t_render = time.perf_counter() - t0

            total_page_time = time.perf_counter() - page_start_time

            time_log_table.append([
                filename,
                f"{height}x{width}",
                f"{t_detect:.3f}s",
                f"{t_ocr:.3f}s",
                f"{t_translate:.3f}s",
                f"{t_inpaint:.3f}s",
                f"{t_render:.3f}s",
                f"{total_page_time:.3f}s",
            ])

            yield (
                f"✅ Xong {idx}/{len(image_paths)}",
                list_orig,
                list_detect,
                list_ocr,
                list_inpaint,
                translate_log,
                list_final,
                output_dir,
                time_log_table,
            )

            if not GLOBAL_STATE["running"]:
                logger.info("🛑 User requested stop.")
                yield (
                    "⚠️ Đã dừng bởi người dùng.",
                    list_orig,
                    list_detect,
                    list_ocr,
                    list_inpaint,
                    translate_log,
                    list_final,
                    output_dir,
                    time_log_table,
                )
                return

        except Exception as e:
            logger.error(f"Error at {filename}: {e}")
            yield (
                f"❌ Lỗi tại {filename}",
                list_orig,
                list_detect,
                list_ocr,
                list_inpaint,
                translate_log,
                list_final,
                output_dir,
                time_log_table,
            )

    GLOBAL_STATE["running"] = False

    yield (
        "🚀 HOÀN TẤT!",
        list_orig,
        list_detect,
        list_ocr,
        list_inpaint,
        translate_log,
        list_final,
        output_dir,
        time_log_table,
    )


# ── UI ─────────────────────────────────────────────────────
with gr.Blocks(title="Comic Pro Translator", fill_width=True) as demo:
    gr.Markdown("# 📚 Comic Translator - Full Pipeline View")
    is_running = gr.State(value=False)

    with gr.Row():
        with gr.Column(scale=1):
            file_input = gr.File(
                label="Upload Folder", file_count="directory", height="200px"
            )
            with gr.Accordion("Settings", open=True):
                out_path = gr.Textbox(label="Output Path")
                f_size = gr.Slider(10, 80, value=28, step=1, label="Font Size")
                gr.Markdown("---")

                gr.Markdown("### 🎯 Detector Model")
                with gr.Row():
                    sel_detector = gr.Dropdown(
                        choices=[e.value for e in BubbleDetectorType],
                        value=BubbleDetectorType.YOLOV8.value,
                        label="Detector Model",
                        show_label=False,
                    )
                    c_slider = gr.Slider(
                        0.1,
                        0.9,
                        value=0.25,
                        step=0.05,
                        label="Threshold",
                    )
                gr.Markdown("---")

                with gr.Row():
                    with gr.Column(min_width=100):
                        gr.Markdown("### 🔍 OCR Model")
                        sel_ocr = gr.Dropdown(
                            choices=[e.value for e in OCREngineType],
                            value=OCREngineType.PADDLE_OCR.value,
                            label="OCR Model",
                            show_label=False,
                        )
                    with gr.Column(min_width=100):
                        gr.Markdown("### 🎨 Inpainting Model")
                        sel_inpaint = gr.Dropdown(
                            choices=[e.value for e in InpainterType],
                            value=InpainterType.LAMA.value,
                            label="Inpainting Model",
                            show_label=False,
                        )
                gr.Markdown("---")

                with gr.Row():
                    with gr.Column(min_width=200):
                        gr.Markdown("### 🌐 Translation Model")
                        sel_translator = gr.Dropdown(
                            choices=[e.value for e in TranslatorType],
                            value=TranslatorType.GEMMA_4_E2B_LLAMACPP_PYTHON.value,
                            label="Translation Model",
                            show_label=False,
                        )
                    with gr.Column(min_width=30):
                        gr.Markdown("#### Source")
                        src_l = gr.Dropdown(
                            ["en", "ja", "ko", "zh-cn", "auto"],
                            value="en",
                            label="Source",
                            show_label=False,
                        )
                    with gr.Column(min_width=30):
                        gr.Markdown("#### Target")
                        tgt_l = gr.Dropdown(
                            ["vi", "en"],
                            value="vi",
                            label="Target",
                            show_label=False,
                        )
                gr.Markdown("---")

            btn = gr.Button("🚀 RUN PROCESS", variant="primary", interactive=False)
            status_log = gr.Textbox(show_label=True, label="Status", interactive=False)
            final_path_display = gr.Textbox(
                show_label=True, label="Saved at", interactive=False
            )

        with gr.Column(scale=3):
            with gr.Tabs():
                with gr.TabItem("1. 🧱 Original"):
                    gal_orig = gr.Gallery(columns=4, height="1000px", preview=True)
                with gr.TabItem("2. 🎯 Detection"):
                    gal_detect = gr.Gallery(columns=4, height="1000px", preview=True)
                with gr.TabItem("3. 🔍 OCR"):
                    gal_ocr = gr.Gallery(columns=4, height="1000px", preview=True)
                with gr.TabItem("4. 🎨 Inpainting"):
                    gal_inpaint = gr.Gallery(columns=4, height="1000px", preview=True)
                with gr.TabItem("5. 🌐 Translation"):
                    text_compare = gr.TextArea(
                        label="Original vs Translated",
                        interactive=False,
                        lines=45,
                    )
                with gr.TabItem("6. 💎 Final Result"):
                    gal_final = gr.Gallery(columns=3, height="1000px", preview=True)

                with gr.TabItem("⏱️ Timing Details"):
                    time_viewer = gr.Dataframe(
                        value=[],
                        headers=[
                            "Filename",
                            "Image size",
                            "Detect",
                            "OCR",
                            "Translate",
                            "Inpaint",
                            "Render",
                            "TOTAL",
                        ],
                        datatype="str",
                        label="⏱️ Processing Time Statistics",
                        interactive=False,
                        max_height="1000px",
                    )

        file_input.change(fn=check_files, inputs=[file_input], outputs=[btn])

        btn.click(fn=handle_click, inputs=[is_running], outputs=[is_running, btn]).then(
            fn=process_comic_folder,
            inputs=[
                file_input,
                out_path,
                src_l,
                tgt_l,
                c_slider,
                f_size,
                sel_detector,
                sel_ocr,
                sel_translator,
                sel_inpaint,
            ],
            outputs=[
                status_log,
                gal_orig,
                gal_detect,
                gal_ocr,
                gal_inpaint,
                text_compare,
                gal_final,
                final_path_display,
                time_viewer,
            ],
        ).then(  # Khi process kết thúc (dù là xong hay là bị dừng)
            fn=lambda: (False, gr.update(value="🚀 RUN PROCESS", variant="primary")),
            outputs=[is_running, btn],
        )

if __name__ == "__main__":
    demo.queue().launch(
        theme=gr.themes.Soft(),
        server_name="0.0.0.0",
        server_port=7860,
    )
