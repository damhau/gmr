# GMR — Good Morning Romane

Kid-friendly morning routine tracker for a Raspberry Pi 4 (1 GB) with the official 7" touchscreen.
Romane rides a unicorn along a trail: each step (réveil, habits, déjeuner, dents) is a stop,
the flag is 7h30. Steps are checked off by Flic buttons (webhooks) or by tapping the screen.

## Layout
- `app/server.py` — zero-dependency backend (Python stdlib: http.server + sqlite3). Port 8000.
- `app/static/index.html` — the UI, 800x480, French. Tap a stop = fait, hold 0.7 s = annuler. Live via SSE.
  The week strip shows Monday to Friday only, and the streak skips weekends (they neither count nor break it).
- `app/static/report.html` — `/report`: review dashboard (KPIs, finish-time trend, weekly stacks, calendar, per-step and per-weekday stats, journal, CSV export). Inline SVG, no libraries.
  School days only: Saturdays and Sundays are left out of every stat, chart and the CSV, even if the routine was done.
- `app/seed_demo.py` — fills a *separate* database with fake mornings to try `/report`: `GMR_DB=/tmp/demo.db python3 app/seed_demo.py --weeks 10`.
- `app/static/admin.html` — `/admin`: map Flic buttons to steps, set step target times and the goal, simulate presses. LAN only, no auth.
- `deploy/` — systemd units, kiosk launcher, `install.sh` (run on the Pi).
- `mockup/` — original mockups from the design conversation.

## Run locally
    python3 app/server.py            # http://localhost:8000
    curl -X POST localhost:8000/event -H 'Content-Type: application/json' -d '{"task":"wake"}'

## Deploy to the Pi
First time only:

    ssh damien@192.168.68.75
    git clone https://github.com/damhau/gmr.git ~/gmr && bash ~/gmr/deploy/install.sh

`install.sh` installs `gmr.service` (state in `~/gmr-data`: database, buttons.json, settings.json),
downloads the Fredoka font, registers Chromium in kiosk mode at boot (labwc / wayfire / X11 autostart,
or cage on tty1 on Pi OS Lite) and enables the auto-deployer.

### Updates are automatic
`gmr-deploy.timer` runs `deploy/autodeploy.sh` every 5 minutes (never between 06:00 and 08:00):

1. `git fetch`; nothing to do if the Pi already runs `origin/main`.
2. `git reset --hard origin/main`, re-run `install.sh` if anything under `deploy/` changed.
3. `systemctl restart gmr`, then poll `/health` for 20 s.
4. If unhealthy: reset to the previous commit, restart again, log it.

The server includes its version (git commit) in every SSE "today" message; the kiosk page reloads itself
when the version changes, so **push to `main` and the screen updates within ~5 minutes**.
The admin page shows the running version and the deploy log, and has an "update now" button
(`POST /api/deploy` -> `systemctl start gmr-deploy-now.service`, via a NOPASSWD sudoers rule installed by `install.sh`).

Manual: `ssh damien@192.168.68.75 'sudo systemctl start gmr-deploy-now.service; tail ~/gmr-data/deploy.log'`

## Themes
The kid screen is themed. One JSON file per theme in `app/static/themes/` (colours, texts with `{goal}`/`{time}`
placeholders, station icons, sky, decorations, confetti, and the rider as an SVG fragment in an 80x80 box).
Shipped: licorne (default), shrek, harry-potter, kpop-demon-hunters, totoro, espace, pirates, dinosaures, sirene,
pokemon, minecraft, mandalorian (Grogu), vice-versa (Joie), lego, rock-star. Switch in `/admin` (applies live over SSE), preview any with `/?theme=<id>`.
To add one: edit `app/tools_make_themes.py` (or write the JSON by hand), run it, push. `GET /api/themes` lists them.

## API
    POST /event          {"task":"wake|clothes|breakfast|teeth","action":"done|undo|skip"}
                         (also accepts ?task=wake&action=done)
    GET  /api/today      today's state
    GET  /api/week?offset=0      Mon-Fri of that week + current streak (weekends skipped)
    GET  /api/version    running version + deploy log;  POST /api/deploy triggers a check now
    GET  /api/report?days=56     everything /report shows, Mon-Fri only (max 730 days); /api/report.csv?days=56 for a spreadsheet
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
