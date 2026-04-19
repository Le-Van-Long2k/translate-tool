from PIL import Image, ImageDraw, ImageFont
import numpy as np

from text_renderer.text_renderer import TextRenderer

import logging

logger = logging.getLogger("TEXT_RENDERER")


class PILCenteredTextRenderer(TextRenderer):
    def __init__(
        self, font_path: str = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ):
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
        font_size: int,  # ✅ bắt buộc truyền vào
    ) -> np.ndarray:

        x1, y1, x2, y2 = box
        w, h = x2 - x1, y2 - y1

        if w < 20 or h < 20:
            return image

        pil_img = Image.fromarray(image)
        draw = ImageDraw.Draw(pil_img)

        try:
            font = ImageFont.truetype(self.font_path, font_size)
        except:
            logger.warning("Invalid font path or font size")
            return image

        # ✅ wrap theo pixel (fix lỗi tràn ngang)
        lines = self.wrap_text_pixel(draw, text, font, w - 10)

        if not lines:
            return image

        line_height = int(font_size * 1.4)
        total_h = line_height * len(lines)

        # ✅ căn giữa theo chiều dọc
        y = y1 + (h - total_h) // 2

        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_w = bbox[2] - bbox[0]

            # ✅ căn giữa ngang
            x = x1 + (w - line_w) // 2

            draw.text(
                (x, y),
                line,
                fill=(255, 255, 255),
                font=font,
                stroke_width=2,
                stroke_fill=(0, 0, 0),
            )

            y += line_height

        # logger.debug(f"Text drawn in box {box} with font size {font_size}")

        return np.array(pil_img)
