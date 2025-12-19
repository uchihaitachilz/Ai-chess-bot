#!/bin/bash
# Install Stockfish binary directly (no sudo required)

set -e

STOCKFISH_DIR="$HOME/stockfish"
STOCKFISH_BIN="$STOCKFISH_DIR/stockfish"

# Create directory if it doesn't exist
mkdir -p "$STOCKFISH_DIR"

# Download Stockfish if not already present
if [ ! -f "$STOCKFISH_BIN" ]; then
    echo "Downloading Stockfish..."
    
    # Detect architecture
    ARCH=$(uname -m)
    
    if [ "$ARCH" = "x86_64" ]; then
        # Linux x86_64 - download Stockfish 16 binary directly
        echo "Downloading Stockfish binary..."
        
        # Try direct binary download first (faster, no extraction needed)
        STOCKFISH_BINARY_URL="https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2"
        
        # Download the binary directly
        if curl -L -f -o "$STOCKFISH_BIN" "$STOCKFISH_BINARY_URL" 2>/dev/null; then
            chmod +x "$STOCKFISH_BIN"
            echo "Downloaded binary directly"
        else
            echo "Direct download failed, trying zip archive..."
            # Fallback to zip download
            STOCKFISH_URL="https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2.zip"
            
            cd "$STOCKFISH_DIR"
            curl -L -f -o stockfish.zip "$STOCKFISH_URL" || {
                echo "Failed to download from GitHub, trying alternative..."
                # Try alternative download method
                wget -q -O stockfish.zip "$STOCKFISH_URL" 2>/dev/null || {
                    echo "All download methods failed"
                    exit 1
                }
            }
            
            # Verify zip file is valid (at least 1MB)
            if [ ! -s stockfish.zip ] || [ $(stat -f%z stockfish.zip 2>/dev/null || stat -c%s stockfish.zip 2>/dev/null || echo 0) -lt 1048576 ]; then
                echo "Downloaded file is too small or invalid, trying Python download..."
                python3 << 'PYTHON_SCRIPT'
import urllib.request
import os
url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2.zip"
filepath = "stockfish.zip"
try:
    urllib.request.urlretrieve(url, filepath)
    if os.path.getsize(filepath) > 1048576:  # > 1MB
        print("Download successful via Python")
    else:
        print("Downloaded file too small")
        exit(1)
except Exception as e:
    print(f"Python download failed: {e}")
    exit(1)
PYTHON_SCRIPT
            fi
            
            # Extract zip
            if command -v unzip &> /dev/null; then
                unzip -q stockfish.zip || exit 1
            else
                python3 -m zipfile -e stockfish.zip . || exit 1
            fi
            
            # Find the stockfish binary in the extracted files
            if [ -f "stockfish_16_linux_x64_avx2" ]; then
                cp stockfish_16_linux_x64_avx2 "$STOCKFISH_BIN"
            else
                find . -name "stockfish*" -type f ! -name "*.zip" ! -name "*.txt" | head -1 | xargs -I {} cp {} "$STOCKFISH_BIN" || {
                    if [ -d "stockfish_16_linux_x64_avx2" ]; then
                        find stockfish_16_linux_x64_avx2 -name "stockfish*" -type f ! -name "*.zip" | head -1 | xargs -I {} cp {} "$STOCKFISH_BIN"
                    fi
                }
            fi
            
            chmod +x "$STOCKFISH_BIN"
            rm -rf stockfish.zip stockfish_16_linux_x64_avx2 2>/dev/null || true
        fi
    else
        echo "Architecture $ARCH detected. Trying system stockfish..."
        if command -v stockfish &> /dev/null; then
            ln -sf "$(which stockfish)" "$STOCKFISH_BIN"
        else
            echo "Error: Could not install Stockfish for architecture $ARCH"
            exit 1
        fi
    fi
fi

echo "Stockfish installed at: $STOCKFISH_BIN"
if [ -f "$STOCKFISH_BIN" ]; then
    "$STOCKFISH_BIN" --version || echo "Binary exists but version check failed"
    echo "SUCCESS: Stockfish is ready at $STOCKFISH_BIN"
else
    echo "ERROR: Stockfish binary not found at $STOCKFISH_BIN"
    exit 1
fi

