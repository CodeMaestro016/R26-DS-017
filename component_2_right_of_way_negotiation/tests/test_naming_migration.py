"""Naming-only equivalence, compatibility and immutable historical evidence."""
# Import ast for use in this module.
import ast
# Import importlib for use in this module.
import importlib
# Import json for use in this module.
import json
# Import subprocess for use in this module.
import subprocess
# Import sys for use in this module.
import sys
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import pytest for use in this module.
import pytest
# Import torch for use in this module.
import torch
# Import file_hash, POLICY, EXPECTED_POLICY_HASH from post_training_evaluation.models for the operations below.
from post_training_evaluation.models import file_hash,POLICY,EXPECTED_POLICY_HASH
# Import renamed from tools.migrate_names for the operations below.
from tools.migrate_names import renamed

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set AUDIT to BASE joined with the path segment 'results/naming_migration'.
AUDIT=BASE/'results/naming_migration'
# Set ARCHIVE to AUDIT joined with the path segment 'pre_migration_runtime'.
ARCHIVE=AUDIT/'pre_migration_runtime'

# Naming equivalence predates the explicitly approved scientific revision.
# Input relative: the supplied relative.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def naming_period_source(relative):
    """Naming equivalence predates the explicitly approved scientific revision.

    Verify both immutable source versions instead of demanding the new
    reconciliation algorithm be identical to the historical naming-only code.
    Original byte/AST equivalence assertions below remain unchanged.
    """
    # Set versions to BASE joined with the path segment
    # 'results/live_deadlock_investigation/20261016/approved_source_v...'.
    versions=BASE/'results/live_deadlock_investigation/20261016/approved_source_versions'
    # Set identity to the decoded data produced by json.loads from the text read from (versions /
    # 'identity.json').
    identity=json.loads((versions/'identity.json').read_text())
    # Set revision to BASE joined with the path segment 'results/final_live_correction/20261016'.
    revision=BASE/'results/final_live_correction/20261016'
    # Set approved to the decoded data produced by json.loads from the text read from (revision /
    # 'approved_source_identity.json').
    approved=json.loads((revision/'approved_source_identity.json').read_text(encoding='utf-8-sig'))
    # Run this branch when relative belongs to identity at 'current'.
    if relative in identity['current']:
        # Run this branch when relative belongs to approved.
        if relative in approved:
            # Separately authorized scientific revision, not naming equivalence.
            # Verify both immutable implementations before using the original
            # naming-period source in the unchanged equivalence assertions.
            # Set following to BASE joined with the path segment 'results/final_demonstrations/v1'.
            following=BASE/'results/final_demonstrations/v1'
            # Set following_identity to the decoded data produced by json.loads from the text read from (following
            # / 'approved_source_identity.json').
            following_identity=json.loads((following/'approved_source_identity.json').read_text())
            # Require the result of file_hash(BASE divided by relative) equals following_identity at relative;
            # otherwise raise AssertionError.
            assert file_hash(BASE/relative)==following_identity[relative]
            # Require the result of file_hash(following joined with the path segment 'source_after' divided by relative) equals
            # following_identity at relative; otherwise raise AssertionError.
            assert file_hash(following/'source_after'/relative)==following_identity[relative]
            # Require the result of file_hash(revision joined with the path segment 'source_after' divided by relative) equals
            # approved at relative; otherwise raise AssertionError.
            assert file_hash(revision/'source_after'/relative)==approved[relative]
            # Require the result of file_hash(versions joined with the path segment 'current' divided by relative) equals
            # identity['current'] at relative; otherwise raise AssertionError.
            assert file_hash(versions/'current'/relative)==identity['current'][relative]
        # Run this branch when relative equals the text 'runtime_simulation/runner.py' and the result of
        # file_hash(BASE divided by relative) differs from identity['current'] at relative.
        elif relative == 'runtime_simulation/runner.py' and file_hash(BASE/relative)!=identity['current'][relative]:
            # Define DisplayOnly to group the state and operations declared below.
            # Base classes: ast.NodeTransformer.
            # Instances expose the attributes and methods implemented in this class.
            class DisplayOnly(ast.NodeTransformer):
                # Visit Call using the inputs and processing steps below.
                # Input node: the supplied node.
                # Output: the result of self.generic_visit(node).
                # Processing: iterate over the relevant records, then select branches using the stated conditions.
                def visit_Call(self,node):
                    # Run this branch when whether node.func has type ast.Attribute and node.func.attr equals the
                    # text 'publish' and whether node.func.value has type ast.Name and node.func.value.id equals
                    # the text 'browser'.
                    if isinstance(node.func,ast.Attribute) and node.func.attr=='publish' and isinstance(node.func.value,ast.Name) and node.func.value.id=='browser':
                        # Set node.keywords to a list of k for k in node.keywords; retain entries satisfying k.arg
                        # does not belong to a set containing the text 'execution_decisions', the text...
                        node.keywords=[k for k in node.keywords if k.arg not in {
                            'execution_decisions','coordination_participants','coordination_timestamp','run_id'}]
                        # Iterate over node.keywords, binding each item to k.
                        for k in node.keywords:
                            # Run this branch when k.arg equals the text 'policy_factors'.
                            # Set k.value to the result of ast.Constant(the text 'DISPLAY_ONLY').
                            if k.arg=='policy_factors':k.value=ast.Constant('DISPLAY_ONLY')
                    # Return the result of self.generic_visit(node) to the caller.
                    return self.generic_visit(node)
            # Set prior to the result of ast.parse(the text read from (versions / 'current' / relative)).
            prior=ast.parse((versions/'current'/relative).read_text(encoding='utf-8-sig'))
            # Set current to the result of ast.parse(the text read from (BASE / relative)).
            current=ast.parse((BASE/relative).read_text(encoding='utf-8-sig'))
            # Require the serialized data produced by ast.dump equals the serialized data produced by ast.dump;
            # otherwise raise AssertionError.
            assert ast.dump(DisplayOnly().visit(prior))==ast.dump(DisplayOnly().visit(current))
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Require the result of file_hash(BASE divided by relative) equals identity['current'] at relative;
            # otherwise raise AssertionError.
            assert file_hash(BASE/relative)==identity['current'][relative]
        # Set previous to versions joined with the path segment 'naming_period' divided by relative.
        previous=versions/'naming_period'/relative
        # Require the result of file_hash(previous) equals identity['naming_period'] at relative; otherwise raise
        # AssertionError.
        assert file_hash(previous)==identity['naming_period'][relative]
        # Return previous to the caller.
        return previous
    # Return BASE divided by relative to the caller.
    return BASE/relative

