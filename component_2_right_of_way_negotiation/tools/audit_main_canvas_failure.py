"""Final audit for main-canvas integration; historical receipts stay untouched."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Read using the inputs and processing steps below.
# Input p: the supplied p.
# Output: the decoded data produced by json.loads from the text read from p.
# Return the decoded data produced by json.loads from the text read from p to the caller.
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
# Sha using the inputs and processing steps below.
# Input p: the supplied p.
# Output: the hexadecimal digest from hashlib.sha256(p.read_bytes()).
# Return the hexadecimal digest from hashlib.sha256(p.read_bytes()) to the caller.
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set root to BASE joined with the path segment 'results/offline_counterfactual'.
    # Set out to root joined with the path segment 'main_canvas_v2'.
    root=BASE/'results/offline_counterfactual';out=root/'main_canvas_v2'
    # Set history to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/historical_inventory.json').
    history=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v at 'sha256'
    # for (p, v) in key/value pairs from history; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v['sha256'] for p,v in history.items())
    # Set protected to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/approved_source_identity.json').
    protected=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals v for (p, v) in
    # key/value pairs from protected; otherwise raise AssertionError.
    assert all(sha(BASE/p)==v for p,v in protected.items())
    # Set native to the result of read(root joined with the path segment 'v1/receipt.json').
    native=read(root/'v1/receipt.json')
    # Require the result of sha(root joined with the path segment 'v1/replay.json') equals native at 'replay_sha256';
    # otherwise raise AssertionError.
    assert sha(root/'v1/replay.json')==native['replay_sha256']
    # Set geometry to the result of read(root joined with the path segment
    # 'central_presentation_v1/geometry_integrity_audit.json').
    geometry=read(root/'central_presentation_v1/geometry_integrity_audit.json')
    # Set policy to the result of sha(BASE joined with the path segment
    # 'results/final_mappo_selection_v2/selected_policy.pt').
    policy=sha(BASE/'results/final_mappo_selection_v2/selected_policy.pt')
    # Require policy equals geometry at 'selected_e5_policy_sha256'; otherwise raise AssertionError.
    assert policy==geometry['selected_e5_policy_sha256']
    # Iterate over a list containing the text 'main_canvas_v1', the text 'main_canvas_v2', binding each item to
    # name.
    for name in ['main_canvas_v1','main_canvas_v2']:
        # Set browser to the result of read(root divided by name joined with the path segment 'receipt.json').
        browser=read(root/name/'receipt.json')
        # Require browser at 'status' equals the text 'PASS' and the negation of browser at 'page_errors';
        # otherwise raise AssertionError.
        assert browser['status']=='PASS' and not browser['page_errors']
        # Require browser at 'no_modal_or_navigation' and browser at 'same_main_canvas'; otherwise raise
        # AssertionError.
        assert browser['no_modal_or_navigation'] and browser['same_main_canvas']
    # Set science to an empty dictionary.
    science={}
    # Iterate over a list containing a tuple containing the text 'scenario2', 4, a tuple containing the text
    # 'scenario4', 16, binding each item to (name, expected).
    for name,expected in [('scenario2',4),('scenario4',16)]:
        # Set terminal to the result of read(root joined with the path segment 'main_canvas_v1' divided by formatted text
        # built from the embedded values).
        terminal=read(root/'main_canvas_v1'/f'{name}_terminal.json')
        # Set metrics to terminal at 'run_metrics'.
        metrics=terminal['run_metrics']
        # Require metrics at 'total_vehicles_completed' equals expected and metrics at 'collisions' equals 0;
        # otherwise raise AssertionError.
        assert metrics['total_vehicles_completed']==expected and metrics['collisions']==0
        # Require metrics at 'centralized_critic_runtime_calls' equals 0 and metrics at 'mappo_decision_epochs' is
        # greater than 0; otherwise raise AssertionError.
        assert metrics['centralized_critic_runtime_calls']==0 and metrics['mappo_decision_epochs']>0
        # Set science[name] to a dictionary built from the supplied values.
        science[name]=dict(simulation_time=terminal['simulation_time'],metrics=metrics)
    # Set result to a dictionary built from the supplied values.
    result=dict(historical_files_unchanged=len(history),protected_source_identities_unchanged=protected,
        # Supply checkpoint_sha256 as policy.
        # Supply raw_replay_sha256 as native at 'replay_sha256'.
        # Supply new_unsafe_experiment as False.
        checkpoint_sha256=policy,raw_replay_sha256=native['replay_sha256'],new_unsafe_experiment=False,
        # Supply collision_distance_from_junction_center_m as geometry at 'distance_from_junction_center_m'.
        collision_distance_from_junction_center_m=geometry['distance_from_junction_center_m'],
        # Supply collision_body_overlap_m2 as geometry at 'body_overlap_m2'.
        # Supply browser_status as the text 'PASS'.
        # Supply scientific_runs as science.
        collision_body_overlap_m2=geometry['body_overlap_m2'],browser_status='PASS',scientific_runs=science,
        # Supply website_source_hashes as a dictionary of p mapped to the result of sha(BASE.parent divided by
        # 'socialmind_drive_showcase' divided by p) for p in a list containing the text
        # 'pages/component2_live_view.py', the text 'pages/component2_inspector.py', the text...
        website_source_hashes={p:sha(BASE.parent/'socialmind_drive_showcase'/p) for p in ['pages/component2_live_view.py','pages/component2_inspector.py','services/main_canvas_replay.py','ui/theme.py']})
    # Write the supplied text to (out / 'verification.json').
    (out/'verification.json').write_text(json.dumps(result,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in result.items() if k not in ['scientific_runs','website_source_hashes','protected_source_identities_unchanged']}))

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
