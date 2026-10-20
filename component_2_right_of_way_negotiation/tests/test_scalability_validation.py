"""Meaningful fixed-design, capacity-attribution, integrity and resume contracts."""
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import pytest for use in this module.
import pytest
# Import MapPathManager from conflict for the operations below.
from conflict import MapPathManager
# Import select_queue_heads from runtime_simulation.queue_heads for the operations below.
from runtime_simulation.queue_heads import select_queue_heads
# Import validate_presentation_schedule from runtime_simulation.schedule for the operations below.
from runtime_simulation.schedule import validate_presentation_schedule
# Import POLICY, EXPECTED_POLICY_HASH, file_hash, digest, write_json from post_training_evaluation.models for the
# operations below.
from post_training_evaluation.models import POLICY, EXPECTED_POLICY_HASH, file_hash, digest, write_json
# Import schedule_payload from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import schedule_payload
# Import cases, models, metrics, runner, reporting from scalability_validation for the operations below.
from scalability_validation import cases, models, metrics, runner, reporting

# Good integrity using the inputs and processing steps below.
# Output: a dictionary built from the supplied values.
def good_integrity():
    # Return a dictionary built from the supplied values to the caller.
    return dict(valid=True,policy_hash_unchanged=True,decentralized_execution=True,
        # Supply centralized_execution_graph_used_for_control as False.
        # Supply training_operations as 0.
        centralized_execution_graph_used_for_control=False,training_operations=0,
        # Supply backward_calls as 0.
        # Supply optimizer_steps as 0.
        # Supply parameter_updates as 0.
        # Supply centralized_critic_runtime_calls as 0.
        # Supply global_execution_calls as 0.
        backward_calls=0,optimizer_steps=0,parameter_updates=0,centralized_critic_runtime_calls=0,global_execution_calls=0)

# Base metrics using the inputs and processing steps below.
# Output: a dictionary built from the supplied values.
def base_metrics():
    # Return a dictionary built from the supplied values to the caller.
    return dict(total_vehicles_scheduled=4,total_vehicles_completed=4,maximum_negotiation_participants=4,
        # Supply collision_count as 0.
        # Supply blocked_zone_violation_count as 0.
        # Supply timeout as False.
        collision_count=0,blocked_zone_violation_count=0,timeout=False)

