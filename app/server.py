#!/usr/bin/env python3
"""Good Morning Romane - morning routine tracker.

Zero dependencies: Python 3.9+ stdlib (http.server + sqlite3 + zoneinfo).

Run:      python3 server.py            (listens on 0.0.0.0:8000)
Env:      GMR_PORT, GMR_DB, GMR_TZ, GMR_GOAL (default HH:MM, overridden by settings.json), GMR_TASKS

API:
  POST /event            {"task":"wake","action":"done|undo|skip"}   <- UI taps / simple webhooks
  POST /hub-event        {"serial":"BF3...","name":"Réveil","click":"click|double|hold","ts":...}
                         <- Flic Hub SDK forwarder (main.js). Button -> task via buttons.json
                            (keys = serial or button name, values = task id), else by button name.
                            click=done, double=undo, hold=skip.
  GET  /api/buttons      mapping + every button seen so far (to find serials)
  POST /api/buttons      {"mapping": {"<serial>": "<task>"|""}}  writes buttons.json ("" removes)
  POST /api/buttons/forget {"serial": "..."}  drop a button from the seen list
  GET/POST /api/settings {"goal":"07:30","targets":{"wake":"06:45",...}}  -> settings.json
  GET  /admin            configuration page: buttons + step times (LAN only, no auth)
  GET  /api/today
  GET  /api/week?offset=0
  GET  /                 -> static/index.html
  GET  /static/<file>
"""
import json
import mimetypes
import os
import re
import queue
import sqlite3
import sys
import threading
from datetime import date, datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
STATIC = HERE / "static"
DB = Path(os.environ.get("GMR_DB", HERE / "morning.db"))
TZ = ZoneInfo(os.environ.get("GMR_TZ", "Europe/Zurich"))
GOAL_TIME = os.environ.get("GMR_GOAL", "07:30")
TASKS = [t for t in os.environ.get("GMR_TASKS", "wake,clothes,breakfast,teeth").split(",") if t]
PORT = int(os.environ.get("GMR_PORT", "8000"))
ACTIONS = ("done", "undo", "skip")
BUTTONS_FILE = Path(os.environ.get("GMR_BUTTONS", HERE / "buttons.json"))
SETTINGS_FILE = Path(os.environ.get("GMR_SETTINGS", HERE / "settings.json"))
DEFAULT_TARGETS = {"wake": "06:45", "clothes": "07:00", "breakfast": "07:10", "teeth": "07:20"}
CLICK_ACTION = {"click": "done", "single": "done", "double": "undo", "hold": "skip"}
# button names (as typed in the Flic app) that resolve to a task without buttons.json
NAME_ALIASES = {
    "wake": "wake", "reveil": "wake", "réveil": "wake", "lever": "wake", "debout": "wake",
    "clothes": "clothes", "habits": "clothes", "habiller": "clothes", "vetements": "clothes", "vêtements": "clothes",
    "breakfast": "breakfast", "dejeuner": "breakfast", "déjeuner": "breakfast", "petit-dejeuner": "breakfast", "manger": "breakfast",
    "teeth": "teeth", "dents": "teeth", "brosser": "teeth",
}


# --- Server-Sent Events: one queue per connected browser -------------------------
_subs, _subs_lock = set(), threading.Lock()


def notify(kind: str, data=None):
    msg = (kind, json.dumps(data if data is not None else {}))
    with _subs_lock:
        subs = list(_subs)
    for q in subs:
        try:
            q.put_nowait(msg)
        except queue.Full:
            pass


def valid_time(v) -> bool:
    return isinstance(v, str) and bool(re.fullmatch(r"([01]\d|2[0-3]):[0-5]\d", v))


def settings() -> dict:
    """settings.json: {"goal": "07:30", "targets": {"wake": "06:45", ...}} - edited from /admin."""
    goal, targets = GOAL_TIME, {t: DEFAULT_TARGETS.get(t, "") for t in TASKS}
    try:
        d = json.loads(SETTINGS_FILE.read_text())
        if valid_time(d.get("goal")):
            goal = d["goal"]
        for t, v in (d.get("targets") or {}).items():
            if t in targets and (valid_time(v) or v == ""):
                targets[t] = v
    except (FileNotFoundError, ValueError, AttributeError):
        pass
    return {"goal": goal, "targets": targets}


