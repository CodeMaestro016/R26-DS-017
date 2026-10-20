"""Verify preserved science and serialize compact observed diagnostic metrics."""
# Import hashlib for use in this module.
import hashlib
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE = Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/live_deadlock_investigation/20261016'.
OUT = BASE / 'results/live_deadlock_investigation/20261016'


# Sha using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the hexadecimal digest from h.
# Processing: iterate over the relevant records.
def sha(path):
    # Set h to the result of hashlib.sha256().
    h = hashlib.sha256()
    # Enter the result of path.open(the text 'rb') as f and run the enclosed operations within that context.
    with path.open('rb') as f:
        # Iterate over the result of iter(a callback that returns the result of f.read(1024 multiplied by 1024),
        # b''), binding each item to block.
        for block in iter(lambda:f.read(1024*1024), b''):
            # Update h with the supplied entries.
            h.update(block)
    # Return the hexadecimal digest from h to the caller.
    return h.hexdigest()


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set prior to BASE joined with the path segment 'results/final_readiness/20261016'.
    prior = BASE / 'results/final_readiness/20261016'
    # Set protected to the decoded data produced by json.loads from the text read from (prior /
    # 'protected_source_inventory.json').
    protected = json.loads((prior/'protected_source_inventory.json').read_text(encoding='utf-8-sig'))
    # Set historical to the decoded data produced by json.loads from the text read from (prior /
    # 'historical_inventory.json').
    historical = json.loads((prior/'historical_inventory.json').read_text(encoding='utf-8-sig'))
    # Set source_changes to a list of name for (name, h) in key/value pairs from protected; retain entries
    # satisfying the result of sha(BASE divided by name) differs from h.
    source_changes = [name for name, h in protected.items() if sha(BASE/name) != h]
    # Set historical_changes to a list of name for (name, item) in key/value pairs from historical; retain entries
    # satisfying the result of sha(BASE divided by name) differs from item at 'sha256'.
    historical_changes = [name for name, item in historical.items() if sha(BASE/name) != item['sha256']]
    # Set summaries to an empty dictionary.
    summaries = {}
    # Iterate over the result of (OUT / 'baseline').iterdir(), binding each item to directory.
    for directory in (OUT/'baseline').iterdir():
        # Run this branch when the negation of whether (directory / 'receipt.json') exists.
        if not (directory/'receipt.json').exists():
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set r to the decoded data produced by json.loads from the text read from (directory / 'receipt.json').
        r = json.loads((directory/'receipt.json').read_text())
        # Set result to the decoded data produced by json.loads from the text read from (directory /
        # 'runtime_result.json').
        result = json.loads((directory/'runtime_result.json').read_text())
        # Set m to r at 'metrics'.
        m = r['metrics']
        # Set stationary_start to None.
        stationary_start = None
        # Set first_persistent_stop to None.
        first_persistent_stop = None
        # Set final_physical to None.
        final_physical = None
        # Set first_physical to None.
        first_physical = None
        # Iterate over the result of (directory / 'timeline.jsonl').read_text(encoding='utf-8').splitlines(),
        # binding each item to line.
        for line in (directory/'timeline.jsonl').read_text(encoding='utf-8').splitlines():
            # Set event to the decoded data produced by json.loads from line.
            event = json.loads(line)
            # Run this branch when event at 'event' differs from the text 'PHYSICAL_STATE'.
            if event['event'] != 'PHYSICAL_STATE':
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set states to event at 'states'.
            states = event['states']
            # Set sample to a dictionary built from the supplied values.
            sample = dict(timestamp=event['timestamp'], active=len(states),
                # Supply moving as the sum of a lazy sequence of s at 'speed' is greater than 0 for s in values
                # from states.
                moving=sum(s['speed']>0 for s in states.values()))
            # Set first_physical to first_physical or sample.
            first_physical = first_physical or sample
            # Set final_physical to sample.
            final_physical = sample
            # Run this branch when states and whether every item is true in a lazy sequence of s['speed'] equals 0
            # for s in values from states.
            if states and all(s['speed']==0 for s in states.values()):
                # Set stationary_start to stationary_start when stationary_start is a different object from None,
                # otherwise event at 'timestamp'.
                stationary_start = stationary_start if stationary_start is not None else event['timestamp']
                # Run this branch when first_persistent_stop is the same object as None and event at 'timestamp'
                # minus stationary_start is at least 15.
                if first_persistent_stop is None and event['timestamp']-stationary_start>=15:
                    # Set first_persistent_stop to a dictionary built from the supplied values.
                    first_persistent_stop=dict(start_sample=stationary_start, confirmed_sample=event['timestamp'])
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set stationary_start to None.
                stationary_start = None
        # Set summaries[directory.name] to a dictionary built from the supplied values.
        summaries[directory.name] = dict(wall_seconds=r['wall_seconds'],
            # Supply run_status as result at 'run_status'.
            # Supply simulation_seconds as result at 'actual_simulation_time_seconds'.
            run_status=result['run_status'], simulation_seconds=result['actual_simulation_time_seconds'],
            # Supply first_physical as first_physical.
            # Supply final_physical as final_physical.
            first_physical=first_physical, final_physical=final_physical,
            # Supply sampled_persistent_all_stationary as first_persistent_stop.
            sampled_persistent_all_stationary=first_persistent_stop,
            # Supply policy_sha256 as result at 'policy_sha256_after'.
            # Supply decentralized as result at 'decentralized_execution'.
            policy_sha256=result['policy_sha256_after'], decentralized=result['decentralized_execution'],
            # Supply critic_calls as result at 'centralized_critic_calls'.
            # Supply metrics as m.
            critic_calls=result['centralized_critic_calls'], metrics=m)
    # Set receipt to a dictionary built from the supplied values.
    receipt = dict(protected_verified=len(protected), protected_changes=source_changes,
        # Supply historical_verified as the number of entries in historical.
        # Supply historical_changes as historical_changes.
        historical_verified=len(historical), historical_changes=historical_changes,
        # Supply runs as summaries.
        # Supply scientific_runtime_changed as False.
        # Supply research_design_approval_required as True.
        runs=summaries, scientific_runtime_changed=False, research_design_approval_required=True)
    # Write the supplied text to (OUT / 'verification.json').
    (OUT/'verification.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    # Require the negation of source_changes and the negation of historical_changes; otherwise raise
    # AssertionError.
    assert not source_changes and not historical_changes
    # Display the serialized data produced by json.dumps.
    print(json.dumps(dict(protected_verified=len(protected), historical_verified=len(historical),
        # Supply indent as 2.
        # Supply changes as 0.
        # Supply runs as a dictionary of k mapped to a dictionary of a mapped to b for (a, b) in key/value pairs
        # from v; retain entries satisfying a differs from the text 'metrics' for (k, v) in key/value pairs from
        # summaries.
        changes=0, runs={k:{a:b for a,b in v.items() if a!='metrics'} for k,v in summaries.items()}), indent=2))


# Run this branch when __name__ equals the text '__main__'.
if __name__ == '__main__':
    # Call main with the supplied arguments.
    main()
