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

    # ================================================================
    # MODEL
    # ================================================================

    def load_model(self):
        logger.info(
            f"[RT-DETR] Loading model: {self.repo_id}"
        )

        self.processor = RTDetrImageProcessor.from_pretrained(
            self.repo_id
        )

        self.model = RTDetrV2ForObjectDetection.from_pretrained(
            self.repo_id
        )

        self.model.to(self.device)
        self.model.eval()

        logger.info(
            f"[RT-DETR] Model loaded on {self.device}"
        )

    # ================================================================
    # GEOMETRY HELPERS
    # ================================================================

    @staticmethod
    def box_area(
        box: Tuple[int, int, int, int]
    ) -> int:
        """
        Diện tích box.
        """
        x1, y1, x2, y2 = box

        return max(0, x2 - x1) * max(
            0,
            y2 - y1
        )

    @staticmethod
    def overlap_area(
        box1: Tuple[int, int, int, int],
        box2: Tuple[int, int, int, int],
    ) -> int:
        """
        Diện tích phần giao nhau giữa 2 box.
        """

        x1, y1, x2, y2 = box1
        ox1, oy1, ox2, oy2 = box2

        overlap_x = max(
            0,
            min(x2, ox2) - max(x1, ox1)
        )

        overlap_y = max(
            0,
            min(y2, oy2) - max(y1, oy1)
        )

        return overlap_x * overlap_y

    @classmethod
    def coverage_ratio(
        cls,
        inner_box: Tuple[int, int, int, int],
        outer_box: Tuple[int, int, int, int],
    ) -> float:
        """
        Tính bao nhiêu % diện tích inner_box
        nằm bên trong outer_box.

        Ví dụ:

            inner_box nằm hoàn toàn trong outer_box
            -> 1.0

            80% inner_box nằm trong outer_box
            -> 0.8
        """

        inner_area = cls.box_area(inner_box)

        if inner_area <= 0:
            return 0.0

        overlap = cls.overlap_area(
            inner_box,
            outer_box
        )

        return overlap / inner_area

    # ================================================================
    # SAME CLASS FILTER
    # ================================================================

    def filter_same_class(
        self,
        items: List[dict],
        class_name: str,
        threshold: float = 0.70,
    ) -> List[dict]:
        """
        Lọc các box trùng trong CÙNG một class.

        Nếu box lớn chiếm >70% diện tích box nhỏ:
            -> bỏ box nhỏ.

        Nếu <=70%:
            -> giữ cả hai.

        Không bao giờ so sánh box giữa các class khác nhau.
        """

        if len(items) <= 1:
            return items

        keep = [True] * len(items)

        for i in range(len(items)):

            if not keep[i]:
                continue

            small_box = items[i]["box"]

            small_area = self.box_area(
                small_box
            )

            if small_area <= 0:
                keep[i] = False
                continue

            for j in range(len(items)):

                if i == j:
                    continue

                if not keep[i]:
                    break

                large_box = items[j]["box"]

                large_area = self.box_area(
                    large_box
                )

                # Chỉ xét khi j thực sự lớn hơn i
                if large_area <= small_area:
                    continue

                overlap = self.overlap_area(
                    small_box,
                    large_box
                )

                if overlap <= 0:
                    continue

                # Bao nhiêu % box nhỏ bị box lớn chiếm
                coverage = overlap / small_area

                if coverage > threshold:

                    keep[i] = False

                    logger.debug(
                        "[RT-DETR] Same-class duplicate removed: "
                        f"class={class_name} "
                        f"small={small_box} "
                        f"large={large_box} "
                        f"small_coverage={coverage:.2%} "
                        f"threshold={threshold:.2%}"
                    )

                    break

        return [
            item
            for item, should_keep in zip(
                items,
                keep
            )
            if should_keep
        ]

    # ================================================================
    # MIN SIZE FILTER
    # ================================================================

    def filter_min_size(
        self,
        items: List[dict],
        class_name: str,
        min_width: int = 15,
        min_height: int = 15,
    ) -> List[dict]:
        """
        Loại box có width hoặc height < 15.
        """

        filtered = []

        for item in items:

            x1, y1, x2, y2 = item["box"]

            width = x2 - x1
            height = y2 - y1

            if width < min_width or height < min_height:

                logger.debug(
                    "[RT-DETR] Remove small box: "
                    f"class={class_name} "
                    f"box={item['box']} "
                    f"size={width}x{height}"
                )

                continue

            filtered.append(item)

        return filtered

    # ================================================================
    # REMOVE TEXT INSIDE BUBBLE
    # ================================================================

    def filter_text_inside_bubbles(
        self,
        text_items: List[dict],
        bubble_items: List[dict],
        class_name: str,
        threshold: float = 0.80,
    ) -> List[dict]:
        """
        Nếu text_bubble hoặc text_free có >80%
        diện tích nằm trong bubble:

            -> bỏ text
            -> giữ bubble

        Nếu <=80%:

            -> giữ text.
        """

        if not text_items or not bubble_items:
            return text_items

        bubble_boxes = [
            item["box"]
            for item in bubble_items
        ]

        filtered = []

        for item in text_items:

            text_box = item["box"]

            inside_bubble = False

            for bubble_box in bubble_boxes:

                coverage = self.coverage_ratio(
                    text_box,
                    bubble_box
                )

                if coverage > threshold:

                    inside_bubble = True

                    logger.debug(
                        "[RT-DETR] Remove text inside bubble: "
                        f"class={class_name} "
                        f"text={text_box} "
                        f"bubble={bubble_box} "
                        f"coverage={coverage:.2%} "
                        f"threshold={threshold:.2%}"
                    )

                    break

            if not inside_bubble:
                filtered.append(item)

        return filtered

    # ================================================================
    # DETECT
    # ================================================================

    def detect(
        self,
        image_path: str,
        conf: float = 0.2,
    ) -> List[Tuple[int, int, int, int]]:
        conf = 0.2 # allways use 0.2 for RT-DETR comic detector

        # ------------------------------------------------------------
        # Model
        # ------------------------------------------------------------

        if self.model is None:
            self.load_model()

        start_time = time.time()

        # ------------------------------------------------------------
        # Load image
        # ------------------------------------------------------------

        if isinstance(image_path, np.ndarray):

            image = Image.fromarray(
                image_path
            ).convert("RGB")

        else:

            image = Image.open(
                image_path
            ).convert("RGB")

        image_width = image.width
        image_height = image.height

        logger.debug(
            "[RT-DETR] Image size: "
            f"{image_width}x{image_height}"
        )

        # ------------------------------------------------------------
        # Preprocess
        # ------------------------------------------------------------

        inputs = self.processor(
            images=image,
            return_tensors="pt",
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        # ------------------------------------------------------------
        # Inference
        # ------------------------------------------------------------

        with torch.inference_mode():

            outputs = self.model(
                **inputs
            )

        # ------------------------------------------------------------
        # Post process
        # ------------------------------------------------------------

        target_sizes = torch.tensor(
            [[image_height, image_width]],
            device=self.device,
        )

        results = (
            self.processor
            .post_process_object_detection(
                outputs,
                target_sizes=target_sizes,
                threshold=conf,
            )[0]
        )

        # ============================================================
        # 1. COLLECT RAW DETECTIONS
        # ============================================================

        detected_items = []

        logger.debug(
            "========== RT-DETR DETECTIONS =========="
        )

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

            raw_x1, raw_y1, raw_x2, raw_y2 = (
                box.tolist()
            )

            x1 = int(raw_x1)
            y1 = int(raw_y1)
            x2 = int(raw_x2)
            y2 = int(raw_y2)

            logger.debug(
                f"class={class_name:<12} "
                f"id={class_id} "
                f"score={score_value:.4f} "
                f"raw_box="
                f"({x1}, {y1}, {x2}, {y2})"
            )

            # --------------------------------------------------------
            # Only 3 supported classes
            # --------------------------------------------------------

            if class_id not in (0, 1, 2):
                logger.debug(
                    "[RT-DETR] Ignore unknown class: "
                    f"id={class_id}"
                )
                continue

            # --------------------------------------------------------
            # Clamp coordinates
            # --------------------------------------------------------

            x1 = max(
                0,
                min(x1, image_width)
            )

            y1 = max(
                0,
                min(y1, image_height)
            )

            x2 = max(
                0,
                min(x2, image_width)
            )

            y2 = max(
                0,
                min(y2, image_height)
            )

            # --------------------------------------------------------
            # Invalid box
            # --------------------------------------------------------

            if x2 <= x1 or y2 <= y1:

                logger.debug(
                    "[RT-DETR] Ignore invalid box: "
                    f"({x1}, {y1}, {x2}, {y2})"
                )

                continue

            detected_items.append(
                {
                    "class_id": class_id,
                    "class_name": class_name,
                    "box": (x1, y1, x2, y2),
                    "score": score_value,
                }
            )

        # ============================================================
        # 2. SPLIT 3 CLASSES
        # ============================================================

        bubble_items = [
            item
            for item in detected_items
            if item["class_id"] == 0
        ]

        text_bubble_items = [
            item
            for item in detected_items
            if item["class_id"] == 1
        ]

        text_free_items = [
            item
            for item in detected_items
            if item["class_id"] == 2
        ]

        logger.debug(
            "[RT-DETR] Raw classes: "
            f"bubble={len(bubble_items)}, "
            f"text_bubble={len(text_bubble_items)}, "
            f"text_free={len(text_free_items)}"
        )

        # ============================================================
        # 3. SAME CLASS DUPLICATE FILTER
        #
        # 70%
        # ============================================================

        bubble_items = self.filter_same_class(
            bubble_items,
            class_name="bubble",
            threshold=0.70,
        )

        text_bubble_items = self.filter_same_class(
            text_bubble_items,
            class_name="text_bubble",
            threshold=0.70,
        )

        text_free_items = self.filter_same_class(
            text_free_items,
            class_name="text_free",
            threshold=0.70,
        )

        logger.debug(
            "[RT-DETR] After same-class filter: "
            f"bubble={len(bubble_items)}, "
            f"text_bubble={len(text_bubble_items)}, "
            f"text_free={len(text_free_items)}"
        )

        # ============================================================
        # 4. SPECIAL BUBBLE FILTER
        #
        # text_bubble/text_free nằm >80% trong bubble
        # -> bỏ text
        #
        # bubble luôn giữ
        # ============================================================

        text_bubble_items = (
            self.filter_text_inside_bubbles(
                text_items=text_bubble_items,
                bubble_items=bubble_items,
                class_name="text_bubble",
                threshold=0.80,
            )
        )

        text_free_items = (
            self.filter_text_inside_bubbles(
                text_items=text_free_items,
                bubble_items=bubble_items,
                class_name="text_free",
                threshold=0.80,
            )
        )

        logger.debug(
            "[RT-DETR] After bubble filter: "
            f"bubble={len(bubble_items)}, "
            f"text_bubble={len(text_bubble_items)}, "
            f"text_free={len(text_free_items)}"
        )

        # ============================================================
        # 5. MINIMUM SIZE FILTER
        #
        # width < 15 OR height < 15 -> remove
        # ============================================================

        bubble_items = self.filter_min_size(
            bubble_items,
            class_name="bubble",
            min_width=15,
            min_height=15,
        )

        text_bubble_items = self.filter_min_size(
            text_bubble_items,
            class_name="text_bubble",
            min_width=15,
            min_height=15,
        )

        text_free_items = self.filter_min_size(
            text_free_items,
            class_name="text_free",
            min_width=15,
            min_height=15,
        )

        logger.debug(
            "[RT-DETR] After minimum-size filter: "
            f"bubble={len(bubble_items)}, "
            f"text_bubble={len(text_bubble_items)}, "
            f"text_free={len(text_free_items)}"
        )

        # ============================================================
        # 6. FINAL MERGE
        #
        # Từ đây không còn phân biệt class.
        # ============================================================

        final_items = (
            bubble_items
            + text_bubble_items
            + text_free_items
        )

        final_boxes = [
            item["box"]
            for item in final_items
        ]

        # ============================================================
        # FINAL LOG
        # ============================================================

        logger.debug(
            "========== RT-DETR FINAL =========="
        )

        for index, item in enumerate(
            final_items,
            start=1,
        ):

            logger.debug(
                f"[RT-DETR] FINAL #{index}: "
                f"class={item['class_name']} "
                f"score={item['score']:.4f} "
                f"box={item['box']}"
            )

        elapsed = time.time() - start_time

        logger.info(
            "RT-DETR Detection completed "
            f"in {elapsed:.3f} seconds | "
            f"bubble={len(bubble_items)}, "
            f"text_bubble={len(text_bubble_items)}, "
            f"text_free={len(text_free_items)}, "
            f"total={len(final_boxes)}"
        )

        return final_boxes

    # ================================================================
    # CLOSE
    # ================================================================

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
