import glob
import os
import tensorrt as trt
from ultralytics import YOLO
from huggingface_hub import hf_hub_download
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def build_tensorrt_comic_engine():
    # Load model
    model_path = hf_hub_download(
        repo_id="ogkalu/comic-speech-bubble-detector-yolov8m",
        filename="comic-speech-bubble-detector.pt",
    )

    model = YOLO(model_path)

    # export ONNX
    model.export(
        format="onnx",
        imgsz=640,
        half=True,
        device=0,
        simplify=False,
        dynamic=True,
    )

    cache_dir = os.path.dirname(model_path)
    onnx_path = os.path.join(cache_dir, "comic-speech-bubble-detector.onnx")
    if not os.path.exists(onnx_path):
        matches = glob.glob(os.path.join(cache_dir, "*.onnx"))
        if matches:
            onnx_path = matches[0]
        else:
            raise FileNotFoundError(f"ONNX export file not found in {cache_dir}")

    logger.info(f"✅ Export ONNX done! File saved to: {onnx_path}")

    # Build TensorRT engine from ONNX using Python TensorRT runtime
    TRT_LOGGER = trt.Logger(trt.Logger.INFO)
    builder = trt.Builder(TRT_LOGGER)
    network = builder.create_network(
        1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
    )
    parser = trt.OnnxParser(network, TRT_LOGGER)

    with open(onnx_path, "rb") as f:
        if not parser.parse(f.read()):
            errors = []
            for i in range(parser.num_errors):
                err = parser.get_error(i)
                errors.append(f"{err.desc()} (line {err.line})")
            raise RuntimeError("Failed to parse ONNX model:\n" + "\n".join(errors))

    config = builder.create_builder_config()
    config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, 1 << 30)  # 1 GiB
    config.set_flag(trt.BuilderFlag.FP16)

    profile = builder.create_optimization_profile()
    profile.set_shape("images", (1, 3, 320, 320), (1, 3, 640, 640), (1, 3, 1280, 1280))
    config.add_optimization_profile(profile)

    logger.info("🚀 Building TensorRT engine with Python API...")
    serialized_engine = builder.build_serialized_network(network, config)
    if serialized_engine is None:
        raise RuntimeError("Failed to build TensorRT engine")

    base_dir = Path(__file__).resolve().parent
    parent_dir = base_dir.parent
    engine_path = parent_dir / "comic.engine"
    with open(engine_path, "wb") as f:
        f.write(bytes(serialized_engine))

    logger.info(f"✅ TensorRT engine saved to: {engine_path}")
