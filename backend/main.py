import asyncio
import gc
import logging
import threading
import time
from contextlib import asynccontextmanager
from io import BytesIO
from typing import Annotated, Optional
from zipfile import ZIP_DEFLATED, BadZipFile, ZipFile

import cv2
import numpy as np
import torch
import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from bubble_detector.bubble_detector_factory import (
    BubbleDetectorFactory,
    BubbleDetectorType,
)
from inpainting.inpainter_factory import (
    InpainterFactory,
    InpainterType,
)
from ocr_engine.ocr_factory import (
    OCREngineFactory,
    OCREngineType,
)
from text_renderer.pil_centered_text import PILCenteredTextRenderer
from translator.translator_factory import (
    TranslatorFactory,
    TranslatorType,
)
from utils.languages import SourceLang, TargetLang
from utils.logger import setup_logger

# =========================
# LOGGER
# =========================
setup_logger()
logger = logging.getLogger("API")


# =========================
# LIFESPAN
# =========================
@asynccontextmanager
async def lifespan(app: FastAPI):
    yield

    # shutdown
    unload_models()


# =========================
# APP
# =========================
app = FastAPI(title="Comic Translator API", lifespan=lifespan)


# =========================
# GLOBAL LOCK
# Only allow 1 request at a time to prevent OOM and model conflicts
# =========================
PROCESS_LOCK = asyncio.Lock()
MODEL_LOCK = threading.Lock()


# =========================
# CONFIG MODEL
# =========================
class ConfigModel(BaseModel):
    font_size_ratio: Optional[float] = None
    detect_model: Optional[BubbleDetectorType] = None
    ocr_model: Optional[OCREngineType] = None
    inpaint_model: Optional[InpainterType] = None
    translate_model: Optional[TranslatorType] = None
    source_lang: Optional[SourceLang] = None
    target_lang: Optional[TargetLang] = None


# =========================
# DEFAULT CONFIG
# =========================
CONFIG = ConfigModel()

CONFIG.detect_model = BubbleDetectorType.YOLOV8_TENSORRT
CONFIG.ocr_model = OCREngineType.TURBO_OCR
CONFIG.inpaint_model = InpainterType.OPENCV
CONFIG.translate_model = TranslatorType.GoogleTranslator
CONFIG.source_lang = SourceLang.zh
CONFIG.target_lang = TargetLang.vi
CONFIG.font_size_ratio = 1.0


# =========================
# GLOBAL MODELS
# =========================
DETECTOR = None
OCR = None
TRANSLATOR = None
INPAINTER = None
RENDERER = PILCenteredTextRenderer()


# =========================
# MEMORY CLEANUP
# =========================
def clear_memory():

    gc.collect()

    if torch.cuda.is_available():
        try:
            torch.cuda.empty_cache()
        except Exception:
            logger.exception("CUDA cleanup failed")

    logger.info("Memory cleaned")


# =========================
# MODEL MANAGER
# =========================
def models_loaded():
    return (
        DETECTOR is not None
        and OCR is not None
        and TRANSLATOR is not None
        and INPAINTER is not None
    )


def load_models():
    global DETECTOR
    global OCR
    global TRANSLATOR
    global INPAINTER

    with MODEL_LOCK:
        if models_loaded():
            return

        logger.info("Loading models...")

        DETECTOR = BubbleDetectorFactory.create(CONFIG.detect_model)

        OCR = OCREngineFactory.create(CONFIG.ocr_model)
        OCR.set_language(CONFIG.source_lang)

        TRANSLATOR = TranslatorFactory.create(CONFIG.translate_model)

        INPAINTER = InpainterFactory.create(CONFIG.inpaint_model)

        logger.info("Models loaded")


def ensure_models_loaded():

    if models_loaded():
        return

    load_models()


def unload_models():
    global DETECTOR
    global OCR
    global TRANSLATOR
    global INPAINTER

    with MODEL_LOCK:
        logger.info("Unloading models...")
        try:
            for model in [DETECTOR, OCR, TRANSLATOR, INPAINTER]:
                if model is not None and hasattr(model, "close"):
                    model.close()

        except Exception:
            logger.exception("Cleanup failed")

        DETECTOR = None
        OCR = None
        TRANSLATOR = None
        INPAINTER = None

        clear_memory()

        logger.info("Models unloaded")


def reload_models():

    with MODEL_LOCK:
        unload_models()

        logger.info("Reloading models...")

        load_models()

        logger.info("Reload complete")


@app.post("/cleanup")
async def cleanup():

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        unload_models()

        return JSONResponse({"status": "ok", "message": "Memory cleaned"})


