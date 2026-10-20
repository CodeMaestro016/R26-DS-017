"""Standalone process and TraCI connection; never calls protected execution."""
# Import argparse for use in this module.
import argparse
# Import defaultdict from collections for the operations below.
from collections import defaultdict
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import re for use in this module.
import re
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import shutil for use in this module.
import shutil
# Import sys for use in this module.
import sys

# Set BASE to Path(__file__).resolve().parents at 1.
# Call sys.path.insert with the supplied arguments.
BASE=Path(__file__).resolve().parents[1];sys.path.insert(0,str(BASE))
# Import traci for use in this module.
import traci
# Import SUMO_CONFIG, SUMO_NETWORK_FILE from config for the operations below.
from config import SUMO_CONFIG,SUMO_NETWORK_FILE
# Import get_scenario from runtime_simulation.scenarios for the operations below.
from runtime_simulation.scenarios import get_scenario
# Import ADMISSION_ORDER from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import ADMISSION_ORDER


# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(path.read_bytes()).
# Return the hexadecimal digest from hashlib.sha256(path.read_bytes()) to the caller.
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions, then handle the
# specified errors.
def main():
    # Set parser to the result of argparse.ArgumentParser().
    # Call parser.add_argument with the supplied arguments.
    parser=argparse.ArgumentParser();parser.add_argument('--confirm-offline-unsafe',action='store_true')
    # Call parser.add_argument with the supplied arguments.
    parser.add_argument('--evidence-version',default='v1',help='New evidence folder; existing runs are never overwritten')
    # Set args to the result of parser.parse_args().
    args=parser.parse_args()
    # Run this branch when the negation of args.confirm_offline_unsafe.
    # Call parser.error with the supplied arguments.
    if not args.confirm_offline_unsafe:parser.error('This is an isolated unsafe educational simulation; explicit confirmation is required.')
    # Set protocol_path to the result of Path(__file__).with_name(the text 'protocol.json').
    protocol_path=Path(__file__).with_name('protocol.json')
    # Set protocol to the decoded data produced by json.loads from the text read from protocol_path.
    protocol=json.loads(protocol_path.read_text())
    # Run this branch when the negation of the result of re.fullmatch(the text '[A-Za-z0-9][A-Za-z0-9_-]*',
    # args.evidence_version).
    # Call parser.error with the supplied arguments.
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*',args.evidence_version):parser.error('Evidence version must be a simple folder name')
    # Set out to BASE joined with the path segment 'results/offline_counterfactual' divided by args.evidence_version.
    # Create the directory requested by out.
    out=BASE/'results/offline_counterfactual'/args.evidence_version;out.mkdir(parents=True,exist_ok=False)
    # Set scenario to the result of get_scenario(protocol at 'scenario_id').
    # Set schedule to the result of scenario.schedule().
    scenario=get_scenario(protocol['scenario_id']);schedule=scenario.schedule()
    # Set manifest to a dictionary built from the supplied values.
    manifest=dict(protocol=protocol,protocol_sha256=sha(protocol_path),
        # Supply assets as a dictionary of a string built from the result of p.relative_to(BASE) mapped to the
        # result of sha(p) for p in a list containing SUMO_CONFIG, SUMO_NETWORK_FILE, BASE joined with the path segment
        # 'networks/intersection.rou.xml', BASE divided by...
        assets={str(p.relative_to(BASE)):sha(p) for p in [SUMO_CONFIG,SUMO_NETWORK_FILE,BASE/'networks/intersection.rou.xml',BASE/'runtime_simulation/final_demonstrations.json']},
        # Supply schedule as a dictionary of k mapped to a list of the result of vars(d) for d in rows for (k,
        # rows) in key/value pairs from schedule.
        schedule={k:[vars(d) for d in rows] for k,rows in schedule.items()})
    # Write the supplied text to (out / 'manifest.json').
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    # Set command to a list containing the result of shutil.which(the text 'sumo') or the text 'sumo', the text
    # '-c', a string built from...
    command=[shutil.which('sumo') or 'sumo','-c',str(SUMO_CONFIG),'--seed',str(protocol['seed']),
        '--step-length','.04','--time-to-teleport','-1','--collision.action','warn',
        '--collision.check-junctions','true','--collision.mingap-factor','0',
        # Include a string built from out joined with the path segment 'sumo_collisions.xml' in this list.
        '--collision-output',str(out/'sumo_collisions.xml'),'--no-step-log','true',
        # Include a string built from out joined with the path segment 'sumo.log' in this list.
        '--log',str(out/'sumo.log'),'--duration-log.disable','true']
    # Set label to the text 'isolated-offline-counterfactual'.
    # Set connection to None.
    # Set frames to an empty list.
    # Set events to an empty list.
    label='isolated-offline-counterfactual';connection=None;frames=[];events=[]
    # Set submitted to an empty set.
    # Set spawned to an empty dictionary.
    # Set completed to an empty dictionary.
    # Set waits to the result of defaultdict(float).
    # Set stationary_since to an empty dictionary.
    # Set deadlock to False.
    submitted=set();spawned={};completed={};waits=defaultdict(float);stationary_since={};deadlock=False
    # Set movements to a dictionary of formatted text built from the embedded values mapped to d.movement_path_id
    # for (a, rows) in key/value pairs from schedule.
    movements={f'PANEL_AV_{a}_{d.sequence_index+1:02d}':d.movement_path_id for a,rows in schedule.items() for d in rows}
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call traci.start with the supplied arguments.
        # Set connection to the result of traci.getConnection(label).
        traci.start(command,label=label);connection=traci.getConnection(label)
        # Set version to the result of connection.getVersion().
        # Set now to 0.0.
        # Set last_sample to the negative of 1.0.
        version=connection.getVersion();now=0.;last_sample=-1.
        # Repeat the following steps while now is less than protocol at 'budget_seconds'.
        while now<protocol['budget_seconds']:
            # Iterate over ADMISSION_ORDER, binding each item to approach.
            for approach in ADMISSION_ORDER:
                # Iterate over schedule at approach, binding each item to d.
                for d in schedule[approach]:
                    # Set ego to formatted text built from the embedded values.
                    ego=f'PANEL_AV_{approach}_{d.sequence_index+1:02d}'
                    # Run this branch when ego does not belong to submitted and d.scheduled_departure_seconds is
                    # at most now.
                    if ego not in submitted and d.scheduled_departure_seconds<=now:
                        # Set route to formatted text built from the embedded values.
                        route=f'route_{approach.lower()}_{d.movement_path_id.rsplit("_",1)[1].lower()}'
                        # Add ego to connection.vehicle.
                        connection.vehicle.add(ego,route,'AV',departSpeed='max',departLane='free',departPos='base')
                        # Set the SUMO speed-control mode using connection.vehicle.setSpeedMode.
                        # Add ego to submitted.
                        connection.vehicle.setSpeedMode(ego,protocol['speed_mode']);submitted.add(ego)
            # Call connection.simulationStep with the supplied arguments.
            # Set now to the result of connection.simulation.getTime().
            connection.simulationStep();now=connection.simulation.getTime()
            # Iterate over the result of connection.simulation.getDepartedIDList(), binding each item to ego.
            # Set spawned[ego] to now.
            for ego in connection.simulation.getDepartedIDList():spawned[ego]=now
            # Iterate over the result of connection.simulation.getArrivedIDList(), binding each item to ego.
            # Set completed[ego] to now.
            for ego in connection.simulation.getArrivedIDList():completed[ego]=now
            # Set vehicles to an empty list.
            vehicles=[]
            # Iterate over the sorted values from the identifiers reported by connection.vehicle.getIDList,
            # binding each item to ego.
            for ego in sorted(connection.vehicle.getIDList()):
                # Set api to connection.vehicle.
                # Set (x, y) to the SUMO position of vehicle ego.
                # Set speed to the SUMO speed of vehicle ego.
                api=connection.vehicle;x,y=api.getPosition(ego);speed=api.getSpeed(ego)
                # Require the result of api.getSpeedMode(ego) equals 38; otherwise raise AssertionError.
                assert api.getSpeedMode(ego)==38
                # Request the specified SUMO speed using api.setSpeed.
                api.setSpeed(ego,min(api.getMaxSpeed(ego),api.getAllowedSpeed(ego)))
                # Run this branch when speed is less than 0.5.
                if speed<.5:
                    # Update waits[ego] to its current value plus 0.04.
                    # Call stationary_since.setdefault with the supplied arguments.
                    waits[ego]+=.04;stationary_since.setdefault(ego,now)
                    # Update deadlock to its current value combined with now minus stationary_since at ego is at
                    # least 15.
                    deadlock|=now-stationary_since[ego]>=15
                # Remove the requested entry from stationary_since.
                else:stationary_since.pop(ego,None)
                # Append a dictionary built from the supplied values to vehicles.
                vehicles.append(dict(id=ego,front_bumper_x=x,front_bumper_y=y,angle_degrees=api.getAngle(ego),
                    # Supply length_m as the result of api.getLength(ego).
                    # Supply width_m as the result of api.getWidth(ego).
                    # Supply speed_mps as speed.
                    length_m=api.getLength(ego),width_m=api.getWidth(ego),speed_mps=speed,
                    # Supply display_state as the text 'APPROACHING'.
                    # Supply movement as movements at ego.
                    # Supply lane_id as the result of api.getLaneID(ego).
                    display_state='APPROACHING',movement=movements[ego],lane_id=api.getLaneID(ego),
                    # Supply length_limit as the result of api.getLength(ego).
                    # Supply accel_limit as the result of api.getAccel(ego).
                    # Supply decel_limit as the result of api.getDecel(ego).
                    length_limit=api.getLength(ego),accel_limit=api.getAccel(ego),decel_limit=api.getDecel(ego)))
            # Set collisions to an empty list.
            collisions=[]
            # Iterate over the result of connection.simulation.getCollisions(), binding each item to c.
            for c in connection.simulation.getCollisions():
                # Set edge to the result of connection.lane.getEdgeID(c.lane).
                # Set index to an integer built from c.lane.rsplit('_', 1) at 1.
                edge=connection.lane.getEdgeID(c.lane);index=int(c.lane.rsplit('_',1)[1])
                # Set position to the result of connection.simulation.convert2D(edge, c.pos, index).
                position=connection.simulation.convert2D(edge,c.pos,index)
                # Append a dictionary built from the supplied values to collisions.
                collisions.append(dict(timestamp=now,collider=c.collider,victim=c.victim,
                    # Supply type as c.type.
                    # Supply lane as c.lane.
                    # Supply lane_position as c.pos.
                    # Supply position as a list built from position.
                    type=c.type,lane=c.lane,lane_position=c.pos,position=list(position),
                    # Supply position_source as the text 'SUMO collision lane/position converted by SUMO
                    # convert2D'.
                    position_source='SUMO collision lane/position converted by SUMO convert2D',
                    # Supply movements as a list containing movements at c.collider, movements at c.victim.
                    movements=[movements[c.collider],movements[c.victim]],
                    # Supply collider_speed as c.colliderSpeed.
                    # Supply victim_speed as c.victimSpeed.
                    collider_speed=c.colliderSpeed,victim_speed=c.victimSpeed))
            # Run this branch when now minus last_sample is at least 0.119 or collisions.
            if now-last_sample>=.119 or collisions:
                # Append a dictionary built from the supplied values to frames.
                # Set last_sample to now.
                frames.append(dict(simulation_time=now,vehicles=vehicles,collisions=collisions));last_sample=now
            # Run this branch when collisions.
            # Extend events with collisions.
            # Leave the nearest enclosing loop immediately.
            if collisions:events.extend(collisions);break
            # Run this branch when the number of entries in completed equals scenario.vehicle_count.
            # Leave the nearest enclosing loop immediately.
            if len(completed)==scenario.vehicle_count:break
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Run this branch when connection is a different object from None.
        # Call connection.close with the supplied arguments.
        if connection is not None:connection.close()
    # Set evidence to a dictionary built from the supplied values.
    evidence=dict(classification=protocol['classification'],version=protocol['version'],scenario_id=scenario.scenario_id,
        # Supply command as command.
        # Supply sumo_version as version.
        # Supply seed as 42.
        # Supply scheduled as scenario.vehicle_count.
        # Supply spawned as the number of entries in spawned.
        # Supply completed as the number of entries in completed.
        command=command,sumo_version=version,seed=42,scheduled=scenario.vehicle_count,spawned=len(spawned),completed=len(completed),
        # Supply departure_times as spawned.
        # Supply completion_times as completed.
        # Supply simulation_time as now.
        # Supply mappo_calls as 0.
        departure_times=spawned,completion_times=completed,simulation_time=now,mappo_calls=0,
        # Supply collision_count as the number of entries in events.
        # Supply collision_events as events.
        collision_count=len(events),collision_events=events,
        # Supply outcome as the text 'ACTUAL_SIMULATOR_COLLISION' when events, otherwise the text
        # 'COMPLETED_WITHOUT_DETECTED_COLLISION' when the number of entries in completed equals
        # scenario.vehicle_count, otherwise the text 'INCOMPLETE_NO_DETECTED_COLLISION'.
        outcome='ACTUAL_SIMULATOR_COLLISION' if events else 'COMPLETED_WITHOUT_DETECTED_COLLISION' if len(completed)==scenario.vehicle_count else 'INCOMPLETE_NO_DETECTED_COLLISION',
        # Supply deadlock_observed as deadlock.
        # Supply mean_waiting_seconds as the sum of values from waits divided by the number of entries in spawned
        # when spawned, otherwise None.
        deadlock_observed=deadlock,mean_waiting_seconds=sum(waits.values())/len(spawned) if spawned else None,
        # Supply throughput_vehicles_per_minute as the number of entries in completed multiplied by 60 divided by
        # now.
        # Supply waiting_by_vehicle as a dictionary built from waits.
        throughput_vehicles_per_minute=len(completed)*60/now,waiting_by_vehicle=dict(waits),
        # Supply detection as the text 'SUMO junction collision checks enabled;...'.
        detection='SUMO junction collision checks enabled; collision.mingap-factor=0 means body overlap rather than a minimum-gap warning',
        # Supply manifest_sha256 as the result of sha(out joined with the path segment 'manifest.json').
        # Supply frames as frames.
        manifest_sha256=sha(out/'manifest.json'),frames=frames)
    # Set trace to out joined with the path segment 'replay.json'.
    # Write the supplied text to trace.
    trace=out/'replay.json';trace.write_text(json.dumps(evidence,separators=(',',':')))
    # Write the supplied text to (out / 'receipt.json').
    (out/'receipt.json').write_text(json.dumps(dict(replay_sha256=sha(trace),**{k:v for k,v in evidence.items() if k!='frames'}),indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in evidence.items() if k not in {'frames','command'}}))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
