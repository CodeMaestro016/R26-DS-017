"""Read recorded evidence; plots show measured points only, never interpolation."""
import html
import json
from pathlib import Path
from .cases import CASES
from .models import ROOT, read_manifest, records, digest, file_hash, write_json

STORY = ("This seven-point targeted scalability study evaluates how system behaviour changes as traffic load increases from 4 to 40 scheduled vehicles under the same intersection, policy, rules and deterministic demand family. It identifies simulation-level observations and limitations, not a statistically universal capacity limit. One episode per load provides no confidence intervals or repeatability estimate.")

def interpretation(rows):
    measured = [r for r in rows if r.get("run_id")]
    valid = [r for r in measured if r["classification"] != "INVALID_EXPERIMENT"]
    text = []
    prefix = []
    for row in rows:
        if row["classification"] != "PASS":
            break
        prefix.append(row["count"])
    if prefix:
        text.append(f"Full completion was observed at every tested load through {prefix[-1]} vehicles.")
    elif measured:
        text.append("No contiguous fully completing operating range from the smallest load has been established.")
    for verdict, label in (("SAFE_DEGRADATION","liveness degradation"),("UNSAFE_FAILURE","an unsafe event"),("NETWORK_CAPACITY_LIMIT","a demonstrable primary network insertion limit"),("INVALID_EXPERIMENT","invalid or interrupted evidence")):
        found = [r["count"] for r in measured if r["classification"] == verdict]
        if found:
            text.append(f"First observed {label} at {min(found)} scheduled vehicles among measured points.")
    if valid and all(not r["metrics"].get("collision_count",0) and not r["metrics"].get("blocked_zone_violation_count",0) for r in valid):
        text.append(f"Zero collisions and blocked-zone violations were recorded in {len(valid)} valid scientific episodes; this does not prove universal safety.")
    if len(measured) < len(CASES):
        text.append(f"Study incomplete: {len(measured)}/7 scientific cases recorded. Preflight is excluded from trends.")
    text.append("No exact capacity threshold between tested points is inferred. Incomplete waits and travel exposure are censored; read them with stop time, insertion and completion counts.")
    return text

def build_payload(root=ROOT):
    frozen = read_manifest(root)
    by_id = {r["scenario_id"]:r for r in records(root)}
    rows = [dict(case_id=c.case_id,count=c.count,classification="NOT_RUN",metrics={}) if c.case_id not in by_id else dict(by_id[c.case_id],case_id=c.case_id,count=c.count) for c in CASES]
    path = Path(root)/"preflight/latest.json"
    return dict(evidence_family="SCALABILITY_VALIDATION_V1", manifest_hash=frozen["manifest_hash"],
        scope=STORY, rows=rows, interpretation=interpretation(rows),
        preflight=json.loads(path.read_text()) if path.exists() else None,
        scientific_episodes_recorded=sum(bool(r.get("run_id")) for r in rows),
        policy_sha256=frozen["manifest"]["policy_sha256"])

def fmt(value):
    if value is None:
        return "N/A"
    return f"{value:.3f}" if isinstance(value,float) else str(value)

def plots(rows, destination):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    charts = (
        ("completion", "Completion rate among scheduled", "completion_rate_among_scheduled"),
        ("mean_wait", "Mean observed incoming wait (s)", "mean_waiting_time_seconds"),
        ("max_wait", "Maximum observed incoming wait (s)", "maximum_waiting_time_seconds"),
        ("throughput", "Completed vehicles / simulated minute", "throughput_vehicles_per_minute"),
        ("active_queue", "Maximum active traffic / incoming queue", "maximum_simultaneous_active_vehicles"),
        ("mappo", "MAPPO inference calls", "mappo_inference_call_count"),
        ("fallback", "Fallback fraction of MAPPO events", "fallback_rate"))
    result = []
    destination.mkdir(parents=True,exist_ok=True)
    for name,label,key in charts:
        fig,ax = plt.subplots(figsize=(6.4,3.8),layout="constrained")
        eligible = [r for r in rows if r.get("run_id") and r["classification"] != "INVALID_EXPERIMENT" and r["metrics"].get(key) is not None]
        if eligible:
            ax.scatter([r["count"] for r in eligible],[r["metrics"][key] for r in eligible],label="Recorded observation",marker="o")
            if name == "active_queue":
                ax.scatter([r["count"] for r in eligible],[sum(r["metrics"].get("maximum_per_approach_queue_depth",{}).values()) for r in eligible],marker="x",label="Sum of per-approach maximum queues (not necessarily simultaneous)")
            ax.legend(fontsize=7)
        else:
            ax.text(.5,.5,"No scientific measurements available",ha="center",transform=ax.transAxes)
        ax.set(xlabel="Scheduled vehicle count",ylabel=label,xticks=[c.count for c in CASES])
        ax.grid(alpha=.2)
        path = destination/(name+".png")
        fig.savefig(path,dpi=130)
        plt.close(fig)
        result.append(path.name)
    return result

