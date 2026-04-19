import time
import torch
import numpy as np
import cv2
from inpainting.inpainter import Inpainter
from simple_lama_inpainting import SimpleLama


class LamaInpaintor(Inpainter):
    def __init__(self, device=None):
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.model = SimpleLama(device=self.device)

        print("LAMA model loaded on device:", self.device)

    # -------------------------
    # INPAINT
    # -------------------------
    def inpaint(self, image, mask):
        image = np.asarray(image, dtype=np.uint8)
        mask = np.asarray(mask, dtype=np.uint8)

        if mask.ndim == 3:
            mask = mask[:, :, 0]

        return self.model(image, mask)

    # -------------------------
    # EXPAND POLYGON
    # -------------------------
    def _expand_poly(self, pts, pad=6):
        """
        Expand polygon outward by simple bbox padding (stable & fast)
        """
        x_min = np.min(pts[:, 0]) - pad
        y_min = np.min(pts[:, 1]) - pad
        x_max = np.max(pts[:, 0]) + pad
        y_max = np.max(pts[:, 1]) + pad

        return np.array(
            [[x_min, y_min], [x_max, y_min], [x_max, y_max], [x_min, y_max]],
            dtype=np.int32,
        )

    # -------------------------
    # NORMALIZE POLY
    # -------------------------
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

    # -------------------------
    # MASK BUILD (IMPORTANT FIX)
    # -------------------------
    def create_mask_from_boxes(self, image_shape, boxes, pad=6):
        h, w = image_shape[:2]
        mask = np.zeros((h, w), dtype=np.uint8)

        valid = 0

        for i, pts_list in enumerate(boxes):
            pts = self._normalize_poly(pts_list)
            if pts is None:
                continue

            # expand box (bubble-friendly)
            pts = self._expand_poly(pts, pad=pad)

            cv2.fillPoly(mask, [pts], 255)
            valid += 1

        # -------------------------
        # MERGE OVERLAPPING REGIONS (KEY FIX)
        # -------------------------
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)

        # light dilation ONLY (avoid full image flood)
        kernel2 = np.ones((3, 3), np.uint8)
        mask = cv2.dilate(mask, kernel2, iterations=1)

        # ensure binary
        mask = (mask > 127).astype(np.uint8) * 255

        # -------------------------
        # DEBUG SAFETY CHECK
        # -------------------------
        coverage = np.sum(mask > 0) / mask.size

        if coverage > 0.6:
            mask = cv2.erode(mask, np.ones((3, 3), np.uint8), iterations=2)

        return mask

    # -------------------------
    # MAIN PIPELINE
    # -------------------------
    def inpaint_from_boxes(self, image, boxes):
        if boxes is None or len(boxes) == 0:
            return image

        image = np.asarray(image, dtype=np.uint8)

        mask = self.create_mask_from_boxes(image.shape, boxes, pad=8)

        if np.sum(mask) == 0:
            print("[MAIN] empty mask")
            return image

        result = self.inpaint(image, mask)
        result = np.array(result)
        result = result.astype(np.uint8)
        return result
