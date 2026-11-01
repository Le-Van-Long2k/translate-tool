import logging
import time
import re

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from text_renderer.text_renderer import TextRenderer


logger = logging.getLogger("TEXT_RENDERER")


class PILCenteredTextRenderer(TextRenderer):
    def __init__(
        self,
        font_path: str = "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    ):
        self.font_path = font_path

        logger.info(
            f"PILCenteredTextRenderer initialized with font: "
            f"{self.font_path}"
        )

    # ============================================================
    # TEXT WRAPPING
    # ============================================================

    def wrap_text_pixel(
        self,
        draw,
        text: str,
        font,
        max_width: int,
    ):
        """
        Wrap text based on actual pixel width.

        Supports:
        - Vietnamese
        - English
        - Chinese
        - Japanese
        - Korean
        - Mixed CJK + Latin text
        """

        if not text:
            return []

        lines = []

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text.strip())

        if not text:
            return []

        current_line = ""

        def text_width(value: str) -> int:
            if not value:
                return 0

            bbox = draw.textbbox(
                (0, 0),
                value,
                font=font,
            )

            return bbox[2] - bbox[0]

        def flush_line():
            nonlocal current_line

            if current_line:
                lines.append(current_line)
                current_line = ""

        # --------------------------------------------------------
        # Tokenize:
        #
        # CJK characters -> individual characters
        # Latin words   -> words
        # Spaces        -> separators
        # --------------------------------------------------------

        tokens = []

        i = 0

        while i < len(text):
            char = text[i]

            # CJK
            if self._is_cjk(char):
                tokens.append(char)
                i += 1
                continue

            # Whitespace
            if char.isspace():
                tokens.append(" ")
                i += 1
                continue

            # Latin / number / punctuation sequence
            j = i

            while j < len(text):
                next_char = text[j]

                if next_char.isspace() or self._is_cjk(next_char):
                    break

                j += 1

            tokens.append(text[i:j])
            i = j

        # --------------------------------------------------------
        # Build lines
        # --------------------------------------------------------

        for token in tokens:

            # Space
            if token == " ":
                if current_line and not current_line.endswith(" "):
                    current_line += " "
                continue

            test_line = current_line + token

            if text_width(test_line.rstrip()) <= max_width:
                current_line = test_line
                continue

            # Current line is full
            if current_line.strip():
                flush_line()

            # Token itself is too large
            if text_width(token) > max_width:

                # Break character by character
                partial = ""

                for char in token:
                    test_partial = partial + char

                    if text_width(test_partial) <= max_width:
                        partial = test_partial
                    else:
                        if partial:
                            lines.append(partial)

                        partial = char

                current_line = partial

            else:
                current_line = token

        flush_line()

        return lines

    # ============================================================
    # CJK DETECTION
    # ============================================================

    @staticmethod
    def _is_cjk(char: str) -> bool:
        """
        Detect Chinese / Japanese / Korean characters.
        """

        code = ord(char)

        return (
            # CJK Unified Ideographs
            0x4E00 <= code <= 0x9FFF

            # CJK Extension A
            or 0x3400 <= code <= 0x4DBF

            # Hiragana
            or 0x3040 <= code <= 0x309F

            # Katakana
            or 0x30A0 <= code <= 0x30FF

            # Hangul
            or 0xAC00 <= code <= 0xD7AF

            # Hangul Jamo
            or 0x1100 <= code <= 0x11FF

            # Full-width forms
            or 0xFF00 <= code <= 0xFFEF
        )

    # ============================================================
    # CHECK FONT FIT
    # ============================================================

    def _check_font_fit(
        self,
        draw,
        lines,
        font,
        max_width,
        max_height,
    ):
        """
        Check whether all lines fit inside the target box.
        """

        if not lines:
            return False, 0

        ascent, descent = font.getmetrics()

        line_height = ascent + descent

        total_height = line_height * len(lines)

        # Vertical check
        if total_height > max_height:
            return False, line_height

        # Horizontal check
        for line in lines:

            bbox = draw.textbbox(
                (0, 0),
                line,
                font=font,
            )

            line_width = bbox[2] - bbox[0]

            if line_width > max_width:
                return False, line_height

        return True, line_height

    # ============================================================
    # BINARY SEARCH FONT SIZE
    # ============================================================

    def _find_best_font(
        self,
        draw,
        text: str,
        max_width: int,
        max_height: int,
        min_size: int,
        max_size: int,
    ):
        """
        Find the largest font size that fits.

        Uses binary search instead of testing a fixed number
        of font sizes.
        """

        best_font = None
        best_lines = None
        best_line_height = None

        low = min_size
        high = max_size

        while low <= high:

            current_size = (low + high) // 2

            logger.debug(
                f"Binary search font size: {current_size}"
            )

            try:
                font = ImageFont.truetype(
                    self.font_path,
                    current_size,
                )

            except OSError:
                logger.warning(
                    f"Invalid font path or font size: "
                    f"{self.font_path}, {current_size}"
                )

                return None, None, None

            lines = self.wrap_text_pixel(
                draw,
                text,
                font,
                max_width,
            )

            fits, line_height = self._check_font_fit(
                draw,
                lines,
                font,
                max_width,
                max_height,
            )

            if fits:

                # This size fits.
                # Save it and try a larger size.
                best_font = font
                best_lines = lines
                best_line_height = line_height

                low = current_size + 1

            else:

                # Too large.
                high = current_size - 1

        return (
            best_font,
            best_lines,
            best_line_height,
        )

    # ============================================================
    # DRAW TEXT
    # ============================================================

    def draw_text_in_box(
        self,
        image: np.ndarray,
        text: str,
        box: tuple[int, int, int, int],
        font_size: int,
    ) -> np.ndarray:

        start_time = time.perf_counter()
        if not text or not text.strip():
            return image

        x1, y1, x2, y2 = box

        w = x2 - x1
        h = y2 - y1

        # Ignore extremely small boxes
        if w < 20 or h < 20:
            return image

        # ========================================================
        # SAFE AREA
        # ========================================================

        scale_hw = 1.0

        target_w = int(w * scale_hw)
        target_h = int(h * scale_hw)

        padding_x = (w - target_w) // 2
        padding_y = (h - target_h) // 2

        # ========================================================
        # PIL IMAGE
        # ========================================================

        pil_img = Image.fromarray(image)

        draw = ImageDraw.Draw(pil_img)

        # ========================================================
        # FONT RANGE
        # ========================================================

        min_font_size = 6

        max_font_size = max(
            min_font_size,
            int(font_size*1.5),
        )

        # ========================================================
        # BINARY SEARCH
        # ========================================================

        (
            best_font,
            best_lines,
            best_line_height,
        ) = self._find_best_font(
            draw=draw,
            text=text,
            max_width=target_w,
            max_height=target_h,
            min_size=min_font_size,
            max_size=max_font_size,
        )

        # ========================================================
        # FALLBACK
        # ========================================================

        if best_font is None or not best_lines:

            logger.debug(
                f"No font size fits box {box}. "
                f"Using minimum font size: {min_font_size}"
            )

            try:
                best_font = ImageFont.truetype(
                    self.font_path,
                    min_font_size,
                )

            except OSError:
                logger.warning(
                    f"Cannot load font: {self.font_path}"
                )

                return image

            best_lines = self.wrap_text_pixel(
                draw,
                text,
                best_font,
                target_w,
            )

            if not best_lines:
                return image

            ascent, descent = best_font.getmetrics()

            best_line_height = (
                ascent + descent
            )

        # ========================================================
        # TOTAL TEXT HEIGHT
        # ========================================================

        total_h = (
            best_line_height
            * len(best_lines)
        )

        # ========================================================
        # VERTICAL CENTER
        # ========================================================

        y = (
            y1
            + padding_y
            + (target_h - total_h) // 2
        )

        # ========================================================
        # DRAW EACH LINE
        # ========================================================

        for line in best_lines:

            bbox = draw.textbbox(
                (0, 0),
                line,
                font=best_font,
            )

            line_w = bbox[2] - bbox[0]

            # Horizontal center
            x = (
                x1
                + padding_x
                + (target_w - line_w) // 2
            )

            draw.text(
                (x, y),
                line,
                fill=(20, 20, 20),
                font=best_font,
                stroke_width=max(1, best_font.size // 12),
                stroke_fill=(255, 255, 255),
            )

            y += best_line_height

        # ========================================================
        # RETURN
        # ========================================================
        enslapsed = time.perf_counter() - start_time
        logger.info(f"[PILCenteredTextRenderer] Drawn text in {enslapsed:.3f}s")

        return np.array(pil_img)