"""Readable report and standalone plots built only from archived measurements."""
# Import csv for use in this module.
import csv
# Import html for use in this module.
import html
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import shutil for use in this module.
import shutil
# Import load_runs, aggregate, METRICS from .aggregation for the operations below.
from .aggregation import load_runs, aggregate, METRICS
# Import ROOT, METHODS, write_json, digest from .models for the operations below.
from .models import ROOT, METHODS, write_json, digest

# Set PLOTS to a tuple containing a tuple containing the text 'total_team_travel_time_seconds', the text 'Total
# team traffic exposure...
PLOTS = (("total_team_travel_time_seconds", "Total team traffic exposure (vehicle s)"),
    # Include a tuple containing the text 'throughput_vehicles_per_minute', the text 'Throughput (vehicles/min)'
    # in this tuple.
    ("throughput_vehicles_per_minute", "Throughput (vehicles/min)"),
    # Include a tuple containing the text 'maximum_waiting_time_seconds', the text 'Maximum observed incoming wait
    # (s)' in this tuple.
    ("maximum_waiting_time_seconds", "Maximum observed incoming wait (s)"),
    # Include a tuple containing the text 'approach_waiting_time_gap_seconds', the text 'Approach mean waiting gap
    # (s)' in this tuple.
    ("approach_waiting_time_gap_seconds", "Approach mean waiting gap (s)"),
    # Include a tuple containing the text 'completion_rate', the text 'Completion rate (fraction)' in this tuple.
    ("completion_rate", "Completion rate (fraction)"),
    # Include a tuple containing the text 'collision_count', the text 'Observed safety events per episode' in this
    # tuple.
    ("collision_count", "Observed safety events per episode"))

# Fmt using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the text 'N/A' when value is the same object as None, otherwise formatted text built from the embedded
# values when whether value has type a tuple containing float, int, otherwise a...
def fmt(value):
    # Return the text 'N/A' when value is the same object as None, otherwise formatted text built from the
    # embedded values when whether value has type a tuple containing float, int, otherwise a string built from
    # value to the caller.
    return "N/A" if value is None else f"{value:.3f}" if isinstance(value, (float, int)) else str(value)

# Table using the inputs and processing steps below.
# Input headers: the supplied headers.
# Input rows: the supplied rows.
# Output: '| ' + ' | '.join(headers) plus ' |\n| ' plus the result of ' | '.join(('---' for _ in headers)) plus
# the text '|' plus the result of '\n'.join(a lazy sequence of '| ' + ' |...
def table(headers, rows):
    # Return '| ' + ' | '.join(headers) plus ' |\n| ' plus the result of ' | '.join(('---' for _ in headers)) plus
    # the text '|' plus the result of '\n'.join(a lazy sequence of '| ' + ' | '.join((fmt(x) for x in row)) plus '
    # |' for row in rows) to the caller.
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "\n".join(
        # Evaluate the text '|' plus the result of ' | '.join(a lazy sequence of fmt(x) for x in row) plus the
        # text '|' as part of the enclosing expression.
        "| " + " | ".join(fmt(x) for x in row) + " |" for row in rows)

