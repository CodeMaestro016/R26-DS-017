"""Summarize saved diagnostic timelines without changing their evidence."""
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE = Path(__file__).resolve().parents[1]
# Set ROOT to BASE joined with the path segment 'results/live_deadlock_investigation/20261016/baseline'.
ROOT = BASE / 'results/live_deadlock_investigation/20261016/baseline'


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set summaries to an empty dictionary.
    summaries = {}
    # Iterate over the result of ROOT.iterdir(), binding each item to directory.
    for directory in ROOT.iterdir():
        # Run this branch when the negation of whether (directory / 'receipt.json') exists.
        if not (directory/'receipt.json').exists():
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set receipt to the decoded data produced by json.loads from the text read from (directory /
        # 'receipt.json').
        receipt = json.loads((directory/'receipt.json').read_text())
        # Set result to the decoded data produced by json.loads from the text read from (directory /
        # 'runtime_result.json').
        result = json.loads((directory/'runtime_result.json').read_text())
        # Set first_blocked to None.
        first_blocked = None
        # Set physical to an empty list.
        physical = []
        # Set sources to an empty list.
        sources = []
        # Set last_decisions to an empty dictionary.
        last_decisions = {}
        # Enter the result of (directory / 'timeline.jsonl').open() as stream and run the enclosed operations
        # within that context.
        with (directory/'timeline.jsonl').open(encoding='utf-8') as stream:
            # Iterate over stream, binding each item to line.
            for line in stream:
                # Set r to the decoded data produced by json.loads from line.
                r = json.loads(line)
                # Run this branch when r at 'event' equals the text 'PHYSICAL_STATE'.
                if r['event'] == 'PHYSICAL_STATE':
                    # Set states to r at 'states'.
                    states = r['states']
                    # Append a dictionary built from the supplied values to physical.
                    physical.append(dict(timestamp=r['timestamp'], active=len(states),
                        # Supply moving as the sum of a lazy sequence of s at 'speed' is greater than 0 for s in
                        # values from states.
                        moving=sum(s['speed'] > 0 for s in states.values()),
                        # Supply maximum_speed as the maximum of a lazy sequence of s at 'speed' for s in values
                        # from states.
                        # Supply default as 0.
                        maximum_speed=max((s['speed'] for s in states.values()), default=0)))
                # Run this branch when r at 'event' equals the text 'EGO_DECISION'.
                elif r['event'] == 'EGO_DECISION':
                    # Set last_decisions[r['ego_id']] to r.
                    last_decisions[r['ego_id']] = r
                # Run this branch when r at 'event' equals the text 'COORDINATION_SOURCE'.
                elif r['event'] == 'COORDINATION_SOURCE':
                    # Append r to sources.
                    sources.append(r)
        # Iterate over result at 'events', binding each item to event.
        for event in result['events']:
            # Run this branch when event at 'status' equals the text 'COMMUNICATED_PRECEDENCE_DISAGREEMENT'.
            if event['status'] == 'COMMUNICATED_PRECEDENCE_DISAGREEMENT':
                # Set first_blocked to event.
                first_blocked = event
                # Leave the nearest enclosing loop immediately.
                break
        # Set selected to the next item from a lazy sequence of r for r in sources; retain entries satisfying
        # first_blocked and r['timestamp'] equals first_blocked['timestamp'].
        selected = next((r for r in sources if first_blocked and r['timestamp']==first_blocked['timestamp']), None)
        # Set premises to an empty list.
        premises = []
        # Run this branch when selected.
        if selected:
            # Iterate over selected at 'snapshots', binding each item to s.
            for s in selected['snapshots']:
                # Set evidence to selected['local_evidence'] at s['ego_id'].
                evidence = selected['local_evidence'][s['ego_id']]
                # Append a dictionary built from the supplied values to premises.
                premises.append(dict(ego_id=s['ego_id'], status=s['negotiation_status'],
                    # Supply local_edges as 'local_precedence_edges' from s; use None if absent.
                    # Supply joint_edges as 'joint_precedence_edges' from s; use None if absent.
                    local_edges=s.get('local_precedence_edges'), joint_edges=s.get('joint_precedence_edges'),
                    # Supply regulatory as evidence at 'regulatory'.
                    # Supply conflict as evidence at 'conflict'.
                    regulatory=evidence['regulatory'], conflict=evidence['conflict'],
                    # Supply disagreements as 'communicated_disagreements' from s; use None if absent.
                    disagreements=s.get('communicated_disagreements')))
        # Set info to a dictionary built from the supplied values.
        info = dict(receipt=receipt, first_blocked_event=first_blocked,
            # Supply last_physical_samples as physical sliced by -5:.
            # Supply premises as premises.
            last_physical_samples=physical[-5:], premises=premises,
            # Supply last_ego_decisions as last_decisions.
            last_ego_decisions=last_decisions)
        # Set summaries[directory.name] to info.
        summaries[directory.name]=info
        # Display the serialized data produced by json.dumps.
        print(json.dumps(dict(scenario=directory.name, first_blocked=first_blocked,
            # Supply last_physical as physical sliced by -1:.
            last_physical=physical[-1:])))
    # Write the supplied text to (ROOT.parent / 'baseline_analysis.json').
    (ROOT.parent/'baseline_analysis.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')


# Run this branch when __name__ equals the text '__main__'.
if __name__ == '__main__':
    # Call main with the supplied arguments.
    main()
