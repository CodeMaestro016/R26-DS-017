"""Read recorded evidence; plots show measured points only, never interpolation."""
# Import html for use in this module.
import html
# Import json for use in this module.
import json
# Import Path from pathlib for the operations below.
from pathlib import Path
# Import CASES from .cases for the operations below.
from .cases import CASES
# Import ROOT, read_manifest, records, digest, file_hash, write_json, protect from .models for the operations
# below.
from .models import ROOT, read_manifest, records, digest, file_hash, write_json, protect

# Set STORY to the text 'SCALABILITY_VALIDATION_V2 uses fixed 0.4-second staggered...'.
STORY = ("SCALABILITY_VALIDATION_V2 uses fixed 0.4-second staggered NESW round-robin departures and unchanged V1 legal movements. This avoids identical initial requested departure times; it does not guarantee separated junction arrivals or prevent deadlock. The seven-point targeted study varies total scheduled vehicles from 4 to 40 under the same intersection, policy, rules and demand-prefix family. V1 remains separate historical evidence. One episode per load provides no confidence intervals or universal capacity estimate.")

# Interpretation using the inputs and processing steps below.
# Input rows: the supplied rows.
# Output: text.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def interpretation(rows):
    # Set measured to a list of r for r in rows; retain entries satisfying 'run_id' from r; use None if absent.
    measured = [r for r in rows if r.get("run_id")]
    # Set valid to a list of r for r in measured; retain entries satisfying r at 'classification' differs from the
    # text 'INVALID_EXPERIMENT'.
    valid = [r for r in measured if r["classification"] != "INVALID_EXPERIMENT"]
    # Set text to an empty list.
    text = []
    # Set prefix to an empty list.
    prefix = []
    # Iterate over rows, binding each item to row.
    for row in rows:
        # Run this branch when row at 'classification' differs from the text 'PASS'.
        if row["classification"] != "PASS":
            # Leave the nearest enclosing loop immediately.
            break
        # Append row at 'count' to prefix.
        prefix.append(row["count"])
    # Run this branch when prefix.
    if prefix:
        # Append formatted text built from the embedded values to text.
        text.append(f"Full completion was observed at every tested load through {prefix[-1]} vehicles.")
    # Run this branch when measured.
    elif measured:
        # Append the text 'No contiguous fully completing operating range from the...' to text.
        text.append("No contiguous fully completing operating range from the smallest load has been established.")
    # Iterate over a tuple containing a tuple containing the text 'SAFE_DEGRADATION', the text 'liveness
    # degradation', a tuple containing the..., binding each item to (verdict, label).
    for verdict, label in (("SAFE_DEGRADATION","liveness degradation"),("UNSAFE_FAILURE","an unsafe event"),("NETWORK_CAPACITY_LIMIT","a demonstrable primary network insertion limit"),("INVALID_EXPERIMENT","invalid or interrupted evidence")):
        # Set found to a list of r at 'count' for r in measured; retain entries satisfying r at 'classification'
        # equals verdict.
        found = [r["count"] for r in measured if r["classification"] == verdict]
        # Run this branch when found.
        if found:
            # Append formatted text built from the embedded values to text.
            text.append(f"First observed {label} at {min(found)} scheduled vehicles among measured points.")
    # Run this branch when valid and whether every item is true in a lazy sequence of not
    # r['metrics'].get('collision_count', 0) and not r['metrics'].get('blocked_zone_violation_count', 0) for r in
    # valid.
    if valid and all(not r["metrics"].get("collision_count",0) and not r["metrics"].get("blocked_zone_violation_count",0) for r in valid):
        # Append formatted text built from the embedded values to text.
        text.append(f"Zero collisions and blocked-zone violations were recorded in {len(valid)} valid scientific episodes; this does not prove universal safety.")
    # Run this branch when the number of entries in measured is less than the number of entries in CASES.
    if len(measured) < len(CASES):
        # Append formatted text built from the embedded values to text.
        text.append(f"Study incomplete: {len(measured)}/7 scientific cases recorded. Preflight is excluded from trends.")
    # Append the text 'No exact capacity threshold between tested points is...' to text.
    text.append("No exact capacity threshold between tested points is inferred. Incomplete waits and travel exposure are censored; read them with stop time, insertion and completion counts.")
    # Return text to the caller.
    return text

