#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
PACKAGE="pdf-page-merger"
VERSION="${VERSION:-1.0.1}"
REVISION="${REVISION:-1}"
ARCH="all"
FULL_VERSION="${VERSION}-${REVISION}"
MAINTAINER="Local Package Builder <local@localhost>"
BUILD_ROOT="$APP_DIR/build/deb"
STAGE="$BUILD_ROOT/${PACKAGE}_${FULL_VERSION}_${ARCH}"
DIST_DIR="$APP_DIR/dist"
OUTPUT="$DIST_DIR/${PACKAGE}_${FULL_VERSION}_${ARCH}.deb"

for tool in dpkg-deb gzip install; do
    if ! command -v "$tool" >/dev/null 2>&1; then
        echo "缺少建置工具：$tool" >&2
        exit 1
    fi
done

for file in main.py main_window.py pdf_engine.py workers.py ui_pages.py ui_widgets.py icons.py theme.py; do
    if [ ! -f "$APP_DIR/$file" ]; then
        echo "缺少應用程式檔案：$file" >&2
        exit 1
    fi
done

rm -rf "$STAGE"
mkdir -p \
    "$STAGE/DEBIAN" \
    "$STAGE/usr/bin" \
    "$STAGE/usr/lib/$PACKAGE" \
    "$STAGE/usr/share/applications" \
    "$STAGE/usr/share/icons/hicolor/scalable/apps" \
    "$STAGE/usr/share/icons/hicolor/256x256/apps" \
    "$STAGE/usr/share/man/man1" \
    "$STAGE/usr/share/doc/$PACKAGE/docs"

for file in main.py main_window.py pdf_engine.py workers.py ui_pages.py ui_widgets.py icons.py theme.py; do
    install -m644 "$APP_DIR/$file" "$STAGE/usr/lib/$PACKAGE/$file"
done

cat > "$STAGE/usr/bin/pdf-page-merger" <<'EOF'
#!/bin/sh
exec /usr/bin/python3 -E -s /usr/lib/pdf-page-merger/main.py "$@"
EOF
chmod 755 "$STAGE/usr/bin/pdf-page-merger"

install -m644 "$APP_DIR/packaging/pdf-page-merger.desktop" \
    "$STAGE/usr/share/applications/pdf-page-merger.desktop"
install -m644 "$APP_DIR/assets/app_icon.svg" \
    "$STAGE/usr/share/icons/hicolor/scalable/apps/pdf-page-merger.svg"
install -m644 "$APP_DIR/assets/app_icon.png" \
    "$STAGE/usr/share/icons/hicolor/256x256/apps/pdf-page-merger.png"

gzip -9n -c "$APP_DIR/packaging/man/pdf-page-merger.1" \
    > "$STAGE/usr/share/man/man1/pdf-page-merger.1.gz"
gzip -9n -c "$APP_DIR/packaging/changelog" \
    > "$STAGE/usr/share/doc/$PACKAGE/changelog.Debian.gz"
chmod 644 "$STAGE/usr/share/man/man1/pdf-page-merger.1.gz" \
    "$STAGE/usr/share/doc/$PACKAGE/changelog.Debian.gz"

install -m644 "$APP_DIR/README.md" "$STAGE/usr/share/doc/$PACKAGE/README.md"
install -m644 "$APP_DIR/CHANGELOG.md" "$STAGE/usr/share/doc/$PACKAGE/CHANGELOG.md"
install -m644 "$APP_DIR/docs/release-notes-v1.0.0.md" \
    "$STAGE/usr/share/doc/$PACKAGE/docs/release-notes-v1.0.0.md"
install -m644 "$APP_DIR/docs/release-notes-v1.0.1.md" \
    "$STAGE/usr/share/doc/$PACKAGE/docs/release-notes-v1.0.1.md"
install -m644 "$APP_DIR/packaging/copyright" "$STAGE/usr/share/doc/$PACKAGE/copyright"
install -m644 "$APP_DIR/docs/screenshot.png" "$STAGE/usr/share/doc/$PACKAGE/docs/screenshot.png"
install -m644 "$APP_DIR/docs/password-dialog.png" "$STAGE/usr/share/doc/$PACKAGE/docs/password-dialog.png"

find "$STAGE/usr" -type d -exec chmod 755 {} +
find "$STAGE/usr" -type f -exec chmod 644 {} +
chmod 755 "$STAGE" "$STAGE/DEBIAN" "$STAGE/usr/bin/pdf-page-merger"

INSTALLED_SIZE="$(du -sk "$STAGE/usr" | cut -f1)"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $PACKAGE
Version: $FULL_VERSION
Section: office
Priority: optional
Architecture: $ARCH
Maintainer: $MAINTAINER
Installed-Size: $INSTALLED_SIZE
Depends: python3 (>= 3.10),
 python3-pyside6.qtwidgets,
 python3-pypdf (>= 5.0),
 python3-cryptography,
 poppler-utils
Recommends: fonts-noto-cjk, xdg-utils
Description: merge PDF files and reorder pages in a desktop app
 PDF Page Merger is a local desktop application for combining multiple
 PDF files into one document. It presents pages as draggable thumbnails,
 supports per-file passwords for encrypted PDFs, renders previews with
 poppler, and writes the merged output atomically.
EOF
chmod 644 "$STAGE/DEBIAN/control"

(
    cd "$STAGE"
    find usr -type f -print0 | LC_ALL=C sort -z | xargs -0 md5sum
) > "$STAGE/DEBIAN/md5sums"
chmod 644 "$STAGE/DEBIAN/md5sums"

if command -v desktop-file-validate >/dev/null 2>&1; then
    desktop-file-validate "$STAGE/usr/share/applications/pdf-page-merger.desktop"
fi

mkdir -p "$DIST_DIR"
rm -f "$OUTPUT" "$DIST_DIR/SHA256SUMS"
if dpkg-deb --help 2>&1 | grep -q -- '--root-owner-group'; then
    dpkg-deb --root-owner-group --build "$STAGE" "$OUTPUT"
elif command -v fakeroot >/dev/null 2>&1; then
    fakeroot dpkg-deb --build "$STAGE" "$OUTPUT"
else
    dpkg-deb --build "$STAGE" "$OUTPUT"
fi

(
    cd "$DIST_DIR"
    sha256sum "$(basename "$OUTPUT")" > SHA256SUMS
)

rm -rf "$BUILD_ROOT"
rmdir "$APP_DIR/build" 2>/dev/null || true

echo
echo "已建立：$OUTPUT"
echo "大小：$(du -h "$OUTPUT" | cut -f1)"
echo "校驗：$DIST_DIR/SHA256SUMS"
dpkg-deb --info "$OUTPUT" | sed -n '1,22p'
