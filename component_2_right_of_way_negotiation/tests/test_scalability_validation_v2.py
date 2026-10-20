"""Staggered evaluation changes only; historical synchronized evidence survives."""
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import SimpleNamespace from types for the operations below.
from types import SimpleNamespace
# Import pytest for use in this module.
import pytest
# Import asdict from dataclasses for the operations below.
from dataclasses import asdict
# Import MapPathManager from conflict for the operations below.
from conflict import MapPathManager
# Import digest, file_hash, EXPECTED_POLICY_HASH, POLICY from post_training_evaluation.models for the operations
# below.
from post_training_evaluation.models import digest, file_hash, EXPECTED_POLICY_HASH, POLICY
# Import schedule_payload from post_training_evaluation.scenarios for the operations below.
from post_training_evaluation.scenarios import schedule_payload
# Import cases as v1_cases from scalability_validation for the operations below.
from scalability_validation import cases as v1_cases
# Import cases, models, metrics, runner, reporting from scalability_validation.v2 for the operations below.
from scalability_validation.v2 import cases, models, metrics, runner, reporting

# Check exact forty staggered entries balanced legal prefixes using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_exact_forty_staggered_entries_balanced_legal_prefixes():
    # Set entries to the result of cases.template().
    entries = cases.template()
    # Require the number of entries in entries equals 40; otherwise raise AssertionError.
    assert len(entries)==40
    # Require a list of r.scheduled_departure_seconds for r in entries equals a list of the rounded value of i
    # multiplied by 0.4 for i in the integer range defined by 40; otherwise raise AssertionError.
    assert [r.scheduled_departure_seconds for r in entries]==[round(i*.4,10) for i in range(40)]
    # Require the number of entries in a set of r.scheduled_departure_seconds for r in entries equals 40;
    # otherwise raise AssertionError.
    assert len({r.scheduled_departure_seconds for r in entries})==40
    # Require a list of r.approach for r in entries equals a list built from the text 'NESW' multiplied by 10;
    # otherwise raise AssertionError.
    assert [r.approach for r in entries]==list('NESW')*10
    # Require cases.HEADWAY equals 1.6 and cases.INTERARRIVAL equals 0.4; otherwise raise AssertionError.
    assert cases.HEADWAY==1.6 and cases.INTERARRIVAL==.4
    # Set legal to MapPathManager().paths.
    legal=MapPathManager().paths
    # Iterate over corresponding items paired from the result of v1_cases.template(), entries, binding each item
    # to (old, new).
    for old,new in zip(v1_cases.template(),entries):
        # Require a tuple containing old.approach, old.movement_path_id, old.sequence_index equals a tuple
        # containing new.approach, new.movement_path_id, new.sequence_index; otherwise raise AssertionError.
        assert (old.approach,old.movement_path_id,old.sequence_index)==(new.approach,new.movement_path_id,new.sequence_index)
        # Require new.movement_path_id belongs to legal; otherwise raise AssertionError.
        assert new.movement_path_id in legal
    # Set seeds to an empty set.
    seeds=set()
    # Require a list of c.count for c in cases.CASES equals a list containing 4, 8, 12, 16, 24, 32, 40; otherwise
    # raise AssertionError.
    assert [c.count for c in cases.CASES]==[4,8,12,16,24,32,40]
    # Iterate over cases.CASES, binding each item to case.
    for case in cases.CASES:
        # Set schedule to the result of case.schedule().
        schedule=case.schedule()
        # Require whether every item is true in a lazy sequence of the number of entries in rows equals case.count
        # integer-divided by 4 for rows in values from schedule; otherwise raise AssertionError.
        assert all(len(rows)==case.count//4 for rows in schedule.values())
        # Set flattened to the sorted values from a lazy sequence of r for rows in values from schedule.
        flattened=sorted((r for rows in schedule.values() for r in rows),key=lambda r:r.scheduled_departure_seconds)
        # Require a tuple built from flattened equals entries sliced by :case.count; otherwise raise
        # AssertionError.
        assert tuple(flattened)==entries[:case.count]
        # Require case.scenario().budget_seconds equals 180.0; otherwise raise AssertionError.
        assert case.scenario().budget_seconds==180.
        # Add an integer built from digest((models.PROTOCOL, case.scenario().scenario_id, None, 'PROPOSED_MAPPO'))
        # sliced by :16 modulo 2 raised to the power 31 to seeds.
        seeds.add(int(digest((models.PROTOCOL,case.scenario().scenario_id,None,'PROPOSED_MAPPO'))[:16],16)%(2**31))
    # Require the number of entries in seeds equals 1; otherwise raise AssertionError.
    assert len(seeds)==1
    # Require the sum of a lazy sequence of c.scenario().budget_seconds for c in cases.CASES equals 1260.0;
    # otherwise raise AssertionError.
    assert sum(c.scenario().budget_seconds for c in cases.CASES)==1260.

# Check exact first twelve predeclared entries using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_exact_first_twelve_predeclared_entries():
    # Set expected to a list containing a tuple containing the text 'N', the text 'LEFT', 0.0, a tuple containing
    # the text 'E', the text...
    expected=[('N','LEFT',0.),('E','STRAIGHT',.4),('S','RIGHT',.8),('W','STRAIGHT',1.2),
        # Include a tuple containing the text 'N', the text 'STRAIGHT', 1.6 in this list.
        ('N','STRAIGHT',1.6),('E','RIGHT',2.),('S','LEFT',2.4),('W','RIGHT',2.8),
        # Include a tuple containing the text 'S', the text 'STRAIGHT', 4.0 in this list.
        ('N','RIGHT',3.2),('E','LEFT',3.6),('S','STRAIGHT',4.),('W','LEFT',4.4)]
    # Require a list of a tuple containing r.approach, r.movement_path_id.rsplit('_', 1) at 1,
    # r.scheduled_departure_seconds for r in cases.template() sliced by :12 equals expected; otherwise raise
    # AssertionError.
    assert [(r.approach,r.movement_path_id.rsplit('_',1)[1],r.scheduled_departure_seconds) for r in cases.template()[:12]]==expected

# Check v1 stays synchronized and is a separate family using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_v1_stays_synchronized_and_is_a_separate_family():
    # Require a list of r.scheduled_departure_seconds for r in v1_cases.template() sliced by :4 equals a list
    # containing 0.0, 0.0, 0.0, 0.0; otherwise raise AssertionError.
    assert [r.scheduled_departure_seconds for r in v1_cases.template()[:4]]==[0.,0.,0.,0.]
    # Require models.PROTOCOL equals the text 'SCALABILITY_VALIDATION_V2'; otherwise raise AssertionError.
    assert models.PROTOCOL=='SCALABILITY_VALIDATION_V2'
    # Require models.ROOT equals the result of Path(the text 'results/scalability_validation/v2'); otherwise raise
    # AssertionError.
    assert models.ROOT==Path('results/scalability_validation/v2')
    # Require the result of file_hash(POLICY) equals EXPECTED_POLICY_HASH; otherwise raise AssertionError.
    assert file_hash(POLICY)==EXPECTED_POLICY_HASH

# Apply pytest.mark.parametrize('root', ['results/scalability_validation/v1',... as a decorator to configure the
# following definition.
@pytest.mark.parametrize('root',['results/scalability_validation/v1','results/scalability_validation/v1/new','results/scalability_validation_archives/v1','results/targeted_validation/v2'])
# Check old evidence roots are read only using the setup, calls, and assertions below.
# Input root: the base directory used to resolve files.
# Output: no explicit value; normal completion returns None.
def test_old_evidence_roots_are_read_only(root):
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        # Call models.prepare with the supplied arguments.
        models.prepare(root)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        # Call reporting.report with the supplied arguments.
        reporting.report(root)
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        # Call runner.execute with the supplied arguments.
        runner.execute(cases.CASES[0],{},root)

# Check freeze stagger and refuse changed manifest using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_freeze_stagger_and_refuse_changed_manifest(tmp_path,monkeypatch):
    # Set frozen to the result of models.prepare(tmp_path).
    frozen=models.prepare(tmp_path)
    # Require frozen['manifest'] at 'interarrival_seconds' equals 0.4; otherwise raise AssertionError.
    assert frozen['manifest']['interarrival_seconds']==.4
    # Require frozen['manifest'] at 'per_approach_headway_seconds' equals 1.6; otherwise raise AssertionError.
    assert frozen['manifest']['per_approach_headway_seconds']==1.6
    # Require frozen['manifest'] at 'demand_sequence' equals a list of the result of asdict(r) for r in the result
    # of cases.template(); otherwise raise AssertionError.
    assert frozen['manifest']['demand_sequence']==[asdict(r) for r in cases.template()]
    # Require the result of models.prepare(tmp_path) equals frozen; otherwise raise AssertionError.
    assert models.prepare(tmp_path)==frozen
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(models,'sources',lambda:{'changed.py':'hash'})
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='MANIFEST_CHANGED'):
        # Call models.prepare with the supplied arguments.
        models.prepare(tmp_path)

