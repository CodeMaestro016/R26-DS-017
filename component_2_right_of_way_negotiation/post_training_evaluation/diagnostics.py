"""Four V1 failure regressions, kept separate from fresh V2 final evidence."""
# Import json for use in this module.
import json
# Import csv for use in this module.
import csv
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import ROOT, digest, write_json, file_hash from .models for the operations below.
from .models import ROOT, digest, write_json, file_hash
# Import FUNCTIONAL, CONTINUOUS, manifest, source_identities from .scenarios for the operations below.
from .scenarios import FUNCTIONAL, CONTINUOUS, manifest, source_identities

# Set DIAGNOSTIC_ROOT to ROOT joined with the path segment 'diagnostics'.
DIAGNOSTIC_ROOT = ROOT / "diagnostics"
# Set CASES to a tuple containing a tuple containing FUNCTIONAL at 2, None, a tuple containing FUNCTIONAL at 4,
# None, a tuple containing...
CASES = ((FUNCTIONAL[2], None), (FUNCTIONAL[4], None),
         # Include a tuple containing CONTINUOUS at 0, 404 in this tuple.
         (CONTINUOUS[0], 404), (CONTINUOUS[0], 606))


# Identity using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def identity(root=DIAGNOSTIC_ROOT):
    # Set current to the result of manifest().
    current = manifest()
    # Update current with the supplied entries.
    current.update(protocol_id="V2_REPAIR_REGRESSION_NOT_FINAL",
        # Supply seeds as a list containing 404, 606.
        # Supply scenarios as a list of a dictionary built from the supplied values for (s, seed) in CASES.
        # Supply scenario as s.__dict__.
        # Supply seed as seed.
        seeds=[404, 606], scenarios=[dict(scenario=s.__dict__, seed=seed) for s, seed in CASES],
        # Supply evidence as the text 'Known V1 failure cases; diagnostic only; no final V2 manifest...'.
        evidence="Known V1 failure cases; diagnostic only; no final V2 manifest frozen")
    # Set frozen to a dictionary containing manifest_hash, manifest.
    frozen = {"manifest_hash": digest(current), "manifest": current}
    # Set path to the result of Path(root) joined with the path segment 'diagnostic_identity.json'.
    path = Path(root) / "diagnostic_identity.json"
    # Run this branch when whether path exists.
    if path.exists():
        # Set saved to the decoded data produced by json.loads from the text read from path.
        saved = json.loads(path.read_text(encoding="utf-8"))
        # Run this branch when saved differs from the decoded data produced by json.loads from the serialized data
        # produced by json.dumps.
        if saved != json.loads(json.dumps(frozen)):
            # Raise RuntimeError with the text 'DIAGNOSTIC_CODE_CHANGED: choose a separate diagnostic output root'
            # to stop this execution path.
            raise RuntimeError("DIAGNOSTIC_CODE_CHANGED: choose a separate diagnostic output root")
        # Return saved to the caller.
        return saved
    # Call write_json with the supplied arguments.
    write_json(path, frozen, exclusive=True)
    # Return frozen to the caller.
    return frozen


# Run diagnostics using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: the result of report_diagnostics(root).
# Processing: iterate over the relevant records.
def run_diagnostics(root=DIAGNOSTIC_ROOT):
    # Import run_episode from .runner for the operations below.
    from .runner import run_episode
    # Set frozen to the result of identity(root).
    frozen = identity(root)
    # Iterate over CASES, binding each item to (scenario, seed).
    for scenario, seed in CASES:
        # Call run_episode with the supplied arguments.
        run_episode(scenario, seed, "PROPOSED_MAPPO", frozen, root=root, suite="diagnostic")
    # Return the result of report_diagnostics(root) to the caller.
    return report_diagnostics(root)


