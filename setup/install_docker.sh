#!/bin/bash

set -e

echo "=========================================="
echo " Docker Engine + Docker Compose V2"
echo "=========================================="

# Check root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Run this script with sudo:"
    echo ""
    echo "  sudo bash install_docker.sh"
    echo ""
    exit 1
fi

# ------------------------------------------
# 1. Remove old Docker packages
# ------------------------------------------

echo "[1/6] Removing old Docker packages..."

apt-get remove -y \
    docker.io \
    docker-doc \
    docker-compose \
    docker-compose-v2 \
    podman-docker \
    containerd \
    runc 2>/dev/null || true


# ------------------------------------------
# 2. Install dependencies
# ------------------------------------------

echo "[2/6] Installing dependencies..."

apt-get update

apt-get install -y \
    ca-certificates \
    curl


# ------------------------------------------
# 3. Add Docker official repository
# ------------------------------------------

echo "[3/6] Adding Docker repository..."

install -m 0755 -d /etc/apt/keyrings

curl -fsSL \
    https://download.docker.com/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc

chmod a+r /etc/apt/keyrings/docker.asc

ARCH=$(dpkg --print-architecture)
CODENAME=$(. /etc/os-release && echo "$VERSION_CODENAME")

echo \
"deb [arch=${ARCH} signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu ${CODENAME} stable" \
> /etc/apt/sources.list.d/docker.list

apt-get update


# ------------------------------------------
# 4. Install Docker Engine + Compose V2
# ------------------------------------------

echo "[4/6] Installing Docker Engine..."

apt-get install -y \
    docker-ce \
    docker-ce-cli \
    containerd.io \
    docker-buildx-plugin \
    docker-compose-plugin


# ------------------------------------------
# 5. Add normal user to docker group
# ------------------------------------------

echo "[5/6] Configuring docker group..."

REAL_USER="${SUDO_USER:-}"

if [ -n "$REAL_USER" ]; then
    usermod -aG docker "$REAL_USER"

    echo ""
    echo "User '$REAL_USER' added to docker group."
fi


# ------------------------------------------
# 6. Verify installation
# ------------------------------------------

echo ""
echo "[6/6] Checking installation..."

echo ""
echo "Docker:"
docker --version

echo ""
echo "Docker Compose:"
docker compose version

echo ""
echo "Buildx:"
docker buildx version

echo ""
echo "=========================================="
echo " Installation completed!"
echo "=========================================="

echo ""
echo "Restart WSL from Windows, please run command below:"
echo ""
echo "  sudo reboot"
echo ""