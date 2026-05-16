from enum import Enum
import asyncio
import gc
import logging
import time
from typing import Optional

import cv2
import numpy as np
import torch
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from bubble_detector.bubble_detector_factory import (
    BubbleDetectorFactory,
    BubbleDetectorType,
)
from ocr_engine.ocr_factory import (
    OCREngineFactory,
    OCREngineType,
)
from translator.translator_factory import (
    TranslatorFactory,
    TranslatorType,
)
from inpainting.inpainter_factory import (
    InpainterFactory,
    InpainterType,
)
from text_renderer.pil_centered_text import PILCenteredTextRenderer

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


# =========================
# GLOBAL LOCK
# Reject request nếu đang xử lý
# =========================

PROCESS_LOCK = asyncio.Lock()


# =========================
# ENUMS
# =========================

class SourceLang(str, Enum):
    en = "en"
    zh = "zh"
    ja = "ja"
    vi = "vi"
    ko = "ko"


class TargetLang(str, Enum):
    vi = "vi"


# =========================
# CONFIG MODEL
# =========================

class ConfigModel(BaseModel):
    font_size: Optional[int] = None
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
CONFIG.ocr_model = OCREngineType.PP_OCR_V5_MOBILE
CONFIG.inpaint_model = InpainterType.OPENCV
CONFIG.translate_model = TranslatorType.HY_MT1_5_1_8B_Q4_K_M
CONFIG.source_lang = SourceLang.en
CONFIG.target_lang = TargetLang.vi
CONFIG.font_size = 28


# =========================
# GLOBAL MODELS
# =========================

DETECTOR = None
OCR_ENGINE = None
TRANSLATOR = None
INPAINTER = None
RENDERER = None


# =========================
# MEMORY CLEANUP
# =========================

def clear_memory():
    gc.collect()

    if torch.cuda.is_available():
        torch.cuda.empty_cache()

    logger.info("Memory cleaned")


# =========================
# STARTUP
# =========================

@app.on_event("startup")
async def startup_event():
    global DETECTOR
    global OCR_ENGINE
    global TRANSLATOR
    global INPAINTER
    global RENDERER

    logger.info("Loading models...")

    DETECTOR = BubbleDetectorFactory.create(
        CONFIG.detect_model
    )

    OCR_ENGINE = OCREngineFactory.create(
        CONFIG.ocr_model
    )

    TRANSLATOR = TranslatorFactory.create(
        CONFIG.translate_model
    )

    INPAINTER = InpainterFactory.create(
        CONFIG.inpaint_model
    )

    RENDERER = PILCenteredTextRenderer()

    logger.info("Models loaded")


# =========================
# CONFIG API
# =========================

@app.post("/config")
async def set_config(cfg: ConfigModel):
    global DETECTOR
    global OCR_ENGINE
    global TRANSLATOR
    global INPAINTER
    global CONFIG

    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy"
        )

    async with PROCESS_LOCK:

        try:
            logger.info("Reloading models...")

            old_detector = DETECTOR
            old_ocr = OCR_ENGINE
            old_translator = TRANSLATOR
            old_inpainter = INPAINTER

            DETECTOR = None
            OCR_ENGINE = None
            TRANSLATOR = None
            INPAINTER = None

            del old_detector
            del old_ocr
            del old_translator
            del old_inpainter

            clear_memory()

            # update config
            if cfg.font_size is not None:
                CONFIG.font_size = cfg.font_size

            if cfg.source_lang is not None:
                CONFIG.source_lang = cfg.source_lang

            if cfg.target_lang is not None:
                CONFIG.target_lang = cfg.target_lang

            if cfg.detect_model is not None:
                CONFIG.detect_model = cfg.detect_model

            if cfg.ocr_model is not None:
                CONFIG.ocr_model = cfg.ocr_model

            if cfg.inpaint_model is not None:
                CONFIG.inpaint_model = cfg.inpaint_model

            if cfg.translate_model is not None:
                CONFIG.translate_model = cfg.translate_model

            # recreate
            DETECTOR = BubbleDetectorFactory.create(
                CONFIG.detect_model
            )

            OCR_ENGINE = OCREngineFactory.create(
                CONFIG.ocr_model
            )

            TRANSLATOR = TranslatorFactory.create(
                CONFIG.translate_model
            )

            INPAINTER = InpainterFactory.create(
                CONFIG.inpaint_model
            )

            logger.info("Models reloaded")

            return JSONResponse({
                "status": "ok",
                "config": CONFIG.model_dump()
            })

        except Exception as e:
            logger.exception("Config update failed")

            raise HTTPException(
                status_code=400,
                detail=f"Failed to update config: {e}"
            )


# =========================
# IMAGE READER
# =========================

def _read_image_from_upload(data: bytes):
    arr = np.frombuffer(data, np.uint8)

    img = cv2.imdecode(
        arr,
        cv2.IMREAD_COLOR
    )

    return img


# =========================
# TRANSLATE COMIC
# =========================

