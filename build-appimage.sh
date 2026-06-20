#!/bin/bash
set -e
# Build reverseaffinite AppImage
# Usage: ./build-appimage.sh

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$REPO_DIR"

echo "[1/5] Installing build dependencies..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-pyqt5 python3-numpy libgl1 libfuse2 desktop-file-utils
sudo pip3 install pyinstaller Pillow psd-tools --break-system-packages -qq

echo "[2/5] Running PyInstaller..."
rm -rf build dist *.spec
pyinstaller \
    --name reverseaffinite \
    --onefile --windowed \
    --add-data "$(python3 -c 'import PyQt5; print(PyQt5.__path__[0])'):PyQt5" \
    --add-data "$(python3 -c 'import numpy; print(numpy.__path__[0])'):numpy" \
    --add-data "$(python3 -c 'import PIL; print(PIL.__path__[0])'):PIL" \
    --add-data "$(python3 -c 'import psd_tools; print(psd_tools.__path__[0])'):psd_tools" \
    --collect-all editor \
    --hidden-import editor.file_formats.psd_import \
    --hidden-import psd_tools \
    main.py

echo "[3/5] Creating AppDir..."
APPDIR=/tmp/AppDir-build
rm -rf "$APPDIR"
mkdir -p "$APPDIR/usr/bin"
cp dist/reverseaffinite "$APPDIR/usr/bin/"

cat > "$APPDIR/AppRun" << 'APP'
#!/bin/bash
HERE="$(dirname "$(readlink -f "$0")")"
export PATH="$HERE/usr/bin:$PATH"
exec "$HERE/usr/bin/reverseaffinite" "$@"
APP
chmod +x "$APPDIR/AppRun"

cat > "$APPDIR/reverseaffinite.desktop" << 'DESK'
[Desktop Entry]
Name=reverseaffinite Photo
Comment=Photo editor inspired by Photoshop
Exec=reverseaffinite
Icon=reverseaffinite
Type=Application
Categories=Graphics;Photography;2DGraphics;RasterGraphics;
Terminal=false
MimeType=image/png;image/jpeg;image/tiff;image/webp;image/bmp;image/x-psd;
DESK

cat > "$APPDIR/reverseaffinite.svg" << 'SVG'
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 256 256">
  <defs>
    <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#ff6b35"/>
      <stop offset="50%" style="stop-color:#7c3aed"/>
      <stop offset="100%" style="stop-color:#06b6d4"/>
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="48" fill="url(#g)"/>
  <text x="128" y="160" font-family="Arial,sans-serif" font-size="100" font-weight="bold" fill="white" text-anchor="middle">R</text>
</svg>
SVG
ln -sf reverseaffinite.svg "$APPDIR/reverseaffinite.png"

echo "[4/5] Downloading appimagetool..."
if [ ! -f /tmp/appimagetool ]; then
    wget -q https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage -O /tmp/appimagetool
    chmod +x /tmp/appimagetool
fi

echo "[5/5] Building AppImage..."
/tmp/appimagetool "$APPDIR" "$REPO_DIR/reverseaffinite-x86_64.AppImage"

echo "DONE: reverseaffinite-x86_64.AppImage ($(du -sh "$REPO_DIR/reverseaffinite-x86_64.AppImage" | cut -f1))"
