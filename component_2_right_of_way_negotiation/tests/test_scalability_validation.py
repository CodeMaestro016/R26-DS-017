"""Meaningful fixed-design, capacity-attribution, integrity and resume contracts."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from conflict import MapPathManager
from runtime_simulation.queue_heads import select_queue_heads
from runtime_simulation.schedule import validate_presentation_schedule
from post_training_evaluation.models import POLICY, EXPECTED_POLICY_HASH, file_hash, digest, write_json
from post_training_evaluation.scenarios import schedule_payload
from scalability_validation import cases, models, metrics, runner, reporting

def good_integrity():
    return dict(valid=True,policy_hash_unchanged=True,decentralized_execution=True,
        centralized_execution_graph_used_for_control=False,training_operations=0,
        backward_calls=0,optimizer_steps=0,parameter_updates=0,centralized_critic_runtime_calls=0,global_execution_calls=0)

def base_metrics():
    return dict(total_vehicles_scheduled=4,total_vehicles_completed=4,maximum_negotiation_participants=4,
        collision_count=0,blocked_zone_violation_count=0,timeout=False)

def test_exact_seven_balanced_legal_prefix_cases_and_common_seed():
    assert cases.LOADS == (4,8,12,16,24,32,40)
    assert [c.case_id for c in cases.CASES] == ['SV-04','SV-08','SV-12','SV-16','SV-24','SV-32','SV-40']
    paths = MapPathManager()
    seeds = set()
    for case in cases.CASES:
        schedule = case.schedule()
        assert validate_presentation_schedule(schedule,allow_repeated_movements=True) == schedule
        assert all(len(rows) == case.count//4 for rows in schedule.values())
        flattened = sorted((r for rows in schedule.values() for r in rows),key=lambda r:(r.sequence_index,'NESW'.index(r.approach)))
        assert tuple(flattened) == cases.template()[:case.count]
        assert {r.movement_path_id.rsplit('_',1)[-1] for r in flattened} == {'LEFT','STRAIGHT','RIGHT'}
        for row in flattened:
            assert row.movement_path_id in paths.paths
            assert row.scheduled_departure_seconds == row.sequence_index*1.5
        scenario = case.scenario()
        seeds.add(int(digest((models.PROTOCOL,scenario.scenario_id,None,'PROPOSED_MAPPO'))[:16],16)%(2**31))
        assert scenario.budget_seconds == 180
    assert len(seeds) == 1
    assert sum(c.scenario().budget_seconds for c in cases.CASES) == 1260

def test_forty_vehicles_only_four_physical_heads():
    paths=MapPathManager()
    movements,states={},{}
    for a,rows in cases.CASES[-1].schedule().items():
        for row in rows:
            v=f'PANEL_AV_{a}_{row.sequence_index+1:02d}'
            movements[v]=row.movement_path_id
            states[v]=dict(lane_id=paths.paths[row.movement_path_id].incoming_lane_id,lane_position=280-row.sequence_index*7.5)
    assert len(states)==40
    assert set(select_queue_heads(states,paths,movements))=={f'PANEL_AV_{a}_01' for a in 'NESW'}
    states.pop('PANEL_AV_N_01')
    assert 'PANEL_AV_N_02' in select_queue_heads(states,paths,movements)

def test_geometry_and_exact_policy():
    geometry=models.geometry()
    assert geometry['incoming_lane_lengths_metres']==dict.fromkeys('NESW',292.8)
    assert geometry['static_storage_vehicles_per_approach']==dict.fromkeys('NESW',39)
    assert geometry['vehicle_length_metres']==5 and geometry['minimum_gap_metres']==2.5
    assert file_hash(POLICY)==EXPECTED_POLICY_HASH

def test_manifest_rejects_tamper_and_source_drift(tmp_path,monkeypatch):
    frozen=models.prepare(tmp_path)
    assert models.prepare(tmp_path)==frozen
    monkeypatch.setattr(models,'sources',lambda:{'modified.py':'different'})
    with pytest.raises(RuntimeError,match='MANIFEST_CHANGED'):
        models.prepare(tmp_path)
    frozen['manifest']['cases'][0]['count']=8
    write_json(tmp_path/'manifest.json',frozen)
    with pytest.raises(RuntimeError,match='CHECKSUM'):
        models.read_manifest(tmp_path)

@pytest.mark.parametrize('root',['results/targeted_validation/v1','results/targeted_validation/v2','results/targeted_validation/latest','results/post_training_evaluation/runs','results/repair_diagnostics/new'])
def test_protected_evidence_roots(root):
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        models.protect(root)

@pytest.mark.parametrize('counter',['training_operations','backward_calls','optimizer_steps','parameter_updates','centralized_critic_runtime_calls','global_execution_calls'])
def test_any_architecture_counter_invalidates_experiment(counter):
    integrity=good_integrity()
    integrity[counter]=1
    assert models.classify(base_metrics(),integrity)=='INVALID_EXPERIMENT'

@pytest.mark.parametrize('change',['global','critic','participants','policy','ego_local'])
def test_integrity_boundaries(change):
    integrity=good_integrity(); m=base_metrics()
    if change=='global': integrity['centralized_execution_graph_used_for_control']=True
    if change=='critic': integrity['centralized_critic_runtime_calls']=1
    if change=='participants': m['maximum_negotiation_participants']=5
    if change=='policy': integrity['policy_hash_unchanged']=False
    if change=='ego_local': integrity['decentralized_execution']=False
    assert models.classify(m,integrity)=='INVALID_EXPERIMENT'

def test_all_safety_liveness_and_capacity_verdicts():
    m=base_metrics(); integrity=good_integrity()
    assert models.classify(m,integrity)=='PASS'
    m.update(total_vehicles_completed=1,timeout=True)
    assert models.classify(m,integrity)=='SAFE_DEGRADATION'
    m['primary_network_capacity_limit_demonstrated']=True
    assert models.classify(m,integrity)=='NETWORK_CAPACITY_LIMIT'
    m['collision_count']=1
    assert models.classify(m,integrity)=='UNSAFE_FAILURE'
    m.update(collision_count=0,blocked_zone_violation_count=1)
    assert models.classify(m,integrity,'invariant exception')=='UNSAFE_FAILURE'
    m['blocked_zone_violation_count']=0
    assert models.classify(m,integrity,'unrelated exception')=='INVALID_EXPERIMENT'

def measurements():
    return {'PANEL_AV_N_01':dict(movement_path_id='N_IN_0_LEFT',scheduled_departure_seconds=0.,actual_departure_seconds=.04,completion_seconds=10.),
            'PANEL_AV_N_02':dict(movement_path_id='N_IN_0_RIGHT',scheduled_departure_seconds=1.5,actual_departure_seconds=2.,completion_seconds=None),
            'PANEL_AV_N_03':dict(movement_path_id='N_IN_0_STRAIGHT',scheduled_departure_seconds=3.,actual_departure_seconds=None,completion_seconds=None)}

def test_actual_spawn_delay_pending_not_a_negotiation_failure():
    m=metrics.insertion_metrics(measurements(),30.,{'N':39},set(),{'N':None})
    assert m['successfully_spawned_vehicle_count']==2 and m['never_spawned_before_budget']==1
    assert m['insertion_delayed_vehicle_count']==1
    assert m['actual_spawn_delay_seconds']=={'PANEL_AV_N_01':.04,'PANEL_AV_N_02':.5}
    assert m['mean_insertion_delay_seconds']==pytest.approx(.27)
    assert m['completion_rate_among_scheduled']==1/3 and m['completion_rate_among_spawned']==.5
    assert m['unfinished_spawned_vehicles']==1 and m['spawned_vehicle_travel_exposure_seconds']==pytest.approx(37.96)
    assert not m['primary_network_capacity_limit_demonstrated']
    assert m['insertion_limitation_cause']=='INSERTION_CAUSE_NOT_ESTABLISHED'

def test_capacity_requires_persistent_storage_and_no_controller_backpressure():
    rows=measurements()
    confirmed=metrics.insertion_metrics(rows,30.,{'N':39},set(),{'N':10.})
    assert confirmed['primary_network_capacity_limit_demonstrated']
    blocked=metrics.insertion_metrics(rows,30.,{'N':39},{'N'},{'N':10.})
    assert not blocked['primary_network_capacity_limit_demonstrated']
    assert blocked['insertion_limitation_cause']=='CONTROLLER_BACKPRESSURE_OBSERVED'
    brief=metrics.insertion_metrics(rows,30.,{'N':39},set(),{'N':20.})
    assert not brief['primary_network_capacity_limit_demonstrated']
    rows['PANEL_AV_N_03']['scheduled_departure_seconds']=40.
    assert not metrics.insertion_metrics(rows,30.,{'N':39},set(),{'N':10.})['primary_network_capacity_limit_demonstrated']

def fake_record(root,frozen,case,suite='scalability'):
    rid=case.case_id+'_'+suite
    m=base_metrics();m.update(total_vehicles_scheduled=case.count,total_vehicles_completed=case.count)
    raw=dict(run_id=rid,suite=suite,scenario_id=case.scenario().scenario_id,manifest_hash=frozen['manifest_hash'],
        schedule_hash=digest(schedule_payload(case.schedule())),metrics=m,integrity=good_integrity(),error=None,
        artifact_sha256={},classification='PASS',policy_action_seed=int(digest((models.PROTOCOL,case.scenario().scenario_id,None,'PROPOSED_MAPPO'))[:16],16)%(2**31))
    p=Path(root)/'runs'/rid
    write_json(p/'result.json',raw);write_json(p/'result.sha256.json',dict(result_hash=digest(raw)))
    provenance=dict(schedule=schedule_payload(case.schedule()),manifest_hash=frozen['manifest_hash'])
    write_json(p/'provenance.json',provenance);write_json(p/'provenance.sha256.json',dict(provenance_hash=digest(provenance)))
    value={**raw,'raw_result_hash':digest(raw),'scenario_id':case.case_id}
    runner.persist(p,value)
    return value

def test_resume_reuses_completed_and_never_retries_interrupted(tmp_path,monkeypatch):
    frozen=models.prepare(tmp_path)
    fake_record(tmp_path,frozen,cases.CASES[0])
    write_json(tmp_path/'attempts/SV-08.json',dict(case_id='SV-08',manifest_hash=frozen['manifest_hash']))
    calls=[]
    def execute(case,frozen,root):
        calls.append(case.case_id)
        return fake_record(root,frozen,case)
    monkeypatch.setattr(runner,'execute',execute)
    monkeypatch.setattr(reporting,'report',lambda root: {})
    runner.run(tmp_path)
    assert calls==['SV-12','SV-16','SV-24','SV-32','SV-40']
    rows=models.records(tmp_path)
    assert len(rows)==7
    assert next(r for r in rows if r['scenario_id']=='SV-08')['classification']=='INVALID_EXPERIMENT'
    runner.run(tmp_path)
    assert len(calls)==5

def test_resume_recovers_raw_completed_without_sumo(tmp_path):
    frozen=models.prepare(tmp_path);case=cases.CASES[0]
    value=fake_record(tmp_path,frozen,case)
    directory=tmp_path/'runs'/value['run_id']
    (directory/'study_result.json').unlink();(directory/'study_result.sha256.json').unlink()
    write_json(tmp_path/'attempts/SV-04.json',dict(case_id='SV-04',manifest_hash=frozen['manifest_hash']))
    recovered=runner.recover_interruption(case,tmp_path,frozen)
    assert recovered['classification']=='PASS' and len(models.records(tmp_path))==1

def test_report_excludes_preflight_and_uses_actual_evidence(tmp_path):
    frozen=models.prepare(tmp_path)
    fake_record(tmp_path,frozen,cases.CASES[0],'preflight')
    assert reporting.build_payload(tmp_path)['scientific_episodes_recorded']==0
    fake_record(tmp_path,frozen,cases.CASES[1])
    payload=reporting.report(tmp_path)
    assert payload['scientific_episodes_recorded']==1
    assert payload['rows'][0]['classification']=='NOT_RUN'
    assert payload['rows'][1]['metrics']['total_vehicles_completed']==8
    assert len(list((tmp_path/'latest/plots').glob('*.png')))==7
    page=(tmp_path/'latest/SCALABILITY_REPORT.html').read_text()
    assert 'Operational Boundary Observation' in page and 'N/A' in page
    assert not any('through 8' in line for line in payload['interpretation'])

def test_record_tampering_rejected(tmp_path):
    frozen=models.prepare(tmp_path)
    value=fake_record(tmp_path,frozen,cases.CASES[0])
    path=tmp_path/'runs'/value['run_id']/'study_result.json'
    value['metrics']['total_vehicles_completed']=0
    write_json(path,value)
    with pytest.raises(RuntimeError,match='CHECKSUM'):
        models.records(tmp_path)

def test_reuses_same_runtime_and_deadlock_definition():
    from post_training_evaluation.runner import run_episode
    from targeted_validation.metrics import PanelTelemetry
    assert runner.run_episode is run_episode
    assert metrics.ScalabilityTelemetry.observe.__qualname__.startswith('ScalabilityTelemetry')
    assert issubclass(metrics.ScalabilityTelemetry,PanelTelemetry)
    assert metrics.DEADLOCK_DURATION_SECONDS==15.

def test_existing_evidence_and_control_sources_unchanged():
    for filename in ['prior_evidence_inventory.json','prior_source_inventory.json']:
        inventory=json.loads((Path('results/scalability_validation/audit')/filename).read_text(encoding='utf-8-sig'))
        assert inventory
        from naming_compat import assert_historical_unchanged
        assert assert_historical_unchanged(inventory)
