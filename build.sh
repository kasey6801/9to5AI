#!/usr/bin/env bash
set -euo pipefail

APP_NAME="9to5AI"
SPEC_FILE="9to5AI.spec"
VENV_PYINSTALLER=".venv/bin/pyinstaller"

echo "==> Checking environment..."
if [ ! -f "$VENV_PYINSTALLER" ]; then
    echo "ERROR: .venv not found. Run setup first:"
    echo "  python3 -m venv .venv"
    echo "  .venv/bin/pip install flask feedparser beautifulsoup4 lxml requests certifi pyinstaller"
    exit 1
fi

if [ ! -f "$SPEC_FILE" ]; then
    echo "ERROR: $SPEC_FILE not found."
    exit 1
fi

echo "==> Generating app icon..."
.venv/bin/pip install Pillow -q
.venv/bin/python make_icon.py
mkdir -p 9to5AI.iconset
sips -z 16 16     9to5AI_icon.png --out 9to5AI.iconset/icon_16x16.png     >/dev/null
sips -z 32 32     9to5AI_icon.png --out 9to5AI.iconset/icon_16x16@2x.png  >/dev/null
sips -z 32 32     9to5AI_icon.png --out 9to5AI.iconset/icon_32x32.png     >/dev/null
sips -z 64 64     9to5AI_icon.png --out 9to5AI.iconset/icon_32x32@2x.png  >/dev/null
sips -z 128 128   9to5AI_icon.png --out 9to5AI.iconset/icon_128x128.png   >/dev/null
sips -z 256 256   9to5AI_icon.png --out 9to5AI.iconset/icon_128x128@2x.png >/dev/null
sips -z 256 256   9to5AI_icon.png --out 9to5AI.iconset/icon_256x256.png   >/dev/null
sips -z 512 512   9to5AI_icon.png --out 9to5AI.iconset/icon_256x256@2x.png >/dev/null
sips -z 512 512   9to5AI_icon.png --out 9to5AI.iconset/icon_512x512.png   >/dev/null
sips -z 1024 1024 9to5AI_icon.png --out 9to5AI.iconset/icon_512x512@2x.png >/dev/null
iconutil -c icns 9to5AI.iconset
rm -rf 9to5AI.iconset

echo "==> Stopping any running instance on port 5002..."
lsof -ti :5002 | xargs kill -9 2>/dev/null || true

echo "==> Cleaning previous builds..."
xattr -cr build/ dist/ 2>/dev/null || true
rm -rf build/ dist/

echo "==> Running PyInstaller (this may take a few minutes)..."
"$VENV_PYINSTALLER" "$SPEC_FILE" --noconfirm

APP_PATH="dist/${APP_NAME}.app"
if [ ! -d "$APP_PATH" ]; then
    echo "ERROR: Expected $APP_PATH was not created. Check PyInstaller output above."
    exit 1
fi

echo "==> Ad-hoc signing the app bundle..."
# Remove stale quarantine flags
xattr -cr "$APP_PATH"
# Sign bundled Python framework explicitly before the deep sign
for fw in "$APP_PATH"/Contents/Frameworks/Python.framework/Versions/*/Python; do
    if [ -f "$fw" ]; then
        codesign --force --sign - "$fw"
    fi
done
# Deep-sign the full bundle (no --options runtime — hardened runtime conflicts with
# bundled Python.framework signed by python.org)
codesign --deep --force --sign - "$APP_PATH"

echo "==> Verifying signature..."
codesign --verify --deep --strict "$APP_PATH" && echo "    Signature OK"

echo "==> Creating DMG installer..."
DMG_PATH="dist/${APP_NAME}.dmg"
DMG_TMP="dist/${APP_NAME}-tmp.dmg"
DMG_STAGE="dist/dmg-stage"

rm -rf "$DMG_STAGE"
mkdir -p "$DMG_STAGE"
cp -R "$APP_PATH" "$DMG_STAGE/"
ln -s /Applications "$DMG_STAGE/Applications"

hdiutil create \
    -volname "$APP_NAME" \
    -srcfolder "$DMG_STAGE" \
    -ov \
    -format UDRW \
    "$DMG_TMP"
rm -rf "$DMG_STAGE"

# Mount r/w DMG to set Finder icon positions
MOUNT_DIR=$(hdiutil attach "$DMG_TMP" -readwrite -noverify -noautoopen | \
    awk 'END {$1=$2=""; print substr($0,3)}' | xargs)

osascript << APPLESCRIPT
tell application "Finder"
    tell disk "$APP_NAME"
        open
        set current view of container window to icon view
        set toolbar visible of container window to false
        set statusbar visible of container window to false
        set the bounds of container window to {400, 200, 900, 500}
        set theViewOptions to the icon view options of container window
        set arrangement of theViewOptions to not arranged
        set icon size of theViewOptions to 100
        set position of item "${APP_NAME}.app" of container window to {150, 150}
        set position of item "Applications" of container window to {350, 150}
        close
        open
        update without registering applications
        delay 2
    end tell
end tell
APPLESCRIPT

hdiutil detach "$MOUNT_DIR" -quiet
hdiutil convert "$DMG_TMP" -format UDZO -o "$DMG_PATH" -ov
rm -f "$DMG_TMP"

BUNDLE_SIZE=$(du -sh "$APP_PATH" | cut -f1)
DMG_SIZE=$(du -sh "$DMG_PATH" | cut -f1)
echo ""
echo "====================================================="
echo "  Build complete: $APP_PATH  ($BUNDLE_SIZE)"
echo "  DMG installer: $DMG_PATH  ($DMG_SIZE)"
echo "====================================================="
echo ""
echo "To test the app:    open $APP_PATH"
echo "To test the DMG:    open $DMG_PATH"
echo ""
echo "NOTE: First launch on another Mac requires right-click → Open"
echo "      to bypass Gatekeeper (no Developer ID — one-time only)."
