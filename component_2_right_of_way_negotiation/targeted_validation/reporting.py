"""Backend-authored compact tables; every failure and unrun case stays visible."""
# Import html for use in this module.
import html
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import CASES from .cases for the operations below.
from .cases import CASES
# Import ROOT, V1_ROOT, EVIDENCE, latest, records, read_checked_manifest from .models for the operations below.
from .models import ROOT, V1_ROOT, EVIDENCE, latest, records, read_checked_manifest
# Import digest, write_json from post_training_evaluation.models for the operations below.
from post_training_evaluation.models import digest, write_json

# Set DISCLAIMER to the text 'This targeted suite validates the implementation against the...'.
DISCLAIMER = "This targeted suite validates the implementation against the specific panel feedback within the defined SUMO scope. It is not an exhaustive statistical study and is not real-world deployment validation."
# Set COMMENTS to a tuple containing a tuple containing the text 'Fairness-time measurement is very important.
# Narrow the scope...', a tuple...
COMMENTS = (
    # Include a tuple containing the text 'Fairness-time measurement is very important. Narrow the scope...', a
    # tuple containing the text... in this tuple.
    ("Fairness-time measurement is very important. Narrow the scope to selected complex intersections.", ("PV-03", "PV-04A"), "Bounded scope, selected complex manoeuvre, nominal dense per-approach/max/p95 wait, TTT, throughput and service-order inversion"),
    # Include a tuple containing the text 'Plan how to demonstrate the implemented system. Need to...', a tuple
    # containing the text... in this tuple.
    ("Plan how to demonstrate the implemented system. Need to address complex scenarios.", ("PV-02", "PV-03", "PV-04A", "PV-04B", "PV-05"), "Regulatory cycle, left turns, both dense conditions and natural four-way limitation with recorded replays"),
    # Include a tuple containing the text '4 vehicles are not enough. Use a more congested scenario.', a tuple
    # containing the text... in this tuple.
    ("4 vehicles are not enough. Use a more congested scenario.", ("PV-04A", "PV-04B"), "Nominal: 16 continuous vehicles, queues and actual progression measurements. Critical: same-scale preserved failure boundary. Both: measured live/moving and <=4 negotiators."),
)

# Fmt using the inputs and processing steps below.
# Input v: the supplied v.
# Output: the text 'N/A' when v is the same object as None, otherwise formatted text built from the embedded
# values when whether v has type float, otherwise a string built from v.
def fmt(v):
    # Return the text 'N/A' when v is the same object as None, otherwise formatted text built from the embedded
    # values when whether v has type float, otherwise a string built from v to the caller.
    return "N/A" if v is None else f"{v:.3f}" if isinstance(v, float) else str(v)

# Table using the inputs and processing steps below.
# Input headers: the supplied headers.
# Input rows: the supplied rows.
# Output: '| ' + ' | '.join(headers) plus ' |\n| ' plus the result of ' | '.join(('---' for _ in headers)) plus
# the text '|' plus the result of '\n'.join(a lazy sequence of '| ' + ' |...
def table(headers, rows):
    # Cell using the inputs and processing steps below.
    # Input v: the supplied v.
    # Output: the result of fmt(v).replace('|', '\\|').replace(the text '', the text '').
    def cell(v):
        # Return the result of fmt(v).replace('|', '\\|').replace(the text '', the text '') to the caller.
        return fmt(v).replace("|", "\\|").replace("\n", " ")
    # Return '| ' + ' | '.join(headers) plus ' |\n| ' plus the result of ' | '.join(('---' for _ in headers)) plus
    # the text '|' plus the result of '\n'.join(a lazy sequence of '| ' + ' | '.join((cell(v) for v in row)) plus
    # ' |' for row in rows) to the caller.
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "\n".join("| " + " | ".join(cell(v) for v in row) + " |" for row in rows)

