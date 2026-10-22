import flet as ft
from . import services as s, theme as t

PAGES = ["Dashboard", "My Goals", "Quests", "Saving History", "Achievements", "Profile"]
ICONS = [ft.Icons.HOME, ft.Icons.FLAG, ft.Icons.EMOJI_EVENTS, ft.Icons.RECEIPT_LONG, ft.Icons.MILITARY_TECH, ft.Icons.PERSON]


def footer():
    return ft.Container(txt_footer(), padding=ft.Padding.only(top=24, bottom=16), alignment=ft.Alignment.CENTER)


def txt_footer():
    return t.txt(t.FOOTER, size=12, color=t.MUTED, text_align=ft.TextAlign.CENTER)


def empty(msg):
    return t.card(t.txt(msg, color=t.MUTED))


def header(title, sub=None):
    return ft.Column([t.txt(title, 26, bold=True)] + ([t.txt(sub, 13, t.MUTED)] if sub else []), spacing=2)


def goal_card(p, app):
    status = "🎉 Goal achieved!" if p["achieved"] else f"{s.rand(p['remaining'])} to go"
    due = f" · by {p['target_date']}" if p["target_date"] else ""
    return t.card(ft.Column([
        ft.Row([t.txt(p["name"], 17, bold=True, expand=True), t.txt(f"{p['pct']:.0f}%", 15, t.EMERALD, True)]),
        t.bar(p["pct"]),
        t.txt(f"{s.rand(p['saved'])} of {s.rand(p['target'])} · {status}{due}", 13, t.MUTED),
        ft.Row([ft.Button("Save", icon=ft.Icons.ADD, on_click=lambda e: app.save_dialog(p["id"])),
                ft.TextButton("Edit", on_click=lambda e: app.goal_dialog(p)),
                ft.TextButton("Delete", on_click=lambda e: app.confirm(f"Delete '{p['name']}' and its saving history?",
                                                                       lambda: s.delete_goal(app.conn, p["id"])))], wrap=True)],
        spacing=8))


def quest_card(q):
    return t.card(ft.Column([
        ft.Row([t.txt(("✅ " if q["done"] else "🎯 ") + q["title"], 16, bold=True, expand=True),
                t.txt(f"+{q['xp']} XP", 14, t.VIOLET, True)]),
        t.txt(q["desc"], 13, t.MUTED),
        t.bar(q["progress"] / q["target"] * 100, t.VIOLET),
        t.txt("Completed" if q["done"] else f"{q['progress']}/{q['target']}" + ("%" if q["id"] == "goal_getter" else ""), 12, t.MUTED)],
        spacing=6))


