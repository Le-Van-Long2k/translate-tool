#!/bin/sh
#
# UV Installation Script (Ubuntu)

curl -LsSf https://astral.sh/uv/install.sh -o install_uv.sh
chmod +x install_uv.sh

UV_INSTALL_DIR=/usr/local/bin sudo -E sh install_uv.sh
uv --version