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

    def _calculate_font_size(self, boxes):
        """
        Calculate font size from bounding boxes.
        For horizontal text, use the height of the box as font size.
        Returns list of font sizes and average font size.
        """
        if not boxes:
            return [], 0
        
        font_sizes = []
        for box in boxes:
            # box is a polygon (typically 4 points for horizontal text)
            box_array = np.array(box)
            
            # Calculate height: difference between max and min y-coordinates
            if len(box_array) > 0:
                y_coords = box_array[:, 1]
                height = np.max(y_coords) - np.min(y_coords)
                font_sizes.append(int(height))
        
        avg_font_size = np.mean(font_sizes) if font_sizes else 0
        return int(avg_font_size)

    def ocr(self, images: Union[np.ndarray, List[np.ndarray]]):
        if isinstance(images, np.ndarray):
            images = [images]

        start_time = time.perf_counter()

        results = self.model.predict(images)

        outputs = []

        for res in results:
            if not res:
                outputs.append({"text": "", "boxes": [], "font_size": 0})
                continue

            texts_all = res.get("rec_texts", [])
            boxes_all = res.get("dt_polys", [])

            text_str = " ".join(texts_all)
            font_size = self._calculate_font_size(boxes_all)
            logger.debug(f"font_size: {font_size} for text: {text_str}")
            
            outputs.append({
                "text": text_str,
                "boxes": boxes_all,
                "font_size": font_size,
            })

        end_time = time.perf_counter()
        
        logger.debug(
            f"[PaddleOCR] Batch {len(images)} images in {end_time - start_time:.3f}s"
        )

        return outputs

    def close(self):

        logger.info("Closing PaddleOCR...")

        try:

            if self.model is not None:

                # release internals
                if hasattr(self.model, "text_detector"):
                    self.model.text_detector = None

                if hasattr(self.model, "text_recognizer"):
                    self.model.text_recognizer = None

                if hasattr(self.model, "text_classifier"):
                    self.model.text_classifier = None

                self.model = None

        except Exception:
            logger.exception("Failed to close PaddleOCR")