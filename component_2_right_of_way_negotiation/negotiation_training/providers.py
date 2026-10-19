"""Semantic action-provider boundary for coupled negotiation episodes."""

from abc import ABC, abstractmethod


PROFILING_SOURCE = "NON_LEARNED_PROFILING_PROVIDER"
PROFILING_RULE = "FIRST_CANONICAL_EXECUTABLE_JOINT_BRANCH"


class NegotiationActionProvider(ABC):
    @abstractmethod
    def select_joint_actions(self, branches, factor_contexts):
        """Return one branch represented by feasible semantic factor actions."""


class DeterministicEnvironmentProfilingActionProvider(NegotiationActionProvider):
    selection_rule = PROFILING_RULE
    outcome_data_used = False

    def select_joint_actions(self, branches, factor_contexts):
        del factor_contexts
        executable = tuple(item for item in branches if item.graph_executable)
        if not executable:
            raise RuntimeError("EXECUTION_BLOCKED_PRECEDENCE_CYCLE")
        return min(executable, key=lambda item: item.branch_id)
