"""Standalone process and TraCI connection; never calls protected execution."""
import argparse
from collections import defaultdict
import hashlib
import json
import re
from pathlib import Path
import shutil
import sys

BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
import traci
from config import SUMO_CONFIG,SUMO_NETWORK_FILE
from runtime_simulation.scenarios import get_scenario
from runtime_simulation.schedule import ADMISSION_ORDER


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--confirm-offline-unsafe',action='store_true')
    parser.add_argument('--evidence-version',default='v1',help='New evidence folder; existing runs are never overwritten')
    args=parser.parse_args()
    if not args.confirm_offline_unsafe:parser.error('This is an isolated unsafe educational simulation; explicit confirmation is required.')
    protocol_path=Path(__file__).with_name('protocol.json')
    protocol=json.loads(protocol_path.read_text())
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',args.evidence_version):parser.error('Evidence version must be a simple folder name')
    out=BASE/'results/offline_counterfactual'/args.evidence_version;out.mkdir(parents=True,exist_ok=False)
    scenario=get_scenario(protocol['scenario_id']);schedule=scenario.schedule()
    manifest=dict(protocol=protocol,protocol_sha256=sha(protocol_path),
        assets={str(p.relative_to(BASE)):sha(p) for p in [SUMO_CONFIG,SUMO_NETWORK_FILE,BASE/'networks/intersection.rou.xml',BASE/'runtime_simulation/final_demonstrations.json']},
        schedule={k:[vars(d) for d in rows] for k,rows in schedule.items()})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    command=[shutil.which('sumo') or 'sumo','-c',str(SUMO_CONFIG),'--seed',str(protocol['seed']),
        '--step-length','.04','--time-to-teleport','-1','--collision.action','warn',
        '--collision.check-junctions','true','--collision.mingap-factor','0',
        '--collision-output',str(out/'sumo_collisions.xml'),'--no-step-log','true',
        '--log',str(out/'sumo.log'),'--duration-log.disable','true']
    label='isolated-offline-counterfactual';connection=None;frames=[];events=[]
    submitted=set();spawned={};completed={};waits=defaultdict(float);stationary_since={};deadlock=False
    movements={f'PANEL_AV_{a}_{d.sequence_index+1:02d}':d.movement_path_id for a,rows in schedule.items() for d in rows}
    try:
        traci.start(command,label=label);connection=traci.getConnection(label)
        version=connection.getVersion();now=0.;last_sample=-1.
        while now<protocol['budget_seconds']:
            for approach in ADMISSION_ORDER:
                for d in schedule[approach]:
                    ego=f'PANEL_AV_{approach}_{d.sequence_index+1:02d}'
                    if ego not in submitted and d.scheduled_departure_seconds<=now:
                        route=f'route_{approach.lower()}_{d.movement_path_id.rsplit("_",1)[1].lower()}'
                        connection.vehicle.add(ego,route,'AV',departSpeed='max',departLane='free',departPos='base')
                        connection.vehicle.setSpeedMode(ego,protocol['speed_mode']);submitted.add(ego)
            connection.simulationStep();now=connection.simulation.getTime()
            for ego in connection.simulation.getDepartedIDList():spawned[ego]=now
            for ego in connection.simulation.getArrivedIDList():completed[ego]=now
            vehicles=[]
            for ego in sorted(connection.vehicle.getIDList()):
                api=connection.vehicle;x,y=api.getPosition(ego);speed=api.getSpeed(ego)
                assert api.getSpeedMode(ego)==38
                api.setSpeed(ego,min(api.getMaxSpeed(ego),api.getAllowedSpeed(ego)))
                if speed<.5:
                    waits[ego]+=.04;stationary_since.setdefault(ego,now)
                    deadlock|=now-stationary_since[ego]>=15
                else:stationary_since.pop(ego,None)
                vehicles.append(dict(id=ego,front_bumper_x=x,front_bumper_y=y,angle_degrees=api.getAngle(ego),
                    length_m=api.getLength(ego),width_m=api.getWidth(ego),speed_mps=speed,
                    display_state='APPROACHING',movement=movements[ego],lane_id=api.getLaneID(ego),
                    length_limit=api.getLength(ego),accel_limit=api.getAccel(ego),decel_limit=api.getDecel(ego)))
            collisions=[]
            for c in connection.simulation.getCollisions():
                edge=connection.lane.getEdgeID(c.lane);index=int(c.lane.rsplit('_',1)[1])
                position=connection.simulation.convert2D(edge,c.pos,index)
                collisions.append(dict(timestamp=now,collider=c.collider,victim=c.victim,
                    type=c.type,lane=c.lane,lane_position=c.pos,position=list(position),
                    position_source='SUMO collision lane/position converted by SUMO convert2D',
                    movements=[movements[c.collider],movements[c.victim]],
                    collider_speed=c.colliderSpeed,victim_speed=c.victimSpeed))
            if now-last_sample>=.119 or collisions:
                frames.append(dict(simulation_time=now,vehicles=vehicles,collisions=collisions));last_sample=now
            if collisions:events.extend(collisions);break
            if len(completed)==scenario.vehicle_count:break
    finally:
        if connection is not None:connection.close()
    evidence=dict(classification=protocol['classification'],version=protocol['version'],scenario_id=scenario.scenario_id,
        command=command,sumo_version=version,seed=42,scheduled=scenario.vehicle_count,spawned=len(spawned),completed=len(completed),
        departure_times=spawned,completion_times=completed,simulation_time=now,mappo_calls=0,
        collision_count=len(events),collision_events=events,
        outcome='ACTUAL_SIMULATOR_COLLISION' if events else 'COMPLETED_WITHOUT_DETECTED_COLLISION' if len(completed)==scenario.vehicle_count else 'INCOMPLETE_NO_DETECTED_COLLISION',
        deadlock_observed=deadlock,mean_waiting_seconds=sum(waits.values())/len(spawned) if spawned else None,
        throughput_vehicles_per_minute=len(completed)*60/now,waiting_by_vehicle=dict(waits),
        detection='SUMO junction collision checks enabled; collision.mingap-factor=0 means body overlap rather than a minimum-gap warning',
        manifest_sha256=sha(out/'manifest.json'),frames=frames)
    trace=out/'replay.json';trace.write_text(json.dumps(evidence,separators=(',',':')))
    (out/'receipt.json').write_text(json.dumps(dict(replay_sha256=sha(trace),**{k:v for k,v in evidence.items() if k!='frames'}),indent=2))
    print(json.dumps({k:v for k,v in evidence.items() if k not in {'frames','command'}}))


if __name__=='__main__':main()
