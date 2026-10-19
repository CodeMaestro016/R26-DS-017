"""Real SUMO queue diagnostics; qualitative, never frozen evaluation output."""
import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import time

BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE));os.chdir(BASE)
from diagnose_live_deadlock import DiagnosticTelemetry
from runtime_simulation import runner
from runtime_simulation.scenarios import get_scenario
from runtime_simulation.queue_heads import select_queue_heads


def main():
    p=argparse.ArgumentParser();p.add_argument('--phase',required=True)
    p.add_argument('--scenario',default='congested_four_approach')
    p.add_argument('--mode',choices=['proposed','rules-only'],default='proposed')
    p.add_argument('--duration',type=float,default=None);a=p.parse_args()
    out=BASE/'results/final_demonstrations/v1'/a.phase/(a.scenario+'__'+a.mode)
    out.mkdir(parents=True,exist_ok=False)
    scenario=get_scenario(a.scenario)
    files=['runtime_simulation/runner.py','negotiation_execution/ego_controller.py',
           'negotiation_execution/native_hold.py','runtime_simulation/queue_heads.py',
           'runtime_simulation/scenario_catalog.json','runtime_simulation/scenarios.py']
    (out/'source_hashes.json').write_text(json.dumps({s:hashlib.sha256((BASE/s).read_bytes()).hexdigest() for s in files},indent=2))
    # Preserve just the execution source needed to identify this revision.
    for s in files[:3]:
        target=out/'source'/s;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((BASE/s).read_bytes())
    class Observer(DiagnosticTelemetry):
        def __init__(self):
            super().__init__(scenario.schedule(),out)
            self.latest={};self.entered=set();self.entry_records=[];self.heads=();self.promotions=[]
            self.sample_at=-1.;self.safe_delay={};self.max_delay={};self.delay_seconds={}
        def decision_trace(self,c,d,admission):
            self.latest[c.ego_id]=dict(permission=d.permission,reason=d.reason,
                eligible=c.negotiation_eligible,requested_speed=d.requested_speed_mps,
                restrictions=[vars(r) for r in d.speed_constraints],admission=admission)
            super().decision_trace(c,d,admission)
        def observe(self,now,states,lifecycle,movements,paths,zones,traci):
            super().observe(now,states,lifecycle,movements,paths,zones,traci)
            heads=select_queue_heads(states,paths,movements)
            for ego in set(heads)-set(self.heads):self.promotions.append(dict(id=ego,time=now))
            self.heads=heads
            for ego,s in states.items():
                progress,_,error=paths.resolve_front_bumper_path_progress(s,paths.paths[movements[ego]])
                if not error and progress>=0 and ego not in self.entered:
                    self.entered.add(ego);self.entry_records.append(dict(id=ego,time=now,
                        authorized=self.latest.get(ego,{}).get('permission')=='PERMITTED'))
            if now<self.sample_at:return
            self.sample_at=now+.119
            rows=[];api=traci.vehicle
            for ego,s in states.items():
                path=paths.paths[movements[ego]];incoming=s['lane_id']==path.incoming_lane_id
                leader=api.getLeader(ego,1000.)
                leader_id=leader[0] if leader and leader[0] else None
                gap_excluding_min_gap=leader[1] if leader_id else None
                minimum_gap=api.getMinGap(ego)
                gap=gap_excluding_min_gap+minimum_gap if leader_id else None
                lead=states.get(leader_id)
                distance=s['lane_length']-s['lane_position'] if incoming else None
                follow_speed=(api.getFollowSpeed(ego,s['speed'],gap,lead['speed'],
                    lead['comfortable_deceleration_mps2'],leader_id) if lead else None)
                stop_speed=api.getStopSpeed(ego,s['speed'],distance) if incoming else None
                dec=self.latest.get(ego,{})
                # A diagnostic availability test, never a permission condition.
                opportunity=bool(incoming and ego not in heads and lead and lead['speed']>.5
                    and follow_speed>s['speed'] and stop_speed>s['speed'] and gap>=minimum_gap)
                delayed=opportunity and s['speed']<.1
                if delayed:
                    self.safe_delay.setdefault(ego,now)
                    self.max_delay[ego]=max(self.max_delay.get(ego,0.),now-self.safe_delay[ego]+.12)
                    self.delay_seconds[ego]=self.delay_seconds.get(ego,0.)+.12
                else:self.safe_delay.pop(ego,None)
                rows.append(dict(id=ego,approach=movements[ego][0],position=s['position'],lane=s['lane_id'],
                    lane_position=s['lane_position'],speed=s['speed'],leader_id=leader_id,
                    leader_position=lead['position'] if lead else None,leader_speed=lead['speed'] if lead else None,
                    bumper_gap_m=gap,traci_gap_excluding_min_gap=gap_excluding_min_gap,min_gap_m=minimum_gap,
                    distance_to_stop_m=distance,native_follow_speed_mps=follow_speed,native_stop_speed_mps=stop_speed,
                    native_speed_without_traci=api.getSpeedWithoutTraCI(ego),speed_mode=api.getSpeedMode(ego),
                    native_stop_state=api.getStopState(ego),queue_head=ego in heads,
                    safe_advancement_available=opportunity,avoidable_standing_sample=delayed,
                    movement_authority='SUMO_NATIVE_FOLLOWING_WITH_ENTRY_STOP' if dec.get('requested_speed') is None else 'TRACI_SPEED_CAP_WITH_NATIVE_SAFETY',
                    previous_step_decision=dec))
            with (out/'queue_timeseries.jsonl').open('a',encoding='utf-8') as f:
                f.write(json.dumps(dict(time=now,vehicles=rows),default=str)+'\n')
    observer=Observer()
    actor=runner.PanelDeterministicInferenceProvider._sample
    factors=[]
    def sample(self,*args,**kwargs):
        value=actor(self,*args,**kwargs)
        assert value.hard_action_mask[value.selected_action_index]
        # Provider exposes the actual trace used by the runtime as well.
        factors.append(dict(ego=value.ego_id,mask=value.hard_action_mask,index=value.selected_action_index))
        return value
    runner.PanelDeterministicInferenceProvider._sample=sample
    factory=None
    if a.mode=='rules-only':
        from post_training_evaluation.baselines import RulesOnlyProvider
        factory=lambda bundle:RulesOnlyProvider(bundle,observer.arrivals)
    began=time.monotonic()
    with (out/'runtime.log').open('w',encoding='utf-8') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
        result=runner.run_runtime_simulation(duration_seconds=a.duration or scenario.recommended_duration_seconds,
            schedule=scenario.schedule(),admission_waves=scenario.admission_waves,
            admission_mode=scenario.admission_mode,scenario_id=scenario.scenario_id,
            web_live=True,browser_state_path=out/'live_state.json',runtime_observer=observer,
            provider_factory=factory,persist_presentation=False,return_failed_result=True,
            presentation_run_id=a.phase+'__'+scenario.scenario_id+'__'+a.mode)
    metrics=observer.result(result)
    receipt=dict(classification='QUALITATIVE_PRESENTATION_REGRESSION',phase=a.phase,scenario=a.scenario,mode=a.mode,
        wall_seconds=time.monotonic()-began,status=result['run_status'],metrics=metrics,
        promotions=observer.promotions,entries=observer.entry_records,
        unauthorized_entries=sum(not r['authorized'] for r in observer.entry_records),
        genuine_actor_factors=factors,maximum_avoidable_standing_seconds=observer.max_delay,
        total_avoidable_standing_seconds=observer.delay_seconds,
        trip_completion_times=observer.completions,source_version=result.get('queue_following_protocol','V1_SPEED_CAP_FOLLOWERS'))
    (out/'runtime_result.json').write_text(json.dumps(result,indent=2,default=str))
    (out/'receipt.json').write_text(json.dumps(receipt,indent=2,default=str))
    print(json.dumps({k:v for k,v in receipt.items() if k not in {'metrics','promotions','entries','genuine_actor_factors','trip_completion_times'}}))


if __name__=='__main__':main()
