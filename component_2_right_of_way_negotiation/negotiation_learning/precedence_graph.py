"""Regulatory yield-dependency graph construction and graph algorithms."""

# Import heapq for use in this module.
import heapq

# Import PrecedenceClaimMessage from .message_models for the operations below.
from .message_models import PrecedenceClaimMessage


# Build directed yield obligations from one ego's local evidence.
# Instances expose the attributes and methods implemented in this class.
class RegulatoryPrecedenceGraphBuilder:
    """Build directed yield obligations from one ego's local evidence.

    Edge convention is invariant: ``A -> B`` means A has a regulatory
    obligation to yield to B. Vehicle IDs break ties only for deterministic
    serialization of mathematically equivalent graph results; they never
    establish legal priority.
    """

    # Set UNRESOLVED to an immutable set built from a set containing the text
    # 'UNRESOLVED_DUE_TO_TARGET_MANOEUVRE', the text 'REGULATORY_INPUT_UNRESOLVED'.
    UNRESOLVED = frozenset({
        "UNRESOLVED_DUE_TO_TARGET_MANOEUVRE",
        "REGULATORY_INPUT_UNRESOLVED",
    })

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Candidate path ids using the inputs and processing steps below.
    # Input edge: the supplied edge.
    # Output: a tuple built from the sorted values from a set of path_id for value in values from
    # edge.get('spatially_conflicting_candidate_paths', {}).
    def _candidate_path_ids(edge):
        # Return a tuple built from the sorted values from a set of path_id for value in values from
        # edge.get('spatially_conflicting_candidate_paths', {}) to the caller.
        return tuple(sorted({
            # Evaluate path_id as part of the enclosing expression.
            path_id
            # Evaluate values from edge.get('spatially_conflicting_candidate_paths', {}) as part of the enclosing
            # expression.
            for value in edge.get("spatially_conflicting_candidate_paths", {}).values()
            # Evaluate a tuple containing value when whether value has type str, otherwise value as part of the
            # enclosing expression.
            for path_id in ((value,) if isinstance(value, str) else value)
        }))

    # Build using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Output: a dictionary containing node_ids, precedence_edges, unresolved_relations.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def build(self, ldm):
        # Set conflict to the result of ldm.get_current_conflict_graph() or an empty dictionary.
        conflict = ldm.get_current_conflict_graph() or {}
        # Set temporal to the result of ldm.get_current_temporal_assessment() or an empty dictionary.
        temporal = ldm.get_current_temporal_assessment() or {}
        # Set regulatory to the result of ldm.get_current_regulatory_assessment() or an empty dictionary.
        regulatory = ldm.get_current_regulatory_assessment() or {}
        # Set regulatory_by_target to a dictionary of 'target_id' from item; use None if absent mapped to item for
        # item in 'assessments' from regulatory; use an empty tuple if absent.
        regulatory_by_target = {
            # Evaluate 'assessments' from regulatory; use an empty tuple if absent as part of the enclosing
            # expression.
            item.get("target_id"): item for item in regulatory.get("assessments", ())
        }
        # Set temporal_by_target to a dictionary of 'target_id' from item; use None if absent mapped to item for
        # item in 'edges' from temporal; use an empty tuple if absent.
        temporal_by_target = {
            # Evaluate 'edges' from temporal; use an empty tuple if absent as part of the enclosing expression.
            item.get("target_id"): item for item in temporal.get("edges", ())
        }
        # Set nodes to a set containing ldm.ego_id.
        nodes = {ldm.ego_id}
        # Set (edges, unresolved) to a tuple containing an empty list, an empty list.
        edges, unresolved = [], []
        # Iterate over 'edges' from conflict; use an empty tuple if absent, binding each item to conflict_edge.
        for conflict_edge in conflict.get("edges", ()):
            # Run this branch when the negation of 'spatially_conflicting_candidate_paths' from conflict_edge; use
            # None if absent.
            if not conflict_edge.get("spatially_conflicting_candidate_paths"):
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set target_id to 'target_track_id' from conflict_edge; use None if absent.
            target_id = conflict_edge.get("target_track_id")
            # Run this branch when target_id does not belong to ldm.tracks.
            if target_id not in ldm.tracks:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Add target_id to nodes.
            nodes.add(target_id)
            # Set rule to target_id from regulatory_by_target; use None if absent.
            rule = regulatory_by_target.get(target_id)
            # Run this branch when rule is the same object as None.
            if rule is None:
                # Append the result of self._unresolved_record(ldm.ego_id, target_id, the text
                # 'REGULATORY_INPUT_UNRESOLVED', conflict_edge, target_id from...) to unresolved.
                unresolved.append(self._unresolved_record(
                    # Supply ldm.ego_id to self._unresolved_record.
                    ldm.ego_id, target_id, "REGULATORY_INPUT_UNRESOLVED",
                    # Supply target_id from temporal_by_target; use None if absent to self._unresolved_record.
                    conflict_edge, temporal_by_target.get(target_id), None,
                ))
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set status to 'regulatory_status' from rule; use None if absent.
            status = rule.get("regulatory_status")
            # Run this branch when status belongs to self.UNRESOLVED.
            if status in self.UNRESOLVED:
                # Append the result of self._unresolved_record(ldm.ego_id, target_id, status, conflict_edge,
                # target_id from temporal_by_target; use None if...) to unresolved.
                unresolved.append(self._unresolved_record(
                    # Supply conflict_edge to self._unresolved_record.
                    ldm.ego_id, target_id, status, conflict_edge,
                    # Supply target_id from temporal_by_target; use None if absent to self._unresolved_record.
                    temporal_by_target.get(target_id), rule,
                ))
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when status equals the text 'NO_PAIRWISE_PRECEDENCE_RULE'.
            if status == "NO_PAIRWISE_PRECEDENCE_RULE":
                # Run this branch when 'execution_interpretation' from regulatory; use None if absent equals the
                # text 'EGO_LOCAL_V2'.
                if regulatory.get("execution_interpretation") == "EGO_LOCAL_V2":
                    # Mutual voluntary admission claims, not legal priority.
                    # Set record to the result of self._edge_record(ldm.ego_id, target_id, conflict_edge,
                    # target_id from temporal_by_target; use None if absent, rule).
                    record = self._edge_record(ldm.ego_id, target_id, conflict_edge,
                        # Supply target_id from temporal_by_target; use None if absent to self._edge_record.
                        temporal_by_target.get(target_id), rule)
                    # Update record with the supplied entries.
                    record.update(applicable_rule_ids=("DE-STVO-11-3",),
                        # Supply source_sections as a tuple containing the text '§ 11'.
                        # Supply hard_constraint_evidence as a dictionary containing mandatory_regulatory_yield,
                        # physical_candidate_conflict, negotiation_eligible_ambiguity.
                        source_sections=("§ 11",), hard_constraint_evidence={
                            # Store False under 'mandatory_regulatory_yield'.
                            "mandatory_regulatory_yield": False,
                            # Store True under 'physical_candidate_conflict'.
                            "physical_candidate_conflict": True,
                            # Store True under 'negotiation_eligible_ambiguity'.
                            "negotiation_eligible_ambiguity": True})
                    # Append record to edges.
                    edges.append(record)
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when status equals the text 'EGO_MUST_YIELD'.
            if status == "EGO_MUST_YIELD":
                # Set (yielding, priority) to a tuple containing ldm.ego_id, target_id.
                yielding, priority = ldm.ego_id, target_id
            # Run this branch when status equals the text 'EGO_HAS_PRECEDENCE_UNDER_RULE'.
            elif status == "EGO_HAS_PRECEDENCE_UNDER_RULE":
                # Set (yielding, priority) to a tuple containing target_id, ldm.ego_id.
                yielding, priority = target_id, ldm.ego_id
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Append the result of self._unresolved_record(ldm.ego_id, target_id, the text
                # 'REGULATORY_INPUT_UNRESOLVED', conflict_edge, target_id from...) to unresolved.
                unresolved.append(self._unresolved_record(
                    # Supply ldm.ego_id to self._unresolved_record.
                    ldm.ego_id, target_id, "REGULATORY_INPUT_UNRESOLVED",
                    # Supply target_id from temporal_by_target; use None if absent to self._unresolved_record.
                    conflict_edge, temporal_by_target.get(target_id), rule,
                ))
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Append the result of self._edge_record(yielding, priority, conflict_edge, target_id from
            # temporal_by_target; use None if absent, rule) to edges.
            edges.append(self._edge_record(
                # Supply conflict_edge to self._edge_record.
                yielding, priority, conflict_edge,
                # Supply target_id from temporal_by_target; use None if absent to self._edge_record.
                temporal_by_target.get(target_id), rule,
            ))
        # Set edges to a tuple built from the sorted values from edges.
        edges = tuple(sorted(edges, key=lambda item: (
            # Include item at 'yielding_vehicle_id' in this tuple.
            item["yielding_vehicle_id"], item["priority_vehicle_id"])))
        # Set analysis to the result of self.analyse(a tuple built from the sorted values from nodes, edges).
        analysis = self.analyse(tuple(sorted(nodes)), edges)
        # Return a dictionary containing node_ids, precedence_edges, unresolved_relations to the caller.
        return {
            # Store a tuple built from the sorted values from nodes under 'node_ids'.
            # Store edges under 'precedence_edges'.
            "node_ids": tuple(sorted(nodes)), "precedence_edges": edges,
            # Store a tuple built from the sorted values from unresolved under 'unresolved_relations'.
            "unresolved_relations": tuple(sorted(
                # Declare item as input parameter.
                unresolved, key=lambda item: (item["ego_id"], item["target_id"])
            # Evaluate analysis as part of the enclosing expression.
            )), **analysis,
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Publish only precedence edges derived from this sender's own LDM.
    # Input ldm: the supplied ldm.
    # Input local_graph: the supplied local graph.
    # Input current_time: the supplied current time.
    # Output: a tuple built from a lazy sequence of the result of PrecedenceClaimMessage() for edge in local_graph
    # at 'precedence_edges'.
    def claim_messages(ldm, local_graph, current_time):
        """Publish only precedence edges derived from this sender's own LDM."""
        # Set conflict to the result of ldm.get_current_conflict_graph() or an empty dictionary.
        conflict = ldm.get_current_conflict_graph() or {}
        # Set regulatory to the result of ldm.get_current_regulatory_assessment() or an empty dictionary.
        regulatory = ldm.get_current_regulatory_assessment() or {}
        # Return a tuple built from a lazy sequence of the result of PrecedenceClaimMessage() for edge in
        # local_graph at 'precedence_edges' to the caller.
        return tuple(PrecedenceClaimMessage(
            # Supply sender_id as ldm.ego_id.
            sender_id=ldm.ego_id,
            # Supply timestamp as a floating-point number built from current_time.
            timestamp=float(current_time),
            # Supply yielding_vehicle_id as edge at 'yielding_vehicle_id'.
            yielding_vehicle_id=edge["yielding_vehicle_id"],
            # Supply priority_vehicle_id as edge at 'priority_vehicle_id'.
            priority_vehicle_id=edge["priority_vehicle_id"],
            # Supply applicable_rule_ids as a tuple built from 'applicable_rule_ids' from edge; use an empty tuple
            # if absent.
            applicable_rule_ids=tuple(edge.get("applicable_rule_ids", ())),
            # Supply source_sections as a tuple built from 'source_sections' from edge; use an empty tuple if
            # absent.
            source_sections=tuple(edge.get("source_sections", ())),
            # Supply regulatory_profile as 'regulatory_profile' from edge; use None if absent.
            regulatory_profile=edge.get("regulatory_profile"),
            # Supply shared_conflict_zone_ids as a tuple built from 'shared_conflict_zone_ids' from edge; use an
            # empty tuple if absent.
            shared_conflict_zone_ids=tuple(edge.get("shared_conflict_zone_ids", ())),
            # Supply conflict_types as a tuple built from 'conflict_types' from edge; use an empty tuple if
            # absent.
            conflict_types=tuple(edge.get("conflict_types", ())),
            # Supply target_candidate_path_ids as a tuple built from 'target_candidate_path_ids' from edge; use an
            # empty tuple if absent.
            target_candidate_path_ids=tuple(edge.get("target_candidate_path_ids", ())),
            # Supply source_conflict_graph_timestamp as a floating-point number built from conflict at
            # 'timestamp'.
            source_conflict_graph_timestamp=float(conflict["timestamp"]),
            # Supply source_regulatory_assessment_timestamp as a floating-point number built from regulatory at
            # 'timestamp'.
            source_regulatory_assessment_timestamp=float(regulatory["timestamp"]),
            # Supply source_observation_age_seconds as 'source_observation_age_seconds' from edge; use None if
            # absent.
            source_observation_age_seconds=edge.get("source_observation_age_seconds"),
            # Supply negotiation_eligible_ambiguity as a Boolean built from 'negotiation_eligible_ambiguity' from
            # edge.get('hard_constraint_evidence', {}); use False if absent.
            negotiation_eligible_ambiguity=bool(edge.get("hard_constraint_evidence", {}).get(
                # Supply the text 'negotiation_eligible_ambiguity' to the enclosing expression.
                "negotiation_eligible_ambiguity", False)),
        # Evaluate local_graph at 'precedence_edges' as part of the enclosing expression.
        ) for edge in local_graph["precedence_edges"])

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Edge record using the inputs and processing steps below.
    # Input yielding: the supplied yielding.
    # Input priority: the supplied priority.
    # Input conflict: the supplied conflict.
    # Input temporal: the supplied temporal.
    # Input rule: the supplied rule.
    # Output: a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
    # source_sections,...
    def _edge_record(cls, yielding, priority, conflict, temporal, rule):
        # Set candidates to a tuple built from 'candidate_assessments' from rule; use an empty tuple if absent.
        candidates = tuple(rule.get("candidate_assessments", ()))
        # Return a dictionary containing yielding_vehicle_id, priority_vehicle_id, applicable_rule_ids,
        # source_sections,... to the caller.
        return {
            # Store yielding under 'yielding_vehicle_id'.
            "yielding_vehicle_id": yielding,
            # Store priority under 'priority_vehicle_id'.
            "priority_vehicle_id": priority,
            # Store a tuple built from 'applicable_rule_ids' from rule; use an empty tuple if absent under
            # 'applicable_rule_ids'.
            "applicable_rule_ids": tuple(rule.get("applicable_rule_ids", ())),
            # Store a tuple built from 'source_sections' from rule; use an empty tuple if absent under
            # 'source_sections'.
            "source_sections": tuple(rule.get("source_sections", ())),
            # Store 'regulatory_profile' from rule; use None if absent under 'regulatory_profile'.
            "regulatory_profile": rule.get("regulatory_profile"),
            # Store the result of cls._candidate_path_ids(conflict) under 'target_candidate_path_ids'.
            "target_candidate_path_ids": cls._candidate_path_ids(conflict),
            # Store a tuple built from the sorted values from a set of 'relative_approach' from item; use None if
            # absent for item in candidates; retain entries satisfying item.get('relative_approach') is a
            # different object from None under 'relative_approaches'.
            "relative_approaches": tuple(sorted({
                # Evaluate 'relative_approach' from item; use None if absent as part of the enclosing expression.
                item.get("relative_approach") for item in candidates
                # Evaluate 'relative_approach' from item; use None if absent is a different object from None as
                # part of the enclosing expression.
                if item.get("relative_approach") is not None
            })),
            # Store 'timestamp' from rule; use None if absent under 'timestamp'.
            "timestamp": rule.get("timestamp"),
            # Store a tuple built from 'shared_conflict_zone_ids' from conflict; use an empty tuple if absent
            # under 'shared_conflict_zone_ids'.
            "shared_conflict_zone_ids": tuple(conflict.get("shared_conflict_zone_ids", ())),
            # Store a tuple built from 'conflict_types' from conflict; use an empty tuple if absent under
            # 'conflict_types'.
            "conflict_types": tuple(conflict.get("conflict_types", ())),
            # Store a Boolean built from 'spatial_conflict_possible' from conflict; use None if absent under
            # 'spatial_conflict_possible'.
            "spatial_conflict_possible": bool(conflict.get("spatial_conflict_possible")),
            # Store a dictionary containing mandatory_regulatory_yield, physical_candidate_conflict under
            # 'hard_constraint_evidence'.
            "hard_constraint_evidence": {
                # Store True under 'mandatory_regulatory_yield'.
                "mandatory_regulatory_yield": True,
                # Store True under 'physical_candidate_conflict'.
                "physical_candidate_conflict": True,
            },
            # Store the result of cls._reachability(temporal) under 'physical_reachability_evidence'.
            "physical_reachability_evidence": cls._reachability(temporal),
            # Store 'observation_age_seconds' from conflict; use None if absent under
            # 'source_observation_age_seconds'.
            "source_observation_age_seconds": conflict.get("observation_age_seconds"),
        }

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Unresolved record using the inputs and processing steps below.
    # Input ego: the ego vehicle used in this calculation.
    # Input target: the supplied target.
    # Input status: the supplied status.
    # Input conflict: the supplied conflict.
    # Input temporal: the supplied temporal.
    # Input rule: the supplied rule.
    # Output: a dictionary containing ego_id, target_id, regulatory_status, target_candidate_path_ids,...
    def _unresolved_record(cls, ego, target, status, conflict, temporal, rule):
        # Return a dictionary containing ego_id, target_id, regulatory_status, target_candidate_path_ids,... to
        # the caller.
        return {
            # Store ego under 'ego_id'.
            # Store target under 'target_id'.
            # Store status under 'regulatory_status'.
            "ego_id": ego, "target_id": target, "regulatory_status": status,
            # Store the result of cls._candidate_path_ids(conflict) under 'target_candidate_path_ids'.
            "target_candidate_path_ids": cls._candidate_path_ids(conflict),
            # Store a tuple built from 'shared_conflict_zone_ids' from conflict; use an empty tuple if absent
            # under 'shared_conflict_zone_ids'.
            "shared_conflict_zone_ids": tuple(conflict.get("shared_conflict_zone_ids", ())),
            # Store a tuple built from 'conflict_types' from conflict; use an empty tuple if absent under
            # 'conflict_types'.
            "conflict_types": tuple(conflict.get("conflict_types", ())),
            # Store rule under 'regulatory_evidence'.
            "regulatory_evidence": rule,
            # Store the result of cls._reachability(temporal) under 'physical_reachability_evidence'.
            "physical_reachability_evidence": cls._reachability(temporal),
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Reachability using the inputs and processing steps below.
    # Input temporal: the supplied temporal.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _reachability(temporal):
        # Run this branch when the negation of temporal.
        if not temporal:
            # Return None to the caller.
            return None
        # Set fields to a tuple containing the text 'status', the text 'temporal_conflict_possible', the text
        # 'evaluations'.
        fields = (
            "status", "temporal_conflict_possible", "evaluations",
        )
        # Return a dictionary of name mapped to name from temporal; use None if absent for name in fields to the
        # caller.
        return {name: temporal.get(name) for name in fields}

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Analyse using the inputs and processing steps below.
    # Input node_ids: the supplied node ids.
    # Input edges: the supplied edges.
    # Output: a dictionary containing cycle_detected, cycle_members, strongly_connected_components,...
    # Processing: iterate over the relevant records.
    def analyse(cls, node_ids, edges):
        # Set adjacency to a dictionary of node mapped to an empty set for node in node_ids.
        adjacency = {node: set() for node in node_ids}
        # Iterate over edges, binding each item to edge.
        for edge in edges:
            # Add edge at 'priority_vehicle_id' to adjacency.setdefault(edge['yielding_vehicle_id'], set()).
            adjacency.setdefault(edge["yielding_vehicle_id"], set()).add(
                # Supply edge at 'priority_vehicle_id' to adjacency.setdefault(edge['yielding_vehicle_id'],
                # set()).add.
                edge["priority_vehicle_id"]
            )
            # Call adjacency.setdefault with the supplied arguments.
            adjacency.setdefault(edge["priority_vehicle_id"], set())
        # Set components to the result of cls._strongly_connected_components(adjacency).
        components = cls._strongly_connected_components(adjacency)
        # Set cyclic to a tuple built from a lazy sequence of component for component in components; retain
        # entries satisfying the number of entries in component is greater than 1.
        cyclic = tuple(component for component in components if len(component) > 1)
        # Set cycle_members to a tuple built from the sorted values from a set of node for component in cyclic.
        cycle_members = tuple(sorted({node for component in cyclic for node in component}))
        # Set topological to None when cyclic, otherwise the result of cls._topological_order(adjacency).
        topological = None if cyclic else cls._topological_order(adjacency)
        # Return a dictionary containing cycle_detected, cycle_members, strongly_connected_components,... to the
        # caller.
        return {
            # Store a Boolean built from cyclic under 'cycle_detected'.
            # Store cycle_members under 'cycle_members'.
            "cycle_detected": bool(cyclic), "cycle_members": cycle_members,
            # Store cyclic under 'strongly_connected_components'.
            "strongly_connected_components": cyclic,
            # Store topological under 'yield_precedence_graph_topological_order'.
            "yield_precedence_graph_topological_order": topological,
            # A -> B means A yields to B, so crossing/service dependencies are
            # satisfied in the reverse of the normal topological sequence.
            # Store a tuple built from the reverse traversal of topological when topological is a different object
            # from None, otherwise None under 'regulatory_service_order'.
            "regulatory_service_order": (
                # Evaluate a tuple built from the reverse traversal of topological when topological is a different
                # object from None, otherwise None as part of the enclosing expression.
                tuple(reversed(topological)) if topological is not None else None
            ),
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Topological order using the inputs and processing steps below.
    # Input adjacency: the supplied adjacency.
    # Output: a tuple built from result.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _topological_order(adjacency):
        # Set indegree to a dictionary of node mapped to 0 for node in adjacency.
        indegree = {node: 0 for node in adjacency}
        # Iterate over values from adjacency, binding each item to targets.
        for targets in adjacency.values():
            # Iterate over targets, binding each item to target.
            for target in targets:
                # Update indegree[target] to its current value plus 1.
                indegree[target] += 1
        # Set ready to a list of node for (node, degree) in key/value pairs from indegree; retain entries
        # satisfying degree equals 0.
        ready = [node for node, degree in indegree.items() if degree == 0]
        # Call heapq.heapify with the supplied arguments.
        heapq.heapify(ready)
        # Set result to an empty list.
        result = []
        # Repeat the following steps while ready.
        while ready:
            # Set node to the result of heapq.heappop(ready).
            node = heapq.heappop(ready)
            # Append node to result.
            result.append(node)
            # Iterate over the sorted values from adjacency at node, binding each item to target.
            for target in sorted(adjacency[node]):
                # Update indegree[target] to its current value minus 1.
                indegree[target] -= 1
                # Run this branch when indegree at target equals 0.
                if indegree[target] == 0:
                    # Call heapq.heappush with the supplied arguments.
                    heapq.heappush(ready, target)
        # Return a tuple built from result to the caller.
        return tuple(result)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Strongly connected components using the inputs and processing steps below.
    # Input adjacency: the supplied adjacency.
    # Output: a tuple built from the sorted values from components.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _strongly_connected_components(adjacency):
        # Set index to 0.
        index = 0
        # Set (indices, lowlinks, stack, on_stack, components) to a tuple containing an empty dictionary, an empty
        # dictionary, an empty list, an empty set, an empty list.
        indices, lowlinks, stack, on_stack, components = {}, {}, [], set(), []

        # Visit using the inputs and processing steps below.
        # Input node: the supplied node.
        # Output: no explicit value; normal completion returns None.
        # Processing: iterate over the relevant records, then select branches using the stated conditions.
        def visit(node):
            # Bind index in the enclosing function scope.
            nonlocal index
            # Set indices[node] and lowlinks[node] to index.
            indices[node] = lowlinks[node] = index
            # Update index to its current value plus 1.
            index += 1
            # Append node to stack.
            stack.append(node)
            # Add node to on_stack.
            on_stack.add(node)
            # Iterate over the sorted values from adjacency at node, binding each item to target.
            for target in sorted(adjacency[node]):
                # Run this branch when target does not belong to indices.
                if target not in indices:
                    # Call visit with the supplied arguments.
                    visit(target)
                    # Set lowlinks[node] to the minimum of lowlinks at node, lowlinks at target.
                    lowlinks[node] = min(lowlinks[node], lowlinks[target])
                # Run this branch when target belongs to on_stack.
                elif target in on_stack:
                    # Set lowlinks[node] to the minimum of lowlinks at node, indices at target.
                    lowlinks[node] = min(lowlinks[node], indices[target])
            # Run this branch when lowlinks at node equals indices at node.
            if lowlinks[node] == indices[node]:
                # Set component to an empty list.
                component = []
                # Repeat the following steps while True.
                while True:
                    # Set member to the result of stack.pop().
                    member = stack.pop()
                    # Remove member from on_stack.
                    on_stack.remove(member)
                    # Append member to component.
                    component.append(member)
                    # Run this branch when member equals node.
                    if member == node:
                        # Leave the nearest enclosing loop immediately.
                        break
                # Append a tuple built from the sorted values from component to components.
                components.append(tuple(sorted(component)))

        # Iterate over the sorted values from adjacency, binding each item to node.
        for node in sorted(adjacency):
            # Run this branch when node does not belong to indices.
            if node not in indices:
                # Call visit with the supplied arguments.
                visit(node)
        # Return a tuple built from the sorted values from components to the caller.
        return tuple(sorted(components))
