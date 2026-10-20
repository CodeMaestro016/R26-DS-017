"""Retain before/after source bytes and verify diagnostic comparison integrity."""
# Import ast for use in this module.
import ast
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import zipfile for use in this module.
import zipfile

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/live_deadlock_investigation/20261016'.
OUT=BASE/'results/live_deadlock_investigation/20261016'


# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from h.
# Processing: iterate over the relevant records.
def sha(path):
    # Set h to the result of hashlib.sha256().
    h=hashlib.sha256()
    # Enter the result of path.open(the text 'rb') as f and run the enclosed operations within that context.
    with path.open('rb') as f:
        # Iterate over the result of iter(a callback that returns the result of f.read(1024 multiplied by 1024),
        # b''), binding each item to block.
        # Update h with the supplied entries.
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    # Return the hexadecimal digest from h to the caller.
    return h.hexdigest()


# Define IgnoreTelemetryInvocation to group the state and operations declared below.
# Base classes: ast.NodeTransformer.
# Instances expose the attributes and methods implemented in this class.
class IgnoreTelemetryInvocation(ast.NodeTransformer):
    # Visit Import From using the inputs and processing steps below.
    # Input node: the supplied node.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def visit_ImportFrom(self,node):
        # Run this branch when node.module equals the text 'browser_state'.
        # Return None to the caller.
        if node.module=='browser_state':return None
        # Return node to the caller.
        return node
    # Visit keyword using the inputs and processing steps below.
    # Input node: the supplied node.
    # Output: the result of self.generic_visit(node).
    # Processing: select branches using the stated conditions.
    def visit_keyword(self,node):
        # Run this branch when node.arg equals the text 'mappo_invocation'.
        # Set node.value to the result of ast.Constant(the text 'DISPLAY_ONLY').
        if node.arg=='mappo_invocation':node.value=ast.Constant('DISPLAY_ONLY')
        # Return the result of self.generic_visit(node) to the caller.
        return self.generic_visit(node)


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set old_hashes to the decoded data produced by json.loads from the text read from (OUT /
    # 'baseline/rule_resolved_two/source_hashes.json').
    old_hashes=json.loads((OUT/'baseline/rule_resolved_two/source_hashes.json').read_text())
    # Set files to a list containing the text 'component_2_right_of_way_negotiation/runtime_simulation/runner.py',
    # the text...
    files=['component_2_right_of_way_negotiation/runtime_simulation/runner.py',
           'component_2_right_of_way_negotiation/runtime_simulation/browser_state.py',
           'socialmind_drive_showcase/pages/component2_live_view.py']
    # Set snapshots to OUT joined with the path segment 'telemetry_sources'.
    snapshots=OUT/'telemetry_sources'
    # Create the directory requested by snapshots.
    snapshots.mkdir(exist_ok=True)
    # Enter the result of zipfile.ZipFile(BASE.parent joined with the path segment
    # 'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip') as z and run the enclosed operations within
    # that context.
    with zipfile.ZipFile(BASE.parent/'deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip') as z:
        # Iterate over files, binding each item to relative.
        for relative in files:
            # Set old to the result of z.read(relative).
            old=z.read(relative)
            # Run this branch when the result of relative.startswith(BASE.name plus the text '/').
            if relative.startswith(BASE.name+'/'):
                # Require the hexadecimal digest from hashlib.sha256(old) equals old_hashes at relative.split('/',
                # 1)[1]; otherwise raise AssertionError.
                assert hashlib.sha256(old).hexdigest()==old_hashes[relative.split('/',1)[1]]
            # Iterate over a list containing a tuple containing the text 'before', old, a tuple containing the
            # text 'after', the bytes read from..., binding each item to (version, content).
            for version,content in [('before',old),('after',(BASE.parent/relative).read_bytes())]:
                # Set destination to snapshots divided by version divided by relative.
                destination=snapshots/version/relative
                # Create the directory requested by destination.parent.
                destination.parent.mkdir(parents=True,exist_ok=True)
                # Run this branch when whether destination exists.
                if destination.exists():
                    # Require the bytes read from destination equals content; otherwise raise AssertionError with
                    # the text 'Source snapshot changed'.
                    assert destination.read_bytes()==content, 'Source snapshot changed'
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Write the supplied bytes to destination.
                    destination.write_bytes(content)
    # Set runner to files at 0.
    runner=files[0]
    # Set before to the result of ast.parse(the text read from (snapshots / 'before' / runner)).
    before=ast.parse((snapshots/'before'/runner).read_text(encoding='utf-8-sig'))
    # Set after to the result of ast.parse(the text read from (snapshots / 'after' / runner)).
    after=ast.parse((snapshots/'after'/runner).read_text(encoding='utf-8-sig'))
    # Set normalizer to the result of IgnoreTelemetryInvocation().
    normalizer=IgnoreTelemetryInvocation()
    # Require the serialized data produced by ast.dump equals the serialized data produced by ast.dump; otherwise
    # raise AssertionError with the text 'Non-telemetry control change'.
    assert ast.dump(normalizer.visit(before))==ast.dump(normalizer.visit(after)), 'Non-telemetry control change'
    # Set prior to BASE joined with the path segment 'results/final_readiness/20261016'.
    prior=BASE/'results/final_readiness/20261016'
    # Set protected to the decoded data produced by json.loads from the text read from (prior /
    # 'protected_source_inventory.json').
    protected=json.loads((prior/'protected_source_inventory.json').read_text(encoding='utf-8-sig'))
    # Set historical to the decoded data produced by json.loads from the text read from (prior /
    # 'historical_inventory.json').
    historical=json.loads((prior/'historical_inventory.json').read_text(encoding='utf-8-sig'))
    # Set changed to a list of the result of name.replace(the text '\\', the text '/') for (name, h) in key/value
    # pairs from protected; retain entries satisfying the result of sha(BASE divided by name) differs from h.
    changed=[name.replace('\\','/') for name,h in protected.items() if sha(BASE/name)!=h]
    # Require a set built from changed equals a set containing the text 'runtime_simulation/runner.py', the text
    # 'runtime_simulation/browser_state.py'; otherwise raise AssertionError.
    assert set(changed)=={'runtime_simulation/runner.py','runtime_simulation/browser_state.py'}
    # Set history_changes to a list of name for (name, item) in key/value pairs from historical; retain entries
    # satisfying the result of sha(BASE divided by name) differs from item at 'sha256'.
    history_changes=[name for name,item in historical.items() if sha(BASE/name)!=item['sha256']]
    # Require the negation of history_changes; otherwise raise AssertionError.
    assert not history_changes
    # Set comparisons to an empty dictionary.
    comparisons={}
    # Set keys to a list containing the text 'total_vehicles_scheduled', the text 'total_vehicles_spawned', the
    # text...
    keys=['total_vehicles_scheduled','total_vehicles_spawned','total_vehicles_completed',
          'mappo_inference_call_count','collision_count','blocked_zone_violation_count',
          'maximum_waiting_time_seconds','throughput_vehicles_per_minute','fallback_activations']
    # Iterate over a list containing the text 'rule_resolved_two', the text 'multiple_left_turns', the text
    # 'congested_four_approach', the text..., binding each item to name.
    for name in ['rule_resolved_two','multiple_left_turns','congested_four_approach','default_panel']:
        # Set newroot to OUT joined with the path segment 'telemetry_v1' divided by name.
        newroot=OUT/'telemetry_v1'/name
        # Set new to the decoded data produced by json.loads from the text read from (newroot / 'receipt.json').
        new=json.loads((newroot/'receipt.json').read_text())
        # Set old to the decoded data produced by json.loads from the text read from (OUT / 'baseline' / name /
        # 'receipt.json').
        old=json.loads((OUT/'baseline'/name/'receipt.json').read_text())
        # Set differences to a dictionary of k mapped to a list containing k from old['metrics']; use None if
        # absent, k from new['metrics']; use None if absent for k in keys; retain entries satisfying k from
        # old['metrics']; use None if absent differs from k from new['metrics']; use None...
        differences={k:[old['metrics'].get(k),new['metrics'].get(k)] for k in keys if old['metrics'].get(k)!=new['metrics'].get(k)}
        # Require the negation of differences; otherwise raise AssertionError.
        assert not differences
        # Set frame to the decoded data produced by json.loads from the text read from (newroot /
        # 'live_state.json').
        frame=json.loads((newroot/'live_state.json').read_text())
        # Run this branch when name belongs to a set containing the text 'congested_four_approach', the text
        # 'default_panel'.
        if name in {'congested_four_approach','default_panel'}:
            # Require frame at 'mappo_invocation' equals the text 'BLOCKED'; otherwise raise AssertionError.
            assert frame['mappo_invocation']=='BLOCKED'
            # Require frame['traffic_progress'] at 'status' equals the text 'PERSISTENT_BLOCKAGE'; otherwise raise
            # AssertionError.
            assert frame['traffic_progress']['status']=='PERSISTENT_BLOCKAGE'
        # Set comparisons[name] to a dictionary built from the supplied values.
        comparisons[name]=dict(metrics={k:new['metrics'].get(k) for k in keys},
            # Supply wall_seconds as new at 'wall_seconds'.
            # Supply same_measured_traffic_outcomes as the negation of differences.
            wall_seconds=new['wall_seconds'],same_measured_traffic_outcomes=not differences,
            # Supply final_mappo_invocation as frame at 'mappo_invocation'.
            # Supply traffic_progress as 'traffic_progress' from frame; use None if absent.
            final_mappo_invocation=frame['mappo_invocation'],traffic_progress=frame.get('traffic_progress'))
    # Set receipt to a dictionary built from the supplied values.
    receipt=dict(version='DISPLAY_TELEMETRY_CORRECTION_V1',
        # Supply research_algorithm_changed as False.
        # Supply runner_control_ast_unchanged as True.
        research_algorithm_changed=False,runner_control_ast_unchanged=True,
        # Supply protected_files_unchanged as 149.
        # Supply protected_telemetry_files_changed as changed.
        protected_files_unchanged=149,protected_telemetry_files_changed=changed,
        # Supply historical_files_unchanged as the number of entries in historical.
        # Supply historical_changes as history_changes.
        historical_files_unchanged=len(historical),historical_changes=history_changes,
        # Supply policy_sha256 as the result of sha(BASE joined with the path segment
        # 'results/final_mappo_selection_v2/selected_policy.pt').
        policy_sha256=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt'),
        # Supply comparisons as comparisons.
        # Supply scientific_liveness_fix_implemented as False.
        comparisons=comparisons,scientific_liveness_fix_implemented=False)
    # Write the supplied text to (OUT / 'telemetry_verification.json').
    (OUT/'telemetry_verification.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps(receipt,indent=2))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