# Check same control loop and observer semantics using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_same_control_loop_and_observer_semantics():
    # Import run_episode from post_training_evaluation.runner for the operations below.
    from post_training_evaluation.runner import run_episode
    # Import PanelTelemetry from targeted_validation.metrics for the operations below.
    from targeted_validation.metrics import PanelTelemetry
    # Import metrics as original from scalability_validation for the operations below.
    from scalability_validation import metrics as original
    # Require runner.run_episode is the same object as run_episode; otherwise raise AssertionError.
    assert runner.run_episode is run_episode
    # Require the result of issubclass(metrics.ScalabilityTelemetry, PanelTelemetry); otherwise raise
    # AssertionError.
    assert issubclass(metrics.ScalabilityTelemetry,PanelTelemetry)
    # Original observer implementation is preserved byte-for-byte; imports
    # resolve to the independent version's frozen source inventory.
    # Require the bytes read from Path(metrics.__file__) equals the bytes read from Path(original.__file__);
    # otherwise raise AssertionError.
    assert Path(metrics.__file__).read_bytes()==Path(original.__file__).read_bytes()
    # Require metrics.DEADLOCK_DURATION_SECONDS equals original.DEADLOCK_DURATION_SECONDS; equals 15.0; otherwise
    # raise AssertionError.
    assert metrics.DEADLOCK_DURATION_SECONDS==original.DEADLOCK_DURATION_SECONDS==15.

