import logging

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from text_renderer.text_renderer import TextRenderer

logger = logging.getLogger("TEXT_RENDERER")


class PILCenteredTextRenderer(TextRenderer):
    def __init__(self, font_path: str = "/usr/share/fonts/truetype/noto/NotoSans-Medium.ttf"):
        self.font_path = font_path
        logger.info(f"PILCenteredTextRenderer initialized with font: {self.font_path}")

    def wrap_text_pixel(self, draw, text, font, max_width):
        words = text.split()
        lines = []
        current_line = ""

        for word in words:
            test_line = word if current_line == "" else current_line + " " + word

            bbox = draw.textbbox((0, 0), test_line, font=font)
            w = bbox[2] - bbox[0]

            if w <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word

        if current_line:
            lines.append(current_line)

        return lines

    def draw_text_in_box(
        self,
        image: np.ndarray,
        text: str,
        box: tuple[int, int, int, int],
        font_size: int,
    ) -> np.ndarray:

        x1, y1, x2, y2 = box
        w, h = x2 - x1, y2 - y1

        if w < 20 or h < 20:
            return image

        scale_hw = 0.8
        target_w = int(w * scale_hw)
        target_h = int(h * scale_hw)

        padding_x = (w - target_w) // 2
        padding_y = (h - target_h) // 2

        pil_img = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_img)

        min_font_size = max(6, int(font_size * 0.4))
        max_font_size = max(min_font_size, int(font_size * 1.0))

        best_font = None
        best_lines = None
        best_line_height = None

        # lưu fallback nhỏ nhất
        fallback_font = None
        fallback_lines = None
        fallback_line_height = None

        # tạo 6 giá trị từ max -> min
        font_sizes = np.linspace(max_font_size, min_font_size, 6, dtype=int)

        # tránh duplicate do ép int
        font_sizes = sorted(set(font_sizes), reverse=True)

        for current_size in font_sizes:
            logger.debug(f"Trying font size: {current_size} for box: {box}")

            try:
                font = ImageFont.truetype(self.font_path, current_size)
            except OSError:
                logger.warning("Invalid font path or font size")
                return image

            # wrap theo pixel
            lines = self.wrap_text_pixel(draw, text, font, target_w)

            if not lines:
                continue

            line_height = int(current_size * 1.3)

            # lưu fallback nhỏ nhất
            fallback_font = font
            fallback_lines = lines
            fallback_line_height = line_height

            total_h = line_height * len(lines)

            # check fit chiều dọc
            if total_h > target_h:
                continue

            # check fit chiều ngang
            fits = True

            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)

                line_w = bbox[2] - bbox[0]

                if line_w > target_w:
                    fits = False
                    break

            if fits:
                best_font = font
                best_lines = lines
                best_line_height = line_height
                break

        # nếu không fit được -> dùng size nhỏ nhất
        if best_font is None:
            logger.debug(f"No font fits box {box}, using smallest font")

            best_font = fallback_font
            best_lines = fallback_lines
            best_line_height = fallback_line_height

        if best_font is None or best_lines is None:
            return image

        total_h = best_line_height * len(best_lines)

        # căn giữa dọc trong vùng
        y = y1 + padding_y + (target_h - total_h) // 2

        for line in best_lines:
            bbox = draw.textbbox((0, 0), line, font=best_font)

            line_w = bbox[2] - bbox[0]

            # căn giữa ngang trong vùng
            x = x1 + padding_x + (target_w - line_w) // 2

            draw.text(
                (x, y),
                line,
                fill=(0, 0, 0),
                font=best_font,
                stroke_width=1,
                stroke_fill=(255, 255, 255),
            )

            y += best_line_height

        # PIL RGB -> OpenCV BGR
        return np.array(pil_img)
