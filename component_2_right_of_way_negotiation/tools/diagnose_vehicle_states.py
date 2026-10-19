"""Synchronized real-SUMO/UI audit; observation hooks never grant permission."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import time

BASE=Path(__file__).resolve().parents[1]
sys.argv[0]=str(Path(__file__).resolve())
sys.path.insert(0,str(BASE.parent));sys.path.insert(0,str(BASE))
os.chdir(BASE)
from diagnose_live_deadlock import DiagnosticTelemetry
from runtime_simulation import runner
from runtime_simulation.scenarios import get_scenario
from conflict import MapPathManager
from socialmind_drive_showcase.pages.component2_live_view import NegotiationVisualHold


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--scenario',required=True)
    parser.add_argument('--duration',type=float,required=True)
    parser.add_argument('--version',required=True)
    parser.add_argument('--presentation-run-id')
    parser.add_argument('--stop-request-path')
    parser.add_argument('--command-trace',action='store_true')
    parser.add_argument('--native-junction-trace',action='store_true')
    parser.add_argument('--planned-holds-probe',action='store_true',
        help='Separate execution-integration experiment, never enabled by production runtime')
    parser.add_argument('--fault',choices=['stale_commitment','missing_declaration','stale_declaration',
        'invalid_declaration','incorrect_declaration','contradictory_declaration',
        'mandatory_constraint_cycle'],default=None)
    args=parser.parse_args()
    root=BASE/'results/vehicle_state_consistency/20261016'/args.version/(args.scenario+('__'+args.fault if args.fault else ''))
    root.mkdir(parents=True,exist_ok=False)
    scenario=get_scenario(args.scenario)
    paths=MapPathManager()
    class Observer(DiagnosticTelemetry):
        def __init__(self):
            super().__init__(scenario.schedule(),root)
            self.latest={};self.entered=set();self.entry_records=[]
        def observe(self,now,states,*rest):
            super().observe(now,states,*rest)
            if args.native_junction_trace and int(now) != getattr(self, 'last_native_second', -1):
                self.last_native_second = int(now)
                with (root/'native_junctions.jsonl').open('a',encoding='utf-8') as stream:
                    for ego, state in states.items():
                        stream.write(json.dumps(dict(timestamp=now,ego_id=ego,speed=state['speed'],
                            native_speed=runner.traci.vehicle.getSpeedWithoutTraCI(ego),
                            next_links=runner.traci.vehicle.getNextLinks(ego),
                            junction_foes=runner.traci.vehicle.getJunctionFoes(ego,100)),default=str)+'\n')
            for ego,state in states.items():
                progress,_,error=paths.resolve_front_bumper_path_progress(state,paths.paths[self.movements[ego]])
                if not error and progress>=0 and ego not in self.entered:
                    prior=self.latest.get(ego,{})
                    authorized=prior.get('permission')=='PERMITTED'
                    self.entry_records.append(dict(ego_id=ego,timestamp=now,authorized=authorized,
                        prior_decision=prior,progress=progress))
                    self.entered.add(ego)
        def decision_trace(self,context,decision,admission_state):
            progress,_,error=paths.resolve_front_bumper_path_progress(context.ego_state,paths.paths[context.movement_path_id])
            self.latest[context.ego_id]=dict(timestamp=context.timestamp,
                permission=decision.permission,reason=decision.reason,
                physical_speed=context.ego_state['speed'],
                front_bumper_position=context.ego_state['position'],
                requested_speed=decision.requested_speed_mps,
                blocked_zones=decision.blocked_zones,admission_state=admission_state,
                mandatory=[vars(c) for c in context.mandatory_commitments],
                fallback_pairs=decision.fallback_pairs,
                coordination_epoch=context.coordination_epoch,
                coordination_complete=context.coordination_complete,
                mappo_receipt=context.mappo_receipt,
                distance_to_entry=None if error else -progress)
            super().decision_trace(context,decision,admission_state)
    observer=Observer()
    actual_sample=runner.PanelDeterministicInferenceProvider._sample
    def record_actor_sample(self,*a,**kw):
        from dataclasses import is_dataclass, fields
        from collections.abc import Mapping
        def serialize(value):
            if is_dataclass(value):return {f.name:serialize(getattr(value,f.name)) for f in fields(value)}
            if isinstance(value,Mapping):return {k:serialize(v) for k,v in value.items()}
            if isinstance(value,(tuple,list)):return [serialize(v) for v in value]
            return value
        began=time.perf_counter_ns()
        sample=actual_sample(self,*a,**kw)
        assert sample.hard_action_mask[sample.selected_action_index]
        with (root/'actor_inputs_and_actions.jsonl').open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(dict(inference_started_wall_ns=began,
                inference_completed_wall_ns=time.perf_counter_ns(),
                actual_factor=serialize(sample)),default=str)+'\n')
        return sample
    runner.PanelDeterministicInferenceProvider._sample=record_actor_sample
    commands=[]
    planned_holds=set()
    if args.command_trace:
        actual_set_speed=runner.traci.vehicle.setSpeed
        def traced_speed(ego,speed):
            response=actual_set_speed(ego,speed)
            if args.planned_holds_probe:
                api=runner.traci.vehicle
                if speed>=0 and ego not in planned_holds:
                    lane=api.getLaneID(ego)
                    if not lane.startswith(':') and '_in_' in lane:
                        try:
                            api.setStop(ego,api.getRoadID(ego),
                                pos=runner.traci.lane.getLength(lane)-0.001,
                                laneIndex=api.getLaneIndex(ego),duration=1e6)
                            planned_holds.add(ego)
                        except runner.traci.TraCIException:
                            pass  # Preserve the original safe speed cap on rejection.
                elif speed<0 and ego in planned_holds:
                    api.setStop(ego,api.getRoadID(ego),
                        pos=runner.traci.lane.getLength(api.getLaneID(ego))-0.001,
                        laneIndex=api.getLaneIndex(ego),duration=0)
                    planned_holds.remove(ego)
            record=dict(timestamp=observer.now,ego_id=ego,actual_traci_speed_request=speed,
                accepted=True,decision=observer.latest.get(ego))
            commands.append(record)
            with (root/'traci_speed_commands.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(record,default=str)+'\n')
            return response
        runner.traci.vehicle.setSpeed=traced_speed
    original=runner.BrowserStatePublisher
    overlay=NegotiationVisualHold()
    stats=dict(frames=0,moving_red=0,wrong_permission_color=0,highlight_overrides=0)
    class Publisher(original):
        def publish(self,**kwargs):
            old=self._last_simulation_time
            super().publish(**kwargs)
            if old==self._last_simulation_time or kwargs.get('scientific_states') is None:return
            raw=self._last_payload
            displayed=overlay.apply(raw)
            rows=[]
            for vehicle in displayed['vehicles']:
                current=observer.latest.get(vehicle['id'],{})
                row=dict(vehicle=vehicle,decision=current)
                rows.append(row)
                if vehicle['display_state']=='BLOCKED' and vehicle['speed_mps']>0:stats['moving_red']+=1
                expected=('READY' if current.get('permission')=='PERMITTED' else
                    'APPROACHING' if vehicle.get('display_stage')=='ORDINARY_APPROACH' else 'BLOCKED')
                if current and vehicle['display_state']!=expected:stats['wrong_permission_color']+=1
                before=next(v for v in raw['vehicles'] if v['id']==vehicle['id'])
                if before['display_state']!=vehicle['display_state']:stats['highlight_overrides']+=1
            stats['frames']+=1
            with (root/'synchronized_frames.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(dict(timestamp=raw['simulation_time'],
                    status=raw['status'],mappo=raw['mappo_invocation'],
                    rows=rows),default=str)+'\n')
    runner.BrowserStatePublisher=Publisher
    if args.fault=='stale_commitment':
        from dataclasses import replace
        deliver=runner._deliver_pair_commitments
        def stale_delivery(*a,**kw):
            return {ego:tuple(replace(c,agreement_id=('STALE_DIAGNOSTIC_EPOCH',)) for c in messages)
                    for ego,messages in deliver(*a,**kw).items()}
        runner._deliver_pair_commitments=stale_delivery
    if args.fault=='mandatory_constraint_cycle':
        # Synthetic contradictory constraint transport, not a legal traffic
        # scenario or a claim that the adopted turning rules contain this cycle.
        from dataclasses import replace
        from negotiation_execution import EgoCoordinationCommitment
        original_context=runner.EgoExecutionContext
        def cyclic_context(*a,**kw):
            context=original_context(*a,**kw)
            rows=context.fallback_endpoint_evidence
            if not context.mappo_receipt or len(rows)<2:return context
            first,second=rows[0].sender_id,rows[1].sender_id
            injected=(EgoCoordinationCommitment(first,second,context.coordination_epoch),
                      EgoCoordinationCommitment(second,first,context.coordination_epoch))
            def local(sender):return tuple(c for c in injected if sender in
                (c.yielding_vehicle_id,c.priority_vehicle_id))
            return replace(context,mandatory_commitments=context.mandatory_commitments+local(context.ego_id),
                fallback_endpoint_evidence=tuple(replace(row,mandatory=row.mandatory+local(row.sender_id))
                    for row in rows))
        runner.EgoExecutionContext=cyclic_context
    hashes={}
    for relative in ['runtime_simulation/runner.py','runtime_simulation/browser_state.py',
                     'negotiation_execution/ego_controller.py','negotiation_execution/replay.py',
                     'negotiation_learning/movement_declarations.py']:
        hashes[relative]=hashlib.sha256((BASE/relative).read_bytes()).hexdigest()
    started=time.monotonic()
    from negotiation_learning.movement_declarations import MovementDeclarationBus
    class FaultChannel(MovementDeclarationBus):
        def publish(self,sender,message):
            super().publish(sender,message)
            if message is None or '_S_' not in sender:return
            from dataclasses import replace
            if args.fault=='missing_declaration':self.messages.pop(sender,None)
            elif args.fault=='stale_declaration':self.messages[sender]=[replace(message,timestamp=-1)]
            elif args.fault=='invalid_declaration':self.messages[sender]=[replace(message,manoeuvre='REVERSE')]
            elif args.fault=='incorrect_declaration':self.messages[sender]=[replace(message,manoeuvre='LEFT',path_id='S_IN_0_LEFT')]
            elif args.fault=='contradictory_declaration':self.messages[sender].append(message)
    with (root/'runtime.log').open('w',encoding='utf-8') as log,contextlib.redirect_stdout(log),contextlib.redirect_stderr(log):
        result=runner.run_runtime_simulation(duration_seconds=args.duration,schedule=scenario.schedule(),
            admission_waves=scenario.admission_waves,admission_mode=scenario.admission_mode,
            scenario_id=args.scenario,runtime_observer=observer,web_live=True,
            browser_state_path=root/'live_state.json',persist_presentation=False,return_failed_result=True,
            presentation_run_id=args.presentation_run_id,stop_request_path=args.stop_request_path,
            movement_protocol_factory=FaultChannel if args.fault and args.fault!='stale_commitment' else None)
    receipt=dict(version=args.version,scenario=args.scenario,injected_fault=args.fault,wall_seconds=time.monotonic()-started,
        stats=stats,entries=observer.entry_records,unauthorized_entries=sum(not r['authorized'] for r in observer.entry_records),
        actual_speed_commands=len(commands),native_speed_releases=sum(r['actual_traci_speed_request']==-1 for r in commands),
        source_hashes=hashes,run_status=result['run_status'],metrics=observer.result(result),
        policy_hash=result['policy_sha256_after'],evidence='DIAGNOSTIC_NOT_FINAL')
    (root/'runtime_result.json').write_text(json.dumps(result,indent=2,default=str),encoding='utf-8')
    (root/'receipt.json').write_text(json.dumps(receipt,indent=2,default=str),encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'entries','metrics','source_hashes'}},default=str))


if __name__=='__main__':main()
