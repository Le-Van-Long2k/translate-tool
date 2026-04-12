from abc import ABC, abstractmethod
from typing import Any, Dict, List
import numpy as np


# Interface for bubble detector
class BubbleDetector(ABC):
    @abstractmethod
    def detect(self, image: np.ndarray, conf: float = 0.25) -> List[Dict[str, Any]]:
        pass