@app.post("/unload_models")
async def unload_models_api():

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        unload_models()

        return JSONResponse({"status": "ok", "message": "Models unloaded"})


@app.post("/reload_models")
async def reload_models_api():

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        unload_models()

        load_models()

        return JSONResponse({"status": "ok", "message": "Models reloaded"})


# =========================
# CONFIG API
# =========================
@app.post("/config")
async def set_config(cfg: ConfigModel):

    global CONFIG

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        changed = False

        if cfg.font_size_ratio is not None:
            CONFIG.font_size_ratio = cfg.font_size_ratio

        if cfg.source_lang is not None:
            CONFIG.source_lang = cfg.source_lang

        if cfg.target_lang is not None:
            CONFIG.target_lang = cfg.target_lang

        if cfg.detect_model is not None and cfg.detect_model != CONFIG.detect_model:
            CONFIG.detect_model = cfg.detect_model
            changed = True

        if cfg.ocr_model is not None and cfg.ocr_model != CONFIG.ocr_model:
            CONFIG.ocr_model = cfg.ocr_model
            changed = True

        if cfg.inpaint_model is not None and cfg.inpaint_model != CONFIG.inpaint_model:
            CONFIG.inpaint_model = cfg.inpaint_model
            changed = True

        if cfg.translate_model is not None and cfg.translate_model != CONFIG.translate_model:
            CONFIG.translate_model = cfg.translate_model
            changed = True

        if changed:
            reload_models()

        return JSONResponse({"status": "ok", "config": CONFIG.model_dump()})


# =========================
# IMAGE READER
# =========================
def _read_image_from_upload(data: bytes):
    arr = np.frombuffer(data, np.uint8)

    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)

    return img


# =========================
# TRANSLATE COMIC ONE IMAGE
# =========================
@app.post("/translate_comic")
async def translate_comic(
    file: Annotated[UploadFile, File()],
    font_size_ratio: Optional[float] = Form(CONFIG.font_size_ratio),
    conf_threshold: float = Form(0.25),
):
    global DETECTOR
    global OCR
    global TRANSLATOR
    global INPAINTER
    global RENDERER
    global CONFIG
    ensure_models_loaded()

    # reject nếu đang bận
    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        start_time = time.perf_counter()

        data = await file.read()

        image = _read_image_from_upload(data)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # detect
        t = time.perf_counter()
        with torch.inference_mode():
            boxes = DETECTOR.detect(image, conf_threshold)
        t_detect = time.perf_counter() - t
        logger.info(f"Detection took {t_detect:.2f}s, found {len(boxes)} boxes")

        # crop bubbles
        bubbles = [image[int(y1) : int(y2), int(x1) : int(x2)] for (x1, y1, x2, y2) in boxes]

        # OCR
        t = time.perf_counter()
        ocr_results = OCR.ocr(bubbles)
        t_ocr = time.perf_counter() - t
        logger.info(f"OCR took {t_ocr:.2f}s")
        original_texts = [item.get("text", "").strip() for item in ocr_results]

        # Parallel Translate and Inpaint task
        t = time.perf_counter()
        translate_task = TRANSLATOR.translate_batch(
            original_texts, from_lang=CONFIG.source_lang, to_lang=CONFIG.target_lang
        )
        inpaint_task = asyncio.to_thread(
            INPAINTER.inpaint_from_boxes, image=image, crop_boxes=boxes, ocr_results=ocr_results
        )

        # wait for both tasks to complete
        translated_texts, cleaned = await asyncio.gather(translate_task, inpaint_task)
        t_translate_inpaint = time.perf_counter() - t
        logger.info(f"Translate + Inpaint took {t_translate_inpaint:.2f}s")

        # render
        final_img = cleaned.copy()
        t = time.perf_counter()
        CONFIG.font_size_ratio = font_size_ratio
        for box, text, ocr_result in zip(boxes, translated_texts, ocr_results, strict=True):
            if text:
                final_img = RENDERER.draw_text_in_box(
                    final_img,
                    str(text).capitalize(),
                    box,
                    font_size=int(CONFIG.font_size_ratio * ocr_result["font_size"]),
                )
        t_render = time.perf_counter() - t
        logger.info(f"Rendering took {t_render:.2f}s")

        total = time.perf_counter() - start_time

        logger.info(f"Done in {total:.2f}s")

        success, buf = cv2.imencode(".png", final_img)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode image")

        return Response(
            content=buf.tobytes(),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=translated.png"},
        )


