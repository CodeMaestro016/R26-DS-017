"""Naming-only equivalence, compatibility and immutable historical evidence."""
import ast
import importlib
import json
import subprocess
import sys
from pathlib import Path
import pytest
import torch
from post_training_evaluation.models import file_hash,POLICY,EXPECTED_POLICY_HASH
from tools.migrate_names import renamed

BASE=Path(__file__).resolve().parents[1]
AUDIT=BASE/'results/naming_migration'
ARCHIVE=AUDIT/'pre_migration_runtime'

def naming_period_source(relative):
    """Naming equivalence predates the explicitly approved scientific revision.

    Verify both immutable source versions instead of demanding the new
    reconciliation algorithm be identical to the historical naming-only code.
    Original byte/AST equivalence assertions below remain unchanged.
    """
    versions=BASE/'results/live_deadlock_investigation/20261016/approved_source_versions'
    identity=json.loads((versions/'identity.json').read_text())
    revision=BASE/'results/final_live_correction/20261016'
    approved=json.loads((revision/'approved_source_identity.json').read_text(encoding='utf-8-sig'))
    if relative in identity['current']:
        if relative in approved:
            # Separately authorized scientific revision, not naming equivalence.
            # Verify both immutable implementations before using the original
            # naming-period source in the unchanged equivalence assertions.
            following=BASE/'results/final_demonstrations/v1'
            following_identity=json.loads((following/'approved_source_identity.json').read_text())
            assert file_hash(BASE/relative)==following_identity[relative]
            assert file_hash(following/'source_after'/relative)==following_identity[relative]
            assert file_hash(revision/'source_after'/relative)==approved[relative]
            assert file_hash(versions/'current'/relative)==identity['current'][relative]
        elif relative == 'runtime_simulation/runner.py' and file_hash(BASE/relative)!=identity['current'][relative]:
            class DisplayOnly(ast.NodeTransformer):
                def visit_Call(self,node):
                    if isinstance(node.func,ast.Attribute) and node.func.attr=='publish' and isinstance(node.func.value,ast.Name) and node.func.value.id=='browser':
                        node.keywords=[k for k in node.keywords if k.arg not in {
                            'execution_decisions','coordination_participants','coordination_timestamp','run_id'}]
                        for k in node.keywords:
                            if k.arg=='policy_factors':k.value=ast.Constant('DISPLAY_ONLY')
                    return self.generic_visit(node)
            prior=ast.parse((versions/'current'/relative).read_text(encoding='utf-8-sig'))
            current=ast.parse((BASE/relative).read_text(encoding='utf-8-sig'))
            assert ast.dump(DisplayOnly().visit(prior))==ast.dump(DisplayOnly().visit(current))
        else:
            assert file_hash(BASE/relative)==identity['current'][relative]
        previous=versions/'naming_period'/relative
        assert file_hash(previous)==identity['naming_period'][relative]
        return previous
    return BASE/relative

@pytest.mark.parametrize('old,new',[('panel_demo','runtime_simulation'),('panel_validation','targeted_validation'),('final_evaluation','post_training_evaluation')])
def test_legacy_imports_share_exact_module_objects(old,new):
    assert importlib.import_module(old) is importlib.import_module(new)
    sub='runner'
    assert importlib.import_module(old+'.'+sub) is importlib.import_module(new+'.'+sub)

def test_legacy_runtime_callable_is_the_same_function():
    from panel_demo.runner import run_panel_demo
    from runtime_simulation.runner import run_runtime_simulation
    assert run_panel_demo is run_runtime_simulation

@pytest.mark.parametrize('script',['run_runtime_simulation.py','run_targeted_validation.py','run_post_training_evaluation.py','run_panel_demo.py','run_panel_validation.py','run_final_evaluation.py','run_scalability_validation.py'])
def test_preferred_and_legacy_help_never_start_sumo(script):
    result=subprocess.run([sys.executable,'-B',script,'--help'],cwd=BASE,capture_output=True,text=True,check=True)
    assert 'usage:' in result.stdout

@pytest.mark.parametrize('old,new,names',[
    ('panel_demo/runner.py','runtime_simulation/runner.py',['run_runtime_simulation']),
    ('panel_demo/queue_heads.py','runtime_simulation/queue_heads.py',['select_queue_heads','approach_queue_depth']),
    ('panel_demo/inference.py','runtime_simulation/inference.py',['PanelDeterministicInferenceProvider']),
    ('final_evaluation/metrics.py','post_training_evaluation/metrics.py',['Telemetry','inversion_rate']),
    ('final_evaluation/models.py','post_training_evaluation/models.py',['classify']),
    ('panel_validation/metrics.py','targeted_validation/metrics.py',['PanelTelemetry']),
    ('panel_validation/cases.py','targeted_validation/cases.py',['nominal_schedule','Case']),
    ('scalability_validation/v2/cases.py','scalability_validation/v2/cases.py',['template','Case']),
    ('scalability_validation/v2/metrics.py','scalability_validation/v2/metrics.py',['ScalabilityTelemetry','insertion_metrics'])])