# Check cli defaults v2 and preflight cannot start suite using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_cli_defaults_v2_and_preflight_cannot_start_suite(monkeypatch,tmp_path):
    # Import run_scalability_validation as cli for use in this module.
    import run_scalability_validation as cli
    # Set calls to an empty list.
    calls=[]
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner,'preflight',lambda root:calls.append(root))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(runner,'run',lambda *args:pytest.fail('Full scientific suite must not start from preflight'))
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr('sys.argv',['run_scalability_validation.py','--preflight','--output-root',str(tmp_path)])
    # Call cli.main with the supplied arguments.
    cli.main()
    # Require calls equals a list containing tmp_path; otherwise raise AssertionError.
    assert calls==[tmp_path]

# Apply pytest.mark.parametrize('flag', ['--run', '--prepare', '--preflight']) as a decorator to configure the
# following definition.
@pytest.mark.parametrize('flag',['--run','--prepare','--preflight'])
# Check cli refuses v1 launches using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Input flag: the supplied flag.
# Output: no explicit value; normal completion returns None.
def test_cli_refuses_v1_launches(monkeypatch,flag):
    # Import run_scalability_validation as cli for use in this module.
    import run_scalability_validation as cli
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr('sys.argv',['run_scalability_validation.py','--version','v1',flag])
    # Enter the result of pytest.raises(SystemExit) as error and run the enclosed operations within that context.
    with pytest.raises(SystemExit) as error:
        # Call cli.main with the supplied arguments.
        cli.main()
    # Require error.value.code equals 2; otherwise raise AssertionError.
    assert error.value.code==2

