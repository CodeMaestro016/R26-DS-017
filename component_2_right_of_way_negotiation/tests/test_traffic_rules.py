# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import PROJECT_ROOT, SUMO_NETWORK_FILE from config for the operations below.
from config import PROJECT_ROOT, SUMO_NETWORK_FILE
# Import MapPathManager from conflict for the operations below.
from conflict import MapPathManager
# Import RegulatoryStatus, TrafficRuleEngine, validate_network_odd from traffic_rules for the operations below.
from traffic_rules import RegulatoryStatus, TrafficRuleEngine, validate_network_odd


# Define StubLDM to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class StubLDM:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input graph: the supplied graph.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, graph):
        # Set self.ego_id to graph at 'ego_id'.
        self.ego_id = graph["ego_id"]
        # Set self.graph to graph.
        self.graph = graph
        # Set self.tracks to a dictionary containing target.
        self.tracks = {
            # Store an empty dictionary under self.ego_id.
            self.ego_id: {},
            # Store a dictionary containing route_id, route_index, ground_truth_route_id under 'target'.
            "target": {
                "route_id": "contradictory",
                # Store 999 under 'route_index'.
                "route_index": 999,
                "ground_truth_route_id": "also_contradictory",
            },
        }

    # Get current conflict graph using the inputs and processing steps below.
    # Output: self.graph.
    def get_current_conflict_graph(self):
        # Return self.graph to the caller.
        return self.graph


# Graph using the inputs and processing steps below.
# Input ego_path: the supplied ego path.
# Input target_paths: the supplied target paths.
# Output: a dictionary containing ego_id, ego_path_id, edges.
# Processing: iterate over the relevant records.
def graph(ego_path, *target_paths):
    # Set grouped to an empty dictionary.
    grouped = {}
    # Iterate over target_paths, binding each item to path.
    for path in target_paths:
        # Append path to grouped.setdefault(path.rsplit('_', 1)[-1], []).
        grouped.setdefault(path.rsplit("_", 1)[-1], []).append(path)
    # Set candidates to a dictionary of name mapped to values at 0 when the number of entries in values equals 1,
    # otherwise a tuple built from values for (name, values) in key/value pairs from grouped.
    candidates = {name: values[0] if len(values) == 1 else tuple(values)
                  # Evaluate key/value pairs from grouped as part of the enclosing expression.
                  for name, values in grouped.items()}
    # Return a dictionary containing ego_id, ego_path_id, edges to the caller.
    return {
        # Store the text 'ego' under 'ego_id'.
        # Store ego_path under 'ego_path_id'.
        "ego_id": "ego", "ego_path_id": ego_path,
        # Store a tuple containing a dictionary containing target_track_id, spatially_conflicting_candidate_paths
        # under 'edges'.
        # Store the text 'target' under 'target_track_id'.
        "edges": ({"target_track_id": "target",
                   # Store candidates under 'spatially_conflicting_candidate_paths'.
                   "spatially_conflicting_candidate_paths": candidates},),
    }


# Assessment using the inputs and processing steps below.
# Input engine: the supplied engine.
# Input ego_path: the supplied ego path.
# Input target_paths: the supplied target paths.
# Output: result['assessments'] at 0.
def assessment(engine, ego_path, *target_paths):
    # Set result to the result of engine.assess_ldm(the result of StubLDM(the result of graph(ego_path, the
    # unpacked values from target_paths)), 4.0).
    result = engine.assess_ldm(StubLDM(graph(ego_path, *target_paths)), 4.0)
    # Return result['assessments'] at 0 to the caller.
    return result["assessments"][0]