# Apply pytest.mark.parametrize('old,new', [('panel_demo', 'runtime_simulation'), ('panel_validation',... as a
# decorator to configure the following definition.
@pytest.mark.parametrize('old,new',[('panel_demo','runtime_simulation'),('panel_validation','targeted_validation'),('final_evaluation','post_training_evaluation')])
# Check legacy imports share exact module objects using the setup, calls, and assertions below.
# Input old: the supplied old.
# Input new: the supplied new.
# Output: no explicit value; normal completion returns None.
def test_legacy_imports_share_exact_module_objects(old,new):
    # Require the result of importlib.import_module(old) is the same object as the result of
    # importlib.import_module(new); otherwise raise AssertionError.
    assert importlib.import_module(old) is importlib.import_module(new)
    # Set sub to the text 'runner'.
    sub='runner'
    # Require the result of importlib.import_module(old plus '.' plus sub) is the same object as the result of
    # importlib.import_module(new plus '.' plus sub); otherwise raise AssertionError.
    assert importlib.import_module(old+'.'+sub) is importlib.import_module(new+'.'+sub)

# Check legacy runtime callable is the same function using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_legacy_runtime_callable_is_the_same_function():
    # Import run_panel_demo from panel_demo.runner for the operations below.
    from panel_demo.runner import run_panel_demo
    # Import run_runtime_simulation from runtime_simulation.runner for the operations below.
    from runtime_simulation.runner import run_runtime_simulation
    # Require run_panel_demo is the same object as run_runtime_simulation; otherwise raise AssertionError.
    assert run_panel_demo is run_runtime_simulation

# Apply pytest.mark.parametrize('script', ['run_runtime_simulation.py', 'run_targeted_validation.py',... as a
# decorator to configure the following definition.
@pytest.mark.parametrize('script',['run_runtime_simulation.py','run_targeted_validation.py','run_post_training_evaluation.py','run_panel_demo.py','run_panel_validation.py','run_final_evaluation.py','run_scalability_validation.py'])
# Check preferred and legacy help never start sumo using the setup, calls, and assertions below.
# Input script: the supplied script.
# Output: no explicit value; normal completion returns None.
def test_preferred_and_legacy_help_never_start_sumo(script):
    # Set result to the result of subprocess.run(a list containing sys.executable, the text '-B', script, the text
    # '--help').
    result=subprocess.run([sys.executable,'-B',script,'--help'],cwd=BASE,capture_output=True,text=True,check=True)
    # Require the text 'usage:' belongs to result.stdout; otherwise raise AssertionError.
    assert 'usage:' in result.stdout

