#!/bin/bash
set -e
echo "[*] Installing dependencies..."

if [ -f /etc/debian_version ]; then
    sudo apt update
    sudo apt install -y gnat gnat-mingw-w64 python3
elif [ -f /etc/redhat-release ]; then
    sudo dnf install -y gcc-gnat mingw64-gcc mingw64-gcc-gnat python3 2>/dev/null || \
    sudo yum install -y gcc-gnat mingw64-gcc mingw64-gcc-gnat python3
elif [ -f /etc/arch-release ]; then
    sudo pacman -S --noconfirm gcc-ada mingw-w64-gcc python
else
    echo "[!] Unsupported distro. Install gnat-mingw-w64 and python3 manually."
    exit 1
fi

echo ""
echo -n "[*] gnatmake: "
command -v x86_64-w64-mingw32-gnatmake && echo "OK" || echo "MISSING"
echo -n "[*] gcc: "
command -v x86_64-w64-mingw32-gcc && echo "OK" || echo "MISSING"
echo -n "[*] python3: "
command -v python3 && echo "OK" || echo "MISSING"
echo ""
echo "[+] Done. Usage: python3 build.py <input.bin>"
