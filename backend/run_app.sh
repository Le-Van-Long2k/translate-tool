#!/bin/bash

# Set TensorRT library path for PaddleOCR
export LD_LIBRARY_PATH="/usr/local/TensorRT/lib:$LD_LIBRARY_PATH"

# Disable TensorRT completely for Paddle
export PADDLE_INFERENCE_DISABLE_TENSORRT=1
export CUDA_MODULE_LOADING=LAZY

# Run the app with uv
exec uv run python3 app.py