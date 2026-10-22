import flet as ft

BG, SURFACE, EMERALD, VIOLET = "#0B1020", "#151D31", "#20D6A0", "#8B7CFF"
TEXT, MUTED, WARN, ERR = "#F4F7FF", "#9BA8C7", "#FFB84D", "#FF6B6B"
TAGLINE = "Small steps. Smart money. Big wins."
FOOTER = "Created by Lindokuhle Mbokazi"
AVATARS = ["🦊", "🦁", "🐼", "🚀", "🌱", "⭐"]


def apply(page: ft.Page):
    page.title = "PennyQuest"
    page.bgcolor = BG
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0


def card(content, gradient=False, **kw):
    g = ft.LinearGradient(colors=["#1B2A4A", "#241D4F"]) if gradient else None
    return ft.Container(content=content, bgcolor=None if gradient else SURFACE, gradient=g,
                        padding=ft.Padding.all(16), border_radius=ft.BorderRadius.all(18), **kw)


def txt(value, size=14, color=TEXT, bold=False, **kw):
    return ft.Text(value, size=size, color=color, weight=ft.FontWeight.BOLD if bold else None, **kw)


def bar(pct, color=EMERALD):
    return ft.ProgressBar(value=max(0.0, min(pct / 100, 1.0)), color=color, bgcolor="#243052", bar_height=10)
