import numpy as np
import cv2

from inpainting.inpainter import Inpainter


class OpencvInpaintor(Inpainter):
    def __init__(self):
        print("OpencvInpaintor initialized")

    # def inpaint_from_boxes(self, image, boxes):
    #     if boxes is None or len(boxes) == 0:
    #         return image

    #     mask = np.zeros(image.shape[:2], dtype=np.uint8)

    #     for pts_list in boxes:
    #         pts = np.array(pts_list, dtype=np.int32)
    #         cv2.fillPoly(mask, [pts], 255)

    #     kernel = np.ones((5, 5), np.uint8)
    #     mask = cv2.dilate(mask, kernel, iterations=1)

    #     return cv2.inpaint(image, mask, 3, cv2.INPAINT_TELEA)
    def inpaint_from_boxes(self, image, boxes):
        if boxes is None or len(boxes) == 0:
            return image

        h, w = image.shape[:2]

        for pts_list in boxes:
            pts = np.array(pts_list, dtype=np.int32)

            # 1. Xác định vùng bao (Bounding Box) của đa giác
            x, y, bw, bh = cv2.boundingRect(pts)

            # 2. Thêm padding (khoảng đệm) để thuật toán lấy mẫu xung quanh tốt hơn
            pad = 10
            x1, y1 = max(0, x - pad), max(0, y - pad)
            x2, y2 = min(w, x + bw + pad), min(h, y + bh + pad)

            # 3. Cắt vùng ảnh và tạo mask cục bộ
            roi_img = image[y1:y2, x1:x2].copy()
            roi_mask = np.zeros((y2 - y1, x2 - x1), dtype=np.uint8)

            # Chỉnh lại tọa độ pts tương ứng với vùng cắt
            pts_shifted = pts - [x1, y1]
            cv2.fillPoly(roi_mask, [pts_shifted], 255)

            # Dilate mask cục bộ (nhanh hơn dilate mask toàn cục)
            kernel = np.ones((5, 5), np.uint8)
            roi_mask = cv2.dilate(roi_mask, kernel, iterations=1)

            # 4. Inpaint chỉ trên vùng ROI nhỏ
            roi_inpainted = cv2.inpaint(roi_img, roi_mask, 3, cv2.INPAINT_TELEA)

            # 5. Dán ngược lại ảnh gốc
            image[y1:y2, x1:x2] = roi_inpainted

        return image
