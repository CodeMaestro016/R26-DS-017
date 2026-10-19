"""Read the single presentation-only Component 2 scenario catalog."""

import json
from pathlib import Path

from socialmind_drive_showcase.config import COMPONENT2_ROOT


SCENARIO_CATALOG_PATH = COMPONENT2_ROOT / "runtime_simulation" / "scenario_catalog.json"


def read_scenario_catalog(path=SCENARIO_CATALOG_PATH):
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    if Path(path) == SCENARIO_CATALOG_PATH:
        values += [item['definition'] for item in json.loads((Path(path).parent/
            'final_demonstrations.json').read_text(encoding='utf-8')) if 'definition' in item]
    return tuple({**item,
                  "vehicle_count": sum(len(wave)
                                       for wave in item["movement_waves"])}
                 for item in values)


def read_final_demonstrations():
    catalogue={v['scenario_id']:v for v in read_scenario_catalog()}
    menu=json.loads((SCENARIO_CATALOG_PATH.parent/'final_demonstrations.json').read_text(encoding='utf-8'))
    return tuple(dict(catalogue[item['scenario_id']],**{k:v for k,v in item.items() if k!='definition'}) for item in menu)