def build_page(name, app):
    c = app.conn
    lv, goals = s.level_info(s.total_xp(c)), s.list_goals(c)
    body = []
    if name == "Dashboard":
        prof = s.get_profile(c)
        tot_t, tot_s = sum(g["target"] for g in goals), sum(g["saved"] for g in goals)
        daily_done = s.daily_done(c)
        body = [header(f"Hi {prof['name']} {prof['avatar']}", t.TAGLINE),
                ft.Button("Record savings", icon=ft.Icons.SAVINGS, on_click=lambda e: app.save_dialog(None)),
                t.card(ft.Column([t.txt("Total savings recorded", 13, t.MUTED), t.txt(s.rand(s.total_saved(c)), 32, t.EMERALD, True),
                                  t.txt(f"{len([g for g in goals if not g['achieved']])} active goals · 🔥 {s.current_streak(c)}-day streak", 13, t.MUTED),
                                  t.bar(tot_s / tot_t * 100 if tot_t else 0), t.txt("Overall goal progress", 12, t.MUTED)], spacing=6), gradient=True),
                t.card(ft.Column([t.txt(f"Level {lv['level']} · {lv['xp']} XP", 16, bold=True), t.bar(lv["pct"], t.VIOLET),
                                  t.txt(f"{lv['to_next']} XP to level {lv['level'] + 1}. XP is a game reward only, not money.", 12, t.MUTED)], spacing=6)),
                t.card(ft.Column([t.txt("Daily challenge", 13, t.VIOLET, True), t.txt(s.daily_challenge(), 15),
                                  t.txt("Only if it fits after your essentials.", 12, t.MUTED),
                                  ft.Button("Done today ✓" if daily_done else "Mark complete", disabled=daily_done,
                                            on_click=lambda e: app.confirm(f"Mark today's challenge complete? (+{s.DAILY_XP} XP)", app.finish_daily))], spacing=6)),
                t.txt("Recent achievements", 16, bold=True)]
        done = [q for q in s.quests(c) if q["done"]]
        body += [t.card(t.txt(f"🏅 {q['title']} (+{q['xp']} XP)")) for q in done[-3:]] or [empty("Your first badge is one saving away.")]
    elif name == "My Goals":
        body = [header("My Goals"), ft.Button("New goal", icon=ft.Icons.ADD, on_click=lambda e: app.goal_dialog(None))]
        body += [goal_card(g, app) for g in goals] or [empty("No goals yet. Create one, like 'Emergency fund' or 'New laptop'.")]
    elif name == "Quests":
        body = [header("Quests", "Complete quests to earn XP. Rewards are granted once.")]
        body += [quest_card(q) for q in s.quests(c)]
        body.append(ft.Button("I reviewed my spending plan", icon=ft.Icons.FACT_CHECK,
                              on_click=lambda e: app.confirm("Have you reviewed your spending plan?", lambda: s.mark_budget_reviewed(c))))
    elif name == "Saving History":
        rows = s.history(c)
        body = [header("Saving History")]
        body += [t.card(ft.Row([ft.Column([t.txt(f"{r['goal']} · {s.rand(r['amount_cents'])}", 15, bold=True),
                                           t.txt(f"{r['day']}" + (f" · {r['note']}" if r["note"] else ""), 12, t.MUTED)], expand=True, spacing=2),
                                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=t.ERR, tooltip="Delete entry",
                                              on_click=lambda e, i=r["id"]: app.confirm("Delete this entry? Goal totals and XP will update.",
                                                                                         lambda: s.delete_contribution(c, i)))])) for r in rows]
        body = body if rows else body + [empty("No savings recorded yet. Every rand counts.")]
    elif name == "Achievements":
        body = [header("Achievements & Insights"),
                t.card(ft.Column([t.txt(f"Total saved: {s.rand(s.total_saved(c))}", 16, bold=True),
                                  t.txt(f"Contributions: {len(s.history(c))} · Best streak: {s.best_streak(c)} days · Level {lv['level']}", 13, t.MUTED)], spacing=4)),
                t.txt("Goal completion", 16, bold=True)]
        body += [t.card(ft.Column([t.txt(f"{g['name']} · {g['pct']:.0f}%", 14), t.bar(g["pct"])], spacing=4)) for g in goals] or [empty("Create a goal to see progress here.")]
        body.append(t.txt("Badges", 16, bold=True))
        body += [t.card(t.txt(f"{'🏅' if q['done'] else '🔒'} {q['title']}", color=t.TEXT if q["done"] else t.MUTED)) for q in s.quests(c)]
    else:
        prof = s.get_profile(c)
        name_f, chosen = ft.TextField(label="Display name", value=prof["name"], max_length=30), {"a": prof["avatar"]}
        avatars = ft.Row([ft.TextButton(a, on_click=lambda e, a=a: chosen.update(a=a) or app.toast(f"Avatar {a} selected, press Save.")) for a in t.AVATARS], wrap=True)
        body = [header("Profile & Settings", "Stored only on this device. No email, password or bank details needed."),
                name_f, avatars, ft.Button("Save profile", on_click=lambda e: (s.save_profile(c, name_f.value, chosen["a"]), app.toast("Profile saved"), app.refresh()))]
    return ft.Column([ft.Container(ft.Column(body, spacing=14), padding=ft.Padding.all(16)), footer()], scroll=ft.ScrollMode.AUTO, expand=True)


