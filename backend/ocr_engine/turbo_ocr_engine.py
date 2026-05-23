import logging
import time
from typing import List, Union

import cv2
import numpy as np
import requests

from ocr_engine.ocr_engine import OCREngine

logger = logging.getLogger("OCR_ENGINE")


class TurboOCREngine(OCREngine):
    def __init__(self, model_name: str):
        self.api_url = "http://turboocr:8000/ocr/raw"

        logger.info(f"TurboOCR API initialized: {self.api_url} - {model_name}")

    def _calculate_font_size(self, boxes):
        """
        Calculate font size from bounding boxes.
        """
        if not boxes:
            return 0

        font_sizes = []

        for box in boxes:
            box_array = np.array(box)

            if len(box_array) > 0:
                y_coords = box_array[:, 1]
                height = np.max(y_coords) - np.min(y_coords)
                font_sizes.append(int(height))

        avg_font_size = np.mean(font_sizes) if font_sizes else 0

        return int(avg_font_size)

    def _image_to_bytes(self, image: np.ndarray):
        """
        Convert OpenCV image to jpg bytes.
        """

        success, encoded_image = cv2.imencode(".jpg", image)

        if not success:
            raise ValueError("Failed to encode image")

        return encoded_image.tobytes()

    def ocr(self, images: Union[np.ndarray, List[np.ndarray]]):

        if isinstance(images, np.ndarray):
            images = [images]

        outputs = []

        start_time = time.perf_counter()

        for image in images:
            try:
                image_bytes = self._image_to_bytes(image)

                response = requests.post(
                    self.api_url,
                    headers={"Content-Type": "image/jpeg"},
                    data=image_bytes,
                    timeout=120,
                )

                response.raise_for_status()

                result_json = response.json()

                results = result_json.get("results", [])

                texts_all = []
                boxes_all = []

                for item in results:
                    text = item.get("text", "")
                    box = item.get("bounding_box", [])

                    if text:
                        texts_all.append(text)

                    if box:
                        boxes_all.append(box)

                text_str = " ".join(texts_all)

                font_size = self._calculate_font_size(boxes_all)

                outputs.append(
                    {
                        "text": text_str,
                        "boxes": boxes_all,
                        "font_size": font_size,
                    }
                )

            except Exception:
                logger.exception("TurboOCR request failed")

                outputs.append(
                    {
                        "text": "",
                        "boxes": [],
                        "font_size": 0,
                    }
                )

        end_time = time.perf_counter()

        logger.debug(f"[TurboOCR] Batch {len(images)} images in {end_time - start_time:.3f}s")

        return outputs

    def close(self):

        logger.info("Closing TurboOCR Engine...")