# Report using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Input suite: the supplied suite.
# Output: data.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def report(root=ROOT, suite=None):
    # Import protect_v1 from .models for the operations below.
    from .models import protect_v1
    # Call protect_v1 with the supplied arguments.
    protect_v1(root)
    # Set root to the result of Path(root).
    root = Path(root)
    # Set frozen to the decoded data produced by json.loads from the text read from (root / 'manifest.json').
    frozen = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    # Run this branch when frozen at 'manifest_hash' differs from the result of digest(frozen at 'manifest').
    if frozen["manifest_hash"] != digest(frozen["manifest"]):
        # Raise RuntimeError with the text 'MANIFEST_HASH_MISMATCH' to stop this execution path.
        raise RuntimeError("MANIFEST_HASH_MISMATCH")
    # Run this branch when suite is the same object as None.
    if suite is None:
        # Set suites to a list of json.loads(p.read_text(encoding='utf-8')) at 'suite' for p in the result of
        # (root / 'runs').glob(the text '*/result.json').
        suites = [json.loads(p.read_text(encoding="utf-8"))["suite"] for p in (root / "runs").glob("*/result.json")]
        # Set suite to the text 'final' when the text 'final' belongs to suites, otherwise the text 'smoke'.
        suite = "final" if "final" in suites else "smoke"
    # Set records to the result of load_runs(root, frozen, suite).
    records = load_runs(root, frozen, suite)
    # Set data to the result of aggregate(records, frozen, suite).
    data = aggregate(records, frozen, suite)
    # Set latest to root joined with the path segment 'latest'.
    latest = root / "latest"
    # Iterate over a tuple containing the text 'plots', the text 'runs', the text 'provenance', binding each item
    # to name.
    for name in ("plots", "runs", "provenance"):
        # Create the directory requested by (latest / name).
        (latest / name).mkdir(parents=True, exist_ok=True)
    # Call write_json with the supplied arguments.
    write_json(latest / "aggregate.json", data)
    # Call shutil.copyfile with the supplied arguments.
    shutil.copyfile(root / "manifest.json", latest / "provenance/manifest.json")
    # Iterate over records, binding each item to record.
    for record in records:
        # Set archive to root joined with the path segment 'runs' divided by record at 'run_id'.
        archive = root / "runs" / record["run_id"]
        # Set destination to latest joined with the path segment 'runs' divided by record at 'run_id'.
        destination = latest / "runs" / record["run_id"]
        # Create the directory requested by destination.
        destination.mkdir(exist_ok=True)
        # Iterate over the result of archive.iterdir(), binding each item to path.
        for path in archive.iterdir():
            # Run this branch when whether path is an existing file.
            if path.is_file():
                # Call shutil.copyfile with the supplied arguments.
                shutil.copyfile(path, destination / path.name)
    # Set faults to root joined with the path segment 'fault_tests.json'.
    faults = root / "fault_tests.json"
    # Set fault_data to the decoded data produced by json.loads from the text read from faults when whether faults
    # exists, otherwise None.
    fault_data = json.loads(faults.read_text(encoding="utf-8")) if faults.exists() else None
    # Run this branch when fault_data is a different object from None.
    if fault_data is not None:
        # Run this branch when fault_data at 'manifest_hash' differs from frozen at 'manifest_hash'.
        if fault_data["manifest_hash"] != frozen["manifest_hash"]:
            # Raise RuntimeError with the text 'FAULT_MANIFEST_MISMATCH' to stop this execution path.
            raise RuntimeError("FAULT_MANIFEST_MISMATCH")
        # Call shutil.copyfile with the supplied arguments.
        shutil.copyfile(faults, latest / "provenance/fault_tests.json")
    # Enter the result of (latest / 'runs/metrics.csv').open(the text 'w') as handle and run the enclosed
    # operations within that context.
    with (latest / "runs/metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        # Set writer to the result of csv.writer(handle).
        writer = csv.writer(handle)
        # Call writer.writerow with the supplied arguments.
        writer.writerow(("run_id", "method", "scenario", "seed", "classification") + METRICS)
        # Iterate over records, binding each item to r.
        for r in records:
            # Call writer.writerow with the supplied arguments.
            writer.writerow((r["run_id"], r["method"], r["scenario_id"], r["seed"], r["classification"]) + tuple(r["metrics"].get(k) for k in METRICS))
    # Import matplotlib for use in this module.
    import matplotlib
    # Call matplotlib.use with the supplied arguments.
    matplotlib.use("Agg")
    # Import matplotlib.pyplot as plt for use in this module.
    import matplotlib.pyplot as plt
    # Iterate over PLOTS, binding each item to (key, ylabel).
    for key, ylabel in PLOTS:
        # Set (fig, axis) to the result of plt.subplots().
        fig, axis = plt.subplots(figsize=(7.5, 4.5), layout="constrained")
        # Iterate over METHODS, binding each item to method.
        for method in METHODS:
            # Set groups to a list of g for g in data at 'groups'; retain entries satisfying g at 'method' equals
            # method and g at 'continuous'.
            groups = [g for g in data["groups"] if g["method"] == method and g["continuous"]]
            # Call groups.sort with the supplied arguments.
            groups.sort(key=lambda g: g["vehicle_count"])
            # Set x to a list of 4.0 divided by g at 'headway_seconds' for g in groups.
            x = [4. / g["headway_seconds"] for g in groups]
            # Set y to a list of g['metrics'][key] at 'mean' for g in groups.
            y = [g["metrics"][key]["mean"] for g in groups]
            # Call axis.plot with the supplied arguments.
            axis.plot(x, [float("nan") if v is None else v for v in y], "o-", label=method.replace("_", " "))
            # Run this branch when key equals the text 'collision_count'.
            if key == "collision_count":
                # Set unsafe to a list of g['metrics']['blocked_zone_violation_count'] at 'mean' for g in groups.
                unsafe = [g["metrics"]["blocked_zone_violation_count"]["mean"] for g in groups]
                # Call axis.plot with the supplied arguments.
                axis.plot(x, [float("nan") if v is None else v for v in unsafe], "x--",
                    # Supply label as the result of method.replace(the text '_', the text '') plus the text
                    # 'blocked-zone violations'.
                    label=method.replace("_", " ") + " blocked-zone violations")
        # Call axis.set with the supplied arguments.
        axis.set(xlabel="Scheduled demand intensity (vehicles/s across four approaches)", ylabel=ylabel)
        # Call axis.grid with the supplied arguments.
        axis.grid(alpha=.25)
        # Call axis.legend with the supplied arguments.
        axis.legend(fontsize=8)
        # Call axis.set_title with the supplied arguments.
        axis.set_title(data["evidence_classification"].replace("_", " "), fontsize=10)
        # Call fig.savefig with the supplied arguments.
        fig.savefig(latest / "plots" / f"{key}.png", dpi=180)
        # Call fig.savefig with the supplied arguments.
        fig.savefig(latest / "plots" / f"{key}.svg")
        # Call plt.close with the supplied arguments.
        plt.close(fig)
    # Set headers to a tuple containing the text 'Scenario', the text 'Method', the text 'n', the text
    # 'Classifications', the text 'TTT (vehicle...
    headers = ("Scenario", "Method", "n", "Classifications", "TTT (vehicle s)", "Travel mean (s)",
        "Throughput (veh/min)", "Completion", "Wait mean (s)", "Wait p95 (s)", "Wait max (s)",
        "Approach gap (s)", "FCFS inversion rate", "Max live", "Max negotiators")
    # Set keys to a tuple containing the text 'total_team_travel_time_seconds', the text
    # 'mean_travel_time_seconds', the text...
    keys = ("total_team_travel_time_seconds", "mean_travel_time_seconds", "throughput_vehicles_per_minute",
        "completion_rate", "mean_waiting_time_seconds", "p95_waiting_time_seconds",
        "maximum_waiting_time_seconds", "approach_waiting_time_gap_seconds",
        "conflicting_pair_fcfs_inversion_rate", "maximum_simultaneous_active_vehicles", "maximum_negotiation_participants")
    # Set rows to a list of a tuple containing g at 'scenario_id', g at 'method', g at 'episode_count', a string
    # built from g['classifications'] plus a tuple built from a lazy sequence of g['metrics'][k]['mean'] for k in
    # keys for g in data at 'groups'.
    rows = [(g["scenario_id"], g["method"], g["episode_count"], str(g["classifications"])) + tuple(
        # Evaluate g['metrics'][k] at 'mean' as part of the enclosing expression.
        g["metrics"][k]["mean"] for k in keys) for g in data["groups"]]
    # Set comparison to the result of table(headers, rows).
    comparison = table(headers, rows)
    # Set paper to the text '# Paper tables' plus data at 'evidence_classification' plus the text '' plus
    # comparison.
    paper = "# Paper tables\n\n" + data["evidence_classification"] + "\n\n" + comparison
    # Update paper to its current value plus the text '## Per-approach mean stopped wait (s)' plus the result of
    # table(a tuple containing the text 'Scenario', the text 'Method', the text 'N', the text 'E', the text...).
    paper += "\n\n## Per-approach mean stopped wait (s)\n\n" + table(("Scenario", "Method", "N", "E", "S", "W"), [
        # Evaluate a tuple containing g at 'scenario_id', g at 'method' plus a tuple built from a lazy sequence of
        # g['per_approach_mean_waiting_time_seconds'][a] at 'mean' for a in the text 'NESW' as part of the
        # enclosing expression.
        (g["scenario_id"], g["method"]) + tuple(g["per_approach_mean_waiting_time_seconds"][a]["mean"] for a in "NESW") for g in data["groups"]])
    # Update paper to its current value plus the text '## All statistics (across per-episode values)' plus the
    # result of table(a tuple containing the text 'Scenario', the text 'Method', the text 'Metric', the text 'n',
    # the...).
    paper += "\n\n## All statistics (across per-episode values)\n\n" + table(
        # Supply a tuple containing the text 'Scenario', the text 'Method', the text 'Metric', the text 'n', the
        # text 'Mean', the text... to table.
        ("Scenario", "Method", "Metric", "n", "Mean", "Median", "Sample SD", "95% CI of mean"),
        # Supply a list of a tuple containing g at 'scenario_id', g at 'method', k, s at 'n', s at 'mean', s at
        # 'median', s at 'standard_deviation', s... for g in data at 'groups' to table.
        [(g["scenario_id"], g["method"], k, s["n"], s["mean"], s["median"], s["standard_deviation"], s["ci95"])
         # Evaluate key/value pairs from g['metrics'] as part of the enclosing expression.
         for g in data["groups"] for k, s in g["metrics"].items()])
    # Update paper to its current value plus the text '## Paired differences (proposed minus baseline)' plus the
    # result of table(a tuple containing the text 'Scenario', the text 'Baseline', the text 'Metric', the text
    # 'Paired...).
    paper += "\n\n## Paired differences (proposed minus baseline)\n\n" + table(
        # Supply a tuple containing the text 'Scenario', the text 'Baseline', the text 'Metric', the text 'Paired
        # n', the text 'Mean... to table.
        ("Scenario", "Baseline", "Metric", "Paired n", "Mean difference", "95% CI"),
        # Supply a list of a tuple containing p at 'scenario_id', p at 'baseline', k plus ' (%)', s at 'n', s at
        # 'mean', s at 'ci95' for p in data at 'paired_comparisons' plus a list of a tuple containing p at
        # 'scenario_id', p at 'baseline', the text 'completion (percentage points)',... for p in data at
        # 'paired_comparisons' to table.
        [(p["scenario_id"], p["baseline"], k + " (%)", s["n"], s["mean"], s["ci95"])
         # Evaluate a list of a tuple containing p at 'scenario_id', p at 'baseline', the text 'completion
         # (percentage points)',... for p in data at 'paired_comparisons' as part of the enclosing expression.
         for p in data["paired_comparisons"] for k, s in p["relative_difference_percent"].items()] + [
        # Evaluate a tuple containing p at 'scenario_id', p at 'baseline', the text 'completion (percentage
        # points)',... as part of the enclosing expression.
        (p["scenario_id"], p["baseline"], "completion (percentage points)",
         # Include p['completion_rate_difference_percentage_points'] at 'mean' in this tuple.
         p["completion_rate_difference_percentage_points"]["n"], p["completion_rate_difference_percentage_points"]["mean"],
         # Include p['completion_rate_difference_percentage_points'] at 'ci95' in this tuple.
         p["completion_rate_difference_percentage_points"]["ci95"]) for p in data["paired_comparisons"]])
    # Set proposed to a list of r for r in records; retain entries satisfying r at 'method' equals the text
    # 'PROPOSED_MAPPO' and r at 'classification' differs from...
    proposed = [r for r in records if r["method"] == "PROPOSED_MAPPO" and r["classification"] != "INVALID_EXPERIMENT"]
    # Import summary from .aggregation for the operations below.
    from .aggregation import summary
    # Set card_value to a callback that returns the result of fmt(summary((r['metrics'].get(key) for r in
    # proposed)) at 'mean').
    card_value = lambda key: fmt(summary(r["metrics"].get(key) for r in proposed)["mean"])
    # Set total_mappo_events to the sum of a lazy sequence of 'mappo_negotiation_events' from r['metrics']; use 0
    # if absent for r in proposed.
    total_mappo_events = sum(r["metrics"].get("mappo_negotiation_events", 0) for r in proposed)
    # Set total_fallbacks to the sum of a lazy sequence of 'fallback_activations' from r['metrics']; use 0 if
    # absent for r in proposed.
    total_fallbacks = sum(r["metrics"].get("fallback_activations", 0) for r in proposed)
    # Set event_fallback_rate to total_fallbacks divided by total_mappo_events when total_mappo_events, otherwise
    # None.
    event_fallback_rate = total_fallbacks / total_mappo_events if total_mappo_events else None
    # Set cards to a dictionary containing Safety, MAPPO and shield, Efficiency, Fairness, Scalability,
    # Architecture.
    cards = {"Safety": f"{data['collision_free_episodes']}/{data['episode_count']} collision-free episodes; {data['blocked_zone_violation_count']} blocked-zone violations",
        # Store formatted text built from the embedded values under 'MAPPO and shield'.
        "MAPPO and shield": f"Proposed episode averages: events {card_value('mappo_negotiation_events')}; accepted {card_value('mappo_outcomes_accepted')}; rejected {card_value('mappo_outcomes_rejected_by_safety_shield')}; fallback activations {card_value('fallback_activations')}; event-weighted fallback rate {fmt(event_fallback_rate)} ({total_fallbacks}/{total_mappo_events})",
        # Store formatted text built from the embedded values under 'Efficiency'.
        "Efficiency": f"Proposed episode averages: TTT {card_value('total_team_travel_time_seconds')} vehicle s; travel {card_value('mean_travel_time_seconds')} s; throughput {card_value('throughput_vehicles_per_minute')} veh/min",
        # Store formatted text built from the embedded values under 'Fairness'.
        "Fairness": f"Proposed episode averages: wait {card_value('mean_waiting_time_seconds')} s; max {card_value('maximum_waiting_time_seconds')} s; p95 {card_value('p95_waiting_time_seconds')} s; approach gap {card_value('approach_waiting_time_gap_seconds')} s; inversion {card_value('conflicting_pair_fcfs_inversion_rate')}",
        # Store formatted text built from the embedded values under 'Scalability'.
        "Scalability": f"Proposed episode averages: completion {card_value('completion_rate')}; max live {card_value('maximum_simultaneous_active_vehicles')}; max negotiators {card_value('maximum_negotiation_participants')}",
        # Store formatted text built from the embedded values under 'Architecture'.
        "Architecture": f"Ego-local: {data['decentralized_execution']}; critic calls: {data['centralized_critic_runtime_calls']}; unchanged policy: {data['policy_hash_unchanged']}"}
    # Set notes to the text 'TTT includes scheduled waiting before insertion and...'.
    notes = ("TTT includes scheduled waiting before insertion and unfinished demand censored at the frozen budget. "
        "Completed-trip summaries use scheduled demand to network exit; unfinished trips are excluded and completion is shown alongside. "
        "Waiting includes only speed below the existing 0.5 m/s threshold on the incoming lane, including followers; unfinished waits are observed lower bounds. "
        "FCFS uses incoming-lane entry and front-bumper incoming-lane exit; timestamp ties use vehicle ID consistently; only geometrically conflicting different-approach pairs with both service times are eligible. "
        "No arbitrary fairness score. Lower waiting gap is more equal across approaches. "
        "HARDWARE-DEPENDENT RUNTIME MEASUREMENTS: full joint semantic inference and each ego decision plus native constraint calculation; no universal real-time claim. "
        "Braking events are contiguous episodes of measured deceleration exceeding configured comfortable deceleration; emergency-stop API counts are separate. "
        "95% CIs use deterministic percentile bootstrap of means (2000 resamples, seed 260826); n=1 has no CI. "
        "Invalid experiments remain visible and are excluded from performance aggregation. Paired percentages with a zero baseline are N/A; positive TTT/wait differences are worse, positive throughput/completion are better. "
        "Smoke is plumbing evidence only. All results are bounded simulation evidence, not real-world validation; inD is intention-model provenance.")
    # Update notes to its current value plus the text 'V2 scientific inference is seeded stochastic masked
    # sampling;...'.
    notes += " V2 scientific inference is seeded stochastic masked sampling; panel argmax is presentation only. Fallback rate counts negotiation epochs requiring eligible pair fallback divided by MAPPO epochs; it is not a pure MAPPO success rate. Protected rule enforcement is recorded as rejected MAPPO, never MAPPO_DIRECT."
    # Set md to formatted text built from the embedded values.
    md = f"# Post-Training Evaluation\n\n**{data['evidence_classification']}**\n\n{data['scope']}\n\n"
    # Update md to its current value plus formatted text built from the embedded values.
    md += f"{data['collision_count']} collisions observed in {data['episode_count']} evaluation episodes. Unsafe episode rate: {fmt(data['unsafe_episode_rate'])}.\n\n"
    # Update md to its current value plus '\n\n'.join((f'**{k}:** {v}' for k, v in cards.items())) plus '\n\n'
    # plus comparison plus the text '' plus notes.
    md += "\n\n".join(f"**{k}:** {v}" for k, v in cards.items()) + "\n\n" + comparison + "\n\n" + notes
    # Update md to its current value plus the text '## Every episode and replay' plus the result of table(a tuple
    # containing the text 'Run', the text 'Method', the text 'Scenario', the text 'Seed', the...).
    md += "\n\n## Every episode and replay\n\n" + table(("Run", "Method", "Scenario", "Seed", "Classification", "Error", "Replay command"), [
        # Evaluate a tuple built from a lazy sequence of r at k for k in a tuple containing the text 'run_id', the
        # text 'method', the text 'scenario_id', the text 'seed', the text 'classification',... as part of the
        # enclosing expression.
        tuple(r[k] for k in ("run_id", "method", "scenario_id", "seed", "classification", "error", "replay_command")) for r in records])
    # Update md to its current value plus the text '## Controlled message faults' plus the result of table(a tuple
    # containing 'Fault', 'Permission', 'Attempted entry rejected', 'Passed', a list of...) when fault_data,
    # otherwise the text 'N/A: not executed'.
    md += "\n\n## Controlled message faults\n\n" + (table(("Fault", "Permission", "Attempted entry rejected", "Passed"), [
        # Evaluate a tuple containing r at 'fault', r at 'permission', r at 'blocked_entry_rejected', r at
        # 'passed' as part of the enclosing expression.
        (r["fault"], r["permission"], r["blocked_entry_rejected"], r["passed"]) for r in fault_data["tests"]]) if fault_data else "N/A: not executed")
    # Iterate over PLOTS, binding each item to (key, ylabel).
    for key, ylabel in PLOTS:
        # Update md to its current value plus formatted text built from the embedded values.
        md += f"\n\n![{ylabel}](plots/{key}.png)"
    # Write the supplied text to (latest / 'POST_TRAINING_EVALUATION_REPORT.md').
    (latest / "POST_TRAINING_EVALUATION_REPORT.md").write_text(md, encoding="utf-8")
    # Write the supplied text to (latest / 'PAPER_TABLES.md').
    (latest / "PAPER_TABLES.md").write_text(paper, encoding="utf-8")
    # HTML is standalone and escapes every archived string; no live computation.
    # Html table using the inputs and processing steps below.
    # Input headers: the supplied headers.
    # Input rows: the supplied rows.
    # Output: "<div class='scroll'><table><thead><tr>" plus ''.join((f'<th>{html.escape(x)}</th>' for x in
    # headers)) plus the text '</tr></thead><tbody>' plus the result of ''.join(a lazy sequence of...
    def html_table(headers, rows):
        # Return "<div class='scroll'><table><thead><tr>" plus ''.join((f'<th>{html.escape(x)}</th>' for x in
        # headers)) plus the text '</tr></thead><tbody>' plus the result of ''.join(a lazy sequence of '<tr>' +
        # ''.join((f'<td>{html.escape(fmt(x))}</td>' for x in row)) + '</tr>'...) plus the text
        # '</tbody></table></div>' to the caller.
        return "<div class='scroll'><table><thead><tr>" + "".join(f"<th>{html.escape(x)}</th>" for x in headers) + "</tr></thead><tbody>" + "".join(
            # Evaluate the text '<tr>' plus the result of ''.join(a lazy sequence of
            # f'<td>{html.escape(fmt(x))}</td>' for x in row) plus the text '</tr>' as part of the enclosing
            # expression.
            "<tr>" + "".join(f"<td>{html.escape(fmt(x))}</td>" for x in row) + "</tr>" for row in rows) + "</tbody></table></div>"
    # Set content to the text "<!doctype html><html lang='en'><meta...".
    content = "<!doctype html><html lang='en'><meta charset='utf-8'><title>Post-Training Evaluation</title><style>body{font:15px Arial;margin:32px;color:#182b3a;line-height:1.5;max-width:1500px}h1,h2{color:#153b57}.cards{display:flex;flex-wrap:wrap;gap:16px}.card{border:1px solid #ccd6df;padding:16px;max-width:260px}.scroll{overflow:auto}table{border-collapse:collapse;font-size:13px}th,td{padding:9px;border:1px solid #d3dbe2;text-align:left}th{background:#eef3f7}img{max-width:750px;width:100%}code{word-break:break-all}</style>"
    # Update content to its current value plus formatted text built from the embedded values.
    content += f"<h1>Post-Training Evaluation</h1><h2>{html.escape(data['evidence_classification'])}</h2><p>{html.escape(data['scope'])}</p>"
    # Update content to its current value plus formatted text built from the embedded values.
    content += f"<p>{data['collision_count']} collisions observed in {data['episode_count']} evaluation episodes. Unsafe episode rate: {fmt(data['unsafe_episode_rate'])}. Integrity valid for all episodes: {data['integrity_all_valid']}.</p>"
    # Update content to its current value plus the text "<div class='cards'>" plus the result of ''.join((f"<div
    # class='card'><strong>{k}</strong><p>{html.escape(v)}</p></div>" for k, v in cards.items())) plus the text
    # '</div><h2>Method comparison</h2>' plus the result of html_table(headers, rows).
    content += "<div class='cards'>" + "".join(f"<div class='card'><strong>{k}</strong><p>{html.escape(v)}</p></div>" for k, v in cards.items()) + "</div><h2>Method comparison</h2>" + html_table(headers, rows)
    # Update content to its current value plus '<h2>Definitions and limits</h2><p>' plus html.escape(notes) plus
    # the text '</p><p>Out of scope:' plus the result of html.escape(the result of ',
    # '.join(data['out_of_scope'])) plus the text '</p>'.
    content += "<h2>Definitions and limits</h2><p>" + html.escape(notes) + "</p><p>Out of scope: " + html.escape(", ".join(data["out_of_scope"])) + "</p>"
    # Iterate over PLOTS, binding each item to (key, ylabel).
    for key, ylabel in PLOTS:
        # Update content to its current value plus formatted text built from the embedded values.
        content += f"<h2>{html.escape(ylabel)}</h2><img src='plots/{key}.png' alt='{html.escape(ylabel)}'>"
    # Update content to its current value plus the text '<h2>Every episode, failure and safe degradation</h2>'
    # plus the result of html_table(a tuple containing the text 'Run', the text 'Method', the text 'Scenario', the
    # text 'Seed', the...).
    content += "<h2>Every episode, failure and safe degradation</h2>" + html_table(("Run", "Method", "Scenario", "Seed", "Classification", "Error", "Replay command"), [
        # Evaluate a tuple built from a lazy sequence of r at k for k in a tuple containing the text 'run_id', the
        # text 'method', the text 'scenario_id', the text 'seed', the text 'classification',... as part of the
        # enclosing expression.
        tuple(r[k] for k in ("run_id", "method", "scenario_id", "seed", "classification", "error", "replay_command")) for r in records])
    # Update content to its current value plus the text '<h2>Controlled message faults</h2>' plus the result of
    # html_table(a tuple containing 'Fault', 'Permission', 'Entry rejected', 'Passed', a list of (r['fault'],...)
    # when fault_data, otherwise the text '<p>N/A: not executed</p>'.
    content += "<h2>Controlled message faults</h2>" + (html_table(("Fault", "Permission", "Entry rejected", "Passed"), [
        # Evaluate a tuple containing r at 'fault', r at 'permission', r at 'blocked_entry_rejected', r at
        # 'passed' as part of the enclosing expression.
        (r["fault"], r["permission"], r["blocked_entry_rejected"], r["passed"]) for r in fault_data["tests"]]) if fault_data else "<p>N/A: not executed</p>")
    # Update content to its current value plus the text "<p><a href='PAPER_TABLES.md'>Full statistical and
    # paired...".
    content += "<p><a href='PAPER_TABLES.md'>Full statistical and paired comparison tables</a></p></html>"
    # Write the supplied text to (latest / 'POST_TRAINING_EVALUATION_REPORT.html').
    (latest / "POST_TRAINING_EVALUATION_REPORT.html").write_text(content, encoding="utf-8")
    # Display the text 'Report:'.
    print("Report:", latest / "POST_TRAINING_EVALUATION_REPORT.html")
    # Return data to the caller.
    return data
