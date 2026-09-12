#!/bin/bash
# Auto-deployer: pulls the latest commit from GitHub and restarts the server, with rollback.
#   autodeploy.sh --scheduled   (from gmr-deploy.timer: respects the quiet window)
#   autodeploy.sh --force       (from gmr-deploy-now.service / the admin button)
# State: $DATA_DIR/VERSION ("<sha> <iso date>"), $DATA_DIR/deploy.log
set -uo pipefail
REPO="${GMR_REPO:-$HOME/gmr}"
DATA_DIR="${GMR_DATA:-$HOME/gmr-data}"
BRANCH="${GMR_BRANCH:-main}"
QUIET_FROM="${GMR_QUIET_FROM:-0600}"; QUIET_TO="${GMR_QUIET_TO:-0800}"   # no deploy during the routine
HEALTH="http://127.0.0.1:${GMR_PORT:-8000}/health"
LOG="$DATA_DIR/deploy.log"
mkdir -p "$DATA_DIR"

log(){ printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*" | tee -a "$LOG" >&2; }
rotate(){ [ "$(wc -l < "$LOG" 2>/dev/null || echo 0)" -gt 600 ] && tail -n 400 "$LOG" > "$LOG.tmp" && mv "$LOG.tmp" "$LOG"; true; }
healthy(){ for _ in $(seq 1 20); do curl -fsS -m 2 "$HEALTH" >/dev/null 2>&1 && return 0; sleep 1; done; return 1; }

# Whole body in a function: bash parses the file completely before running it, so git replacing this
# script mid-deploy (it updates itself) cannot corrupt the run.
main(){
exec 9>"$DATA_DIR/.deploy.lock"
flock -n 9 || { log "another deploy is running, skipping"; exit 0; }

MODE="${1:---scheduled}"
write_version(){ printf '%s %s\n' "$(git rev-parse --short HEAD)" "$(date -Iseconds)" > "$DATA_DIR/VERSION"; }
restart(){ sudo -n systemctl restart gmr.service 9>&-; }   # 9>&- : never leak the lock to children
restart_kiosk(){
  if systemctl is-enabled gmr-kiosk.service >/dev/null 2>&1; then sudo -n systemctl restart gmr-kiosk.service 9>&-; return; fi
  # desktop session (labwc/wayfire/X11): kill the old browser, relaunch kiosk.sh inside the session
  pkill -f "gmr/deploy/kiosk.sh"; pkill -f "chromium.*--kiosk"; sleep 1
  export XDG_RUNTIME_DIR="/run/user/$(id -u)"
  WD=$(ls "$XDG_RUNTIME_DIR" 2>/dev/null | grep -m1 '^wayland-[0-9]*$'); [ -n "$WD" ] && export WAYLAND_DISPLAY="$WD"
  [ -z "${DISPLAY:-}" ] && [ -S /tmp/.X11-unix/X0 ] && export DISPLAY=:0
  nohup setsid "$REPO/deploy/kiosk.sh" >/dev/null 2>&1 9>&- &
}
if [ "$MODE" = "--kiosk" ]; then log "kiosk restart requested"; restart_kiosk; return 0; fi

if [ "$MODE" = "--scheduled" ]; then
  NOW=$(date +%H%M)
  if [ "$NOW" -ge "$QUIET_FROM" ] && [ "$NOW" -lt "$QUIET_TO" ]; then return 0; fi   # quiet window, silently skip
fi

cd "$REPO" || { log "repo $REPO missing"; return 1; }
if ! git fetch -q origin "$BRANCH" 2>>"$LOG"; then log "git fetch failed (offline?)"; return 1; fi
LOCAL=$(git rev-parse HEAD); REMOTE=$(git rev-parse "origin/$BRANCH")
if [ "$LOCAL" = "$REMOTE" ]; then
  [ "$MODE" = "--force" ] && log "up to date (${LOCAL:0:7})"
  return 0
fi
# a commit that already failed its health check is not retried by the timer (only by --force or a newer commit)
if [ "$MODE" = "--scheduled" ] && [ "$(cat "$DATA_DIR/failed_sha" 2>/dev/null)" = "$REMOTE" ]; then return 0; fi

log "update ${LOCAL:0:7} -> ${REMOTE:0:7}: $(git log -1 --format=%s "$REMOTE")"
CHANGED=$(git diff --name-only "$LOCAL" "$REMOTE")
git reset -q --hard "$REMOTE" || { log "git reset failed"; return 1; }


if echo "$CHANGED" | grep -q '^deploy/'; then
  log "deploy/ changed: refreshing units and kiosk script"
  SKIP_APT=1 bash "$REPO/deploy/install.sh" >>"$LOG" 2>&1 || log "install.sh --refresh reported an error (see above)"
fi

write_version
restart
if healthy; then
  rm -f "$DATA_DIR/failed_sha"
  log "OK: running $(git rev-parse --short HEAD)"
  if echo "$CHANGED" | grep -q '^deploy/kiosk.sh$'; then
    log "kiosk.sh changed: restarting the kiosk browser"
    restart_kiosk
  fi
  rotate; return 0
fi

log "HEALTH CHECK FAILED on ${REMOTE:0:7}, rolling back to ${LOCAL:0:7} (this commit will not be retried automatically)"
echo "$REMOTE" > "$DATA_DIR/failed_sha"
git reset -q --hard "$LOCAL"
write_version
restart
if healthy; then log "rolled back, running ${LOCAL:0:7}"; else log "ROLLBACK ALSO UNHEALTHY - check: journalctl -u gmr -n 50"; fi
rotate; return 1
}
main "$@"
exit $?