# Build payload using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: a dictionary built from the supplied values.
def build_payload(root=ROOT):
    # Set frozen to the result of read_manifest(root).
    frozen = read_manifest(root)
    # Set by_id to a dictionary of r at 'scenario_id' mapped to r for r in the result of records(root).
    by_id = {r["scenario_id"]:r for r in records(root)}
    # Set rows to a list of a dictionary built from the supplied values when c.case_id does not belong to by_id,
    # otherwise a dictionary built from by_id at c.case_id for c in CASES.
    rows = [dict(case_id=c.case_id,count=c.count,classification="NOT_RUN",metrics={}) if c.case_id not in by_id else dict(by_id[c.case_id],case_id=c.case_id,count=c.count) for c in CASES]
    # Set path to the result of Path(root) joined with the path segment 'preflight/latest.json'.
    path = Path(root)/"preflight/latest.json"
    # Return a dictionary built from the supplied values to the caller.
    return dict(evidence_family="SCALABILITY_VALIDATION_V2", manifest_hash=frozen["manifest_hash"],
        # Supply scope as STORY.
        # Supply rows as rows.
        # Supply interpretation as the result of interpretation(rows).
        scope=STORY, rows=rows, interpretation=interpretation(rows),
        # Supply preflight as the decoded data produced by json.loads from the text read from path when whether
        # path exists, otherwise None.
        preflight=json.loads(path.read_text()) if path.exists() else None,
        # Supply scientific_episodes_recorded as the sum of a lazy sequence of a Boolean built from 'run_id' from
        # r; use None if absent for r in rows.
        scientific_episodes_recorded=sum(bool(r.get("run_id")) for r in rows),
        # Supply policy_sha256 as frozen['manifest'] at 'policy_sha256'.
        policy_sha256=frozen["manifest"]["policy_sha256"])

# Fmt using the inputs and processing steps below.
# Input value: the supplied value.
# Output: return the value selected by the matching return branch below.
# Processing: select branches using the stated conditions.
def fmt(value):
    # Run this branch when value is the same object as None.
    if value is None:
        # Return the text 'N/A' to the caller.
        return "N/A"
    # Return formatted text built from the embedded values when whether value has type float, otherwise a string
    # built from value to the caller.
    return f"{value:.3f}" if isinstance(value,float) else str(value)