# Check exact seven balanced legal prefix cases and common seed using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_exact_seven_balanced_legal_prefix_cases_and_common_seed():
    # Require cases.LOADS equals a tuple containing 4, 8, 12, 16, 24, 32, 40; otherwise raise AssertionError.
    assert cases.LOADS == (4,8,12,16,24,32,40)
    # Require a list of c.case_id for c in cases.CASES equals a list containing the text 'SV-04', the text
    # 'SV-08', the text 'SV-12', the text 'SV-16', the text 'SV-24', the text...; otherwise raise AssertionError.
    assert [c.case_id for c in cases.CASES] == ['SV-04','SV-08','SV-12','SV-16','SV-24','SV-32','SV-40']
    # Set paths to the result of MapPathManager().
    paths = MapPathManager()
    # Set seeds to an empty set.
    seeds = set()
    # Iterate over cases.CASES, binding each item to case.
    for case in cases.CASES:
        # Set schedule to the result of case.schedule().
        schedule = case.schedule()
        # Require the result of validate_presentation_schedule(schedule) equals schedule; otherwise raise
        # AssertionError.
        assert validate_presentation_schedule(schedule,allow_repeated_movements=True) == schedule
        # Require whether every item is true in a lazy sequence of the number of entries in rows equals case.count
        # integer-divided by 4 for rows in values from schedule; otherwise raise AssertionError.
        assert all(len(rows) == case.count//4 for rows in schedule.values())
        # Set flattened to the sorted values from a lazy sequence of r for rows in values from schedule.
        flattened = sorted((r for rows in schedule.values() for r in rows),key=lambda r:(r.sequence_index,'NESW'.index(r.approach)))
        # Require a tuple built from flattened equals cases.template() sliced by :case.count; otherwise raise
        # AssertionError.
        assert tuple(flattened) == cases.template()[:case.count]
        # Require a set of r.movement_path_id.rsplit('_', 1) at -1 for r in flattened equals a set containing the
        # text 'LEFT', the text 'STRAIGHT', the text 'RIGHT'; otherwise raise AssertionError.
        assert {r.movement_path_id.rsplit('_',1)[-1] for r in flattened} == {'LEFT','STRAIGHT','RIGHT'}
        # Iterate over flattened, binding each item to row.
        for row in flattened:
            # Require row.movement_path_id belongs to paths.paths; otherwise raise AssertionError.
            assert row.movement_path_id in paths.paths
            # Require row.scheduled_departure_seconds equals row.sequence_index multiplied by 1.5; otherwise raise
            # AssertionError.
            assert row.scheduled_departure_seconds == row.sequence_index*1.5
        # Set scenario to the result of case.scenario().
        scenario = case.scenario()
        # Add an integer built from digest((models.PROTOCOL, scenario.scenario_id, None, 'PROPOSED_MAPPO')) sliced
        # by :16 modulo 2 raised to the power 31 to seeds.
        seeds.add(int(digest((models.PROTOCOL,scenario.scenario_id,None,'PROPOSED_MAPPO'))[:16],16)%(2**31))
        # Require scenario.budget_seconds equals 180; otherwise raise AssertionError.
        assert scenario.budget_seconds == 180
    # Require the number of entries in seeds equals 1; otherwise raise AssertionError.
    assert len(seeds) == 1
    # Require the sum of a lazy sequence of c.scenario().budget_seconds for c in cases.CASES equals 1260;
    # otherwise raise AssertionError.
    assert sum(c.scenario().budget_seconds for c in cases.CASES) == 1260

# Check forty vehicles only four physical heads using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_forty_vehicles_only_four_physical_heads():
    # Set paths to the result of MapPathManager().
    paths=MapPathManager()
    # Set (movements, states) to a tuple containing an empty dictionary, an empty dictionary.
    movements,states={},{}
    # Iterate over key/value pairs from cases.CASES[-1].schedule(), binding each item to (a, rows).
    for a,rows in cases.CASES[-1].schedule().items():
        # Iterate over rows, binding each item to row.
        for row in rows:
            # Set v to formatted text built from the embedded values.
            v=f'PANEL_AV_{a}_{row.sequence_index+1:02d}'
            # Set movements[v] to row.movement_path_id.
            movements[v]=row.movement_path_id
            # Set states[v] to a dictionary built from the supplied values.
            states[v]=dict(lane_id=paths.paths[row.movement_path_id].incoming_lane_id,lane_position=280-row.sequence_index*7.5)
    # Require the number of entries in states equals 40; otherwise raise AssertionError.
    assert len(states)==40
    # Require a set built from the result of select_queue_heads(states, paths, movements) equals a set of
    # formatted text built from the embedded values for a in the text 'NESW'; otherwise raise AssertionError.
    assert set(select_queue_heads(states,paths,movements))=={f'PANEL_AV_{a}_01' for a in 'NESW'}
    # Remove the requested entry from states.
    states.pop('PANEL_AV_N_01')
    # Require the text 'PANEL_AV_N_02' belongs to the result of select_queue_heads(states, paths, movements);
    # otherwise raise AssertionError.
    assert 'PANEL_AV_N_02' in select_queue_heads(states,paths,movements)

# Check geometry and exact policy using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_geometry_and_exact_policy():
    # Set geometry to the result of models.geometry().
    geometry=models.geometry()
    # Require geometry at 'incoming_lane_lengths_metres' equals the result of dict.fromkeys(the text 'NESW',
    # 292.8); otherwise raise AssertionError.
    assert geometry['incoming_lane_lengths_metres']==dict.fromkeys('NESW',292.8)
    # Require geometry at 'static_storage_vehicles_per_approach' equals the result of dict.fromkeys(the text
    # 'NESW', 39); otherwise raise AssertionError.
    assert geometry['static_storage_vehicles_per_approach']==dict.fromkeys('NESW',39)
    # Require geometry at 'vehicle_length_metres' equals 5 and geometry at 'minimum_gap_metres' equals 2.5;
    # otherwise raise AssertionError.
    assert geometry['vehicle_length_metres']==5 and geometry['minimum_gap_metres']==2.5
    # Require the result of file_hash(POLICY) equals EXPECTED_POLICY_HASH; otherwise raise AssertionError.
    assert file_hash(POLICY)==EXPECTED_POLICY_HASH

# Check manifest rejects tamper and source drift using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_manifest_rejects_tamper_and_source_drift(tmp_path,monkeypatch):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen=models.prepare(tmp_path)
    # Require the result of models.prepare(tmp_path) equals frozen; otherwise raise AssertionError.
    assert models.prepare(tmp_path)==frozen
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(models,'sources',lambda:{'modified.py':'different'})
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='MANIFEST_CHANGED'):
        # Call models.prepare with the supplied arguments.
        models.prepare(tmp_path)
    # Set frozen['manifest']['cases'][0]['count'] to 8.
    frozen['manifest']['cases'][0]['count']=8
    # Call write_json with the supplied arguments.
    write_json(tmp_path/'manifest.json',frozen)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='CHECKSUM'):
        # Call models.read_manifest with the supplied arguments.
        models.read_manifest(tmp_path)

