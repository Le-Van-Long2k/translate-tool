from enum import Enum
from typing import Union

from bubble_detector.bubble_detector import BubbleDetector
from bubble_detector.rt_detr_comic_detector import RTDETRComicDetector
from bubble_detector.yolo_v8_bubble_detector import (
    YOLOv8BubbleDetector,
    YOLOv8TensorRT,
)


class BubbleDetectorType(str, Enum):
    YOLOV8 = "yolov8"
    YOLOV8_TENSORRT = "yolov8_tensorrt"
    RTDETR_COMIC_DETECTOR = "rt_detr_comic_detector"


MODEL_REGISTRY = {
    BubbleDetectorType.YOLOV8: YOLOv8BubbleDetector,
    BubbleDetectorType.YOLOV8_TENSORRT: YOLOv8TensorRT,
    BubbleDetectorType.RTDETR_COMIC_DETECTOR: RTDETRComicDetector,
}


class BubbleDetectorFactory:
    @staticmethod
    def create(model_type: Union[str, BubbleDetectorType]) -> BubbleDetector:
        if isinstance(model_type, str):
            model_type = BubbleDetectorType(model_type)

        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        return MODEL_REGISTRY[model_type]()