# Plots using the inputs and processing steps below.
# Input rows: the supplied rows.
# Input destination: the supplied destination.
# Output: result.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def plots(rows, destination):
    # Import matplotlib for use in this module.
    import matplotlib
    # Call matplotlib.use with the supplied arguments.
    matplotlib.use("Agg")
    # Import matplotlib.pyplot as plt for use in this module.
    import matplotlib.pyplot as plt
    # Set charts to a tuple containing a tuple containing the text 'completion', the text 'Completion rate among
    # scheduled', the text...
    charts = (
        # Include a tuple containing the text 'completion', the text 'Completion rate among scheduled', the text
        # 'completion_rate_among_scheduled' in this tuple.
        ("completion", "Completion rate among scheduled", "completion_rate_among_scheduled"),
        # Include a tuple containing the text 'mean_wait', the text 'Mean observed incoming wait (s)', the text
        # 'mean_waiting_time_seconds' in this tuple.
        ("mean_wait", "Mean observed incoming wait (s)", "mean_waiting_time_seconds"),
        # Include a tuple containing the text 'max_wait', the text 'Maximum observed incoming wait (s)', the text
        # 'maximum_waiting_time_seconds' in this tuple.
        ("max_wait", "Maximum observed incoming wait (s)", "maximum_waiting_time_seconds"),
        # Include a tuple containing the text 'throughput', the text 'Completed vehicles / simulated minute', the
        # text... in this tuple.
        ("throughput", "Completed vehicles / simulated minute", "throughput_vehicles_per_minute"),
        # Include a tuple containing the text 'active_queue', the text 'Maximum active traffic / incoming queue',
        # the text... in this tuple.
        ("active_queue", "Maximum active traffic / incoming queue", "maximum_simultaneous_active_vehicles"),
        # Include a tuple containing the text 'mappo', the text 'MAPPO inference calls', the text
        # 'mappo_inference_call_count' in this tuple.
        ("mappo", "MAPPO inference calls", "mappo_inference_call_count"),
        # Include a tuple containing the text 'fallback', the text 'Fallback fraction of MAPPO events', the text
        # 'fallback_rate' in this tuple.
        ("fallback", "Fallback fraction of MAPPO events", "fallback_rate"))
    # Set result to an empty list.
    result = []
    # Create the directory requested by destination.
    destination.mkdir(parents=True,exist_ok=True)
    # Iterate over charts, binding each item to (name, label, key).
    for name,label,key in charts:
        # Set (fig, ax) to the result of plt.subplots().
        fig,ax = plt.subplots(figsize=(6.4,3.8),layout="constrained")
        # Set eligible to a list of r for r in rows; retain entries satisfying 'run_id' from r; use None if absent
        # and r at 'classification' differs from the text...
        eligible = [r for r in rows if r.get("run_id") and r["classification"] != "INVALID_EXPERIMENT" and r["metrics"].get(key) is not None]
        # Run this branch when eligible.
        if eligible:
            # Call ax.scatter with the supplied arguments.
            ax.scatter([r["count"] for r in eligible],[r["metrics"][key] for r in eligible],label="Recorded observation",marker="o")
            # Run this branch when name equals the text 'active_queue'.
            if name == "active_queue":
                # Call ax.scatter with the supplied arguments.
                ax.scatter([r["count"] for r in eligible],[sum(r["metrics"].get("maximum_per_approach_queue_depth",{}).values()) for r in eligible],marker="x",label="Sum of per-approach maximum queues (not necessarily simultaneous)")
            # Call ax.legend with the supplied arguments.
            ax.legend(fontsize=7)
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Call ax.text with the supplied arguments.
            ax.text(.5,.5,"No scientific measurements available",ha="center",transform=ax.transAxes)
        # Call ax.set with the supplied arguments.
        ax.set(xlabel="Scheduled vehicle count",ylabel=label,xticks=[c.count for c in CASES])
        # Call ax.grid with the supplied arguments.
        ax.grid(alpha=.2)
        # Set path to destination divided by name plus the text '.png'.
        path = destination/(name+".png")
        # Call fig.savefig with the supplied arguments.
        fig.savefig(path,dpi=130)
        # Call plt.close with the supplied arguments.
        plt.close(fig)
        # Append path.name to result.
        result.append(path.name)
    # Return result to the caller.
    return result