# Apply pytest.mark.parametrize('root', ['results/targeted_validation/v1',... as a decorator to configure the
# following definition.
@pytest.mark.parametrize('root',['results/targeted_validation/v1','results/targeted_validation/v2','results/targeted_validation/latest','results/post_training_evaluation/runs','results/repair_diagnostics/new'])
# Check protected evidence roots using the setup, calls, and assertions below.
# Input root: the base directory used to resolve files.
# Output: no explicit value; normal completion returns None.
def test_protected_evidence_roots(root):
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        # Call models.protect with the supplied arguments.
        models.protect(root)

# Apply pytest.mark.parametrize('counter', ['training_operations', 'backward_calls', 'optimizer_steps',... as a
# decorator to configure the following definition.
@pytest.mark.parametrize('counter',['training_operations','backward_calls','optimizer_steps','parameter_updates','centralized_critic_runtime_calls','global_execution_calls'])
# Check any architecture counter invalidates experiment using the setup, calls, and assertions below.
# Input counter: the supplied counter.
# Output: no explicit value; normal completion returns None.
def test_any_architecture_counter_invalidates_experiment(counter):
    # Set integrity to the result of good_integrity().
    integrity=good_integrity()
    # Set integrity[counter] to 1.
    integrity[counter]=1
    # Require the result of models.classify(the result of base_metrics(), integrity) equals the text
    # 'INVALID_EXPERIMENT'; otherwise raise AssertionError.
    assert models.classify(base_metrics(),integrity)=='INVALID_EXPERIMENT'