# Report diagnostics using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: records.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def report_diagnostics(root=DIAGNOSTIC_ROOT):
    # Set root to the result of Path(root).
    root = Path(root)
    # Set frozen to the decoded data produced by json.loads from the text read from (root /
    # 'diagnostic_identity.json').
    frozen = json.loads((root / "diagnostic_identity.json").read_text(encoding="utf-8"))
    # Set records to an empty list.
    records = []
    # Iterate over the sorted values from the result of (root / 'runs').glob(the text '*/result.json'), binding
    # each item to path.
    for path in sorted((root / "runs").glob("*/result.json")):
        # Set record to the decoded data produced by json.loads from the text read from path.
        record = json.loads(path.read_text(encoding="utf-8"))
        # Set checksum to the decoded data produced by json.loads from the text read from
        # path.with_name('result.sha256.json').
        checksum = json.loads(path.with_name("result.sha256.json").read_text(encoding="utf-8"))
        # Run this branch when the result of digest(record) differs from checksum at 'result_hash'.
        if digest(record) != checksum["result_hash"]:
            # Raise RuntimeError with the text 'DIAGNOSTIC_RESULT_CHECKSUM_MISMATCH' to stop this execution path.
            raise RuntimeError("DIAGNOSTIC_RESULT_CHECKSUM_MISMATCH")
        # Run this branch when record at 'manifest_hash' equals frozen at 'manifest_hash' and record at 'suite'
        # equals the text 'diagnostic'.
        if record["manifest_hash"] == frozen["manifest_hash"] and record["suite"] == "diagnostic":
            # Append record to records.
            records.append(record)
    # Set latest to root joined with the path segment 'latest'.
    latest = root / "latest"
    # Call write_json with the supplied arguments.
    write_json(latest / "diagnostic_report.json", {"evidence": "REGRESSION_NOT_FINAL",
        # Store frozen under 'diagnostic_identity'.
        # Store records under 'runs'.
        "diagnostic_identity": frozen, "runs": records})
    # Set lines to a list containing the text '# V2 repair diagnostics', the text '', the text 'Known V1 failure
    # regressions. These are not...
    lines = ["# V2 repair diagnostics", "", "Known V1 failure regressions. These are not final evaluation results.", "",
        "| Case | Seed | Classification | Completed | Collisions | Violations | MAPPO | Accepted | Rejected | Fallback |", "|---|---|---|---|---|---|---|---|---|---|"]
    # Iterate over records, binding each item to r.
    for r in records:
        # Set m to r at 'metrics'.
        m = r["metrics"]
        # Append formatted text built from the embedded values to lines.
        lines.append(f"| {r['scenario_id']} | {r['seed']} | {r['classification']} | {m['total_vehicles_completed']}/{m['total_vehicles_scheduled']} | {m['collision_count']} | {m['blocked_zone_violation_count']} | {m.get('mappo_negotiation_events',0)} | {m.get('mappo_outcomes_accepted',0)} | {m.get('mappo_outcomes_rejected_by_shield',0)} | {m.get('fallback_activations',0)} |")
    # Update lines to its current value plus a list containing the text '', the text '| Case | Seed | Inferences |
    # Maximum wait (s) | Timeout |...', the text...
    lines += ["", "| Case | Seed | Inferences | Maximum wait (s) | Timeout | Deadlock | Fallback rate | Critic calls | Ego-local | Global graph controls | Policy unchanged | Action seed |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    # Iterate over records, binding each item to r.
    for r in records:
        # Set (m, i) to a tuple containing r at 'metrics', r at 'integrity'.
        m, i = r["metrics"], r["integrity"]
        # Set values to a list containing r at 'scenario_id', r at 'seed', m at 'mappo_inference_call_count', m at
        # 'maximum_waiting_time_seconds', m...
        values = [r['scenario_id'], r['seed'], m['mappo_inference_call_count'],
            # Include m at 'maximum_waiting_time_seconds' in this list.
            m['maximum_waiting_time_seconds'], m['timeout'],m['deadlock_observed'],
            # Include i at 'centralized_critic_runtime_calls' in this list.
            m.get('fallback_rate',0),i['centralized_critic_runtime_calls'],
            # Include i at 'centralized_execution_graph_used_for_control' in this list.
            i['decentralized_execution'],i['centralized_execution_graph_used_for_control'],
            # Include i at 'policy_hash_unchanged' in this list.
            i['policy_hash_unchanged'],r['policy_action_seed']]
        # Append the text '|' plus the result of ' | '.join(the result of map(str, values)) plus the text '|' to
        # lines.
        lines.append("| " + " | ".join(map(str,values)) + " |")
    # Update lines to its current value plus a list containing the text '', formatted text built from the embedded
    # values, the text 'Fallback rate = MAPPO epochs...
    lines += ["", f"Controller: {frozen['manifest']['controller_version']}. Shield: {frozen['manifest']['shield_version']}. Scientific inference: seeded stochastic masked sample.",
        "Fallback rate = MAPPO epochs requiring eligible pair fallback / MAPPO epochs. Mandatory turning-rule retention is recorded as rejection, never MAPPO_DIRECT.", "",
        "Fresh final seeds remain unrun and unfrozen: 1103, 2207, 3301, 4409, 5501, 6607, 7703, 8807, 9901, 11003.", ""]
    # Iterate over records, binding each item to r.
    for r in records:
        # Update lines to its current value plus a list containing formatted text built from the embedded values,
        # the text '', the text '```powershell', r at...
        lines += [f"Run `{r['run_id']}`; error: {r['error']}", "", "```powershell", r['replay_command'], "```", ""]
    # Write the supplied text to (latest / 'diagnostic_report.md').
    (latest / "diagnostic_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    # Set keys to the sorted values from a set of k for r in records; retain entries satisfying the negation of
    # whether v has type (dict, list).
    keys = sorted({k for r in records for k,v in r['metrics'].items() if not isinstance(v,(dict,list))})
    # Enter the result of (latest / 'diagnostic_metrics.csv').open(the text 'w') as handle and run the enclosed
    # operations within that context.
    with (latest / "diagnostic_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        # Set writer to the result of csv.writer(handle).
        writer = csv.writer(handle)
        # Call writer.writerow with the supplied arguments.
        writer.writerow(["run_id","scenario_id","seed","classification",*keys])
        # Iterate over records, binding each item to r.
        for r in records:
            # Call writer.writerow with the supplied arguments.
            writer.writerow([r['run_id'],r['scenario_id'],r['seed'],r['classification'],
                # Include the unpacked values from a lazy sequence of k from r['metrics']; use None if absent for
                # k in keys in this list.
                *(r['metrics'].get(k) for k in keys)])
    # Display the text 'Diagnostic report:'.
    print("Diagnostic report:", latest / "diagnostic_report.md")
    # Return records to the caller.
    return records
