"""Synchronized real-SUMO/UI audit; observation hooks never grant permission."""
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

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set sys.argv[0] to a string built from the result of Path(__file__).resolve().
sys.argv[0]=str(Path(__file__).resolve())
# Call sys.path.insert with the supplied arguments.
sys.path.insert(0,str(BASE.parent));sys.path.insert(0,str(BASE))
# Call os.chdir with the supplied arguments.
os.chdir(BASE)
# Import DiagnosticTelemetry from diagnose_live_deadlock for the operations below.
from diagnose_live_deadlock import DiagnosticTelemetry
# Import runner from runtime_simulation for the operations below.
from runtime_simulation import runner
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario
# Import MapPathManager from conflict for the operations below.
from conflict import MapPathManager
# Import NegotiationVisualHold from socialmind_drive_showcase.pages.component2_live_view for the operations below.
from socialmind_drive_showcase.pages.component2_live_view import NegotiationVisualHold


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set parser to the result of argparse.ArgumentParser().
    parser=argparse.ArgumentParser()
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--scenario',required=True)
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--duration',type=float,required=True)
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--version',required=True)
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--presentation-run-id')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--stop-request-path')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--command-trace',action='store_true')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--native-junction-trace',action='store_true')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--planned-holds-probe',action='store_true',
        # Supply help as the text 'Separate execution-integration experiment, never enabled by...'.
        help='Separate execution-integration experiment, never enabled by production runtime')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--fault',choices=['stale_commitment','missing_declaration','stale_declaration',
        'invalid_declaration','incorrect_declaration','contradictory_declaration',
        # Supply default as None.
        'mandatory_constraint_cycle'],default=None)
    # Set args to the result of parser.parse_args().
    args=parser.parse_args()
    # Set root to BASE joined with the path segment 'results/vehicle_state_consistency/20261016' divided by args.version
    # divided by args.scenario plus '__' plus args.fault when args.fault, otherwise the text ''.
    root=BASE/'results/vehicle_state_consistency/20261016'/args.version/(args.scenario+('__'+args.fault if args.fault else ''))
    # Create the directory requested by root.
    root.mkdir(parents=True,exist_ok=False)
    # Set scenario to the result of get_scenario(args.scenario).
    scenario=get_scenario(args.scenario)
    # Set paths to the result of MapPathManager().
    paths=MapPathManager()
    # Define Observer to group the state and operations declared below.
    # Base classes: DiagnosticTelemetry.
    # Instances expose the attributes and methods implemented in this class.
    class Observer(DiagnosticTelemetry):
        # Initialize the instance attributes and collaborators used by the operations below.
        # Output: no explicit value; normal completion returns None.
        def __init__(self):
            # Call super().__init__ with the supplied arguments.
            super().__init__(scenario.schedule(),root)
            # Set self.latest to an empty dictionary.
            # Set self.entered to an empty set.
            # Set self.entry_records to an empty list.
            self.latest={};self.entered=set();self.entry_records=[]
        # Observe using the inputs and processing steps below.
        # Input now: the time used for this operation.
        # Input states: the supplied states.
        # Input rest: the supplied rest.
        # Output: no explicit value; normal completion returns None.
        # Processing: iterate over the relevant records, then select branches using the stated conditions.
        def observe(self,now,states,*rest):
            # Call super().observe with the supplied arguments.
            super().observe(now,states,*rest)
            # Run this branch when args.native_junction_trace and an integer built from now differs from the
            # requested attribute of self.
            if args.native_junction_trace and int(now) != getattr(self, 'last_native_second', -1):
                # Set self.last_native_second to an integer built from now.
                self.last_native_second = int(now)
                # Enter the result of (root / 'native_junctions.jsonl').open(the text 'a') as stream and run the
                # enclosed operations within that context.
                with (root/'native_junctions.jsonl').open('a',encoding='utf-8') as stream:
                    # Iterate over key/value pairs from states, binding each item to (ego, state).
                    for ego, state in states.items():
                        # Call stream.write with the supplied arguments.
                        stream.write(json.dumps(dict(timestamp=now,ego_id=ego,speed=state['speed'],
                            # Supply native_speed as the result of runner.traci.vehicle.getSpeedWithoutTraCI(ego).
                            native_speed=runner.traci.vehicle.getSpeedWithoutTraCI(ego),
                            # Supply next_links as the result of runner.traci.vehicle.getNextLinks(ego).
                            next_links=runner.traci.vehicle.getNextLinks(ego),
                            # Supply default as str.
                            # Supply junction_foes as the result of runner.traci.vehicle.getJunctionFoes(ego,
                            # 100).
                            junction_foes=runner.traci.vehicle.getJunctionFoes(ego,100)),default=str)+'\n')
            # Iterate over key/value pairs from states, binding each item to (ego, state).
            for ego,state in states.items():
                # Set (progress, _, error) to the result of paths.resolve_front_bumper_path_progress(state,
                # paths.paths at self.movements[ego]).
                progress,_,error=paths.resolve_front_bumper_path_progress(state,paths.paths[self.movements[ego]])
                # Run this branch when the negation of error and progress is at least 0 and ego does not belong to
                # self.entered.
                if not error and progress>=0 and ego not in self.entered:
                    # Set prior to ego from self.latest; use an empty dictionary if absent.
                    prior=self.latest.get(ego,{})
                    # Set authorized to 'permission' from prior; use None if absent equals the text 'PERMITTED'.
                    authorized=prior.get('permission')=='PERMITTED'
                    # Append a dictionary built from the supplied values to self.entry_records.
                    self.entry_records.append(dict(ego_id=ego,timestamp=now,authorized=authorized,
                        # Supply prior_decision as prior.
                        # Supply progress as progress.
                        prior_decision=prior,progress=progress))
                    # Add ego to self.entered.
                    self.entered.add(ego)
        # Decision trace using the inputs and processing steps below.
        # Input context: the supplied context.
        # Input decision: the supplied decision.
        # Input admission_state: the supplied admission state.
        # Output: no explicit value; normal completion returns None.
        def decision_trace(self,context,decision,admission_state):
            # Set (progress, _, error) to the result of
            # paths.resolve_front_bumper_path_progress(context.ego_state, paths.paths at
            # context.movement_path_id).
            progress,_,error=paths.resolve_front_bumper_path_progress(context.ego_state,paths.paths[context.movement_path_id])
            # Set self.latest[context.ego_id] to a dictionary built from the supplied values.
            self.latest[context.ego_id]=dict(timestamp=context.timestamp,
                # Supply permission as decision.permission.
                # Supply reason as decision.reason.
                permission=decision.permission,reason=decision.reason,
                # Supply physical_speed as context.ego_state at 'speed'.
                physical_speed=context.ego_state['speed'],
                # Supply front_bumper_position as context.ego_state at 'position'.
                front_bumper_position=context.ego_state['position'],
                # Supply requested_speed as decision.requested_speed_mps.
                requested_speed=decision.requested_speed_mps,
                # Supply blocked_zones as decision.blocked_zones.
                # Supply admission_state as admission_state.
                blocked_zones=decision.blocked_zones,admission_state=admission_state,
                # Supply mandatory as a list of the result of vars(c) for c in context.mandatory_commitments.
                mandatory=[vars(c) for c in context.mandatory_commitments],
                # Supply fallback_pairs as decision.fallback_pairs.
                fallback_pairs=decision.fallback_pairs,
                # Supply coordination_epoch as context.coordination_epoch.
                coordination_epoch=context.coordination_epoch,
                # Supply coordination_complete as context.coordination_complete.
                coordination_complete=context.coordination_complete,
                # Supply mappo_receipt as context.mappo_receipt.
                mappo_receipt=context.mappo_receipt,
                # Supply distance_to_entry as None when error, otherwise the negative of progress.
                distance_to_entry=None if error else -progress)
            # Call super().decision_trace with the supplied arguments.
            super().decision_trace(context,decision,admission_state)
    # Set observer to the result of Observer().
    observer=Observer()
    # Set actual_sample to runner.PanelDeterministicInferenceProvider._sample.
    actual_sample=runner.PanelDeterministicInferenceProvider._sample
    # Record actor sample using the inputs and processing steps below.
    # Input a: the supplied a.
    # Input kw: the supplied kw.
    # Output: sample.
    def record_actor_sample(self,*a,**kw):
        # Import is_dataclass, fields from dataclasses for the operations below.
        from dataclasses import is_dataclass, fields
        # Import Mapping from collections.abc for the operations below.
        from collections.abc import Mapping
        # Serialize using the inputs and processing steps below.
        # Input value: the supplied value.
        # Output: return the value selected by the matching return branch below.
        # Processing: select branches using the stated conditions.
        def serialize(value):
            # Run this branch when the result of is_dataclass(value).
            # Return a dictionary of f.name mapped to the result of serialize(the requested attribute of value)
            # for f in the result of fields(value) to the caller.
            if is_dataclass(value):return {f.name:serialize(getattr(value,f.name)) for f in fields(value)}
            # Run this branch when whether value has type Mapping.
            # Return a dictionary of k mapped to the result of serialize(v) for (k, v) in key/value pairs from
            # value to the caller.
            if isinstance(value,Mapping):return {k:serialize(v) for k,v in value.items()}
            # Run this branch when whether value has type a tuple containing tuple, list.
            # Return a list of the result of serialize(v) for v in value to the caller.
            if isinstance(value,(tuple,list)):return [serialize(v) for v in value]
            # Return value to the caller.
            return value
        # Set began to the result of time.perf_counter_ns().
        began=time.perf_counter_ns()
        # Set sample to the result of actual_sample(self, the unpacked values from a).
        sample=actual_sample(self,*a,**kw)
        # Require sample.hard_action_mask at sample.selected_action_index; otherwise raise AssertionError.
        assert sample.hard_action_mask[sample.selected_action_index]
        # Enter the result of (root / 'actor_inputs_and_actions.jsonl').open(the text 'a') as stream and run the
        # enclosed operations within that context.
        with (root/'actor_inputs_and_actions.jsonl').open('a',encoding='utf-8') as stream:
            # Call stream.write with the supplied arguments.
            stream.write(json.dumps(dict(inference_started_wall_ns=began,
                # Supply inference_completed_wall_ns as the result of time.perf_counter_ns().
                inference_completed_wall_ns=time.perf_counter_ns(),
                # Supply default as str.
                # Supply actual_factor as the result of serialize(sample).
                actual_factor=serialize(sample)),default=str)+'\n')
        # Return sample to the caller.
        return sample
    # Set runner.PanelDeterministicInferenceProvider._sample to record_actor_sample.
    runner.PanelDeterministicInferenceProvider._sample=record_actor_sample
    # Set commands to an empty list.
    commands=[]
    # Set planned_holds to an empty set.
    planned_holds=set()
    # Run this branch when args.command_trace.
    if args.command_trace:
        # Set actual_set_speed to runner.traci.vehicle.setSpeed.
        actual_set_speed=runner.traci.vehicle.setSpeed
        # Traced speed using the inputs and processing steps below.
        # Input ego: the ego vehicle used in this calculation.
        # Input speed: the supplied speed.
        # Output: response.
        # Processing: select branches using the stated conditions, then handle the specified errors.
        def traced_speed(ego,speed):
            # Set response to the result of actual_set_speed(ego, speed).
            response=actual_set_speed(ego,speed)
            # Run this branch when args.planned_holds_probe.
            if args.planned_holds_probe:
                # Set api to runner.traci.vehicle.
                api=runner.traci.vehicle
                # Run this branch when speed is at least 0 and ego does not belong to planned_holds.
                if speed>=0 and ego not in planned_holds:
                    # Set lane to the result of api.getLaneID(ego).
                    lane=api.getLaneID(ego)
                    # Run this branch when the negation of the result of lane.startswith(the text ':') and the
                    # text '_in_' belongs to lane.
                    if not lane.startswith(':') and '_in_' in lane:
                        # Attempt the enclosed operations and route matching exceptions to the handlers below.
                        try:
                            # Call api.setStop with the supplied arguments.
                            api.setStop(ego,api.getRoadID(ego),
                                # Supply pos as the result of runner.traci.lane.getLength(lane) minus 0.001.
                                pos=runner.traci.lane.getLength(lane)-0.001,
                                # Supply laneIndex as the result of api.getLaneIndex(ego).
                                # Supply duration as 1000000.0.
                                laneIndex=api.getLaneIndex(ego),duration=1e6)
                            # Add ego to planned_holds.
                            planned_holds.add(ego)
                        # Handle runner.traci.TraCIException using the recovery steps below.
                        except runner.traci.TraCIException:
                            # Keep this block syntactically valid without performing an operation.
                            pass  # Preserve the original safe speed cap on rejection.
                # Run this branch when speed is less than 0 and ego belongs to planned_holds.
                elif speed<0 and ego in planned_holds:
                    # Call api.setStop with the supplied arguments.
                    api.setStop(ego,api.getRoadID(ego),
                        # Supply pos as the result of runner.traci.lane.getLength(the result of
                        # api.getLaneID(ego)) minus 0.001.
                        pos=runner.traci.lane.getLength(api.getLaneID(ego))-0.001,
                        # Supply laneIndex as the result of api.getLaneIndex(ego).
                        # Supply duration as 0.
                        laneIndex=api.getLaneIndex(ego),duration=0)
                    # Remove ego from planned_holds.
                    planned_holds.remove(ego)
            # Set record to a dictionary built from the supplied values.
            record=dict(timestamp=observer.now,ego_id=ego,actual_traci_speed_request=speed,
                # Supply accepted as True.
                # Supply decision as ego from observer.latest; use None if absent.
                accepted=True,decision=observer.latest.get(ego))
            # Append record to commands.
            commands.append(record)
            # Enter the result of (root / 'traci_speed_commands.jsonl').open(the text 'a') as stream and run the
            # enclosed operations within that context.
            with (root/'traci_speed_commands.jsonl').open('a',encoding='utf-8') as stream:
                # Call stream.write with the supplied arguments.
                stream.write(json.dumps(record,default=str)+'\n')
            # Return response to the caller.
            return response
        # Set runner.traci.vehicle.setSpeed to traced_speed.
        runner.traci.vehicle.setSpeed=traced_speed
    # Set original to runner.BrowserStatePublisher.
    original=runner.BrowserStatePublisher
    # Set overlay to the result of NegotiationVisualHold().
    overlay=NegotiationVisualHold()
    # Set stats to a dictionary built from the supplied values.
    stats=dict(frames=0,moving_red=0,wrong_permission_color=0,highlight_overrides=0)
    # Define Publisher to group the state and operations declared below.
    # Base classes: original.
    # Instances expose the attributes and methods implemented in this class.
    class Publisher(original):
        # Publish using the inputs and processing steps below.
        # Input kwargs: the supplied kwargs.
        # Output: no explicit value; normal completion returns None.
        # Processing: iterate over the relevant records, then select branches using the stated conditions.
        def publish(self,**kwargs):
            # Set old to self._last_simulation_time.
            old=self._last_simulation_time
            # Call super().publish with the supplied arguments.
            super().publish(**kwargs)
            # Run this branch when old equals self._last_simulation_time or 'scientific_states' from kwargs; use
            # None if absent is the same object as None.
            # Return no value to the caller.
            if old==self._last_simulation_time or kwargs.get('scientific_states') is None:return
            # Set raw to self._last_payload.
            raw=self._last_payload
            # Set displayed to the result of overlay.apply(raw).
            displayed=overlay.apply(raw)
            # Set rows to an empty list.
            rows=[]
            # Iterate over displayed at 'vehicles', binding each item to vehicle.
            for vehicle in displayed['vehicles']:
                # Set current to vehicle['id'] from observer.latest; use an empty dictionary if absent.
                current=observer.latest.get(vehicle['id'],{})
                # Set row to a dictionary built from the supplied values.
                row=dict(vehicle=vehicle,decision=current)
                # Append row to rows.
                rows.append(row)
                # Run this branch when vehicle at 'display_state' equals the text 'BLOCKED' and vehicle at
                # 'speed_mps' is greater than 0.
                # Update stats['moving_red'] to its current value plus 1.
                if vehicle['display_state']=='BLOCKED' and vehicle['speed_mps']>0:stats['moving_red']+=1
                # Set expected to the text 'READY' when 'permission' from current; use None if absent equals the
                # text 'PERMITTED', otherwise the text 'APPROACHING' when 'display_stage' from vehicle; use None
                # if absent equals the text 'ORDINARY_APPROACH', otherwise the text 'BLOCKED'.
                expected=('READY' if current.get('permission')=='PERMITTED' else
                    # Evaluate the text 'APPROACHING' when 'display_stage' from vehicle; use None if absent equals
                    # the text 'ORDINARY_APPROACH', otherwise the text 'BLOCKED' as part of the enclosing
                    # expression.
                    'APPROACHING' if vehicle.get('display_stage')=='ORDINARY_APPROACH' else 'BLOCKED')
                # Run this branch when current and vehicle at 'display_state' differs from expected.
                # Update stats['wrong_permission_color'] to its current value plus 1.
                if current and vehicle['display_state']!=expected:stats['wrong_permission_color']+=1
                # Set before to the next item from a lazy sequence of v for v in raw at 'vehicles'; retain entries
                # satisfying v at 'id' equals vehicle at 'id'.
                before=next(v for v in raw['vehicles'] if v['id']==vehicle['id'])
                # Run this branch when before at 'display_state' differs from vehicle at 'display_state'.
                # Update stats['highlight_overrides'] to its current value plus 1.
                if before['display_state']!=vehicle['display_state']:stats['highlight_overrides']+=1
            # Update stats['frames'] to its current value plus 1.
            stats['frames']+=1
            # Enter the result of (root / 'synchronized_frames.jsonl').open(the text 'a') as stream and run the
            # enclosed operations within that context.
            with (root/'synchronized_frames.jsonl').open('a',encoding='utf-8') as stream:
                # Call stream.write with the supplied arguments.
                stream.write(json.dumps(dict(timestamp=raw['simulation_time'],
                    # Supply status as raw at 'status'.
                    # Supply mappo as raw at 'mappo_invocation'.
                    status=raw['status'],mappo=raw['mappo_invocation'],
                    # Supply default as str.
                    # Supply rows as rows.
                    rows=rows),default=str)+'\n')
    # Set runner.BrowserStatePublisher to Publisher.
    runner.BrowserStatePublisher=Publisher
    # Run this branch when args.fault equals the text 'stale_commitment'.
    if args.fault=='stale_commitment':
        # Import replace from dataclasses for the operations below.
        from dataclasses import replace
        # Set deliver to runner._deliver_pair_commitments.
        deliver=runner._deliver_pair_commitments
        # Stale delivery using the inputs and processing steps below.
        # Input a: the supplied a.
        # Input kw: the supplied kw.
        # Output: a dictionary of ego mapped to a tuple built from a lazy sequence of the result of replace(c) for
        # c in messages for (ego, messages) in key/value pairs from deliver(*a, **kw).
        def stale_delivery(*a,**kw):
            # Return a dictionary of ego mapped to a tuple built from a lazy sequence of the result of replace(c)
            # for c in messages for (ego, messages) in key/value pairs from deliver(*a, **kw) to the caller.
            return {ego:tuple(replace(c,agreement_id=('STALE_DIAGNOSTIC_EPOCH',)) for c in messages)
                    # Supply the unpacked keyword arguments as kw.
                    for ego,messages in deliver(*a,**kw).items()}
        # Set runner._deliver_pair_commitments to stale_delivery.
        runner._deliver_pair_commitments=stale_delivery
    # Run this branch when args.fault equals the text 'mandatory_constraint_cycle'.
    if args.fault=='mandatory_constraint_cycle':
        # Synthetic contradictory constraint transport, not a legal traffic
        # scenario or a claim that the adopted turning rules contain this cycle.
        # Import replace from dataclasses for the operations below.
        from dataclasses import replace
        # Import EgoCoordinationCommitment from negotiation_execution for the operations below.
        from negotiation_execution import EgoCoordinationCommitment
        # Set original_context to runner.EgoExecutionContext.
        original_context=runner.EgoExecutionContext
        # Cyclic context using the inputs and processing steps below.
        # Input a: the supplied a.
        # Input kw: the supplied kw.
        # Output: return the value selected by the matching return branch below.
        # Processing: select branches using the stated conditions.
        def cyclic_context(*a,**kw):
            # Set context to the result of original_context(the unpacked values from a).
            context=original_context(*a,**kw)
            # Set rows to context.fallback_endpoint_evidence.
            rows=context.fallback_endpoint_evidence
            # Run this branch when the negation of context.mappo_receipt or the number of entries in rows is less
            # than 2.
            # Return context to the caller.
            if not context.mappo_receipt or len(rows)<2:return context
            # Set (first, second) to a tuple containing rows[0].sender_id, rows[1].sender_id.
            first,second=rows[0].sender_id,rows[1].sender_id
            # Set injected to a tuple containing the result of EgoCoordinationCommitment(first, second,
            # context.coordination_epoch), the result of...
            injected=(EgoCoordinationCommitment(first,second,context.coordination_epoch),
                      # Include the result of EgoCoordinationCommitment(second, first, context.coordination_epoch)
                      # in this tuple.
                      EgoCoordinationCommitment(second,first,context.coordination_epoch))
            # Local using the inputs and processing steps below.
            # Input sender: the supplied sender.
            # Output: a tuple built from a lazy sequence of c for c in injected; retain entries satisfying sender
            # belongs to a tuple containing c.yielding_vehicle_id, c.priority_vehicle_id.
            # Return a tuple built from a lazy sequence of c for c in injected; retain entries satisfying sender
            # belongs to a tuple containing c.yielding_vehicle_id, c.priority_vehicle_id to the caller.
            def local(sender):return tuple(c for c in injected if sender in
                # Evaluate a tuple containing c.yielding_vehicle_id, c.priority_vehicle_id as part of the
                # enclosing expression.
                (c.yielding_vehicle_id,c.priority_vehicle_id))
            # Return the result of replace(context) to the caller.
            return replace(context,mandatory_commitments=context.mandatory_commitments+local(context.ego_id),
                # Supply fallback_endpoint_evidence as a tuple built from a lazy sequence of the result of
                # replace(row) for row in rows.
                # Supply mandatory as row.mandatory plus the result of local(row.sender_id).
                fallback_endpoint_evidence=tuple(replace(row,mandatory=row.mandatory+local(row.sender_id))
                    # Evaluate rows as part of the enclosing expression.
                    for row in rows))
        # Set runner.EgoExecutionContext to cyclic_context.
        runner.EgoExecutionContext=cyclic_context
    # Set hashes to an empty dictionary.
    hashes={}
    # Iterate over a list containing the text 'runtime_simulation/runner.py', the text
    # 'runtime_simulation/browser_state.py', the text..., binding each item to relative.
    for relative in ['runtime_simulation/runner.py','runtime_simulation/browser_state.py',
                     'negotiation_execution/ego_controller.py','negotiation_execution/replay.py',
                     'negotiation_learning/movement_declarations.py']:
        # Set hashes[relative] to the hexadecimal digest from hashlib.sha256((BASE / relative).read_bytes()).
        hashes[relative]=hashlib.sha256((BASE/relative).read_bytes()).hexdigest()
    # Set started to the monotonic clock time.
    started=time.monotonic()
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
        def publish(self,sender,message):
            # Call super().publish with the supplied arguments.
            super().publish(sender,message)
            # Run this branch when message is the same object as None or the text '_S_' does not belong to sender.
            # Return no value to the caller.
            if message is None or '_S_' not in sender:return
            # Import replace from dataclasses for the operations below.
            from dataclasses import replace
            # Run this branch when args.fault equals the text 'missing_declaration'.
            # Remove the requested entry from self.messages.
            if args.fault=='missing_declaration':self.messages.pop(sender,None)
            # Run this branch when args.fault equals the text 'stale_declaration'.
            # Set self.messages[sender] to a list containing the result of replace(message).
            elif args.fault=='stale_declaration':self.messages[sender]=[replace(message,timestamp=-1)]
            # Run this branch when args.fault equals the text 'invalid_declaration'.
            # Set self.messages[sender] to a list containing the result of replace(message).
            elif args.fault=='invalid_declaration':self.messages[sender]=[replace(message,manoeuvre='REVERSE')]
            # Run this branch when args.fault equals the text 'incorrect_declaration'.
            # Set self.messages[sender] to a list containing the result of replace(message).
            elif args.fault=='incorrect_declaration':self.messages[sender]=[replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT')]
            # Run this branch when args.fault equals the text 'contradictory_declaration'.
            # Append message to self.messages[sender].
            elif args.fault=='contradictory_declaration':self.messages[sender].append(message)
    # Enter the result of (root / 'runtime.log').open(the text 'w') as log; the result of
    # contextlib.redirect_stdout(log); the result of contextlib.redirect_stderr(log) and run the enclosed
    # operations within that context.
    with (root/'runtime.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        # Set result to the result of runner.run_runtime_simulation().
        result=runner.run_runtime_simulation(duration_seconds=args.duration,schedule=scenario.schedule(),
            # Supply admission_waves as scenario.admission_waves.
            # Supply admission_mode as scenario.admission_mode.
            admission_waves=scenario.admission_waves,admission_mode=scenario.admission_mode,
            # Supply scenario_id as args.scenario.
            # Supply runtime_observer as observer.
            # Supply web_live as True.
            scenario_id=args.scenario,runtime_observer=observer,web_live=True,
            # Supply browser_state_path as root joined with the path segment 'live_state.json'.
            # Supply persist_presentation as False.
            # Supply return_failed_result as True.
            browser_state_path=root/'live_state.json',persist_presentation=False,return_failed_result=True,
            # Supply presentation_run_id as args.presentation_run_id.
            # Supply stop_request_path as args.stop_request_path.
            presentation_run_id=args.presentation_run_id,stop_request_path=args.stop_request_path,
            # Supply movement_protocol_factory as FaultChannel when args.fault and args.fault differs from the
            # text 'stale_commitment', otherwise None.
            movement_protocol_factory=FaultChannel if args.fault and args.fault!='stale_commitment' else None)
    # Set receipt to a dictionary built from the supplied values.
    receipt=dict(version=args.version,scenario=args.scenario,injected_fault=args.fault,wall_seconds=time.monotonic()-started,
        # Supply stats as stats.
        # Supply entries as observer.entry_records.
        # Supply unauthorized_entries as the sum of a lazy sequence of the negation of r at 'authorized' for r in
        # observer.entry_records.
        stats=stats,entries=observer.entry_records,unauthorized_entries=sum(not r['authorized'] for r in observer.entry_records),
        # Supply actual_speed_commands as the number of entries in commands.
        # Supply native_speed_releases as the sum of a lazy sequence of r at 'actual_traci_speed_request' equals
        # the negative of 1 for r in commands.
        actual_speed_commands=len(commands),native_speed_releases=sum(r['actual_traci_speed_request']==-1 for r in commands),
        # Supply source_hashes as hashes.
        # Supply run_status as result at 'run_status'.
        # Supply metrics as the result of observer.result(result).
        source_hashes=hashes,run_status=result['run_status'],metrics=observer.result(result),
        # Supply policy_hash as result at 'policy_sha256_after'.
        # Supply evidence as the text 'DIAGNOSTIC_NOT_FINAL'.
        policy_hash=result['policy_sha256_after'],evidence='DIAGNOSTIC_NOT_FINAL')
    # Write the supplied text to (root / 'runtime_result.json').
    (root/'runtime_result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    # Write the supplied text to (root / 'receipt.json').
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2,default=str),encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'entries','metrics','source_hashes'}},default=str))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
