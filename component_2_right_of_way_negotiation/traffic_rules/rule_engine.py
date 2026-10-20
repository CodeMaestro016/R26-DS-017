"""Source-traceable German StVO rules for the constrained research ODD."""

# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Import RegulatoryContext from .regulatory_context for the operations below.
from .regulatory_context import RegulatoryContext
# Import RegulatoryAssessment, RegulatoryStatus, RuleRecord from .rule_models for the operations below.
from .rule_models import RegulatoryAssessment, RegulatoryStatus, RuleRecord


# Evaluate local candidate paths without route truth or probabilities.
# Instances expose the attributes and methods implemented in this class.
class TrafficRuleEngine:
    """Evaluate local candidate paths without route truth or probabilities."""

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Input context: the supplied context.
    # Input profile_file: the supplied profile file.
    # Input runtime_v2: the supplied runtime v2.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path_manager, context=None, profile_file=None, runtime_v2=False):
        # Set self.path_manager to path_manager.
        self.path_manager = path_manager
        # Set self.runtime_v2 to a Boolean built from runtime_v2.
        self.runtime_v2 = bool(runtime_v2)
        # Set self.context to context or the result of RegulatoryContext().
        self.context = context or RegulatoryContext()
        # Set profile_file to profile_file or the result of Path(__file__).with_name(the text 'profiles') divided
        # by the text 'de_stvo_uncontrolled_4way_v1.json'.
        profile_file = profile_file or Path(__file__).with_name("profiles") / "de_stvo_uncontrolled_4way_v1.json"
        # Set payload to the decoded data produced by json.loads from the text read from Path(profile_file).
        payload = json.loads(Path(profile_file).read_text(encoding="utf-8"))
        # Set self.rules to a tuple built from a lazy sequence of the result of RuleRecord() for record in payload
        # at 'rules'.
        self.rules = tuple(RuleRecord(**record) for record in payload["rules"])
        # Set self._rules_by_id to a dictionary of rule.rule_id mapped to rule for rule in self.rules.
        self._rules_by_id = {rule.rule_id: rule for rule in self.rules}
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Empty totals using the inputs and processing steps below.
    # Output: a dictionary containing local_regulatory_assessments_built, spatial_conflict_pairs_assessed,...
    def _empty_totals():
        # Return a dictionary containing local_regulatory_assessments_built, spatial_conflict_pairs_assessed,...
        # to the caller.
        return {
            # Store 0 under 'local_regulatory_assessments_built'.
            "local_regulatory_assessments_built": 0,
            # Store 0 under 'spatial_conflict_pairs_assessed'.
            "spatial_conflict_pairs_assessed": 0,
            # Store 0 under 'stvo_8_right_before_left_obligations'.
            "stvo_8_right_before_left_obligations": 0,
            # Store 0 under 'stvo_9_turning_oncoming_obligations'.
            "stvo_9_turning_oncoming_obligations": 0,
            # Store 0 under 'stvo_9_4_left_oncoming_right_obligations'.
            "stvo_9_4_left_oncoming_right_obligations": 0,
            # Store 0 under 'ego_mandatory_yield_assessments'.
            "ego_mandatory_yield_assessments": 0,
            # Store 0 under 'ego_precedence_under_rule_assessments'.
            "ego_precedence_under_rule_assessments": 0,
            # Store 0 under 'manoeuvre_dependent_unresolved_assessments'.
            "manoeuvre_dependent_unresolved_assessments": 0,
            # Store 0 under 'regulatory_input_unresolved'.
            "regulatory_input_unresolved": 0,
            # Store 0 under 'target_route_truth_fields_consumed'.
            "target_route_truth_fields_consumed": 0,
        }

    # Reset using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    def reset(self):
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Path ids using the inputs and processing steps below.
    # Input value: the supplied value.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _path_ids(value):
        # Run this branch when whether value has type str.
        if isinstance(value, str):
            # Return a tuple containing value to the caller.
            return (value,)
        # Return a tuple built from value or an empty tuple to the caller.
        return tuple(value or ())

    # Evaluate candidate using the inputs and processing steps below.
    # Input ego_path: the supplied ego path.
    # Input target_path: the supplied target path.
    # Output: a dictionary containing target_candidate_path_id, target_candidate_manoeuvre, relative_approach,...
    # Processing: select branches using the stated conditions.
    def _evaluate_candidate(self, ego_path, target_path):
        # Set relation to the result of self.path_manager.approach_relation(ego_path.path_id,
        # target_path.path_id).
        relation = self.path_manager.approach_relation(
            # Supply target_path.path_id to self.path_manager.approach_relation.
            ego_path.path_id, target_path.path_id
        )
        # Set rule_ids to an empty list.
        rule_ids = []
        # Set status to RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE.
        status = RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE

        # Rule source: StVO § 8(1). Machine interpretation: at this
        # uncontrolled equal-road junction, a conflicting vehicle from the
        # right has priority. No number is used because priority is topological.
        # Run this branch when self.context.context_type equals the text 'UNCONTROLLED_EQUAL_PRIORITY'.
        if self.context.context_type == "UNCONTROLLED_EQUAL_PRIORITY":
            # Run this branch when relation equals the text 'RIGHT'.
            if relation == "RIGHT":
                # Append the text 'DE-STVO-8-1' to rule_ids.
                rule_ids.append("DE-STVO-8-1")
                # Set status to RegulatoryStatus.EGO_MUST_YIELD.
                status = RegulatoryStatus.EGO_MUST_YIELD
            # Run this branch when relation equals the text 'LEFT'.
            elif relation == "LEFT":
                # Append the text 'DE-STVO-8-1' to rule_ids.
                rule_ids.append("DE-STVO-8-1")
                # Set status to RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.
                status = RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE

        # Rule source: StVO § 9(3). Machine interpretation: a turning ego lets
        # physically conflicting oncoming passenger vehicles pass. Geometry,
        # not a numerical time/distance threshold, establishes applicability.
        # Run this branch when ego_path.manoeuvre belongs to a set containing the text 'LEFT', the text 'RIGHT'
        # and relation equals the text 'ONCOMING'.
        if ego_path.manoeuvre in {"LEFT", "RIGHT"} and relation == "ONCOMING":
            # Append the text 'DE-STVO-9-3' to rule_ids.
            rule_ids.append("DE-STVO-9-3")
            # Set status to RegulatoryStatus.EGO_MUST_YIELD.
            status = RegulatoryStatus.EGO_MUST_YIELD

        # Rule source: StVO § 9(4). Machine interpretation: left-turning ego
        # yields to an oncoming right-turn candidate. No numeric priority score.
        # Run this branch when ego_path.manoeuvre equals the text 'LEFT' and relation equals the text 'ONCOMING'
        # and target_path.manoeuvre equals the text 'RIGHT'.
        if (ego_path.manoeuvre == "LEFT" and relation == "ONCOMING"
                # Evaluate target_path.manoeuvre equals the text 'RIGHT' as part of the enclosing expression.
                and target_path.manoeuvre == "RIGHT"):
            # Append the text 'DE-STVO-9-4' to rule_ids.
            rule_ids.append("DE-STVO-9-4")
            # Set status to RegulatoryStatus.EGO_MUST_YIELD.
            status = RegulatoryStatus.EGO_MUST_YIELD

        # Run this branch when self.runtime_v2 and relation equals the text 'ONCOMING'.
        if self.runtime_v2 and relation == "ONCOMING":
            # Correct current runtime only; historical CTDE/replay stays frozen.
            # Set rule_ids to an empty list.
            rule_ids = []
            # Set status to RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE.
            status = RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE
            # Run this branch when ego_path.manoeuvre belongs to a set containing the text 'LEFT', the text
            # 'RIGHT' and target_path.manoeuvre equals the text 'STRAIGHT'.
            if ego_path.manoeuvre in {"LEFT", "RIGHT"} and target_path.manoeuvre == "STRAIGHT":
                # Set rule_ids to a list containing the text 'DE-STVO-9-3'.
                rule_ids = ["DE-STVO-9-3"]
                # Set status to RegulatoryStatus.EGO_MUST_YIELD.
                status = RegulatoryStatus.EGO_MUST_YIELD
            # Run this branch when ego_path.manoeuvre equals the text 'LEFT' and target_path.manoeuvre equals the
            # text 'RIGHT'.
            elif ego_path.manoeuvre == "LEFT" and target_path.manoeuvre == "RIGHT":
                # Set rule_ids to a list containing the text 'DE-STVO-9-3', the text 'DE-STVO-9-4'.
                rule_ids = ["DE-STVO-9-3", "DE-STVO-9-4"]
                # Set status to RegulatoryStatus.EGO_MUST_YIELD.
                status = RegulatoryStatus.EGO_MUST_YIELD
            # Run this branch when ego_path.manoeuvre equals the text 'STRAIGHT' and target_path.manoeuvre belongs
            # to a set containing the text 'LEFT', the text 'RIGHT'.
            elif ego_path.manoeuvre == "STRAIGHT" and target_path.manoeuvre in {"LEFT", "RIGHT"}:
                # Set rule_ids to a list containing the text 'DE-STVO-9-3'.
                rule_ids = ["DE-STVO-9-3"]
                # Set status to RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.
                status = RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE
            # Run this branch when ego_path.manoeuvre equals the text 'RIGHT' and target_path.manoeuvre equals the
            # text 'LEFT'.
            elif ego_path.manoeuvre == "RIGHT" and target_path.manoeuvre == "LEFT":
                # Set rule_ids to a list containing the text 'DE-STVO-9-4'.
                rule_ids = ["DE-STVO-9-4"]
                # Set status to RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.
                status = RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE

        # Set sections to a tuple built from the result of dict.fromkeys(a lazy sequence of
        # self._rules_by_id[rule_id].section for rule_id in rule_ids).
        sections = tuple(dict.fromkeys(
            # Evaluate self._rules_by_id[rule_id].section as part of the enclosing expression.
            self._rules_by_id[rule_id].section for rule_id in rule_ids
        ))
        # Return a dictionary containing target_candidate_path_id, target_candidate_manoeuvre,
        # relative_approach,... to the caller.
        return {
            # Store target_path.path_id under 'target_candidate_path_id'.
            "target_candidate_path_id": target_path.path_id,
            # Store target_path.manoeuvre under 'target_candidate_manoeuvre'.
            "target_candidate_manoeuvre": target_path.manoeuvre,
            # Store relation under 'relative_approach'.
            "relative_approach": relation,
            # Store a tuple built from rule_ids under 'applicable_rule_ids'.
            "applicable_rule_ids": tuple(rule_ids),
            # Store sections under 'source_sections'.
            "source_sections": sections,
            # Store status.value under 'regulatory_status'.
            "regulatory_status": status.value,
            # Store status is the same object as RegulatoryStatus.EGO_MUST_YIELD under 'mandatory_yield'.
            "mandatory_yield": status is RegulatoryStatus.EGO_MUST_YIELD,
        }

    # Assess ldm using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def assess_ldm(self, ldm, current_time):
        # Set graph to the result of ldm.get_current_conflict_graph().
        graph = ldm.get_current_conflict_graph()
        # Run this branch when the negation of graph or the negation of 'ego_path_id' from graph; use None if
        # absent.
        if not graph or not graph.get("ego_path_id"):
            # Return a dictionary containing ego_id, timestamp, regulatory_profile, assessments, metrics to the
            # caller.
            return {"ego_id": ldm.ego_id, "timestamp": float(current_time),
                    # Store self.context.profile_id under 'regulatory_profile'.
                    "regulatory_profile": self.context.profile_id,
                    # Store an empty tuple under 'assessments'.
                    # Store the result of self._empty_totals() under 'metrics'.
                    "assessments": (), "metrics": self._empty_totals()}
        # Set ego_path to graph['ego_path_id'] from self.path_manager.paths; use None if absent.
        ego_path = self.path_manager.paths.get(graph["ego_path_id"])
        # Set results to an empty list.
        results = []
        # Iterate over 'edges' from graph; use an empty tuple if absent, binding each item to edge.
        for edge in graph.get("edges", ()):
            # Set candidates to an empty list.
            candidates = []
            # Iterate over key/value pairs from edge.get('spatially_conflicting_candidate_paths', {}), binding
            # each item to (manoeuvre, path_value).
            for manoeuvre, path_value in edge.get(
                    # Supply an empty dictionary to edge.get.
                    "spatially_conflicting_candidate_paths", {}).items():
                # Delete manoeuvre from its containing namespace or collection.
                del manoeuvre
                # Iterate over the result of self._path_ids(path_value), binding each item to path_id.
                for path_id in self._path_ids(path_value):
                    # Set target_path to path_id from self.path_manager.paths; use None if absent.
                    target_path = self.path_manager.paths.get(path_id)
                    # Run this branch when target_path is a different object from None.
                    if target_path is not None:
                        # Append the result of self._evaluate_candidate(ego_path, target_path) to candidates.
                        candidates.append(self._evaluate_candidate(ego_path, target_path))
            # Set assessment to the result of self._aggregate(ldm.ego_id, 'target_track_id' from edge; use None if
            # absent, a floating-point number built from...).
            assessment = self._aggregate(
                # Supply 'target_track_id' from edge; use None if absent to self._aggregate.
                ldm.ego_id, edge.get("target_track_id"), float(current_time),
                # Supply ego_path.path_id to self._aggregate.
                ego_path.path_id, candidates,
            )
            # Append the result of assessment.to_dict() to results.
            results.append(assessment.to_dict())
            # Call self._count with the supplied arguments.
            self._count(assessment)
        # Return a dictionary containing ego_id, timestamp, regulatory_profile, execution_interpretation,
        # assessments to the caller.
        return {"ego_id": ldm.ego_id, "timestamp": float(current_time),
                # Store self.context.profile_id under 'regulatory_profile'.
                "regulatory_profile": self.context.profile_id,
                # Store the text 'EGO_LOCAL_V2' when self.runtime_v2, otherwise the text 'HISTORICAL_V1' under
                # 'execution_interpretation'.
                "execution_interpretation": "EGO_LOCAL_V2" if self.runtime_v2 else "HISTORICAL_V1",
                # Store a tuple built from results under 'assessments'.
                "assessments": tuple(results)}

    # Aggregate using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input target_id: the supplied target id.
    # Input timestamp: the supplied timestamp.
    # Input ego_path_id: the supplied ego path id.
    # Input candidates: the supplied candidates.
    # Output: the result of RegulatoryAssessment(ego_id, target_id, timestamp, self.context.profile_id,
    # ego_path_id, a tuple built from...).
    # Processing: select branches using the stated conditions.
    def _aggregate(self, ego_id, target_id, timestamp, ego_path_id, candidates):
        # Run this branch when the negation of candidates.
        if not candidates:
            # Set status to RegulatoryStatus.REGULATORY_INPUT_UNRESOLVED.
            status = RegulatoryStatus.REGULATORY_INPUT_UNRESOLVED
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set statuses to a set of item at 'regulatory_status' for item in candidates.
            statuses = {item["regulatory_status"] for item in candidates}
            # Set status to the result of RegulatoryStatus(the next item from the result of iter(statuses)) when
            # the number of entries in statuses equals 1, otherwise
            # RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE.
            status = (RegulatoryStatus(next(iter(statuses))) if len(statuses) == 1
                      # Evaluate RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE as part of the enclosing
                      # expression.
                      else RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE)
        # Set rule_ids to a tuple built from the sorted values from a set of rule_id for item in candidates.
        rule_ids = tuple(sorted({rule_id for item in candidates
                                 # Evaluate item at 'applicable_rule_ids' as part of the enclosing expression.
                                 for rule_id in item["applicable_rule_ids"]}))
        # Set sections to a tuple built from the sorted values from a set of section for item in candidates.
        sections = tuple(sorted({section for item in candidates
                                 # Evaluate item at 'source_sections' as part of the enclosing expression.
                                 for section in item["source_sections"]}))
        # Return the result of RegulatoryAssessment(ego_id, target_id, timestamp, self.context.profile_id,
        # ego_path_id, a tuple built from...) to the caller.
        return RegulatoryAssessment(
            # Supply self.context.profile_id to RegulatoryAssessment.
            ego_id, target_id, timestamp, self.context.profile_id, ego_path_id,
            # Supply a tuple built from candidates to RegulatoryAssessment.
            tuple(candidates), status.value, rule_ids, sections,
            # Supply status is the same object as RegulatoryStatus.EGO_MUST_YIELD to RegulatoryAssessment.
            status is RegulatoryStatus.EGO_MUST_YIELD,
            # Supply the text 'StVO § 8(2)' when status is the same object as RegulatoryStatus.EGO_MUST_YIELD,
            # otherwise None to RegulatoryAssessment.
            "StVO § 8(2)" if status is RegulatoryStatus.EGO_MUST_YIELD else None,
            # Supply True to the enclosing expression.
            True,
        )

    # Count using the inputs and processing steps below.
    # Input assessment: the supplied assessment.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def _count(self, assessment):
        # Update self._totals['local_regulatory_assessments_built'] to its current value plus 1.
        self._totals["local_regulatory_assessments_built"] += 1
        # Update self._totals['spatial_conflict_pairs_assessed'] to its current value plus 1.
        self._totals["spatial_conflict_pairs_assessed"] += 1
        # Set rules to a set built from assessment.applicable_rule_ids.
        rules = set(assessment.applicable_rule_ids)
        # Update self._totals['stvo_8_right_before_left_obligations'] to its current value plus the text
        # 'DE-STVO-8-1' belongs to rules and assessment.mandatory_yield.
        self._totals["stvo_8_right_before_left_obligations"] += (
            # Evaluate the text 'DE-STVO-8-1' belongs to rules and assessment.mandatory_yield as part of the
            # enclosing expression.
            "DE-STVO-8-1" in rules and assessment.mandatory_yield)
        # Update self._totals['stvo_9_turning_oncoming_obligations'] to its current value plus the text
        # 'DE-STVO-9-3' belongs to rules.
        self._totals["stvo_9_turning_oncoming_obligations"] += "DE-STVO-9-3" in rules
        # Update self._totals['stvo_9_4_left_oncoming_right_obligations'] to its current value plus the text
        # 'DE-STVO-9-4' belongs to rules.
        self._totals["stvo_9_4_left_oncoming_right_obligations"] += "DE-STVO-9-4" in rules
        # Set mapping to a dictionary of the supplied entries.
        mapping = {
            # Store the text 'ego_mandatory_yield_assessments' under RegulatoryStatus.EGO_MUST_YIELD.value.
            RegulatoryStatus.EGO_MUST_YIELD.value: "ego_mandatory_yield_assessments",
            # Store the text 'ego_precedence_under_rule_assessments' under
            # RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.value.
            RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.value: "ego_precedence_under_rule_assessments",
            # Store the text 'manoeuvre_dependent_unresolved_assessments' under
            # RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE.value.
            RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE.value: "manoeuvre_dependent_unresolved_assessments",
            # Store the text 'regulatory_input_unresolved' under
            # RegulatoryStatus.REGULATORY_INPUT_UNRESOLVED.value.
            RegulatoryStatus.REGULATORY_INPUT_UNRESOLVED.value: "regulatory_input_unresolved",
        }
        # Set key to assessment.regulatory_status from mapping; use None if absent.
        key = mapping.get(assessment.regulatory_status)
        # Run this branch when key.
        if key:
            # Update self._totals[key] to its current value plus 1.
            self._totals[key] += 1

    # Validation summary using the inputs and processing steps below.
    # Output: a dictionary built from self._totals.
    def validation_summary(self):
        # Return a dictionary built from self._totals to the caller.
        return dict(self._totals)
