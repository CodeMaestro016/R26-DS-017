"""Verify preserved science and serialize compact observed diagnostic metrics."""
import hashlib
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'results/live_deadlock_investigation/20261016'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda:f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    prior = BASE / 'results/final_readiness/20261016'
    protected = json.loads((prior/'protected_source_inventory.json').read_text(encoding='utf-8-sig'))
    historical = json.loads((prior/'historical_inventory.json').read_text(encoding='utf-8-sig'))
    source_changes = [name for name, h in protected.items() if sha(BASE/name) != h]
    historical_changes = [name for name, item in historical.items() if sha(BASE/name) != item['sha256']]
    summaries = {}
    for directory in (OUT/'baseline').iterdir():
        if not (directory/'receipt.json').exists():
            continue
        r = json.loads((directory/'receipt.json').read_text())
        result = json.loads((directory/'runtime_result.json').read_text())
        m = r['metrics']
        stationary_start = None
        first_persistent_stop = None
        final_physical = None
        first_physical = None
        for line in (directory/'timeline.jsonl').read_text(encoding='utf-8').splitlines():
            event = json.loads(line)
            if event['event'] != 'PHYSICAL_STATE':
                continue
            states = event['states']
            sample = dict(timestamp=event['timestamp'], active=len(states),
                moving=sum(s['speed']>0 for s in states.values()))
            first_physical = first_physical or sample
            final_physical = sample
            if states and all(s['speed']==0 for s in states.values()):
                stationary_start = stationary_start if stationary_start is not None else event['timestamp']
                if first_persistent_stop is None and event['timestamp']-stationary_start>=15:
                    first_persistent_stop=dict(start_sample=stationary_start, confirmed_sample=event['timestamp'])
            else:
                stationary_start = None
        summaries[directory.name] = dict(wall_seconds=r['wall_seconds'],
            run_status=result['run_status'], simulation_seconds=result['actual_simulation_time_seconds'],
            first_physical=first_physical, final_physical=final_physical,
            sampled_persistent_all_stationary=first_persistent_stop,
            policy_sha256=result['policy_sha256_after'], decentralized=result['decentralized_execution'],
            critic_calls=result['centralized_critic_calls'], metrics=m)
    receipt = dict(protected_verified=len(protected), protected_changes=source_changes,
        historical_verified=len(historical), historical_changes=historical_changes,
        runs=summaries, scientific_runtime_changed=False, research_design_approval_required=True)
    (OUT/'verification.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    assert not source_changes and not historical_changes
    print(json.dumps(dict(protected_verified=len(protected), historical_verified=len(historical),
        changes=0, runs={k:{a:b for a,b in v.items() if a!='metrics'} for k,v in summaries.items()}), indent=2))


if __name__ == '__main__':
    main()