def report(root=ROOT):
    payload = build_payload(root)
    latest = Path(root)/"latest"
    latest.mkdir(parents=True,exist_ok=True)
    images = plots(payload["rows"],latest/"plots")
    columns = ("Load","Scheduled","Spawned","Completed","Completion %","Collisions","Blocked violations","Mean wait","Max wait","Throughput","MAPPO calls","Fallback %","Result")
    values = []
    for r in payload["rows"]:
        m = r["metrics"]
        percentage = lambda key: m[key]*100 if m.get(key) is not None else None
        values.append([r["case_id"],r["count"],m.get("successfully_spawned_vehicle_count"),m.get("total_vehicles_completed"),percentage("completion_rate_among_scheduled"),m.get("collision_count"),m.get("blocked_zone_violation_count"),m.get("mean_waiting_time_seconds"),m.get("maximum_waiting_time_seconds"),m.get("throughput_vehicles_per_minute"),m.get("mappo_inference_call_count"),percentage("fallback_rate"),r["classification"]])
    table = "<table><tr>"+"".join(f"<th>{html.escape(c)}</th>" for c in columns)+"</tr>"+"".join("<tr>"+"".join(f"<td>{html.escape(fmt(x))}</td>" for x in row)+"</tr>" for row in values)+"</table>"
    md = ["# Scalability / Operational Boundary",STORY,"Manifest: `"+payload["manifest_hash"]+"`", "Scientific episodes recorded: "+str(payload["scientific_episodes_recorded"])+"/7 (preflight excluded).", "## Operational Boundary Observation",*payload["interpretation"],"| "+" | ".join(columns)+" |","|"+"---|"*len(columns)]
    md += ["| "+" | ".join(fmt(x) for x in row)+" |" for row in values]
    detail = []
    excluded = {"vehicle_measurements","native_emergency_braking_evidence","collision_evidence"}
    for r in payload["rows"]:
        if not r.get("run_id"):
            continue
        lines = [f"## {r['case_id']} measured evidence", "Run: "+r["run_id"], "| Metric | Value |","|---|---|"]
        items = {**{k:v for k,v in r["metrics"].items() if k not in excluded},**{"integrity."+k:v for k,v in r["integrity"].items()}}
        lines += ["| "+k+" | "+(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else fmt(v))+" |" for k,v in items.items()]
        md.extend(lines)
        detail.append(f"<h2>{r['case_id']} measured evidence</h2><p>Run: {r['run_id']}</p><table><tr><th>Metric</th><th>Value</th></tr>"+"".join("<tr><td>"+html.escape(k)+"</td><td>"+html.escape(json.dumps(v,sort_keys=True) if isinstance(v,(dict,list)) else fmt(v))+"</td></tr>" for k,v in items.items())+"</table>")
    preflight = ""
    if payload["preflight"]:
        preflight = "<h2>Preflight — excluded from scientific results</h2><pre>"+html.escape(json.dumps(payload["preflight"],indent=2))+"</pre>"
        md.extend(["## PREFLIGHT_NOT_SCIENTIFIC_RESULT", "```json", json.dumps(payload["preflight"],indent=2), "```"])
    md += ["## Measured-point plots"]+[f"![{name}](plots/{name})" for name in images]
    page = '<!doctype html><html><head><meta charset="utf-8"><title>Scalability Evaluation</title><style>body{font:15px system-ui;margin:32px;color:#183047}table{border-collapse:collapse;max-width:100%;font-size:12px}td,th{padding:7px;border:1px solid #cad4de;text-align:left;overflow-wrap:anywhere}pre{white-space:pre-wrap}img{width:min(640px,100%)}</style></head><body><h1>Scalability / Operational Boundary</h1><p>'+html.escape(STORY)+"</p><p>Manifest: "+payload["manifest_hash"]+"</p><h2>Operational Boundary Observation</h2>"+"".join("<p>"+html.escape(t)+"</p>" for t in payload["interpretation"])+table+"".join(f'<p><img src="plots/{name}" alt="{name}"></p>' for name in images)+"".join(detail)+preflight+"</body></html>"
    (latest/"SCALABILITY_REPORT.md").write_text("\n\n".join(md),encoding="utf-8")
    (latest/"SCALABILITY_REPORT.html").write_text(page,encoding="utf-8")
    write_json(latest/"scalability_summary.json",payload)
    write_json(latest/"scalability_summary.sha256.json",dict(summary_hash=digest(payload)))
    write_json(latest/"report_artifacts.json",{p.name:file_hash(p) for p in (latest/"plots").glob("*.png")})
    return payload
