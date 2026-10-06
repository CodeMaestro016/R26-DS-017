"""Regulatory yield-dependency graph construction and graph algorithms."""

import heapq

from .message_models import PrecedenceClaimMessage


class RegulatoryPrecedenceGraphBuilder:
    """Build directed yield obligations from one ego's local evidence.

    Edge convention is invariant: ``A -> B`` means A has a regulatory
    obligation to yield to B. Vehicle IDs break ties only for deterministic
    serialization of mathematically equivalent graph results; they never
    establish legal priority.
    """

    UNRESOLVED = frozenset({
        "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE",
        "REGULATORY_INPUT_UNRESOLVED",
    })

    @staticmethod
    def _candidate_path_ids(edge):
        return tuple(sorted({
            path_id
            for value in edge.get("spatially_conflicting_candidate_paths", {}).values()
            for path_id in ((value,) if isinstance(value, str) else value)
        }))

    def build(self, ldm):
        conflict = ldm.get_current_conflict_graph() or {}
        temporal = ldm.get_current_temporal_assessment() or {}
        regulatory = ldm.get_current_regulatory_assessment() or {}
        regulatory_by_target = {
            item.get("target_id"): item for item in regulatory.get("assessments", ())
        }
        temporal_by_target = {
            item.get("target_id"): item for item in temporal.get("edges", ())
        }
        nodes = {ldm.ego_id}
        edges, unresolved = [], []
        for conflict_edge in conflict.get("edges", ()):
            if not conflict_edge.get("spatially_conflicting_candidate_paths"):
                continue
            target_id = conflict_edge.get("target_track_id")
            if target_id not in ldm.tracks:
                continue
            nodes.add(target_id)
            rule = regulatory_by_target.get(target_id)
            if rule is None:
                unresolved.append(self._unresolved_record(
                    ldm.ego_id, target_id, "REGULATORY_INPUT_UNRESOLVED",
                    conflict_edge, temporal_by_target.get(target_id), None,
                ))
                continue
            status = rule.get("regulatory_status")
            if status in self.UNRESOLVED:
                unresolved.append(self._unresolved_record(
                    ldm.ego_id, target_id, status, conflict_edge,
                    temporal_by_target.get(target_id), rule,
                ))
                continue
            if status == "NO_PAIRWISE_PRECEDENCE_RULE":
                continue
            if status == "EGO_MUST_YIELD":
                yielding, priority = ldm.ego_id, target_id
            elif status == "EGO_HAS_PRECEDENCE_UNDER_RULE":
                yielding, priority = target_id, ldm.ego_id
            else:
                unresolved.append(self._unresolved_record(
                    ldm.ego_id, target_id, "REGULATORY_INPUT_UNRESOLVED",
                    conflict_edge, temporal_by_target.get(target_id), rule,
                ))
                continue
            edges.append(self._edge_record(
                yielding, priority, conflict_edge,
                temporal_by_target.get(target_id), rule,
            ))
        edges = tuple(sorted(edges, key=lambda item: (
            item["yielding_vehicle_id"], item["priority_vehicle_id"])))
        analysis = self.analyse(tuple(sorted(nodes)), edges)
        return {
            "node_ids": tuple(sorted(nodes)), "precedence_edges": edges,
            "unresolved_relations": tuple(sorted(
                unresolved, key=lambda item: (item["ego_id"], item["target_id"])
            )), **analysis,
        }

    @staticmethod
    def claim_messages(ldm, local_graph, current_time):
        """Publish only precedence edges derived from this sender's own LDM."""
        conflict = ldm.get_current_conflict_graph() or {}
        regulatory = ldm.get_current_regulatory_assessment() or {}
        return tuple(PrecedenceClaimMessage(
            sender_id=ldm.ego_id,
            timestamp=float(current_time),
            yielding_vehicle_id=edge["yielding_vehicle_id"],
            priority_vehicle_id=edge["priority_vehicle_id"],
            applicable_rule_ids=tuple(edge.get("applicable_rule_ids", ())),
            source_sections=tuple(edge.get("source_sections", ())),
            regulatory_profile=edge.get("regulatory_profile"),
            shared_conflict_zone_ids=tuple(edge.get("shared_conflict_zone_ids", ())),
            conflict_types=tuple(edge.get("conflict_types", ())),
            target_candidate_path_ids=tuple(edge.get("target_candidate_path_ids", ())),
            source_conflict_graph_timestamp=float(conflict["timestamp"]),
            source_regulatory_assessment_timestamp=float(regulatory["timestamp"]),
            source_observation_age_seconds=edge.get("source_observation_age_seconds"),
        ) for edge in local_graph["precedence_edges"])

    @classmethod
    def _edge_record(cls, yielding, priority, conflict, temporal, rule):
        candidates = tuple(rule.get("candidate_assessments", ()))
        return {
            "yielding_vehicle_id": yielding,
            "priority_vehicle_id": priority,
            "applicable_rule_ids": tuple(rule.get("applicable_rule_ids", ())),
            "source_sections": tuple(rule.get("source_sections", ())),
            "regulatory_profile": rule.get("regulatory_profile"),
            "target_candidate_path_ids": cls._candidate_path_ids(conflict),
            "relative_approaches": tuple(sorted({
                item.get("relative_approach") for item in candidates
                if item.get("relative_approach") is not None
            })),
            "timestamp": rule.get("timestamp"),
            "shared_conflict_zone_ids": tuple(conflict.get("shared_conflict_zone_ids", ())),
            "conflict_types": tuple(conflict.get("conflict_types", ())),
            "spatial_conflict_possible": bool(conflict.get("spatial_conflict_possible")),
            "hard_constraint_evidence": {
                "mandatory_regulatory_yield": True,
                "physical_candidate_conflict": True,
            },
            "physical_reachability_evidence": cls._reachability(temporal),
            "source_observation_age_seconds": conflict.get("observation_age_seconds"),
        }

    @classmethod
    def _unresolved_record(cls, ego, target, status, conflict, temporal, rule):
        return {
            "ego_id": ego, "target_id": target, "regulatory_status": status,
            "target_candidate_path_ids": cls._candidate_path_ids(conflict),
            "shared_conflict_zone_ids": tuple(conflict.get("shared_conflict_zone_ids", ())),
            "conflict_types": tuple(conflict.get("conflict_types", ())),
            "regulatory_evidence": rule,
            "physical_reachability_evidence": cls._reachability(temporal),
        }

    @staticmethod
    def _reachability(temporal):
        if not temporal:
            return None
        fields = (
            "status", "temporal_conflict_possible", "evaluations",
        )
        return {name: temporal.get(name) for name in fields}

    @classmethod
    def analyse(cls, node_ids, edges):
        adjacency = {node: set() for node in node_ids}
        for edge in edges:
            adjacency.setdefault(edge["yielding_vehicle_id"], set()).add(
                edge["priority_vehicle_id"]
            )
            adjacency.setdefault(edge["priority_vehicle_id"], set())
        components = cls._strongly_connected_components(adjacency)
        cyclic = tuple(component for component in components if len(component) > 1)
        cycle_members = tuple(sorted({node for component in cyclic for node in component}))
        topological = None if cyclic else cls._topological_order(adjacency)
        return {
            "cycle_detected": bool(cyclic), "cycle_members": cycle_members,
            "strongly_connected_components": cyclic,
            "yield_precedence_graph_topological_order": topological,
            # A -> B means A yields to B, so crossing/service dependencies are
            # satisfied in the reverse of the normal topological sequence.
            "regulatory_service_order": (
                tuple(reversed(topological)) if topological is not None else None
            ),
        }

    @staticmethod
    def _topological_order(adjacency):
        indegree = {node: 0 for node in adjacency}
        for targets in adjacency.values():
            for target in targets:
                indegree[target] += 1
        ready = [node for node, degree in indegree.items() if degree == 0]
        heapq.heapify(ready)
        result = []
        while ready:
            node = heapq.heappop(ready)
            result.append(node)
            for target in sorted(adjacency[node]):
                indegree[target] -= 1
                if indegree[target] == 0:
                    heapq.heappush(ready, target)
        return tuple(result)

    @staticmethod
    def _strongly_connected_components(adjacency):
        index = 0
        indices, lowlinks, stack, on_stack, components = {}, {}, [], set(), []

        def visit(node):
            nonlocal index
            indices[node] = lowlinks[node] = index
            index += 1
            stack.append(node)
            on_stack.add(node)
            for target in sorted(adjacency[node]):
                if target not in indices:
                    visit(target)
                    lowlinks[node] = min(lowlinks[node], lowlinks[target])
                elif target in on_stack:
                    lowlinks[node] = min(lowlinks[node], indices[target])
            if lowlinks[node] == indices[node]:
                component = []
                while True:
                    member = stack.pop()
                    on_stack.remove(member)
                    component.append(member)
                    if member == node:
                        break
                components.append(tuple(sorted(component)))

        for node in sorted(adjacency):
            if node not in indices:
                visit(node)
        return tuple(sorted(components))
