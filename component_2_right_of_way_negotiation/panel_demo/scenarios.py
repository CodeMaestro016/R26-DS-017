"""Immutable qualitative presentation scenarios; never policy outcomes."""

from dataclasses import dataclass
import json
from pathlib import Path
from types import MappingProxyType

from .schedule import PanelDemand


CATALOG_PATH = Path(__file__).with_name("scenario_catalog.json")


@dataclass(frozen=True)
class PresentationScenario:
    scenario_id: str
    display_name: str
    description: str
    category: str
    verified_tag: str
    difficulty: str
    evidence_classification: str
    source_type: str
    movement_waves: tuple
    movement_summary: str
    admission_mode: str = "ROLLING_WAVES"
    demand_headway_seconds: float = 0.0
    recommended_duration_seconds: float = 220.0

    @property
    def vehicle_count(self):
        return sum(len(wave) for wave in self.movement_waves)

    def schedule(self):
        rows = {approach: [] for approach in "NESW"}
        counts = {approach: 0 for approach in rows}
        for wave in self.movement_waves:
            for path_id in wave:
                approach = path_id[0]
                rows[approach].append(PanelDemand(
                    approach, path_id, counts[approach],
                    counts[approach] * self.demand_headway_seconds))
                counts[approach] += 1
        return {key: tuple(value) for key, value in rows.items()}

    @property
    def admission_waves(self):
        return tuple(tuple(path_id[0] for path_id in wave)
                     for wave in self.movement_waves)


def load_scenario_catalog(path=CATALOG_PATH):
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    scenarios = tuple(PresentationScenario(
        item["scenario_id"], item["display_name"], item["description"],
        item["category"], item["verified_tag"], item["difficulty"],
        item["evidence_classification"], item["source_type"],
        tuple(tuple(wave) for wave in item["movement_waves"]),
        item["movement_summary"], item.get("admission_mode", "ROLLING_WAVES"),
        float(item.get("demand_headway_seconds", 0.0)),
        float(item.get("recommended_duration_seconds", 220.0))) for item in values)
    if len({item.scenario_id for item in scenarios}) != len(scenarios):
        raise ValueError("PRESENTATION_SCENARIO_IDS_NOT_UNIQUE")
    if any(item.evidence_classification != "QUALITATIVE_PRESENTATION_ONLY"
           for item in scenarios):
        raise ValueError("PRESENTATION_SCENARIO_EVIDENCE_CLASS_INVALID")
    return scenarios


SCENARIOS = load_scenario_catalog()
SCENARIO_BY_ID = MappingProxyType({item.scenario_id: item
                                  for item in SCENARIOS})


def get_scenario(scenario_id):
    try:
        return SCENARIO_BY_ID[str(scenario_id)]
    except KeyError as error:
        raise ValueError("UNKNOWN_PRESENTATION_SCENARIO") from error
