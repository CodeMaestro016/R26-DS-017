import hashlib
import inspect
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from socialmind_drive_showcase import config
from socialmind_drive_showcase.pages.home import home_page
from socialmind_drive_showcase.services.browser_launcher import open_showcase
from socialmind_drive_showcase.services.component_launcher import ComponentLauncher
from socialmind_drive_showcase.services.result_reader import read_panel_results
from socialmind_drive_showcase.ui.reusable import (image_or_fallback,
    initials_for, portrait_or_initials)


def sha256(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()


def test_app_and_home_import_successfully():
    import socialmind_drive_showcase.app as showcase_app
    assert callable(showcase_app.build_app)
    assert callable(home_page)


def test_all_four_components_exist_and_only_component_two_is_live():
    assert len(config.COMPONENTS) == 4
    assert [item.number for item in config.COMPONENTS] == ["01", "02", "03", "04"]
    assert [item.number for item in config.COMPONENTS if item.live] == ["02"]
    assert all(not item.live and item.launch_command is None
               for item in config.COMPONENTS if item.number != "02")


def test_component_two_command_resolves_to_existing_entry_point():
    command = config.COMPONENT2.launch_command
    assert command == ("{python}", "run_panel_demo.py", "--gui", "--gui-delay-ms", "10")
    assert (config.COMPONENT2.working_directory / command[1]).is_file()


def test_result_reader_loads_current_panel_result():
    result = read_panel_results(config.COMPONENT2.result_path)
    assert result["available"] is True
    assert "presentation_vehicles_completed" in result["metrics"]
    assert result["payload"]["evidence_classification"] == "QUALITATIVE_PRESENTATION_ONLY"


def test_missing_and_invalid_results_have_friendly_empty_state(tmp_path):
    missing = read_panel_results(tmp_path / "missing.json")
    assert missing["available"] is False and "No panel-demo result" in missing["message"]
    bad = tmp_path / "bad.json"
    bad.write_text("not json", encoding="utf-8")
    assert read_panel_results(bad)["available"] is False


def test_missing_image_has_explicit_styled_fallback_contract():
    source = inspect.getsource(image_or_fallback)
    assert "fallback-visual" in source
    assert "if target.is_file()" in source


def test_old_dashboard_is_neither_imported_nor_referenced():
    root = config.SHOWCASE_ROOT
    source = "\n".join(path.read_text(encoding="utf-8")
                       for path in root.rglob("*.py") if "tests" not in path.parts)
    assert "debug_dashboard" not in source
    assert "sumo_debug_overlay" not in source


def test_no_arbitrary_command_input_or_shell_execution():
    source = (config.SHOWCASE_ROOT / "services" / "component_launcher.py").read_text()
    assert "shell=False" in source
    assert "user_input" not in source and "request.args" not in source
    assert "launch_command" in source


def test_duplicate_component_launch_is_prevented():
    launcher = ComponentLauncher(config.COMPONENT2)
    launcher.status = "RUNNING"
    assert launcher.launch() is False


def test_non_live_component_cannot_launch():
    launcher = ComponentLauncher(config.COMPONENTS[0])
    assert launcher.launch() is False
    assert launcher.status == "FAILED"


def test_chrome_launcher_falls_back_when_chrome_missing(monkeypatch, tmp_path):
    opened = []
    monkeypatch.setattr("webbrowser.open", lambda url, new=0: opened.append((url, new)))
    mode = open_showcase("http://127.0.0.1:8088", candidates=(tmp_path / "none.exe",))
    assert mode == "DEFAULT_BROWSER"
    assert opened == [("http://127.0.0.1:8088", 1)]


def test_scientific_and_old_dashboard_baseline_hashes_are_unchanged():
    expected = {
        "run_panel_demo.py": "2FCFE941ED787802183079301010939C1EBE01CEC16DFA167E160E601001F97B",
        "debug_dashboard.py": "D363EA829AF524F51307E681B2FD29051AD1C4A22C9E6EAD9383C9EBFBFE71C3",
        "debug_dashboard.html": "21E767A2592AA619550096070A19FA1B5F6AD8CA69BA3B4031BE0BAD0D2DE1AE",
        "sumo_debug_overlay.py": "F5A1E7E810372839FD52F239E1789E2CEFB3FAE912F609C433D27F09431F570A",
    }
    for relative, digest in expected.items():
        assert sha256(config.COMPONENT2_ROOT / relative) == digest


def test_local_only_host_and_predefined_port():
    assert config.HOST == "127.0.0.1"
    assert config.PORT == 8088


def test_home_and_brand_asset_mapping_resolves():
    assert config.HOME_HERO_IMAGE.name == "home_page.png"
    assert config.HOME_HERO_IMAGE.is_file()
    assert config.RESEARCH_VISION_IMAGE.name == "socialmind_hero.jpg"
    assert config.BRAND_LOGO_IMAGE.name == "socialmind_logo.png"
    assert config.BRAND_LOGO_IMAGE.is_file()
    navbar_source = (config.SHOWCASE_ROOT / "ui" / "navbar.py").read_text()
    assert "BRAND_LOGO_IMAGE" in navbar_source


def test_component_asset_extensions_match_real_files():
    expected = {"01": "component_1.jpg", "02": "component_2.png",
                "03": "component_3.png", "04": "component_4.png"}
    assert {item.number: item.image_name for item in config.COMPONENTS} == expected
    assert all((config.SHOWCASE_ROOT / "assets" / "images" /
                item.image_name).is_file() for item in config.COMPONENTS)


def test_research_team_count_and_exact_display_order():
    assert len(config.TEAM_MEMBERS) == 4
    assert [person.name for person in config.TEAM_MEMBERS] == [
        "Avishka Piyumal", "Iresha Nethmini",
        "Dhananji Thakshila", "Imashi Hasinika"]
    assert [person.display_order for person in config.TEAM_MEMBERS] == [1, 2, 3, 4]


def test_supervision_roles_are_separate_from_student_members():
    assert len(config.SUPERVISORS) == 2
    assert [(person.name, person.role) for person in config.SUPERVISORS] == [
        ("Samadhi Rathnayake", "Supervisor"),
        ("Adya Dissanayake", "Co-Supervisor")]
    assert not ({person.name for person in config.TEAM_MEMBERS} &
                {person.name for person in config.SUPERVISORS})


def test_missing_portrait_contract_uses_initials_fallback():
    assert initials_for("Avishka Piyumal") == "AP"
    assert initials_for("Iresha Nethmini") == "IN"
    source = inspect.getsource(portrait_or_initials)
    assert "if target.is_file()" in source
    assert 'return "initials"' in source


def test_existing_component_two_launch_contract_remains_unchanged():
    assert config.COMPONENT2.launch_command == (
        "{python}", "run_panel_demo.py", "--gui", "--gui-delay-ms", "10")
