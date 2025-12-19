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
    OS=$(uname -s | tr '[:upper:]' '[:lower:]')
    
    if [ "$ARCH" = "x86_64" ]; then
        # Linux x86_64
        STOCKFISH_URL="https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2.zip"
        curl -L -o "$STOCKFISH_DIR/stockfish.zip" "$STOCKFISH_URL"
        unzip -q "$STOCKFISH_DIR/stockfish.zip" -d "$STOCKFISH_DIR"
        mv "$STOCKFISH_DIR/stockfish_16_linux_x64_avx2/stockfish_16_linux_x64_avx2" "$STOCKFISH_BIN" 2>/dev/null || \
        mv "$STOCKFISH_DIR/stockfish_16_linux_x64_avx2" "$STOCKFISH_BIN" 2>/dev/null || \
        find "$STOCKFISH_DIR" -name "stockfish*" -type f -executable | head -1 | xargs -I {} mv {} "$STOCKFISH_BIN"
        rm -rf "$STOCKFISH_DIR/stockfish.zip" "$STOCKFISH_DIR/stockfish_16_linux_x64_avx2" 2>/dev/null || true
    else
        # Try to use system stockfish or download generic binary
        echo "Architecture $ARCH not directly supported, trying alternative..."
        if command -v stockfish &> /dev/null; then
            ln -sf "$(which stockfish)" "$STOCKFISH_BIN"
        else
            echo "Error: Could not install Stockfish for architecture $ARCH"
            exit 1
        fi
    fi
    
    chmod +x "$STOCKFISH_BIN"
fi

echo "Stockfish installed at: $STOCKFISH_BIN"
"$STOCKFISH_BIN" --version || echo "Version check failed, but binary exists"

# Export path for use in Python
echo "$STOCKFISH_DIR" >> "$GITHUB_ENV" 2>/dev/null || true
export PATH="$STOCKFISH_DIR:$PATH"