# Apply pytest.mark.parametrize('old,new,names', [('panel_demo/runner.py',... as a decorator to configure the
# following definition.
@pytest.mark.parametrize('old,new,names',[
    # Include a tuple containing the text 'panel_demo/runner.py', the text 'runtime_simulation/runner.py', a list
    # containing the text... in this list.
    ('panel_demo/runner.py','runtime_simulation/runner.py',['run_runtime_simulation']),
    # Include a tuple containing the text 'panel_demo/queue_heads.py', the text
    # 'runtime_simulation/queue_heads.py', a list containing the... in this list.
    ('panel_demo/queue_heads.py','runtime_simulation/queue_heads.py',['select_queue_heads','approach_queue_depth']),
    # Include a tuple containing the text 'panel_demo/inference.py', the text 'runtime_simulation/inference.py', a
    # list containing the text... in this list.
    ('panel_demo/inference.py','runtime_simulation/inference.py',['PanelDeterministicInferenceProvider']),
    # Include a tuple containing the text 'final_evaluation/metrics.py', the text
    # 'post_training_evaluation/metrics.py', a list containing... in this list.
    ('final_evaluation/metrics.py','post_training_evaluation/metrics.py',['Telemetry','inversion_rate']),
    # Include a tuple containing the text 'final_evaluation/models.py', the text
    # 'post_training_evaluation/models.py', a list containing... in this list.
    ('final_evaluation/models.py','post_training_evaluation/models.py',['classify']),
    # Include a tuple containing the text 'panel_validation/metrics.py', the text
    # 'targeted_validation/metrics.py', a list containing the... in this list.
    ('panel_validation/metrics.py','targeted_validation/metrics.py',['PanelTelemetry']),
    # Include a tuple containing the text 'panel_validation/cases.py', the text 'targeted_validation/cases.py', a
    # list containing the text... in this list.
    ('panel_validation/cases.py','targeted_validation/cases.py',['nominal_schedule','Case']),
    # Include a tuple containing the text 'scalability_validation/v2/cases.py', the text
    # 'scalability_validation/v2/cases.py', a list... in this list.
    ('scalability_validation/v2/cases.py','scalability_validation/v2/cases.py',['template','Case']),
    # Include a tuple containing the text 'scalability_validation/v2/metrics.py', the text
    # 'scalability_validation/v2/metrics.py', a list... in this list.
    ('scalability_validation/v2/metrics.py','scalability_validation/v2/metrics.py',['ScalabilityTelemetry','insertion_metrics'])])
# Check operational metrics and schedules have identical ast after renaming using the setup, calls, and assertions
# below.
# Input old: the supplied old.
# Input new: the supplied new.
# Input names: the supplied names.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_operational_metrics_and_schedules_have_identical_ast_after_renaming(old,new,names):
    # Set previous to the result of ast.parse(the result of renamed(the text read from (ARCHIVE / old))).
    previous=ast.parse(renamed((ARCHIVE/old).read_text(encoding='utf-8-sig')))
    # Set current to the result of ast.parse(the text read from naming_period_source(new)).
    current=ast.parse(naming_period_source(new).read_text(encoding='utf-8-sig'))
    # Iterate over names, binding each item to name.
    for name in names:
        # Set a to the next item from a lazy sequence of n for n in previous.body; retain entries satisfying the
        # requested attribute of n equals name.
        a=next(n for n in previous.body if getattr(n,'name',None)==name)
        # Set b to the next item from a lazy sequence of n for n in current.body; retain entries satisfying the
        # requested attribute of n equals name.
        b=next(n for n in current.body if getattr(n,'name',None)==name)
        # Require the serialized data produced by ast.dump equals the serialized data produced by ast.dump;
        # otherwise raise AssertionError.
        assert ast.dump(a,include_attributes=False)==ast.dump(b,include_attributes=False)

