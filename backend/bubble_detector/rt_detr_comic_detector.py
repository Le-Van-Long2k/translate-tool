import time
from typing import List, Tuple
import logging

import numpy as np
import torch
from PIL import Image

from bubble_detector.bubble_detector import BubbleDetector

from transformers import (
    RTDetrImageProcessor,
    RTDetrV2ForObjectDetection,
)


logger = logging.getLogger("RTDETRComicDetector")


class RTDETRComicDetector(BubbleDetector):

    CLASSES = {
        0: "bubble",
        1: "text_bubble",
        2: "text_free",
    }

    def __init__(self):
        self.repo_id = "ogkalu/comic-text-and-bubble-detector"

        self.processor = None
        self.model = None

        self.device = (
            "cuda"
            if torch.cuda.is_available()
            else "cpu"
        )

    def load_model(self):
        self.processor = RTDetrImageProcessor.from_pretrained(
            self.repo_id
        )

        self.model = RTDetrV2ForObjectDetection.from_pretrained(
            self.repo_id
        )

        self.model.to(self.device)
        self.model.eval()

    def merge_overlapping_boxes(
        self,
        boxes: List[Tuple[int, int, int, int]]
    ) -> List[Tuple[int, int, int, int]]:
        """
        Merge các box bị chồng lấn thành một box lớn.

        Ví dụ:
            A overlap B
            B overlap C

        => A, B, C sẽ được merge thành một box.

        Box chỉ chạm cạnh nhau sẽ KHÔNG được merge.
        """

        if not boxes:
            return []

        # Copy để không thay đổi boxes gốc
        remaining = list(boxes)

        merged_boxes = []

        while remaining:

            # Lấy một box làm box hiện tại
            current = remaining.pop(0)

            x1, y1, x2, y2 = current

            changed = True

            # Tiếp tục tìm box overlap cho đến khi
            # không còn box nào có thể merge
            while changed:

                changed = False
                new_remaining = []

                for other in remaining:

                    ox1, oy1, ox2, oy2 = other

                    # Kiểm tra overlap
                    overlap = (
                        x1 < ox2
                        and x2 > ox1
                        and y1 < oy2
                        and y2 > oy1
                    )

                    if overlap:

                        # Merge thành bounding box lớn nhất
                        x1 = min(x1, ox1)
                        y1 = min(y1, oy1)
                        x2 = max(x2, ox2)
                        y2 = max(y2, oy2)

                        changed = True

                    else:
                        new_remaining.append(other)

                remaining = new_remaining

            merged_boxes.append(
                (x1, y1, x2, y2)
            )

        return merged_boxes

    def detect(
        self,
        image_path: str,
        conf: float = 0.5
    ) -> List[Tuple[int, int, int, int]]:

        if self.model is None:
            self.load_model()

        start_time = time.time()

        # ------------------------------------------
        # Load image
        # ------------------------------------------

        if isinstance(image_path, np.ndarray):
            image = Image.fromarray(image_path).convert("RGB")
        else:
            image = Image.open(image_path).convert("RGB")

        image_width = image.width
        image_height = image.height

        logger.debug(
            f"[RT-DETR] Image size: "
            f"{image_width}x{image_height}"
        )

        # ------------------------------------------
        # Preprocess
        # ------------------------------------------

        inputs = self.processor(
            images=image,
            return_tensors="pt",
        )

        inputs = {
            k: v.to(self.device)
            for k, v in inputs.items()
        }

        # ------------------------------------------
        # Detection
        # ------------------------------------------

        with torch.inference_mode():
            outputs = self.model(**inputs)

        target_sizes = torch.tensor(
            [[image_height, image_width]],
            device=self.device,
        )

        results = self.processor.post_process_object_detection(
            outputs,
            target_sizes=target_sizes,
            threshold=conf,
        )[0]

        boxes = []

        # ------------------------------------------
        # Box filtering settings
        # ------------------------------------------

        MIN_WIDTH = 10
        MIN_HEIGHT = 10

        # ------------------------------------------
        # Debug statistics
        # ------------------------------------------

        class_counts = {
            "bubble": 0,
            "text_bubble": 0,
            "text_free": 0,
        }

        logger.debug(
            "========== RT-DETR DETECTIONS =========="
        )

        # ------------------------------------------
        # Process detections
        # ------------------------------------------

        for score, label, box in zip(
            results["scores"],
            results["labels"],
            results["boxes"],
        ):
            class_id = label.item()

            class_name = self.CLASSES.get(
                class_id,
                f"unknown_{class_id}"
            )

            score_value = float(score)

            # Raw coordinates from model
            raw_x1, raw_y1, raw_x2, raw_y2 = box.tolist()

            class_counts[class_name] = (
                class_counts.get(class_name, 0) + 1
            )

            # ------------------------------------------
            # Convert coordinates to integer
            # ------------------------------------------

            x1 = int(raw_x1)
            y1 = int(raw_y1)
            x2 = int(raw_x2)
            y2 = int(raw_y2)

            logger.debug(
                f"class={class_name:<12} "
                f"id={class_id} "
                f"score={score_value:.4f} "
                f"raw_box=({x1}, {y1}, {x2}, {y2})"
            )

            # ------------------------------------------
            # Only keep text classes
            #
            # 1 = text_bubble
            # 2 = text_free
            # ------------------------------------------

            if class_id not in (1, 2):
                continue

            # ------------------------------------------
            # Clamp coordinates to image boundaries
            #
            # Example:
            #   y1 = -1
            #
            # becomes:
            #   y1 = 0
            #
            # This prevents NumPy slicing such as:
            #   image[-1:701]
            #
            # which can produce an empty crop.
            # ------------------------------------------

            original_box = (x1, y1, x2, y2)

            x1 = max(0, min(x1, image_width))
            y1 = max(0, min(y1, image_height))
            x2 = max(0, min(x2, image_width))
            y2 = max(0, min(y2, image_height))

            clamped_box = (x1, y1, x2, y2)

            if original_box != clamped_box:
                logger.debug(
                    f"[RT-DETR] Clamped box: "
                    f"{original_box} -> {clamped_box}"
                )

            # ------------------------------------------
            # Validate coordinates
            # ------------------------------------------

            if x2 <= x1 or y2 <= y1:
                logger.debug(
                    f"[RT-DETR] Skip invalid box: "
                    f"class={class_name} "
                    f"score={score_value:.4f} "
                    f"box={clamped_box}"
                )
                continue

            # ------------------------------------------
            # Calculate box size
            # ------------------------------------------

            width = x2 - x1
            height = y2 - y1

            logger.debug(
                f"[RT-DETR] Valid box: "
                f"class={class_name} "
                f"score={score_value:.4f} "
                f"box=({x1}, {y1}, {x2}, {y2}) "
                f"size=({width}x{height})"
            )

            # ------------------------------------------
            # Remove very small boxes
            # ------------------------------------------

            if width < MIN_WIDTH or height < MIN_HEIGHT:
                logger.debug(
                    f"[RT-DETR] Skip small box: "
                    f"class={class_name} "
                    f"score={score_value:.4f} "
                    f"box=({x1}, {y1}, {x2}, {y2}) "
                    f"size=({width}x{height})"
                )
                continue

            # ------------------------------------------
            # Add valid box
            # ------------------------------------------

            boxes.append(
                (
                    x1,
                    y1,
                    x2,
                    y2,
                )
            )

        # ------------------------------------------
        # Merge overlapping boxes
        # ------------------------------------------

        boxes_before_merge = len(boxes)

        boxes = self.merge_overlapping_boxes(boxes)

        boxes_after_merge = len(boxes)

        logger.debug(
            f"Boxes before merge : {boxes_before_merge}"
        )

        logger.debug(
            f"Boxes after merge  : {boxes_after_merge}"
        )

        # ------------------------------------------
        # Final validation after merge
        #
        # Safety check in case merge produces
        # unexpected coordinates.
        # ------------------------------------------

        valid_boxes = []

        for box in boxes:

            x1, y1, x2, y2 = box

            # Clamp again after merge
            x1 = max(0, min(x1, image_width))
            y1 = max(0, min(y1, image_height))
            x2 = max(0, min(x2, image_width))
            y2 = max(0, min(y2, image_height))

            width = x2 - x1
            height = y2 - y1

            if width <= 0 or height <= 0:
                logger.debug(
                    f"[RT-DETR] Skip invalid merged box: "
                    f"({x1}, {y1}, {x2}, {y2})"
                )
                continue

            if width < MIN_WIDTH or height < MIN_HEIGHT:
                logger.debug(
                    f"[RT-DETR] Skip small merged box: "
                    f"({x1}, {y1}, {x2}, {y2}) "
                    f"size=({width}x{height})"
                )
                continue

            valid_boxes.append(
                (
                    x1,
                    y1,
                    x2,
                    y2,
                )
            )

        boxes = valid_boxes

        # ------------------------------------------
        # Statistics
        # ------------------------------------------

        logger.debug("------------------------------------------")

        logger.debug(
            f"bubble      : {class_counts['bubble']}"
        )

        logger.debug(
            f"text_bubble : {class_counts['text_bubble']}"
        )

        logger.debug(
            f"text_free   : {class_counts['text_free']}"
        )

        logger.debug(
            f"returned    : {len(boxes)}"
        )

        logger.debug(
            "=========================================="
        )

        # ------------------------------------------
        # Timing
        # ------------------------------------------

        elapsed = time.time() - start_time

        logger.debug(
            f"RT-DETR Detection completed "
            f"in {elapsed:.3f} seconds"
        )

        return boxes

    def close(self) -> None:

        if self.model is not None:
            del self.model
            self.model = None

        self.processor = None

        if torch.cuda.is_available():
            torch.cuda.empty_cache()

        logger.debug(
            "RT-DETR detector closed"
        )