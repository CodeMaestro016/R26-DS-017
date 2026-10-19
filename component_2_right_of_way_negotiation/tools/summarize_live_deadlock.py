"""Summarize saved diagnostic timelines without changing their evidence."""
import json
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE / 'results/live_deadlock_investigation/20261016/baseline'


def main():
    summaries = {}
    for directory in ROOT.iterdir():
        if not (directory/'receipt.json').exists():
            continue
        receipt = json.loads((directory/'receipt.json').read_text())
        result = json.loads((directory/'runtime_result.json').read_text())
        first_blocked = None
        physical = []
        sources = []
        last_decisions = {}
        with (directory/'timeline.jsonl').open(encoding='utf-8') as stream:
            for line in stream:
                r = json.loads(line)
                if r['event'] == 'PHYSICAL_STATE':
                    states = r['states']
                    physical.append(dict(timestamp=r['timestamp'], active=len(states),
                        moving=sum(s['speed'] > 0 for s in states.values()),
                        maximum_speed=max((s['speed'] for s in states.values()), default=0)))
                elif r['event'] == 'EGO_DECISION':
                    last_decisions[r['ego_id']] = r
                elif r['event'] == 'COORDINATION_SOURCE':
                    sources.append(r)
        for event in result['events']:
            if event['status'] == 'COMMUNICATED_PRECEDENCE_DISAGREEMENT':
                first_blocked = event
                break
        selected = next((r for r in sources if first_blocked and r['timestamp']==first_blocked['timestamp']), None)
        premises = []
        if selected:
            for s in selected['snapshots']:
                evidence = selected['local_evidence'][s['ego_id']]
                premises.append(dict(ego_id=s['ego_id'], status=s['negotiation_status'],
                    local_edges=s.get('local_precedence_edges'), joint_edges=s.get('joint_precedence_edges'),
                    regulatory=evidence['regulatory'], conflict=evidence['conflict'],
                    disagreements=s.get('communicated_disagreements')))
        info = dict(receipt=receipt, first_blocked_event=first_blocked,
            last_physical_samples=physical[-5:], premises=premises,
            last_ego_decisions=last_decisions)
        summaries[directory.name]=info
        print(json.dumps(dict(scenario=directory.name, first_blocked=first_blocked,
            last_physical=physical[-1:])))
    (ROOT.parent/'baseline_analysis.json').write_text(json.dumps(summaries, indent=2), encoding='utf-8')


if __name__ == '__main__':
    main()
