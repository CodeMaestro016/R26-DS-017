"""Event-driven real-SUMO diagnostics, separate from frozen scientific studies."""
# Import argparse for use in this module.
import argparse
# Import contextlib for use in this module.
import contextlib
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import os for use in this module.
import os
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import sys for use in this module.
import sys
# Import time for use in this module.
import time
# Import replace from dataclasses for the operations below.
from dataclasses import replace

# Set BASE to Path(__file__).resolve().parents at 1.
BASE = Path(__file__).resolve().parents[1]
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0, str(BASE))
# Call os.chdir with the supplied arguments.
os.chdir(BASE)
# Import Telemetry from post_training_evaluation.metrics for the operations below.
from post_training_evaluation.metrics import Telemetry
# Import run_runtime_simulation from runtime_simulation.runner for the operations below.
from runtime_simulation.runner import run_runtime_simulation
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario


# Define DiagnosticTelemetry to group the state and operations declared below.
# Base classes: Telemetry.
# Instances expose the attributes and methods implemented in this class.
class DiagnosticTelemetry(Telemetry):
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input schedule: the supplied schedule.
    # Input directory: the supplied directory.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, schedule, directory):
        # Call super().__init__ with the supplied arguments.
        super().__init__(schedule)
        # Set self.trace_path to directory joined with the path segment 'timeline.jsonl'.
        self.trace_path = directory / 'timeline.jsonl'
        # Set self.signatures to an empty dictionary.
        self.signatures = {}
        # Set self.physical_second to the negative of 1.
        self.physical_second = -1

    # Observe using the inputs and processing steps below.
    # Input now: the time used for this operation.
    # Input states: the supplied states.
    # Input args: the supplied args.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def observe(self, now, states, *args):
        # Keep accounting every step, physical samples once per simulated second.
        # Set target to self.trace_path.
        target = self.trace_path
        # Set self.trace_path to None.
        self.trace_path = None
        # Call super().observe with the supplied arguments.
        super().observe(now, states, *args)
        # Set self.trace_path to target.
        self.trace_path = target
        # Run this branch when an integer built from now differs from self.physical_second.
        if int(now) != self.physical_second:
            # Set self.physical_second to an integer built from now.
            self.physical_second = int(now)
            # Call self._trace with the supplied arguments.
            self._trace(dict(event='PHYSICAL_STATE', timestamp=now, states=states,
                             # Supply movements as a dictionary built from self.movements.
                             movements=dict(self.movements)))

    # Decision trace using the inputs and processing steps below.
    # Input context: the supplied context.
    # Input decision: the supplied decision.
    # Input admission_state: the supplied admission state.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def decision_trace(self, context, decision, admission_state):
        # Set signature to a tuple containing decision.permission, decision.reason, admission_state,
        # context.coordination_epoch,...
        signature = (decision.permission, decision.reason, admission_state,
                     # Include decision.shield_rejection_reason in this tuple.
                     context.coordination_epoch, decision.shield_rejection_reason,
                     # Include a tuple built from a lazy sequence of a tuple containing c.yielding_vehicle_id,
                     # c.priority_vehicle_id for c in context.commitments in this tuple.
                     tuple((c.yielding_vehicle_id, c.priority_vehicle_id) for c in context.commitments))
        # Run this branch when context.ego_id from self.signatures; use None if absent differs from signature.
        if self.signatures.get(context.ego_id) != signature:
            # Set self.signatures[context.ego_id] to signature.
            self.signatures[context.ego_id] = signature
            # Call super().decision_trace with the supplied arguments.
            super().decision_trace(context, decision, admission_state)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set parser to the result of argparse.ArgumentParser().
    parser = argparse.ArgumentParser()
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--scenario', required=True)
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--duration', type=float, required=True)
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--version', default='baseline')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--fault', choices=['missing','stale','invalid','incorrect','contradictory'], default=None)
    # Set args to the result of parser.parse_args().
    args = parser.parse_args()
    # Set root to BASE joined with the path segment 'results/live_deadlock_investigation/20261016' divided by args.version.
    root = BASE / 'results/live_deadlock_investigation/20261016' / args.version
    # Set directory to root divided by args.scenario plus '__' plus args.fault when args.fault, otherwise the text
    # ''.
    directory = root / (args.scenario + ('__'+args.fault if args.fault else ''))
    # Create the directory requested by directory.
    directory.mkdir(parents=True, exist_ok=False)
    # Set sources to an empty dictionary.
    sources = {}
    # Iterate over the result of os.walk(BASE), binding each item to (folder, dirs, files).
    for folder, dirs, files in os.walk(BASE):
        # Set dirs[:] to a list of d for d in dirs; retain entries satisfying d does not belong to a set
        # containing the text 'results', the text 'archive', the text...
        dirs[:] = [d for d in dirs if d not in {'results','archive','__pycache__','.pytest_cache','deliverables'}]
        # Iterate over files, binding each item to name.
        for name in files:
            # Set p to the result of Path(folder) divided by name.
            p = Path(folder) / name
            # Run this branch when p.suffix belongs to a set containing the text '.py', the text '.json', the text
            # '.xml', the text '.sumocfg', the text '.onnx', the text '.npz'.
            if p.suffix in {'.py','.json','.xml','.sumocfg','.onnx','.npz'}:
                # Set sources[p.relative_to(BASE).as_posix()] to the hexadecimal digest from
                # hashlib.sha256(p.read_bytes()).
                sources[p.relative_to(BASE).as_posix()] = hashlib.sha256(p.read_bytes()).hexdigest()
    # Write the supplied text to (directory / 'source_hashes.json').
    (directory/'source_hashes.json').write_text(json.dumps(sources, indent=2), encoding='utf-8')
    # Set scenario to the result of get_scenario(args.scenario).
    scenario = get_scenario(args.scenario)
    # Set observer to the result of DiagnosticTelemetry(the result of scenario.schedule(), directory).
    observer = DiagnosticTelemetry(scenario.schedule(), directory)
    # Set started to the monotonic clock time.
    started = time.monotonic()
    # Import MovementDeclarationBus from negotiation_learning.movement_declarations for the operations below.
    from negotiation_learning.movement_declarations import MovementDeclarationBus
    # Define FaultChannel to group the state and operations declared below.
    # Base classes: MovementDeclarationBus.
    # Instances expose the attributes and methods implemented in this class.
    class FaultChannel(MovementDeclarationBus):
        # Publish using the inputs and processing steps below.
        # Input sender: the supplied sender.
        # Input message: the supplied message.
        # Output: no explicit value; normal completion returns None.
        # Processing: select branches using the stated conditions.
        def publish(self, sender, message):
            # Call super().publish with the supplied arguments.
            super().publish(sender, message)
            # Run this branch when message is the same object as None or the text '_S_' does not belong to sender.
            if message is None or '_S_' not in sender:
                # Return no value to the caller.
                return
            # Run this branch when args.fault equals the text 'missing'.
            # Remove the requested entry from self.messages.
            if args.fault == 'missing':self.messages.pop(sender,None)
            # Run this branch when args.fault equals the text 'stale'.
            # Set self.messages[sender] to a list containing the result of replace(message).
            elif args.fault == 'stale':self.messages[sender]=[replace(message,timestamp=-1)]
            # Run this branch when args.fault equals the text 'invalid'.
            # Set self.messages[sender] to a list containing the result of replace(message).
            elif args.fault == 'invalid':self.messages[sender]=[replace(message,manoeuvre='INVALID')]
            # Run this branch when args.fault equals the text 'incorrect'.
            # Set self.messages[sender] to a list containing the result of replace(message).
            elif args.fault == 'incorrect':self.messages[sender]=[replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT')]
            # Run this branch when args.fault equals the text 'contradictory'.
            # Append the result of replace(message) to self.messages[sender].
            elif args.fault == 'contradictory':self.messages[sender].append(replace(message,manoeuvre='LEFT'))
    # Enter the result of (directory / 'runtime.log').open(the text 'w') as log; the result of
    # contextlib.redirect_stdout(log); the result of contextlib.redirect_stderr(log) and run the enclosed
    # operations within that context.
    with (directory/'runtime.log').open('w', encoding='utf-8') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        # Set result to the result of run_runtime_simulation().
        result = run_runtime_simulation(duration_seconds=args.duration,
            # Supply schedule as the result of scenario.schedule().
            # Supply admission_waves as scenario.admission_waves.
            schedule=scenario.schedule(), admission_waves=scenario.admission_waves,
            # Supply admission_mode as scenario.admission_mode.
            # Supply scenario_id as args.scenario.
            admission_mode=scenario.admission_mode, scenario_id=args.scenario,
            # Supply runtime_observer as observer.
            # Supply output_dir as directory.
            runtime_observer=observer, output_dir=directory,
            # Supply web_live as True.
            # Supply browser_state_path as directory joined with the path segment 'live_state.json'.
            web_live=True, browser_state_path=directory/'live_state.json',
            # Supply persist_presentation as False.
            # Supply return_failed_result as True.
            persist_presentation=False, return_failed_result=True,
            # Supply movement_protocol_factory as FaultChannel when args.fault, otherwise None.
            movement_protocol_factory=FaultChannel if args.fault else None)
    # Write the supplied text to (directory / 'runtime_result.json').
    (directory/'runtime_result.json').write_text(json.dumps(result, default=str, indent=2), encoding='utf-8')
    # Set metrics to the result of observer.result(result).
    metrics = observer.result(result)
    # Set receipt to a dictionary built from the supplied values.
    receipt = dict(scenario=args.scenario, evidence='DIAGNOSTIC_NOT_FINAL',
        # Supply version as args.version.
        # Supply injected_fault as args.fault.
        # Supply wall_seconds as the monotonic clock time minus started.
        version=args.version, injected_fault=args.fault, wall_seconds=time.monotonic()-started,
        # Supply run_status as 'run_status' from result; use None if absent.
        # Supply metrics as metrics.
        run_status=result.get('run_status'), metrics=metrics,
        # Supply policy_hash_unchanged as 'policy_hash_unchanged' from result; use None if absent.
        policy_hash_unchanged=result.get('policy_hash_unchanged'),
        # Supply centralized_critic_calls as 'centralized_critic_calls' from result; use None if absent.
        centralized_critic_calls=result.get('centralized_critic_calls'))
    # Write the supplied text to (directory / 'receipt.json').
    (directory/'receipt.json').write_text(json.dumps(receipt, default=str, indent=2), encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in receipt.items() if k!='metrics'}))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:metrics.get(k) for k in ['total_vehicles_scheduled','total_vehicles_spawned',
        'total_vehicles_completed','mappo_inference_call_count','deadlock_observed','collision_count',
        'blocked_zone_violation_count','maximum_waiting_time_seconds']}))


# Run this branch when __name__ equals the text '__main__'.
if __name__ == '__main__':
    # Call main with the supplied arguments.
    main()