# Report using the inputs and processing steps below.
# Input root: the base directory used to resolve files.
# Output: payload.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def report(root=ROOT):
    # Call protect with the supplied arguments.
    protect(root)
    # Set payload to the result of build_payload(root).
    payload = build_payload(root)
    # Set latest to the result of Path(root) joined with the path segment 'latest'.
    latest = Path(root)/"latest"
    # Create the directory requested by latest.
    latest.mkdir(parents=True,exist_ok=True)
    # Set images to the result of plots(payload at 'rows', latest joined with the path segment 'plots').
    images = plots(payload["rows"],latest/"plots")
    # Set columns to a tuple containing the text 'Load', the text 'Scheduled', the text 'Spawned', the text
    # 'Completed', the text 'Completion %',...
    columns = ("Load","Scheduled","Spawned","Completed","Completion %","Collisions","Blocked violations","Mean wait","Max wait","Throughput","MAPPO calls","Fallback %","Result")
    # Set values to an empty list.
    values = []
    # Iterate over payload at 'rows', binding each item to r.
    for r in payload["rows"]:
        # Set m to r at 'metrics'.
        m = r["metrics"]
        # Set percentage to a callback that returns m at key multiplied by 100 when key from m; use None if absent
        # is a different object from None, otherwise None.
        percentage = lambda key: m[key]*100 if m.get(key) is not None else None
        # Append a list containing r at 'case_id', r at 'count', 'successfully_spawned_vehicle_count' from m; use
        # None if absent,... to values.
        values.append([r["case_id"],r["count"],m.get("successfully_spawned_vehicle_count"),m.get("total_vehicles_completed"),percentage("completion_rate_among_scheduled"),m.get("collision_count"),m.get("blocked_zone_violation_count"),m.get("mean_waiting_time_seconds"),m.get("maximum_waiting_time_seconds"),m.get("throughput_vehicles_per_minute"),m.get("mappo_inference_call_count"),percentage("fallback_rate"),r["classification"]])
    # Set table to '<table><tr>' plus ''.join((f'<th>{html.escape(c)}</th>' for c in columns)) plus the text
    # '</tr>' plus the result of ''.join(a lazy sequence of '<tr>' + ''.join((f'<td>{html.escape(fmt(x))}</td>'
    # for x in row)) + '</tr>'...) plus the text '</table>'.
    table = "<table><tr>"+"".join(f"<th>{html.escape(c)}</th>" for c in columns)+"</tr>"+"".join("<tr>"+"".join(f"<td>{html.escape(fmt(x))}</td>" for x in row)+"</tr>" for row in values)+"</table>"
    # Set md to a list containing the text '# Scalability / Operational Boundary', STORY, the text 'Manifest: `'
    # plus payload at...
    md = ["# Scalability / Operational Boundary",STORY,"Manifest: `"+payload["manifest_hash"]+"`", "Scientific episodes recorded: "+str(payload["scientific_episodes_recorded"])+"/7 (preflight excluded).", "## Operational Boundary Observation",*payload["interpretation"],"| "+" | ".join(columns)+" |","|"+"---|"*len(columns)]
    # Update md to its current value plus a list of the text '|' plus the result of ' | '.join((fmt(x) for x in
    # row)) plus the text '|' for row in values.
    md += ["| "+" | ".join(fmt(x) for x in row)+" |" for row in values]
    # Set detail to an empty list.
    detail = []
    # Set excluded to a set containing the text 'vehicle_measurements', the text
    # 'native_emergency_braking_evidence', the text 'collision_evidence'.
    excluded = {"vehicle_measurements","native_emergency_braking_evidence","collision_evidence"}
    # Iterate over payload at 'rows', binding each item to r.
    for r in payload["rows"]:
        # Run this branch when the negation of 'run_id' from r; use None if absent.
        if not r.get("run_id"):
            # Skip the rest of this loop iteration and process the next item.
            continue
        # Set lines to a list containing formatted text built from the embedded values, the text 'Run:' plus r at
        # 'run_id', the text '| Metric |...
        lines = [f"## {r['case_id']} measured evidence", "Run: "+r["run_id"], "| Metric | Value |","|---|---|"]
        # Set items to a dictionary of the supplied entries.
        items = {**{k:v for k,v in r["metrics"].items() if k not in excluded},**{"integrity."+k:v for k,v in r["integrity"].items()}}
        # Update lines to its current value plus a list of '| ' + k plus ' | ' plus json.dumps(v, sort_keys=True)
        # when isinstance(v, (dict, list)), otherwise fmt(v) plus the text '|' for (k, v) in key/value pairs from
        # items.
        lines += ["| "+k+" | "+(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else fmt(v))+" |" for k,v in items.items()]
        # Extend md with lines.
        md.extend(lines)
        # Append formatted text built from the embedded values plus the result of ''.join(a lazy sequence of
        # '<tr><td>' + html.escape(k) + '</td><td>' + html.escape(json.dumps(v,...) plus the text '</table>' to
        # detail.
        detail.append(f"<h2>{r['case_id']} measured evidence</h2><p>Run: {r['run_id']}</p><table><tr><th>Metric</th><th>Value</th></tr>"+"".join("<tr><td>"+html.escape(k)+"</td><td>"+html.escape(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else fmt(v))+"</td></tr>" for k,v in items.items())+"</table>")
    # Set preflight to the text ''.
    preflight = ""
    # Run this branch when payload at 'preflight'.
    if payload["preflight"]:
        # Set preflight to the text '<h2>Preflight — excluded from scientific results</h2><pre>' plus the result
        # of html.escape(the serialized data produced by json.dumps) plus the text '</pre>'.
        preflight = "<h2>Preflight — excluded from scientific results</h2><pre>"+html.escape(json.dumps(payload["preflight"],indent=2))+"</pre>"
        # Extend md with a list containing the text '## PREFLIGHT_NOT_SCIENTIFIC_RESULT', the text '```json', the
        # serialized data produced by...
        md.extend(["## PREFLIGHT_NOT_SCIENTIFIC_RESULT", "```json", json.dumps(payload["preflight"],indent=2), "```"])
    # Update md to its current value plus a list containing the text '## Measured-point plots' plus a list of
    # formatted text built from the embedded values for name in images.
    md += ["## Measured-point plots"]+[f"![{name}](plots/{name})" for name in images]
    # Set page to '<!doctype html><html><head><meta charset="utf-8"><title>Scalability... plus ''.join((f'<p><img
    # src="plots/{name}" alt="{name}"></p>' for name in images)) plus the result of ''.join(detail) plus preflight
    # plus the text '</body></html>'.
    page = '<!doctype html><html><head><meta charset="utf-8"><title>Scalability Evaluation</title><style>body{font:15px system-ui;margin:32px;color:#183047}table{border-collapse:collapse;max-width:100%;font-size:12px}td,th{padding:7px;border:1px solid #cad4de;text-align:left;overflow-wrap:anywhere}pre{white-space:pre-wrap}img{width:min(640px,100%)}</style></head><body><h1>Scalability / Operational Boundary</h1><p>'+html.escape(STORY)+"</p><p>Manifest: "+payload["manifest_hash"]+"</p><h2>Operational Boundary Observation</h2>"+"".join("<p>"+html.escape(t)+"</p>" for t in payload["interpretation"])+table+"".join(f'<p><img src="plots/{name}" alt="{name}"></p>' for name in images)+"".join(detail)+preflight+"</body></html>"
    # Keep consecutive table rows adjacent for valid Markdown tables.
    # Set markdown to the text ''.
    markdown = ""
    # Iterate over md, binding each item to line.
    for line in md:
        # Update markdown to its current value plus the text '' when the result of line.startswith('|') and the
        # result of markdown.rstrip().split('\n')[-1].startswith('|'), otherwise the text '' plus line.
        markdown += ("\n" if line.startswith("|") and markdown.rstrip().split("\n")[-1].startswith("|") else "\n\n") + line
    # Write the supplied text to (latest / 'SCALABILITY_REPORT.md').
    (latest/"SCALABILITY_REPORT.md").write_text(markdown.lstrip(),encoding="utf-8")
    # Write the supplied text to (latest / 'SCALABILITY_REPORT.html').
    (latest/"SCALABILITY_REPORT.html").write_text(page,encoding="utf-8")
    # Call write_json with the supplied arguments.
    write_json(latest/"scalability_summary.json",payload)
    # Call write_json with the supplied arguments.
    write_json(latest/"scalability_summary.sha256.json",dict(summary_hash=digest(payload)))
    # Call write_json with the supplied arguments.
    write_json(latest/"report_artifacts.json",{p.name:file_hash(p) for p in (latest/"plots").glob("*.png")})
    # Return payload to the caller.
    return payload
