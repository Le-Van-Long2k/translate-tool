import numpy as np
import cv2

from inpainting.inpainter import Inpainter
import time
import logging

logger = logging.getLogger("OpencvInpaintor")

class OpencvInpaintor(Inpainter):
    def __init__(self):
        print("OpencvInpaintor initialized")

    def _normalize_poly(self, pts):
        if pts is None:
            return None

        pts = np.array(pts)

        if pts.size == 0:
            return None

        pts = np.squeeze(pts)

        if pts.ndim == 1:
            pts = pts.reshape(-1, 2)

        if pts.shape[0] < 3:
            return None

        return pts.astype(np.int32)

    def create_local_mask(self, crop_shape, local_boxes, pad=4):
        h, w = crop_shape[:2]

        mask = np.zeros((h, w), dtype=np.uint8)

        for pts in local_boxes:

            pts = self._normalize_poly(pts)

            if pts is None:
                continue

            x_min = max(0, np.min(pts[:, 0]) - pad)
            y_min = max(0, np.min(pts[:, 1]) - pad)

            x_max = min(w - 1, np.max(pts[:, 0]) + pad)
            y_max = min(h - 1, np.max(pts[:, 1]) + pad)

            expanded = np.array(
                [
                    [x_min, y_min],
                    [x_max, y_min],
                    [x_max, y_max],
                    [x_min, y_max],
                ],
                dtype=np.int32,
            )

            cv2.fillPoly(mask, [expanded], 255)

        # merge nearby regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # small dilation
        mask = cv2.dilate(mask, np.ones((3, 3), np.uint8), iterations=1)

        mask = (mask > 127).astype(np.uint8) * 255

        return mask

    def inpaint(self, image, mask):
        image = np.asarray(image, dtype=np.uint8)
        mask = np.asarray(mask, dtype=np.uint8)

        if mask.ndim == 3:
            mask = mask[:, :, 0]

        return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)

    def inpaint_from_boxes(self, image, crop_boxes, ocr_results, pad=4, debug_dir=None):
        """Inpaint using OpenCV over crops defined by `crop_boxes` and polygon boxes
        provided inside `ocr_results` (each item should be a dict with key 'boxes').
        Behavior follows `LamaInpaintor.inpaint_from_boxes` but uses OpenCV inpainting.
        """
        start_time = time.perf_counter()

        image = np.asarray(image, dtype=np.uint8)

        output = image.copy()

        for i, item in enumerate(ocr_results):

            if i >= len(crop_boxes):
                continue

            x1, y1, x2, y2 = map(int, crop_boxes[i])

            # clamp
            x1 = max(0, x1)
            y1 = max(0, y1)

            x2 = min(output.shape[1], x2)
            y2 = min(output.shape[0], y2)

            if x2 <= x1 or y2 <= y1:
                continue

            crop = output[y1:y2, x1:x2].copy()

            local_boxes = item.get("boxes") or []

            if len(local_boxes) == 0:
                continue

            mask = self.create_local_mask(crop.shape, local_boxes, pad=pad)

            if not mask.any():
                continue

            inpainted_crop = self.inpaint(crop, mask)

            inpainted_crop = np.asarray(inpainted_crop).astype(np.uint8)

            target_h = y2 - y1
            target_w = x2 - x1

            if inpainted_crop.shape[:2] != (target_h, target_w):
                inpainted_crop = cv2.resize(inpainted_crop, (target_w, target_h), interpolation=cv2.INTER_LINEAR)

            output[y1:y2, x1:x2] = inpainted_crop

        elapsed = time.perf_counter() - start_time
        logger.info(f"[OpencvInpaintor] Inpainted in {elapsed:.3f}s")
        return output
