"""Real SUMO queue diagnostics; qualitative, never frozen evaluation output."""
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
# Call sys.path.insert with the supplied arguments.
# Call os.chdir with the supplied arguments.
sys.path.insert(0,str(BASE));os.chdir(BASE)
# Import DiagnosticTelemetry from diagnose_live_deadlock for the operations below.
from diagnose_live_deadlock import DiagnosticTelemetry
# Import runner from runtime_simulation for the operations below.
from runtime_simulation import runner
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario
# Import select_queue_heads from runtime_simulation.queue_heads for the operations below.
from runtime_simulation.queue_heads import select_queue_heads


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set p to the result of argparse.ArgumentParser().
    # Call p.add_argument with the supplied arguments.
    p=argparse.ArgumentParser();p.add_argument('--phase',required=True)
    # Call p.add_argument with the supplied arguments.
    p.add_argument('--scenario',default='congested_four_approach')
    # Call p.add_argument with the supplied arguments.
    p.add_argument('--mode',choices=['proposed','rules-only'],default='proposed')
    # Call p.add_argument with the supplied arguments.
    # Set a to the result of p.parse_args().
    p.add_argument('--duration',type=float,default=None);a=p.parse_args()
    # Set out to BASE joined with the path segment 'results/final_demonstrations/v1' divided by a.phase divided by
    # a.scenario plus the text '__' plus a.mode.
    out=BASE/'results/final_demonstrations/v1'/a.phase/(a.scenario+'__'+a.mode)
    # Create the directory requested by out.
    out.mkdir(parents=True,exist_ok=False)
    # Set scenario to the result of get_scenario(a.scenario).
    scenario=get_scenario(a.scenario)
    # Set files to a list containing the text 'runtime_simulation/runner.py', the text
    # 'negotiation_execution/ego_controller.py', the text...
    files=['runtime_simulation/runner.py','negotiation_execution/ego_controller.py',
           'negotiation_execution/native_hold.py','runtime_simulation/queue_heads.py',
           'runtime_simulation/scenario_catalog.json','runtime_simulation/scenarios.py']
    # Write the supplied text to (out / 'source_hashes.json').
    (out/'source_hashes.json').write_text(json.dumps({s:hashlib.sha256((BASE/s).read_bytes()).hexdigest() for s in files},indent=2))
    # Preserve just the execution source needed to identify this revision.
    # Iterate over files sliced by :3, binding each item to s.
    for s in files[:3]:
        # Set target to out joined with the path segment 'source' divided by s.
        # Create the directory requested by target.parent.
        # Write the supplied bytes to target.
        target=out/'source'/s;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((BASE/s).read_bytes())
    # Define Observer to group the state and operations declared below.
    # Base classes: DiagnosticTelemetry.
    # Instances expose the attributes and methods implemented in this class.
    class Observer(DiagnosticTelemetry):
        # Initialize the instance attributes and collaborators used by the operations below.
        # Output: no explicit value; normal completion returns None.
        def __init__(self):
            # Call super().__init__ with the supplied arguments.
            super().__init__(scenario.schedule(),out)
            # Set self.latest to an empty dictionary.
            # Set self.entered to an empty set.
            # Set self.entry_records to an empty list.
            # Set self.heads to an empty tuple.
            # Set self.promotions to an empty list.
            self.latest={};self.entered=set();self.entry_records=[];self.heads=();self.promotions=[]
            # Set self.sample_at to the negative of 1.0.
            # Set self.safe_delay to an empty dictionary.
            # Set self.max_delay to an empty dictionary.
            # Set self.delay_seconds to an empty dictionary.
            self.sample_at=-1.;self.safe_delay={};self.max_delay={};self.delay_seconds={}
        # Decision trace using the inputs and processing steps below.
        # Input c: the supplied c.
        # Input d: the supplied d.
        # Input admission: the supplied admission.
        # Output: no explicit value; normal completion returns None.
        def decision_trace(self,c,d,admission):
            # Set self.latest[c.ego_id] to a dictionary built from the supplied values.
            self.latest[c.ego_id]=dict(permission=d.permission,reason=d.reason,
                # Supply eligible as c.negotiation_eligible.
                # Supply requested_speed as d.requested_speed_mps.
                eligible=c.negotiation_eligible,requested_speed=d.requested_speed_mps,
                # Supply restrictions as a list of the result of vars(r) for r in d.speed_constraints.
                # Supply admission as admission.
                restrictions=[vars(r) for r in d.speed_constraints],admission=admission)
            # Call super().decision_trace with the supplied arguments.
            super().decision_trace(c,d,admission)
        # Observe using the inputs and processing steps below.
        # Input now: the time used for this operation.
        # Input states: the supplied states.
        # Input lifecycle: the supplied lifecycle.
        # Input movements: the supplied movements.
        # Input paths: the supplied paths.
        # Input zones: the supplied zones.
        # Input traci: the supplied traci.
        # Output: no explicit value; normal completion returns None.
        # Processing: iterate over the relevant records, then select branches using the stated conditions.
        def observe(self,now,states,lifecycle,movements,paths,zones,traci):
            # Call super().observe with the supplied arguments.
            super().observe(now,states,lifecycle,movements,paths,zones,traci)
            # Set heads to the result of select_queue_heads(states, paths, movements).
            heads=select_queue_heads(states,paths,movements)
            # Iterate over a set built from heads minus a set built from self.heads, binding each item to ego.
            # Append a dictionary built from the supplied values to self.promotions.
            for ego in set(heads)-set(self.heads):self.promotions.append(dict(id=ego,time=now))
            # Set self.heads to heads.
            self.heads=heads
            # Iterate over key/value pairs from states, binding each item to (ego, s).
            for ego,s in states.items():
                # Set (progress, _, error) to the result of paths.resolve_front_bumper_path_progress(s,
                # paths.paths at movements[ego]).
                progress,_,error=paths.resolve_front_bumper_path_progress(s,paths.paths[movements[ego]])
                # Run this branch when the negation of error and progress is at least 0 and ego does not belong to
                # self.entered.
                if not error and progress>=0 and ego not in self.entered:
                    # Add ego to self.entered.
                    # Append a dictionary built from the supplied values to self.entry_records.
                    self.entered.add(ego);self.entry_records.append(dict(id=ego,time=now,
                        # Supply authorized as 'permission' from self.latest.get(ego, {}); use None if absent
                        # equals the text 'PERMITTED'.
                        authorized=self.latest.get(ego,{}).get('permission')=='PERMITTED'))
            # Run this branch when now is less than self.sample_at.
            # Return no value to the caller.
            if now<self.sample_at:return
            # Set self.sample_at to now plus 0.119.
            self.sample_at=now+.119
            # Set rows to an empty list.
            # Set api to traci.vehicle.
            rows=[];api=traci.vehicle
            # Iterate over key/value pairs from states, binding each item to (ego, s).
            for ego,s in states.items():
                # Set path to paths.paths at movements[ego].
                # Set incoming to s at 'lane_id' equals path.incoming_lane_id.
                path=paths.paths[movements[ego]];incoming=s['lane_id']==path.incoming_lane_id
                # Set leader to the result of api.getLeader(ego, 1000.0).
                leader=api.getLeader(ego,1000.)
                # Set leader_id to leader at 0 when leader and leader at 0, otherwise None.
                leader_id=leader[0] if leader and leader[0] else None
                # Set gap_excluding_min_gap to leader at 1 when leader_id, otherwise None.
                gap_excluding_min_gap=leader[1] if leader_id else None
                # Set minimum_gap to the result of api.getMinGap(ego).
                minimum_gap=api.getMinGap(ego)
                # Set gap to gap_excluding_min_gap plus minimum_gap when leader_id, otherwise None.
                gap=gap_excluding_min_gap+minimum_gap if leader_id else None
                # Set lead to leader_id from states; use None if absent.
                lead=states.get(leader_id)
                # Set distance to s at 'lane_length' minus s at 'lane_position' when incoming, otherwise None.
                distance=s['lane_length']-s['lane_position'] if incoming else None
                # Set follow_speed to the result of api.getFollowSpeed(ego, s at 'speed', gap, lead at 'speed',
                # lead at 'comfortable_deceleration_mps2', leader_id) when lead, otherwise None.
                follow_speed=(api.getFollowSpeed(ego,s['speed'],gap,lead['speed'],
                    # Supply lead at 'comfortable_deceleration_mps2' to api.getFollowSpeed.
                    lead['comfortable_deceleration_mps2'],leader_id) if lead else None)
                # Set stop_speed to the result of api.getStopSpeed(ego, s at 'speed', distance) when incoming,
                # otherwise None.
                stop_speed=api.getStopSpeed(ego,s['speed'],distance) if incoming else None
                # Set dec to ego from self.latest; use an empty dictionary if absent.
                dec=self.latest.get(ego,{})
                # A diagnostic availability test, never a permission condition.
                # Set opportunity to a Boolean built from incoming and ego does not belong to heads and lead and
                # lead at 'speed' is greater than 0.5 and follow_speed is greater than s at 'speed' and stop_speed
                # is greater than s at 'speed' and gap is at least minimum_gap.
                opportunity=bool(incoming and ego not in heads and lead and lead['speed']>.5
                    # Evaluate follow_speed is greater than s at 'speed' as part of the enclosing expression.
                    and follow_speed>s['speed'] and stop_speed>s['speed'] and gap>=minimum_gap)
                # Set delayed to opportunity and s at 'speed' is less than 0.1.
                delayed=opportunity and s['speed']<.1
                # Run this branch when delayed.
                if delayed:
                    # Call self.safe_delay.setdefault with the supplied arguments.
                    self.safe_delay.setdefault(ego,now)
                    # Set self.max_delay[ego] to the maximum of ego from self.max_delay; use 0.0 if absent, now
                    # minus self.safe_delay at ego plus 0.12.
                    self.max_delay[ego]=max(self.max_delay.get(ego,0.),now-self.safe_delay[ego]+.12)
                    # Set self.delay_seconds[ego] to ego from self.delay_seconds; use 0.0 if absent plus 0.12.
                    self.delay_seconds[ego]=self.delay_seconds.get(ego,0.)+.12
                # Remove the requested entry from self.safe_delay.
                else:self.safe_delay.pop(ego,None)
                # Append a dictionary built from the supplied values to rows.
                rows.append(dict(id=ego,approach=movements[ego][0],position=s['position'],lane=s['lane_id'],
                    # Supply lane_position as s at 'lane_position'.
                    # Supply speed as s at 'speed'.
                    # Supply leader_id as leader_id.
                    lane_position=s['lane_position'],speed=s['speed'],leader_id=leader_id,
                    # Supply leader_position as lead at 'position' when lead, otherwise None.
                    # Supply leader_speed as lead at 'speed' when lead, otherwise None.
                    leader_position=lead['position'] if lead else None,leader_speed=lead['speed'] if lead else None,
                    # Supply bumper_gap_m as gap.
                    # Supply traci_gap_excluding_min_gap as gap_excluding_min_gap.
                    # Supply min_gap_m as minimum_gap.
                    bumper_gap_m=gap,traci_gap_excluding_min_gap=gap_excluding_min_gap,min_gap_m=minimum_gap,
                    # Supply distance_to_stop_m as distance.
                    # Supply native_follow_speed_mps as follow_speed.
                    # Supply native_stop_speed_mps as stop_speed.
                    distance_to_stop_m=distance,native_follow_speed_mps=follow_speed,native_stop_speed_mps=stop_speed,
                    # Supply native_speed_without_traci as the result of api.getSpeedWithoutTraCI(ego).
                    # Supply speed_mode as the result of api.getSpeedMode(ego).
                    native_speed_without_traci=api.getSpeedWithoutTraCI(ego),speed_mode=api.getSpeedMode(ego),
                    # Supply native_stop_state as the result of api.getStopState(ego).
                    # Supply queue_head as ego belongs to heads.
                    native_stop_state=api.getStopState(ego),queue_head=ego in heads,
                    # Supply safe_advancement_available as opportunity.
                    # Supply avoidable_standing_sample as delayed.
                    safe_advancement_available=opportunity,avoidable_standing_sample=delayed,
                    # Supply movement_authority as the text 'SUMO_NATIVE_FOLLOWING_WITH_ENTRY_STOP' when
                    # 'requested_speed' from dec; use None if absent is the same object as None, otherwise the
                    # text 'TRACI_SPEED_CAP_WITH_NATIVE_SAFETY'.
                    movement_authority='SUMO_NATIVE_FOLLOWING_WITH_ENTRY_STOP' if dec.get('requested_speed') is None else 'TRACI_SPEED_CAP_WITH_NATIVE_SAFETY',
                    # Supply previous_step_decision as dec.
                    previous_step_decision=dec))
            # Enter the result of (out / 'queue_timeseries.jsonl').open(the text 'a') as f and run the enclosed
            # operations within that context.
            with (out/'queue_timeseries.jsonl').open('a',encoding='utf-8') as f:
                # Call f.write with the supplied arguments.
                f.write(json.dumps(dict(time=now,vehicles=rows),default=str)+'\n')
    # Set observer to the result of Observer().
    observer=Observer()
    # Set actor to runner.PanelDeterministicInferenceProvider._sample.
    actor=runner.PanelDeterministicInferenceProvider._sample
    # Set factors to an empty list.
    factors=[]
    # Sample using the inputs and processing steps below.
    # Input args: the supplied args.
    # Input kwargs: the supplied kwargs.
    # Output: value.
    def sample(self,*args,**kwargs):
        # Set value to the result of actor(self, the unpacked values from args).
        value=actor(self,*args,**kwargs)
        # Require value.hard_action_mask at value.selected_action_index; otherwise raise AssertionError.
        assert value.hard_action_mask[value.selected_action_index]
        # Provider exposes the actual trace used by the runtime as well.
        # Append a dictionary built from the supplied values to factors.
        factors.append(dict(ego=value.ego_id,mask=value.hard_action_mask,index=value.selected_action_index))
        # Return value to the caller.
        return value
    # Set runner.PanelDeterministicInferenceProvider._sample to sample.
    runner.PanelDeterministicInferenceProvider._sample=sample
    # Set factory to None.
    factory=None
    # Run this branch when a.mode equals the text 'rules-only'.
    if a.mode=='rules-only':
        # Import RulesOnlyProvider from post_training_evaluation.baselines for the operations below.
        from post_training_evaluation.baselines import RulesOnlyProvider
        # Set factory to a callback that returns the result of RulesOnlyProvider(bundle, observer.arrivals).
        factory=lambda bundle:RulesOnlyProvider(bundle,observer.arrivals)
    # Set began to the monotonic clock time.
    began=time.monotonic()
    # Enter the result of (out / 'runtime.log').open(the text 'w') as f; the result of
    # contextlib.redirect_stdout(f); the result of contextlib.redirect_stderr(f) and run the enclosed operations
    # within that context.
    with (out/'runtime.log').open('w',encoding='utf-8') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        # Set result to the result of runner.run_runtime_simulation().
        result=runner.run_runtime_simulation(duration_seconds=a.duration or scenario.recommended_duration_seconds,
            # Supply schedule as the result of scenario.schedule().
            # Supply admission_waves as scenario.admission_waves.
            schedule=scenario.schedule(),admission_waves=scenario.admission_waves,
            # Supply admission_mode as scenario.admission_mode.
            # Supply scenario_id as scenario.scenario_id.
            admission_mode=scenario.admission_mode,scenario_id=scenario.scenario_id,
            # Supply web_live as True.
            # Supply browser_state_path as out joined with the path segment 'live_state.json'.
            # Supply runtime_observer as observer.
            web_live=True,browser_state_path=out/'live_state.json',runtime_observer=observer,
            # Supply provider_factory as factory.
            # Supply persist_presentation as False.
            # Supply return_failed_result as True.
            provider_factory=factory,persist_presentation=False,return_failed_result=True,
            # Supply presentation_run_id as a.phase plus '__' plus scenario.scenario_id plus the text '__' plus
            # a.mode.
            presentation_run_id=a.phase+'__'+scenario.scenario_id+'__'+a.mode)
    # Set metrics to the result of observer.result(result).
    metrics=observer.result(result)
    # Set receipt to a dictionary built from the supplied values.
    receipt=dict(classification='QUALITATIVE_PRESENTATION_REGRESSION',phase=a.phase,scenario=a.scenario,mode=a.mode,
        # Supply wall_seconds as the monotonic clock time minus began.
        # Supply status as result at 'run_status'.
        # Supply metrics as metrics.
        wall_seconds=time.monotonic()-began,status=result['run_status'],metrics=metrics,
        # Supply promotions as observer.promotions.
        # Supply entries as observer.entry_records.
        promotions=observer.promotions,entries=observer.entry_records,
        # Supply unauthorized_entries as the sum of a lazy sequence of the negation of r at 'authorized' for r in
        # observer.entry_records.
        unauthorized_entries=sum(not r['authorized'] for r in observer.entry_records),
        # Supply genuine_actor_factors as factors.
        # Supply maximum_avoidable_standing_seconds as observer.max_delay.
        genuine_actor_factors=factors,maximum_avoidable_standing_seconds=observer.max_delay,
        # Supply total_avoidable_standing_seconds as observer.delay_seconds.
        total_avoidable_standing_seconds=observer.delay_seconds,
        # Supply trip_completion_times as observer.completions.
        # Supply source_version as 'queue_following_protocol' from result; use the text 'V1_SPEED_CAP_FOLLOWERS'
        # if absent.
        trip_completion_times=observer.completions,source_version=result.get('queue_following_protocol','V1_SPEED_CAP_FOLLOWERS'))
    # Write the supplied text to (out / 'runtime_result.json').
    (out/'runtime_result.json').write_text(json.dumps(result,indent=2,default=str))
    # Write the supplied text to (out / 'receipt.json').
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2,default=str))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'metrics','promotions','entries','genuine_actor_factors','trip_completion_times'}}))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
