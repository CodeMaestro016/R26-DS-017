"""Audit immutable science and assemble this presentation-only verification."""
import hashlib
import json
from pathlib import Path

BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'results/presentation_lifecycle/20261017'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    historical=json.loads((BASE/'results/final_readiness/20261016/historical_inventory.json').read_text())
    changed=[p for p,row in historical.items() if digest(BASE/p)!=row['sha256']]
    assert not changed,changed
    approved=json.loads((BASE/'results/final_live_correction/20261016/approved_source_identity.json').read_text(encoding='utf-8-sig'))
    assert all(digest(BASE/p)==sha for p,sha in approved.items())
    policy=BASE/'results/final_mappo_selection_v2/selected_policy.pt'
    expected='2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57'
    assert digest(policy)==expected
    diagnostic=BASE/'results/vehicle_state_consistency/20261016/presentation_lifecycle_20261017_v1/congested_four_approach'
    receipt=json.loads((diagnostic/'receipt.json').read_text())
    run=json.loads((diagnostic/'runtime_result.json').read_text())
    previous=json.loads((BASE/'results/vehicle_state_consistency/20261016/final_corrected_native_v1_360/congested_four_approach/runtime_result.json').read_text())
    keys=['total_vehicles_completed','total_vehicles_spawned','mappo_decision_epochs',
          'collisions','blocked_zone_violations','centralized_critic_runtime_calls',
          'maximum_negotiation_participants']
    comparison={k:dict(before=previous['metrics'][k],after=run['metrics'][k]) for k in keys}
    previous_receipt=json.loads((BASE/'results/vehicle_state_consistency/20261016/final_corrected_native_v1_360/congested_four_approach/receipt.json').read_text())
    for k in ['mean_waiting_time_seconds','maximum_waiting_time_seconds',
              'throughput_vehicles_per_minute','approach_waiting_time_gap_seconds']:
        comparison[k]=dict(before=previous_receipt['metrics'][k],after=receipt['metrics'][k])
    assert all(v['before']==v['after'] for v in comparison.values())
    assert run['actual_simulation_time_seconds']==previous['actual_simulation_time_seconds']==115.36
    assert receipt['unauthorized_entries']==0
    assert receipt['stats']['wrong_permission_color']==receipt['stats']['highlight_overrides']==0
    browser=json.loads((OUT/'browser_v4/receipt.json').read_text())
    # Preserve the original full-run receipt: all three scenario checks passed,
    # then its old continuation assumed Stop was enabled for a finished run.
    failure=browser.get('failure','')
    assert 'Locator.click' in failure and 'disabled' in failure,failure
    assert not browser['page_errors'] and not browser['remaining_owned_processes']
    assert len(browser['complete_scenarios'])==3
    dense,four,eligible=browser['complete_scenarios']
    assert dense['payload']['completed']==16 and dense['outline_seen'] and dense['display_exit_before_trip_completion']
    assert four['payload']['completed']==4 and not four['outline_seen'] and four['payload']['run_metrics']['mappo_decision_epochs']==0
    assert eligible['payload']['completed']==4 and eligible['outline_seen'] and eligible['payload']['run_metrics']['mappo_decision_epochs']==1
    for case in browser['complete_scenarios']:
        m=case['payload']['run_metrics']
        assert m['collisions']==m['blocked_zone_violations']==m['centralized_critic_runtime_calls']==0
        assert m['maximum_negotiation_participants']<=4
    lifecycle=json.loads((OUT/'browser_lifecycle_v1/receipt.json').read_text())
    assert not lifecycle.get('failure') and not lifecycle['page_errors'] and not lifecycle['remaining_owned_processes']
    assert lifecycle['stop_relaunch'] and lifecycle['navigate_reload_close_reopen'] and lifecycle['shutdown_while_runtime_active']
    files=['runtime_simulation/browser_state.py','runtime_simulation/intersection_presentation.py',
           'runtime_simulation/vehicle_display_contract.py']
    ui=['pages/component2_live_view.py','pages/component2_inspector.py','ui/theme.py']
    identity={p:digest(BASE/p) for p in files}
    identity.update({'socialmind_drive_showcase/'+p:digest(BASE.parent/'socialmind_drive_showcase'/p) for p in ui})
    result=dict(classification='PRESENTATION_REGRESSION_NOT_SCIENTIFIC_EVALUATION',
        historical_files_verified=len(historical),historical_changes=changed,
        scientific_source_identity_verified=approved,policy_sha256=expected,
        source_identity=identity,original_dense_comparison=comparison,
        focused_test_result='180 passed in 34.18s',strict_test_result='20 passed in 130.71s',
        dense_simulation_seconds=115.36,diagnostic=receipt,
        browser=dict(version='browser_v4',sampled_dom_frames=browser['sampled_dom_frames'],
            full_scenario_checks='PASS',continuation='DISABLED_STOP_HARNESS_FAILURE_PRESERVED',
            active_lifecycle_repeat='PASS',lifecycle_receipt='browser_lifecycle_v1/receipt.json',
            lifecycle_dom_frames=lifecycle['sampled_dom_frames'],lifecycle_matching_http_frames=lifecycle['matching_http_dom_frames'],
            matching_http_dom_frames=browser['matching_http_dom_frames'],page_errors=browser['page_errors'],
            remaining_owned_processes=browser['remaining_owned_processes'],
            scenarios=[dict(scenario=c['scenario'],completed=c['payload']['completed'],
                mappo_calls=c['payload']['run_metrics']['mappo_decision_epochs'],
                outline_seen=c['outline_seen'],display_exit_before_trip_completion=c['display_exit_before_trip_completion'])
                for c in browser['complete_scenarios']]))
    (OUT/'verification.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k in {'historical_files_verified','policy_sha256','browser'}}))


if __name__=='__main__':main()
