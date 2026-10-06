import json
from pathlib import Path

from config import PROJECT_ROOT, SUMO_NETWORK_FILE
from conflict import MapPathManager
from traffic_rules import RegulatoryStatus, TrafficRuleEngine, validate_network_odd


class StubLDM:
    def __init__(self, graph):
        self.ego_id = graph["ego_id"]
        self.graph = graph
        self.tracks = {
            self.ego_id: {},
            "target": {
                "route_id": "contradictory",
                "route_index": 999,
                "ground_truth_route_id": "also_contradictory",
            },
        }

    def get_current_conflict_graph(self):
        return self.graph


def graph(ego_path, *target_paths):
    grouped = {}
    for path in target_paths:
        grouped.setdefault(path.rsplit("_", 1)[-1], []).append(path)
    candidates = {name: values[0] if len(values) == 1 else tuple(values)
                  for name, values in grouped.items()}
    return {
        "ego_id": "ego", "ego_path_id": ego_path,
        "edges": ({"target_track_id": "target",
                   "spatially_conflicting_candidate_paths": candidates},),
    }


def assessment(engine, ego_path, *target_paths):
    result = engine.assess_ldm(StubLDM(graph(ego_path, *target_paths)), 4.0)
    return result["assessments"][0]


def test_static_approach_relations_and_right_before_left():
    paths = MapPathManager()
    engine = TrafficRuleEngine(paths)
    assert paths.approach_relation("W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT") == "RIGHT"
    assert paths.approach_relation("W_IN_0_STRAIGHT", "N_IN_0_STRAIGHT") == "LEFT"
    assert paths.approach_relation("W_IN_0_STRAIGHT", "E_IN_0_STRAIGHT") == "ONCOMING"
    right = assessment(engine, "W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT")
    assert right["regulatory_status"] == RegulatoryStatus.EGO_MUST_YIELD.value
    assert "DE-STVO-8-1" in right["applicable_rule_ids"]
    left = assessment(engine, "W_IN_0_STRAIGHT", "N_IN_0_STRAIGHT")
    assert left["regulatory_status"] == RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.value
    oncoming = assessment(engine, "W_IN_0_STRAIGHT", "E_IN_0_STRAIGHT")
    assert oncoming["regulatory_status"] == RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE.value


def test_turning_oncoming_and_left_oncoming_right_rules():
    engine = TrafficRuleEngine(MapPathManager())
    turning = assessment(engine, "W_IN_0_RIGHT", "E_IN_0_STRAIGHT")
    assert turning["regulatory_status"] == RegulatoryStatus.EGO_MUST_YIELD.value
    assert "DE-STVO-9-3" in turning["applicable_rule_ids"]
    left_right = assessment(engine, "W_IN_0_LEFT", "E_IN_0_RIGHT")
    assert {"DE-STVO-9-3", "DE-STVO-9-4"}.issubset(left_right["applicable_rule_ids"])


def test_only_graph_spatial_edges_create_assessments():
    engine = TrafficRuleEngine(MapPathManager())
    empty = {"ego_id": "ego", "ego_path_id": "W_IN_0_STRAIGHT", "edges": ()}
    result = engine.assess_ldm(StubLDM(empty), 1.0)
    assert result["assessments"] == ()


def test_candidate_disagreement_is_unresolved_without_probability_or_route_truth():
    engine = TrafficRuleEngine(MapPathManager())
    before = assessment(
        engine, "W_IN_0_STRAIGHT", "S_IN_0_STRAIGHT", "N_IN_0_STRAIGHT"
    )
    assert before["regulatory_status"] == RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE.value
    assert "safe_to_enter" in before and before["safe_to_enter"] is False
    assert before["control_action"] is None


def test_catalogue_negotiation_rule_and_network_odd_validation(tmp_path):
    profile = PROJECT_ROOT / "traffic_rules" / "profiles" / "de_stvo_uncontrolled_4way_v1.json"
    rules = {item["rule_id"]: item for item in json.loads(profile.read_text(encoding="utf-8"))["rules"]}
    assert rules["DE-STVO-11-3"]["implementation_status"] == "NEGOTIATION_ENABLING_RULE"
    assert rules["DE-STVO-11-1"]["implementation_status"] == "DEFERRED_REQUIRED_INPUT_NOT_AVAILABLE"
    assert validate_network_odd(SUMO_NETWORK_FILE)["passed"] is True
    bad = tmp_path / "bad.net.xml"
    bad.write_text('<net lefthand="true"><junction id="center" type="priority" incLanes="a b c"/></net>', encoding="utf-8")
    result = validate_network_odd(bad)
    assert result["passed"] is False
    assert result["right_hand_network_confirmed"] is False
    assert result["right_before_left"] is False


def test_archived_source_provenance_and_active_sections():
    import hashlib
    archive = PROJECT_ROOT / "docs" / "regulatory_sources" / "de_stvo" / "2026-08-11"
    source = archive / "BJNR036710013.xml"
    source_md = (archive / "SOURCE.md").read_text(encoding="utf-8")
    digest = hashlib.sha256(source.read_bytes()).hexdigest().upper()
    assert source.name in source_md
    assert digest in source_md
    engine = TrafficRuleEngine(MapPathManager())
    assert all(rule.section and rule.paragraph for rule in engine.rules
               if rule.implementation_status == "ACTIVE")
