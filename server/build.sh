#!/bin/bash
# Render build script to ensure proper installation

# Install Stockfish
echo "Installing Stockfish..."
sudo apt-get update -qq
sudo apt-get install -y stockfish -qq

# Find Stockfish path
STOCKFISH_PATH=$(which stockfish || echo "/usr/bin/stockfish")
echo "Stockfish found at: $STOCKFISH_PATH"

# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Install Python dependencies
pip install -r requirements.txt