async def process_one_image(
    image: np.ndarray,
    font_size_ratio: float,
    conf_threshold: float,
) -> np.ndarray:

    with torch.inference_mode():
        boxes = DETECTOR.detect(image, conf_threshold)

    bubbles = [image[int(y1) : int(y2), int(x1) : int(x2)] for (x1, y1, x2, y2) in boxes]

    ocr_results = OCR.ocr(bubbles)

    original_texts = [item.get("text", "").strip() for item in ocr_results]

    translated_texts, cleaned = await asyncio.gather(
        TRANSLATOR.translate_batch(
            original_texts,
            from_lang=CONFIG.source_lang,
            to_lang=CONFIG.target_lang,
        ),
        asyncio.to_thread(
            INPAINTER.inpaint_from_boxes,
            image=image,
            crop_boxes=boxes,
            ocr_results=ocr_results,
        ),
    )

    final_img = cleaned.copy()

    for box, text, ocr_result in zip(boxes, translated_texts, ocr_results, strict=True):
        if text:
            final_img = RENDERER.draw_text_in_box(
                final_img,
                str(text).capitalize(),
                box,
                font_size=int(font_size_ratio * ocr_result["font_size"]),
            )

    return final_img


# =========================
# TRANSLATE COMIC ZIP
# =========================
@app.post("/translate_comic_zip")
async def translate_comic_zip(
    file: Annotated[UploadFile, File()],
    font_size_ratio: float = Form(CONFIG.font_size_ratio),
    conf_threshold: float = Form(0.25),
):
    ensure_models_loaded()

    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy",
        )

    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(
            status_code=400,
            detail="Please upload a ZIP file",
        )

    async with PROCESS_LOCK:
        zip_bytes = await file.read()

        try:
            input_zip = ZipFile(BytesIO(zip_bytes), "r")
        except BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Invalid ZIP file",
            ) from None

        output_buffer = BytesIO()

        with ZipFile(
            output_buffer,
            "w",
            compression=ZIP_DEFLATED,
        ) as output_zip:
            for name in sorted(input_zip.namelist()):
                # bỏ thư mục
                if name.endswith("/"):
                    continue

                if not name.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                    continue

                try:
                    image_bytes = input_zip.read(name)

                    image = _read_image_from_upload(image_bytes)

                    if image is None:
                        logger.warning(f"Skip invalid image: {name}")
                        continue

                    result = await process_one_image(
                        image=image,
                        font_size_ratio=font_size_ratio,
                        conf_threshold=conf_threshold,
                    )

                    ext = name.rsplit(".", 1)[-1].lower()

                    if ext == "jpg":
                        ext = "jpeg"

                    success, buf = cv2.imencode(
                        f".{ext}",
                        result,
                    )

                    if not success:
                        continue

                    output_zip.writestr(
                        name,
                        buf.tobytes(),
                    )

                except Exception:
                    logger.exception(f"Failed processing {name}")

        output_buffer.seek(0)

        return Response(
            content=output_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=translated.zip"},
        )


# =========================
# SINGLE BOX CHAT
# =========================


@app.post("/translate_one_box_chat")
async def translate_one_box_chat(
    file: Annotated[UploadFile, File()],
):
    global OCR
    global TRANSLATOR
    global CONFIG
    ensure_models_loaded()

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        start = time.perf_counter()

        data = await file.read()

        image = _read_image_from_upload(data)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        # OCR
        ocr_results = OCR.ocr([image])

        # Translate
        original_texts = [item.get("text", "").strip() for item in ocr_results]
        translated_texts = await TRANSLATOR.translate_batch(
            original_texts, from_lang=CONFIG.source_lang, to_lang=CONFIG.target_lang
        )

        total = time.perf_counter() - start

        return JSONResponse(
            {
                "original": original_texts[0] if original_texts else "",
                "translated": translated_texts[0] if translated_texts else "",
                "timings": round(total, 4),
            }
        )


# =========================
# HEALTH
# =========================
@app.get("/health")
async def health():

    gpu_mem = None

    if torch.cuda.is_available():
        gpu_mem = {
            "allocated_mb": round(torch.cuda.memory_allocated() / 1024 / 1024, 2),
            "reserved_mb": round(torch.cuda.memory_reserved() / 1024 / 1024, 2),
        }

    return JSONResponse(
        {
            "status": "ok",
            "busy": PROCESS_LOCK.locked(),
            "gpu": gpu_mem,
            "models": {
                "detector": DETECTOR is not None,
                "ocr": OCR is not None,
                "translator": TRANSLATOR is not None,
                "inpainter": INPAINTER is not None,
            },
        }
    )


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8052,
        workers=1,
    )