# Check static approach relations and right before left using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_static_approach_relations_and_right_before_left():
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set engine to the result of TrafficRuleEngine(paths).
    engine = TrafficRuleEngine(paths)
    # Require the result of paths.approach_relation(the text 'W_IN_0_STRAIGHT', the text 'S_IN_0_STRAIGHT') equals
    # the text 'RIGHT'; otherwise raise AssertionError.
    assert paths.approach_relation("W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT") == "RIGHT"
    # Require the result of paths.approach_relation(the text 'W_IN_0_STRAIGHT', the text 'N_IN_0_STRAIGHT') equals
    # the text 'LEFT'; otherwise raise AssertionError.
    assert paths.approach_relation("W_IN_0_STRAIGHT", "N_IN_0_STRAIGHT") == "LEFT"
    # Require the result of paths.approach_relation(the text 'W_IN_0_STRAIGHT', the text 'E_IN_0_STRAIGHT') equals
    # the text 'ONCOMING'; otherwise raise AssertionError.
    assert paths.approach_relation("W_IN_0_STRAIGHT", "E_IN_0_STRAIGHT") == "ONCOMING"
    # Set right to the result of assessment(engine, the text 'W_IN_0_STRAIGHT', the text 'S_IN_0_STRAIGHT').
    right = assessment(engine, "W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT")
    # Require right at 'regulatory_status' equals RegulatoryStatus.EGO_MUST_YIELD.value; otherwise raise
    # AssertionError.
    assert right["regulatory_status"] == RegulatoryStatus.EGO_MUST_YIELD.value
    # Require the text 'DE-STVO-8-1' belongs to right at 'applicable_rule_ids'; otherwise raise AssertionError.
    assert "DE-STVO-8-1" in right["applicable_rule_ids"]
    # Set left to the result of assessment(engine, the text 'W_IN_0_STRAIGHT', the text 'N_IN_0_STRAIGHT').
    left = assessment(engine, "W_IN_0_STRAIGHT", "N_IN_0_STRAIGHT")
    # Require left at 'regulatory_status' equals RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.value; otherwise
    # raise AssertionError.
    assert left["regulatory_status"] == RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.value
    # Set oncoming to the result of assessment(engine, the text 'W_IN_0_STRAIGHT', the text 'E_IN_0_STRAIGHT').
    oncoming = assessment(engine, "W_IN_0_STRAIGHT", "E_IN_0_STRAIGHT")
    # Require oncoming at 'regulatory_status' equals RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE.value; otherwise
    # raise AssertionError.
    assert oncoming["regulatory_status"] == RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE.value


# Check turning oncoming and left oncoming right rules using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_turning_oncoming_and_left_oncoming_right_rules():
    # Set engine to the result of TrafficRuleEngine(the result of MapPathManager()).
    engine = TrafficRuleEngine(MapPathManager())
    # Set turning to the result of assessment(engine, the text 'W_IN_0_RIGHT', the text 'E_IN_0_STRAIGHT').
    turning = assessment(engine, "W_IN_0_RIGHT", "E_IN_0_STRAIGHT")
    # Require turning at 'regulatory_status' equals RegulatoryStatus.EGO_MUST_YIELD.value; otherwise raise
    # AssertionError.
    assert turning["regulatory_status"] == RegulatoryStatus.EGO_MUST_YIELD.value
    # Require the text 'DE-STVO-9-3' belongs to turning at 'applicable_rule_ids'; otherwise raise AssertionError.
    assert "DE-STVO-9-3" in turning["applicable_rule_ids"]
    # Set left_right to the result of assessment(engine, the text 'W_IN_0_LEFT', the text 'E_IN_0_RIGHT').
    left_right = assessment(engine, "W_IN_0_LEFT", "E_IN_0_RIGHT")
    # Require the result of {'DE-STVO-9-3', 'DE-STVO-9-4'}.issubset(left_right at 'applicable_rule_ids');
    # otherwise raise AssertionError.
    assert {"DE-STVO-9-3", "DE-STVO-9-4"}.issubset(left_right["applicable_rule_ids"])


