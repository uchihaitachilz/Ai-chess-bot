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
import sys
import json

# Get latest release info from GitHub API
print("Fetching latest Stockfish release info...")
try:
    api_url = "https://api.github.com/repos/official-stockfish/Stockfish/releases/latest"
    with urllib.request.urlopen(api_url) as response:
        release_data = json.loads(response.read())
    
    # Find Linux x64 AVX2 asset
    zip_url = None
    for asset in release_data.get('assets', []):
        name = asset.get('name', '')
        if 'linux' in name.lower() and 'x64' in name.lower() and 'avx2' in name.lower() and name.endswith('.zip'):
            zip_url = asset.get('browser_download_url')
            print(f"Found release asset: {name}")
            break
    
    if not zip_url:
        # Fallback: try to construct URL from tag
        tag = release_data.get('tag_name', '')
        print(f"Release tag: {tag}, trying constructed URLs...")
        urls = [
            f"https://github.com/official-stockfish/Stockfish/releases/download/{tag}/stockfish_{tag}_linux_x64_avx2.zip",
            f"https://github.com/official-stockfish/Stockfish/releases/download/{tag}/stockfish-{tag}-linux-x64-avx2.zip",
        ]
    else:
        urls = [zip_url]
except Exception as e:
    print(f"Could not fetch release info: {e}")
    print("Trying known working URLs...")
    # Fallback to known working URLs
    urls = [
        "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish_16.1_linux_x64_avx2.zip",
        "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2.zip",
        "https://github.com/official-stockfish/Stockfish/releases/download/sf_15.1/stockfish_15.1_linux_x64_avx2.zip",
    ]

zip_path = "stockfish.zip"
success = False

for url in urls:
    print(f"Trying: {url}")
    try:
        # Download
        def show_progress(block_num, block_size, total_size):
            if total_size > 0 and block_num % 50 == 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                print(f"Progress: {percent}%", end='\r', file=sys.stderr)
        
        urllib.request.urlretrieve(url, zip_path, show_progress)
        print("\nDownload complete")
        
        # Verify file size (should be > 1MB)
        file_size = os.path.getsize(zip_path)
        if file_size < 1048576:
            print(f"File too small ({file_size} bytes), trying next URL...")
            os.remove(zip_path)
            continue
        
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
                    if os.path.isfile(src) and os.path.getsize(src) > 1000000:  # > 1MB
                        dst = "stockfish"
                        if os.path.exists(dst):
                            os.remove(dst)
                        os.rename(src, dst)
                        os.chmod(dst, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                        print(f"Found binary: {src} -> {dst}")
                        binary_found = True
                        break
            if binary_found:
                break
        
        if binary_found:
            # Cleanup
            os.remove(zip_path)
            for item in os.listdir("."):
                if os.path.isdir(item) and item.startswith("stockfish"):
                    import shutil
                    shutil.rmtree(item)
            print("SUCCESS: Stockfish extracted and ready")
            success = True
            break
        else:
            print("Binary not found in archive, trying next URL...")
            os.remove(zip_path)
            for item in os.listdir("."):
                if os.path.isdir(item):
                    import shutil
                    shutil.rmtree(item)
    except Exception as e:
        print(f"Error with {url}: {e}")
        if os.path.exists(zip_path):
            os.remove(zip_path)
        continue

if not success:
    print("ERROR: All download URLs failed")
    sys.exit(1)
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