def save_settings(d: dict) -> dict:
    if not isinstance(d, dict):
        return {"ok": False, "error": "settings must be an object"}
    cur = settings()
    if "goal" in d:
        if not valid_time(d["goal"]):
            return {"ok": False, "error": f"goal: expected HH:MM, got {d['goal']!r}"}
        cur["goal"] = d["goal"]
    for t, v in (d.get("targets") or {}).items():
        if t not in TASKS:
            return {"ok": False, "error": f"unknown task {t!r}"}
        if v not in ("", None) and not valid_time(v):
            return {"ok": False, "error": f"{t}: expected HH:MM, got {v!r}"}
        cur["targets"][t] = v or ""
    tmp = SETTINGS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(cur, indent=2) + "\n")
    tmp.replace(SETTINGS_FILE)
    notify("settings", cur)
    notify("today", api_today())
    return {"ok": True, **cur}


def button_map() -> dict:
    """buttons.json: {"<serial or name>": "<task>"} - re-read on every event so edits apply live."""
    try:
        m = json.loads(BUTTONS_FILE.read_text())
        return {str(k).strip().lower(): v for k, v in m.items() if v in TASKS}
    except (FileNotFoundError, ValueError):
        return {}


def resolve_task(serial: str, name: str):
    m = button_map()
    for key in (serial, name):
        if key and key.strip().lower() in m:
            return m[key.strip().lower()]
    n = (name or "").strip().lower()
    if n in NAME_ALIASES:
        return NAME_ALIASES[n]
    for alias, task in NAME_ALIASES.items():
        if alias in n:  # "Bouton réveil" -> wake
            return task
    return None


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY, day TEXT, task TEXT, action TEXT, ts TEXT)""")
    con.execute("CREATE INDEX IF NOT EXISTS events_day ON events(day)")
    con.execute("""CREATE TABLE IF NOT EXISTS buttons(
        serial TEXT PRIMARY KEY, name TEXT, last_seen TEXT, last_click TEXT, presses INTEGER DEFAULT 0)""")
    return con


def now():
    return datetime.now(TZ)


def record(task: str, action: str) -> dict:
    n = now()
    with db() as con:
        con.execute("INSERT INTO events(day, task, action, ts) VALUES (?,?,?,?)",
                    (n.date().isoformat(), task, action, n.isoformat()))
    notify("today", api_today())
    return {"ok": True, "day": n.date().isoformat(), "task": task, "action": action}


def hub_event(payload: dict) -> dict:
    serial = str(payload.get("serial") or "").strip()
    name = str(payload.get("name") or "").strip()
    click = str(payload.get("click") or "click").strip().lower()
    n = now()
    if not serial and not name:
        return {"ok": False, "reason": "no serial/name in payload"}
    with db() as con:
        con.execute("""INSERT INTO buttons(serial, name, last_seen, last_click, presses) VALUES (?,?,?,?,1)
            ON CONFLICT(serial) DO UPDATE SET name=excluded.name, last_seen=excluded.last_seen,
            last_click=excluded.last_click, presses=presses+1""", (serial or "?", name, n.isoformat(), click))
    task, action = resolve_task(serial, name), CLICK_ACTION.get(click)
    notify("buttons", {"serial": serial, "click": click})
    sys.stderr.write(f"hub-event: serial={serial!r} name={name!r} click={click!r} -> task={task} action={action}\n")
    if not task or not action:
        # 200 on purpose: the hub script would otherwise queue and retry this forever
        return {"ok": False, "reason": "unmapped button" if not task else "unknown click",
                "serial": serial, "name": name, "click": click,
                "hint": f"add {{\"{serial or name}\": \"<task>\"}} to {BUTTONS_FILE.name} or name the button after a task"}
    return {**record(task, action), "serial": serial, "name": name, "click": click}


def api_buttons() -> dict:
    with db() as con:
        seen = [dict(r) for r in con.execute("SELECT * FROM buttons ORDER BY rowid")]
    for b in seen:
        b["task"] = resolve_task(b["serial"], b["name"])
    return {"tasks": TASKS, "mapping_file": str(BUTTONS_FILE), "mapping": button_map(),
            "click_actions": CLICK_ACTION, "seen": seen}


def save_mapping(mapping: dict) -> dict:
    if not isinstance(mapping, dict):
        return {"ok": False, "error": "mapping must be an object"}
    clean, bad = {}, []
    for k, v in mapping.items():
        k, v = str(k).strip(), (str(v).strip() if v else "")
        if not k:
            continue
        if v and v not in TASKS:
            bad.append(k)
        elif v:
            clean[k] = v
    if bad:
        return {"ok": False, "error": f"unknown task for {bad}", "tasks": TASKS}
    out = {"_comment": "Flic button -> task. Keys: button serial. Values: " + " | ".join(TASKS)
                       + ". Edited from /admin; re-read on every press."}
    out.update(clean)
    tmp = BUTTONS_FILE.with_suffix(".tmp")
    tmp.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(BUTTONS_FILE)
    notify("buttons", {"mapping": clean})
    return {"ok": True, "mapping": clean}


def forget_button(serial: str) -> dict:
    with db() as con:
        con.execute("DELETE FROM buttons WHERE serial=?", (serial,))
    m = {k: v for k, v in button_map().items() if k != serial.strip().lower()}
    save_mapping(m)
    return {"ok": True}


# --- report ------------------------------------------------------------------------
def _min(t):  # "HH:MM" -> minutes since midnight
    return int(t[:2]) * 60 + int(t[3:]) if t else None


def _hhmm(m):
    return None if m is None else "%02d:%02d" % (divmod(int(round(m)), 60))


def _avg(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


def _rate(a, b):
    return round(100 * a / b) if b else None


def day_rows(con, start: date, end: date) -> dict:
    """{day: [(task, action, ts), ...]} for start..end in one query."""
    out = {}
    for r in con.execute("SELECT day, task, action, ts FROM events WHERE day BETWEEN ? AND ? ORDER BY id",
                         (start.isoformat(), end.isoformat())):
        out.setdefault(r["day"], []).append((r["task"], r["action"], r["ts"]))
    return out


def analyse_day(d: date, rows: list, goal: str, targets: dict) -> dict:
    st = {t: {"state": "todo", "time": None} for t in TASKS}
    undo = 0
    for task, action, ts in rows:
        if task not in st:
            continue
        if action == "undo":
            undo += 1
            st[task] = {"state": "todo", "time": None}
        else:
            st[task] = {"state": action, "time": datetime.fromisoformat(ts).strftime("%H:%M")}
    for t in TASKS:
        tg = targets.get(t) or ""
        st[t]["target"] = tg or None
        st[t]["late"] = bool(st[t]["state"] == "done" and tg and st[t]["time"] > tg)
    done = [t for t in TASKS if st[t]["state"] == "done"]
    times = [_min(st[t]["time"]) for t in done]
    complete = len(done) == len(TASKS)
    finished = max(times) if complete else None
    return {"day": d.isoformat(), "weekday": d.weekday(), "active": bool(rows), "tasks": st,
            "done": len(done), "skipped": sum(1 for t in TASKS if st[t]["state"] == "skip"),
            "complete": complete, "finished_at": _hhmm(finished),
            "on_time": bool(complete and finished <= _min(goal)),
            "first_at": _hhmm(min(times)) if times else None,
            "duration_min": (max(times) - min(times)) if complete and len(times) > 1 else None,
            "undo": undo}


def period_stats(days: list, goal: str, targets: dict) -> dict:
    active = [x for x in days if x["active"]]
    complete = [x for x in active if x["complete"]]
    on_time = [x for x in complete if x["on_time"]]
    fin = [_min(x["finished_at"]) for x in complete]
    # streaks over calendar days (a day without routine breaks the streak)
    best = cur = 0
    for x in days:
        cur = cur + 1 if x["complete"] else 0
        best = max(best, cur)
    per_task = {}
    for i, t in enumerate(TASKS):
        ts = [_min(x["tasks"][t]["time"]) for x in active if x["tasks"][t]["state"] == "done"]
        late = [x for x in active if x["tasks"][t]["late"]]
        tg = _min(targets.get(t) or "")
        gaps = []
        if i:
            prev = TASKS[i - 1]
            for x in active:
                a, b = x["tasks"][prev], x["tasks"][t]
                if a["state"] == "done" and b["state"] == "done":
                    gaps.append(_min(b["time"]) - _min(a["time"]))
        per_task[t] = {
            "target": targets.get(t) or None, "done": len(ts),
            "avg": _hhmm(_avg(ts)), "median": _hhmm(_median(ts)),
            "earliest": _hhmm(min(ts)) if ts else None, "latest": _hhmm(max(ts)) if ts else None,
            "late": len(late), "on_target_rate": _rate(len(ts) - len(late), len(ts)) if tg is not None else None,
            "avg_delay_when_late": round(_avg([_min(x["tasks"][t]["time"]) - tg for x in late]) or 0) if late else None,
            "skipped": sum(1 for x in active if x["tasks"][t]["state"] == "skip"),
            "missed": sum(1 for x in active if x["tasks"][t]["state"] == "todo"),
            "avg_gap_min": round(_avg(gaps)) if gaps else None,
        }
    weekdays = []
    for wd in range(7):
        xs = [x for x in active if x["weekday"] == wd]
        cs = [x for x in xs if x["complete"]]
        weekdays.append({"weekday": wd, "active": len(xs), "complete": len(cs),
                         "on_time": sum(1 for x in cs if x["on_time"]),
                         "completion_rate": _rate(len(cs), len(xs)),
                         "on_time_rate": _rate(sum(1 for x in cs if x["on_time"]), len(xs)),
                         "avg_finish": _hhmm(_avg([_min(x["finished_at"]) for x in cs]))})
    school_days = [x for x in days if x["weekday"] < 5]
    return {
        "days_total": len(days), "active_days": len(active), "complete_days": len(complete),
        "on_time_days": len(on_time), "incomplete_days": len(active) - len(complete),
        "missed_weekdays": sum(1 for x in school_days if not x["active"]),
        "completion_rate": _rate(len(complete), len(active)),
        "on_time_rate": _rate(len(on_time), len(active)),
        "avg_finish": _hhmm(_avg(fin)), "median_finish": _hhmm(_median(fin)),
        "best_finish": min(((x["finished_at"], x["day"]) for x in complete), default=(None, None)),
        "worst_finish": max(((x["finished_at"], x["day"]) for x in complete), default=(None, None)),
        "avg_start": _hhmm(_avg([_min(x["first_at"]) for x in active if x["first_at"]])),
        "avg_duration_min": round(_avg([x["duration_min"] for x in complete]) or 0) if complete else None,
        "avg_margin_min": round(_min(goal) - _avg(fin)) if fin else None,  # + = before the flag
        "undo_total": sum(x["undo"] for x in active), "skipped_total": sum(x["skipped"] for x in active),
        "best_streak": best, "per_task": per_task, "weekdays": weekdays,
    }


def api_report(days_back: int = 56) -> dict:
    cfg = settings()
    goal, targets = cfg["goal"], cfg["targets"]
    days_back = max(7, min(730, days_back))
    today_ = now().date()
    start = today_ - timedelta(days=days_back - 1)
    prev_start = start - timedelta(days=days_back)
    with db() as con:
        rows = day_rows(con, prev_start, today_)
        first = con.execute("SELECT MIN(day) AS d, COUNT(*) AS n FROM events").fetchone()
        # current streak needs to look past the window
        streak, d = 0, today_
        if not summarize(day_status(con, d), goal)["complete"]:
            d -= timedelta(days=1)
        while summarize(day_status(con, d), goal)["complete"]:
            streak += 1
            d -= timedelta(days=1)
    cur = [analyse_day(start + timedelta(days=i), rows.get((start + timedelta(days=i)).isoformat(), []), goal, targets)
           for i in range(days_back)]
    prev = [analyse_day(prev_start + timedelta(days=i), rows.get((prev_start + timedelta(days=i)).isoformat(), []), goal, targets)
            for i in range(days_back)]
    weeks = {}
    for x in cur:
        d = date.fromisoformat(x["day"])
        monday = (d - timedelta(days=d.weekday())).isoformat()
        w = weeks.setdefault(monday, {"week_of": monday, "active": 0, "complete": 0, "on_time": 0, "fin": [], "days": 0})
        w["days"] += 1
        if x["active"]:
            w["active"] += 1
        if x["complete"]:
            w["complete"] += 1
            w["fin"].append(_min(x["finished_at"]))
        if x["on_time"]:
            w["on_time"] += 1
    week_list = []
    for w in weeks.values():
        week_list.append({**{k: v for k, v in w.items() if k != "fin"}, "avg_finish": _hhmm(_avg(w["fin"])),
                          "perfect": w["active"] >= 4 and w["on_time"] == w["active"]})
    stats = period_stats(cur, goal, targets)
    stats["current_streak"] = streak
    return {"from": start.isoformat(), "to": today_.isoformat(), "days_back": days_back,
            "goal": goal, "targets": targets, "tasks": TASKS,
            "tracking_since": first["d"], "events_total": first["n"],
            "kpis": stats, "previous": period_stats(prev, goal, targets),
            "weeks": week_list, "days": cur}


def report_csv(days_back: int = 56) -> str:
    import csv
    import io
    r = api_report(days_back)
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(["day", "weekday", "active", "complete", "on_time", "first_at", "finished_at", "duration_min", "undo", "skipped"]
               + [f"{t}_time" for t in TASKS] + [f"{t}_state" for t in TASKS])
    for x in r["days"]:
        w.writerow([x["day"], x["weekday"], int(x["active"]), int(x["complete"]), int(x["on_time"]), x["first_at"] or "",
                    x["finished_at"] or "", x["duration_min"] if x["duration_min"] is not None else "", x["undo"], x["skipped"]]
                   + [x["tasks"][t]["time"] or "" for t in TASKS] + [x["tasks"][t]["state"] for t in TASKS])
    return out.getvalue()


def day_status(con, d: date) -> dict:
    """Last action wins per task -> {task: {"state": done|skip|todo, "time": HH:MM|None}}"""
    rows = con.execute("SELECT task, action, ts FROM events WHERE day=? ORDER BY id",
                       (d.isoformat(),)).fetchall()
    st = {t: {"state": "todo", "time": None} for t in TASKS}
    for r in rows:
        if r["task"] not in st:
            continue
        if r["action"] == "undo":
            st[r["task"]] = {"state": "todo", "time": None}
        else:
            st[r["task"]] = {"state": r["action"],
                             "time": datetime.fromisoformat(r["ts"]).strftime("%H:%M")}
    return st


def summarize(st: dict, goal: str = None) -> dict:
    goal = goal or settings()["goal"]
    done = [t for t in TASKS if st[t]["state"] == "done"]
    times = [st[t]["time"] for t in TASKS if st[t]["state"] == "done"]
    finished = max(times) if len(done) == len(TASKS) else None
    return {"tasks": st, "done": len(done), "total": len(TASKS),
            "complete": len(done) == len(TASKS), "finished_at": finished,
            "on_time": bool(finished and finished <= goal)}


def api_today() -> dict:
    cfg = settings()
    with db() as con:
        d = now().date()
        return {"day": d.isoformat(), "goal": cfg["goal"], "targets": cfg["targets"],
                "now": now().strftime("%H:%M"), **summarize(day_status(con, d), cfg["goal"])}


def api_week(offset: int = 0) -> dict:
    goal = settings()["goal"]
    with db() as con:
        today_ = now().date()
        monday = today_ - timedelta(days=today_.weekday()) + timedelta(weeks=offset)
        days = []
        for i in range(7):
            d = monday + timedelta(days=i)
            days.append({"day": d.isoformat(), "weekday": d.weekday(),
                         "today": d == today_, "future": d > today_,
                         **summarize(day_status(con, d), goal)})
        # streak: consecutive complete days ending today (or yesterday if today isn't done yet)
        streak, d = 0, today_
        if not summarize(day_status(con, d), goal)["complete"]:
            d -= timedelta(days=1)
        while summarize(day_status(con, d), goal)["complete"]:
            streak += 1
            d -= timedelta(days=1)
        return {"week_of": monday.isoformat(), "goal": goal, "days": days, "streak": streak}


class Handler(BaseHTTPRequestHandler):
    server_version = "gmr/1.0"

    def log_message(self, fmt, *args):  # quieter logs: only non-GET or errors
        if self.command != "GET" or (args and str(args[1]).startswith(("4", "5"))):
            sys.stderr.write("%s - %s\n" % (self.address_string(), fmt % args))

    def send_json(self, obj, status=200):
        body = json.dumps(obj).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path):
        try:
            data = path.read_bytes()
        except (FileNotFoundError, IsADirectoryError):
            return self.send_json({"error": "not found"}, 404)
        ctype = mimetypes.guess_type(str(path))[0] or "application/octet-stream"
        if ctype.startswith("text/"):
            ctype += "; charset=utf-8"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(data)

    def stream(self):
        q = queue.Queue(maxsize=64)
        with _subs_lock:
            _subs.add(q)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()
            self.wfile.write(("retry: 2000\nevent: today\ndata: " + json.dumps(api_today()) + "\n\n").encode())
            self.wfile.flush()
            while True:
                try:
                    kind, data = q.get(timeout=20)
                    self.wfile.write(f"event: {kind}\ndata: {data}\n\n".encode())
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")  # keep-alive, also detects dead clients
                self.wfile.flush()
        except (BrokenPipeError, ConnectionResetError, OSError):
            pass
        finally:
            with _subs_lock:
                _subs.discard(q)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/api/stream":
            return self.stream()
        if u.path in ("/", "/index.html"):
            return self.send_file(STATIC / "index.html")
        if u.path == "/admin":
            return self.send_file(STATIC / "admin.html")
        if u.path == "/report":
            return self.send_file(STATIC / "report.html")
        if u.path in ("/api/report", "/api/report.csv"):
            try:
                n = int(parse_qs(u.query).get("days", ["56"])[0])
            except ValueError:
                n = 56
            if u.path.endswith(".csv"):
                body = report_csv(n).encode("utf-8-sig")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", f'attachment; filename="gmr-{n}j.csv"')
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                return self.wfile.write(body)
            return self.send_json(api_report(n))
        if u.path == "/api/today":
            return self.send_json(api_today())
        if u.path == "/api/week":
            try:
                offset = int(parse_qs(u.query).get("offset", ["0"])[0])
            except ValueError:
                offset = 0
            return self.send_json(api_week(offset))
        if u.path == "/health":
            return self.send_json({"ok": True})
        if u.path == "/api/buttons":
            return self.send_json(api_buttons())
        if u.path == "/api/settings":
            return self.send_json(settings())
        if u.path.startswith("/static/"):
            target = (STATIC / u.path[len("/static/"):]).resolve()
            if STATIC.resolve() not in target.parents:
                return self.send_json({"error": "forbidden"}, 403)
            return self.send_file(target)
        self.send_json({"error": "not found"}, 404)

    def read_json(self):
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length else b""
        try:
            body = json.loads(raw) if raw.strip() else {}
            return body if isinstance(body, dict) else {}
        except ValueError:
            return {}

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/hub-event":
            return self.send_json(hub_event(self.read_json()))
        if u.path == "/api/buttons":
            r = save_mapping(self.read_json().get("mapping"))
            return self.send_json(r, 200 if r["ok"] else 400)
        if u.path == "/api/settings":
            r = save_settings(self.read_json())
            return self.send_json(r, 200 if r["ok"] else 400)
        if u.path == "/api/buttons/forget":
            serial = str(self.read_json().get("serial") or "").strip()
            return self.send_json(forget_button(serial) if serial else {"ok": False}, 200 if serial else 400)
        if u.path != "/event":
            return self.send_json({"error": "not found"}, 404)
        body = self.read_json()
        task, action = body.get("task"), body.get("action", "done")
        # Also accept ?task=wake&action=done for hubs that only do simple requests
        qs = parse_qs(u.query)
        task = task or qs.get("task", [None])[0]
        action = action or qs.get("action", ["done"])[0]
        if task not in TASKS or action not in ACTIONS:
            return self.send_json({"error": "unknown task or action",
                                   "tasks": TASKS, "actions": list(ACTIONS)}, 400)
        self.send_json(record(task, action))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


def main():
    db().close()  # create schema up front so errors show at startup
    srv = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    srv.daemon_threads = True
    print(f"gmr: serving on http://0.0.0.0:{PORT}  db={DB}  tz={TZ.key}  goal={GOAL_TIME}", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
