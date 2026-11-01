import asyncio
import gc
import logging
import os
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
from config import get_default_config
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
# APP
# =========================
app = FastAPI(title="Comic Translator API")


@app.get("/health_check")
async def health_check():
    return JSONResponse(
        {
            "status": "ok",
            "models_loaded": models_loaded(),
        }
    )


# =========================
# GLOBAL LOCK
# Only allow 1 request at a time to prevent OOM and model conflicts
# =========================
PROCESS_LOCK = asyncio.Lock()


# =========================
# CONFIG MODEL
# =========================
class ConfigModel(BaseModel):
    font_size_ratio: Optional[float] = None
    detect_model: Optional[BubbleDetectorType] = None
    ocr_model: Optional[OCREngineType] = None
    inpaint_model: Optional[InpainterType] = None
    translate_model: Optional[TranslatorType] = None
    source_lang: Optional[SourceLang] = SourceLang.auto
    target_lang: Optional[TargetLang] = None


class TextTranslationRequest(BaseModel):
    text: str


class TranslateSystemPromptRequest(BaseModel):
    prompt: str


# =========================
# DEFAULT CONFIG
# =========================
DEFAULT_CONFIG = get_default_config()
CONFIG = ConfigModel()

CONFIG.detect_model = DEFAULT_CONFIG["detect_model"]
CONFIG.ocr_model = DEFAULT_CONFIG["ocr_model"]
CONFIG.inpaint_model = DEFAULT_CONFIG["inpaint_model"]
CONFIG.translate_model = DEFAULT_CONFIG["translate_model"]
CONFIG.source_lang = DEFAULT_CONFIG["source_lang"]
CONFIG.target_lang = DEFAULT_CONFIG["target_lang"]
CONFIG.font_size_ratio = DEFAULT_CONFIG["font_size_ratio"]


# =========================
# GLOBAL MODELS
# Models are loaded by a separate startup module (e.g., startup.py)
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
# MODEL MANAGER (removed - models loaded elsewhere)
# =========================
def models_loaded():
    return (
        DETECTOR is not None
        and OCR is not None
        and TRANSLATOR is not None
        and INPAINTER is not None
    )


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
            # Models will be reloaded by the startup module
            pass

        return JSONResponse({"status": "ok", "config": CONFIG.model_dump()})


# =========================
# IMAGE READER
# =========================
def _read_image_from_upload(data: bytes):
    arr = np.frombuffer(data, np.uint8)
    img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    return img


# =========================
# DETECT BUBBLES ONLY
# =========================
@app.post("/detect_bubbles")
async def detect_bubbles(
    file: Annotated[UploadFile, File()],
    conf_threshold: float = Form(0.25),
):
    global DETECTOR

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        start_time = time.perf_counter()

        data = await file.read()
        image = _read_image_from_upload(data)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        t = time.perf_counter()
        with torch.inference_mode():
            boxes = DETECTOR.detect(image, conf_threshold)

        t_detect = time.perf_counter() - t
        logger.debug(f"Bubble detection took {t_detect:.2f}s, found {len(boxes)} boxes")

        result_image = image.copy()
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

        success, buf = cv2.imencode(".png", result_image)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode image")

        total = time.perf_counter() - start_time
        logger.debug(f"Bubble detection completed in {total:.2f}s")

        return Response(
            content=buf.tobytes(),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=detected_bubbles.png"},
        )


# =========================
# DETECT BUBBLES + OCR
# =========================
@app.post("/detect_bubbles_ocr")
async def detect_bubbles_ocr(
    file: Annotated[UploadFile, File()],
    conf_threshold: float = Form(0.25),
):
    global DETECTOR
    global OCR

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        start_time = time.perf_counter()

        data = await file.read()
        image = _read_image_from_upload(data)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        with torch.inference_mode():
            boxes = DETECTOR.detect(image, conf_threshold)

        logger.debug(f"Bubble detection found {len(boxes)} boxes")

        bubbles = []
        for x1, y1, x2, y2 in boxes:
            x1 = max(0, int(x1))
            y1 = max(0, int(y1))
            x2 = min(image.shape[1], int(x2))
            y2 = min(image.shape[0], int(y2))
            if x2 <= x1 or y2 <= y1:
                bubbles.append(None)
                continue
            bubbles.append(image[y1:y2, x1:x2])

        ocr_results = OCR.ocr(bubbles)

        result_image = image.copy()
        for box, ocr_result in zip(boxes, ocr_results, strict=False):
            x1, y1, x2, y2 = map(int, box)
            text = ocr_result.get("text", "").strip()

            cv2.rectangle(result_image, (x1, y1), (x2, y2), (0, 255, 0), 2)

            if text:
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.7
                thickness = 2
                (tw, th), baseline = cv2.getTextSize(text, font, font_scale, thickness)

                text_x = x1
                text_y = max(th + baseline + 5, y1)

                cv2.rectangle(
                    result_image,
                    (text_x, text_y - th - baseline - 5),
                    (text_x + tw + 8, text_y + 3),
                    (0, 0, 0),
                    -1,
                )

                cv2.putText(
                    result_image,
                    text,
                    (text_x + 4, text_y - 2),
                    font,
                    font_scale,
                    (255, 255, 255),
                    thickness,
                    cv2.LINE_AA,
                )

        success, buf = cv2.imencode(".png", result_image)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to encode image")

        total = time.perf_counter() - start_time
        logger.debug(f"Detect + OCR completed in {total:.2f}s")

        return Response(
            content=buf.tobytes(),
            media_type="image/png",
            headers={"Content-Disposition": "attachment; filename=detected_bubbles_ocr.png"},
        )


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

    if PROCESS_LOCK.locked():
        raise HTTPException(status_code=429, detail="Server is busy")

    async with PROCESS_LOCK:
        start_time = time.perf_counter()

        data = await file.read()
        image = _read_image_from_upload(data)

        if image is None:
            raise HTTPException(status_code=400, detail="Invalid image file")

        t = time.perf_counter()
        with torch.inference_mode():
            boxes = DETECTOR.detect(image, conf_threshold)
        t_detect = time.perf_counter() - t
        logger.debug(f"Detection took {t_detect:.2f}s, found {len(boxes)} boxes")

        bubbles = [image[int(y1):int(y2), int(x1):int(x2)] for (x1, y1, x2, y2) in boxes]

        t = time.perf_counter()
        ocr_results = OCR.ocr(bubbles)
        t_ocr = time.perf_counter() - t
        original_texts = [item.get("text", "").strip() for item in ocr_results]

        t = time.perf_counter()
        translate_task = TRANSLATOR.translate_batch(
            original_texts, from_lang=CONFIG.source_lang, to_lang=CONFIG.target_lang
        )
        inpaint_task = asyncio.to_thread(
            INPAINTER.inpaint_from_boxes, image=image, crop_boxes=boxes, ocr_results=ocr_results
        )

        translated_texts, cleaned = await asyncio.gather(translate_task, inpaint_task)
        t_translate_inpaint = time.perf_counter() - t
        logger.debug(f"Translate + Inpaint took {t_translate_inpaint:.2f}s")

        final_img = cleaned.copy()
        for box, text, ocr_result in zip(boxes, translated_texts, ocr_results, strict=True):
            if text:
                final_img = RENDERER.draw_text_in_box(
                    final_img, str(text), box, font_size=int(CONFIG.font_size_ratio * ocr_result["font_size"])
                )

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


# =========================
# TRANSLATE COMIC ZIP
# =========================
@app.post("/translate_comic_zip")
async def translate_comic_zip(
    file: Annotated[UploadFile, File()],
    font_size_ratio: float = Form(CONFIG