@app.post("/translate_comic")
async def translate_comic(
    file: UploadFile = File(...),
    font_size: Optional[int] = Form(None),
    conf_threshold: float = Form(0.25),
):
    global DETECTOR
    global OCR_ENGINE
    global TRANSLATOR
    global INPAINTER
    global RENDERER
    global CONFIG

    # reject nếu đang bận
    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy"
        )

    async with PROCESS_LOCK:

        start_time = time.perf_counter()

        data = await file.read()

        image = _read_image_from_upload(data)

        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        # detect
        try:
            with torch.inference_mode():
                boxes = DETECTOR.detect(
                    image,
                    conf_threshold
                )

        except Exception:
            logger.exception("Detection error")
            boxes = []

        # crop bubbles
        bubbles = []

        for (x1, y1, x2, y2) in boxes:

            x1 = int(x1)
            y1 = int(y1)
            x2 = int(x2)
            y2 = int(y2)

            crop = image[y1:y2, x1:x2]

            if crop.size > 0:
                bubbles.append(crop)

        # OCR
        try:
            ocr_results = (
                OCR_ENGINE.ocr(bubbles)
                if bubbles
                else []
            )

        except Exception:
            logger.exception("OCR error")
            ocr_results = []

        # extract text
        original_texts = [
            (item or {}).get("text", "").strip()
            for item in ocr_results
        ]

        # translate
        try:
            translated_texts = (
                await TRANSLATOR.translate_batch(
                    original_texts,
                    from_lang=CONFIG.source_lang,
                    to_lang=CONFIG.target_lang
                )
                if original_texts
                else []
            )

        except Exception:
            logger.exception("Translation error")
            translated_texts = []

        # inpaint
        try:
            cleaned = INPAINTER.inpaint_from_boxes(
                image=image.copy(),
                crop_boxes=boxes,
                ocr_results=ocr_results
            )

        except Exception:
            logger.exception("Inpaint error")

            cleaned = image.copy()

        # render
        final_img = cleaned

        fs = (
            int(font_size)
            if font_size is not None
            else CONFIG.font_size
        )

        for box, text in zip(boxes, translated_texts):

            if not text:
                continue

            try:
                final_img = RENDERER.draw_text_in_box(
                    final_img,
                    str(text).capitalize(),
                    box,
                    font_size=fs
                )

            except Exception:
                logger.exception("Render error")

        total = time.perf_counter() - start_time

        logger.info(f"Done in {total:.2f}s")

        success, buf = cv2.imencode(
            ".png",
            final_img
        )

        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to encode image"
            )

        return Response(
            content=buf.tobytes(),
            media_type="image/png",
            headers={
                "Content-Disposition":
                "attachment; filename=translated.png"
            },
        )


# =========================
# SINGLE BOX CHAT
# =========================

@app.post("/translate_one_box_chat")
async def translate_one_box_chat(
    file: UploadFile = File(...),
    box: str = Form(...),
):
    global OCR_ENGINE
    global TRANSLATOR
    global CONFIG

    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy"
        )

    async with PROCESS_LOCK:

        start = time.perf_counter()

        data = await file.read()

        image = _read_image_from_upload(data)

        if image is None:
            raise HTTPException(
                status_code=400,
                detail="Invalid image file"
            )

        try:
            x1, y1, x2, y2 = map(
                int,
                box.split(",")
            )

        except Exception:
            raise HTTPException(
                status_code=400,
                detail="Invalid box format"
            )

        h, w = image.shape[:2]

        x1 = max(0, min(x1, w))
        x2 = max(0, min(x2, w))
        y1 = max(0, min(y1, h))
        y2 = max(0, min(y2, h))

        if x2 <= x1 or y2 <= y1:
            raise HTTPException(
                status_code=400,
                detail="Invalid box coordinates"
            )

        crop = image[y1:y2, x1:x2]

        # OCR
        t0 = time.perf_counter()

        try:
            ocr_results = OCR_ENGINE.ocr([crop])

        except Exception:
            logger.exception("OCR error")
            ocr_results = []

        t_ocr = time.perf_counter() - t0

        orig = (
            (ocr_results[0] or {}).get("text", "").strip()
            if ocr_results
            else ""
        )

        # Translate
        t0 = time.perf_counter()

        try:
            translated = (
                await TRANSLATOR.translate(
                    orig,
                    from_lang=CONFIG.source_lang,
                    to_lang=CONFIG.target_lang
                )
                if orig
                else ""
            )

        except Exception:
            logger.exception("Translation error")
            translated = ""

        t_translate = time.perf_counter() - t0

        total = time.perf_counter() - start

        return JSONResponse({
            "original": orig,
            "translated": translated,
            "timings": {
                "ocr": round(t_ocr, 4),
                "translate": round(t_translate, 4),
                "total": round(total, 4),
            },
        })


# =========================
# HEALTH
# =========================

@app.get("/health")
async def health():

    return JSONResponse({
        "status": "ok",
        "busy": PROCESS_LOCK.locked(),
        "models": {
            "detector": DETECTOR is not None,
            "ocr": OCR_ENGINE is not None,
            "translator": TRANSLATOR is not None,
            "inpainter": INPAINTER is not None,
        }
    })


# =========================
# MAIN
# =========================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8052,
        workers=1,
    )