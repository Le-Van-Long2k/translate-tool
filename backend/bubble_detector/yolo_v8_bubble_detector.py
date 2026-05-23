import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import torch
from huggingface_hub import hf_hub_download
from ultralytics import YOLO

from bubble_detector.bubble_detector import BubbleDetector
from bubble_detector.convert_tensorrt.tensortRT import build_tensorrt_comic_engine

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

    def detect(self, image_path: str, conf: float = 0.1) -> List[Tuple[int, int, int, int]]:
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
        logger.debug(f"YOLOv8 Bubble Detection completed in {end_time - start_time:.3f} seconds")
        logger.debug(f"Detected {len(boxes)} bubbles in image")
        return boxes


class YOLOv8TensorRT(BubbleDetector):
    """
    YOLOv8 TensorRT for detect speech bubble in comic.
    """

    def __init__(self):
        self.engine_path = Path(__file__).parent / "comic.engine"
        if not self.engine_path.exists():
            logger.info(f"TensorRT engine not found at {self.engine_path}, building engine...")
            build_tensorrt_comic_engine()
        self.device = "cuda:0"
        self.model = YOLO(self.engine_path)
        logger.info(f"YOLOv8TensorRT Bubble Detector initialized with engine: {self.engine_path}")

    def _box_area(self, box):
        x1, y1, x2, y2 = box
        return max(0, x2 - x1) * max(0, y2 - y1)

    def _overlap_ratio(self, box1, box2):
        """
        overlap ratio based on smaller box area
        """
        x1 = max(box1[0], box2[0])
        y1 = max(box1[1], box2[1])
        x2 = min(box1[2], box2[2])
        y2 = min(box1[3], box2[3])

        inter_w = max(0, x2 - x1)
        inter_h = max(0, y2 - y1)

        inter_area = inter_w * inter_h

        area1 = self._box_area(box1)
        area2 = self._box_area(box2)

        smaller_area = min(area1, area2)

        if smaller_area == 0:
            return 0

        return inter_area / smaller_area

    def _filter_duplicate_boxes(self, boxes, overlap_thresh=0.8):
        """
        Remove duplicated boxes.
        If overlap > threshold, keep the larger box.
        """

        if not boxes:
            return []

        # sort by area descending
        boxes = sorted(boxes, key=self._box_area, reverse=True)

        kept_boxes = []

        for box in boxes:
            duplicated = False

            for kept in kept_boxes:
                overlap = self._overlap_ratio(box, kept)

                if overlap >= overlap_thresh:
                    duplicated = True
                    break

            if not duplicated:
                kept_boxes.append(box)

        return kept_boxes

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

            # remove duplicated boxes
            boxes = self._filter_duplicate_boxes(boxes, overlap_thresh=0.8)
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
