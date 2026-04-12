import torch
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
from typing import List, Tuple
import numpy as np
from bubble_detector.bubble_detector import BubbleDetector

# import logging
import time

# logger = logging.getLogger(__name__)


class YOLOv8BubbleDetector(BubbleDetector):
    def __init__(self, repo_id: str = "ogkalu/comic-speech-bubble-detector-yolov8m"):
        self.repo_id = repo_id
        self.model = None
        print(f"YOLOv8BubbleDetector initialized with repo_id: {self.repo_id}")

    def load_model(self) -> None:
        model_path = hf_hub_download(
            repo_id=self.repo_id, filename="comic-speech-bubble-detector.pt"
        )
        self.model = YOLO(model_path)
        print(f"Model loaded from {self.repo_id}")

    def detect(
        self, image_path: str, conf: float = 0.25
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
                verbose=False,  # 🔥 tắt log
                stream=False,
                save=False,
                imgsz=480,
            )

        boxes = []
        for r in results:
            for box in r.boxes.xyxy.cpu().numpy():
                x1, y1, x2, y2 = map(int, box)
                boxes.append((x1, y1, x2, y2))
        end_time = time.time()
        print(
            f"[YOLOv8] Bubble Detection completed in {end_time - start_time:.3f} seconds"
        )
        print(f"Detected {len(boxes)} bubbles in image")
        return boxes
