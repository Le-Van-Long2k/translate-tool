
python -m pip install paddlepaddle-gpu==3.2.1 \
-i https://www.paddlepaddle.org.cn/packages/stable/cu118/

python3 -m pip install paddlepaddle-gpu==3.3.0 -i https://www.paddlepaddle.org.cn/packages/stable/cu129/

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118



pip install ultralytics onnx onnxruntime

tar -xvf TensorRT-8.6.1.6.Linux.x86_64-gnu.cuda-12.0.tar.gz 
sudo mv TensorRT-8.6.1.6 /usr/local/TensorRT
nano ~/.bashrc

Thêm vào cuối:
export TENSORRT_HOME=/usr/local/TensorRT
export LD_LIBRARY_PATH=$TENSORRT_HOME/lib:$LD_LIBRARY_PATH
export PATH=$TENSORRT_HOME/bin:$PATH
source ~/.bashrc



pip install tensorrt




pip install git+https://github.com/ShivangKakkar/googletrans.git

sudo apt install python3-tk -y


sudo apt install libcublas-12-0
pip install ctranslate2[cuda12] transformers sentencepiece
ct2-transformers-converter --model facebook/nllb-200-distilled-600M \
    --output_dir nllb-200-distilled-600M-ct2 \
    --quantization int8 \
    --force

ct2-transformers-converter \
    --model facebook/nllb-200-distilled-600M \
    --output_dir nllb-600M-ct2-float16 \
    --quantization float16 \
    --force



# 2026-04-12
cd backend
uv sync
uv run bubble_detector/convert_tensorrt/tensortRT.py

bash translator/llama_server/run_server.sh
uv run app.py


# 2026-04-19
export PATH=/usr/local/cuda/bin:$PATH
export LD_LIBRARY_PATH=/usr/local/cuda/lib64:$LD_LIBRARY_PATH
export CUDA_HOME=/usr/local/cuda
CMAKE_ARGS="-DGGML_CUDA=ON -DCMAKE_CUDA_COMPILER=/usr/local/cuda/bin/nvcc" uv pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir


Bước 1: Cài đặt NVIDIA Container Toolkit
# Thêm GPG Key và Repository vào hệ thống
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg \
  && curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

# Cập nhật danh sách gói và cài đặt toolkit
sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker




# Cài đặt Docker Compose V2 (Plugin)
sudo apt-get update
sudo apt-get install ca-certificates curl gnupg
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update
sudo apt-get install docker-compose-plugin

# Build docker
docker compose up --build