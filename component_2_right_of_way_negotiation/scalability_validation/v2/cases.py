"""One predetermined demand family: no search and no outcome-dependent inputs."""
from dataclasses import asdict, dataclass
from runtime_simulation.schedule import PanelDemand
from post_training_evaluation.scenarios import Scenario, schedule_payload

LOADS = (4, 8, 12, 16, 24, 32, 40)
INTERARRIVAL = 0.4
HEADWAY = 4 * INTERARRIVAL
BUDGET = 180.0
APPROACHES = "NESW"
MOVEMENTS = ("LEFT", "STRAIGHT", "RIGHT")
PHASE = {"N": 0, "E": 1, "S": 2, "W": 1}

def template():
    return tuple(PanelDemand(a, f"{a}_IN_0_{MOVEMENTS[(i + PHASE[a]) % 3]}", i,
                            round((4 * i + offset) * INTERARRIVAL, 10))
                 for i in range(10) for offset, a in enumerate(APPROACHES))

@dataclass(frozen=True)
class Case:
    count: int

    @property
    def case_id(self):
        return f"SV-{self.count:02d}"

    def schedule(self):
        prefix = template()[:self.count]
        return {a: tuple(row for row in prefix if row.approach == a) for a in APPROACHES}

    def scenario(self):
        return Scenario("scalability_prefix_family", self.count, HEADWAY, BUDGET, True)

CASES = tuple(Case(n) for n in LOADS)
BY_ID = {c.case_id: c for c in CASES}

def frozen_cases():
    return [dict(case_id=c.case_id, count=c.count, scenario=asdict(c.scenario()),
                 schedule=schedule_payload(c.schedule())) for c in CASES]
