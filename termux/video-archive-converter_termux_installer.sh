#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

VERSION="1.0.0"
PKG="video-archive-converter_${VERSION}_all_termux.deb"

trap 'rm -f "$PKG"' EXIT

curl -LO "https://github.com/BlueSlime07/Video_archive_converter/releases/download/${VERSION}/${PKG}"

pkg install "./${PKG}"

echo
echo "Video Archive Converter installed successfully."
echo
echo "Run:"
echo "  video-archive-converter --help"
