"""Versioned deterministic demand; no outcome-dependent schedule selection."""
from dataclasses import asdict, dataclass
from runtime_simulation.scenarios import get_scenario
from post_training_evaluation.scenarios import Scenario, schedule_payload
from runtime_simulation.schedule import PanelDemand

NOMINAL_MOVEMENTS = {
    "N": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"),
    "E": ("LEFT", "RIGHT", "STRAIGHT", "LEFT"),
    "S": ("LEFT", "STRAIGHT", "RIGHT", "LEFT"),
    "W": ("STRAIGHT", "LEFT", "RIGHT", "STRAIGHT"),
}
NOMINAL_SCENARIO_ID = "nominal_dense_continuous_16"

def nominal_schedule():
    return {a: tuple(PanelDemand(a, f"{a}_IN_0_{movement}", i,
        (6. if a == "W" else 0.) + i * 1.5) for i, movement in enumerate(mix))
        for a, mix in NOMINAL_MOVEMENTS.items()}

@dataclass(frozen=True)
class Case:
    case_id: str
    scenario_id: str | None
    budget_seconds: float
    methods: tuple[str, ...]
    purpose: str

    def schedule(self):
        if self.scenario_id == NOMINAL_SCENARIO_ID:
            return nominal_schedule()
        return get_scenario(self.scenario_id).schedule()

    def scenario(self):
        if self.scenario_id == NOMINAL_SCENARIO_ID:
            return Scenario(self.scenario_id, 16, 1.5, self.budget_seconds, True)
        original = get_scenario(self.scenario_id)
        return Scenario(original.scenario_id, original.vehicle_count,
            original.demand_headway_seconds, self.budget_seconds,
            original.admission_mode == "INDEPENDENT_DEMAND")

CASES_V1 = (
    Case("PV-01", "rule_resolved_two", 60., ("PROPOSED_MAPPO",), "Rule-resolved sanity"),
    Case("PV-02", "regulatory_cycle", 90., ("PROPOSED_MAPPO", "RULES_ONLY"), "Negotiation-required cycle; paired demand"),
    Case("PV-03", "multiple_left_turns", 90., ("PROPOSED_MAPPO",), "Selected complex manoeuvre"),
    Case("PV-04", "congested_four_approach", 180., ("PROPOSED_MAPPO",), "Dense continuous 16-vehicle traffic; fairness/time"),
    Case("PV-05", "four_way_simultaneous", 60., ("PROPOSED_MAPPO",), "Natural critical limitation case"),
    Case("PV-06", None, 0., (), "Controlled missing/stale coordination fail-safe"),
)
CASES = CASES_V1[:3] + (
    Case("PV-04A", NOMINAL_SCENARIO_ID, 180., ("PROPOSED_MAPPO",), "Nominal dense continuous traffic: predeclared capability test"),
    Case("PV-04B", "congested_four_approach", 180., ("PROPOSED_MAPPO",), "Critical dense: preserved reciprocal-precedence limitation"),
) + CASES_V1[4:]
BY_ID = {c.case_id: c for c in CASES}
BY_ID["PV-04"] = CASES_V1[3]  # Historical V1 replay/test identifier, not a V2 case.

def frozen_cases():
    return [dict(asdict(c), schedule=schedule_payload(c.schedule()) if c.scenario_id else None,
        vehicle_count=c.scenario().vehicle_count if c.scenario_id else None) for c in CASES]
