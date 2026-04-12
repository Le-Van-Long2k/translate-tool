#!/bin/bash
echo "========================================="
echo "   Ollama Installation Script (Ubuntu)   "
echo "========================================="

# Step 1: Install Ollama
echo "[1/3] Downloading and installing Ollama..."
curl -fsSL https://ollama.com/install.sh | sh

# Check if installation succeeded
if [ $? -ne 0 ]; then
    echo "❌ Installation failed. Please check your internet or permissions."
    exit 1
fi

echo "✅ Ollama installed successfully."

# Step 2: Verify installation
echo "[2/3] Checking Ollama version..."
ollama --version

if [ $? -ne 0 ]; then
    echo "❌ Ollama is not working properly."
    exit 1
fi

echo "✅ Ollama is working."