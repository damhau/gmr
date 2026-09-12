#!/bin/bash
# Launches Chromium full-screen on the GMR page. Waits for the server first.
# --once : run the browser a single time (systemd/cage restarts it); default: loop forever (desktop autostart).
URL="${GMR_URL:-http://127.0.0.1:8000}"
BROWSER=$(command -v chromium || command -v chromium-browser || true)
[ -z "$BROWSER" ] && { echo "kiosk: no chromium found" >&2; exit 1; }

for i in $(seq 1 60); do
  curl -fsS -m 2 "$URL/health" >/dev/null 2>&1 && break
  sleep 1
done

FLAGS=(
  --kiosk "$URL"
  --incognito --noerrdialogs --no-first-run --disable-infobars
  --disable-session-crashed-bubble --disable-features=Translate,MediaRouter,TranslateUI
  --disable-component-update --disable-sync --disable-breakpad --disable-extensions
  --disable-background-networking --check-for-update-interval=31536000
  --overscroll-history-navigation=0 --disable-pinch --touch-events=enabled
  --autoplay-policy=no-user-gesture-required --password-store=basic
  --renderer-process-limit=2 --js-flags=--max-old-space-size=128
  --hide-scrollbars --lang=fr
)
[ -n "$WAYLAND_DISPLAY" ] && FLAGS+=(--ozone-platform=wayland)

if [ "$1" = "--once" ]; then
  exec "$BROWSER" "${FLAGS[@]}"
fi
while true; do
  "$BROWSER" "${FLAGS[@]}"
  sleep 2
done
