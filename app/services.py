"""Business logic: goals, contributions, streaks, quests, XP and levels. XP/streaks are derived from saved rows."""
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation

QUESTS = [  # id, title, description, reward XP, target count
    ("first_step", "First Step", "Record your first saving contribution.", 50, 1),
    ("seven_day", "Seven-Day Saver", "Record savings on seven separate days.", 100, 7),
    ("budget_explorer", "Budget Explorer", "Review your spending plan.", 30, 1),
    ("goal_getter", "Goal Getter", "Reach 25% of a savings target.", 75, 25),
    ("consistency", "Consistency Champion", "Save on three consecutive days.", 100, 3),
]
DAILY_XP = 10
DAILY_CHALLENGES = [
    "Identify one unnecessary expense you could skip this week.",
    "Set aside R10 toward a goal, if it's comfortable for you.",
    "Review your savings goal for two minutes.",
    "Plan tomorrow's spending before the day starts.",
    "Check one subscription or recurring cost: is it still worth it?",
    "Write down what your top goal will let you do when you reach it.",
    "Compare prices on one thing you plan to buy this week.",
]
LEVEL_TABLE = [0, 100, 250, 500, 800]


class ValidationError(ValueError):
    pass


def parse_amount(raw) -> int:
    """Parse rand text into cents. Rejects empty, malformed, zero, negative and non-finite values."""
    try:
        d = Decimal(str(raw).strip().replace(",", ".").replace("R", "").replace(" ", ""))
    except (InvalidOperation, AttributeError):
        raise ValidationError("Enter a valid amount, like 150 or 49.99.")
    if not d.is_finite():
        raise ValidationError("Enter a valid amount, like 150 or 49.99.")
    if d <= 0:
        raise ValidationError("Amount must be greater than R0.")
    if d.as_tuple().exponent < -2:
        raise ValidationError("Use at most two decimal places.")
    return int(d * 100)


def rand(cents: int) -> str:
    return f"R{cents / 100:,.2f}".replace(",", " ")


def _today(today): return today or date.today()


# ---------- goals ----------
def create_goal(conn, name, target_raw, target_date=None, today=None) -> int:
    name = (name or "").strip()
    if not name:
        raise ValidationError("Give your goal a name.")
    cents = parse_amount(target_raw)
    if target_date:
        try:
            date.fromisoformat(target_date)
        except ValueError:
            raise ValidationError("Use the date format YYYY-MM-DD, or leave it blank.")
    cur = conn.execute("INSERT INTO goals(name,target_cents,target_date,created) VALUES(?,?,?,?)",
                       (name, cents, target_date or None, _today(today).isoformat()))
    conn.commit()
    return cur.lastrowid


def update_goal(conn, goal_id, name, target_raw):
    name = (name or "").strip()
    if not name:
        raise ValidationError("Give your goal a name.")
    conn.execute("UPDATE goals SET name=?, target_cents=? WHERE id=?", (name, parse_amount(target_raw), goal_id))
    conn.commit()
    sync_quests(conn)


def delete_goal(conn, goal_id):
    conn.execute("DELETE FROM goals WHERE id=?", (goal_id,))
    conn.commit()
    sync_quests(conn)


def goal_progress(conn, goal_id) -> dict:
    g = conn.execute("SELECT * FROM goals WHERE id=?", (goal_id,)).fetchone()
    saved = conn.execute("SELECT COALESCE(SUM(amount_cents),0) FROM contributions WHERE goal_id=?", (goal_id,)).fetchone()[0]
    return {"id": g["id"], "name": g["name"], "target": g["target_cents"], "saved": saved,
            "remaining": max(g["target_cents"] - saved, 0), "pct": min(saved / g["target_cents"] * 100, 100.0),
            "achieved": saved >= g["target_cents"], "target_date": g["target_date"]}


def list_goals(conn) -> list[dict]:
    return [goal_progress(conn, r["id"]) for r in conn.execute("SELECT id FROM goals ORDER BY id")]


# ---------- contributions ----------
def record_contribution(conn, goal_id, amount_raw, note="", allow_over=False, today=None) -> int:
    cents = parse_amount(amount_raw)
    p = goal_progress(conn, goal_id)
    if cents > p["remaining"] and not allow_over:
        raise ValidationError(f"That's more than the {rand(p['remaining'])} left on this goal. Tick 'allow extra' to save it anyway.")
    cur = conn.execute("INSERT INTO contributions(goal_id,amount_cents,note,day) VALUES(?,?,?,?)",
                       (goal_id, cents, (note or "").strip()[:80], _today(today).isoformat()))
    conn.commit()
    sync_quests(conn, today)
    return cur.lastrowid


def delete_contribution(conn, contribution_id, today=None):
    conn.execute("DELETE FROM contributions WHERE id=?", (contribution_id,))
    conn.commit()
    sync_quests(conn, today)


