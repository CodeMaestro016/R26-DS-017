"""Audit immutable science and assemble this presentation-only verification."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/presentation_lifecycle/20261017'.
OUT=BASE/'results/presentation_lifecycle/20261017'


# Digest using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from hashlib.sha256(path.read_bytes()).
def digest(path):
    # Return the hexadecimal digest from hashlib.sha256(path.read_bytes()) to the caller.
    return hashlib.sha256(path.read_bytes()).hexdigest()


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def main():
    # Set historical to the decoded data produced by json.loads from the text read from (BASE /
    # 'results/final_readiness/20261016/historical_inventory.json').
    historical=json.loads((BASE/'results/final_readiness/20261016/historical_inventory.json').read_text())
    # Set changed to a list of p for (p, row) in key/value pairs from historical; retain entries satisfying the
    # result of digest(BASE divided by p) differs from row at 'sha256'.
    changed=[p for p,row in historical.items() if digest(BASE/p)!=row['sha256']]
    # Require the negation of changed; otherwise raise AssertionError with changed.
    assert not changed,changed
    # Set approved to the decoded data produced by json.loads from the text read from (BASE /
    # 'results/final_live_correction/20261016/approved_source_identity.json').
    approved=json.loads((BASE/'results/final_live_correction/20261016/approved_source_identity.json').read_text(encoding='utf-8-sig'))
    # Require whether every item is true in a lazy sequence of the result of digest(BASE / p) equals sha for (p,
    # sha) in key/value pairs from approved; otherwise raise AssertionError.
    assert all(digest(BASE/p)==sha for p,sha in approved.items())
    # Set policy to BASE joined with the path segment 'results/final_mappo_selection_v2/selected_policy.pt'.
    policy=BASE/'results/final_mappo_selection_v2/selected_policy.pt'
    # Set expected to the text '2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'.
    expected='2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'
    # Require the result of digest(policy) equals expected; otherwise raise AssertionError.
    assert digest(policy)==expected
    # Set diagnostic to BASE joined with the path segment
    # 'results/vehicle_state_consistency/20261016/presentation_lifecy...'.
    diagnostic=BASE/'results/vehicle_state_consistency/20261016/presentation_lifecycle_20261017_v1/congested_four_approach'
    # Set receipt to the decoded data produced by json.loads from the text read from (diagnostic /
    # 'receipt.json').
    receipt=json.loads((diagnostic/'receipt.json').read_text())
    # Set run to the decoded data produced by json.loads from the text read from (diagnostic /
    # 'runtime_result.json').
    run=json.loads((diagnostic/'runtime_result.json').read_text())
    # Set previous to the decoded data produced by json.loads from the result of (BASE /...().
    previous=json.loads((BASE/'results/vehicle_state_consistency/20261016/final_corrected_native_v1_360/congested_four_approach/runtime_result.json').read_text())
    # Set keys to a list containing the text 'total_vehicles_completed', the text 'total_vehicles_spawned', the
    # text 'mappo_decision_epochs',...
    keys=['total_vehicles_completed','total_vehicles_spawned','mappo_decision_epochs',
          'collisions','blocked_zone_violations','centralized_critic_runtime_calls',
          'maximum_negotiation_participants']
    # Set comparison to a dictionary of k mapped to a dictionary built from the supplied values for k in keys.
    comparison={k:dict(before=previous['metrics'][k],after=run['metrics'][k]) for k in keys}
    # Set previous_receipt to the decoded data produced by json.loads from the result of (BASE /...().
    previous_receipt=json.loads((BASE/'results/vehicle_state_consistency/20261016/final_corrected_native_v1_360/congested_four_approach/receipt.json').read_text())
    # Iterate over a list containing the text 'mean_waiting_time_seconds', the text
    # 'maximum_waiting_time_seconds', the text..., binding each item to k.
    for k in ['mean_waiting_time_seconds','maximum_waiting_time_seconds',
              'throughput_vehicles_per_minute','approach_waiting_time_gap_seconds']:
        # Set comparison[k] to a dictionary built from the supplied values.
        comparison[k]=dict(before=previous_receipt['metrics'][k],after=receipt['metrics'][k])
    # Require whether every item is true in a lazy sequence of v at 'before' equals v at 'after' for v in values
    # from comparison; otherwise raise AssertionError.
    assert all(v['before']==v['after'] for v in comparison.values())
    # Require run at 'actual_simulation_time_seconds' equals previous at 'actual_simulation_time_seconds'; equals
    # 115.36; otherwise raise AssertionError.
    assert run['actual_simulation_time_seconds']==previous['actual_simulation_time_seconds']==115.36
    # Require receipt at 'unauthorized_entries' equals 0; otherwise raise AssertionError.
    assert receipt['unauthorized_entries']==0
    # Require receipt['stats'] at 'wrong_permission_color' equals receipt['stats'] at 'highlight_overrides';
    # equals 0; otherwise raise AssertionError.
    assert receipt['stats']['wrong_permission_color']==receipt['stats']['highlight_overrides']==0
    # Set browser to the decoded data produced by json.loads from the text read from (OUT /
    # 'browser_v4/receipt.json').
    browser=json.loads((OUT/'browser_v4/receipt.json').read_text())
    # Preserve the original full-run receipt: all three scenario checks passed,
    # then its old continuation assumed Stop was enabled for a finished run.
    # Set failure to 'failure' from browser; use the text '' if absent.
    failure=browser.get('failure','')
    # Require the text 'Locator.click' belongs to failure and the text 'disabled' belongs to failure; otherwise
    # raise AssertionError with failure.
    assert 'Locator.click' in failure and 'disabled' in failure,failure
    # Require the negation of browser at 'page_errors' and the negation of browser at 'remaining_owned_processes';
    # otherwise raise AssertionError.
    assert not browser['page_errors'] and not browser['remaining_owned_processes']
    # Require the number of entries in browser at 'complete_scenarios' equals 3; otherwise raise AssertionError.
    assert len(browser['complete_scenarios'])==3
    # Set (dense, four, eligible) to browser at 'complete_scenarios'.
    dense,four,eligible=browser['complete_scenarios']
    # Require dense['payload'] at 'completed' equals 16 and dense at 'outline_seen' and dense at
    # 'display_exit_before_trip_completion'; otherwise raise AssertionError.
    assert dense['payload']['completed']==16 and dense['outline_seen'] and dense['display_exit_before_trip_completion']
    # Require four['payload'] at 'completed' equals 4 and the negation of four at 'outline_seen' and
    # four['payload']['run_metrics'] at 'mappo_decision_epochs' equals 0; otherwise raise AssertionError.
    assert four['payload']['completed']==4 and not four['outline_seen'] and four['payload']['run_metrics']['mappo_decision_epochs']==0
    # Require eligible['payload'] at 'completed' equals 4 and eligible at 'outline_seen' and
    # eligible['payload']['run_metrics'] at 'mappo_decision_epochs' equals 1; otherwise raise AssertionError.
    assert eligible['payload']['completed']==4 and eligible['outline_seen'] and eligible['payload']['run_metrics']['mappo_decision_epochs']==1
    # Iterate over browser at 'complete_scenarios', binding each item to case.
    for case in browser['complete_scenarios']:
        # Set m to case['payload'] at 'run_metrics'.
        m=case['payload']['run_metrics']
        # Require m at 'collisions' equals m at 'blocked_zone_violations'; equals m at
        # 'centralized_critic_runtime_calls'; equals 0; otherwise raise AssertionError.
        assert m['collisions']==m['blocked_zone_violations']==m['centralized_critic_runtime_calls']==0
        # Require m at 'maximum_negotiation_participants' is at most 4; otherwise raise AssertionError.
        assert m['maximum_negotiation_participants']<=4
    # Set lifecycle to the decoded data produced by json.loads from the text read from (OUT /
    # 'browser_lifecycle_v1/receipt.json').
    lifecycle=json.loads((OUT/'browser_lifecycle_v1/receipt.json').read_text())
    # Require the negation of 'failure' from lifecycle; use None if absent and the negation of lifecycle at
    # 'page_errors' and the negation of lifecycle at 'remaining_owned_processes'; otherwise raise AssertionError.
    assert not lifecycle.get('failure') and not lifecycle['page_errors'] and not lifecycle['remaining_owned_processes']
    # Require lifecycle at 'stop_relaunch' and lifecycle at 'navigate_reload_close_reopen' and lifecycle at
    # 'shutdown_while_runtime_active'; otherwise raise AssertionError.
    assert lifecycle['stop_relaunch'] and lifecycle['navigate_reload_close_reopen'] and lifecycle['shutdown_while_runtime_active']
    # Set files to a list containing the text 'runtime_simulation/browser_state.py', the text...
    files=['runtime_simulation/browser_state.py','runtime_simulation/intersection_presentation.py',
           'runtime_simulation/vehicle_display_contract.py']
    # Set ui to a list containing the text 'pages/component2_live_view.py', the text
    # 'pages/component2_inspector.py', the text 'ui/theme.py'.
    ui=['pages/component2_live_view.py','pages/component2_inspector.py','ui/theme.py']
    # Set identity to a dictionary of p mapped to the result of digest(BASE divided by p) for p in files.
    identity={p:digest(BASE/p) for p in files}
    # Update identity with the supplied entries.
    identity.update({'socialmind_drive_showcase/'+p:digest(BASE.parent/'socialmind_drive_showcase'/p) for p in ui})
    # Set result to a dictionary built from the supplied values.
    result=dict(classification='PRESENTATION_REGRESSION_NOT_SCIENTIFIC_EVALUATION',
        # Supply historical_files_verified as the number of entries in historical.
        # Supply historical_changes as changed.
        historical_files_verified=len(historical),historical_changes=changed,
        # Supply scientific_source_identity_verified as approved.
        # Supply policy_sha256 as expected.
        scientific_source_identity_verified=approved,policy_sha256=expected,
        # Supply source_identity as identity.
        # Supply original_dense_comparison as comparison.
        source_identity=identity,original_dense_comparison=comparison,
        # Supply focused_test_result as the text '180 passed in 34.18s'.
        # Supply strict_test_result as the text '20 passed in 130.71s'.
        focused_test_result='180 passed in 34.18s',strict_test_result='20 passed in 130.71s',
        # Supply dense_simulation_seconds as 115.36.
        # Supply diagnostic as receipt.
        dense_simulation_seconds=115.36,diagnostic=receipt,
        # Supply browser as a dictionary built from the supplied values.
        # Supply version as the text 'browser_v4'.
        # Supply sampled_dom_frames as browser at 'sampled_dom_frames'.
        browser=dict(version='browser_v4',sampled_dom_frames=browser['sampled_dom_frames'],
            # Supply full_scenario_checks as the text 'PASS'.
            # Supply continuation as the text 'DISABLED_STOP_HARNESS_FAILURE_PRESERVED'.
            full_scenario_checks='PASS',continuation='DISABLED_STOP_HARNESS_FAILURE_PRESERVED',
            # Supply active_lifecycle_repeat as the text 'PASS'.
            # Supply lifecycle_receipt as the text 'browser_lifecycle_v1/receipt.json'.
            active_lifecycle_repeat='PASS',lifecycle_receipt='browser_lifecycle_v1/receipt.json',
            # Supply lifecycle_dom_frames as lifecycle at 'sampled_dom_frames'.
            # Supply lifecycle_matching_http_frames as lifecycle at 'matching_http_dom_frames'.
            lifecycle_dom_frames=lifecycle['sampled_dom_frames'],lifecycle_matching_http_frames=lifecycle['matching_http_dom_frames'],
            # Supply matching_http_dom_frames as browser at 'matching_http_dom_frames'.
            # Supply page_errors as browser at 'page_errors'.
            matching_http_dom_frames=browser['matching_http_dom_frames'],page_errors=browser['page_errors'],
            # Supply remaining_owned_processes as browser at 'remaining_owned_processes'.
            remaining_owned_processes=browser['remaining_owned_processes'],
            # Supply scenarios as a list of a dictionary built from the supplied values for c in browser at
            # 'complete_scenarios'.
            # Supply scenario as c at 'scenario'.
            # Supply completed as c['payload'] at 'completed'.
            scenarios=[dict(scenario=c['scenario'],completed=c['payload']['completed'],
                # Supply mappo_calls as c['payload']['run_metrics'] at 'mappo_decision_epochs'.
                mappo_calls=c['payload']['run_metrics']['mappo_decision_epochs'],
                # Supply outline_seen as c at 'outline_seen'.
                # Supply display_exit_before_trip_completion as c at 'display_exit_before_trip_completion'.
                outline_seen=c['outline_seen'],display_exit_before_trip_completion=c['display_exit_before_trip_completion'])
                # Evaluate browser at 'complete_scenarios' as part of the enclosing expression.
                for c in browser['complete_scenarios']]))
    # Write the supplied text to (OUT / 'verification.json').
    (OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    # Display the serialized data produced by json.dumps.
    print(json.dumps({k:v for k,v in result.items() if k in {'historical_files_verified','policy_sha256','browser'}}))


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