# Apply pytest.mark.parametrize('change', ['global', 'critic', 'participants', 'policy', 'ego_local']) as a
# decorator to configure the following definition.
@pytest.mark.parametrize('change',['global','critic','participants','policy','ego_local'])
# Check integrity boundaries using the setup, calls, and assertions below.
# Input change: the supplied change.
# Output: no explicit value; normal completion returns None.
# Processing: select branches using the stated conditions.
def test_integrity_boundaries(change):
    # Set integrity to the result of good_integrity().
    # Set m to the result of base_metrics().
    integrity=good_integrity(); m=base_metrics()
    # Run this branch when change equals the text 'global'.
    # Set integrity['centralized_execution_graph_used_for_control'] to True.
    if change=='global': integrity['centralized_execution_graph_used_for_control']=True
    # Run this branch when change equals the text 'critic'.
    # Set integrity['centralized_critic_runtime_calls'] to 1.
    if change=='critic': integrity['centralized_critic_runtime_calls']=1
    # Run this branch when change equals the text 'participants'.
    # Set m['maximum_negotiation_participants'] to 5.
    if change=='participants': m['maximum_negotiation_participants']=5
    # Run this branch when change equals the text 'policy'.
    # Set integrity['policy_hash_unchanged'] to False.
    if change=='policy': integrity['policy_hash_unchanged']=False
    # Run this branch when change equals the text 'ego_local'.
    # Set integrity['decentralized_execution'] to False.
    if change=='ego_local': integrity['decentralized_execution']=False
    # Require the result of models.classify(m, integrity) equals the text 'INVALID_EXPERIMENT'; otherwise raise
    # AssertionError.
    assert models.classify(m,integrity)=='INVALID_EXPERIMENT'

# Check all safety liveness and capacity verdicts using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_all_safety_liveness_and_capacity_verdicts():
    # Set m to the result of base_metrics().
    # Set integrity to the result of good_integrity().
    m=base_metrics(); integrity=good_integrity()
    # Require the result of models.classify(m, integrity) equals the text 'PASS'; otherwise raise AssertionError.
    assert models.classify(m,integrity)=='PASS'
    # Update m with the supplied entries.
    m.update(total_vehicles_completed=1,timeout=True)
    # Require the result of models.classify(m, integrity) equals the text 'SAFE_DEGRADATION'; otherwise raise
    # AssertionError.
    assert models.classify(m,integrity)=='SAFE_DEGRADATION'
    # Set m['primary_network_capacity_limit_demonstrated'] to True.
    m['primary_network_capacity_limit_demonstrated']=True
    # Require the result of models.classify(m, integrity) equals the text 'NETWORK_CAPACITY_LIMIT'; otherwise
    # raise AssertionError.
    assert models.classify(m,integrity)=='NETWORK_CAPACITY_LIMIT'
    # Set m['collision_count'] to 1.
    m['collision_count']=1
    # Require the result of models.classify(m, integrity) equals the text 'UNSAFE_FAILURE'; otherwise raise
    # AssertionError.
    assert models.classify(m,integrity)=='UNSAFE_FAILURE'
    # Update m with the supplied entries.
    m.update(collision_count=0,blocked_zone_violation_count=1)
    # Require the result of models.classify(m, integrity, the text 'invariant exception') equals the text
    # 'UNSAFE_FAILURE'; otherwise raise AssertionError.
    assert models.classify(m,integrity,'invariant exception')=='UNSAFE_FAILURE'
    # Set m['blocked_zone_violation_count'] to 0.
    m['blocked_zone_violation_count']=0
    # Require the result of models.classify(m, integrity, the text 'unrelated exception') equals the text
    # 'INVALID_EXPERIMENT'; otherwise raise AssertionError.
    assert models.classify(m,integrity,'unrelated exception')=='INVALID_EXPERIMENT'

# Measurements using the inputs and processing steps below.
# Output: a dictionary containing PANEL_AV_N_01, PANEL_AV_N_02, PANEL_AV_N_03.
def measurements():
    # Return a dictionary containing PANEL_AV_N_01, PANEL_AV_N_02, PANEL_AV_N_03 to the caller.
    return {'PANEL_AV_N_01':dict(movement_path_id='N_IN_0_LEFT',scheduled_departure_seconds=0.,actual_departure_seconds=.04,completion_seconds=10.),
            # Store a dictionary built from the supplied values under 'PANEL_AV_N_02'.
            'PANEL_AV_N_02':dict(movement_path_id='N_IN_0_RIGHT',scheduled_departure_seconds=1.5,actual_departure_seconds=2.,completion_seconds=None),
            # Store a dictionary built from the supplied values under 'PANEL_AV_N_03'.
            'PANEL_AV_N_03':dict(movement_path_id='N_IN_0_STRAIGHT',scheduled_departure_seconds=3.,actual_departure_seconds=None,completion_seconds=None)}