# Check v2 oncoming turn rules are symmetric and do not invent mutual yield using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_v2_oncoming_turn_rules_are_symmetric_and_do_not_invent_mutual_yield():
    # Set engine to the result of TrafficRuleEngine(the result of MapPathManager()).
    engine=TrafficRuleEngine(MapPathManager(),runtime_v2=True)
    # Require assessment(engine, 'W_IN_0_LEFT', 'E_IN_0_LEFT') at 'regulatory_status' equals the text
    # 'NO_PAIRWISE_PRECEDENCE_RULE'; otherwise raise AssertionError.
    assert assessment(engine,"W_IN_0_LEFT","E_IN_0_LEFT")["regulatory_status"]=="NO_PAIRWISE_PRECEDENCE_RULE"
    # Require assessment(engine, 'W_IN_0_RIGHT', 'E_IN_0_RIGHT') at 'regulatory_status' equals the text
    # 'NO_PAIRWISE_PRECEDENCE_RULE'; otherwise raise AssertionError.
    assert assessment(engine,"W_IN_0_RIGHT","E_IN_0_RIGHT")["regulatory_status"]=="NO_PAIRWISE_PRECEDENCE_RULE"
    # Require assessment(engine, 'W_IN_0_RIGHT', 'E_IN_0_LEFT') at 'regulatory_status' equals the text
    # 'EGO_HAS_PRECEDENCE_UNDER_RULE'; otherwise raise AssertionError.
    assert assessment(engine,"W_IN_0_RIGHT","E_IN_0_LEFT")["regulatory_status"]=="EGO_HAS_PRECEDENCE_UNDER_RULE"
    # Require assessment(engine, 'W_IN_0_LEFT', 'E_IN_0_RIGHT') at 'regulatory_status' equals the text
    # 'EGO_MUST_YIELD'; otherwise raise AssertionError.
    assert assessment(engine,"W_IN_0_LEFT","E_IN_0_RIGHT")["regulatory_status"]=="EGO_MUST_YIELD"
    # Require assessment(engine, 'W_IN_0_STRAIGHT', 'E_IN_0_RIGHT') at 'regulatory_status' equals the text
    # 'EGO_HAS_PRECEDENCE_UNDER_RULE'; otherwise raise AssertionError.
    assert assessment(engine,"W_IN_0_STRAIGHT","E_IN_0_RIGHT")["regulatory_status"]=="EGO_HAS_PRECEDENCE_UNDER_RULE"
    # Set mixed to the result of assessment(engine, the text 'W_IN_0_LEFT', the text 'E_IN_0_LEFT', the text
    # 'E_IN_0_RIGHT', the text...).
    mixed=assessment(engine,"W_IN_0_LEFT","E_IN_0_LEFT","E_IN_0_RIGHT","E_IN_0_STRAIGHT")
    # Require mixed at 'regulatory_status' equals the text 'UNRESOLVED_DUE_TO_TARGET_MANOEUVRE'; otherwise raise
    # AssertionError.
    assert mixed["regulatory_status"]=="UNRESOLVED_DUE_TO_TARGET_MANOEUVRE"


# Check only graph spatial edges create assessments using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_only_graph_spatial_edges_create_assessments():
    # Set engine to the result of TrafficRuleEngine(the result of MapPathManager()).
    engine = TrafficRuleEngine(MapPathManager())
    # Set empty to a dictionary containing ego_id, ego_path_id, edges.
    empty = {"ego_id": "ego", "ego_path_id": "W_IN_0_STRAIGHT", "edges": ()}
    # Set result to the result of engine.assess_ldm(the result of StubLDM(empty), 1.0).
    result = engine.assess_ldm(StubLDM(empty), 1.0)
    # Require result at 'assessments' equals an empty tuple; otherwise raise AssertionError.
    assert result["assessments"] == ()


# Check candidate disagreement is unresolved without probability or route truth using the setup, calls, and
# assertions below.
# Output: no explicit value; normal completion returns None.
def test_candidate_disagreement_is_unresolved_without_probability_or_route_truth():
    # Set engine to the result of TrafficRuleEngine(the result of MapPathManager()).
    engine = TrafficRuleEngine(MapPathManager())
    # Set before to the result of assessment(engine, the text 'W_IN_0_STRAIGHT', the text 'S_IN_0_STRAIGHT', the
    # text 'N_IN_0_STRAIGHT').
    before = assessment(
        # Supply engine to assessment.
        engine, "W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT", "N_IN_0_STRAIGHT"
    )
    # Require before at 'regulatory_status' equals RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE.value;
    # otherwise raise AssertionError.
    assert before["regulatory_status"] == RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE.value
    # Require the text 'safe_to_enter' belongs to before and before at 'safe_to_enter' is the same object as
    # False; otherwise raise AssertionError.
    assert "safe_to_enter" in before and before["safe_to_enter"] is False
    # Require before at 'control_action' is the same object as None; otherwise raise AssertionError.
    assert before["control_action"] is None


