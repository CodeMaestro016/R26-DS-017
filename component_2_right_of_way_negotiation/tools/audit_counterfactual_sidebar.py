"""Audit new isolated evidence against retained protected/historical results."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import xml.etree.ElementTree as ET for use in this module.
import xml.etree.ElementTree as ET

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/offline_counterfactual/v1'.
OUT=BASE/'results/offline_counterfactual/v1'
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
    # Set historic to the result of read(BASE joined with the path segment
    # 'results/final_readiness/20261016/historical_inventory.json').
    historic=read(BASE/'results/final_readiness/20261016/historical_inventory.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals value at
    # 'sha256' for (p, value) in key/value pairs from historic; otherwise raise AssertionError.
    assert all(sha(BASE/p)==value['sha256'] for p,value in historic.items())
    # Set approved to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/approved_source_identity.json').
    approved=read(BASE/'results/final_demonstrations/v1/approved_source_identity.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals value for (p,
    # value) in key/value pairs from approved; otherwise raise AssertionError.
    assert all(sha(BASE/p)==value for p,value in approved.items())
    # Set previous to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/after_v1/final_coordination_fa...').
    previous=read(BASE/'results/final_demonstrations/v1/after_v1/final_coordination_failure__proposed/runtime_result.json')
    # Set current to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/sidebar_counterfactual_protect...').
    current=read(BASE/'results/final_demonstrations/v1/sidebar_counterfactual_protected_v1/final_coordination_failure__proposed/runtime_result.json')
    # Iterate over a list containing the text 'presentation_schedule', the text 'scheduled_departure_seconds', the
    # text..., binding each item to key.
    for key in ['presentation_schedule','scheduled_departure_seconds','actual_departure_seconds','metrics','actual_simulation_time_seconds','policy_sha256_after']:
        # Require previous at key equals current at key; otherwise raise AssertionError with key.
        assert previous[key]==current[key],key
    # Set comparison to the result of read(BASE joined with the path segment
    # 'results/final_demonstrations/v1/comparison.json').
    comparison=read(BASE/'results/final_demonstrations/v1/comparison.json')
    # Set (primary, rules) to comparison at 'modes'.
    # Require primary at 'completed' equals 6 and rules at 'completed' equals 1; otherwise raise AssertionError.
    primary,rules=comparison['modes'];assert primary['completed']==6 and rules['completed']==1
    # Require primary at 'collisions' equals rules at 'collisions'; equals 0; otherwise raise AssertionError.
    assert primary['collisions']==rules['collisions']==0
    # Set native to the result of read(OUT joined with the path segment 'receipt.json').
    # Set manifest to the result of read(OUT joined with the path segment 'manifest.json').
    native=read(OUT/'receipt.json');manifest=read(OUT/'manifest.json')
    # Require native at 'departure_times' equals current at 'actual_departure_seconds'; otherwise raise
    # AssertionError.
    assert native['departure_times']==current['actual_departure_seconds']
    # Require native at 'replay_sha256' equals the result of sha(OUT joined with the path segment 'replay.json'); otherwise
    # raise AssertionError.
    assert native['replay_sha256']==sha(OUT/'replay.json')
    # Require native at 'manifest_sha256' equals the result of sha(OUT joined with the path segment 'manifest.json');
    # otherwise raise AssertionError.
    assert native['manifest_sha256']==sha(OUT/'manifest.json')
    # Require whether every item is true in a lazy sequence of the result of sha(BASE / p) equals value for (p,
    # value) in key/value pairs from manifest['assets']; otherwise raise AssertionError.
    assert all(sha(BASE/p)==value for p,value in manifest['assets'].items())
    # Set collisions to the result of ET.parse(OUT / 'sumo_collisions.xml').getroot().findall(the text
    # 'collision').
    collisions=ET.parse(OUT/'sumo_collisions.xml').getroot().findall('collision')
    # Require the number of entries in collisions equals native at 'collision_count'; equals 1; otherwise raise
    # AssertionError.
    assert len(collisions)==native['collision_count']==1
    # Set collision to a dictionary built from native['collision_events'] at 0.
    collision=dict(native['collision_events'][0],sumo_event_time=float(collisions[0].get('time')))
    # Set browser to the result of read(OUT joined with the path segment 'browser_scroll_v7/receipt.json').
    browser=read(OUT/'browser_scroll_v7/receipt.json')
    # Require the negation of 'failure' from browser; use None if absent and the negation of browser at
    # 'page_errors' and the negation of browser at 'remaining_owned_processes'; otherwise raise AssertionError.
    assert not browser.get('failure') and not browser['page_errors'] and not browser['remaining_owned_processes']
    # Require the number of entries in browser at 'scroll_checks' equals 5 and browser at 'headed'; otherwise
    # raise AssertionError.
    assert len(browser['scroll_checks'])==5 and browser['headed']
    # Require browser['independent_right_panel_scroll'] at 'after' is greater than
    # browser['independent_right_panel_scroll']['before'] at 'top'; otherwise raise AssertionError.
    assert browser['independent_right_panel_scroll']['after']>browser['independent_right_panel_scroll']['before']['top']
    # Iterate over browser at 'scroll_checks', binding each item to row.
    for row in browser['scroll_checks']:
        # Require row['after_updates'] at 'stable'; otherwise raise AssertionError.
        assert row['after_updates']['stable']
        # Require the absolute value of row['after_updates'] at 'top' minus row['bottom'] at 'top' is at most 2;
        # otherwise raise AssertionError.
        assert abs(row['after_updates']['top']-row['bottom']['top'])<=2
        # Require row['dragged'] at 'top' is greater than row['incremental'] at 'top' plus 20; otherwise raise
        # AssertionError.
        assert row['dragged']['top']>row['incremental']['top']+20
    # Set source_paths to a list containing the text 'offline_counterfactual/run.py', the text
    # 'offline_counterfactual/protocol.json'.
    source_paths=['offline_counterfactual/run.py','offline_counterfactual/protocol.json']
    # Set source to a dictionary of p mapped to the result of sha(BASE divided by p) for p in source_paths.
    source={p:sha(BASE/p) for p in source_paths}
    # Iterate over a list containing the text 'app.py', the text 'pages/component2_live_view.py', the text
    # 'pages/counterfactual_replay.py',..., binding each item to p.
    for p in ['app.py','pages/component2_live_view.py','pages/counterfactual_replay.py','services/counterfactual_reader.py','ui/theme.py']:
        # Set source['socialmind_drive_showcase/' + p] to the result of sha(BASE.parent joined with the path segment
        # 'socialmind_drive_showcase' divided by p).
        source['socialmind_drive_showcase/'+p]=sha(BASE.parent/'socialmind_drive_showcase'/p)
    # Set result to a dictionary built from the supplied values.
    result=dict(classification='EDUCATIONAL_COUNTERFACTUAL_AND_PRESENTATION_VERIFICATION',
        # Supply historical_files_unchanged as the number of entries in historic.
        # Supply protected_source_identity_unchanged as approved.
        historical_files_unchanged=len(historic),protected_source_identity_unchanged=approved,
        # Supply protected_metrics_identical as True.
        # Supply protected_completed as 6.
        # Supply rules_only_preserved_completed as 1.
        protected_metrics_identical=True,protected_completed=6,rules_only_preserved_completed=1,
        # Supply policy_sha256 as current at 'policy_sha256_after'.
        # Supply counterfactual as native.
        policy_sha256=current['policy_sha256_after'],counterfactual=native,
        # Supply actual_collision as collision.
        # Supply source_identity as source.
        actual_collision=collision,source_identity=source,
        # Supply browser as a dictionary built from the supplied values.
        # Supply status as the text 'PASS'.
        # Supply receipt as the text 'browser_scroll_v7/receipt.json'.
        # Supply viewports as a list containing the text '1600x1000', the text '1280x720'.
        browser=dict(status='PASS',receipt='browser_scroll_v7/receipt.json',viewports=['1600x1000','1280x720'],
            # Supply scroll_checks as 5.
            # Supply retention_during_repeated_updates as True.
            # Supply native_scrollbar_drag_verified as True.
            scroll_checks=5,retention_during_repeated_updates=True,native_scrollbar_drag_verified=True,
            # Supply page_errors as an empty list.
            # Supply remaining_owned_processes as an empty list.
            # Supply shutdown_timeout as 'shutdown_timeout' from browser; use False if absent.
            page_errors=[],remaining_owned_processes=[],shutdown_timeout=browser.get('shutdown_timeout',False)))
    # Write the supplied text to (OUT / 'verification.json').
    (OUT/'verification.json').write_text(json.dumps(result,indent=2))
    # Display the serialized data produced by json.dumps.
    print(json.dumps(dict(historical_files_unchanged=len(historic),protected_completed=6,
        # Supply collisions as native at 'collision_count'.
        # Supply event_time as collision at 'sumo_event_time'.
        # Supply browser as result at 'browser'.
        collisions=native['collision_count'],event_time=collision['sumo_event_time'],browser=result['browser'])))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
