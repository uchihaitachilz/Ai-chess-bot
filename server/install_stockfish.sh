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
        # Linux x86_64 - download Stockfish 16
        STOCKFISH_URL="https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2.zip"
        curl -L -o "$STOCKFISH_DIR/stockfish.zip" "$STOCKFISH_URL" || {
            echo "Failed to download, trying alternative URL..."
            STOCKFISH_URL="https://stockfishchess.org/files/stockfish_16_linux_x64_avx2.zip"
            curl -L -o "$STOCKFISH_DIR/stockfish.zip" "$STOCKFISH_URL" || exit 1
        }
        
        cd "$STOCKFISH_DIR"
        unzip -q stockfish.zip || exit 1
        
        # Find the stockfish binary in the extracted files
        find . -name "stockfish*" -type f -executable ! -name "*.zip" | head -1 | xargs -I {} cp {} "$STOCKFISH_BIN" || {
            # Try alternative extraction
            if [ -d "stockfish_16_linux_x64_avx2" ]; then
                cp stockfish_16_linux_x64_avx2/stockfish_16_linux_x64_avx2 "$STOCKFISH_BIN" 2>/dev/null || \
                find stockfish_16_linux_x64_avx2 -name "stockfish*" -type f -executable | head -1 | xargs -I {} cp {} "$STOCKFISH_BIN"
            fi
        }
        
        chmod +x "$STOCKFISH_BIN"
        rm -rf stockfish.zip stockfish_16_linux_x64_avx2 2>/dev/null || true
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