# Check actual spawn delay pending not a negotiation failure using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_actual_spawn_delay_pending_not_a_negotiation_failure():
    # Set m to the result of metrics.insertion_metrics(the result of measurements(), 30.0, a dictionary containing
    # N, an empty set, a dictionary...).
    m=metrics.insertion_metrics(measurements(),30.,{'N':39},set(),{'N':None})
    # Require m at 'successfully_spawned_vehicle_count' equals 2 and m at 'never_spawned_before_budget' equals 1;
    # otherwise raise AssertionError.
    assert m['successfully_spawned_vehicle_count']==2 and m['never_spawned_before_budget']==1
    # Require m at 'insertion_delayed_vehicle_count' equals 1; otherwise raise AssertionError.
    assert m['insertion_delayed_vehicle_count']==1
    # Require m at 'actual_spawn_delay_seconds' equals a dictionary containing PANEL_AV_N_01, PANEL_AV_N_02;
    # otherwise raise AssertionError.
    assert m['actual_spawn_delay_seconds']=={'PANEL_AV_N_01':.04,'PANEL_AV_N_02':.5}
    # Require m at 'mean_insertion_delay_seconds' equals the result of pytest.approx(0.27); otherwise raise
    # AssertionError.
    assert m['mean_insertion_delay_seconds']==pytest.approx(.27)
    # Require m at 'completion_rate_among_scheduled' equals 1 divided by 3 and m at
    # 'completion_rate_among_spawned' equals 0.5; otherwise raise AssertionError.
    assert m['completion_rate_among_scheduled']==1/3 and m['completion_rate_among_spawned']==.5
    # Require m at 'unfinished_spawned_vehicles' equals 1 and m at 'spawned_vehicle_travel_exposure_seconds'
    # equals the result of pytest.approx(37.96); otherwise raise AssertionError.
    assert m['unfinished_spawned_vehicles']==1 and m['spawned_vehicle_travel_exposure_seconds']==pytest.approx(37.96)
    # Require the negation of m at 'primary_network_capacity_limit_demonstrated'; otherwise raise AssertionError.
    assert not m['primary_network_capacity_limit_demonstrated']
    # Require m at 'insertion_limitation_cause' equals the text 'INSERTION_CAUSE_NOT_ESTABLISHED'; otherwise raise
    # AssertionError.
    assert m['insertion_limitation_cause']=='INSERTION_CAUSE_NOT_ESTABLISHED'

# Check capacity requires persistent storage and no controller backpressure using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
def test_capacity_requires_persistent_storage_and_no_controller_backpressure():
    # Set rows to the result of measurements().
    rows=measurements()
    # Set confirmed to the result of metrics.insertion_metrics(rows, 30.0, a dictionary containing N, an empty
    # set, a dictionary containing N).
    confirmed=metrics.insertion_metrics(rows,30.,{'N':39},set(),{'N':10.})
    # Require confirmed at 'primary_network_capacity_limit_demonstrated'; otherwise raise AssertionError.
    assert confirmed['primary_network_capacity_limit_demonstrated']
    # Set blocked to the result of metrics.insertion_metrics(rows, 30.0, a dictionary containing N, a set
    # containing the text 'N', a dictionary containing N).
    blocked=metrics.insertion_metrics(rows,30.,{'N':39},{'N'},{'N':10.})
    # Require the negation of blocked at 'primary_network_capacity_limit_demonstrated'; otherwise raise
    # AssertionError.
    assert not blocked['primary_network_capacity_limit_demonstrated']
    # Require blocked at 'insertion_limitation_cause' equals the text 'CONTROLLER_BACKPRESSURE_OBSERVED';
    # otherwise raise AssertionError.
    assert blocked['insertion_limitation_cause']=='CONTROLLER_BACKPRESSURE_OBSERVED'
    # Set brief to the result of metrics.insertion_metrics(rows, 30.0, a dictionary containing N, an empty set, a
    # dictionary containing N).
    brief=metrics.insertion_metrics(rows,30.,{'N':39},set(),{'N':20.})
    # Require the negation of brief at 'primary_network_capacity_limit_demonstrated'; otherwise raise
    # AssertionError.
    assert not brief['primary_network_capacity_limit_demonstrated']
    # Set rows['PANEL_AV_N_03']['scheduled_departure_seconds'] to 40.0.
    rows['PANEL_AV_N_03']['scheduled_departure_seconds']=40.
    # Require the negation of metrics.insertion_metrics(rows, 30.0, {'N': 39}, set(), {'N': 10.0}) at
    # 'primary_network_capacity_limit_demonstrated'; otherwise raise AssertionError.
    assert not metrics.insertion_metrics(rows,30.,{'N':39},set(),{'N':10.})['primary_network_capacity_limit_demonstrated']

