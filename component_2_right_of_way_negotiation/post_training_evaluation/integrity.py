"""Runtime guards with measured counters and exact tensor comparisons."""
# Import ExitStack from contextlib for the operations below.
from contextlib import ExitStack
# Import patch from unittest.mock for the operations below.
from unittest.mock import patch
# Import torch for use in this module.
import torch
# Import ConflictZoneExecutionPlanner from negotiation_execution for the operations below.
from negotiation_execution import ConflictZoneExecutionPlanner
# Import POLICY, EXPECTED_POLICY_HASH, file_hash from .models for the operations below.
from .models import POLICY, EXPECTED_POLICY_HASH, file_hash

# Define IntegrityGuard to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class IntegrityGuard:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.stack to the result of ExitStack().
        self.stack = ExitStack()
        # Set self.modules to an empty tuple.
        self.modules = ()
        # Set self.before to an empty tuple.
        self.before = ()
        # Set self.counts to the result of dict.fromkeys(a tuple containing the text
        # 'centralized_critic_runtime_calls', the text 'training_operations',...).
        self.counts = dict.fromkeys(("centralized_critic_runtime_calls", "training_operations",
                                    "backward_calls", "optimizer_steps", "parameter_updates",
                                    # Supply 0 to the enclosing expression.
                                    "global_execution_calls"), 0)
        # Set self.hash_before to the result of file_hash(POLICY).
        self.hash_before = file_hash(POLICY)

    # Reject using the inputs and processing steps below.
    # Input name: the supplied name.
    # Output: blocked.
    def reject(self, name):
        # Blocked using the inputs and processing steps below.
        # Input args: the supplied args.
        # Input kwargs: the supplied kwargs.
        # Output: no explicit value; normal completion returns None.
        def blocked(*args, **kwargs):
            # Update self.counts[name] to its current value plus 1.
            self.counts[name] += 1
            # Raise RuntimeError with the text 'EVALUATION_INTEGRITY_BREACH:' plus name to stop this execution
            # path.
            raise RuntimeError("EVALUATION_INTEGRITY_BREACH:" + name)
        # Return blocked to the caller.
        return blocked

    # Bind using the inputs and processing steps below.
    # Input bundle: the supplied bundle.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def bind(self, bundle):
        # Set self.modules to a tuple containing bundle.gnn, bundle.proposer_actor, bundle.responder_actor.
        self.modules = (bundle.gnn, bundle.proposer_actor, bundle.responder_actor)
        # Set self.before to a tuple built from a lazy sequence of a dictionary of k mapped to the result of
        # v.detach().clone() for (k, v) in key/value pairs from module.state_dict() for module in self.modules.
        self.before = tuple({k: v.detach().clone() for k, v in module.state_dict().items()}
                            # Evaluate self.modules as part of the enclosing expression.
                            for module in self.modules)
        # Call self.stack.enter_context with the supplied arguments.
        self.stack.enter_context(torch.no_grad())
        # Iterate over a tuple containing a tuple containing torch.Tensor, the text 'backward', the text
        # 'backward_calls', a tuple containing..., binding each item to (target, name, counter).
        for target, name, counter in ((torch.Tensor, "backward", "backward_calls"),
            # Include a tuple containing torch.autograd, the text 'backward', the text 'backward_calls' in this
            # tuple.
            (torch.autograd, "backward", "backward_calls"),
            # Include a tuple containing torch.autograd, the text 'grad', the text 'backward_calls' in this tuple.
            (torch.autograd, "grad", "backward_calls"),
            # Include a tuple containing ConflictZoneExecutionPlanner, the text 'plan', the text
            # 'global_execution_calls' in this tuple.
            (ConflictZoneExecutionPlanner, "plan", "global_execution_calls")):
            # Call self.stack.enter_context with the supplied arguments.
            self.stack.enter_context(patch.object(target, name, self.reject(counter)))
        # Every installed optimizer implementation, including overrides.
        # Set seen to an empty set.
        seen = set()
        # Visit using the inputs and processing steps below.
        # Output: no explicit value; normal completion returns None.
        # Processing: iterate over the relevant records, then select branches using the stated conditions.
        def visit(cls):
            # Run this branch when cls belongs to seen.
            if cls in seen:
                # Return no value to the caller.
                return
            # Add cls to seen.
            seen.add(cls)
            # Iterate over the result of cls.__subclasses__(), binding each item to child.
            for child in cls.__subclasses__():
                # Call visit with the supplied arguments.
                visit(child)
            # Run this branch when the text 'step' belongs to cls.__dict__.
            if "step" in cls.__dict__:
                # Call self.stack.enter_context with the supplied arguments.
                self.stack.enter_context(patch.object(cls, "step", self.reject("optimizer_steps")))
        # Call visit with the supplied arguments.
        visit(torch.optim.Optimizer)
        # Iterate over self.modules, binding each item to module.
        for module in self.modules:
            # Iterate over the result of module.modules(), binding each item to child.
            for child in module.modules():
                # Set original_train to child.train.
                original_train = child.train
                # Train using the inputs and processing steps below.
                # Input mode: the supplied mode.
                # Input original: the supplied original.
                # Output: return the value selected by the matching return branch below.
                # Processing: select branches using the stated conditions.
                def train(mode=True, original=original_train):
                    # Run this branch when mode.
                    if mode:
                        # Return the result of self.reject('training_operations')() to the caller.
                        return self.reject("training_operations")()
                    # Return the result of original(False) to the caller.
                    return original(False)
                # Call self.stack.enter_context with the supplied arguments.
                self.stack.enter_context(patch.object(child, "train", train))
        # Call self.stack.enter_context with the supplied arguments.
        self.stack.enter_context(patch.object(bundle.centralized_critic, "forward",
            # Supply the result of self.reject(the text 'centralized_critic_runtime_calls') to patch.object.
            self.reject("centralized_critic_runtime_calls")))

    # Finish using the inputs and processing steps below.
    # Input runtime: the supplied runtime.
    # Output: result.
    def finish(self, runtime=None):
        # Set unchanged to a Boolean built from self.modules and whether every item is true in a lazy sequence of
        # before.keys() == module.state_dict().keys() and all((before[k].dtype == v.dtype and
        # torch.equal(before[k], v) for k, v in... for (before, module) in corresponding items paired from
        # self.before, self.modules.
        unchanged = bool(self.modules) and all(
            # Evaluate keys from before equals keys from module.state_dict() and whether every item is true in a
            # lazy sequence of before[k].dtype == v.dtype and torch.equal(before[k], v) for (k, v) in key/value
            # pairs from module.state_dict() as part of the enclosing expression.
            before.keys() == module.state_dict().keys() and all(
                # Evaluate before[k].dtype equals v.dtype and the result of torch.equal(before at k, v) as part of
                # the enclosing expression.
                before[k].dtype == v.dtype and torch.equal(before[k], v)
                # Evaluate key/value pairs from module.state_dict() as part of the enclosing expression.
                for k, v in module.state_dict().items())
            # Evaluate corresponding items paired from self.before, self.modules as part of the enclosing
            # expression.
            for before, module in zip(self.before, self.modules))
        # Set self.counts['parameter_updates'] to an integer built from a Boolean built from self.modules and the
        # negation of unchanged.
        self.counts["parameter_updates"] = int(bool(self.modules) and not unchanged)
        # Set eval_mode to a Boolean built from self.modules and whether every item is true in a lazy sequence of
        # the negation of child.training for module in self.modules.
        eval_mode = bool(self.modules) and all(not child.training
            # Evaluate the result of module.modules() as part of the enclosing expression.
            for module in self.modules for child in module.modules())
        # Call self.stack.close with the supplied arguments.
        self.stack.close()
        # Set after to the result of file_hash(POLICY).
        after = file_hash(POLICY)
        # Set result to a dictionary containing state_dict_unchanged, modules_in_evaluation_mode,
        # policy_sha256_before,...
        result = {**self.counts, "state_dict_unchanged": unchanged,
            # Store eval_mode under 'modules_in_evaluation_mode'.
            "modules_in_evaluation_mode": eval_mode,
            # Store self.hash_before under 'policy_sha256_before'.
            # Store after under 'policy_sha256_after'.
            "policy_sha256_before": self.hash_before, "policy_sha256_after": after,
            # Store self.hash_before equals after; equals EXPECTED_POLICY_HASH under 'policy_hash_unchanged'.
            "policy_hash_unchanged": self.hash_before == after == EXPECTED_POLICY_HASH,
            # Store 'decentralized_execution' from (runtime or {}); use False if absent under
            # 'decentralized_execution'.
            "decentralized_execution": (runtime or {}).get("decentralized_execution", False),
            # Store 'centralized_execution_graph_used_for_control' from (runtime or {}); use True if absent under
            # 'centralized_execution_graph_used_for_control'.
            "centralized_execution_graph_used_for_control": (runtime or {}).get(
                # Supply the text 'centralized_execution_graph_used_for_control' to the enclosing expression.
                "centralized_execution_graph_used_for_control", True)}
        # Set result['valid'] to unchanged and eval_mode and result at 'policy_hash_unchanged' and result at
        # 'decentralized_execution' and the negation of result at 'centralized_execution_graph_used_for_control'
        # and the negation of whether any item is true in values from self.counts and
        # 'maximum_negotiation_participants' from (runtime or {}).get('metrics', {}); use 5 if absent is at most
        # 4.
        result["valid"] = (unchanged and eval_mode and result["policy_hash_unchanged"] and
            # Evaluate the negation of result at 'centralized_execution_graph_used_for_control' as part of the
            # enclosing expression.
            result["decentralized_execution"] and not result["centralized_execution_graph_used_for_control"]
            # Evaluate 'maximum_negotiation_participants' from (runtime or {}).get('metrics', {}); use 5 if absent
            # is at most 4 as part of the enclosing expression.
            and not any(self.counts.values()) and (runtime or {}).get("metrics", {}).get(
                # Supply 4 to the enclosing expression.
                "maximum_negotiation_participants", 5) <= 4)
        # Return result to the caller.
        return result
