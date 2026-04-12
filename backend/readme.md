ollama run MedAIBase/Tencent-HY-MT1.5:1.8b



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