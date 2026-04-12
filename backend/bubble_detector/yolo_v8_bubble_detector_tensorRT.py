import numpy as np
import time
from ultralytics import YOLO
from typing import List, Dict, Any
from pathlib import Path
from bubble_detector.bubble_detector import BubbleDetector


class YOLOv8TensorRT(BubbleDetector):
    """
    YOLOv8 TensorRT cho việc detect speech bubble trong comic.
    """

    def __init__(
        self,
        engine_path: str = str(Path(__file__).parent / "comic.engine"),
        device: str = "cuda:0",
    ):
        self.engine_path = engine_path
        self.device = device
        self.model = YOLO(self.engine_path)
        print(
            f"YOLOv8TensorRT initialized with engine: {engine_path}, device: {device}"
        )

    def detect(self, image: np.ndarray, conf: float = 0.25) -> List[Dict[str, Any]]:
        """Predict trên ảnh numpy array"""

        start = time.perf_counter()

        results = self.model.predict(
            source=image, device=self.device, conf=conf, imgsz=640, verbose=False
        )[0]

        boxes = []
        if results:
            for box in results[0].boxes or []:
                x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                boxes.append((int(x1), int(y1), int(x2), int(y2)))
        end = time.perf_counter()
        inference_time = end - start

        # print(
        #     f"[YOLOv8 TensorRT] Inference: {inference_time:.3f} s | "
        #     f"Detected {len(boxes)} bubbles"
        # )

        return boxes
