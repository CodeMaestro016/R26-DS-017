"""Deterministic discovery from map geometry and the operational rule engine."""

# Import combinations from itertools for the operations below.
from itertools import combinations

# Import NegotiationStatus from negotiation_learning.models for the operations below.
from negotiation_learning.models import NegotiationStatus
# Import RegulatoryPrecedenceGraphBuilder from negotiation_learning.precedence_graph for the operations below.
from negotiation_learning.precedence_graph import RegulatoryPrecedenceGraphBuilder

# Import ScenarioDiscoveryRecord from .models for the operations below.
from .models import ScenarioDiscoveryRecord


# Define NegotiationScenarioEnumerator to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class NegotiationScenarioEnumerator:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Input conflict_zone_manager: the supplied conflict zone manager.
    # Input traffic_rule_engine: the supplied traffic rule engine.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path_manager, conflict_zone_manager, traffic_rule_engine):
        # Set self.paths to path_manager.
        self.paths = path_manager
        # Set self.zones to conflict_zone_manager.
        self.zones = conflict_zone_manager
        # Set self.rules to traffic_rule_engine.
        self.rules = traffic_rule_engine

    # Enumerate every 2..N combination with at most one path per approach.
    # Output: a tuple built from records.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def enumerate(self):
        """Enumerate every 2..N combination with at most one path per approach."""
        # Set paths to a tuple built from a lazy sequence of self.paths.paths at path_id for path_id in the sorted
        # values from self.paths.paths.
        paths = tuple(self.paths.paths[path_id] for path_id in sorted(self.paths.paths))
        # Set approach_count to the number of entries in a set of path.incoming_lane_id for path in paths.
        approach_count = len({path.incoming_lane_id for path in paths})
        # Set records to an empty list.
        records = []
        # Iterate over the integer range defined by 2, approach_count plus 1, binding each item to size.
        for size in range(2, approach_count + 1):
            # Iterate over the result of combinations(paths, size), binding each item to chosen.
            for chosen in combinations(paths, size):
                # Run this branch when the number of entries in a set of item.incoming_lane_id for item in chosen
                # differs from size.
                if len({item.incoming_lane_id for item in chosen}) != size:
                    # Skip the rest of this loop iteration and process the next item.
                    continue
                # Append the result of self._classify(chosen) to records.
                records.append(self._classify(chosen))
        # Return a tuple built from records to the caller.
        return tuple(records)

    # Classify using the inputs and processing steps below.
    # Input chosen: the supplied chosen.
    # Output: the result of ScenarioDiscoveryRecord(candidate_id, path_ids, a tuple built from physical, a tuple
    # built from the sorted values from...).
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _classify(self, chosen):
        # Set path_ids to a tuple built from a lazy sequence of item.path_id for item in chosen.
        path_ids = tuple(item.path_id for item in chosen)
        # Set (physical, edges, unresolved) to a tuple containing an empty list, an empty set, False.
        physical, edges, unresolved = [], set(), False
        # Iterate over the result of combinations(chosen, 2), binding each item to (first, second).
        for first, second in combinations(chosen, 2):
            # Set relationship to the result of self.zones.relationship(first.path_id, second.path_id).
            relationship = self.zones.relationship(first.path_id, second.path_id)
            # Run this branch when the negation of relationship.coordinated_conflict.
            if not relationship.coordinated_conflict:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Append a tuple containing first.path_id, second.path_id, relationship.conflict_zone_id,
            # relationship.conflict_type to physical.
            physical.append((first.path_id, second.path_id,
                             # Include relationship.conflict_zone_id in this tuple.
                             relationship.conflict_zone_id,
                             # Include relationship.conflict_type in this tuple.
                             relationship.conflict_type))
            # Set pair to an empty list.
            pair = []
            # Iterate over a tuple containing a tuple containing first, second, a tuple containing second, first,
            # binding each item to (ego, target).
            for ego, target in ((first, second), (second, first)):
                # Set result to the result of self.rules._evaluate_candidate(ego, target).
                result = self.rules._evaluate_candidate(ego, target)
                # Append result at 'regulatory_status' to pair.
                pair.append(result["regulatory_status"])
                # Run this branch when result at 'regulatory_status' equals the text 'EGO_MUST_YIELD'.
                if result["regulatory_status"] == "EGO_MUST_YIELD":
                    # Add a tuple containing ego.path_id, target.path_id to edges.
                    edges.add((ego.path_id, target.path_id))
            # Update unresolved to its current value combined with the number of entries in a set built from pair
            # equals 0.
            unresolved |= len(set(pair)) == 0
        # Set edge_dicts to a tuple built from a lazy sequence of a dictionary containing yielding_vehicle_id,
        # priority_vehicle_id for (source, target) in the sorted values from edges.
        edge_dicts = tuple({"yielding_vehicle_id": source,
                            # Store target under 'priority_vehicle_id'.
                            "priority_vehicle_id": target}
                           # Evaluate a tuple containing source, target as part of the enclosing expression.
                           for source, target in sorted(edges))
        # Set analysis to the result of RegulatoryPrecedenceGraphBuilder.analyse(path_ids, edge_dicts).
        analysis = RegulatoryPrecedenceGraphBuilder.analyse(path_ids, edge_dicts)
        # Run this branch when the negation of physical.
        if not physical:
            # Set status to NegotiationStatus.NO_ACTIVE_CONFLICT.value.
            status = NegotiationStatus.NO_ACTIVE_CONFLICT.value
            # Set (result, rejection) to a tuple containing the text 'REJECTED', the text
            # 'NO_PHYSICAL_COORDINATED_CONFLICT'.
            result, rejection = "REJECTED", "NO_PHYSICAL_COORDINATED_CONFLICT"
        # Run this branch when unresolved.
        elif unresolved:
            # Set status to NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value.
            status = NegotiationStatus.NEGOTIATION_REQUIRED_UNRESOLVED_PRECEDENCE.value
            # Set (result, rejection) to a tuple containing the text 'RETAINED', None.
            result, rejection = "RETAINED", None
        # Run this branch when analysis at 'cycle_detected'.
        elif analysis["cycle_detected"]:
            # Set status to NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value.
            status = NegotiationStatus.NEGOTIATION_REQUIRED_REGULATORY_CYCLE.value
            # Set (result, rejection) to a tuple containing the text 'RETAINED', None.
            result, rejection = "RETAINED", None
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set status to NegotiationStatus.REGULATORY_ORDER_RESOLVED.value.
            status = NegotiationStatus.REGULATORY_ORDER_RESOLVED.value
            # Set (result, rejection) to a tuple containing the text 'REJECTED', the text
            # 'REGULATORY_ORDER_ACYCLIC'.
            result, rejection = "REJECTED", "REGULATORY_ORDER_ACYCLIC"
        # Set candidate_id to a tuple containing the text 'MAP_RULE_CANDIDATE', path_ids.
        candidate_id = ("MAP_RULE_CANDIDATE", path_ids)
        # Return the result of ScenarioDiscoveryRecord(candidate_id, path_ids, a tuple built from physical, a
        # tuple built from the sorted values from...) to the caller.
        return ScenarioDiscoveryRecord(
            # Supply a tuple built from the sorted values from edges to ScenarioDiscoveryRecord.
            candidate_id, path_ids, tuple(physical), tuple(sorted(edges)),
            # Supply analysis at 'strongly_connected_components' to ScenarioDiscoveryRecord.
            analysis["strongly_connected_components"], status, result, rejection,
            # Store the text 'MAP_PATH_MANAGER' under 'path_source'.
            {"path_source": "MAP_PATH_MANAGER",
             "geometry_source": "CONFLICT_ZONE_MANAGER",
             "rule_source": "TRAFFIC_RULE_ENGINE",
             "topology_source": "REGULATORY_PRECEDENCE_GRAPH_BUILDER"},
        )
