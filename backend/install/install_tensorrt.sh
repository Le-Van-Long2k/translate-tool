tar -xvf TensorRT-8.6.1.6.Linux.x86_64-gnu.cuda-11.8.tar.gz
cd TensorRT-8.6.1.6
ls lib | grep nvinfer
export LD_LIBRARY_PATH=$PWD/lib:$LD_LIBRARY_PATH

uv run python - <<'PY'
import paddle.inference as paddle_infer
print(paddle_infer.get_trt_runtime_version())
PY