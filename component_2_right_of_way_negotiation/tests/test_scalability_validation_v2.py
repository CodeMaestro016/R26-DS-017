"""Staggered evaluation changes only; historical synchronized evidence survives."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest
from dataclasses import asdict
from conflict import MapPathManager
from post_training_evaluation.models import digest, file_hash, EXPECTED_POLICY_HASH, POLICY
from post_training_evaluation.scenarios import schedule_payload
from scalability_validation import cases as v1_cases
from scalability_validation.v2 import cases, models, metrics, runner, reporting

def test_exact_forty_staggered_entries_balanced_legal_prefixes():
    entries = cases.template()
    assert len(entries)==40
    assert [r.scheduled_departure_seconds for r in entries]==[round(i*.4,10) for i in range(40)]
    assert len({r.scheduled_departure_seconds for r in entries})==40
    assert [r.approach for r in entries]==list('NESW')*10
    assert cases.HEADWAY==1.6 and cases.INTERARRIVAL==.4
    legal=MapPathManager().paths
    for old,new in zip(v1_cases.template(),entries):
        assert (old.approach,old.movement_path_id,old.sequence_index)==(new.approach,new.movement_path_id,new.sequence_index)
        assert new.movement_path_id in legal
    seeds=set()
    assert [c.count for c in cases.CASES]==[4,8,12,16,24,32,40]
    for case in cases.CASES:
        schedule=case.schedule()
        assert all(len(rows)==case.count//4 for rows in schedule.values())
        flattened=sorted((r for rows in schedule.values() for r in rows),key=lambda r:r.scheduled_departure_seconds)
        assert tuple(flattened)==entries[:case.count]
        assert case.scenario().budget_seconds==180.
        seeds.add(int(digest((models.PROTOCOL,case.scenario().scenario_id,None,'PROPOSED_MAPPO'))[:16],16)%(2**31))
    assert len(seeds)==1
    assert sum(c.scenario().budget_seconds for c in cases.CASES)==1260.

def test_exact_first_twelve_predeclared_entries():
    expected=[('N','LEFT',0.),('E','STRAIGHT',.4),('S','RIGHT',.8),('W','STRAIGHT',1.2),
        ('N','STRAIGHT',1.6),('E','RIGHT',2.),('S','LEFT',2.4),('W','RIGHT',2.8),
        ('N','RIGHT',3.2),('E','LEFT',3.6),('S','STRAIGHT',4.),('W','LEFT',4.4)]
    assert [(r.approach,r.movement_path_id.rsplit('_',1)[1],r.scheduled_departure_seconds) for r in cases.template()[:12]]==expected

def test_v1_stays_synchronized_and_is_a_separate_family():
    assert [r.scheduled_departure_seconds for r in v1_cases.template()[:4]]==[0.,0.,0.,0.]
    assert models.PROTOCOL=='SCALABILITY_VALIDATION_V2'
    assert models.ROOT==Path('results/scalability_validation/v2')
    assert file_hash(POLICY)==EXPECTED_POLICY_HASH

@pytest.mark.parametrize('root',['results/scalability_validation/v1','results/scalability_validation/v1/new','results/scalability_validation_archives/v1','results/targeted_validation/v2'])
def test_old_evidence_roots_are_read_only(root):
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        models.prepare(root)
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        reporting.report(root)
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        runner.execute(cases.CASES[0],{},root)

def test_freeze_stagger_and_refuse_changed_manifest(tmp_path,monkeypatch):
    frozen=models.prepare(tmp_path)
    assert frozen['manifest']['interarrival_seconds']==.4
    assert frozen['manifest']['per_approach_headway_seconds']==1.6
    assert frozen['manifest']['demand_sequence']==[asdict(r) for r in cases.template()]
    assert models.prepare(tmp_path)==frozen
    monkeypatch.setattr(models,'sources',lambda:{'changed.py':'hash'})
    with pytest.raises(RuntimeError,match='MANIFEST_CHANGED'):
        models.prepare(tmp_path)

def test_same_control_loop_and_observer_semantics():
    from post_training_evaluation.runner import run_episode
    from targeted_validation.metrics import PanelTelemetry
    from scalability_validation import metrics as original
    assert runner.run_episode is run_episode
    assert issubclass(metrics.ScalabilityTelemetry,PanelTelemetry)
    # Original observer implementation is preserved byte-for-byte; imports
    # resolve to the independent version's frozen source inventory.
    assert Path(metrics.__file__).read_bytes()==Path(original.__file__).read_bytes()
    assert metrics.DEADLOCK_DURATION_SECONDS==original.DEADLOCK_DURATION_SECONDS==15.

def test_cli_defaults_v2_and_preflight_cannot_start_suite(monkeypatch,tmp_path):
    import run_scalability_validation as cli
    calls=[]
    monkeypatch.setattr(runner,'preflight',lambda root:calls.append(root))
    monkeypatch.setattr(runner,'run',lambda *args:pytest.fail('Full scientific suite must not start from preflight'))
    monkeypatch.setattr('sys.argv',['run_scalability_validation.py','--preflight','--output-root',str(tmp_path)])
    cli.main()
    assert calls==[tmp_path]

@pytest.mark.parametrize('flag',['--run','--prepare','--preflight'])
def test_cli_refuses_v1_launches(monkeypatch,flag):
    import run_scalability_validation as cli
    monkeypatch.setattr('sys.argv',['run_scalability_validation.py','--version','v1',flag])
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code==2

def test_v2_report_identifies_family_and_excludes_preflight(tmp_path):
    models.prepare(tmp_path)
    payload=reporting.report(tmp_path)
    assert payload['evidence_family']=='SCALABILITY_VALIDATION_V2'
    assert payload['scientific_episodes_recorded']==0
    assert all(r['classification']=='NOT_RUN' for r in payload['rows'])
    md=(tmp_path/'latest/SCALABILITY_REPORT.md').read_text()
    assert '|---|---|' in md
    assert '| NOT_RUN |\n| SV-08' in md
    assert '0.4-second staggered' in md
    assert len(list((tmp_path/'latest/plots').glob('*.png')))==7

def test_original_evidence_v1_runtime_and_operational_sources_unchanged():
    inventory=json.loads(Path('results/scalability_validation/audit_v2/prior_evidence_inventory.json').read_text(encoding='utf-8-sig'))
    assert len(inventory)>=1092
    assert all(file_hash(path).lower()==sha.lower() for path,sha in inventory.items())
    archive=Path('results/scalability_validation_archives/v1/runtime')
    archived=json.loads(archive.parent.joinpath('runtime_inventory.json').read_text(encoding='utf-8-sig'))
    assert all(file_hash(archive/path).lower()==sha.lower() for path,sha in archived.items())
    for path,sha in archived.items():
        if path=='run_scalability_validation.py':
            continue  # Only CLI dispatch changed; archived original remains available.
        from naming_compat import historical_path
        assert file_hash(historical_path(path)).lower()==sha.lower()
