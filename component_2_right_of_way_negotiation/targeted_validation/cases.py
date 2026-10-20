"""Versioned deterministic demand; no outcome-dependent schedule selection."""
# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario
# Import Scenario, schedule_payload from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import Scenario, schedule_payload
# Import PanelDemand from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import PanelDemand

# Set NOMINAL_MOVEMENTS to a dictionary containing N, E, S, W.
NOMINAL_MOVEMENTS = {
    # Store a tuple containing the text 'LEFT', the text 'STRAIGHT', the text 'RIGHT', the text 'LEFT' under 'N'.
    "N": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"),
    # Store a tuple containing the text 'LEFT', the text 'RIGHT', the text 'STRAIGHT', the text 'LEFT' under 'E'.
    "E": ("LEFT", "RIGHT", "STRAIGHT", "LEFT"),
    # Store a tuple containing the text 'LEFT', the text 'STRAIGHT', the text 'RIGHT', the text 'LEFT' under 'S'.
    "S": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"),
    # Store a tuple containing the text 'STRAIGHT', the text 'LEFT', the text 'RIGHT', the text 'STRAIGHT' under
    # 'W'.
    "W": ("STRAIGHT", "LEFT", "RIGHT", "STRAIGHT"),
}
# Set NOMINAL_SCENARIO_ID to the text 'nominal_dense_continuous_16'.
NOMINAL_SCENARIO_ID = "nominal_dense_continuous_16"

# Nominal schedule using the inputs and processing steps below.
# Output: a dictionary of a mapped to a tuple built from a lazy sequence of the result of PanelDemand(a,
# f'{a}_IN_0_{movement}', i, (6.0 if a == 'W' else 0.0) + i * 1.5) for (i, movement) in...
def nominal_schedule():
    # Return a dictionary of a mapped to a tuple built from a lazy sequence of the result of PanelDemand(a,
    # f'{a}_IN_0_{movement}', i, (6.0 if a == 'W' else 0.0) + i * 1.5) for (i, movement) in index/value pairs from
    # mix for (a, mix) in key/value pairs from NOMINAL_MOVEMENTS to the caller.
    return {a: tuple(PanelDemand(a, f"{a}_IN_0_{movement}", i,
        # Supply 6.0 when a equals the text 'W', otherwise 0.0 plus i multiplied by 1.5 to PanelDemand.
        (6. if a == "W" else 0.) + i * 1.5) for i, movement in enumerate(mix))
        # Evaluate key/value pairs from NOMINAL_MOVEMENTS as part of the enclosing expression.
        for a, mix in NOMINAL_MOVEMENTS.items()}

# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define Case to group the state and operations declared below.
# Declared fields: case_id, scenario_id, budget_seconds, methods, purpose.
# Construction and attribute behavior follow the declared decorators and base classes.
class Case:
    # Declare case_id as str for this data structure.
    case_id: str
    # Declare scenario_id as str | None for this data structure.
    scenario_id: str | None
    # Declare budget_seconds as float for this data structure.
    budget_seconds: float
    # Declare methods as tuple[str, ...] for this data structure.
    methods: tuple[str, ...]
    # Declare purpose as str for this data structure.
    purpose: str

    # Schedule using the inputs and processing steps below.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def schedule(self):
        # Run this branch when self.scenario_id equals NOMINAL_SCENARIO_ID.
        if self.scenario_id == NOMINAL_SCENARIO_ID:
            # Return the result of nominal_schedule() to the caller.
            return nominal_schedule()
        # Return the result of get_scenario(self.scenario_id).schedule() to the caller.
        return get_scenario(self.scenario_id).schedule()

    # Scenario using the inputs and processing steps below.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def scenario(self):
        # Run this branch when self.scenario_id equals NOMINAL_SCENARIO_ID.
        if self.scenario_id == NOMINAL_SCENARIO_ID:
            # Return the result of Scenario(self.scenario_id, 16, 1.5, self.budget_seconds, True) to the caller.
            return Scenario(self.scenario_id, 16, 1.5, self.budget_seconds, True)
        # Set original to the result of get_scenario(self.scenario_id).
        original = get_scenario(self.scenario_id)
        # Return the result of Scenario(original.scenario_id, original.vehicle_count,
        # original.demand_headway_seconds,...) to the caller.
        return Scenario(original.scenario_id, original.vehicle_count,
            # Supply original.demand_headway_seconds to Scenario.
            original.demand_headway_seconds, self.budget_seconds,
            # Supply original.admission_mode equals the text 'INDEPENDENT_DEMAND' to Scenario.
            original.admission_mode == "INDEPENDENT_DEMAND")

