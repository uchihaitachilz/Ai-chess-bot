#!/bin/bash
# Render build script to ensure proper installation

# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Set environment variables for Rust (if needed)
export CARGO_HOME=/tmp/cargo
export RUSTUP_HOME=/tmp/rustup
mkdir -p $CARGO_HOME $RUSTUP_HOME 2>/dev/null || true

# Install dependencies - prefer pre-built wheels
pip install --upgrade pip
pip install -r requirements.txt

