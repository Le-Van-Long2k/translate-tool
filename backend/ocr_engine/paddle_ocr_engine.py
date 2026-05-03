import logging
import os
import numpy as np
import time

from paddleocr import PaddleOCR
from ocr_engine.ocr_engine import OCREngine
from typing import List, Union

logger = logging.getLogger("OCR_ENGINE")


class PaddleOCREngine(OCREngine):
    def __init__(self, model_name: str = "PP-OCRv5_server"):
        text_detection_model_name = f"{model_name}_det"
        text_recognition_model_name = f"{model_name}_rec"
        self.model = PaddleOCR(
            text_detection_model_name=text_detection_model_name,
            text_recognition_model_name=text_recognition_model_name,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            rec_batch_num=16,
            device="gpu",
        )
        logger.info(
            f"PaddleOCR initialized: {text_detection_model_name} and {text_recognition_model_name}"
        )

    def ocr(self, images: Union[np.ndarray, List[np.ndarray]]):
        if isinstance(images, np.ndarray):
            images = [images]

        start_time = time.perf_counter()

        results = self.model.predict(images)

        outputs = []

        for res in results:
            if not res:
                outputs.append({"text": "", "boxes": []})
                continue

            texts_all = res.get("rec_texts", [])
            boxes_all = res.get("dt_polys", [])

            text_str = " ".join(texts_all)
            outputs.append({"text": text_str, "boxes": boxes_all})

        end_time = time.perf_counter()
        logger.debug(
            f"[PaddleOCR] Batch {len(images)} images in {end_time - start_time:.3f}s"
        )

        return outputs
