#!/bin/bash
# Build ReadForSleep.app from mac/launcher.applescript and install it.
#
#   mac/build.sh                 # installs to ~/Applications
#   mac/build.sh /Applications   # or anywhere else
#
# Re-run after editing the launcher or moving the project (the project path
# is hard-coded in launcher.applescript).
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
DEST="${1:-$HOME/Applications}"
APP="$DEST/ReadForSleep.app"
TMP="$(mktemp -d)"

osacompile -o "$TMP/ReadForSleep.app" "$DIR/launcher.applescript"
cp "$DIR/icon.icns" "$TMP/ReadForSleep.app/Contents/Resources/applet.icns"

PLIST="$TMP/ReadForSleep.app/Contents/Info.plist"
/usr/libexec/PlistBuddy -c 'Set :OSAAppletShowStartupScreen false' "$PLIST" 2>/dev/null \
  || /usr/libexec/PlistBuddy -c 'Add :OSAAppletShowStartupScreen bool false' "$PLIST"

# Replacing the icon breaks the seal osacompile wrote; re-sign ad hoc.
codesign --force --sign - "$TMP/ReadForSleep.app"

mkdir -p "$DEST"
# A running copy of the old applet would keep the bundle busy.
pkill -f "ReadForSleep.app/Contents/MacOS/applet" 2>/dev/null || true
rm -rf "$APP"
mv "$TMP/ReadForSleep.app" "$APP"
rmdir "$TMP"
touch "$APP"   # nudge Finder / Launchpad to refresh the icon
echo "Installed $APP"
