from pathlib import Path
import torch
from bubble_detector.convert_tensorrt.tensortRT import build_tensorrt_comic_engine
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
from typing import Any, Dict, List, Tuple
import numpy as np
from bubble_detector.bubble_detector import BubbleDetector
import time
import logging

logger = logging.getLogger("BUBBLE_DETECTOR")


class YOLOv8BubbleDetector(BubbleDetector):
    """
    YOLOv8 for detect speech bubble in comic.
    """

    def __init__(self):
        self.repo_id = "ogkalu/comic-speech-bubble-detector-yolov8m"
        self.model = None
        logger.info(f"YOLOv8 Bubble Detector initialized with repo_id: {self.repo_id}")

    def load_model(self) -> None:
        model_path = hf_hub_download(
            repo_id=self.repo_id, filename="comic-speech-bubble-detector.pt"
        )
        self.model = YOLO(model_path)
        logger.info(f"YOLOv8 Bubble Detector model loaded from {self.repo_id}")

    def detect(
        self, image_path: str, conf: float = 0.1
    ) -> List[Tuple[int, int, int, int]]:
        if self.model is None:
            self.load_model()

        start_time = time.time()

        with torch.inference_mode():
            results = self.model.predict(
                source=image_path,
                conf=conf,
                device=0,
                half=True,
                verbose=False,
                stream=False,
                save=False,
                imgsz=640,
            )

        boxes = []
        for r in results:
            if len(r.boxes) > 0:
                coords = r.boxes.xyxy.cpu().numpy().astype(int)

                for coord in coords:
                    x1, y1, x2, y2 = coord
                    boxes.append((x1, y1, x2, y2))
        end_time = time.time()
        logger.debug(
            f"YOLOv8 Bubble Detection completed in {end_time - start_time:.3f} seconds"
        )
        logger.debug(f"Detected {len(boxes)} bubbles in image")
        return boxes


class YOLOv8TensorRT(BubbleDetector):
    """
    YOLOv8 TensorRT for detect speech bubble in comic.
    """

    def __init__(self):
        self.engine_path = Path(__file__).parent / "comic.engine"
        if not self.engine_path.exists():
            logger.info(
                f"TensorRT engine not found at {self.engine_path}, building engine..."
            )
            build_tensorrt_comic_engine()
        self.device = "cuda:0"
        self.model = YOLO(self.engine_path)
        logger.info(
            f"YOLOv8TensorRT Bubble Detector initialized with engine: {self.engine_path}"
        )

    def detect(self, image: np.ndarray, conf: float = 0.1) -> List[Dict[str, Any]]:
        start_time = time.perf_counter()

        with torch.inference_mode():
            results = self.model.predict(
                source=image, device=self.device, conf=conf, imgsz=640, verbose=False
            )[0]

        boxes = []
        if len(results.boxes) > 0:
            coords = results.boxes.xyxy.cpu().numpy().astype(int)
            
            for coord in coords:
                x1, y1, x2, y2 = coord
                boxes.append((x1, y1, x2, y2))
        end_time = time.perf_counter()

        logger.debug(
            f"YOLOv8TensorRT Bubble Detection completed in {end_time - start_time:.3f} seconds"
        )
        logger.debug(f"Detected {len(boxes)} bubbles in image")

        return boxes

    def close(self):

        logger.info("Closing TensorRT detector...")

        try:

            if self.model is not None:

                predictor = getattr(self.model, "predictor", None)

                if predictor is not None:

                    predictor.model = None

                self.model = None

        except Exception:
            logger.exception("Failed to close TensorRT detector")