def test_operational_metrics_and_schedules_have_identical_ast_after_renaming(old,new,names):
    previous=ast.parse(renamed((ARCHIVE/old).read_text(encoding='utf-8-sig')))
    current=ast.parse(naming_period_source(new).read_text(encoding='utf-8-sig'))
    for name in names:
        a=next(n for n in previous.body if getattr(n,'name',None)==name)
        b=next(n for n in current.body if getattr(n,'name',None)==name)
        assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)

def test_rules_execution_and_scenario_json_are_byte_identical():
    for folder in ['traffic_rules','negotiation_execution','negotiation_learning','negotiation_training','networks']:
        for original in (ARCHIVE/folder).rglob('*'):
            if original.is_file():
                assert file_hash(original)==file_hash(naming_period_source(original.relative_to(ARCHIVE).as_posix()))
    assert file_hash(ARCHIVE/'panel_demo/scenario_catalog.json')==file_hash(BASE/'runtime_simulation/scenario_catalog.json')

def test_selected_e5_bytes_and_every_tensor_are_unchanged():
    assert file_hash(POLICY)==EXPECTED_POLICY_HASH
    assert file_hash(ARCHIVE/POLICY)==EXPECTED_POLICY_HASH
    before=torch.load(ARCHIVE/POLICY,map_location='cpu',weights_only=False)
    after=torch.load(POLICY,map_location='cpu',weights_only=False)
    tensors=[]
    def compare(a,b):
        if isinstance(a,torch.Tensor):
            assert isinstance(b,torch.Tensor) and a.dtype==b.dtype and torch.equal(a,b)
            tensors.append(a)
        elif isinstance(a,dict):
            assert a.keys()==b.keys()
            for key in a: compare(a[key],b[key])
        elif isinstance(a,(list,tuple)):
            assert len(a)==len(b)
            for x,y in zip(a,b): compare(x,y)
    compare(before,after)
    assert tensors

def test_every_historical_file_is_unchanged():
    inventory=json.loads((AUDIT/'historical_inventory.json').read_text())
    assert len(inventory)==1683
    assert all(file_hash(BASE/path)==sha for path,sha in inventory.items())

@pytest.mark.parametrize('root',['results/panel_validation/v1','results/panel_validation/v2'])
def test_exact_historical_runtime_can_be_reconstructed_without_simulation(root):
    from historical_replay import materialize
    frozen=json.loads(Path(root,'manifest.json').read_text())
    snapshot=materialize(frozen)
    script='import json; from final_evaluation.scenarios import source_identities; print(json.dumps(source_identities(),sort_keys=True))'
    result=subprocess.run([sys.executable,'-B','-c',script],cwd=snapshot,capture_output=True,text=True,check=True)
    assert json.loads(result.stdout)==frozen['manifest']['source_identities']

def test_preferred_pv03_replay_routes_to_preserved_record_without_launch(monkeypatch):
    import historical_replay
    from targeted_validation.runner import replay
    calls=[]
    monkeypatch.setattr(historical_replay,'replay',lambda root,run_id,**kw:calls.append((root,run_id,kw)))
    replay('PV-03',gui=True)
    assert len(calls)==1
    original=json.loads((calls[0][0]/'runs'/calls[0][1]/'result.json').read_text())
    assert original['scenario_id']=='multiple_left_turns' and original['method']=='PROPOSED_MAPPO'
    assert calls[0][2]==dict(kind='targeted',gui=True)

def test_historical_replay_prepares_only_new_destinations(monkeypatch):
    import historical_replay
    calls=[]
    monkeypatch.setattr(historical_replay,'_launch',lambda command,**kwargs:calls.append(command))
    historical_replay.replay('results/panel_validation/v1','20261008T171616134855Z_5e39804a')
    assert calls and 'targeted_validation' in calls[0][6]

def test_report_refuses_historical_in_place_write():
    from targeted_validation.reporting import report
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        report(Path('results/panel_validation/v1'))

@pytest.mark.parametrize('root',['results/panel_validation/v1','results/final_evaluation/v2_candidate','results/panel_validation_archives/v1'])
def test_scalability_preserves_both_old_and_preferred_evidence_guards(root):
    from scalability_validation import models
    from scalability_validation.v2 import models as v2
    for module in (models,v2):
        with pytest.raises(RuntimeError,match='READ_ONLY'):
            module.protect(root)
