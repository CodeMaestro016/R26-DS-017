"""Source-traceable German StVO rules for the constrained research ODD."""

import json
from pathlib import Path

from .regulatory_context import RegulatoryContext
from .rule_models import RegulatoryAssessment, RegulatoryStatus, RuleRecord


class TrafficRuleEngine:
    """Evaluate local candidate paths without route truth or probabilities."""

    def __init__(self, path_manager, context=None, profile_file=None):
        self.path_manager = path_manager
        self.context = context or RegulatoryContext()
        profile_file = profile_file or Path(__file__).with_name("profiles") / "de_stvo_uncontrolled_4way_v1.json"
        payload = json.loads(Path(profile_file).read_text(encoding="utf-8"))
        self.rules = tuple(RuleRecord(**record) for record in payload["rules"])
        self._rules_by_id = {rule.rule_id: rule for rule in self.rules}
        self._totals = self._empty_totals()

    @staticmethod
    def _empty_totals():
        return {
            "local_regulatory_assessments_built": 0,
            "spatial_conflict_pairs_assessed": 0,
            "stvo_8_right_before_left_obligations": 0,
            "stvo_9_turning_oncoming_obligations": 0,
            "stvo_9_4_left_oncoming_right_obligations": 0,
            "ego_mandatory_yield_assessments": 0,
            "ego_precedence_under_rule_assessments": 0,
            "manoeuvre_dependent_unresolved_assessments": 0,
            "regulatory_input_unresolved": 0,
            "target_route_truth_fields_consumed": 0,
        }

    def reset(self):
        self._totals = self._empty_totals()

    @staticmethod
    def _path_ids(value):
        if isinstance(value, str):
            return (value,)
        return tuple(value or ())

    def _evaluate_candidate(self, ego_path, target_path):
        relation = self.path_manager.approach_relation(
            ego_path.path_id, target_path.path_id
        )
        rule_ids = []
        status = RegulatoryStatus.NO_PAIRWISE_PRECEDENCE_RULE

        # Rule source: StVO § 8(1). Machine interpretation: at this
        # uncontrolled equal-road junction, a conflicting vehicle from the
        # right has priority. No number is used because priority is topological.
        if self.context.context_type == "UNCONTROLLED_EQUAL_PRIORITY":
            if relation == "RIGHT":
                rule_ids.append("DE-STVO-8-1")
                status = RegulatoryStatus.EGO_MUST_YIELD
            elif relation == "LEFT":
                rule_ids.append("DE-STVO-8-1")
                status = RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE

        # Rule source: StVO § 9(3). Machine interpretation: a turning ego lets
        # physically conflicting oncoming passenger vehicles pass. Geometry,
        # not a numerical time/distance threshold, establishes applicability.
        if ego_path.manoeuvre in {"LEFT", "RIGHT"} and relation == "ONCOMING":
            rule_ids.append("DE-STVO-9-3")
            status = RegulatoryStatus.EGO_MUST_YIELD

        # Rule source: StVO § 9(4). Machine interpretation: left-turning ego
        # yields to an oncoming right-turn candidate. No numeric priority score.
        if (ego_path.manoeuvre == "LEFT" and relation == "ONCOMING"
                and target_path.manoeuvre == "RIGHT"):
            rule_ids.append("DE-STVO-9-4")
            status = RegulatoryStatus.EGO_MUST_YIELD

        sections = tuple(dict.fromkeys(
            self._rules_by_id[rule_id].section for rule_id in rule_ids
        ))
        return {
            "target_candidate_path_id": target_path.path_id,
            "target_candidate_manoeuvre": target_path.manoeuvre,
            "relative_approach": relation,
            "applicable_rule_ids": tuple(rule_ids),
            "source_sections": sections,
            "regulatory_status": status.value,
            "mandatory_yield": status is RegulatoryStatus.EGO_MUST_YIELD,
        }

    def assess_ldm(self, ldm, current_time):
        graph = ldm.get_current_conflict_graph()
        if not graph or not graph.get("ego_path_id"):
            return {"ego_id": ldm.ego_id, "timestamp": float(current_time),
                    "regulatory_profile": self.context.profile_id,
                    "assessments": (), "metrics": self._empty_totals()}
        ego_path = self.path_manager.paths.get(graph["ego_path_id"])
        results = []
        for edge in graph.get("edges", ()):
            candidates = []
            for manoeuvre, path_value in edge.get(
                    "spatially_conflicting_candidate_paths", {}).items():
                del manoeuvre
                for path_id in self._path_ids(path_value):
                    target_path = self.path_manager.paths.get(path_id)
                    if target_path is not None:
                        candidates.append(self._evaluate_candidate(ego_path, target_path))
            assessment = self._aggregate(
                ldm.ego_id, edge.get("target_track_id"), float(current_time),
                ego_path.path_id, candidates,
            )
            results.append(assessment.to_dict())
            self._count(assessment)
        return {"ego_id": ldm.ego_id, "timestamp": float(current_time),
                "regulatory_profile": self.context.profile_id,
                "assessments": tuple(results)}

    def _aggregate(self, ego_id, target_id, timestamp, ego_path_id, candidates):
        if not candidates:
            status = RegulatoryStatus.REGULATORY_INPUT_UNRESOLVED
        else:
            statuses = {item["regulatory_status"] for item in candidates}
            status = (RegulatoryStatus(next(iter(statuses))) if len(statuses) == 1
                      else RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE)
        rule_ids = tuple(sorted({rule_id for item in candidates
                                 for rule_id in item["applicable_rule_ids"]}))
        sections = tuple(sorted({section for item in candidates
                                 for section in item["source_sections"]}))
        return RegulatoryAssessment(
            ego_id, target_id, timestamp, self.context.profile_id, ego_path_id,
            tuple(candidates), status.value, rule_ids, sections,
            status is RegulatoryStatus.EGO_MUST_YIELD,
            "StVO § 8(2)" if status is RegulatoryStatus.EGO_MUST_YIELD else None,
            True,
        )

    def _count(self, assessment):
        self._totals["local_regulatory_assessments_built"] += 1
        self._totals["spatial_conflict_pairs_assessed"] += 1
        rules = set(assessment.applicable_rule_ids)
        self._totals["stvo_8_right_before_left_obligations"] += (
            "DE-STVO-8-1" in rules and assessment.mandatory_yield)
        self._totals["stvo_9_turning_oncoming_obligations"] += "DE-STVO-9-3" in rules
        self._totals["stvo_9_4_left_oncoming_right_obligations"] += "DE-STVO-9-4" in rules
        mapping = {
            RegulatoryStatus.EGO_MUST_YIELD.value: "ego_mandatory_yield_assessments",
            RegulatoryStatus.EGO_HAS_PRECEDENCE_UNDER_RULE.value: "ego_precedence_under_rule_assessments",
            RegulatoryStatus.UNRESOLVED_DUE_TO_TARGET_MANOEUVRE.value: "manoeuvre_dependent_unresolved_assessments",
            RegulatoryStatus.REGULATORY_INPUT_UNRESOLVED.value: "regulatory_input_unresolved",
        }
        key = mapping.get(assessment.regulatory_status)
        if key:
            self._totals[key] += 1

    def validation_summary(self):
        return dict(self._totals)
