#!/bin/bash
# Launches Chromium full-screen on the GMR page. Waits for the server first.
# --once : run the browser a single time (systemd/cage restarts it); default: loop forever (desktop autostart).
URL="${GMR_URL:-http://127.0.0.1:8000}"
# Prefer the real binary over the /usr/bin/chromium wrapper: Raspberry Pi OS's wrapper injects
# --force-renderer-accessibility, --enable-gpu-rasterization, --use-angle=gles, remote extensions...
# which cost memory and paint a grey window on a Pi 4 under Wayland.
BROWSER=""
for c in /usr/lib/chromium/chromium /usr/lib/chromium-browser/chromium-browser; do [ -x "$c" ] && { BROWSER=$c; break; }; done
[ -z "$BROWSER" ] && BROWSER=$(command -v chromium || command -v chromium-browser || true)
[ -z "$BROWSER" ] && { echo "kiosk: no chromium found" >&2; exit 1; }

for i in $(seq 1 60); do
  curl -fsS -m 2 "$URL/health" >/dev/null 2>&1 && break
  sleep 1
done

FLAGS=(
  --kiosk "$URL"
  --incognito --noerrdialogs --no-first-run --disable-infobars
  --disable-session-crashed-bubble --disable-translate --disable-features=Translate,TranslateUI,MediaRouter
  --disable-component-update --disable-sync --disable-breakpad --disable-extensions
  --disable-background-networking --check-for-update-interval=31536000
  --overscroll-history-navigation=0 --disable-pinch --touch-events=enabled
  --autoplay-policy=no-user-gesture-required --password-store=basic
  # Pi 4 / 1 GB: GPU compositing under Wayland paints a grey window and costs a GPU process; software is plenty for this page
  --disable-gpu --renderer-process-limit=1 --process-per-site --js-flags=--max-old-space-size=96
  --disable-dev-shm-usage --no-default-browser-check --disable-pings
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