# Fake record using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input frozen: the supplied frozen.
# Input case: the supplied case.
# Input suite: the supplied suite.
# Output: value.
def fake_record(root,frozen,case,suite='scalability'):
    # Set rid to case.case_id plus the text '_' plus suite.
    rid=case.case_id+'_'+suite
    # Set m to the result of base_metrics().
    # Update m with the supplied entries.
    m=base_metrics();m.update(total_vehicles_scheduled=case.count,total_vehicles_completed=case.count)
    # Set raw to a dictionary built from the supplied values.
    raw=dict(run_id=rid,suite=suite,scenario_id=case.scenario().scenario_id,manifest_hash=frozen['manifest_hash'],
        # Supply schedule_hash as the result of digest(the result of schedule_payload(the result of
        # case.schedule())).
        # Supply metrics as m.
        # Supply integrity as the result of good_integrity().
        # Supply error as None.
        schedule_hash=digest(schedule_payload(case.schedule())),metrics=m,integrity=good_integrity(),error=None,
        # Supply artifact_sha256 as an empty dictionary.
        # Supply classification as the text 'PASS'.
        # Supply policy_action_seed as an integer built from digest((models.PROTOCOL, case.scenario().scenario_id,
        # None, 'PROPOSED_MAPPO')) sliced by :16 modulo 2 raised to the power 31.
        artifact_sha256={},classification='PASS',policy_action_seed=int(digest((models.PROTOCOL,case.scenario().scenario_id,None,'PROPOSED_MAPPO'))[:16],16)%(2**31))
    # Set p to the result of Path(root) joined with the path segment 'runs' divided by rid.
    p=Path(root)/'runs'/rid
    # Call write_json with the supplied arguments.
    write_json(p/'result.json',raw);write_json(p/'result.sha256.json',dict(result_hash=digest(raw)))
    # Set provenance to a dictionary built from the supplied values.
    provenance=dict(schedule=schedule_payload(case.schedule()),manifest_hash=frozen['manifest_hash'])
    # Call write_json with the supplied arguments.
    write_json(p/'provenance.json',provenance);write_json(p/'provenance.sha256.json',dict(provenance_hash=digest(provenance)))
    # Set value to a dictionary containing raw_result_hash, scenario_id.
    value={**raw,'raw_result_hash':digest(raw),'scenario_id':case.case_id}
    # Call runner.persist with the supplied arguments.
    runner.persist(p,value)
    # Return value to the caller.
    return value

