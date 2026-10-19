"""Runtime guards with measured counters and exact tensor comparisons."""
from contextlib import ExitStack
from unittest.mock import patch
import torch
from negotiation_execution import ConflictZoneExecutionPlanner
from .models import POLICY, EXPECTED_POLICY_HASH, file_hash

class IntegrityGuard:
    def __init__(self):
        self.stack = ExitStack()
        self.modules = ()
        self.before = ()
        self.counts = dict.fromkeys(("centralized_critic_runtime_calls", "training_operations",
                                    "backward_calls", "optimizer_steps", "parameter_updates",
                                    "global_execution_calls"), 0)
        self.hash_before = file_hash(POLICY)

    def reject(self, name):
        def blocked(*args, **kwargs):
            self.counts[name] += 1
            raise RuntimeError("EVALUATION_INTEGRITY_BREACH:" + name)
        return blocked

    def bind(self, bundle):
        self.modules = (bundle.gnn, bundle.proposer_actor, bundle.responder_actor)
        self.before = tuple({k: v.detach().clone() for k, v in module.state_dict().items()}
                            for module in self.modules)
        self.stack.enter_context(torch.no_grad())
        for target, name, counter in ((torch.Tensor, "backward", "backward_calls"),
            (torch.autograd, "backward", "backward_calls"),
            (torch.autograd, "grad", "backward_calls"),
            (ConflictZoneExecutionPlanner, "plan", "global_execution_calls")):
            self.stack.enter_context(patch.object(target, name, self.reject(counter)))
        # Every installed optimizer implementation, including overrides.
        seen = set()
        def visit(cls):
            if cls in seen:
                return
            seen.add(cls)
            for child in cls.__subclasses__():
                visit(child)
            if "step" in cls.__dict__:
                self.stack.enter_context(patch.object(cls, "step", self.reject("optimizer_steps")))
        visit(torch.optim.Optimizer)
        for module in self.modules:
            for child in module.modules():
                original_train = child.train
                def train(mode=True, original=original_train):
                    if mode:
                        return self.reject("training_operations")()
                    return original(False)
                self.stack.enter_context(patch.object(child, "train", train))
        self.stack.enter_context(patch.object(bundle.centralized_critic, "forward",
            self.reject("centralized_critic_runtime_calls")))

    def finish(self, runtime=None):
        unchanged = bool(self.modules) and all(
            before.keys() == module.state_dict().keys() and all(
                before[k].dtype == v.dtype and torch.equal(before[k], v)
                for k, v in module.state_dict().items())
            for before, module in zip(self.before, self.modules))
        self.counts["parameter_updates"] = int(bool(self.modules) and not unchanged)
        eval_mode = bool(self.modules) and all(not child.training
            for module in self.modules for child in module.modules())
        self.stack.close()
        after = file_hash(POLICY)
        result = {**self.counts, "state_dict_unchanged": unchanged,
            "modules_in_evaluation_mode": eval_mode,
            "policy_sha256_before": self.hash_before, "policy_sha256_after": after,
            "policy_hash_unchanged": self.hash_before == after == EXPECTED_POLICY_HASH,
            "decentralized_execution": (runtime or {}).get("decentralized_execution", False),
            "centralized_execution_graph_used_for_control": (runtime or {}).get(
                "centralized_execution_graph_used_for_control", True)}
        result["valid"] = (unchanged and eval_mode and result["policy_hash_unchanged"] and
            result["decentralized_execution"] and not result["centralized_execution_graph_used_for_control"]
            and not any(self.counts.values()) and (runtime or {}).get("metrics", {}).get(
                "maximum_negotiation_participants", 5) <= 4)
        return result
