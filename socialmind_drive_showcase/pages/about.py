from nicegui import ui

from socialmind_drive_showcase.config import (COMPONENTS, FACULTY_NAME,
    INSTITUTION_LOCATION, INSTITUTION_LOGO_IMAGE, INSTITUTION_NAME,
    PROJECT_DESCRIPTION, PROJECT_SUBTITLE, PROJECT_TITLE, SUPERVISORS,
    TEAM_ASSET_ROOT, TEAM_MEMBERS)
from socialmind_drive_showcase.ui.layout import page_layout
from socialmind_drive_showcase.ui.reusable import portrait_or_initials, section_heading


def about_page():
    with page_layout("about"):
        with ui.element("section").classes("detail-hero w-full"):
            with ui.column().classes("page-shell"):
                ui.label("ABOUT THE INITIATIVE").classes("eyebrow")
                ui.label(PROJECT_TITLE).classes("detail-title")
                ui.label(PROJECT_SUBTITLE).classes("hero-subtitle")
        _overview_and_directions()
        _institution()
        _research_team()
        _supervision()


def _overview_and_directions():
    with ui.element("section").classes("section w-full"):
        with ui.column().classes("page-shell"):
            section_heading("PROJECT OVERVIEW",
                            "A common platform for four research directions",
                            PROJECT_DESCRIPTION)
            ui.label("FOUR RESEARCH DIRECTIONS").classes("eyebrow mt-12")
            with ui.element("div").classes("info-grid mt-5"):
                for component in COMPONENTS:
                    with ui.element("article").classes("direction-card"):
                        ui.label(component.number).classes("component-number")
                        ui.icon(component.icon, size="24px").classes("text-cyan-7")
                        ui.label(component.pillar).classes("eyebrow mt-3")
                        ui.label(component.title).classes("font-bold mt-3 leading-snug")


def _institution():
    with ui.element("section").classes("section institution-section w-full"):
        with ui.column().classes("page-shell"):
            section_heading("INSTITUTION", "Research rooted at SLIIT")
            with ui.element("div").classes("institution-card mt-8"):
                with ui.element("div").classes("institution-logo-wrap"):
                    if INSTITUTION_LOGO_IMAGE.is_file():
                        ui.image(str(INSTITUTION_LOGO_IMAGE)).classes("institution-logo")
                    else:
                        ui.icon("account_balance", size="58px").classes("text-cyan-7")
                with ui.column().classes("gap-2 justify-center"):
                    ui.label(INSTITUTION_NAME).classes("text-2xl font-extrabold")
                    ui.label(FACULTY_NAME).classes("text-lg text-blue-grey-7")
                    with ui.row().classes("items-center gap-2"):
                        ui.icon("location_on", size="18px").classes("text-cyan-7")
                        ui.label(INSTITUTION_LOCATION).classes("text-blue-grey-6")


def _research_team():
    with ui.element("section").classes("section w-full"):
        with ui.column().classes("page-shell"):
            section_heading("OUR RESEARCH TEAM",
                            "The people behind SOCIALMIND DRIVE",
                            "Four student researchers from the Department of Computer Science at SLIIT.")
            with ui.element("div").classes("team-grid mt-9"):
                for person in TEAM_MEMBERS:
                    _person_card(person)


def _person_card(person):
    with ui.element("article").classes("person-card"):
        portrait_or_initials(person, TEAM_ASSET_ROOT)
        ui.label(f"{person.display_order:02d}").classes("person-number")
        ui.label(person.role.upper()).classes("person-role")
        ui.label(person.name.upper()).classes("person-name")
        ui.label(person.department).classes("person-department")
        with ui.row().classes("items-center justify-center gap-2 mt-4 no-wrap"):
            ui.icon("mail_outline", size="17px").classes("text-cyan-7")
            ui.link(person.email, f"mailto:{person.email}").classes("person-email")


def _supervision():
    with ui.element("section").classes("section section-dark w-full"):
        with ui.column().classes("page-shell"):
            section_heading("PROJECT SUPERVISION",
                            "Academic guidance and research oversight")
            with ui.element("div").classes("supervisor-grid mt-9"):
                for person in SUPERVISORS:
                    with ui.element("article").classes("supervisor-card"):
                        portrait_or_initials(person, TEAM_ASSET_ROOT, large=True)
                        with ui.column().classes("gap-2 grow justify-center"):
                            ui.label(person.role.upper()).classes("supervisor-role")
                            ui.label(person.name).classes("text-2xl font-extrabold text-white")
                            ui.label(person.department).classes("text-blue-grey-3")
                            ui.label(person.institution).classes("text-blue-grey-4 text-sm")
                            with ui.row().classes("items-center gap-2 mt-2"):
                                ui.icon("mail_outline", size="17px").classes("text-cyan-3")
                                ui.link(person.email, f"mailto:{person.email}").classes("text-cyan-2 text-sm")
