# GMR — Good Morning Romane

Kid-friendly morning routine tracker for a Raspberry Pi 4 (1 GB) with the official 7" touchscreen.
Romane rides a unicorn along a trail: each step (réveil, habits, déjeuner, dents) is a stop,
the flag is 7h30. Steps are checked off by Flic buttons (webhooks) or by tapping the screen.

## Layout
- `app/server.py` — zero-dependency backend (Python stdlib: http.server + sqlite3). Port 8000.
- `app/static/index.html` — the UI, 800x480, French. Tap a stop = fait, hold 0.7 s = annuler. Live via SSE.
- `app/static/admin.html` — `/admin`: map Flic buttons to steps, set step target times and the goal, simulate presses. LAN only, no auth.
- `deploy/` — systemd units, kiosk launcher, `install.sh` (run on the Pi).
- `mockup/` — original mockups from the design conversation.

## Run locally
    python3 app/server.py            # http://localhost:8000
    curl -X POST localhost:8000/event -H 'Content-Type: application/json' -d '{"task":"wake"}'

## Deploy to the Pi
    ssh damien@192.168.68.75 'mkdir -p ~/gmr'
    scp -r app deploy damien@192.168.68.75:~/gmr/
    ssh damien@192.168.68.75 'bash ~/gmr/deploy/install.sh'

`install.sh` installs `gmr.service`, downloads the Fredoka font, and registers Chromium in
kiosk mode at boot (labwc / wayfire / X11 autostart, or cage on tty1 on Pi OS Lite).

Update later: re-run the `scp` line and `ssh damien@192.168.68.75 'sudo systemctl restart gmr'`.

## API
    POST /event          {"task":"wake|clothes|breakfast|teeth","action":"done|undo|skip"}
                         (also accepts ?task=wake&action=done)
    GET  /api/today      today's state
    GET  /api/week?offset=0
    GET  /api/stream     Server-Sent Events: "today" pushed on every change, plus "buttons" and "settings"
    GET  /health
    POST /hub-event      Flic Hub SDK payload (see below)
    GET  /api/buttons    button mapping + every button seen

## Flic Hub
Two options.

**A. Hub SDK script (`main.js` on the hub)** forwarding every press as
`{"serial":..,"name":..,"click":"click|double|hold","ts":..}` to `POST http://<pi>:8000/hub-event`.
The server maps button -> task:
1. `app/buttons.json`, edited from **http://<pi>:8000/admin**: press a button, it appears in the list,
   pick its step, save. (Keys = serial, values = task id. Re-read on every event, no restart needed.)
2. otherwise by the button's name in the Flic app: réveil / habits / déjeuner / dents (or wake / clothes / breakfast / teeth).
Click = done, double click = undo, hold = skip. Unknown buttons get a 200 with `"ok": false` (so the hub
does not retry forever) and show up in `GET /api/buttons` with their serial. Watch presses live with
`journalctl -u gmr -f` on the Pi.

**B. No script**: per button, Click -> Internet Request: POST `http://<pi>:8000/event`,
Content-Type application/json, body `{"task":"wake"}`. Double click -> `"action":"undo"`, hold -> `"action":"skip"`.

## Settings
Step target times and the goal (flag) are set from `/admin` and stored in `app/settings.json`
(not in git; created on first save). Environment variables in `deploy/gmr.service`: `GMR_GOAL` (default 07:30),
`GMR_TZ` (Europe/Zurich), `GMR_TASKS`, `GMR_PORT`, `GMR_DB`. Texts/icons/positions live at the top of `index.html`.
