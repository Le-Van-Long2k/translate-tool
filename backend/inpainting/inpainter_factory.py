from enum import Enum
from typing import Union

from inpainting.inpainter import Inpainter
from inpainting.lama_inpaintor import LamaInpaintor
from inpainting.opencv_inpaintor import OpencvInpaintor


class InpainterType(Enum):
    LAMA = "lama"
    OPENCV = "opencv"


MODEL_REGISTRY = {
    InpainterType.LAMA: LamaInpaintor,
    InpainterType.OPENCV: OpencvInpaintor,
}


class InpainterFactory:
    @staticmethod
    def create(model_type: Union[str, InpainterType]) -> Inpainter:
        if isinstance(model_type, str):
            model_type = InpainterType(model_type)

        if model_type not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model type: {model_type}")

        return MODEL_REGISTRY[model_type]()