# Html table using the inputs and processing steps below.
# Input headers: the supplied headers.
# Input rows: the supplied rows.
# Output: "<div class='scroll'><table><thead><tr>" plus ''.join(('<th>' + html.escape(h) + '</th>' for h in
# headers)) plus the text '</tr></thead><tbody>' plus the result of ''.join(a lazy...
def html_table(headers, rows):
    # Return "<div class='scroll'><table><thead><tr>" plus ''.join(('<th>' + html.escape(h) + '</th>' for h in
    # headers)) plus the text '</tr></thead><tbody>' plus the result of ''.join(a lazy sequence of '<tr>' +
    # ''.join(('<td>' + html.escape(fmt(v)) + '</td>' for v in row)) +...) plus the text '</tbody></table></div>'
    # to the caller.
    return "<div class='scroll'><table><thead><tr>" + "".join("<th>" + html.escape(h) + "</th>" for h in headers) + "</tr></thead><tbody>" + "".join("<tr>" + "".join("<td>" + html.escape(fmt(v)) + "</td>" for v in row) + "</tr>" for row in rows) + "</tbody></table></div>"

# Build payload using the inputs and processing steps below.
# Input frozen: the supplied frozen.
# Input runs: the supplied runs.
# Input fault: the supplied fault.
# Output: a dictionary built from the supplied values.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def build_payload(frozen, runs, fault=None):
    # Set entries to an empty list.
    entries = []
    # Iterate over frozen['manifest'] at 'cases', binding each item to c.
    for c in frozen["manifest"]["cases"]:
        # Iterate over c at 'methods' or a tuple containing the text 'CONTROLLED_MESSAGE_CHECKS', binding each
        # item to method.
        for method in c["methods"] or ("CONTROLLED_MESSAGE_CHECKS",):
            # Set found to a list of r for r in runs; retain entries satisfying r at 'scenario_id' equals c at
            # 'scenario_id' and r at 'method' equals method.
            found = [r for r in runs if r["scenario_id"] == c["scenario_id"] and r["method"] == method]
            # Run this branch when c at 'case_id' equals the text 'PV-06'.
            if c["case_id"] == "PV-06":
                # Set found to a list containing a dictionary built from the supplied values when fault, otherwise
                # an empty list.
                found = [dict(classification=fault["classification"], metrics={}, integrity={}, run_id=None,
                    # Supply historical_v1 as a Boolean built from 'historical_v1' from fault; use None if absent.
                    historical_v1=bool(fault.get("historical_v1")))] if fault else []
            # Iterate over found or a list containing None, binding each item to r.
            for r in found or [None]:
                # Append a dictionary built from the supplied values to entries.
                entries.append(dict(case_id=c["case_id"], method=method, purpose=c["purpose"],
                    # Supply vehicles as c at 'vehicle_count'.
                    # Supply classification as r at 'classification' when r, otherwise the text 'NOT_RUN'.
                    vehicles=c["vehicle_count"], classification=r["classification"] if r else "NOT_RUN",
                    # Supply evidence_version as the text 'PANEL_VALIDATION_V1 (preserved historical record)' when
                    # r and 'historical_v1' from r; use None if absent, otherwise the text 'PANEL_VALIDATION_V2'.
                    evidence_version=("PANEL_VALIDATION_V1 (preserved historical record)" if r and r.get("historical_v1") else "PANEL_VALIDATION_V2"),
                    # Supply run as r.
                    # Supply metrics as 'metrics' from r; use an empty dictionary if absent when r, otherwise an
                    # empty dictionary.
                    run=r, metrics=r.get("metrics", {}) if r else {}))
    # Set traffic to a list of e for e in entries; retain entries satisfying e at 'case_id' differs from the text
    # 'PV-06' and e at 'run'.
    traffic = [e for e in entries if e["case_id"] != "PV-06" and e["run"]]
    # Set dense to a list of e for e in entries; retain entries satisfying e at 'case_id' belongs to a set
    # containing the text 'PV-04A', the text 'PV-04B'.
    dense = [e for e in entries if e["case_id"] in {"PV-04A", "PV-04B"}]
    # Iterate over dense, binding each item to e.
    for e in dense:
        # Set e['demonstrates_learned_negotiation'] to a Boolean built from 'mappo_inference_call_count' from
        # e['metrics']; use 0 if absent when e at 'run', otherwise None.
        e["demonstrates_learned_negotiation"] = bool(e["metrics"].get("mappo_inference_call_count", 0)) if e["run"] else None
        # Set e['negotiation_note'] to the text 'No MAPPO calls were observed; this case does not demonstrate...'
        # when e at 'run' and the negation of e at 'demonstrates_learned_negotiation', otherwise the text
        # 'Recorded invocation only; execution outcomes distinguish...' when e at 'run', otherwise the text
        # 'Measurement pending.'.
        e["negotiation_note"] = "No MAPPO calls were observed; this case does not demonstrate the learned negotiation layer." if e["run"] and not e["demonstrates_learned_negotiation"] else "Recorded invocation only; execution outcomes distinguish direct MAPPO from safety fallback." if e["run"] else "Measurement pending."
    # Set traceability to a list of a dictionary built from the supplied values for (comment, ids, description) in
    # COMMENTS.
    traceability = [dict(comment=comment, evidence_cases=ids, evidence=description,
        # Supply status as the text 'MEASURED' when whether every item is true in a lazy sequence of whether any
        # item is true in (e['case_id'] == cid and e['classification'] != 'NOT_RUN' for e in entries) for cid in
        # ids, otherwise the text 'IMPLEMENTED; MEASUREMENT_PENDING'.
        status="MEASURED" if all(any(e["case_id"] == cid and e["classification"] != "NOT_RUN" for e in entries) for cid in ids) else "IMPLEMENTED; MEASUREMENT_PENDING",
        # Supply interpretation as the text 'Addressed means implemented and measured, not that every...'.
        interpretation="Addressed means implemented and measured, not that every scenario passed.") for comment, ids, description in COMMENTS]
    # Set totals to None when the negation of traffic, otherwise a dictionary built from the supplied values.
    totals = None if not traffic else dict(
        # Supply collisions as the sum of a lazy sequence of 'collision_count' from e['metrics']; use 0 if absent
        # for e in traffic.
        collisions=sum(e["metrics"].get("collision_count", 0) for e in traffic),
        # Supply blocked_zone_violations as the sum of a lazy sequence of 'blocked_zone_violation_count' from
        # e['metrics']; use 0 if absent for e in traffic.
        blocked_zone_violations=sum(e["metrics"].get("blocked_zone_violation_count", 0) for e in traffic),
        # Supply decentralized_execution as whether every item is true in a lazy sequence of
        # 'decentralized_execution' from e['run']['integrity']; use False if absent for e in traffic.
        decentralized_execution=all(e["run"]["integrity"].get("decentralized_execution", False) for e in traffic),
        # Supply centralized_critic_runtime_calls as the sum of a lazy sequence of
        # 'centralized_critic_runtime_calls' from e['run']['integrity']; use 0 if absent for e in traffic.
        centralized_critic_runtime_calls=sum(e["run"]["integrity"].get("centralized_critic_runtime_calls", 0) for e in traffic),
        # Supply policy_hash_unchanged as whether every item is true in a lazy sequence of 'policy_hash_unchanged'
        # from e['run']['integrity']; use False if absent for e in traffic.
        policy_hash_unchanged=all(e["run"]["integrity"].get("policy_hash_unchanged", False) for e in traffic),
        # Supply global_execution_graph_used_for_control as whether any item is true in a lazy sequence of
        # 'centralized_execution_graph_used_for_control' from e['run']['integrity']; use True if absent for e in
        # traffic.
        global_execution_graph_used_for_control=any(e["run"]["integrity"].get("centralized_execution_graph_used_for_control", True) for e in traffic))
    # Return a dictionary built from the supplied values to the caller.
    return dict(schema_version=1, evidence_classification=EVIDENCE,
        # Supply manifest_hash as frozen at 'manifest_hash'.
        # Supply scope as frozen['manifest'] at 'scope'.
        # Supply disclaimer as DISCLAIMER.
        manifest_hash=frozen["manifest_hash"], scope=frozen["manifest"]["scope"], disclaimer=DISCLAIMER,
        # Supply data_provenance as frozen['manifest'] at 'data_provenance'.
        # Supply cases as entries.
        # Supply dense as dense.
        data_provenance=frozen["manifest"]["data_provenance"], cases=entries, dense=dense,
        # Supply traceability as traceability.
        # Supply faults as fault.
        # Supply totals as totals.
        traceability=traceability, faults=fault, totals=totals,
        # Supply metric_definitions as frozen['manifest'] at 'metric_definitions'.
        metric_definitions=frozen["manifest"]["metric_definitions"],
        # Supply limitations as a list of e for e in entries; retain entries satisfying e at 'classification'
        # belongs to a set containing the text 'SAFE_DEGRADATION', the...
        limitations=[e for e in entries if e["classification"] in {"SAFE_DEGRADATION", "UNSAFE_FAILURE", "INVALID_EXPERIMENT"}],
        # Supply complete as whether every item is true in a lazy sequence of e at 'classification' differs from
        # the text 'NOT_RUN' for e in entries.
        complete=all(e["classification"] != "NOT_RUN" for e in entries),
        # Supply note as the text 'Preflight, replays, qualitative demonstrations and...'.
        note="Preflight, replays, qualitative demonstrations and comprehensive final evaluation are excluded from these panel case results.")