def history(conn) -> list[dict]:
    rows = conn.execute("""SELECT c.id, c.day, g.name goal, c.amount_cents, c.note FROM contributions c
                           JOIN goals g ON g.id=c.goal_id ORDER BY c.day DESC, c.id DESC""").fetchall()
    return [dict(r) for r in rows]


def total_saved(conn) -> int:
    return conn.execute("SELECT COALESCE(SUM(amount_cents),0) FROM contributions").fetchone()[0]


# ---------- streaks ----------
def _days(conn) -> list[date]:
    return sorted({date.fromisoformat(r[0]) for r in conn.execute("SELECT DISTINCT day FROM contributions")})


def best_streak(conn) -> int:
    best = run = 0
    prev = None
    for d in _days(conn):
        run = run + 1 if prev and d - prev == timedelta(days=1) else 1
        best, prev = max(best, run), d
    return best


def current_streak(conn, today=None) -> int:
    days, t = set(_days(conn)), _today(today)
    d = t if t in days else t - timedelta(days=1)  # a streak stays alive until a full day is missed
    n = 0
    while d in days:
        n, d = n + 1, d - timedelta(days=1)
    return n


# ---------- quests, XP, levels ----------
def quest_progress(conn) -> dict:
    goals = list_goals(conn)
    return {"first_step": min(conn.execute("SELECT COUNT(*) FROM contributions").fetchone()[0], 1),
            "seven_day": min(len(_days(conn)), 7),
            "budget_explorer": 1 if conn.execute("SELECT 1 FROM meta WHERE key='budget_reviewed'").fetchone() else 0,
            "goal_getter": int(min(max([g["pct"] for g in goals], default=0), 25)),
            "consistency": min(best_streak(conn), 3)}


def sync_quests(conn, today=None):
    """Award each completed quest once; revoke awards whose requirement no longer holds (e.g. after a deletion)."""
    prog = quest_progress(conn)
    claimed = {r[0] for r in conn.execute("SELECT quest_id FROM quest_claims")}
    for qid, _t, _d, _xp, target in QUESTS:
        done = prog[qid] >= target
        if done and qid not in claimed:
            conn.execute("INSERT OR IGNORE INTO quest_claims VALUES(?,?)", (qid, _today(today).isoformat()))
        elif not done and qid in claimed:
            conn.execute("DELETE FROM quest_claims WHERE quest_id=?", (qid,))
    conn.commit()


def mark_budget_reviewed(conn, today=None):
    conn.execute("INSERT OR IGNORE INTO meta VALUES('budget_reviewed','1')")
    conn.commit()
    sync_quests(conn, today)


def quests(conn) -> list[dict]:
    prog, claimed = quest_progress(conn), {r[0] for r in conn.execute("SELECT quest_id FROM quest_claims")}
    return [{"id": q, "title": t, "desc": d, "xp": xp, "target": tg, "progress": prog[q], "done": q in claimed}
            for q, t, d, xp, tg in QUESTS]


def daily_challenge(today=None) -> str:
    return DAILY_CHALLENGES[_today(today).toordinal() % len(DAILY_CHALLENGES)]


def daily_done(conn, today=None) -> bool:
    return conn.execute("SELECT 1 FROM daily_claims WHERE day=?", (_today(today).isoformat(),)).fetchone() is not None


def complete_daily(conn, today=None) -> bool:
    """Returns True only the first time on a given day."""
    cur = conn.execute("INSERT OR IGNORE INTO daily_claims VALUES(?)", (_today(today).isoformat(),))
    conn.commit()
    return cur.rowcount == 1


def total_xp(conn) -> int:
    q = {t[0]: t[3] for t in QUESTS}
    xp = sum(q[r[0]] for r in conn.execute("SELECT quest_id FROM quest_claims"))
    return xp + DAILY_XP * conn.execute("SELECT COUNT(*) FROM daily_claims").fetchone()[0]


def level_start(level: int) -> int:
    """Levels 1-5 use LEVEL_TABLE; after that each level needs 300 + 50*(level-5) more XP than the last."""
    if level <= len(LEVEL_TABLE):
        return LEVEL_TABLE[level - 1]
    xp = LEVEL_TABLE[-1]
    for lv in range(len(LEVEL_TABLE) + 1, level + 1):
        xp += 300 + 50 * (lv - len(LEVEL_TABLE))
    return xp


def level_info(xp: int) -> dict:
    lv = 1
    while level_start(lv + 1) <= xp:
        lv += 1
    lo, hi = level_start(lv), level_start(lv + 1)
    return {"level": lv, "xp": xp, "next_at": hi, "to_next": hi - xp, "pct": (xp - lo) / (hi - lo) * 100}


# ---------- profile ----------
def get_profile(conn) -> dict:
    return dict(conn.execute("SELECT name, avatar FROM profile WHERE id=1").fetchone())


def save_profile(conn, name, avatar):
    name = (name or "").strip()[:30] or "Saver"
    conn.execute("UPDATE profile SET name=?, avatar=? WHERE id=1", (name, avatar))
    conn.commit()
