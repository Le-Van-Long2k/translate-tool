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
RENDERER = PILCenteredTextRenderer()


# =========================
# MEMORY CLEANUP
# =========================

def clear_memory():
    gc.collect()
    if torch.cuda.is_available():
        with torch.cuda.device(torch.cuda.current_device()):
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

    logger.info("🧹 Đã dọn dẹp sạch sẽ VRAM và RAM.")

# =========================
# MODEL MANAGER
# =========================
def load_models():
    global DETECTOR
    global OCR_ENGINE
    global TRANSLATOR
    global INPAINTER

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

    logger.info("Models loaded")

def unload_models():
    global DETECTOR
    global OCR_ENGINE
    global TRANSLATOR
    global INPAINTER

    logger.info("Unloading models...")

    try:
        if DETECTOR in globals():
            del DETECTOR

        if OCR_ENGINE in globals():
            del OCR_ENGINE

        if TRANSLATOR in globals():
            del TRANSLATOR

        if INPAINTER in globals():
            del INPAINTER

    except Exception:
        logger.exception("Error while unloading models")

    DETECTOR = None
    OCR_ENGINE = None
    TRANSLATOR = None
    INPAINTER = None

    clear_memory()

    logger.info("Models unloaded")


# =========================
# STARTUP
# =========================

@app.on_event("startup")
async def startup_event():
    load_models()

@app.on_event("shutdown")
async def shutdown_event():
    unload_models()

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

            # update config
            if cfg.font_size != CONFIG.font_size:
                CONFIG.font_size = cfg.font_size

            if cfg.source_lang != CONFIG.source_lang:
                CONFIG.source_lang = cfg.source_lang

            if cfg.target_lang != CONFIG.target_lang:
                CONFIG.target_lang = cfg.target_lang

            if cfg.detect_model != CONFIG.detect_model:
                del DETECTOR
                CONFIG.detect_model = cfg.detect_model
                DETECTOR = BubbleDetectorFactory.create(
                    CONFIG.detect_model
                )

            if cfg.ocr_model != CONFIG.ocr_model:
                del OCR_ENGINE
                CONFIG.ocr_model = cfg.ocr_model
                OCR_ENGINE = OCREngineFactory.create(
                    CONFIG.ocr_model
                )

            if cfg.inpaint_model != CONFIG.inpaint_model:
                del INPAINTER
                CONFIG.inpaint_model = cfg.inpaint_model
                INPAINTER = InpainterFactory.create(
                    CONFIG.inpaint_model
                )

            if cfg.translate_model != CONFIG.translate_model:
                del TRANSLATOR
                CONFIG.translate_model = cfg.translate_model
                TRANSLATOR = TranslatorFactory.create(
                    CONFIG.translate_model
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
    font_size: Optional[int] = Form(CONFIG.font_size),
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
        ocr_results = OCR_ENGINE.ocr(bubbles)

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
        CONFIG.font_size = font_size
        for box, text in zip(boxes, translated_texts):
            if text:
                final_img = RENDERER.draw_text_in_box(
                    final_img, str(text).capitalize(), box, font_size=CONFIG.font_size
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

        h, w = image.shape[:2]

        # OCR
        ocr_results = OCR_ENGINE.ocr([image])


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