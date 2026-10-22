import flet as ft
from app import database as db, services as s, theme as t, views as v


class FakeApp:
    def __init__(self, conn): self.conn = conn
    def __getattr__(self, n): return lambda *a, **k: None


def texts(ctrl, out):
    if isinstance(ctrl, ft.Text): out.append(ctrl.value or "")
    for attr in ("content", "controls"):
        sub = getattr(ctrl, attr, None)
        for x in (sub if isinstance(sub, list) else [sub] if sub is not None else []):
            texts(x, out)
    return out


def test_every_page_builds_with_footer_and_data(tmp_path):
    conn = db.connect(str(tmp_path / "v.db"))
    for populated in (False, True):
        if populated:
            g = s.create_goal(conn, "Laptop", "1000"); s.record_contribution(conn, g, "300", "x")
        for name in v.PAGES:
            assert t.FOOTER in texts(v.build_page(name, FakeApp(conn)), []), name