# Check catalogue negotiation rule and network odd validation using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_catalogue_negotiation_rule_and_network_odd_validation(tmp_path):
    # Set profile to PROJECT_ROOT joined with the path segment 'traffic_rules' joined with the path segment 'profiles' divided by
    # the text 'de_stvo_uncontrolled_4way_v1.json'.
    profile = PROJECT_ROOT / "traffic_rules" / "profiles" / "de_stvo_uncontrolled_4way_v1.json"
    # Set rules to a dictionary of item at 'rule_id' mapped to item for item in
    # json.loads(profile.read_text(encoding='utf-8')) at 'rules'.
    rules = {item["rule_id"]: item for item in json.loads(profile.read_text(encoding="utf-8"))["rules"]}
    # Require rules['DE-STVO-11-3'] at 'implementation_status' equals the text 'NEGOTIATION_ENABLING_RULE';
    # otherwise raise AssertionError.
    assert rules["DE-STVO-11-3"]["implementation_status"] == "NEGOTIATION_ENABLING_RULE"
    # Require rules['DE-STVO-11-1'] at 'implementation_status' equals the text
    # 'DEFERRED_REQUIRED_INPUT_NOT_AVAILABLE'; otherwise raise AssertionError.
    assert rules["DE-STVO-11-1"]["implementation_status"] == "DEFERRED_REQUIRED_INPUT_NOT_AVAILABLE"
    # Require validate_network_odd(SUMO_NETWORK_FILE) at 'passed' is the same object as True; otherwise raise
    # AssertionError.
    assert validate_network_odd(SUMO_NETWORK_FILE)["passed"] is True
    # Set bad to tmp_path joined with the path segment 'bad.net.xml'.
    bad = tmp_path / "bad.net.xml"
    # Write the supplied text to bad.
    bad.write_text('<net lefthand="true"><junction id="center" type="priority" incLanes="a b c"/></net>', encoding="utf-8")
    # Set result to the result of validate_network_odd(bad).
    result = validate_network_odd(bad)
    # Require result at 'passed' is the same object as False; otherwise raise AssertionError.
    assert result["passed"] is False
    # Require result at 'right_hand_network_confirmed' is the same object as False; otherwise raise
    # AssertionError.
    assert result["right_hand_network_confirmed"] is False
    # Require result at 'right_before_left' is the same object as False; otherwise raise AssertionError.
    assert result["right_before_left"] is False


# Check archived source provenance and active sections using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_archived_source_provenance_and_active_sections():
    # Import hashlib for use in this module.
    import hashlib
    # Set archive to PROJECT_ROOT joined with the path segment 'docs' joined with the path segment 'regulatory_sources' joined with the path segment
    # 'de_stvo' joined with the path segment '2026-08-11'.
    archive = PROJECT_ROOT / "docs" / "regulatory_sources" / "de_stvo" / "2026-08-11"
    # Set source to archive joined with the path segment 'BJNR036710013.xml'.
    source = archive / "BJNR036710013.xml"
    # Set source_md to the text read from (archive / 'SOURCE.md').
    source_md = (archive / "SOURCE.md").read_text(encoding="utf-8")
    # Set digest to the result of hashlib.sha256(source.read_bytes()).hexdigest().upper().
    digest = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    # Require source.name belongs to source_md; otherwise raise AssertionError.
    assert source.name in source_md
    # Require digest belongs to source_md; otherwise raise AssertionError.
    assert digest in source_md
    # Set engine to the result of TrafficRuleEngine(the result of MapPathManager()).
    engine = TrafficRuleEngine(MapPathManager())
    # Require whether every item is true in a lazy sequence of rule.section and rule.paragraph for rule in
    # engine.rules; retain entries satisfying rule.implementation_status equals the text 'ACTIVE'; otherwise raise
    # AssertionError.
    assert all(rule.section and rule.paragraph for rule in engine.rules
               # Evaluate rule.implementation_status equals the text 'ACTIVE' as part of the enclosing expression.
               if rule.implementation_status == "ACTIVE")