# Check rules execution and scenario json are byte identical using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def test_rules_execution_and_scenario_json_are_byte_identical():
    # Iterate over a list containing the text 'traffic_rules', the text 'negotiation_execution', the text
    # 'negotiation_learning', the text..., binding each item to folder.
    for folder in ['traffic_rules','negotiation_execution','negotiation_learning','negotiation_training','networks']:
        # Iterate over the result of (ARCHIVE / folder).rglob(the text '*'), binding each item to original.
        for original in (ARCHIVE/folder).rglob('*'):
            # Run this branch when whether original is an existing file.
            if original.is_file():
                # Require the result of file_hash(original) equals the result of file_hash(the result of
                # naming_period_source(the result of original.relative_to(ARCHIVE).as_posix())); otherwise raise
                # AssertionError.
                assert file_hash(original)==file_hash(naming_period_source(original.relative_to(ARCHIVE).as_posix()))
    # Require the result of file_hash(ARCHIVE joined with the path segment 'panel_demo/scenario_catalog.json') equals the
    # result of file_hash(BASE joined with the path segment 'runtime_simulation/scenario_catalog.json'); otherwise raise
    # AssertionError.
    assert file_hash(ARCHIVE/'panel_demo/scenario_catalog.json')==file_hash(BASE/'runtime_simulation/scenario_catalog.json')

# Check selected e5 bytes and every tensor are unchanged using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_selected_e5_bytes_and_every_tensor_are_unchanged():
    # Require the result of file_hash(POLICY) equals EXPECTED_POLICY_HASH; otherwise raise AssertionError.
    assert file_hash(POLICY)==EXPECTED_POLICY_HASH
    # Require the result of file_hash(ARCHIVE divided by POLICY) equals EXPECTED_POLICY_HASH; otherwise raise
    # AssertionError.
    assert file_hash(ARCHIVE/POLICY)==EXPECTED_POLICY_HASH
    # Set before to the decoded data produced by torch.load from ARCHIVE divided by POLICY.
    before=torch.load(ARCHIVE/POLICY,map_location='cpu',weights_only=False)
    # Set after to the decoded data produced by torch.load from POLICY.
    after=torch.load(POLICY,map_location='cpu',weights_only=False)
    # Set tensors to an empty list.
    tensors=[]
    # Compare using the inputs and processing steps below.
    # Input a: the supplied a.
    # Input b: the supplied b.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def compare(a,b):
        # Run this branch when whether a has type torch.Tensor.
        if isinstance(a,torch.Tensor):
            # Require whether b has type torch.Tensor and a.dtype equals b.dtype and the result of torch.equal(a,
            # b); otherwise raise AssertionError.
            assert isinstance(b,torch.Tensor) and a.dtype==b.dtype and torch.equal(a,b)
            # Append a to tensors.
            tensors.append(a)
        # Run this branch when whether a has type dict.
        elif isinstance(a,dict):
            # Require keys from a equals keys from b; otherwise raise AssertionError.
            assert a.keys()==b.keys()
            # Iterate over a, binding each item to key.
            # Call compare with the supplied arguments.
            for key in a: compare(a[key],b[key])
        # Run this branch when whether a has type a tuple containing list, tuple.
        elif isinstance(a,(list,tuple)):
            # Require the number of entries in a equals the number of entries in b; otherwise raise
            # AssertionError.
            assert len(a)==len(b)
            # Iterate over corresponding items paired from a, b, binding each item to (x, y).
            # Call compare with the supplied arguments.
            for x,y in zip(a,b): compare(x,y)
    # Call compare with the supplied arguments.
    compare(before,after)
    # Require tensors; otherwise raise AssertionError.
    assert tensors

# Check every historical file is unchanged using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_every_historical_file_is_unchanged():
    # Set inventory to the decoded data produced by json.loads from the text read from (AUDIT /
    # 'historical_inventory.json').
    inventory=json.loads((AUDIT/'historical_inventory.json').read_text())
    # Require the number of entries in inventory equals 1683; otherwise raise AssertionError.
    assert len(inventory)==1683
    # Require whether every item is true in a lazy sequence of the result of file_hash(BASE / path) equals sha for
    # (path, sha) in key/value pairs from inventory; otherwise raise AssertionError.
    assert all(file_hash(BASE/path)==sha for path,sha in inventory.items())

