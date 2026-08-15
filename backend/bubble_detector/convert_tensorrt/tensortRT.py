import glob
import logging
import os
from pathlib import Path

import tensorrt as trt
from huggingface_hub import hf_hub_download
from ultralytics import YOLO


logger = logging.getLogger("BUBBLE_DETECTOR")


# Hugging Face model
HF_REPO_ID = "ogkalu/comic-speech-bubble-detector-yolov8m"
HF_FILENAME = "comic-speech-bubble-detector.pt"

# Model input
DEFAULT_INPUT_SIZE = 640

# TensorRT workspace size: 1 GiB
WORKSPACE_SIZE = 1 << 30


def _get_model_paths():
    """
    Download YOLO model and determine ONNX / TensorRT engine paths.
    """

    model_path = Path(
        hf_hub_download(
            repo_id=HF_REPO_ID,
            filename=HF_FILENAME,
        )
    )

    cache_dir = model_path.parent

    onnx_path = cache_dir / "comic-speech-bubble-detector.onnx"

    # Save engine next to this Python module's parent directory.
    #
    # /app/bubble_detector/convert_tensorrt/tensortRT.py
    #                       ↑
    # parent.parent = /app/bubble_detector
    base_dir = Path(__file__).resolve().parent
    engine_path = base_dir.parent / "comic.engine"

    return model_path, onnx_path, engine_path


def _export_onnx(model_path: Path, onnx_path: Path):
    """
    Export YOLO .pt model to ONNX.

    Important:
    - Do NOT use half=True here.
    - TensorRT will handle FP16 optimization later.
    """

    logger.info("Loading YOLO model from: %s", model_path)

    model = YOLO(str(model_path))

    logger.info("Exporting YOLO model to ONNX...")

    exported_path = model.export(
        format="onnx",
        imgsz=DEFAULT_INPUT_SIZE,
        device=0,
        simplify=False,
        dynamic=True,
        half=False,
    )

    exported_path = Path(exported_path)

    if exported_path.exists():
        # Ultralytics normally returns the actual exported ONNX path.
        if exported_path != onnx_path:
            logger.info(
                "Ultralytics exported ONNX to: %s",
                exported_path,
            )

            # Use the actual exported path.
            onnx_path = exported_path

    if not onnx_path.exists():
        matches = list(onnx_path.parent.glob("*.onnx"))

        if matches:
            # Prefer the expected filename.
            expected = [
                path
                for path in matches
                if path.name == "comic-speech-bubble-detector.onnx"
            ]

            if expected:
                onnx_path = expected[0]
            else:
                onnx_path = matches[0]

        else:
            raise FileNotFoundError(
                f"ONNX export file not found.\n"
                f"Expected: {onnx_path}\n"
                f"Directory: {onnx_path.parent}"
            )

    logger.info(
        "✅ ONNX export completed: %s",
        onnx_path,
    )

    return onnx_path


def _get_input_info(network):
    """
    Get the first input tensor from TensorRT network.
    """

    if network.num_inputs < 1:
        raise RuntimeError(
            "TensorRT network has no input tensors."
        )

    input_tensor = network.get_input(0)

    input_name = input_tensor.name
    input_shape = tuple(input_tensor.shape)

    logger.info(
        "TensorRT input detected: name=%s shape=%s",
        input_name,
        input_shape,
    )

    return input_name, input_shape


def _configure_fp16(config, builder):
    """
    Enable FP16 if supported.

    TensorRT Python bindings can differ between versions.
    Some versions expose BuilderFlag.FP16 normally, while
    others may expose the enum differently.

    This function safely handles both cases.
    """

    # Check whether TensorRT builder supports FP16.
    try:
        fp16_supported = builder.platform_has_fast_fp16
    except AttributeError:
        # If the property is unavailable, assume FP16 may be supported
        # and try to find the flag.
        fp16_supported = True

    if not fp16_supported:
        logger.warning(
            "⚠️ TensorRT platform does not report fast FP16 support. "
            "Building FP32 engine."
        )
        return False

    # Try the normal TensorRT API first.
    fp16_flag = getattr(trt.BuilderFlag, "FP16", None)

    if fp16_flag is not None:
        config.set_flag(fp16_flag)

        logger.info(
            "✅ TensorRT FP16 mode enabled."
        )

        return True

    logger.warning(
        "⚠️ trt.BuilderFlag.FP16 is not available in this "
        "TensorRT Python binding. Building FP32 engine instead."
    )

    return False


def _create_optimization_profile(
    builder,
    config,
    input_name,
):
    """
    Create optimization profile for dynamic input.

    min:  320x320
    opt:  640x640
    max: 1280x1280
    """

    profile = builder.create_optimization_profile()

    profile.set_shape(
        input_name,
        (1, 3, 320, 320),
        (1, 3, 640, 640),
        (1, 3, 1280, 1280),
    )

    config.add_optimization_profile(profile)

    logger.info(
        "✅ Optimization profile configured for input '%s'",
        input_name,
    )

    logger.info(
        "   MIN: (1, 3, 320, 320)"
    )

    logger.info(
        "   OPT: (1, 3, 640, 640)"
    )

    logger.info(
        "   MAX: (1, 3, 1280, 1280)"
    )


