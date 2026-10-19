from contextlib import contextmanager
from nicegui import ui
from .navbar import navbar
from .footer import footer
from .theme import apply_theme


@contextmanager
def page_layout(active=""):
    apply_theme()
    navbar(active)
    yield
    footer()
