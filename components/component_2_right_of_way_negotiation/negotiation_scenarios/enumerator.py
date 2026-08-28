"""Deterministic discovery from map geometry and the operational rule engine."""

from itertools import combinations

from negotiation_learning.models import NegotiationStatus
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder

from .models import ScenarioDiscoveryRecord


class NegotiationScenarioEnumerator:
    def __init__(self, path_manager, conflict_zone_manager, traffic_rule_engine):
        self.paths = path_manager
        self.zones = conflict_zone_manager
        self.rules = traffic_rule_engine

    def enumerate(self):
        """Enumerate every 2..N combination with at most one path per approach."""
        paths = tuple(self.paths.paths[path_id] for path_id in sorted(self.paths.paths))
        approach_count = len({path.incoming_lane_id for path in paths})
        records = []
        for size in range(2, approach_count + 1):
            for chosen in combinations(paths, size):
                if len({item.incoming_lane_id for item in chosen}) != size:
                    continue
                records.append(self._classify(chosen))
        return tuple(records)

    def _classify(self, chosen):
        path_ids = tuple(item.path_id for item in chosen)
        physical, edges, unresolved = [], set(), False
        for first, second in combinations(chosen, 2):
            relationship = self.zones.relationship(first.path_id, second.path_id)
            if not relationship.coordinated_conflict:
                continue
            physical.append((first.path_id, second.path_id,
                             relationship.conflict_zone_id,
                             relationship.conflict_type))
            pair = []
            for ego, target in ((first, second), (second, first)):
                result = self.rules._evaluate_candidate(ego, target)
                pair.append(result["regulatory_status"])
                if result["regulatory_status"] == "EGO_MUST_YIELD":
                    edges.add((ego.path_id, target.path_id))
            unresolved |= len(set(pair)) == 0
        edge_dicts = tuple({"yielding_vehicle_id": source,
                            "priority_vehicle_id": target}
                           for source, target in sorted(edges))
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(path_ids, edge_dicts)
        if not physical:
            status = NegotiationStatus.NO_ACTIVE_CONFLICT.value
            result, rejection = "REJECTED", "NO_PHYSICAL_COORDINATED_CONFLICT"
        elif unresolved:
            status = NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value
            result, rejection = "RETAINED", None
        elif analysis["cycle_detected"]:
            status = NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value
            result, rejection = "RETAINED", None
        else:
            status = NegotiationStatus.REGULATORY_ORDER_RESOLVED.value
            result, rejection = "REJECTED", "REGULATORY_ORDER_ACYCLIC"
        candidate_id = ("MAP_RULE_CANDIDATE", path_ids)
        return ScenarioDiscoveryRecord(
            candidate_id, path_ids, tuple(physical), tuple(sorted(edges)),
            analysis["strongly_connected_components"], status, result, rejection,
            {"path_source": "MAP_PATH_MANAGER",
             "geometry_source": "CONFLICT_ZONE_MANAGER",
             "rule_source": "TRAFFIC_RULE_ENGINE",
             "topology_source": "REGULATORY_PRECEDENCE_GRAPH_BUILDER"},
        )
