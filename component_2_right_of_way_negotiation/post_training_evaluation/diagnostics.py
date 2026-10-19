"""Four V1 failure regressions, kept separate from fresh V2 final evidence."""
import json
import csv
from pathlib import Path
from .models import ROOT, digest, write_json, file_hash
from .scenarios import FUNCTIONAL, CONTINUOUS, manifest, source_identities

DIAGNOSTIC_ROOT = ROOT / "diagnostics"
CASES = ((FUNCTIONAL[2], None), (FUNCTIONAL[4], None),
         (CONTINUOUS[0], 404), (CONTINUOUS[0], 606))


def identity(root=DIAGNOSTIC_ROOT):
    current = manifest()
    current.update(protocol_id="V2_REPAIR_REGRESSION_NOT_FINAL",
        seeds=[404, 606], scenarios=[dict(scenario=s.__dict__, seed=seed) for s, seed in CASES],
        evidence="Known V1 failure cases; diagnostic only; no final V2 manifest frozen")
    frozen = {"manifest_hash": digest(current), "manifest": current}
    path = Path(root) / "diagnostic_identity.json"
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if saved != json.loads(json.dumps(frozen)):
            raise RuntimeError("DIAGNOSTIC_CODE_CHANGED: choose a separate diagnostic output root")
        return saved
    write_json(path, frozen, exclusive=True)
    return frozen


def run_diagnostics(root=DIAGNOSTIC_ROOT):
    from .runner import run_episode
    frozen = identity(root)
    for scenario, seed in CASES:
        run_episode(scenario, seed, "PROPOSED_MAPPO", frozen, root=root, suite="diagnostic")
    return report_diagnostics(root)


def report_diagnostics(root=DIAGNOSTIC_ROOT):
    root = Path(root)
    frozen = json.loads((root / "diagnostic_identity.json").read_text(encoding="utf-8"))
    records = []
    for path in sorted((root / "runs").glob("*/result.json")):
        record = json.loads(path.read_text(encoding="utf-8"))
        checksum = json.loads(path.with_name("result.sha256.json").read_text(encoding="utf-8"))
        if digest(record) != checksum["result_hash"]:
            raise RuntimeError("DIAGNOSTIC_RESULT_CHECKSUM_MISMATCH")
        if record["manifest_hash"] == frozen["manifest_hash"] and record["suite"] == "diagnostic":
            records.append(record)
    latest = root / "latest"
    write_json(latest / "diagnostic_report.json", {"evidence": "REGRESSION_NOT_FINAL",
        "diagnostic_identity": frozen, "runs": records})
    lines = ["# V2 repair diagnostics", "", "Known V1 failure regressions. These are not final evaluation results.", "",
        "| Case | Seed | Classification | Completed | Collisions | Violations | MAPPO | Accepted | Rejected | Fallback |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        m = r["metrics"]
        lines.append(f"| {r['scenario_id']} | {r['seed']} | {r['classification']} | {m['total_vehicles_completed']}/{m['total_vehicles_scheduled']} | {m['collision_count']} | {m['blocked_zone_violation_count']} | {m.get('mappo_negotiation_events',0)} | {m.get('mappo_outcomes_accepted',0)} | {m.get('mappo_outcomes_rejected_by_shield',0)} | {m.get('fallback_activations',0)} |")
    lines += ["", "| Case | Seed | Inferences | Maximum wait (s) | Timeout | Deadlock | Fallback rate | Critic calls | Ego-local | Global graph controls | Policy unchanged | Action seed |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in records:
        m, i = r["metrics"], r["integrity"]
        values = [r['scenario_id'], r['seed'], m['mappo_inference_call_count'],
            m['maximum_waiting_time_seconds'], m['timeout'],m['deadlock_observed'],
            m.get('fallback_rate',0),i['centralized_critic_runtime_calls'],
            i['decentralized_execution'],i['centralized_execution_graph_used_for_control'],
            i['policy_hash_unchanged'],r['policy_action_seed']]
        lines.append("| " + " | ".join(map(str,values)) + " |")
    lines += ["", f"Controller: {frozen['manifest']['controller_version']}. Shield: {frozen['manifest']['shield_version']}. Scientific inference: seeded stochastic masked sample.",
        "Fallback rate = MAPPO epochs requiring eligible pair fallback / MAPPO epochs. Mandatory turning-rule retention is recorded as rejection, never MAPPO_DIRECT.", "",
        "Fresh final seeds remain unrun and unfrozen: 1103, 2207, 3301, 4409, 5501, 6607, 7703, 8807, 9901, 11003.", ""]
    for r in records:
        lines += [f"Run `{r['run_id']}`; error: {r['error']}", "", "```powershell", r['replay_command'], "```", ""]
    (latest / "diagnostic_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    keys = sorted({k for r in records for k,v in r['metrics'].items() if not isinstance(v,(dict,list))})
    with (latest / "diagnostic_metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["run_id","scenario_id","seed","classification",*keys])
        for r in records:
            writer.writerow([r['run_id'],r['scenario_id'],r['seed'],r['classification'],
                *(r['metrics'].get(k) for k in keys)])
    print("Diagnostic report:", latest / "diagnostic_report.md")
    return records