# Set CASES_V1 to a tuple containing the result of Case(the text 'PV-01', the text 'rule_resolved_two', 60.0, a
# tuple containing the text...),...
CASES_V1 = (
    # Include the result of Case(the text 'PV-01', the text 'rule_resolved_two', 60.0, a tuple containing the
    # text...) in this tuple.
    Case("PV-01", "rule_resolved_two", 60., ("PROPOSED_MAPPO",), "Rule-resolved sanity"),
    # Include the result of Case(the text 'PV-02', the text 'regulatory_cycle', 90.0, a tuple containing the
    # text...) in this tuple.
    Case("PV-02", "regulatory_cycle", 90., ("PROPOSED_MAPPO", "RULES_ONLY"), "Negotiation-required cycle; paired demand"),
    # Include the result of Case(the text 'PV-03', the text 'multiple_left_turns', 90.0, a tuple containing the
    # text...) in this tuple.
    Case("PV-03", "multiple_left_turns", 90., ("PROPOSED_MAPPO",), "Selected complex manoeuvre"),
    # Include the result of Case(the text 'PV-04', the text 'congested_four_approach', 180.0, a tuple containing
    # the text...) in this tuple.
    Case("PV-04", "congested_four_approach", 180., ("PROPOSED_MAPPO",), "Dense continuous 16-vehicle traffic; fairness/time"),
    # Include the result of Case(the text 'PV-05', the text 'four_way_simultaneous', 60.0, a tuple containing the
    # text...) in this tuple.
    Case("PV-05", "four_way_simultaneous", 60., ("PROPOSED_MAPPO",), "Natural critical limitation case"),
    # Include the result of Case(the text 'PV-06', None, 0.0, an empty tuple, the text 'Controlled missing/stale
    # coordination...) in this tuple.
    Case("PV-06", None, 0., (), "Controlled missing/stale coordination fail-safe"),
)
# Set CASES to CASES_V1 sliced by :3 plus a tuple containing the result of Case('PV-04A', NOMINAL_SCENARIO_ID,
# 180.0, ('PROPOSED_MAPPO',), 'Nominal dense continuous... plus CASES_V1 sliced by 4:.
CASES = CASES_V1[:3] + (
    # Include the result of Case(the text 'PV-04A', NOMINAL_SCENARIO_ID, 180.0, a tuple containing the text
    # 'PROPOSED_MAPPO', the...) in this tuple.
    Case("PV-04A", NOMINAL_SCENARIO_ID, 180., ("PROPOSED_MAPPO",), "Nominal dense continuous traffic: predeclared capability test"),
    # Include the result of Case(the text 'PV-04B', the text 'congested_four_approach', 180.0, a tuple containing
    # the text...) in this tuple.
    Case("PV-04B", "congested_four_approach", 180., ("PROPOSED_MAPPO",), "Critical dense: preserved reciprocal-precedence limitation"),
# Evaluate CASES_V1 sliced by 4: as part of the enclosing expression.
) + CASES_V1[4:]
# Set BY_ID to a dictionary of c.case_id mapped to c for c in CASES.
BY_ID = {c.case_id: c for c in CASES}
# Set BY_ID['PV-04'] to CASES_V1 at 3.
BY_ID["PV-04"] = CASES_V1[3]  # Historical V1 replay/test identifier, not a V2 case.

# Frozen cases using the inputs and processing steps below.
# Output: a list of a dictionary built from the result of asdict(c) for c in CASES.
def frozen_cases():
    # Return a list of a dictionary built from the result of asdict(c) for c in CASES to the caller.
    return [dict(asdict(c), schedule=schedule_payload(c.schedule()) if c.scenario_id else None,
        # Supply vehicle_count as c.scenario().vehicle_count when c.scenario_id, otherwise None.
        vehicle_count=c.scenario().vehicle_count if c.scenario_id else None) for c in CASES]
