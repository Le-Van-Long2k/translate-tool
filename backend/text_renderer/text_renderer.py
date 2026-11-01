from abc import ABC, abstractmethod
import numpy as np

class TextRenderer(ABC):
    @abstractmethod
    def draw_text_in_box(
        self,
        image: np.ndarray,
        text: str,
        box: tuple[int, int, int, int]
    ) -> np.ndarray:
        """Vẽ text vào giữa box, trả về ảnh đã vẽ"""
        pass