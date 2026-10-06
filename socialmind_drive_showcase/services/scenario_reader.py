"""Read the single presentation-only Component 2 scenario catalog."""

import json
from pathlib import Path

from socialmind_drive_showcase.config import COMPONENT2_ROOT


SCENARIO_CATALOG_PATH = COMPONENT2_ROOT / "panel_demo" / "scenario_catalog.json"


def read_scenario_catalog(path=SCENARIO_CATALOG_PATH):
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    return tuple({**item,
                  "vehicle_count": sum(len(wave)
                                       for wave in item["movement_waves"])}
                 for item in values)
