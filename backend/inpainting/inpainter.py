from abc import ABC, abstractmethod
from typing import Any, Dict, List
import numpy as np


class Inpainter(ABC):
    @abstractmethod
    def inpaint_from_boxes(
        self, image: np.ndarray, crop_boxes: List[np.ndarray], boxes: List[Dict[str, Any]]
    ) -> np.ndarray:
        pass
