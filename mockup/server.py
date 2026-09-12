"""Morning routine tracker — Flic Hub webhooks -> SQLite -> kid-friendly web app.

Run:  pip install fastapi uvicorn && uvicorn server:app --host 0.0.0.0 --port 8000
Flic Hub "Internet Request" action per button:
  POST http://<pi>:8000/event   body: {"task":"wake","action":"done"}
  (double-click -> action "undo"; hold -> action "skip")
"""
import sqlite3
from datetime import datetime, date, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

TZ = ZoneInfo("Europe/Zurich")
DB = Path(__file__).parent / "morning.db"
TASKS = ["wake", "clothes", "breakfast", "teeth"]  # order of the routine
GOAL_TIME = "07:30"  # "all done before" target shown on the page

app = FastAPI(title="Morning routine")


def db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS events(
        id INTEGER PRIMARY KEY, day TEXT, task TEXT, action TEXT, ts TEXT)""")
    return con


class Event(BaseModel):
    task: str
    action: str = "done"  # done | undo | skip


@app.post("/event")
def post_event(ev: Event):
    if ev.task not in TASKS or ev.action not in ("done", "undo", "skip"):
        raise HTTPException(400, "unknown task or action")
    now = datetime.now(TZ)
    with db() as con:
        con.execute("INSERT INTO events(day, task, action, ts) VALUES (?,?,?,?)",
                    (now.date().isoformat(), ev.task, ev.action, now.isoformat()))
    return {"ok": True, "day": now.date().isoformat(), "task": ev.task, "action": ev.action}


def day_status(con, d: date) -> dict:
    """Last action wins per task. Returns {task: {"state": done|skip|todo, "time": HH:MM|None}}"""
    rows = con.execute("SELECT task, action, ts FROM events WHERE day=? ORDER BY id",
                       (d.isoformat(),)).fetchall()
    st = {t: {"state": "todo", "time": None} for t in TASKS}
    for r in rows:
        if r["action"] == "undo":
            st[r["task"]] = {"state": "todo", "time": None}
        else:
            st[r["task"]] = {"state": r["action"],
                             "time": datetime.fromisoformat(r["ts"]).strftime("%H:%M")}
    return st


def summarize(st: dict) -> dict:
    done = [t for t in TASKS if st[t]["state"] == "done"]
    times = [st[t]["time"] for t in TASKS if st[t]["time"]]
    finished = max(times) if len(done) == len(TASKS) else None
    return {"tasks": st, "done": len(done), "total": len(TASKS),
            "complete": len(done) == len(TASKS), "finished_at": finished,
            "on_time": bool(finished and finished <= GOAL_TIME)}


@app.get("/api/today")
def today():
    with db() as con:
        d = datetime.now(TZ).date()
        return {"day": d.isoformat(), "goal": GOAL_TIME, **summarize(day_status(con, d))}


@app.get("/api/week")
def week(offset: int = 0):
    """Mon..Sun of current week (offset=-1 for last week). Includes streak."""
    with db() as con:
        today_ = datetime.now(TZ).date()
        monday = today_ - timedelta(days=today_.weekday()) + timedelta(weeks=offset)
        days = []
        for i in range(7):
            d = monday + timedelta(days=i)
            days.append({"day": d.isoformat(), "weekday": d.strftime("%a"),
                         "future": d > today_, **summarize(day_status(con, d))})
        # streak: consecutive complete days ending today (or yesterday if today not done)
        streak, d = 0, today_
        if not summarize(day_status(con, d))["complete"]:
            d -= timedelta(days=1)
        while summarize(day_status(con, d))["complete"]:
            streak += 1
            d -= timedelta(days=1)
        return {"week_of": monday.isoformat(), "goal": GOAL_TIME, "days": days, "streak": streak}


@app.get("/")
def index():
    return FileResponse(Path(__file__).parent / "static" / "index.html")


app.mount("/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static")
