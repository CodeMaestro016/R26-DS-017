"""Event-driven real-SUMO diagnostics, separate from frozen scientific studies."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import time
from dataclasses import replace

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))
os.chdir(BASE)
from post_training_evaluation.metrics import Telemetry
from runtime_simulation.runner import run_runtime_simulation
from runtime_simulation.scenarios import get_scenario


class DiagnosticTelemetry(Telemetry):
    def __init__(self, schedule, directory):
        super().__init__(schedule)
        self.trace_path = directory / 'timeline.jsonl'
        self.signatures = {}
        self.physical_second = -1

    def observe(self, now, states, *args):
        # Keep accounting every step, physical samples once per simulated second.
        target = self.trace_path
        self.trace_path = None
        super().observe(now, states, *args)
        self.trace_path = target
        if int(now) != self.physical_second:
            self.physical_second = int(now)
            self._trace(dict(event='PHYSICAL_STATE', timestamp=now, states=states,
                             movements=dict(self.movements)))

    def decision_trace(self, context, decision, admission_state):
        signature = (decision.permission, decision.reason, admission_state,
                     context.coordination_epoch, decision.shield_rejection_reason,
                     tuple((c.yielding_vehicle_id, c.priority_vehicle_id) for c in context.commitments))
        if self.signatures.get(context.ego_id) != signature:
            self.signatures[context.ego_id] = signature
            super().decision_trace(context, decision, admission_state)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scenario', required=True)
    parser.add_argument('--duration', type=float, required=True)
    parser.add_argument('--version', default='baseline')
    parser.add_argument('--fault', choices=['missing','stale','invalid','incorrect','contradictory'], default=None)
    args = parser.parse_args()
    root = BASE / 'results/live_deadlock_investigation/20261016' / args.version
    directory = root / (args.scenario + ('__'+args.fault if args.fault else ''))
    directory.mkdir(parents=True, exist_ok=False)
    sources = {}
    for folder, dirs, files in os.walk(BASE):
        dirs[:] = [d for d in dirs if d not in {'results','archive','__pycache__','.pytest_cache','deliverables'}]
        for name in files:
            p = Path(folder) / name
            if p.suffix in {'.py','.json','.xml','.sumocfg','.onnx','.npz'}:
                sources[p.relative_to(BASE).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    (directory/'source_hashes.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
    scenario = get_scenario(args.scenario)
    observer = DiagnosticTelemetry(scenario.schedule(), directory)
    started = time.monotonic()
    from negotiation_learning.movement_declarations import MovementDeclarationBus
    class FaultChannel(MovementDeclarationBus):
        def publish(self, sender, message):
            super().publish(sender, message)
            if message is None or '_S_' not in sender:
                return
            if args.fault == 'missing':self.messages.pop(sender,None)
            elif args.fault == 'stale':self.messages[sender]=[replace(message,timestamp=-1)]
            elif args.fault == 'invalid':self.messages[sender]=[replace(message,manoeuvre='INVALID')]
            elif args.fault == 'incorrect':self.messages[sender]=[replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT')]
            elif args.fault == 'contradictory':self.messages[sender].append(replace(message,manoeuvre='LEFT'))
    with (directory/'runtime.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        result = run_runtime_simulation(duration_seconds=args.duration,
            schedule=scenario.schedule(), admission_waves=scenario.admission_waves,
            admission_mode=scenario.admission_mode, scenario_id=args.scenario,
            runtime_observer=observer, output_dir=directory,
            web_live=True, browser_state_path=directory/'live_state.json',
            persist_presentation=False, return_failed_result=True,
            movement_protocol_factory=FaultChannel if args.fault else None)
    (directory/'runtime_result.json').write_text(json.dumps(result, default=str, indent=2), encoding='utf-8')
    metrics = observer.result(result)
    receipt = dict(scenario=args.scenario, evidence='DIAGNOSTIC_NOT_FINAL',
        version=args.version, injected_fault=args.fault, wall_seconds=time.monotonic()-started,
        run_status=result.get('run_status'), metrics=metrics,
        policy_hash_unchanged=result.get('policy_hash_unchanged'),
        centralized_critic_calls=result.get('centralized_critic_calls'))
    (directory/'receipt.json').write_text(json.dumps(receipt, default=str, indent=2), encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='metrics'}))
    print(json.dumps({k:metrics.get(k) for k in ['total_vehicles_scheduled','total_vehicles_spawned',
        'total_vehicles_completed','mappo_inference_call_count','deadlock_observed','collision_count',
        'blocked_zone_violation_count','maximum_waiting_time_seconds']}))


if __name__ == '__main__':
    main()
