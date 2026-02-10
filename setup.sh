#!/usr/bin/env bash
# setup.sh - Downloads SVG datasets and builds TinyVG conversion tools.
#
# After running this, the conversion pipeline (convert_and_analyze.py) can be
# executed to produce TVG files and compression benchmarks.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORK="/tmp/tinyvg-eval-work"
mkdir -p "$WORK"

# ---------- 1. Zig compiler (needed to build TinyVG SDK) ----------
ZIG_VERSION="0.14.0"
ZIG_DIR="$WORK/zig-linux-x86_64-$ZIG_VERSION"
if [ ! -x "$ZIG_DIR/zig" ]; then
    echo ">> Downloading Zig $ZIG_VERSION ..."
    curl -sL "https://ziglang.org/download/$ZIG_VERSION/zig-linux-x86_64-$ZIG_VERSION.tar.xz" \
        | tar xJ -C "$WORK"
fi
export PATH="$ZIG_DIR:$PATH"
echo "   Zig: $(zig version)"

# ---------- 2. TinyVG SDK (tvg-text, svg2tvgt) ----------
SDK_DIR="$WORK/tinyvg-sdk"
if [ ! -d "$SDK_DIR" ]; then
    echo ">> Cloning TinyVG SDK ..."
    git clone --depth 1 https://github.com/TinyVG/sdk.git "$SDK_DIR"
fi

