"""Immutable qualitative presentation scenarios; never policy outcomes."""

# Import dataclass from dataclasses for the operations below.
from dataclasses import dataclass
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import MappingProxyType from types for the operations below.
from types import MappingProxyType

# Import PanelDemand from .schedule for the operations below.
from .schedule import PanelDemand


# Set CATALOG_PATH to the result of Path(__file__).with_name(the text 'scenario_catalog.json').
CATALOG_PATH = Path(__file__).with_name("scenario_catalog.json")
# Set FINAL_DEMONSTRATIONS_PATH to the result of Path(__file__).with_name(the text 'final_demonstrations.json').
FINAL_DEMONSTRATIONS_PATH = Path(__file__).with_name('final_demonstrations.json')


# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define PresentationScenario to group the state and operations declared below.
# Declared fields: scenario_id, display_name, description, category, verified_tag, difficulty,
# evidence_classification, source_type, movement_waves, movement_summary, admission_mode,
# demand_headway_seconds,....
# Construction and attribute behavior follow the declared decorators and base classes.
class PresentationScenario:
    # Declare scenario_id as str for this data structure.
    scenario_id: str
    # Declare display_name as str for this data structure.
    display_name: str
    # Declare description as str for this data structure.
    description: str
    # Declare category as str for this data structure.
    category: str
    # Declare verified_tag as str for this data structure.
    verified_tag: str
    # Declare difficulty as str for this data structure.
    difficulty: str
    # Declare evidence_classification as str for this data structure.
    evidence_classification: str
    # Declare source_type as str for this data structure.
    source_type: str
    # Declare movement_waves as tuple for this data structure.
    movement_waves: tuple
    # Declare movement_summary as str for this data structure.
    movement_summary: str
    # Set admission_mode to the text 'ROLLING_WAVES'; declare its type as str.
    admission_mode: str = "ROLLING_WAVES"
    # Set demand_headway_seconds to 0.0; declare its type as float.
    demand_headway_seconds: float = 0.0
    # Set recommended_duration_seconds to 220.0; declare its type as float.
    recommended_duration_seconds: float = 220.0

    # Apply property as a decorator to configure the following definition.
    @property
    # Vehicle count using the inputs and processing steps below.
    # Output: the sum of a lazy sequence of the number of entries in wave for wave in self.movement_waves.
    def vehicle_count(self):
        # Return the sum of a lazy sequence of the number of entries in wave for wave in self.movement_waves to
        # the caller.
        return sum(len(wave) for wave in self.movement_waves)

    # Schedule using the inputs and processing steps below.
    # Output: a dictionary of key mapped to a tuple built from value for (key, value) in key/value pairs from
    # rows.
    # Processing: iterate over the relevant records.
    def schedule(self):
        # Set rows to a dictionary of approach mapped to an empty list for approach in the text 'NESW'.
        rows = {approach: [] for approach in "NESW"}
        # Set counts to a dictionary of approach mapped to 0 for approach in rows.
        counts = {approach: 0 for approach in rows}
        # Iterate over self.movement_waves, binding each item to wave.
        for wave in self.movement_waves:
            # Iterate over wave, binding each item to path_id.
            for path_id in wave:
                # Set approach to path_id at 0.
                approach = path_id[0]
                # Append the result of PanelDemand(approach, path_id, counts at approach, counts at approach
                # multiplied by self.demand_headway_seconds) to rows[approach].
                rows[approach].append(PanelDemand(
                    # Supply counts at approach to PanelDemand.
                    approach, path_id, counts[approach],
                    # Supply counts at approach multiplied by self.demand_headway_seconds to PanelDemand.
                    counts[approach] * self.demand_headway_seconds))
                # Update counts[approach] to its current value plus 1.
                counts[approach] += 1
        # Return a dictionary of key mapped to a tuple built from value for (key, value) in key/value pairs from
        # rows to the caller.
        return {key: tuple(value) for key, value in rows.items()}

    # Apply property as a decorator to configure the following definition.
    @property
    # Admission waves using the inputs and processing steps below.
    # Output: a tuple built from a lazy sequence of a tuple built from a lazy sequence of path_id[0] for path_id
    # in wave for wave in self.movement_waves.
    def admission_waves(self):
        # Return a tuple built from a lazy sequence of a tuple built from a lazy sequence of path_id[0] for
        # path_id in wave for wave in self.movement_waves to the caller.
        return tuple(tuple(path_id[0] for path_id in wave)
                     # Evaluate self.movement_waves as part of the enclosing expression.
                     for wave in self.movement_waves)


