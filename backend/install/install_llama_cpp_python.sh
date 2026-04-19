#!/bin/bash
export CC=gcc
export CXX=g++
export CUDAHOSTCXX=g++

CMAKE_ARGS="-DGGML_CUDA=on" uv pip install llama-cpp-python --force-reinstall --no-cache-dir