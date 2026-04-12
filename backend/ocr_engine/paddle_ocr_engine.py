import logging
import os
import numpy as np
import time

# Set TensorRT library path for PaddleOCR
tensorrt_lib_path = "/usr/local/TensorRT/lib"
current_ld_path = os.environ.get("LD_LIBRARY_PATH", "")
if tensorrt_lib_path not in current_ld_path:
    os.environ["LD_LIBRARY_PATH"] = f"{tensorrt_lib_path}:{current_ld_path}"

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
from paddleocr import PaddleOCR
from ocr_engine.ocr_engine import OCREngine
from typing import List, Union

logger = logging.getLogger(__name__)


class PaddleOCREngine(OCREngine):
    def __init__(self):
        self.ocr = PaddleOCR(
            text_detection_model_name="PP-OCRv5_server_det",
            text_recognition_model_name="PP-OCRv5_server_rec",
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            rec_batch_num=6,
            device="gpu",
            use_tensorrt=False,
            # precision="fp16",
        )
        print("PaddleOCR DET + REC initialized")

    def recognize(self, images: Union[np.ndarray, List[np.ndarray]]):
        """
        images: np.ndarray hoặc List[np.ndarray]
        """

        # đảm bảo luôn là list
        if isinstance(images, np.ndarray):
            images = [images]

        start_time = time.perf_counter()

        results = self.ocr.predict(images)

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
        # print(f"[PaddleOCR] Batch {len(images)} images in {end_time - start_time:.3f}s")

        return outputs