# Report using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def report(root=ROOT):
    # Read historical records without regenerating their reports in place.
    # Set requested to the result of Path(root).
    requested = Path(root)
    # Set legacy to the result of Path(the text 'results/panel_validation').
    legacy = Path("results/panel_validation")
    # Set historical_view to requested equals ROOT and the negation of whether (requested / 'manifest.json')
    # exists.
    historical_view = requested == ROOT and not (requested/"manifest.json").exists()
    # Run this branch when historical_view.
    if historical_view:
        # Set root to legacy joined with the path segment 'v2'.
        root = legacy/"v2"
    # Set frozen to the result of read_checked_manifest(root).
    frozen = read_checked_manifest(root)
    # Set fault_path to the result of Path(root) joined with the path segment 'faults.json'.
    fault_path = Path(root) / "faults.json"
    # Set fault to the decoded data produced by json.loads from the text read from fault_path when whether
    # fault_path exists, otherwise None.
    fault = json.loads(fault_path.read_text()) if fault_path.exists() else None
    # Run this branch when fault and fault at 'manifest_hash' differs from frozen at 'manifest_hash' or fault at
    # 'checksum' differs from the result of digest(fault['tests']).
    if fault and (fault["manifest_hash"] != frozen["manifest_hash"] or fault["checksum"] != digest(fault["tests"])):
        # Raise RuntimeError with the text 'PANEL_FAULT_EVIDENCE_MISMATCH' to stop this execution path.
        raise RuntimeError("PANEL_FAULT_EVIDENCE_MISMATCH")
    # Set measured to the result of records(root).
    measured = records(root)
    # Retain V1 records as visibly historical evidence; never rewrite or reclassify them.
    # Run this branch when historical_view or root equals ROOT or the result of Path(root).resolve() equals the
    # result of ROOT.resolve().
    if historical_view or root == ROOT or Path(root).resolve() == ROOT.resolve():
        # Run this branch when whether (V1_ROOT / 'manifest.json') is an existing file.
        if (V1_ROOT / "manifest.json").is_file():
            # Update measured to its current value plus a list of a dictionary built from r for r in the result of
            # records(V1_ROOT).
            measured += [dict(r, historical_v1=True) for r in records(V1_ROOT)]
            # Run this branch when fault is the same object as None and whether (V1_ROOT / 'faults.json') is an
            # existing file.
            if fault is None and (V1_ROOT / "faults.json").is_file():
                # Set old_fault to the decoded data produced by json.loads from the text read from (V1_ROOT /
                # 'faults.json').
                old_fault = json.loads((V1_ROOT / "faults.json").read_text())
                # Set old_manifest to the result of read_checked_manifest(V1_ROOT).
                old_manifest = read_checked_manifest(V1_ROOT)
                # Run this branch when old_fault at 'manifest_hash' differs from old_manifest at 'manifest_hash'
                # or old_fault at 'checksum' differs from the result of digest(old_fault at 'tests').
                if old_fault["manifest_hash"] != old_manifest["manifest_hash"] or old_fault["checksum"] != digest(old_fault["tests"]):
                    # Raise RuntimeError with the text 'V1_FAULT_EVIDENCE_MISMATCH' to stop this execution path.
                    raise RuntimeError("V1_FAULT_EVIDENCE_MISMATCH")
                # Set fault to a dictionary built from old_fault.
                fault = dict(old_fault, historical_v1=True)
    # Set payload to the result of build_payload(frozen, measured, fault).
    payload = build_payload(frozen, measured, fault)
    # Set destination to the result of latest(requested).
    destination = latest(requested)
    # Run this branch when the result of requested.resolve() equals the result of legacy.resolve() or the result
    # of legacy.resolve() belongs to requested.resolve().parents.
    if requested.resolve() == legacy.resolve() or legacy.resolve() in requested.resolve().parents:
        # Raise RuntimeError with the text 'HISTORICAL_REPORT_IS_READ_ONLY' to stop this execution path.
        raise RuntimeError("HISTORICAL_REPORT_IS_READ_ONLY")
    # Call write_json with the supplied arguments.
    write_json(destination / "panel_summary.json", payload)
    # Call write_json with the supplied arguments.
    write_json(destination / "panel_summary.sha256.json", {"payload_hash": digest(payload)})
    # Set headers to a tuple containing the text 'Case / method', the text 'Evidence version', the text
    # 'Vehicles', the text 'Purpose', the text...
    headers = ("Case / method", "Evidence version", "Vehicles", "Purpose", "Completed", "Collisions", "Blocked-zone violations", "Mean wait (s)", "Max wait (s)", "MAPPO calls", "Fallbacks", "Result")
    # Set rows to an empty list.
    rows = []
    # Iterate over payload at 'cases', binding each item to e.
    for e in payload["cases"]:
        # Set m to e at 'metrics'.
        m = e["metrics"]
        # Append a tuple containing e at 'case_id' plus the text '/' plus e at 'method', e at 'evidence_version',
        # e at 'vehicles', e at... to rows.
        rows.append((e["case_id"] + " / " + e["method"], e["evidence_version"], e["vehicles"], e["purpose"],
            # Include formatted text built from the embedded values when the text 'total_vehicles_completed'
            # belongs to m, otherwise None in this tuple.
            f"{m['total_vehicles_completed']}/{m['total_vehicles_scheduled']}" if "total_vehicles_completed" in m else None,
            # Include the unpacked values from a list of k from m; use None if absent for k in a tuple containing
            # the text 'collision_count', the text 'blocked_zone_violation_count', the text
            # 'mean_waiting_time_seconds',... in this tuple.
            *[m.get(k) for k in ("collision_count", "blocked_zone_violation_count", "mean_waiting_time_seconds", "maximum_waiting_time_seconds", "mappo_inference_call_count", "fallback_activations")], e["classification"]))
    # Set sections to a list containing a tuple containing the text 'Seven-case design / seven traffic episodes',
    # headers, rows.
    sections = [("Seven-case design / seven traffic episodes", headers, rows)]
    # Append a tuple containing the text 'SUCCESSFUL CAPABILITY EVIDENCE', headers, a list of row for (row, entry)
    # in corresponding items... to sections.
    sections.append(("SUCCESSFUL CAPABILITY EVIDENCE", headers, [row for row, entry in zip(rows, payload["cases"]) if entry["classification"] == "PASS" and entry["case_id"] in {"PV-01", "PV-02", "PV-03", "PV-04A"}]))
    # Set dense_keys to a tuple containing the text 'total_vehicles_scheduled', the text 'total_vehicles_spawned',
    # the text...
    dense_keys = ("total_vehicles_scheduled", "total_vehicles_spawned", "total_vehicles_completed",
        "maximum_simultaneous_active_vehicles", "maximum_simultaneously_moving_vehicles", "maximum_negotiation_participants",
        "mean_waiting_time_seconds", "median_waiting_time_seconds", "p95_waiting_time_seconds", "maximum_waiting_time_seconds",
        "approach_waiting_time_gap_seconds", "conflicting_pair_fcfs_inversion_rate", "total_team_travel_time_seconds", "mean_travel_time_seconds", "throughput_vehicles_per_minute", "completion_rate",
        "negotiation_events", "rule_resolved_events", "mappo_inference_call_count", "mappo_outcomes_accepted", "mappo_outcomes_rejected_by_safety_shield", "fallback_activations", "fallback_rate", "native_emergency_braking_events", "emergency_braking_warning_count")
    # Iterate over payload at 'dense', binding each item to e.
    for e in payload["dense"]:
        # Set m to e at 'metrics'.
        m = e["metrics"]
        # Set dense_rows to a list of a tuple containing the result of key.replace(the text '_', the text ''), key
        # from m; use None if absent for key in dense_keys.
        dense_rows = [(key.replace("_", " "), m.get(key)) for key in dense_keys]
        # Iterate over the text 'NESW', binding each item to a.
        for a in "NESW":
            # Update dense_rows to its current value plus a list containing a tuple containing a plus the text
            # 'mean wait (s)', a from m.get('per_approach_mean_waiting_time_seconds',...
            dense_rows += [(a + " mean wait (s)", m.get("per_approach_mean_waiting_time_seconds", {}).get(a)),
                           # Include a tuple containing a plus the text 'maximum queue depth', a from
                           # m.get('maximum_per_approach_queue_depth', {}); use None if... in this list.
                           (a + " maximum queue depth", m.get("maximum_per_approach_queue_depth", {}).get(a))]
        # Update dense_rows to its current value plus a list containing a tuple containing the text
        # 'Classification', e at 'classification', a tuple containing the text 'Evidence...
        dense_rows += [("Classification", e["classification"]), ("Evidence version", e["evidence_version"]), ("Learned negotiation evidence", e["negotiation_note"])]
        # Append a tuple containing e at 'case_id' plus the text 'Dense 16-Vehicle Validation', a tuple containing
        # the text 'Measurement', the... to sections.
        sections.append((e["case_id"] + " Dense 16-Vehicle Validation", ("Measurement", "Recorded value"), dense_rows))
    # Set details to an empty list.
    details = []
    # Iterate over payload at 'cases', binding each item to e.
    for e in payload["cases"]:
        # Set (r, m) to a tuple containing e at 'run', e at 'metrics'.
        r, m = e["run"], e["metrics"]
        # Run this branch when r and e at 'case_id' differs from the text 'PV-06'.
        if r and e["case_id"] != "PV-06":
            # Append a tuple containing e at 'case_id', e at 'method', r at 'termination_reason',
            # 'observed_simulation_time_seconds' from m; use... to details.
            details.append((e["case_id"], e["method"], r["termination_reason"], m.get("observed_simulation_time_seconds"), m.get("timeout"), m.get("deadlock_observed"), m.get("mappo_outcomes_accepted"), m.get("mappo_outcomes_rejected_by_safety_shield"), m.get("fallback_rate"), r["wall_clock_seconds"]))
    # Update sections to its current value plus a list containing a tuple containing the text 'Termination and
    # negotiation', a tuple containing the text 'Case', the text...
    sections += [("Termination and negotiation", ("Case", "Method", "Reason", "Observed sim s", "Timeout", "Deadlock observed", "Accepted", "Rejected", "Fallback rate", "Wall s"), details),
        # Include a tuple containing the text 'PANEL FEEDBACK TRACEABILITY', a tuple containing the text 'Original
        # comment', the text 'Cases',... in this list.
        ("PANEL FEEDBACK TRACEABILITY", ("Original comment", "Cases", "Evidence", "Status"), [(t["comment"], ", ".join(t["evidence_cases"]), t["evidence"], t["status"]) for t in payload["traceability"]]),
        # Include a tuple containing the text 'LIMITATION / FAILURE EVIDENCE', a tuple containing the text 'Case',
        # the text 'Method', the text... in this list.
        ("LIMITATION / FAILURE EVIDENCE", ("Case", "Method", "Result", "Cause"), [(e["case_id"], e["method"], e["classification"], json.dumps(e["metrics"].get("deadlock_cause") or (e["run"] or {}).get("error"))) for e in payload["limitations"]]),
        # Supply sort_keys as True.
        ("Architecture / integrity", ("Case", "Method", "Runtime guard values"), [(e["case_id"], e["method"], json.dumps(e["run"]["integrity"], sort_keys=True)) for e in payload["cases"] if e["run"] and e["case_id"] != "PV-06"]),
        # Include a tuple containing the text 'Recorded events and exact replay', a tuple containing the text
        # 'Case', the text 'Run', the text... in this list.
        ("Recorded events and exact replay", ("Case", "Run", "Execution outcomes", "Replay command"), [(e["case_id"], e["run"]["run_id"], ", ".join(str(v.get("execution_outcome")) for v in e["run"].get("runtime_events", [])), e["run"]["replay_command"]) for e in payload["cases"] if e["run"] and e["case_id"] != "PV-06"]),
        # Include a tuple containing the text 'Metric definitions', a tuple containing the text 'Metric', the text
        # 'Plain-English definition',... in this list.
        ("Metric definitions", ("Metric", "Plain-English definition"), list(payload["metric_definitions"].items()))]
    # Run this branch when fault.
    if fault:
        # Append a tuple containing the text 'PV-06 controlled message checks', a tuple containing the text
        # 'Fault', the text 'Permission',... to sections.
        sections.append(("PV-06 controlled message checks", ("Fault", "Permission", "Attempted entry rejected", "Passed"), [(t["fault"], t["permission"], t["blocked_entry_rejected"], t["passed"]) for t in fault["tests"]]))
    # Set intro to a list containing EVIDENCE, payload at 'scope', DISCLAIMER, payload at 'data_provenance',
    # payload at 'note', the text...
    intro = [EVIDENCE, payload["scope"], DISCLAIMER, payload["data_provenance"], payload["note"],
        "Nominal Dense evaluates operation under continuous congested traffic within the intended operating scope; it is capability evidence only to the extent demonstrated by its actual result. Critical Dense preserves a known liveness limitation under reciprocal mandatory-precedence conditions.",
        "V1 records retain their original run IDs, classifications, metrics and manifest identities. Historical rows are not newly executed V2 episodes. If V2 reruns a case, both records remain visible.",
        "Comment addressed means the requested evidence was implemented and measured; it does not mean every case passed.",
        "For a recorded dense SAFE_DEGRADATION result: Safety was maintained, but liveness/throughput degraded under dense demand. This is bounded episode evidence, not universal safety or production readiness.",
        "Unrun cases and inapplicable metrics display NOT_RUN / N/A. No confidence intervals or statistical generalization from this small suite."]
    # Set md to the text '# Targeted Validation' plus the result of '\n\n'.join(intro).
    md = "# Targeted Validation\n\n" + "\n\n".join(intro)
    # Set body to the text "<!doctype html><html lang='en'><meta..." plus the result of ''.join(a lazy sequence of
    # '<p>' + html.escape(p) plus '</p>' for p in intro).
    body = "<!doctype html><html lang='en'><meta charset='utf-8'><title>Targeted Validation</title><style>body{font:15px Arial;max-width:1500px;margin:30px;color:#203446;line-height:1.5}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd5df;padding:8px;text-align:left;overflow-wrap:anywhere}th{background:#edf3f7}.scroll{overflow:auto}h2{margin-top:32px}</style><h1>Targeted Validation</h1>" + "".join("<p>" + html.escape(p) + "</p>" for p in intro)
    # Iterate over sections, binding each item to (title, columns, values).
    for title, columns, values in sections:
        # Update md to its current value plus the text '##' plus title plus the text '' plus the result of
        # table(columns, values).
        md += "\n\n## " + title + "\n\n" + table(columns, values)
        # Update body to its current value plus the text '<h2>' plus the result of html.escape(title) plus the
        # text '</h2>' plus the result of html_table(columns, values).
        body += "<h2>" + html.escape(title) + "</h2>" + html_table(columns, values)
    # Write the supplied text to (destination / 'TARGETED_VALIDATION_REPORT.md').
    (destination / "TARGETED_VALIDATION_REPORT.md").write_text(md + "\n", encoding="utf-8")
    # Write the supplied text to (destination / 'TARGETED_VALIDATION_REPORT.html').
    (destination / "TARGETED_VALIDATION_REPORT.html").write_text(body + "</html>", encoding="utf-8")
    # Display the text 'Report:'.
    print("Report:", destination / "TARGETED_VALIDATION_REPORT.html", flush=True)
    # Return payload to the caller.
    return payload

# Print summary using the inputs and processing steps below.
# Input payload: the supplied payload.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records.
def print_summary(payload):
    # Display the text 'TARGETED VALIDATION COMPLETE' when payload at 'complete', otherwise the text 'TARGETED
    # VALIDATION INCOMPLETE'.
    print("TARGETED VALIDATION COMPLETE" if payload["complete"] else "TARGETED VALIDATION INCOMPLETE")
    # Iterate over payload at 'cases', binding each item to e.
    for e in payload["cases"]:
        # Set label to the text 'FAIL-SAFE PASS' when e at 'case_id' equals the text 'PV-06' and e at
        # 'classification' equals the text 'PASS', otherwise e at 'classification'.
        label = "FAIL-SAFE PASS" if e["case_id"] == "PV-06" and e["classification"] == "PASS" else e["classification"]
        # Display e at 'case_id'.
        print(e["case_id"], e["method"], label)
    # Display the text 'Safety and architecture:'.
    print("Safety and architecture:", payload["totals"])
    # Display the text 'Report:...'.
    print("Report: results\\targeted_validation\\v2\\latest\\TARGETED_VALIDATION_REPORT.html")
