from contextlib import asynccontextmanager
from enum import Enum
import asyncio
import gc
import logging
import time
from typing import Optional
import threading
import cv2
import numpy as np
import torch
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import uvicorn

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
# Reject request nếu đang xử lý
# =========================

PROCESS_LOCK = asyncio.Lock()
MODEL_LOCK = threading.Lock()


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
CONFIG.ocr_model = OCREngineType.PP_OCR_V5_MOBILE
CONFIG.inpaint_model = InpainterType.OPENCV
CONFIG.translate_model = TranslatorType.HY_MT1_5_1_8B_Q4_K_M
CONFIG.source_lang = SourceLang.en
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

        DETECTOR = BubbleDetectorFactory.create(
            CONFIG.detect_model
        )

        OCR = OCREngineFactory.create(
            CONFIG.ocr_model
        )

        TRANSLATOR = TranslatorFactory.create(
            CONFIG.translate_model
        )

        INPAINTER = InpainterFactory.create(
            CONFIG.inpaint_model
        )

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

            for model in [
                DETECTOR,
                OCR,
                TRANSLATOR,
                INPAINTER
            ]:

                if model is not None:

                    if hasattr(model, "close"):
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
# =========================
# CLEAN MEMORY
# =========================

@app.post("/cleanup")
async def cleanup():

    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy"
        )

    async with PROCESS_LOCK:
        unload_models()

        return JSONResponse({
            "status": "ok",
            "message": "Memory cleaned"
        })

# =========================
# UNLOAD MODELS
# =========================

@app.post("/unload_models")
async def unload_models_api():

    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy"
        )

    async with PROCESS_LOCK:

        unload_models()

        return JSONResponse({
            "status": "ok",
            "message": "Models unloaded"
        })

# =========================
# RELOAD MODELS
# =========================

@app.post("/reload_models")
async def reload_models_api():

    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy"
        )

    async with PROCESS_LOCK:

        unload_models()

        load_models()

        return JSONResponse({
            "status": "ok",
            "message": "Models reloaded"
        })
    
# =========================
# CONFIG API
# =========================

@app.post("/config")
async def set_config(cfg: ConfigModel):

    global CONFIG

    if PROCESS_LOCK.locked():
        raise HTTPException(
            status_code=429,
            detail="Server is busy"
        )

    async with PROCESS_LOCK:

        changed = False

        if cfg.font_size_ratio is not None:
            CONFIG.font_size_ratio = cfg.font_size_ratio

        if cfg.source_lang is not None:
            CONFIG.source_lang = cfg.source_lang

        if cfg.target_lang is not None:
            CONFIG.target_lang = cfg.target_lang

        if (
            cfg.detect_model is not None
            and cfg.detect_model != CONFIG.detect_model
        ):
            CONFIG.detect_model = cfg.detect_model
            changed = True

        if (
            cfg.ocr_model is not None
            and cfg.ocr_model != CONFIG.ocr_model
        ):
            CONFIG.ocr_model = cfg.ocr_model
            changed = True

        if (
            cfg.inpaint_model is not None
            and cfg.inpaint_model != CONFIG.inpaint_model
        ):
            CONFIG.inpaint_model = cfg.inpaint_model
            changed = True

        if (
            cfg.translate_model is not None
            and cfg.translate_model != CONFIG.translate_model
        ):
            CONFIG.translate_model = cfg.translate_model
            changed = True

        # reload nếu đổi model
        if changed:
            reload_models()

        return JSONResponse({
            "status": "ok",
            "config": CONFIG.model_dump()
        })

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
        with torch.inference_mode():
            boxes = DETECTOR.detect(
                image,
                conf_threshold
            )

        # crop bubbles
        bubbles = [
            image[int(y1) : int(y2), int(x1) : int(x2)]
            for (x1, y1, x2, y2) in boxes
        ]

        # OCR
        ocr_results = OCR.ocr(bubbles)

        # translate
        original_texts = [item.get("text", "").strip() for item in ocr_results]
        translated_texts = await TRANSLATOR.translate_batch(
                original_texts,
                from_lang=CONFIG.source_lang,
                to_lang=CONFIG.target_lang
            )

        # inpaint
        cleaned = INPAINTER.inpaint_from_boxes(
            image=image,
            crop_boxes=boxes,
            ocr_results=ocr_results
        )

        # render
        final_img = cleaned.copy()
        CONFIG.font_size_ratio = font_size_ratio
        for box, text, ocr_result in zip(boxes, translated_texts, ocr_results):
            if text:
                final_img = RENDERER.draw_text_in_box(
                    final_img, str(text).capitalize(), box, font_size=int(CONFIG.font_size_ratio*ocr_result["font_size"]),
                )

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
):
    global OCR
    global TRANSLATOR
    global CONFIG
    ensure_models_loaded()

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

        # OCR
        ocr_results = OCR.ocr([image])


        # Translate
        original_texts = [item.get("text", "").strip() for item in ocr_results]
        translated_texts = await TRANSLATOR.translate_batch(
                original_texts,
                from_lang=CONFIG.source_lang,
                to_lang=CONFIG.target_lang
            )

        total = time.perf_counter() - start

        return JSONResponse({
            "original": original_texts[0] if original_texts else "",
            "translated": translated_texts[0] if translated_texts else "",
            "timings": round(total, 4),
        })


# =========================
# HEALTH
# =========================

@app.get("/health")
async def health():

    gpu_mem = None

    if torch.cuda.is_available():
        gpu_mem = {
            "allocated_mb":
                round(torch.cuda.memory_allocated() / 1024 / 1024, 2),

            "reserved_mb":
                round(torch.cuda.memory_reserved() / 1024 / 1024, 2),
        }

    return JSONResponse({
        "status": "ok",
        "busy": PROCESS_LOCK.locked(),
        "gpu": gpu_mem,
        "models": {
            "detector": DETECTOR is not None,
            "ocr": OCR is not None,
            "translator": TRANSLATOR is not None,
            "inpainter": INPAINTER is not None,
        }
    })


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