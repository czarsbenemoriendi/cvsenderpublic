#!/bin/bash
# Render launchd/pl.cvsender.scout.plist.template with your $HOME and install
# it into ~/Library/LaunchAgents. Refuses to overwrite a modified installed
# plist — the diff prints first, you decide.
#
# Re-run after editing the template (schedule, paths): it diffs and guides
# through bootout+bootstrap instead of silently diverging.
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TEMPLATE="$DIR/pl.cvsender.scout.plist.template"
LABEL="pl.cvsender.scout"
TARGET="$HOME/Library/LaunchAgents/$LABEL.plist"

[ -f "$TEMPLATE" ] || { echo "template missing: $TEMPLATE" >&2; exit 1; }

mkdir -p "$(dirname "$TARGET")"
sed -e "s|__HOME__|$HOME|g" "$TEMPLATE" > "$TARGET.new"

if [ -f "$TARGET" ] && ! diff -q "$TARGET" "$TARGET.new" >/dev/null 2>&1; then
    echo "=== installed plist differs from template:" >&2
    diff -u "$TARGET" "$TARGET.new" || true
    echo "=== resolve intentionally:" >&2
    echo "  launchctl bootout gui/$(id -u)/$LABEL" >&2
    echo "  mv $TARGET.new $TARGET" >&2
    echo "  launchctl bootstrap gui/$(id -u) $TARGET" >&2
    exit 1
fi

mv "$TARGET.new" "$TARGET"
launchctl bootstrap "gui/$(id -u)" "$TARGET" 2>/dev/null \
    || echo "already bootstrapped (re-run bootout+bootstrap after schedule changes)"
echo "installed: $TARGET"