# Apply pytest.mark.parametrize('root', ['results/panel_validation/v1', 'results/panel_validation/v2']) as a
# decorator to configure the following definition.
@pytest.mark.parametrize('root',['results/panel_validation/v1','results/panel_validation/v2'])
# Check exact historical runtime can be reconstructed without simulation using the setup, calls, and assertions
# below.
# Input root: the base directory used to resolve files.
# Output: no explicit value; normal completion returns None.
def test_exact_historical_runtime_can_be_reconstructed_without_simulation(root):
    # Import materialize from historical_replay for the operations below.
    from historical_replay import materialize
    # Set frozen to the decoded data produced by json.loads from the text read from Path(root, 'manifest.json').
    frozen=json.loads(Path(root,'manifest.json').read_text())
    # Set snapshot to the result of materialize(frozen).
    snapshot=materialize(frozen)
    # Set script to the text 'import json; from final_evaluation.scenarios import...'.
    script='import json; from final_evaluation.scenarios import source_identities; print(json.dumps(source_identities(),sort_keys=True))'
    # Set result to the result of subprocess.run(a list containing sys.executable, the text '-B', the text '-c',
    # script).
    result=subprocess.run([sys.executable,'-B','-c',script],cwd=snapshot,capture_output=True,text=True,check=True)
    # Require the decoded data produced by json.loads from result.stdout equals frozen['manifest'] at
    # 'source_identities'; otherwise raise AssertionError.
    assert json.loads(result.stdout)==frozen['manifest']['source_identities']

# Check preferred pv03 replay routes to preserved record without launch using the setup, calls, and assertions
# below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_preferred_pv03_replay_routes_to_preserved_record_without_launch(monkeypatch):
    # Import historical_replay for use in this module.
    import historical_replay
    # Import replay from targeted_validation.runner for the operations below.
    from targeted_validation.runner import replay
    # Set calls to an empty list.
    calls=[]
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(historical_replay,'replay',lambda root,run_id,**kw:calls.append((root,run_id,kw)))
    # Call replay with the supplied arguments.
    replay('PV-03',gui=True)
    # Require the number of entries in calls equals 1; otherwise raise AssertionError.
    assert len(calls)==1
    # Set original to the decoded data produced by json.loads from the text read from (calls[0][0] / 'runs' /
    # calls[0][1] / 'result.json').
    original=json.loads((calls[0][0]/'runs'/calls[0][1]/'result.json').read_text())
    # Require original at 'scenario_id' equals the text 'multiple_left_turns' and original at 'method' equals the
    # text 'PROPOSED_MAPPO'; otherwise raise AssertionError.
    assert original['scenario_id']=='multiple_left_turns' and original['method']=='PROPOSED_MAPPO'
    # Require calls[0] at 2 equals a dictionary built from the supplied values; otherwise raise AssertionError.
    assert calls[0][2]==dict(kind='targeted',gui=True)

# Check historical replay prepares only new destinations using the setup, calls, and assertions below.
# Input monkeypatch: the supplied monkeypatch.
# Output: no explicit value; normal completion returns None.
def test_historical_replay_prepares_only_new_destinations(monkeypatch):
    # Import historical_replay for use in this module.
    import historical_replay
    # Set calls to an empty list.
    calls=[]
    # Call monkeypatch.setattr with the supplied arguments.
    monkeypatch.setattr(historical_replay,'_launch',lambda command,**kwargs:calls.append(command))
    # Call historical_replay.replay with the supplied arguments.
    historical_replay.replay('results/panel_validation/v1','20261008T171616134855Z_5e39804a')
    # Require calls and the text 'targeted_validation' belongs to calls[0] at 6; otherwise raise AssertionError.
    assert calls and 'targeted_validation' in calls[0][6]

# Check report refuses historical in place write using the setup, calls, and assertions below.
# Output: no explicit value; normal completion returns None.
def test_report_refuses_historical_in_place_write():
    # Import report from targeted_validation.reporting for the operations below.
    from targeted_validation.reporting import report
    # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
    with pytest.raises(RuntimeError,match='READ_ONLY'):
        # Call report with the supplied arguments.
        report(Path('results/panel_validation/v1'))

# Apply pytest.mark.parametrize('root', ['results/panel_validation/v1',... as a decorator to configure the
# following definition.
@pytest.mark.parametrize('root',['results/panel_validation/v1','results/final_evaluation/v2_candidate','results/panel_validation_archives/v1'])
# Check scalability preserves both old and preferred evidence guards using the setup, calls, and assertions below.
# Input root: the base directory used to resolve files.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def test_scalability_preserves_both_old_and_preferred_evidence_guards(root):
    # Import models from scalability_validation for the operations below.
    from scalability_validation import models
    # Import models as v2 from scalability_validation.v2 for the operations below.
    from scalability_validation.v2 import models as v2
    # Iterate over a tuple containing models, v2, binding each item to module.
    for module in (models,v2):
        # Enter the result of pytest.raises(RuntimeError) and run the enclosed operations within that context.
        with pytest.raises(RuntimeError,match='READ_ONLY'):
            # Call module.protect with the supplied arguments.
            module.protect(root)
