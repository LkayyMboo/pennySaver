# PennyQuest
*Small steps. Smart money. Big wins.* A gamified savings tracker for South African students (Python + Flet + SQLite). Local demo: no logins, no bank data, no real money. XP is a game reward only.

## Run
    python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
    pip install -r requirements.txt
    python main.py                # desktop window
    flet run --web main.py        # browser

## Test
    python -m pytest -q

## Data
SQLite file at `~/.pennyquest/pennyquest.db`, or wherever `PENNYQUEST_DB` points. Never commit it (see .gitignore).

## Deploy
Any host that runs Python and injects `PORT` works: `python main.py` serves the web app on `0.0.0.0:$PORT`.
Set `PENNYQUEST_DB` to a path on a persistent disk/volume (e.g. `/data/pennyquest.db`); on an ephemeral filesystem, data is lost on restart.
Start command: `python main.py`; build command: `pip install -r requirements.txt`.

## Screenshot checklist
Dashboard (with goal and streak) · New goal dialog · Record savings dialog · My Goals · Quests (one complete) · Saving History · Achievements · Profile · Test run output · Mobile-width view