# Check resume reuses completed and never retries interrupted using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_resume_reuses_completed_and_never_retries_interrupted(tmp_path,monkeypatch):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen=models.prepare(tmp_path)
    # Call fake_record with the supplied arguments.
    fake_record(tmp_path,frozen,cases.CASES[0])
    # Call write_json with the supplied arguments.
    write_json(tmp_path/'attempts/SV-08.json',dict(case_id='SV-08',manifest_hash=frozen['manifest_hash']))
    # Set calls to an empty list.
    calls=[]
    # Execute using the inputs and processing steps below.
    # Input case: the supplied case.
    # Input frozen: the supplied frozen.
    # Input root: the base directory used to resolve files.
    # Output: the result of fake_record(root, frozen, case).
    def execute(case,frozen,root):
        # Append case.case_id to calls.
        calls.append(case.case_id)
        # Return the result of fake_record(root, frozen, case) to the caller.
        return fake_record(root,frozen,case)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner,'execute',execute)
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(reporting,'report',lambda root: {})
    # Call runner.run with the supplied arguments.
    runner.run(tmp_path)
    # Require calls equals a list containing the text 'SV-12', the text 'SV-16', the text 'SV-24', the text
    # 'SV-32', the text 'SV-40'; otherwise raise AssertionError.
    assert calls==['SV-12','SV-16','SV-24','SV-32','SV-40']
    # Set rows to the result of models.records(tmp_path).
    rows=models.records(tmp_path)
    # Require the number of entries in rows equals 7; otherwise raise AssertionError.
    assert len(rows)==7
    # Require next((r for r in rows if r['scenario_id'] == 'SV-08')) at 'classification' equals the text
    # 'INVALID_EXPERIMENT'; otherwise raise AssertionError.
    assert next(r for r in rows if r['scenario_id']=='SV-08')['classification']=='INVALID_EXPERIMENT'
    # Call runner.run with the supplied arguments.
    runner.run(tmp_path)
    # Require the number of entries in calls equals 5; otherwise raise AssertionError.
    assert len(calls)==5

# Check resume recovers raw completed without sumo using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_resume_recovers_raw_completed_without_sumo(tmp_path):
    # Set frozen to the result of models.prepare(tmp_path).
    # Set case to cases.CASES at 0.
    frozen=models.prepare(tmp_path);case=cases.CASES[0]
    # Set value to the result of fake_record(tmp_path, frozen, case).
    value=fake_record(tmp_path,frozen,case)
    # Set directory to tmp_path joined with the path segment 'runs' divided by value at 'run_id'.
    directory=tmp_path/'runs'/value['run_id']
    # Call (directory / 'study_result.json').unlink with the supplied arguments.
    # Call (directory / 'study_result.sha256.json').unlink with the supplied arguments.
    (directory/'study_result.json').unlink();(directory/'study_result.sha256.json').unlink()
    # Call write_json with the supplied arguments.
    write_json(tmp_path/'attempts/SV-04.json',dict(case_id='SV-04',manifest_hash=frozen['manifest_hash']))
    # Set recovered to the result of runner.recover_interruption(case, tmp_path, frozen).
    recovered=runner.recover_interruption(case,tmp_path,frozen)
    # Require recovered at 'classification' equals the text 'PASS' and the number of entries in the result of
    # models.records(tmp_path) equals 1; otherwise raise AssertionError.
    assert recovered['classification']=='PASS' and len(models.records(tmp_path))==1

