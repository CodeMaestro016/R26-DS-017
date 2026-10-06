"""Readable report and standalone plots built only from archived measurements."""
import csv
import html
import json
from pathlib import Path
import shutil
from .aggregation import load_runs, aggregate, METRICS
from .models import ROOT, METHODS, write_json, digest

PLOTS = (("total_team_travel_time_seconds", "Total team traffic exposure (vehicle s)"),
    ("throughput_vehicles_per_minute", "Throughput (vehicles/min)"),
    ("maximum_waiting_time_seconds", "Maximum observed incoming wait (s)"),
    ("approach_waiting_time_gap_seconds", "Approach mean waiting gap (s)"),
    ("completion_rate", "Completion rate (fraction)"),
    ("collision_count", "Observed safety events per episode"))

def fmt(value):
    return "N/A" if value is None else f"{value:.3f}" if isinstance(value, (float, int)) else str(value)

def table(headers, rows):
    return "| " + " | ".join(headers) + " |\n| " + " | ".join("---" for _ in headers) + " |\n" + "\n".join(
        "| " + " | ".join(fmt(x) for x in row) + " |" for row in rows)

def report(root=ROOT, suite=None):
    root = Path(root)
    frozen = json.loads((root / "manifest.json").read_text(encoding="utf-8"))
    if frozen["manifest_hash"] != digest(frozen["manifest"]):
        raise RuntimeError("MANIFEST_HASH_MISMATCH")
    if suite is None:
        suites = [json.loads(p.read_text(encoding="utf-8"))["suite"] for p in (root / "runs").glob("*/result.json")]
        suite = "final" if "final" in suites else "smoke"
    records = load_runs(root, frozen, suite)
    data = aggregate(records, frozen, suite)
    latest = root / "latest"
    for name in ("plots", "runs", "provenance"):
        (latest / name).mkdir(parents=True, exist_ok=True)
    write_json(latest / "aggregate.json", data)
    shutil.copyfile(root / "manifest.json", latest / "provenance/manifest.json")
    for record in records:
        archive = root / "runs" / record["run_id"]
        destination = latest / "runs" / record["run_id"]
        destination.mkdir(exist_ok=True)
        for path in archive.iterdir():
            if path.is_file():
                shutil.copyfile(path, destination / path.name)
    faults = root / "fault_tests.json"
    fault_data = json.loads(faults.read_text(encoding="utf-8")) if faults.exists() else None
    if fault_data is not None:
        if fault_data["manifest_hash"] != frozen["manifest_hash"]:
            raise RuntimeError("FAULT_MANIFEST_MISMATCH")
        shutil.copyfile(faults, latest / "provenance/fault_tests.json")
    with (latest / "runs/metrics.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("run_id", "method", "scenario", "seed", "classification") + METRICS)
        for r in records:
            writer.writerow((r["run_id"], r["method"], r["scenario_id"], r["seed"], r["classification"]) + tuple(r["metrics"].get(k) for k in METRICS))
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for key, ylabel in PLOTS:
        fig, axis = plt.subplots(figsize=(7.5, 4.5), layout="constrained")
        for method in METHODS:
            groups = [g for g in data["groups"] if g["method"] == method and g["continuous"]]
            groups.sort(key=lambda g: g["vehicle_count"])
            x = [4. / g["headway_seconds"] for g in groups]
            y = [g["metrics"][key]["mean"] for g in groups]
            axis.plot(x, [float("nan") if v is None else v for v in y], "o-", label=method.replace("_", " "))
            if key == "collision_count":
                unsafe = [g["metrics"]["blocked_zone_violation_count"]["mean"] for g in groups]
                axis.plot(x, [float("nan") if v is None else v for v in unsafe], "x--",
                    label=method.replace("_", " ") + " blocked-zone violations")
        axis.set(xlabel="Scheduled demand intensity (vehicles/s across four approaches)", ylabel=ylabel)
        axis.grid(alpha=.25)
        axis.legend(fontsize=8)
        axis.set_title(data["evidence_classification"].replace("_", " "), fontsize=10)
        fig.savefig(latest / "plots" / f"{key}.png", dpi=180)
        fig.savefig(latest / "plots" / f"{key}.svg")
        plt.close(fig)
    headers = ("Scenario", "Method", "n", "Classifications", "TTT (vehicle s)", "Travel mean (s)",
        "Throughput (veh/min)", "Completion", "Wait mean (s)", "Wait p95 (s)", "Wait max (s)",
        "Approach gap (s)", "FCFS inversion rate", "Max live", "Max negotiators")
    keys = ("total_team_travel_time_seconds", "mean_travel_time_seconds", "throughput_vehicles_per_minute",
        "completion_rate", "mean_waiting_time_seconds", "p95_waiting_time_seconds",
        "maximum_waiting_time_seconds", "approach_waiting_time_gap_seconds",
        "conflicting_pair_fcfs_inversion_rate", "maximum_simultaneous_active_vehicles", "maximum_negotiation_participants")
    rows = [(g["scenario_id"], g["method"], g["episode_count"], str(g["classifications"])) + tuple(
        g["metrics"][k]["mean"] for k in keys) for g in data["groups"]]
    comparison = table(headers, rows)
    paper = "# Paper tables\n\n" + data["evidence_classification"] + "\n\n" + comparison
    paper += "\n\n## Per-approach mean stopped wait (s)\n\n" + table(("Scenario", "Method", "N", "E", "S", "W"), [
        (g["scenario_id"], g["method"]) + tuple(g["per_approach_mean_waiting_time_seconds"][a]["mean"] for a in "NESW") for g in data["groups"]])
    paper += "\n\n## All statistics (across per-episode values)\n\n" + table(
        ("Scenario", "Method", "Metric", "n", "Mean", "Median", "Sample SD", "95% CI of mean"),
        [(g["scenario_id"], g["method"], k, s["n"], s["mean"], s["median"], s["standard_deviation"], s["ci95"])
         for g in data["groups"] for k, s in g["metrics"].items()])
    paper += "\n\n## Paired differences (proposed minus baseline)\n\n" + table(
        ("Scenario", "Baseline", "Metric", "Paired n", "Mean difference", "95% CI"),
        [(p["scenario_id"], p["baseline"], k + " (%)", s["n"], s["mean"], s["ci95"])
         for p in data["paired_comparisons"] for k, s in p["relative_difference_percent"].items()] + [
        (p["scenario_id"], p["baseline"], "completion (percentage points)",
         p["completion_rate_difference_percentage_points"]["n"], p["completion_rate_difference_percentage_points"]["mean"],
         p["completion_rate_difference_percentage_points"]["ci95"]) for p in data["paired_comparisons"]])
    proposed = [r for r in records if r["method"] == "PROPOSED_MAPPO" and r["classification"] != "INVALID_EXPERIMENT"]
    from .aggregation import summary
    card_value = lambda key: fmt(summary(r["metrics"].get(key) for r in proposed)["mean"])
    cards = {"Safety": f"{data['collision_free_episodes']}/{data['episode_count']} collision-free episodes; {data['blocked_zone_violation_count']} blocked-zone violations",
        "Efficiency": f"Proposed episode averages: TTT {card_value('total_team_travel_time_seconds')} vehicle s; travel {card_value('mean_travel_time_seconds')} s; throughput {card_value('throughput_vehicles_per_minute')} veh/min",
        "Fairness": f"Proposed episode averages: wait {card_value('mean_waiting_time_seconds')} s; max {card_value('maximum_waiting_time_seconds')} s; p95 {card_value('p95_waiting_time_seconds')} s; approach gap {card_value('approach_waiting_time_gap_seconds')} s; inversion {card_value('conflicting_pair_fcfs_inversion_rate')}",
        "Scalability": f"Proposed episode averages: completion {card_value('completion_rate')}; max live {card_value('maximum_simultaneous_active_vehicles')}; max negotiators {card_value('maximum_negotiation_participants')}",
        "Architecture": f"Ego-local: {data['decentralized_execution']}; critic calls: {data['centralized_critic_runtime_calls']}; unchanged policy: {data['policy_hash_unchanged']}"}
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
    md = f"# Final quantitative evaluation\n\n**{data['evidence_classification']}**\n\n{data['scope']}\n\n"
    md += f"{data['collision_count']} collisions observed in {data['episode_count']} evaluation episodes. Unsafe episode rate: {fmt(data['unsafe_episode_rate'])}.\n\n"
    md += "\n\n".join(f"**{k}:** {v}" for k, v in cards.items()) + "\n\n" + comparison + "\n\n" + notes
    md += "\n\n## Every episode and replay\n\n" + table(("Run", "Method", "Scenario", "Seed", "Classification", "Error", "Replay command"), [
        tuple(r[k] for k in ("run_id", "method", "scenario_id", "seed", "classification", "error", "replay_command")) for r in records])
    md += "\n\n## Controlled message faults\n\n" + (table(("Fault", "Permission", "Attempted entry rejected", "Passed"), [
        (r["fault"], r["permission"], r["blocked_entry_rejected"], r["passed"]) for r in fault_data["tests"]]) if fault_data else "N/A: not executed")
    for key, ylabel in PLOTS:
        md += f"\n\n![{ylabel}](plots/{key}.png)"
    (latest / "PANEL_EVALUATION_REPORT.md").write_text(md, encoding="utf-8")
    (latest / "PAPER_TABLES.md").write_text(paper, encoding="utf-8")
    # HTML is standalone and escapes every archived string; no live computation.
    def html_table(headers, rows):
        return "<div class='scroll'><table><thead><tr>" + "".join(f"<th>{html.escape(x)}</th>" for x in headers) + "</tr></thead><tbody>" + "".join(
            "<tr>" + "".join(f"<td>{html.escape(fmt(x))}</td>" for x in row) + "</tr>" for row in rows) + "</tbody></table></div>"
    content = "<!doctype html><html lang='en'><meta charset='utf-8'><title>Final evaluation</title><style>body{font:15px Arial;margin:32px;color:#182b3a;line-height:1.5;max-width:1500px}h1,h2{color:#153b57}.cards{display:flex;flex-wrap:wrap;gap:16px}.card{border:1px solid #ccd6df;padding:16px;max-width:260px}.scroll{overflow:auto}table{border-collapse:collapse;font-size:13px}th,td{padding:9px;border:1px solid #d3dbe2;text-align:left}th{background:#eef3f7}img{max-width:750px;width:100%}code{word-break:break-all}</style>"
    content += f"<h1>Final quantitative evaluation</h1><h2>{html.escape(data['evidence_classification'])}</h2><p>{html.escape(data['scope'])}</p>"
    content += f"<p>{data['collision_count']} collisions observed in {data['episode_count']} evaluation episodes. Unsafe episode rate: {fmt(data['unsafe_episode_rate'])}. Integrity valid for all episodes: {data['integrity_all_valid']}.</p>"
    content += "<div class='cards'>" + "".join(f"<div class='card'><strong>{k}</strong><p>{html.escape(v)}</p></div>" for k, v in cards.items()) + "</div><h2>Method comparison</h2>" + html_table(headers, rows)
    content += "<h2>Definitions and limits</h2><p>" + html.escape(notes) + "</p><p>Out of scope: " + html.escape(", ".join(data["out_of_scope"])) + "</p>"
    for key, ylabel in PLOTS:
        content += f"<h2>{html.escape(ylabel)}</h2><img src='plots/{key}.png' alt='{html.escape(ylabel)}'>"
    content += "<h2>Every episode, failure and safe degradation</h2>" + html_table(("Run", "Method", "Scenario", "Seed", "Classification", "Error", "Replay command"), [
        tuple(r[k] for k in ("run_id", "method", "scenario_id", "seed", "classification", "error", "replay_command")) for r in records])
    content += "<h2>Controlled message faults</h2>" + (html_table(("Fault", "Permission", "Entry rejected", "Passed"), [
        (r["fault"], r["permission"], r["blocked_entry_rejected"], r["passed"]) for r in fault_data["tests"]]) if fault_data else "<p>N/A: not executed</p>")
    content += "<p><a href='PAPER_TABLES.md'>Full statistical and paired comparison tables</a></p></html>"
    (latest / "PANEL_EVALUATION_REPORT.html").write_text(content, encoding="utf-8")
    print("Report:", latest / "PANEL_EVALUATION_REPORT.html")
    return data
