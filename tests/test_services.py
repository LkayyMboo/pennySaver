import pytest
from datetime import date, timedelta
from app import database as db, services as s

D = date(2026, 10, 21)

@pytest.fixture
def conn(tmp_path):
    return db.connect(str(tmp_path / "t.db"))

def test_db_initialises(conn):
    names = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"goals", "contributions", "quest_claims", "daily_claims", "profile"} <= names

def test_goal_and_contribution(conn):
    g = s.create_goal(conn, "Laptop", "1000", today=D)
    s.record_contribution(conn, g, "250.50", "payday", today=D)
    p = s.goal_progress(conn, g)
    assert (p["saved"], p["remaining"], round(p["pct"], 2)) == (25050, 74950, 25.05)

@pytest.mark.parametrize("bad", ["-5", "0", "abc", "", "nan", "inf", "1.234"])
def test_bad_amounts_rejected(conn, bad):
    g = s.create_goal(conn, "G", "100", today=D)
    with pytest.raises(s.ValidationError):
        s.record_contribution(conn, g, bad, today=D)

def test_over_contribution_needs_opt_in(conn):
    g = s.create_goal(conn, "G", "100", today=D)
    with pytest.raises(s.ValidationError):
        s.record_contribution(conn, g, "150", today=D)
    s.record_contribution(conn, g, "150", allow_over=True, today=D)
    assert s.goal_progress(conn, g)["achieved"]

def test_xp_levels():
    assert s.level_info(0)["level"] == 1 and s.level_info(99)["level"] == 1
    assert s.level_info(100)["level"] == 2 and s.level_info(249)["level"] == 2
    assert s.level_info(250)["level"] == 3 and s.level_info(500)["level"] == 4
    assert s.level_info(800)["level"] == 5 and s.level_info(800)["to_next"] == 350

def test_quest_xp_awarded_once(conn):
    g = s.create_goal(conn, "G", "1000", today=D)
    s.record_contribution(conn, g, "300", today=D)      # first step + goal getter
    s.record_contribution(conn, g, "10", today=D)
    assert s.total_xp(conn) == 50 + 75
    s.sync_quests(conn, D); s.sync_quests(conn, D)
    assert s.total_xp(conn) == 125

def test_streaks_and_consistency_quest(conn):
    g = s.create_goal(conn, "G", "1000", today=D)
    for i in (2, 1, 0):
        s.record_contribution(conn, g, "5", today=D - timedelta(days=i))
    assert s.current_streak(conn, D) == 3 and s.best_streak(conn) == 3
    assert any(q["id"] == "consistency" and q["done"] for q in s.quests(conn))

def test_deleting_contribution_keeps_xp_consistent(conn):
    g = s.create_goal(conn, "G", "1000", today=D)
    c = s.record_contribution(conn, g, "5", today=D)
    assert s.total_xp(conn) == 50
    s.delete_contribution(conn, c, D)
    assert s.total_xp(conn) == 0 and s.total_saved(conn) == 0

def test_daily_challenge_once_and_deterministic(conn):
    assert s.daily_challenge(D) == s.daily_challenge(D)
    assert s.complete_daily(conn, D) is True and s.complete_daily(conn, D) is False
    assert s.total_xp(conn) == s.DAILY_XP
    assert s.complete_daily(conn, D + timedelta(days=1)) is True

def test_persistence_after_restart(tmp_path):
    path = str(tmp_path / "p.db")
    c1 = db.connect(path); g = s.create_goal(c1, "Trip", "500", today=D)
    s.record_contribution(c1, g, "50", today=D); s.save_profile(c1, "Thandi", "🦁"); c1.close()
    c2 = db.connect(path)
    assert s.total_saved(c2) == 5000 and s.get_profile(c2)["name"] == "Thandi"