def _parse_onnx(network, parser, onnx_path: Path):
    """
    Parse ONNX file into TensorRT network.
    """

    logger.info(
        "Parsing ONNX with TensorRT: %s",
        onnx_path,
    )

    with open(onnx_path, "rb") as f:
        onnx_data = f.read()

    if parser.parse(onnx_data):
        logger.info(
            "✅ ONNX parsed successfully by TensorRT."
        )
        return

    errors = []

    for i in range(parser.num_errors):
        error = parser.get_error(i)

        try:
            error_text = error.desc()
        except Exception:
            error_text = str(error)

        errors.append(
            f"[{i}] {error_text}"
        )

    error_message = "\n".join(errors)

    raise RuntimeError(
        "❌ Failed to parse ONNX model with TensorRT.\n"
        f"ONNX: {onnx_path}\n"
        f"TensorRT errors:\n{error_message}"
    )


def _build_engine(
    onnx_path: Path,
    engine_path: Path,
):
    """
    Build TensorRT serialized engine from ONNX.
    """

    logger.info(
        "🚀 Starting TensorRT engine build..."
    )

    TRT_LOGGER = trt.Logger(trt.Logger.INFO)

    builder = trt.Builder(TRT_LOGGER)

    if builder is None:
        raise RuntimeError(
            "Failed to create TensorRT Builder."
        )

    # TensorRT modern API:
    # No EXPLICIT_BATCH flag is required.
    network = builder.create_network()

    if network is None:
        raise RuntimeError(
            "Failed to create TensorRT Network."
        )

    parser = trt.OnnxParser(
        network,
        TRT_LOGGER,
    )

    if parser is None:
        raise RuntimeError(
            "Failed to create TensorRT ONNX Parser."
        )

    _parse_onnx(
        network,
        parser,
        onnx_path,
    )

    input_name, input_shape = _get_input_info(
        network
    )

    config = builder.create_builder_config()

    if config is None:
        raise RuntimeError(
            "Failed to create TensorRT BuilderConfig."
        )

    # TensorRT modern API.
    config.set_memory_pool_limit(
        trt.MemoryPoolType.WORKSPACE,
        WORKSPACE_SIZE,
    )

    logger.info(
        "TensorRT workspace limit: %d MiB",
        WORKSPACE_SIZE // (1024 * 1024),
    )

    # Enable FP16 if available.
    fp16_enabled = _configure_fp16(
        config,
        builder,
    )

    # Dynamic ONNX model requires optimization profile.
    _create_optimization_profile(
        builder,
        config,
        input_name,
    )

    logger.info(
        "Building TensorRT serialized engine..."
    )

    logger.info(
        "Input: %s",
        input_name,
    )

    logger.info(
        "FP16: %s",
        fp16_enabled,
    )

    serialized_engine = builder.build_serialized_network(
        network,
        config,
    )

    if serialized_engine is None:
        raise RuntimeError(
            "❌ TensorRT failed to build serialized engine."
        )

    # Ensure parent directory exists.
    engine_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with open(engine_path, "wb") as f:
        f.write(
            bytes(serialized_engine)
        )

    logger.info(
        "✅ TensorRT engine successfully saved:"
    )

    logger.info(
        "   %s",
        engine_path,
    )

    return engine_path


def build_tensorrt_comic_engine(
    force_rebuild=False,
):
    """
    Build TensorRT engine for comic speech bubble detection.

    Returns:
        Path: Path to generated TensorRT engine.
    """

    model_path, onnx_path, engine_path = (
        _get_model_paths()
    )

    logger.info(
        "Model path: %s",
        model_path,
    )

    logger.info(
        "ONNX path: %s",
        onnx_path,
    )

    logger.info(
        "TensorRT engine path: %s",
        engine_path,
    )

    # Reuse existing engine unless explicitly requested
    # to rebuild.
    if engine_path.exists() and not force_rebuild:
        logger.info(
            "✅ TensorRT engine already exists."
        )

        logger.info(
            "Skipping TensorRT build: %s",
            engine_path,
        )

        return engine_path

    # Export ONNX if it does not exist.
    if not onnx_path.exists():
        onnx_path = _export_onnx(
            model_path,
            onnx_path,
        )
    else:
        logger.info(
            "✅ ONNX file already exists."
        )

        logger.info(
            "Skipping ONNX export: %s",
            onnx_path,
        )

    # Build TensorRT engine.
    return _build_engine(
        onnx_path,
        engine_path,
    )


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s "
            "%(levelname)s "
            "%(name)s: "
            "%(message)s"
        ),
    )

    build_tensorrt_comic_engine()