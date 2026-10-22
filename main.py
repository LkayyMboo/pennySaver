import os
import flet as ft
from app import database
from app.views import App


def main(page: ft.Page):
    App(page, database.connect())


if __name__ == "__main__":
    if os.environ.get("PORT"):  # hosting platforms inject PORT
        ft.run(main, view=ft.AppView.WEB_BROWSER, host="0.0.0.0", port=int(os.environ["PORT"]))
    else:
        ft.run(main)
