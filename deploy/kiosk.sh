#!/bin/bash
# Launches Chromium full-screen on the GMR page. Waits for the server first.
# --once : run the browser a single time (systemd/cage restarts it); default: loop forever (desktop autostart).
URL="${GMR_URL:-http://127.0.0.1:8000}"
LOGF="${GMR_DATA:-$HOME/gmr-data}/kiosk.log"; mkdir -p "$(dirname "$LOGF")"
# keep the log short: truncate at each script start, then log every browser launch/exit
{ echo "=== kiosk.sh start $(date '+%F %T')  uptime=$(cut -d' ' -f1 /proc/uptime)s  WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-}  DISPLAY=${DISPLAY:-}  XDG_RUNTIME_DIR=${XDG_RUNTIME_DIR:-}  XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-}"; } > "$LOGF"
exec 2>>"$LOGF"
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
# Wait for the network to be up (Chromium's network service crashes at boot if it starts while interfaces move)
for i in $(seq 1 "${GMR_KIOSK_NET_WAIT:-30}"); do ip route 2>/dev/null | grep -q "^default" && break; sleep 1; done
# Let the compositor settle (output mode/rotation applied by kanshi or wlr-randr)
sleep "${GMR_KIOSK_DELAY:-10}"
command -v wlr-randr >/dev/null && wlr-randr >>"$LOGF" 2>&1

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

if [ "${1:-}" = "--once" ]; then
  echo "launch $(date '+%T') $BROWSER" >>"$LOGF"
  exec "$BROWSER" "${FLAGS[@]}" >>"$LOGF" 2>&1
fi
# Watchdog: the page keeps a live SSE stream to the server from 127.0.0.1. No local stream = page not loaded
# (e.g. Chromium's network service crashed during the first load -> empty window). Then relaunch the browser.
local_streams(){ curl -fsS -m 3 "$URL/api/kiosk" 2>/dev/null | grep -o '"local_streams": *[0-9]*' | grep -o '[0-9]*$'; }
while true; do
  echo "launch $(date '+%T') $BROWSER" >>"$LOGF"
  "$BROWSER" "${FLAGS[@]}" >>"$LOGF" 2>&1 &
  BPID=$!
  loaded=0; misses=0; t=0
  while kill -0 "$BPID" 2>/dev/null; do
    sleep 5; t=$((t+5))
    n=$(local_streams); n=${n:-0}
    if [ "$n" -ge 1 ]; then loaded=1; misses=0
    elif [ "$loaded" = 0 ] && [ "$t" -ge "${GMR_KIOSK_LOAD_TIMEOUT:-45}" ]; then
      echo "watchdog $(date '+%T'): page not loaded after ${t}s, relaunching browser" >>"$LOGF"; kill "$BPID"; break
    elif [ "$loaded" = 1 ]; then
      misses=$((misses+1))
      if [ "$misses" -ge 12 ]; then echo "watchdog $(date '+%T'): page stream gone for 60s, relaunching browser" >>"$LOGF"; kill "$BPID"; break; fi
    fi
  done
  wait "$BPID" 2>/dev/null; echo "browser exited rc=$? $(date '+%T')" >>"$LOGF"
  sleep 2
done
