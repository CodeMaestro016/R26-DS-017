from pathlib import Path
from nicegui import ui


def section_heading(eyebrow, title, copy=None, dark=False):
    ui.label(eyebrow).classes("eyebrow")
    ui.label(title).classes("section-title")
    if copy:
        ui.label(copy).classes("section-copy")


def image_or_fallback(path, icon="directions_car", label="Presentation image space"):
    target = Path(path)
    if target.is_file():
        ui.image(str(target)).classes("detail-image w-full")
        return "image"
    with ui.element("div").classes("fallback-visual w-full"):
        with ui.column().classes("items-center relative z-10"):
            ui.icon(icon, size="64px").classes("text-cyan-3")
            ui.label(label).classes("text-sm text-blue-grey-2 tracking-wider")
    return "fallback"


def card_image_or_fallback(path, icon="image"):
    target = Path(path)
    with ui.element("div").classes("component-image-wrap"):
        if target.is_file():
            ui.image(str(target)).classes("component-image")
            return "image"
        ui.icon(icon, size="48px").classes("text-cyan-3 relative z-10")
    return "fallback"


def initials_for(name):
    return "".join(part[0] for part in str(name).split()[:2]).upper()


def portrait_or_initials(person, asset_root, large=False):
    target = Path(asset_root) / person.image_name
    size_class = "person-portrait-large" if large else "person-portrait"
    if target.is_file():
        ui.image(str(target)).classes(size_class)
        return "image"
    with ui.element("div").classes(f"initials-avatar {size_class}"):
        ui.label(initials_for(person.name))
    return "initials"