class App:
    def __init__(self, page, conn):
        self.page, self.conn, self.index = page, conn, 0
        self.holder = ft.Container(expand=True)
        t.apply(page)
        page.add(ft.SafeArea(ft.Column([self.holder, ft.NavigationBar(
            destinations=[ft.NavigationBarDestination(icon=i, label=n.split()[-1] if n != "My Goals" else "Goals") for n, i in zip(PAGES, ICONS)],
            on_change=lambda e: self.go(int(e.control.selected_index)), bgcolor=t.SURFACE)], expand=True, spacing=0), expand=True))
        self.go(0)

    def go(self, i):
        self.index = i
        self.holder.content = build_page(PAGES[i], self)
        self.page.update()

    def refresh(self): self.go(self.index)
    def toast(self, m): self.page.show_dialog(ft.SnackBar(ft.Text(m)))

    def confirm(self, msg, action):
        def yes(e):
            self.page.pop_dialog(); action(); self.refresh()
        self.page.show_dialog(ft.AlertDialog(title=ft.Text("Please confirm"), content=ft.Text(msg), actions=[
            ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()), ft.Button("Yes", on_click=yes)]))

    def finish_daily(self):
        self.toast(f"+{s.DAILY_XP} XP, nice work!" if s.complete_daily(self.conn) else "Already completed today.")

    def goal_dialog(self, p):
        name = ft.TextField(label="Goal name", value=p["name"] if p else "")
        target = ft.TextField(label="Target amount (R)", value=f"{p['target'] / 100:.2f}" if p else "", keyboard_type=ft.KeyboardType.NUMBER)
        due = ft.TextField(label="Target date (optional, YYYY-MM-DD)", visible=p is None)
        err = ft.Text("", color=t.ERR)

        def ok(e):
            try:
                s.update_goal(self.conn, p["id"], name.value, target.value) if p else s.create_goal(self.conn, name.value, target.value, due.value.strip())
            except s.ValidationError as ex:
                err.value = str(ex); self.page.update(); return
            self.page.pop_dialog(); self.refresh()
        self.page.show_dialog(ft.AlertDialog(title=ft.Text("Edit goal" if p else "New goal"), content=ft.Column([name, target, due, err], tight=True),
                                             actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()), ft.Button("Save", on_click=ok)]))

    def save_dialog(self, goal_id):
        goals = [g for g in s.list_goals(self.conn) if not g["achieved"]]
        if not goals:
            return self.toast("Create a goal first, then record savings toward it.")
        pick = ft.Dropdown(label="Goal", options=[ft.DropdownOption(key=str(g["id"]), text=g["name"]) for g in goals],
                           value=str(goal_id if goal_id in [g["id"] for g in goals] else goals[0]["id"]))
        amount, note = ft.TextField(label="Amount (R)", keyboard_type=ft.KeyboardType.NUMBER), ft.TextField(label="Note (optional)", max_length=80)
        over, err = ft.Checkbox(label="Allow extra beyond the goal"), ft.Text("", color=t.ERR)

        def ok(e):
            try:
                before = {q["id"] for q in s.quests(self.conn) if q["done"]}
                s.record_contribution(self.conn, int(pick.value), amount.value, note.value, over.value)
                new = [q["title"] for q in s.quests(self.conn) if q["done"] and q["id"] not in before]
            except s.ValidationError as ex:
                err.value = str(ex); self.page.update(); return
            self.page.pop_dialog(); self.refresh()
            self.toast("Saved! 🎉" + (f" Quest complete: {', '.join(new)}" if new else ""))
        self.page.show_dialog(ft.AlertDialog(title=ft.Text("Record savings"), content=ft.Column([pick, amount, note, over, err], tight=True),
                                             actions=[ft.TextButton("Cancel", on_click=lambda e: self.page.pop_dialog()), ft.Button("Save", on_click=ok)]))