# Check report excludes preflight and uses actual evidence using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_report_excludes_preflight_and_uses_actual_evidence(tmp_path):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen=models.prepare(tmp_path)
    # Call fake_record with the supplied arguments.
    fake_record(tmp_path,frozen,cases.CASES[0],'preflight')
    # Require reporting.build_payload(tmp_path) at 'scientific_episodes_recorded' equals 0; otherwise raise
    # AssertionError.
    assert reporting.build_payload(tmp_path)['scientific_episodes_recorded']==0
    # Call fake_record with the supplied arguments.
    fake_record(tmp_path,frozen,cases.CASES[1])
    # Set payload to the result of reporting.report(tmp_path).
    payload=reporting.report(tmp_path)
    # Require payload at 'scientific_episodes_recorded' equals 1; otherwise raise AssertionError.
    assert payload['scientific_episodes_recorded']==1
    # Require payload['rows'][0] at 'classification' equals the text 'NOT_RUN'; otherwise raise AssertionError.
    assert payload['rows'][0]['classification']=='NOT_RUN'
    # Require payload['rows'][1]['metrics'] at 'total_vehicles_completed' equals 8; otherwise raise
    # AssertionError.
    assert payload['rows'][1]['metrics']['total_vehicles_completed']==8
    # Require the number of entries in a list built from the result of (tmp_path / 'latest/plots').glob('*.png')
    # equals 7; otherwise raise AssertionError.
    assert len(list((tmp_path/'latest/plots').glob('*.png')))==7
    # Set page to the text read from (tmp_path / 'latest/SCALABILITY_REPORT.html').
    page=(tmp_path/'latest/SCALABILITY_REPORT.html').read_text()
    # Require the text 'Operational Boundary Observation' belongs to page and the text 'N/A' belongs to page;
    # otherwise raise AssertionError.
    assert 'Operational Boundary Observation' in page and 'N/A' in page
    # Require the negation of whether any item is true in a lazy sequence of 'through 8' belongs to line for line
    # in payload at 'interpretation'; otherwise raise AssertionError.
    assert not any('through 8' in line for line in payload['interpretation'])

# Check record tampering rejected using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_record_tampering_rejected(tmp_path):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen=models.prepare(tmp_path)
    # Set value to the result of fake_record(tmp_path, frozen, cases.CASES at 0).
    value=fake_record(tmp_path,frozen,cases.CASES[0])
    # Set path to tmp_path joined with the path segment 'runs' divided by value at 'run_id' joined with the path segment
    # 'study_result.json'.
    path=tmp_path/'runs'/value['run_id']/'study_result.json'
    # Set value['metrics']['total_vehicles_completed'] to 0.
    value['metrics']['total_vehicles_completed']=0
    # Call write_json with the supplied arguments.
    write_json(path,value)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='CHECKSUM'):
        # Call models.records with the supplied arguments.
        models.records(tmp_path)

# Check reuses same runtime and deadlock definition using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_reuses_same_runtime_and_deadlock_definition():
    # Import run_episode from post_training_evaluation.runner for the operations below.
    from post_training_evaluation.runner import run_episode
    # Import PanelTelemetry from targeted_validation.metrics for the operations below.
    from targeted_validation.metrics import PanelTelemetry
    # Require runner.run_episode is the same object as run_episode; otherwise raise AssertionError.
    assert runner.run_episode is run_episode
    # Require the result of metrics.ScalabilityTelemetry.observe.__qualname__.startswith(the text
    # 'ScalabilityTelemetry'); otherwise raise AssertionError.
    assert metrics.ScalabilityTelemetry.observe.__qualname__.startswith('ScalabilityTelemetry')
    # Require the result of issubclass(metrics.ScalabilityTelemetry, PanelTelemetry); otherwise raise
    # AssertionError.
    assert issubclass(metrics.ScalabilityTelemetry,PanelTelemetry)
    # Require metrics.DEADLOCK_DURATION_SECONDS equals 15.0; otherwise raise AssertionError.
    assert metrics.DEADLOCK_DURATION_SECONDS==15.

# Check existing evidence and control sources unchanged using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_existing_evidence_and_control_sources_unchanged():
    # Iterate over a list containing the text 'prior_evidence_inventory.json', the text
    # 'prior_source_inventory.json', binding each item to filename.
    for filename in ['prior_evidence_inventory.json','prior_source_inventory.json']:
        # Set inventory to the decoded data produced by json.loads from the text read from
        # (Path('results/scalability_validation/audit') / filename).
        inventory=json.loads((Path('results/scalability_validation/audit')/filename).read_text(encoding='utf-8-sig'))
        # Require inventory; otherwise raise AssertionError.
        assert inventory
        # Import assert_historical_unchanged from naming_compat for the operations below.
        from naming_compat import assert_historical_unchanged
        # Require the result of assert_historical_unchanged(inventory); otherwise raise AssertionError.
        assert assert_historical_unchanged(inventory)
