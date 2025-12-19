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
        name_lower = asset.get('name', '').lower()
        name_original = asset.get('name', '')
        url = asset.get('browser_download_url')
        if not url:
            continue
        
        # Match ubuntu/linux and x64, prefer avx2
        is_linux = 'linux' in name_lower or 'ubuntu' in name_lower
        is_x64 = 'x64' in name_lower or 'x86_64' in name_lower or 'amd64' in name_lower
        is_avx2 = 'avx2' in name_lower
        is_zip = name_lower.endswith('.zip')
        is_tar = name_lower.endswith('.tar') or name_lower.endswith('.tar.gz')
        is_binary = (is_zip or is_tar) and not name_lower.endswith('.md') and not name_lower.endswith('.txt') and not name_lower.endswith('.sha256') and not name_lower.endswith('.sig')
        
        if is_linux and is_x64 and is_binary:
            priority = 3 if is_avx2 else 2 if 'bmi2' in name_lower else 1  # Prefer AVX2, then BMI2
            asset_info = {
                'url': url,
                'name': name_original,
                'priority': priority,
                'is_zip': is_zip,
                'is_tar': is_tar
            }
            urls.append(asset_info)
            print(f"Matched asset: {name_original} (priority: {priority})")
    
    # Sort by priority (AVX2 first)
    if urls:
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
    # Fallback to known working URLs - use latest release format
    urls = [
        {'url': 'https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64-avx2.tar', 'name': 'stockfish-ubuntu-x86-64-avx2.tar', 'priority': 3, 'is_zip': False, 'is_tar': True},
        {'url': 'https://github.com/official-stockfish/Stockfish/releases/download/sf_17.1/stockfish-ubuntu-x86-64.tar', 'name': 'stockfish-ubuntu-x86-64.tar', 'priority': 1, 'is_zip': False, 'is_tar': True},
        {'url': 'https://github.com/official-stockfish/Stockfish/releases/download/sf_16.1/stockfish-ubuntu-x86-64-avx2.tar', 'name': 'stockfish-ubuntu-x86-64-avx2.tar', 'priority': 3, 'is_zip': False, 'is_tar': True},
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
            
            # Find the binary - handle case where stockfish might be a directory
            binary_found = False
            target_binary = "stockfish"
            
            # Remove target if it exists (file or directory)
            if os.path.exists(target_binary):
                if os.path.isdir(target_binary):
                    import shutil
                    shutil.rmtree(target_binary)
                else:
                    os.remove(target_binary)
            
            # List all extracted files for debugging
            print("Searching for binary in extracted files...")
            all_files = []
            for root, dirs, files in os.walk("."):
                # Skip the zip file itself
                if zip_path in files:
                    files.remove(zip_path)
                for file in files:
                    full_path = os.path.join(root, file)
                    if os.path.isfile(full_path):
                        size = os.path.getsize(full_path)
                        all_files.append((full_path, size))
                        if 'stockfish' in file.lower() or size > 1000000:
                            print(f"  Found: {full_path} ({size / 1024 / 1024:.2f} MB)")
            
            # Search for the binary - try multiple patterns
            search_patterns = [
                lambda f, s: f.endswith('stockfish') and s > 1000000,  # Exact name
                lambda f, s: 'stockfish' in os.path.basename(f).lower() and s > 1000000 and not f.endswith('.zip'),
                lambda f, s: s > 5000000 and os.access(f, os.X_OK),  # Large executable
                lambda f, s: s > 1000000 and not f.endswith('.zip') and not f.endswith('.txt') and not f.endswith('.md'),
            ]
            
            for pattern in search_patterns:
                for file_path, file_size in all_files:
                    if pattern(file_path, file_size):
                        # Copy to target location
                        import shutil
                        shutil.copy2(file_path, target_binary)
                        os.chmod(target_binary, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                        print(f"Found binary: {file_path} -> {target_binary}")
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
            
            # Extract tar - try different modes
            print("Extracting tar archive...")
            extracted = False
            for mode in ['r', 'r:*', 'r:gz', 'r:bz2', 'r:xz']:
                try:
                    print(f"Trying mode: {mode}")
                    with tarfile.open(tar_path, mode) as tar_ref:
                        members = tar_ref.getmembers()
                        print(f"Tar file members: {len(members)}")
                        if members:
                            print("First few members:")
                            for member in members[:5]:
                                print(f"  - {member.name} ({member.size} bytes, isfile: {member.isfile()}, type: {member.type})")
                            tar_ref.extractall(".")
                            print("Extraction complete")
                            extracted = True
                            break
                except tarfile.ReadError:
                    print(f"Mode {mode} failed: ReadError")
                    continue
                except Exception as e:
                    print(f"Mode {mode} failed: {e}")
                    continue
            
            if not extracted:
                print("ERROR: Could not extract tar file with any mode")
                raise Exception("Tar extraction failed")
            
            # Find the binary - handle case where stockfish might be a directory
            binary_found = False
            target_binary = "stockfish"
            
            # Remove target if it exists (file or directory)
            if os.path.exists(target_binary):
                if os.path.isdir(target_binary):
                    import shutil
                    shutil.rmtree(target_binary)
                else:
                    os.remove(target_binary)
            
            # List all extracted files for debugging
            print("Searching for binary in extracted files...")
            print(f"Current directory: {os.getcwd()}")
            print(f"Directory contents: {os.listdir('.')}")
            all_files = []
            for root, dirs, files in os.walk("."):
                # Skip the tar file itself
                if tar_path in files:
                    files.remove(tar_path)
                for file in files:
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, ".")
                    if os.path.isfile(full_path):
                        size = os.path.getsize(full_path)
                        all_files.append((full_path, size))
                        print(f"  File: {rel_path} ({size / 1024 / 1024:.2f} MB, executable: {os.access(full_path, os.X_OK)})")
            
            # Also check if there's a stockfish directory with the binary inside
            if os.path.isdir("stockfish"):
                print("Found 'stockfish' directory, checking inside...")
                stockfish_dir = "stockfish"
                for root, dirs, files in os.walk(stockfish_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, ".")
                        if os.path.isfile(full_path):
                            size = os.path.getsize(full_path)
                            all_files.append((full_path, size))
                            print(f"  File: {rel_path} ({size / 1024 / 1024:.2f} MB, executable: {os.access(full_path, os.X_OK)})")
            
            if not all_files:
                print("WARNING: No files found after extraction!")
                print(f"Directory structure: {[os.path.join(root, d) for root, dirs, _ in os.walk('.') for d in dirs]}")
            
            # Search for the binary - try multiple patterns
            search_patterns = [
                lambda f, s: f.endswith('stockfish') and s > 1000000,  # Exact name
                lambda f, s: 'stockfish' in os.path.basename(f).lower() and s > 1000000 and not f.endswith('.tar'),
                lambda f, s: s > 5000000 and os.access(f, os.X_OK),  # Large executable
                lambda f, s: s > 1000000 and not f.endswith('.tar') and not f.endswith('.txt') and not f.endswith('.md'),
            ]
            
            for pattern in search_patterns:
                for file_path, file_size in all_files:
                    if pattern(file_path, file_size):
                        # Copy to target location
                        import shutil
                        shutil.copy2(file_path, target_binary)
                        os.chmod(target_binary, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
                        print(f"Found binary: {file_path} -> {target_binary}")
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

