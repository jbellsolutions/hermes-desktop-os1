#!/bin/bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PATH="${HOME}/.swiftly/bin:${PATH}"

cd "$ROOT_DIR"
HERMES_MAC_ARCHS=arm64 bash scripts/build-macos-app.sh || {
  EXEC="${ROOT_DIR}/.build/arm64-apple-macosx/release/OS1"
  BUNDLE="${ROOT_DIR}/dist/OS1.app"
  MACOS="${BUNDLE}/Contents/MacOS"
  RES="${BUNDLE}/Contents/Resources"
  mkdir -p "$MACOS" "$RES"
  cp "$EXEC" "$MACOS/OS1"
  xcrun strip -S -x "$MACOS/OS1"
  cp packaging/Info.plist "$BUNDLE/Contents/Info.plist"
  cp packaging/OS1.icns "$RES/AppIcon.icns"
  cp Vendor/SwiftTerm/Sources/SwiftTerm/Apple/Metal/Shaders.metal "$RES/Shaders.metal"
  cp -R .build/arm64-apple-macosx/release/OS1_OS1.bundle "$RES/"
  find Sources/OS1/Resources -maxdepth 1 -name '*.lproj' -exec cp -R {} "$RES/" \;
  BID=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$BUNDLE/Contents/Info.plist")
  codesign --force --deep --sign - --requirements "=designated => identifier \"$BID\"" "$BUNDLE"
}

osascript -e 'quit app "OS1"' 2>/dev/null || true
sleep 1
rm -rf /Applications/OS1.app
cp -R "$ROOT_DIR/dist/OS1.app" /Applications/OS1.app
open /Applications/OS1.app
