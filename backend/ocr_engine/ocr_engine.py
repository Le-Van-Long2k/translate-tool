from abc import ABC, abstractmethod
from typing import List, Union
import numpy as np


class OCREngine(ABC):
    @abstractmethod
    def ocr(self, images: Union[np.ndarray, List[np.ndarray]]):
        pass
