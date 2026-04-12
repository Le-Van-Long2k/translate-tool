#!/bin/bash

# Set TensorRT library path BEFORE any Python imports
export LD_LIBRARY_PATH="/usr/local/TensorRT/lib:$LD_LIBRARY_PATH"

# Also set CUDA library path if needed
export LD_LIBRARY_PATH="/usr/local/cuda/lib64:$LD_LIBRARY_PATH"

# Disable problematic TensorRT plugins
export TF_DISABLE_TENSORRT_PLUGINS=1

# Set TensorRT environment variables for compatibility
export TENSORRT_LOG_LEVEL=ERROR
export CUDA_MODULE_LOADING=EAGER

# Try to disable Paddle TensorRT plugins
export PADDLE_TENSORRT_DISABLE_PLUGINS=1

# Disable specific problematic plugin
export TENSORRT_DISABLE_EMB_LAYER_NORM_PLUGIN=1

# Run the app
exec uv run python3 app.py