"""Semantic action-provider boundary for coupled negotiation episodes."""

# Import ABC, abstractmethod from abc for the operations below.
from abc import ABC, abstractmethod


# Set PROFILING_SOURCE to the text 'NON_LEARNED_PROFILING_PROVIDER'.
PROFILING_SOURCE = "NON_LEARNED_PROFILING_PROVIDER"
# Set PROFILING_RULE to the text 'FIRST_CANONICAL_EXECUTABLE_JOINT_BRANCH'.
PROFILING_RULE = "FIRST_CANONICAL_EXECUTABLE_JOINT_BRANCH"


# Define NegotiationActionProvider to group the state and operations declared below.
# Base classes: ABC.
# Instances expose the attributes and methods implemented in this class.
class NegotiationActionProvider(ABC):
    # Apply abstractmethod as a decorator to configure the following definition.
    @abstractmethod
    # Return one branch represented by feasible semantic factor actions.
    # Input branches: the supplied branches.
    # Input factor_contexts: the supplied factor contexts.
    # Output: no explicit value; normal completion returns None.
    def select_joint_actions(self, branches, factor_contexts):
        """Return one branch represented by feasible semantic factor actions."""


# Define DeterministicEnvironmentProfilingActionProvider to group the state and operations declared below.
# Base classes: NegotiationActionProvider.
# Instances expose the attributes and methods implemented in this class.
class DeterministicEnvironmentProfilingActionProvider(NegotiationActionProvider):
    # Set selection_rule to PROFILING_RULE.
    selection_rule = PROFILING_RULE
    # Set outcome_data_used to False.
    outcome_data_used = False

    # Select joint actions using the inputs and processing steps below.
    # Input branches: the supplied branches.
    # Input factor_contexts: the supplied factor contexts.
    # Output: the minimum of executable.
    # Processing: select branches using the stated conditions.
    def select_joint_actions(self, branches, factor_contexts):
        # Delete factor_contexts from its containing namespace or collection.
        del factor_contexts
        # Set executable to a tuple built from a lazy sequence of item for item in branches; retain entries
        # satisfying item.graph_executable.
        executable = tuple(item for item in branches if item.graph_executable)
        # Run this branch when the negation of executable.
        if not executable:
            # Raise RuntimeError with the text 'EXECUTION_BLOCKED_PRECEDENCE_CYCLE' to stop this execution path.
            raise RuntimeError("EXECUTION_BLOCKED_PRECEDENCE_CYCLE")
        # Return the minimum of executable to the caller.
        return min(executable, key=lambda item: item.branch_id)
