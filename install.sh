#!/bin/bash

set -e

echo "=========================================="
echo "  Ada Shellcode Loader - Installer"
echo "=========================================="
echo ""

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    echo "[*] Detected: Linux"
    
    # Detect distribution
    if [ -f /etc/debian_version ]; then
        echo "[*] Distribution: Debian/Ubuntu"
        
        echo "[*] Updating package lists..."
        sudo apt update
        
        echo "[*] Installing GNAT Ada compiler..."
        sudo apt install -y gnat
        
        echo "[*] Installing MinGW-w64 cross-compiler..."
        sudo apt install -y gnat-mingw-w64
        
        echo "[*] Installing Python3 (if not present)..."
        sudo apt install -y python3
        
    elif [ -f /etc/redhat-release ]; then
        echo "[*] Distribution: RedHat/CentOS/Fedora"
        
        echo "[*] Installing EPEL repository..."
        sudo yum install -y epel-release || sudo dnf install -y epel-release
        
        echo "[*] Installing GNAT Ada compiler..."
        sudo yum install -y gcc-gnat || sudo dnf install -y gcc-gnat
        
        echo "[*] Installing MinGW-w64..."
        sudo yum install -y mingw64-gcc mingw64-gcc-gnat || sudo dnf install -y mingw64-gcc mingw64-gcc-gnat
        
        echo "[*] Installing Python3..."
        sudo yum install -y python3 || sudo dnf install -y python3
        
    elif [ -f /etc/arch-release ]; then
        echo "[*] Distribution: Arch Linux"
        
        echo "[*] Installing GNAT Ada compiler..."
        sudo pacman -S --noconfirm gcc-ada
        
        echo "[*] Installing MinGW-w64..."
        sudo pacman -S --noconfirm mingw-w64-gcc
        
        echo "[*] Installing Python3..."
        sudo pacman -S --noconfirm python
        
    else
        echo "[!] Unsupported Linux distribution"
        echo "[!] Please install manually:"
        echo "    - GNAT Ada compiler (gnat)"
        echo "    - MinGW-w64 cross-compiler (gnat-mingw-w64)"
        echo "    - Python 3"
        exit 1
    fi
    
elif [[ "$OSTYPE" == "darwin"* ]]; then
    echo "[*] Detected: macOS"
    
    if ! command -v brew &> /dev/null; then
        echo "[!] Homebrew not found. Installing..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    echo "[*] Installing GNAT Ada compiler..."
    brew install gcc
    
    echo "[*] Installing MinGW-w64..."
    brew install mingw-w64
    
    echo "[*] Python3 should be pre-installed on macOS"
    
else
    echo "[!] Unsupported operating system: $OSTYPE"
    echo "[!] This installer supports Linux and macOS only"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Verifying Installation"
echo "=========================================="
echo ""

# Verify installations
echo -n "[*] Checking gnatmake... "
if command -v gnatmake &> /dev/null; then
    echo "OK ($(gnatmake --version | head -1))"
else
    echo "FAILED"
    exit 1
fi

echo -n "[*] Checking x86_64-w64-mingw32-gnatmake... "
if command -v x86_64-w64-mingw32-gnatmake &> /dev/null; then
    echo "OK"
else
    echo "FAILED"
    exit 1
fi

echo -n "[*] Checking python3... "
if command -v python3 &> /dev/null; then
    echo "OK ($(python3 --version))"
else
    echo "FAILED"
    exit 1
fi

echo ""
echo "=========================================="
echo "  Installation Complete!"
echo "=========================================="
echo ""
echo "You can now build the loader:"
echo "  python3 build.py shellcode.bin"
echo ""
