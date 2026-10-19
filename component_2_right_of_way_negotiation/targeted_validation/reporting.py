"""Backend-authored compact tables; every failure and unrun case stays visible."""
import html
import json
from pathlib import Path
from .cases import CASES
from .models import ROOT, V1_ROOT, EVIDENCE, latest, records, read_checked_manifest
from post_training_evaluation.models import digest, write_json

DISCLAIMER = "This targeted suite validates the implementation against the specific panel feedback within the defined SUMO scope. It is not an exhaustive statistical study and is not real-world deployment validation."
COMMENTS = (
    ("Fairness-time measurement is very important. Narrow the scope to selected complex intersections.", ("PV-03", "PV-04A"), "Bounded scope, selected complex manoeuvre, nominal dense per-approach/max/p95 wait, TTT, throughput and service-order inversion"),
    ("Plan how to demonstrate the implemented system. Need to address complex scenarios.", ("PV-02", "PV-03", "PV-04A", "PV-04B", "PV-05"), "Regulatory cycle, left turns, both dense conditions and natural four-way limitation with recorded replays"),
    ("4 vehicles are not enough. Use a more congested scenario.", ("PV-04A", "PV-04B"), "Nominal: 16 continuous vehicles, queues and actual progression measurements. Critical: same-scale preserved failure boundary. Both: measured live/moving and <=4 negotiators."),
)

def fmt(v):
    return "N/A" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)

def table(headers, rows):
    def cell(v):
        return fmt(v).replace("|", "\\|").replace("\n", " ")
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "\n".join("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)

def html_table(headers, rows):
    return "<div class='scroll'><table><thead><tr>" + "".join("<th>" + html.escape(h) + "</th>" for h in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + html.escape(fmt(v)) + "</td>" for v in row) + "</tr>" for row in rows) + "</tbody></table></div>"

def build_payload(frozen, runs, fault=None):
    entries = []
    for c in frozen["manifest"]["cases"]:
        for method in c["methods"] or ("CONTROLLED_MESSAGE_CHECKS",):
            found = [r for r in runs if r["scenario_id"] == c["scenario_id"] and r["method"] == method]
            if c["case_id"] == "PV-06":
                found = [dict(classification=fault["classification"], metrics={}, integrity={}, run_id=None,
                    historical_v1=bool(fault.get("historical_v1")))] if fault else []
            for r in found or [None]:
                entries.append(dict(case_id=c["case_id"], method=method, purpose=c["purpose"],
                    vehicles=c["vehicle_count"], classification=r["classification"] if r else "NOT_RUN",
                    evidence_version=("PANEL_VALIDATION_V1 (preserved historical record)" if r and r.get("historical_v1") else "PANEL_VALIDATION_V2"),
                    run=r, metrics=r.get("metrics", {}) if r else {}))
    traffic = [e for e in entries if e["case_id"] != "PV-06" and e["run"]]
    dense = [e for e in entries if e["case_id"] in {"PV-04A", "PV-04B"}]
    for e in dense:
        e["demonstrates_learned_negotiation"] = bool(e["metrics"].get("mappo_inference_call_count", 0)) if e["run"] else None
        e["negotiation_note"] = "No MAPPO calls were observed; this case does not demonstrate the learned negotiation layer." if e["run"] and not e["demonstrates_learned_negotiation"] else "Recorded invocation only; execution outcomes distinguish direct MAPPO from safety fallback." if e["run"] else "Measurement pending."
    traceability = [dict(comment=comment, evidence_cases=ids, evidence=description,
        status="MEASURED" if all(any(e["case_id"] == cid and e["classification"] != "NOT_RUN" for e in entries) for cid in ids) else "IMPLEMENTED; MEASUREMENT_PENDING",
        interpretation="Addressed means implemented and measured, not that every scenario passed.") for comment, ids, description in COMMENTS]
    totals = None if not traffic else dict(
        collisions=sum(e["metrics"].get("collision_count", 0) for e in traffic),
        blocked_zone_violations=sum(e["metrics"].get("blocked_zone_violation_count", 0) for e in traffic),
        decentralized_execution=all(e["run"]["integrity"].get("decentralized_execution", False) for e in traffic),
        centralized_critic_runtime_calls=sum(e["run"]["integrity"].get("centralized_critic_runtime_calls", 0) for e in traffic),
        policy_hash_unchanged=all(e["run"]["integrity"].get("policy_hash_unchanged", False) for e in traffic),
        global_execution_graph_used_for_control=any(e["run"]["integrity"].get("centralized_execution_graph_used_for_control", True) for e in traffic))
    return dict(schema_version=1, evidence_classification=EVIDENCE,
        manifest_hash=frozen["manifest_hash"], scope=frozen["manifest"]["scope"], disclaimer=DISCLAIMER,
        data_provenance=frozen["manifest"]["data_provenance"], cases=entries, dense=dense,
        traceability=traceability, faults=fault, totals=totals,
        metric_definitions=frozen["manifest"]["metric_definitions"],
        limitations=[e for e in entries if e["classification"] in {"SAFE_DEGRADATION", "UNSAFE_FAILURE", "INVALID_EXPERIMENT"}],
        complete=all(e["classification"] != "NOT_RUN" for e in entries),
        note="Preflight, replays, qualitative demonstrations and comprehensive final evaluation are excluded from these panel case results.")

