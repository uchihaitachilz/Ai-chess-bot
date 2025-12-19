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
import tarfile
import os
import stat
import sys
import json

# Get latest release info from GitHub API
print("Fetching latest Stockfish release info...")
urls = []
try:
    api_url = "https://api.github.com/repos/official-stockfish/Stockfish/releases/latest"
    with urllib.request.urlopen(api_url) as response:
        release_data = json.loads(response.read())
    
    print(f"Release: {release_data.get('tag_name', 'unknown')}")
    assets = release_data.get('assets', [])
    print(f"Found {len(assets)} assets")
    
    # Print first few asset names for debugging
    print("Sample asset names:")
    for asset in assets[:5]:
        print(f"  - {asset.get('name', 'unknown')}")
    
    # Find all Linux x64 AVX2 assets (zip or binary) - be more flexible with matching
    for asset in assets:
        name = asset.get('name', '').lower()
        url = asset.get('browser_download_url')
        if not url:
            continue
        
    # Match ubuntu/linux and x64, prefer avx2
    is_linux = 'linux' in name or 'ubuntu' in name
    is_x64 = 'x64' in name or 'x86_64' in name or 'amd64' in name
    is_avx2 = 'avx2' in name
    is_zip = name.endswith('.zip')
    is_tar = name.endswith('.tar') or name.endswith('.tar.gz')
    is_binary = (is_zip or is_tar) and not name.endswith('.md') and not name.endswith('.txt') and not name.endswith('.sha256') and not name.endswith('.sig')
    
    if is_linux and is_x64 and is_binary:
        priority = 2 if is_avx2 else 1  # Prefer AVX2
        asset_info = {
            'url': url,
            'name': asset.get('name', ''),
            'priority': priority,
            'is_zip': is_zip,
            'is_tar': is_tar
        }
        urls.append(asset_info)
    
    # Sort by priority (AVX2 first)
    urls.sort(key=lambda x: x['priority'], reverse=True)
    
    if not urls:
        print("No matching assets found. Listing all assets:")
        for asset in assets:
            print(f"  - {asset.get('name', 'unknown')}")
        print("\nTrying tag-based URLs...")
        tag = release_data.get('tag_name', '').replace('sf_', '')
        # Try common naming patterns
        base_url = f"https://github.com/official-stockfish/Stockfish/releases/download/{release_data.get('tag_name', '')}"
        urls = [
            {'url': f"{base_url}/stockfish-ubuntu-x86-64-avx2.tar", 'name': 'fallback-avx2.tar', 'priority': 2, 'is_zip': False, 'is_tar': True},
            {'url': f"{base_url}/stockfish-ubuntu-x86-64.tar", 'name': 'fallback.tar', 'priority': 1, 'is_zip': False, 'is_tar': True},
        ]
except Exception as e:
    print(f"Could not fetch release info: {e}")
    print("Trying known working URLs...")
    # Fallback to known working URLs
    urls = [
        "https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish_16.1_linux_x64_avx2.zip",
        "https://github.com/official-stockfish/Stockfish/releases/download/sf_16/stockfish_16_linux_x64_avx2.zip",
        "https://github.com/official-stockfish/Stockfish/releases/download/sf_15.1/stockfish_15.1_linux_x64_avx2.zip",
    ]

success = False

for asset_info in urls:
    url = asset_info['url']
    asset_name = asset_info['name']
    is_zip = asset_info.get('is_zip', False)
    is_tar = asset_info.get('is_tar', False)
    
    print(f"\nTrying: {asset_name} ({url})")
    try:
        if is_zip:
            zip_path = "stockfish.zip"
            # Download zip
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
                    if file.startswith("stockfish") and not file.endswith(".zip") and not file.endswith(".txt") and not file.endswith(".md"):
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
        elif is_tar:
            tar_path = "stockfish.tar"
            # Download tar
            def show_progress(block_num, block_size, total_size):
                if total_size > 0 and block_num % 50 == 0:
                    percent = min(100, (block_num * block_size * 100) // total_size)
                    print(f"Progress: {percent}%", end='\r', file=sys.stderr)
            
            urllib.request.urlretrieve(url, tar_path, show_progress)
            print("\nDownload complete")
            
            # Verify file size
            file_size = os.path.getsize(tar_path)
            if file_size < 1048576:
                print(f"File too small ({file_size} bytes), trying next URL...")
                os.remove(tar_path)
                continue
            
            print(f"File size: {file_size / 1024 / 1024:.2f} MB")
            
            # Extract tar
            print("Extracting tar archive...")
            with tarfile.open(tar_path, 'r') as tar_ref:
                tar_ref.extractall(".")
            
            # Find the binary
            binary_found = False
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.startswith("stockfish") and not file.endswith(".tar") and not file.endswith(".txt") and not file.endswith(".md"):
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
                os.remove(tar_path)
                for item in os.listdir("."):
                    if os.path.isdir(item) and item.startswith("stockfish"):
                        import shutil
                        shutil.rmtree(item)
                print("SUCCESS: Stockfish extracted and ready")
                success = True
                break
            else:
                print("Binary not found in archive, trying next URL...")
                os.remove(tar_path)
                for item in os.listdir("."):
                    if os.path.isdir(item):
                        import shutil
                        shutil.rmtree(item)
        else:
            # Direct binary download
            print("Downloading binary directly...")
            urllib.request.urlretrieve(url, "stockfish")
            os.chmod("stockfish", stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
            print("SUCCESS: Binary downloaded directly")
            success = True
            break
            
    except Exception as e:
        print(f"Error with {asset_name}: {e}")
        for cleanup_file in ["stockfish.zip", "stockfish.tar", "stockfish"]:
            if os.path.exists(cleanup_file):
                os.remove(cleanup_file)
        continue

if not success:
    print("ERROR: All download methods failed")
    print("Trying to compile from source as last resort...")
    # Last resort: try to use system package manager if available
    import subprocess
    try:
        result = subprocess.run(['which', 'stockfish'], capture_output=True, text=True)
        if result.returncode == 0:
            stockfish_path = result.stdout.strip()
            print(f"Found system stockfish at: {stockfish_path}")
            os.symlink(stockfish_path, "stockfish")
            success = True
    except:
        pass

if not success:
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

