#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUILD_DIR="/tmp/reverseaffinite_build"
QT_LOCAL_DIR="$PROJECT_DIR/qt_local/gcc_64"

echo "=== reverseaffinite Build Script ==="

# Try to ensure Qt5 is available for CMake
if [ -d "$QT_LOCAL_DIR/include/QtCore" ]; then
    echo "[OK] Local Qt5 headers at $QT_LOCAL_DIR"
elif dpkg -l qtbase5-dev 2>/dev/null | grep -q 'qtbase5-dev' 2>/dev/null && command -v qmake &>/dev/null; then
    echo "[OK] System Qt5 found via apt."
else
    echo "[INFO] Qt5 headers not found. Attempting to download via aqtinstall..."

    if python3 -c "import aqt" 2>/dev/null; then
        AQT_CMD="python3 -m aqt"
    else
        echo "[INFO] Installing aqtinstall..."
        if python3 -c "import sysconfig; v=sysconfig.get_config_var('EXTERNALLY_MANAGED'); exit(0 if v else 1)" 2>/dev/null; then
            pip install aqtinstall -q --break-system-packages 2>&1 || true
        else
            pip install aqtinstall -q 2>&1 || true
        fi
        if python3 -c "import aqt" 2>/dev/null; then
            AQT_CMD="python3 -m aqt"
        fi
    fi

    if [ -n "${AQT_CMD:-}" ]; then
        echo "Downloading Qt5 5.15.2..."
        QT_TMP=$(mktemp -d)
        $AQT_CMD install-qt linux desktop 5.15.2 gcc_64 -O "$QT_TMP" 2>&1
        rm -rf "$QT_LOCAL_DIR"
        mkdir -p "$PROJECT_DIR/qt_local"
        (cd "$QT_TMP/5.15.2" && tar cf - gcc_64 --dereference) | (cd "$PROJECT_DIR/qt_local" && tar xf - 2>/dev/null || true)
        rm -rf "$QT_TMP"
        find "$QT_LOCAL_DIR/lib/cmake" -name "*.cmake" -exec sed -i 's/\(libQt5[^.]*\)\.so\.5\.15\.2/\1.so/g' {} \; 2>/dev/null || true
        echo "[OK] Qt5 downloaded to $QT_LOCAL_DIR"
    else
        echo ""
        echo "[WARNING] Could not install aqtinstall."
        echo "Install manually: pip install aqtinstall --break-system-packages"
        echo "Or system Qt5:   sudo apt install qtbase5-dev qtchooser qt5-qmake"
        echo "CMake will look for system Qt5 as fallback."
    fi
fi

# Configure with CMake
echo ""
echo "=== Configuring CMake ==="
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"
cmake -S "$PROJECT_DIR" -B "$BUILD_DIR" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_EXPORT_COMPILE_COMMANDS=ON \
    -DCMAKE_PREFIX_PATH="$QT_LOCAL_DIR" \
    2>&1 || { echo "CMake configure failed. Ensure Qt5 dev headers are installed."; exit 1; }

# Build
echo ""
echo "=== Building ==="
cmake --build "$BUILD_DIR" -j"$(nproc)" 2>&1

echo ""
echo "=== Build Complete ==="
echo "Binary at: $BUILD_DIR/reverseaffinite"
echo ""
echo "To run: $BUILD_DIR/reverseaffinite"
