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
        # Linux x86_64 - download Stockfish using Python (more reliable)
        echo "Downloading Stockfish using Python..."
        
        cd "$STOCKFISH_DIR"
        python3 << 'PYTHON_SCRIPT'
import urllib.request
import zipfile
import os
import stat

# Download Stockfish 16
url = "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2.zip"
zip_path = "stockfish.zip"

print(f"Downloading from {url}...")
try:
    # Download with progress
    def show_progress(block_num, block_size, total_size):
        if total_size > 0:
            percent = min(100, (block_num * block_size * 100) // total_size)
            if block_num % 10 == 0:  # Print every 10 blocks
                print(f"Progress: {percent}%", end='\r')
    
    urllib.request.urlretrieve(url, zip_path, show_progress)
    print("\nDownload complete")
    
    # Verify file size (should be > 1MB)
    file_size = os.path.getsize(zip_path)
    if file_size < 1048576:
        print(f"ERROR: Downloaded file too small ({file_size} bytes)")
        exit(1)
    
    print(f"File size: {file_size / 1024 / 1024:.2f} MB")
    
    # Extract zip
    print("Extracting...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(".")
    
    # Find the binary
    binary_found = False
    for root, dirs, files in os.walk("."):
        for file in files:
            if file.startswith("stockfish") and not file.endswith(".zip") and not file.endswith(".txt"):
                src = os.path.join(root, file)
                # Check if it's executable or a binary
                if os.path.isfile(src):
                    dst = "stockfish"
                    os.rename(src, dst)
                    # Make executable
                    os.chmod(dst, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                    print(f"Found binary: {src} -> {dst}")
                    binary_found = True
                    break
        if binary_found:
            break
    
    if not binary_found:
        print("ERROR: Could not find stockfish binary in archive")
        exit(1)
    
    # Cleanup
    os.remove(zip_path)
    # Remove extracted directory if exists
    for item in os.listdir("."):
        if os.path.isdir(item) and item.startswith("stockfish"):
            import shutil
            shutil.rmtree(item)
    
    print("SUCCESS: Stockfish extracted and ready")
    
except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
    exit(1)
PYTHON_SCRIPT
        
        if [ -f "$STOCKFISH_BIN" ]; then
            echo "Stockfish binary ready"
        else
            echo "ERROR: Binary extraction failed"
            exit 1
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