# Check v2 report identifies family and excludes preflight using the setup, calls, and assertions below.
# Input tmp_path: the supplied tmp path.
# Output: no explicit value; normal completion returns None.
def test_v2_report_identifies_family_and_excludes_preflight(tmp_path):
    # Call models.prepare with the supplied arguments.
    models.prepare(tmp_path)
    # Set payload to the result of reporting.report(tmp_path).
    payload=reporting.report(tmp_path)
    # Require payload at 'evidence_family' equals the text 'SCALABILITY_VALIDATION_V2'; otherwise raise
    # AssertionError.
    assert payload['evidence_family']=='SCALABILITY_VALIDATION_V2'
    # Require payload at 'scientific_episodes_recorded' equals 0; otherwise raise AssertionError.
    assert payload['scientific_episodes_recorded']==0
    # Require whether every item is true in a lazy sequence of r at 'classification' equals the text 'NOT_RUN' for
    # r in payload at 'rows'; otherwise raise AssertionError.
    assert all(r['classification']=='NOT_RUN' for r in payload['rows'])
    # Set md to the text read from (tmp_path / 'latest/SCALABILITY_REPORT.md').
    md=(tmp_path/'latest/SCALABILITY_REPORT.md').read_text()
    # Require the text '|---|---|' belongs to md; otherwise raise AssertionError.
    assert '|---|---|' in md
    # Require the text '| NOT_RUN | | SV-08' belongs to md; otherwise raise AssertionError.
    assert '| NOT_RUN |\n| SV-08' in md
    # Require the text '0.4-second staggered' belongs to md; otherwise raise AssertionError.
    assert '0.4-second staggered' in md
    # Require the number of entries in a list built from the result of (tmp_path / 'latest/plots').glob('*.png')
    # equals 7; otherwise raise AssertionError.
    assert len(list((tmp_path/'latest/plots').glob('*.png')))==7

# Check original evidence v1 runtime and operational sources unchanged using the setup, calls, and assertions
# below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def test_original_evidence_v1_runtime_and_operational_sources_unchanged():
    # Set inventory to the decoded data produced by json.loads from the text read from
    # Path('results/scalability_validation/audit_v2/prior_evidence_inventory.json').
    inventory=json.loads(Path('results/scalability_validation/audit_v2/prior_evidence_inventory.json').read_text(encoding='utf-8-sig'))
    # Require the number of entries in inventory is at least 1092; otherwise raise AssertionError.
    assert len(inventory)>=1092
    # Require whether every item is true in a lazy sequence of the result of file_hash(path).lower() equals the
    # result of sha.lower() for (path, sha) in key/value pairs from inventory; otherwise raise AssertionError.
    assert all(file_hash(path).lower()==sha.lower() for path,sha in inventory.items())
    # Set archive to the result of Path(the text 'results/scalability_validation_archives/v1/runtime').
    archive=Path('results/scalability_validation_archives/v1/runtime')
    # Set archived to the decoded data produced by json.loads from the text read from
    # archive.parent.joinpath('runtime_inventory.json').
    archived=json.loads(archive.parent.joinpath('runtime_inventory.json').read_text(encoding='utf-8-sig'))
    # Require whether every item is true in a lazy sequence of the result of file_hash(archive / path).lower()
    # equals the result of sha.lower() for (path, sha) in key/value pairs from archived; otherwise raise
    # AssertionError.
    assert all(file_hash(archive/path).lower()==sha.lower() for path,sha in archived.items())
    # Iterate over key/value pairs from archived, binding each item to (path, sha).
    for path,sha in archived.items():
        # Run this branch when path equals the text 'run_scalability_validation.py'.
        if path=='run_scalability_validation.py':
            # Skip the rest of this loop iteration and process the next item.
            continue  # Only CLI dispatch changed; archived original remains available.
        # Import historical_path from naming_compat for the operations below.
        from naming_compat import historical_path
        # Require the result of file_hash(historical_path(path)).lower() equals the result of sha.lower();
        # otherwise raise AssertionError.
        assert file_hash(historical_path(path)).lower()==sha.lower()
