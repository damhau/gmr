#!/usr/bin/env python3
"""Fill a database with realistic fake mornings, to try /report before real data exists.

    GMR_DB=/tmp/demo.db python3 seed_demo.py --weeks 10
    GMR_DB=/tmp/demo.db python3 server.py           # then open /report

Never run it against the real morning.db (it refuses unless --force)."""
import argparse
import os
import random
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve().parent
TZ = ZoneInfo(os.environ.get("GMR_TZ", "Europe/Zurich"))
TASKS = ["wake", "clothes", "breakfast", "teeth"]

ap = argparse.ArgumentParser()
ap.add_argument("--weeks", type=int, default=10)
ap.add_argument("--seed", type=int, default=7)
ap.add_argument("--force", action="store_true")
a = ap.parse_args()

db = Path(os.environ.get("GMR_DB", HERE / "morning.db"))
if db.name == "morning.db" and not a.force:
    raise SystemExit("refusing to seed the real morning.db (set GMR_DB=... or pass --force)")
random.seed(a.seed)
con = sqlite3.connect(db)
con.execute("CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, day TEXT, task TEXT, action TEXT, ts TEXT)")
con.execute("DELETE FROM events")

today = datetime.now(TZ).date()
start = today - timedelta(weeks=a.weeks)
d = start
skill = 0.0  # slowly improves over time
while d <= today:
    skill = min(1.0, (d - start).days / max(1, (today - start).days))
    weekend = d.weekday() >= 5
    if weekend and random.random() < 0.7:            # most weekends: no routine
        d += timedelta(days=1); continue
    if not weekend and random.random() < 0.06:       # sick day / holiday
        d += timedelta(days=1); continue
    # wake between 6:35 and 7:05, earlier as skill grows
    t = 6 * 60 + 35 + random.gauss(14 - 8 * skill, 8)
    t = max(6 * 60 + 25, t)
    # bad day: everything slow
    slow = random.random() < (0.25 - 0.15 * skill)
    gaps = {"clothes": (14, 5), "breakfast": (12, 4), "teeth": (9, 4)}
    n_done = 4 if random.random() > (0.08 - 0.05 * skill) else random.choice([2, 3])
    for i, task in enumerate(TASKS):
        if i >= n_done:
            break
        if i:
            mu, sd = gaps[task]
            t += max(2, random.gauss(mu * (1.6 if slow else 1), sd))
        ts = datetime.combine(d, time(int(t // 60), int(t % 60), random.randint(0, 59)), TZ)
        # occasional mistaken press followed by an undo
        if random.random() < 0.05:
            con.execute("INSERT INTO events(day,task,action,ts) VALUES(?,?,?,?)",
                        (d.isoformat(), TASKS[min(3, i + 1)], "done", ts.isoformat()))
            con.execute("INSERT INTO events(day,task,action,ts) VALUES(?,?,?,?)",
                        (d.isoformat(), TASKS[min(3, i + 1)], "undo", (ts + timedelta(seconds=20)).isoformat()))
        con.execute("INSERT INTO events(day,task,action,ts) VALUES(?,?,?,?)", (d.isoformat(), task, "done", ts.isoformat()))
    if n_done < 4 and random.random() < 0.3:          # sometimes a step is explicitly skipped
        ts = datetime.combine(d, time(int(t // 60), int(t % 60)), TZ)
        con.execute("INSERT INTO events(day,task,action,ts) VALUES(?,?,?,?)", (d.isoformat(), TASKS[n_done], "skip", ts.isoformat()))
    d += timedelta(days=1)
con.commit()
n = con.execute("SELECT COUNT(*), MIN(day), MAX(day) FROM events").fetchone()
print(f"seeded {n[0]} events from {n[1]} to {n[2]} into {db}")