def report(root=ROOT):
    # Read historical records without regenerating their reports in place.
    requested = Path(root)
    legacy = Path("results/panel_validation")
    historical_view = requested == ROOT and not (requested/"manifest.json").exists()
    if historical_view:
        root = legacy/"v2"
    frozen = read_checked_manifest(root)
    fault_path = Path(root) / "faults.json"
    fault = json.loads(fault_path.read_text()) if fault_path.exists() else None
    if fault and (fault["manifest_hash"] != frozen["manifest_hash"] or fault["checksum"] != digest(fault["tests"])):
        raise RuntimeError("PANEL_FAULT_EVIDENCE_MISMATCH")
    measured = records(root)
    # Retain V1 records as visibly historical evidence; never rewrite or reclassify them.
    if historical_view or root == ROOT or Path(root).resolve() == ROOT.resolve():
        if (V1_ROOT / "manifest.json").is_file():
            measured += [dict(r, historical_v1=True) for r in records(V1_ROOT)]
            if fault is None and (V1_ROOT / "faults.json").is_file():
                old_fault = json.loads((V1_ROOT / "faults.json").read_text())
                old_manifest = read_checked_manifest(V1_ROOT)
                if old_fault["manifest_hash"] != old_manifest["manifest_hash"] or old_fault["checksum"] != digest(old_fault["tests"]):
                    raise RuntimeError("V1_FAULT_EVIDENCE_MISMATCH")
                fault = dict(old_fault, historical_v1=True)
    payload = build_payload(frozen, measured, fault)
    destination = latest(requested)
    if requested.resolve() == legacy.resolve() or legacy.resolve() in requested.resolve().parents:
        raise RuntimeError("HISTORICAL_REPORT_IS_READ_ONLY")
    write_json(destination / "panel_summary.json", payload)
    write_json(destination / "panel_summary.sha256.json", {"payload_hash": digest(payload)})
    headers = ("Case / method", "Evidence version", "Vehicles", "Purpose", "Completed", "Collisions", "Blocked-zone violations", "Mean wait (s)", "Max wait (s)", "MAPPO calls", "Fallbacks", "Result")
    rows = []
    for e in payload["cases"]:
        m = e["metrics"]
        rows.append((e["case_id"] + " / " + e["method"], e["evidence_version"], e["vehicles"], e["purpose"],
            f"{m['total_vehicles_completed']}/{m['total_vehicles_scheduled']}" if "total_vehicles_completed" in m else None,
            *[m.get(k) for k in ("collision_count", "blocked_zone_violation_count", "mean_waiting_time_seconds", "maximum_waiting_time_seconds", "mappo_inference_call_count", "fallback_activations")], e["classification"]))
    sections = [("Seven-case design / seven traffic episodes", headers, rows)]
    sections.append(("SUCCESSFUL CAPABILITY EVIDENCE", headers, [row for row, entry in zip(rows, payload["cases"]) if entry["classification"] == "PASS" and entry["case_id"] in {"PV-01", "PV-02", "PV-03", "PV-04A"}]))
    dense_keys = ("total_vehicles_scheduled", "total_vehicles_spawned", "total_vehicles_completed",
        "maximum_simultaneous_active_vehicles", "maximum_simultaneously_moving_vehicles", "maximum_negotiation_participants",
        "mean_waiting_time_seconds", "median_waiting_time_seconds", "p95_waiting_time_seconds", "maximum_waiting_time_seconds",
        "approach_waiting_time_gap_seconds", "conflicting_pair_fcfs_inversion_rate", "total_team_travel_time_seconds", "mean_travel_time_seconds", "throughput_vehicles_per_minute", "completion_rate",
        "negotiation_events", "rule_resolved_events", "mappo_inference_call_count", "mappo_outcomes_accepted", "mappo_outcomes_rejected_by_safety_shield", "fallback_activations", "fallback_rate", "native_emergency_braking_events", "emergency_braking_warning_count")
    for e in payload["dense"]:
        m = e["metrics"]
        dense_rows = [(key.replace("_", " "), m.get(key)) for key in dense_keys]
        for a in "NESW":
            dense_rows += [(a + " mean wait (s)", m.get("per_approach_mean_waiting_time_seconds", {}).get(a)),
                           (a + " maximum queue depth", m.get("maximum_per_approach_queue_depth", {}).get(a))]
        dense_rows += [("Classification", e["classification"]), ("Evidence version", e["evidence_version"]), ("Learned negotiation evidence", e["negotiation_note"])]
        sections.append((e["case_id"] + " Dense 16-Vehicle Validation", ("Measurement", "Recorded value"), dense_rows))
    details = []
    for e in payload["cases"]:
        r, m = e["run"], e["metrics"]
        if r and e["case_id"] != "PV-06":
            details.append((e["case_id"], e["method"], r["termination_reason"], m.get("observed_simulation_time_seconds"), m.get("timeout"), m.get("deadlock_observed"), m.get("mappo_outcomes_accepted"), m.get("mappo_outcomes_rejected_by_safety_shield"), m.get("fallback_rate"), r["wall_clock_seconds"]))
    sections += [("Termination and negotiation", ("Case", "Method", "Reason", "Observed sim s", "Timeout", "Deadlock observed", "Accepted", "Rejected", "Fallback rate", "Wall s"), details),
        ("PANEL FEEDBACK TRACEABILITY", ("Original comment", "Cases", "Evidence", "Status"), [(t["comment"], ", ".join(t["evidence_cases"]), t["evidence"], t["status"]) for t in payload["traceability"]]),
        ("LIMITATION / FAILURE EVIDENCE", ("Case", "Method", "Result", "Cause"), [(e["case_id"], e["method"], e["classification"], json.dumps(e["metrics"].get("deadlock_cause") or (e["run"] or {}).get("error"))) for e in payload["limitations"]]),
        ("Architecture / integrity", ("Case", "Method", "Runtime guard values"), [(e["case_id"], e["method"], json.dumps(e["run"]["integrity"], sort_keys=True)) for e in payload["cases"] if e["run"] and e["case_id"] != "PV-06"]),
        ("Recorded events and exact replay", ("Case", "Run", "Execution outcomes", "Replay command"), [(e["case_id"], e["run"]["run_id"], ", ".join(str(v.get("execution_outcome")) for v in e["run"].get("runtime_events", [])), e["run"]["replay_command"]) for e in payload["cases"] if e["run"] and e["case_id"] != "PV-06"]),
        ("Metric definitions", ("Metric", "Plain-English definition"), list(payload["metric_definitions"].items()))]
    if fault:
        sections.append(("PV-06 controlled message checks", ("Fault", "Permission", "Attempted entry rejected", "Passed"), [(t["fault"], t["permission"], t["blocked_entry_rejected"], t["passed"]) for t in fault["tests"]]))
    intro = [EVIDENCE, payload["scope"], DISCLAIMER, payload["data_provenance"], payload["note"],
        "Nominal Dense evaluates operation under continuous congested traffic within the intended operating scope; it is capability evidence only to the extent demonstrated by its actual result. Critical Dense preserves a known liveness limitation under reciprocal mandatory-precedence conditions.",
        "V1 records retain their original run IDs, classifications, metrics and manifest identities. Historical rows are not newly executed V2 episodes. If V2 reruns a case, both records remain visible.",
        "Comment addressed means the requested evidence was implemented and measured; it does not mean every case passed.",
        "For a recorded dense SAFE_DEGRADATION result: Safety was maintained, but liveness/throughput degraded under dense demand. This is bounded episode evidence, not universal safety or production readiness.",
        "Unrun cases and inapplicable metrics display NOT_RUN / N/A. No confidence intervals or statistical generalization from this small suite."]
    md = "# Targeted Validation\n\n" + "\n\n".join(intro)
    body = "<!doctype html><html lang='en'><meta charset='utf-8'><title>Targeted Validation</title><style>body{font:15px Arial;max-width:1500px;margin:30px;color:#203446;line-height:1.5}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd5df;padding:8px;text-align:left;overflow-wrap:anywhere}th{background:#edf3f7}.scroll{overflow:auto}h2{margin-top:32px}</style><h1>Targeted Validation</h1>" + "".join("<p>" + html.escape(p) + "</p>" for p in intro)
    for title, columns, values in sections:
        md += "\n\n## " + title + "\n\n" + table(columns, values)
        body += "<h2>" + html.escape(title) + "</h2>" + html_table(columns, values)
    (destination / "TARGETED_VALIDATION_REPORT.md").write_text(md + "\n", encoding="utf-8")
    (destination / "TARGETED_VALIDATION_REPORT.html").write_text(body + "</html>", encoding="utf-8")
    print("Report:", destination / "TARGETED_VALIDATION_REPORT.html", flush=True)
    return payload

def print_summary(payload):
    print("TARGETED VALIDATION COMPLETE" if payload["complete"] else "TARGETED VALIDATION INCOMPLETE")
    for e in payload["cases"]:
        label = "FAIL-SAFE PASS" if e["case_id"] == "PV-06" and e["classification"] == "PASS" else e["classification"]
        print(e["case_id"], e["method"], label)
    print("Safety and architecture:", payload["totals"])
    print("Report: results\\targeted_validation\\v2\\latest\\TARGETED_VALIDATION_REPORT.html")
