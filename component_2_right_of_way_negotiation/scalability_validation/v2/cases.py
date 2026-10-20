"""One predetermined demand family: no search and no outcome-dependent inputs."""
# Import asdict, dataclass from dataclasses for the operations below.
from dataclasses import asdict, dataclass
# Import PanelDemand from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import PanelDemand
# Import Scenario, schedule_payload from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import Scenario, schedule_payload

# Set LOADS to a tuple containing 4, 8, 12, 16, 24, 32, 40.
LOADS = (4, 8, 12, 16, 24, 32, 40)
# Set INTERARRIVAL to 0.4.
INTERARRIVAL = 0.4
# Set HEADWAY to 4 multiplied by INTERARRIVAL.
HEADWAY = 4 * INTERARRIVAL
# Set BUDGET to 180.0.
BUDGET = 180.0
# Set APPROACHES to the text 'NESW'.
APPROACHES = "NESW"
# Set MOVEMENTS to a tuple containing the text 'LEFT', the text 'STRAIGHT', the text 'RIGHT'.
MOVEMENTS = ("LEFT", "STRAIGHT", "RIGHT")
# Set PHASE to a dictionary containing N, E, S, W.
PHASE = {"N": 0, "E": 1, "S": 2, "W": 1}

# Template using the inputs and processing steps below.
# Output: a tuple built from a lazy sequence of the result of PanelDemand(a, formatted text built from the
# embedded values, i, the rounded value of (4 * i + offset) *...) for i in the integer...
def template():
    # Return a tuple built from a lazy sequence of the result of PanelDemand(a, formatted text built from the
    # embedded values, i, the rounded value of (4 * i + offset) *...) for i in the integer range defined by 10 to
    # the caller.
    return tuple(PanelDemand(a, f"{a}_IN_0_{MOVEMENTS[(i + PHASE[a]) % 3]}", i,
                            # Supply the rounded value of 4 multiplied by i plus offset multiplied by INTERARRIVAL
                            # to PanelDemand.
                            round((4 * i + offset) * INTERARRIVAL, 10))
                 # Evaluate index/value pairs from APPROACHES as part of the enclosing expression.
                 for i in range(10) for offset, a in enumerate(APPROACHES))

# Apply dataclass(frozen=True) as a decorator to configure the following definition.
@dataclass(frozen=True)
# Define Case to group the state and operations declared below.
# Declared fields: count.
# Construction and attribute behavior follow the declared decorators and base classes.
class Case:
    # Declare count as int for this data structure.
    count: int

    # Apply property as a decorator to configure the following definition.
    @property
    # Case id using the inputs and processing steps below.
    # Output: formatted text built from the embedded values.
    def case_id(self):
        # Return formatted text built from the embedded values to the caller.
        return f"SV-{self.count:02d}"

    # Schedule using the inputs and processing steps below.
    # Output: a dictionary of a mapped to a tuple built from a lazy sequence of row for row in prefix; retain
    # entries satisfying row.approach equals a for a in APPROACHES.
    def schedule(self):
        # Set prefix to template() sliced by :self.count.
        prefix = template()[:self.count]
        # Return a dictionary of a mapped to a tuple built from a lazy sequence of row for row in prefix; retain
        # entries satisfying row.approach equals a for a in APPROACHES to the caller.
        return {a: tuple(row for row in prefix if row.approach == a) for a in APPROACHES}

    # Scenario using the inputs and processing steps below.
    # Output: the result of Scenario(the text 'scalability_prefix_family', self.count, HEADWAY, BUDGET, True).
    def scenario(self):
        # Return the result of Scenario(the text 'scalability_prefix_family', self.count, HEADWAY, BUDGET, True)
        # to the caller.
        return Scenario("scalability_prefix_family", self.count, HEADWAY, BUDGET, True)

# Set CASES to a tuple built from a lazy sequence of the result of Case(n) for n in LOADS.
CASES = tuple(Case(n) for n in LOADS)
# Set BY_ID to a dictionary of c.case_id mapped to c for c in CASES.
BY_ID = {c.case_id: c for c in CASES}

# Frozen cases using the inputs and processing steps below.
# Output: a list of a dictionary built from the supplied values for c in CASES.
def frozen_cases():
    # Return a list of a dictionary built from the supplied values for c in CASES to the caller.
    return [dict(case_id=c.case_id, count=c.count, scenario=asdict(c.scenario()),
                 # Supply schedule as the result of schedule_payload(the result of c.schedule()).
                 schedule=schedule_payload(c.schedule())) for c in CASES]
