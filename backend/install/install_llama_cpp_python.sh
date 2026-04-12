sudo apt install gcc-10 g++-10

export CC=gcc-10
export CXX=g++-10
export CUDAHOSTCXX=g++-10

CMAKE_ARGS="-DGGML_CUDA=on" uv pip install llama-cpp-python --force-reinstall --no-cache-dir