# Build Zig tools (tvg-text)
if [ ! -x "$SDK_DIR/zig-out/bin/tvg-text" ]; then
    echo ">> Building TinyVG Zig tools ..."
    # Pre-fetch Zig dependencies (the Zig package manager may not work through proxies)
    ZIG_CACHE="$WORK/zig-cache"
    mkdir -p "$ZIG_CACHE/p"
    for dep_url_hash in \
        "https://github.com/ikskuh/zig-args/archive/9425b94c103a031777fdd272c555ce93a7dea581.zip args-0.0.0-CiLiqv_NAAC97fGpk9hS2K681jkiqPsWP6w3ucb_ctGH" \
        "https://github.com/ikskuh/parser-toolkit/archive/0d5e00d4830bca53d10fee5d562152f1329d5784.zip parser_toolkit-0.1.0-baYGPS1CEwDuQk1W_5QEfKF_BWU5lN4qb8kVZoQ6Id9k"; do
        url="${dep_url_hash% *}"
        hash="${dep_url_hash#* }"
        dest="$ZIG_CACHE/p/$hash"
        if [ ! -d "$dest" ]; then
            tmpzip="$WORK/dep-$hash.zip"
            curl -sL "$url" -o "$tmpzip"
            mkdir -p "$dest"
            unzip -qo "$tmpzip" -d "$dest"
            # Move files out of the nested directory
            subdir=$(ls "$dest")
            mv "$dest/$subdir"/* "$dest/" 2>/dev/null || true
            rmdir "$dest/$subdir" 2>/dev/null || true
            rm -f "$tmpzip"
        fi
    done
    (cd "$SDK_DIR" && ZIG_GLOBAL_CACHE_DIR="$ZIG_CACHE" zig build --system "$ZIG_CACHE/p")
fi
echo "   tvg-text: $SDK_DIR/zig-out/bin/tvg-text"

# Build .NET tool (svg2tvgt)
SVG2TVGT_DLL="$SDK_DIR/src/tools/svg2tvgt/bin/Debug/net8.0/svg2tvgt.dll"
if [ ! -f "$SVG2TVGT_DLL" ]; then
    echo ">> Building svg2tvgt (.NET) ..."
    # Patch target framework to net8.0 if needed
    sed -i 's/net6\.0/net8.0/' "$SDK_DIR/src/tools/svg2tvgt/svg2tvgt.csproj"
    (cd "$SDK_DIR/src/tools/svg2tvgt" && dotnet restore --source /dev/null && dotnet build --no-restore)
fi
echo "   svg2tvgt: $SVG2TVGT_DLL"

# ---------- 3. SVGO (SVG optimizer) ----------
if ! command -v svgo &>/dev/null; then
    echo ">> Installing SVGO ..."
    npm install -g svgo
fi
echo "   svgo: $(svgo --version)"

# ---------- 4. Compression tools ----------
for tool in zstd brotli; do
    if ! command -v "$tool" &>/dev/null; then
        echo ">> Installing $tool ..."
        apt-get install -y "$tool"
    fi
done
echo "   zstd: $(zstd --version 2>&1)"
echo "   brotli: $(brotli --version 2>&1)"

# ---------- 5. SVG source datasets ----------
SVG_BASE="$WORK/svg-sources"
mkdir -p "$SVG_BASE"

# 5a. Zig logos
ZIG_SVG="$SVG_BASE/zig-logo"
if [ ! -d "$ZIG_SVG" ]; then
    echo ">> Downloading Zig logo SVGs ..."
    git clone --depth 1 https://github.com/ziglang/logo.git "$ZIG_SVG"
fi

# 5b. W3C SVG samples (from dev.w3.org svgweb)
W3C_SVG="$SVG_BASE/w3c"
if [ ! -d "$W3C_SVG" ] || [ "$(ls "$W3C_SVG"/*.svg 2>/dev/null | wc -l)" -lt 100 ]; then
    echo ">> Downloading W3C SVG samples ..."
    mkdir -p "$W3C_SVG"
    curl -sL "https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/" \
        | python3 -c "
import sys, re
html = sys.stdin.read()
for f in re.findall(r'<a href=\"([^\"]+\.svg)\">', html):
    print(f)
" | while read -r fname; do
        curl -sL "https://dev.w3.org/SVG/tools/svgweb/samples/svg-files/$fname" \
            -o "$W3C_SVG/$fname"
    done
fi

# 5c. Material Design icons
MDI_REPO="$SVG_BASE/material-design-repo"
MDI_SVG="$SVG_BASE/material-design"
if [ ! -d "$MDI_SVG" ] || [ "$(ls "$MDI_SVG"/*.svg 2>/dev/null | wc -l)" -lt 1000 ]; then
    echo ">> Downloading Material Design SVGs ..."
    if [ ! -d "$MDI_REPO" ]; then
        git clone --depth 1 https://github.com/Templarian/MaterialDesign-SVG.git "$MDI_REPO"
    fi
    mkdir -p "$MDI_SVG"
    cp "$MDI_REPO"/svg/*.svg "$MDI_SVG/"
fi

# 5d. Papirus icons
PAPIRUS_REPO="$SVG_BASE/papirus-repo"
PAPIRUS_SVG="$SVG_BASE/papirus"
if [ ! -d "$PAPIRUS_SVG" ] || [ "$(ls "$PAPIRUS_SVG"/*.svg 2>/dev/null | wc -l)" -lt 1000 ]; then
    echo ">> Downloading Papirus SVGs ..."
    if [ ! -d "$PAPIRUS_REPO" ]; then
        git clone --depth 1 https://github.com/PapirusDevelopmentTeam/papirus-icon-theme.git "$PAPIRUS_REPO"
    fi
    mkdir -p "$PAPIRUS_SVG"
    # Collect unique SVGs (by basename) from Papirus theme
    find "$PAPIRUS_REPO/Papirus" -name "*.svg" -print0 \
        | while IFS= read -r -d '' f; do
            bn="$(basename "$f")"
            [ -f "$PAPIRUS_SVG/$bn" ] || cp "$f" "$PAPIRUS_SVG/$bn"
        done
fi

# 5e. FreeSVG.org - these 5 specific files are no longer easily retrievable from
# the site. We skip them (0.2% of the dataset) and note the omission.

echo ""
echo "=== Setup complete ==="
echo "Zig logos:        $(ls "$SVG_BASE/zig-logo"/*.svg 2>/dev/null | wc -l) SVGs"
echo "W3C samples:      $(ls "$SVG_BASE/w3c"/*.svg 2>/dev/null | wc -l) SVGs"
echo "Material Design:  $(ls "$SVG_BASE/material-design"/*.svg 2>/dev/null | wc -l) SVGs"
echo "Papirus:          $(ls "$SVG_BASE/papirus"/*.svg 2>/dev/null | wc -l) SVGs"
echo ""
echo "Run: python3 convert_and_analyze.py"
