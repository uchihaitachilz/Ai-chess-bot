#!/bin/bash
# Render build script to ensure proper installation

# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Install Rust if needed (for pydantic-core)
# This is a workaround for Render's read-only filesystem issue
export CARGO_HOME=/tmp/cargo
export RUSTUP_HOME=/tmp/rustup
mkdir -p $CARGO_HOME $RUSTUP_HOME

# Install dependencies with pre-built wheels preferred
pip install --only-binary :all: -r requirements.txt || pip install -r requirements.txt