# Load scenario catalog using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: scenarios.
# Processing: select branches using the stated conditions.
def load_scenario_catalog(path=CATALOG_PATH):
    # Set values to the decoded data produced by json.loads from the text read from Path(path).
    values = json.loads(Path(path).read_text(encoding="utf-8"))
    # Run this branch when the result of Path(path) equals CATALOG_PATH.
    if Path(path) == CATALOG_PATH:
        # Update values to its current value plus a list of item at 'definition' for item in the decoded data
        # produced by json.loads from the text read from FINAL_DEMONSTRATIONS_PATH; retain entries satisfying the
        # text 'definition' belongs to item.
        values += [item['definition'] for item in json.loads(
            # Supply encoding as the text 'utf-8'.
            FINAL_DEMONSTRATIONS_PATH.read_text(encoding='utf-8')) if 'definition' in item]
    # Set scenarios to a tuple built from a lazy sequence of the result of PresentationScenario(item at
    # 'scenario_id', item at 'display_name', item at 'description', item at 'category', item...) for item in
    # values.
    scenarios = tuple(PresentationScenario(
        # Supply item at 'display_name' to PresentationScenario.
        item["scenario_id"], item["display_name"], item["description"],
        # Supply item at 'verified_tag' to PresentationScenario.
        item["category"], item["verified_tag"], item["difficulty"],
        # Supply item at 'evidence_classification' to PresentationScenario.
        item["evidence_classification"], item["source_type"],
        # Supply a tuple built from a lazy sequence of a tuple built from wave for wave in item at
        # 'movement_waves' to PresentationScenario.
        tuple(tuple(wave) for wave in item["movement_waves"]),
        # Supply 'admission_mode' from item; use the text 'ROLLING_WAVES' if absent to PresentationScenario.
        item["movement_summary"], item.get("admission_mode", "ROLLING_WAVES"),
        # Supply a floating-point number built from 'demand_headway_seconds' from item; use 0.0 if absent to
        # PresentationScenario.
        float(item.get("demand_headway_seconds", 0.0)),
        # Supply a floating-point number built from 'recommended_duration_seconds' from item; use 220.0 if absent
        # to PresentationScenario.
        float(item.get("recommended_duration_seconds", 220.0))) for item in values)
    # Run this branch when the number of entries in a set of item.scenario_id for item in scenarios differs from
    # the number of entries in scenarios.
    if len({item.scenario_id for item in scenarios}) != len(scenarios):
        # Raise ValueError with the text 'PRESENTATION_SCENARIO_IDS_NOT_UNIQUE' to stop this execution path.
        raise ValueError("PRESENTATION_SCENARIO_IDS_NOT_UNIQUE")
    # Run this branch when whether any item is true in a lazy sequence of item.evidence_classification differs
    # from the text 'QUALITATIVE_PRESENTATION_ONLY' for item in scenarios.
    if any(item.evidence_classification != "QUALITATIVE_PRESENTATION_ONLY"
           # Evaluate scenarios as part of the enclosing expression.
           for item in scenarios):
        # Raise ValueError with the text 'PRESENTATION_SCENARIO_EVIDENCE_CLASS_INVALID' to stop this execution
        # path.
        raise ValueError("PRESENTATION_SCENARIO_EVIDENCE_CLASS_INVALID")
    # Return scenarios to the caller.
    return scenarios


# Set SCENARIOS to the result of load_scenario_catalog().
SCENARIOS = load_scenario_catalog()
# Set SCENARIO_BY_ID to the result of MappingProxyType(a dictionary of item.scenario_id mapped to item for item in
# SCENARIOS).
SCENARIO_BY_ID = MappingProxyType({item.scenario_id: item
                                  # Evaluate SCENARIOS as part of the enclosing expression.
                                  for item in SCENARIOS})


# Get scenario using the inputs and processing steps below.
# Input scenario_id: the supplied scenario id.
# Output: SCENARIO_BY_ID at str(scenario_id).
# Processing: handle the specified errors.
def get_scenario(scenario_id):
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Return SCENARIO_BY_ID at str(scenario_id) to the caller.
        return SCENARIO_BY_ID[str(scenario_id)]
    # Handle KeyError as error using the recovery steps below.
    except KeyError as error:
        # Raise ValueError with the text 'UNKNOWN_PRESENTATION_SCENARIO' to stop this execution path.
        raise ValueError("UNKNOWN_PRESENTATION_SCENARIO") from error
