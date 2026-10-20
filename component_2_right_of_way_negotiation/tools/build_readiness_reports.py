"""Build separate readiness documents from the audited archive, never official results."""
# Import json for use in this module.
import json
# Import statistics for use in this module.
import statistics
# Import Counter from collections for the operations below.
from collections import Counter
# Import Path from pathlib for the operations below.
from pathlib import Path

# Set BASE to Path(__file__).resolve().parents at 1.
BASE=Path(__file__).resolve().parents[1]
# Set OUT to BASE joined with the path segment 'results/final_readiness/20261016'.
OUT=BASE/'results/final_readiness/20261016'
# Set DOCS to BASE joined with the path segment 'docs/final_readiness'.
DOCS=BASE/'docs/final_readiness'

# Read using the inputs and processing steps below.
# Input path: the path or path object supplied by the caller.
# Output: the decoded data produced by json.loads from the text read from path.
# Return the decoded data produced by json.loads from the text read from path to the caller.
def read(path):return json.loads(path.read_text(encoding='utf-8-sig'))
# Shown using the inputs and processing steps below.
# Input value: the supplied value.
# Output: the text 'N/A' when value is the same object as None, otherwise a string built from value.
# Return the text 'N/A' when value is the same object as None, otherwise a string built from value to the caller.
def shown(value):return 'N/A' if value is None else str(value)
# Table using the inputs and processing steps below.
# Input headers: the supplied headers.
# Input rows: the supplied rows.
# Output: '| ' + ' | '.join(headers) + ' |\n|' plus '---|' * len(headers) plus the text '' plus the result of
# '\n'.join(a lazy sequence of '| ' + ' | '.join((shown(v).replace('|', '\\|') for v in...
def table(headers,rows):
    # Return '| ' + ' | '.join(headers) + ' |\n|' plus '---|' * len(headers) plus the text '' plus the result of
    # '\n'.join(a lazy sequence of '| ' + ' | '.join((shown(v).replace('|', '\\|') for v in row)) + ' |' for
    # row...) plus the text '' to the caller.
    return '| '+' | '.join(headers)+' |\n|'+'---|'*len(headers)+'\n'+'\n'.join('| '+' | '.join(shown(v).replace('|','\\|') for v in row)+' |' for row in rows)+'\n'
# Save using the inputs and processing steps below.
# Input name: the supplied name.
# Input text: the supplied text.
# Output: no explicit value; normal completion returns None.
def save(name,text):
    # Create the directory requested by DOCS.
    DOCS.mkdir(parents=True,exist_ok=True)
    # Write the supplied text to (DOCS / name).
    (DOCS/name).write_text(text,encoding='utf-8')

# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: iterate over the relevant records, then select branches using the stated conditions.
def main():
    # Set audit to the result of read(OUT joined with the path segment 'initial_audit.json').
    audit=read(OUT/'initial_audit.json')
    # Set family to the next item from a lazy sequence of f for f in audit at 'families'; retain entries
    # satisfying f at 'root' equals the text 'results/final_evaluation'.
    family=next(f for f in audit['families'] if f['root']=='results/final_evaluation')
    # Set final to a list of r for r in family at 'runs'; retain entries satisfying r at 'suite' equals the text
    # 'final' and the negation of r at 'verification_errors'.
    final=[r for r in family['runs'] if r['suite']=='final' and not r['verification_errors']]
    # Set methods to the result of Counter(a lazy sequence of r at 'method' for r in final).
    methods=Counter(r['method'] for r in final)
    # Set missing to the result of Counter(a lazy sequence of key at 2 for key in family at 'missing_final_keys').
    missing=Counter(key[2] for key in family['missing_final_keys'])
    # Set ratios to a list of r at 'wall_clock_seconds' divided by r['metrics'] at
    # 'observed_simulation_time_seconds' for r in final; retain entries satisfying 'wall_clock_seconds' from r;
    # use None if absent and 'observed_simulation_time_seconds'...
    ratios=[r['wall_clock_seconds']/r['metrics']['observed_simulation_time_seconds'] for r in final if r.get('wall_clock_seconds') and r['metrics'].get('observed_simulation_time_seconds',0)>0]
    # Set sizes to a list of the sum of a lazy sequence of p.stat().st_size for p in the result of (BASE /
    # r['path']).parent.iterdir(); retain entries satisfying whether p is an existing file for r in final.
    sizes=[sum(p.stat().st_size for p in (BASE/r['path']).parent.iterdir() if p.is_file()) for r in final]
    # Set observed_max_count to the maximum of a lazy sequence of r['metrics'] at 'total_vehicles_scheduled' for r
    # in final.
    observed_max_count=max(r['metrics']['total_vehicles_scheduled'] for r in final)
    # Set load_factor to the maximum of 1, 32 divided by observed_max_count.
    load_factor=max(1,32/observed_max_count)
    # Set maximum_budget to 62100.
    maximum_budget=62100
    # Set low_hours to maximum_budget multiplied by the result of statistics.median(ratios) divided by 3600.
    low_hours=maximum_budget*statistics.median(ratios)/3600
    # Set high_hours to maximum_budget multiplied by the maximum of ratios multiplied by load_factor divided by
    # 3600.
    high_hours=maximum_budget*max(ratios)*load_factor/3600
    # Set disk_estimate to the maximum of sizes multiplied by load_factor multiplied by 165.
    disk_estimate=max(sizes)*load_factor*165
    # Set traced to an empty list.
    traced=[]
    # Iterate over audit at 'families', binding each item to f.
    for f in audit['families']:
        # Iterate over 'runs' from f; use an empty list if absent, binding each item to r.
        for r in f.get('runs',[]):
            # Set directory to (BASE / r['path']).parent.
            directory=(BASE/r['path']).parent
            # Run this branch when the negation of whether (directory / 'execution_trace.jsonl') is an existing
            # file.
            # Skip the rest of this loop iteration and process the next item.
            if not (directory/'execution_trace.jsonl').is_file():continue
            # Set elapsed to 'observed_simulation_time_seconds' from r['metrics']; use 0 if absent.
            elapsed=r['metrics'].get('observed_simulation_time_seconds',0)
            # Set population to 'total_vehicles_scheduled' from r['metrics']; use 0 if absent.
            population=r['metrics'].get('total_vehicles_scheduled',0)
            # Run this branch when elapsed and population.
            if elapsed and population:
                # Set total to the sum of a lazy sequence of p.stat().st_size for p in the result of
                # directory.iterdir(); retain entries satisfying whether p is an existing file.
                total=sum(p.stat().st_size for p in directory.iterdir() if p.is_file())
                # Append a tuple containing total divided by elapsed multiplied by population, a string built from
                # the result of... to traced.
                traced.append((total/(elapsed*population),str(directory.relative_to(BASE)),total,elapsed,population))
    # Set trace_reference to the maximum of traced.
    trace_reference=max(traced)
    # Set planned_vehicle_seconds to 3 multiplied by 180 multiplied by 2 + 4 + 3 + 4 plus 4 plus 10 multiplied by
    # 8 * 240 + 12 * 300 + 16 * 360 + 24 * 480 plus 32 * 600.
    planned_vehicle_seconds=3*(180*(2+4+3+4+4)+10*(8*240+12*300+16*360+24*480+32*600))
    # Set trace_disk_estimate to trace_reference at 0 multiplied by planned_vehicle_seconds.
    trace_disk_estimate=trace_reference[0]*planned_vehicle_seconds
    # Set rows to an empty list.
    rows=[]
    # Iterate over a list containing the text 'PROPOSED_MAPPO', the text 'RULE_PLUS_FCFS', the text 'RULES_ONLY',
    # binding each item to method.
    for method in ['PROPOSED_MAPPO','RULE_PLUS_FCFS','RULES_ONLY']:
        # Set counts to the result of Counter(a lazy sequence of r at 'classification' for r in final; retain
        # entries satisfying r at 'method'...).
        counts=Counter(r['classification'] for r in final if r['method']==method)
        # Append a list containing method, 55, methods at method, missing at method, counts at 'PASS', counts at
        # 'SAFE_DEGRADATION', counts... to rows.
        rows.append([method,55,methods[method],missing[method],counts['PASS'],counts['SAFE_DEGRADATION'],counts['UNSAFE_FAILURE'],counts['INVALID_EXPERIMENT']])
    # Call save with the supplied arguments.
    save('FINAL_EVALUATION_PREFLIGHT.md',f'''# Final evaluation preflight — 16 October 2026

**BLOCKED; no long-suite approval or execution.** This document is not an
official completed-evaluation report.

## Protocol and exact counts

Archived V1: FINAL_EGO_LOCAL_EVALUATION_V1, manifest
`{family['manifest_hash']}` at `{family['root']}/manifest.json`.
Manifest, result, provenance and demand checksums verify for 34 final records;
**34/165 recorded final episodes; 131 missing**. Recorded episodes are not
equivalent to successful discharge. Nine separate smoke episodes (5 PASS,
4 SAFE_DEGRADATION) are excluded from that count. The saved latest aggregate
describes smoke, not the final archive.

{table(['Method','Expected','Verified final','Missing','PASS','SAFE_DEGRADATION','UNSAFE_FAILURE','INVALID'],rows)}

The complete missing (scenario, seed, method) list is in
`results/final_readiness/20261016/initial_audit.json`, under this family.
No existing record is discarded, relabeled or selected for favorable outcomes.
Seven separate development smoke records fail full archive verification and
are not included in these totals.

Current intended V2: FINAL_EGO_LOCAL_EVALUATION_V2, EGO_ADMISSION_V2 /
PAIR_ORDER_V2_1, scientific SEEDED_STOCHASTIC_MASKED_SAMPLE, demand seeds
1103,2207,3301,4409,5501,6607,7703,8807,9901,11003, unchanged methods and budgets.
Preferred output root is `results/post_training_evaluation/v2_candidate/`.
**No V2 final manifest exists: 0/165 current V2 final episodes, 165 missing.**
The archived V1 uses old seeds 101..1010 and presentation argmax; it must not
be mixed with V2 or resumed through renamed/current code. Python is 3.13.1;
SUMO executable is 1.26.0 (matching archived binary metadata), while installed
TraCI/SUMO Python tools are 1.27.1. Renaming changed live source identities;
source mismatches are not repaired by modifying an old manifest.

## Integrity and acceptance blockers

E5 SHA-256 remains
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
Archived inference guard counters are retained. New full active regression:
848 passed, two existing strict expected liveness failures; no assertions or
xfail markers were weakened. This does not establish accepted complete discharge.

`results/repair_diagnostics/validation_summary.json` explicitly says
ready_for_final_evaluation=false. [REPAIR_V2_AUDIT.md](../REPAIR_V2_AUDIT.md)
states: "Do not prepare or run final V2 while acceptance is pending."
The three stalled diagnostic cases and dense-discharge limitation remain.
No subsequent acceptance record or approved final manifest was found.
Scientific behavior must not be changed without separate impact analysis and
approval. The acceptance gate requires review/resolution before any V2
preparation, followed by explicit approval of the long suite.

## Resume and comparison safeguards

The active runner requires a prepared matching manifest, verifies source and
checkpoint identities, and uses checksum-verified (scenario, seed, method)
keys to reuse every recorded episode, including unfavorable/invalid outcomes.
Duplicate keys are refused. Paired methods use identical frozen generated
demand; physics, speed mode, model assets and budgets are shared. IntegrityGuard
rejects training, backward, optimizer, parameter mutation, critic use and global
physical execution authority. Maximum negotiation participants stays four.

An interrupted directory with provenance but no result is not a completed
episode. The current runner identifies completion through result records and
does not provide a transactional attempt ledger for the final study. Such a
directory must be inventoried and reviewed before any resume; never silently
erase it or call its metrics a success. Source mismatches fail closed.
**The stopped V1 archive is not safe/authorized to resume as current V2.**

## Resource estimates (approximate, not measurements of the missing study)

The seven-/ten-seed planned matrix still has maximum 62,100 simulated seconds.
Using the observed V1 median wall/sim ratio gives roughly {low_hours:.1f} hours
for all budgets. A conservative observed maximum ratio scaled by
32/{observed_max_count} for the largest population gives {high_hours:.1f} hours.
These are planning extrapolations, not reliable bounds: larger populations,
machine load and early stops can change cost substantially. They are not
permission to start the study.

Largest observed final episode directory: {max(sizes)/1024**2:.2f} MiB.
The legacy V1 metadata-only extrapolation is {disk_estimate/1024**3:.2f} GiB,
but **must not be used as V2's required disk reserve**, because V1 did not save
the same per-step traces. Using the maximum observed traced bytes per scheduled
vehicle-second from `{trace_reference[1]}` ({trace_reference[2]/1024**2:.2f} MiB,
{trace_reference[3]} simulated seconds, {trace_reference[4]} scheduled vehicles),
the full planned {planned_vehicle_seconds:,} scheduled vehicle-seconds project
about **{trace_disk_estimate/1024**3:.2f} GiB of trace/evidence storage**. A 2x
planning reserve is **{2*trace_disk_estimate/1024**3:.2f} GiB**, excluding the
environment, extra diagnostics and duplicated archives. This linear exposure
projection can still underestimate richer interactions and is not a bound.
Available disk at audit: {audit['disk_free_bytes']/1024**3:.2f} GiB, below both
the traced-storage projection and the planning reserve. **Storage planning is
an additional blocker**: review/add capacity before approval. Retain full traces;
do not remove evidence merely to make a run fit.

## Commands and approval boundary

**There is currently no approved runnable long-suite resume command.**
The following are conditional future commands only, after documented acceptance,
source review and explicit user approval. They were not executed:

```powershell
Set-Location "C:\\Users\\Iresha Nethmini\\Documents\\R26-DS-017\\component_2_right_of_way_negotiation"
$projectPython = "C:\\R26-DS-017\\venv\\Scripts\\python.exe"
# ONLY after the V2 acceptance/preparation gate is resolved and approved:
& $projectPython -B run_post_training_evaluation.py --prepare --output-root "results\\post_training_evaluation\\v2_candidate"
# ONLY after separate explicit approval of the long suite:
& $projectPython -B run_post_training_evaluation.py --suite final --output-root "results\\post_training_evaluation\\v2_candidate"
# Resume only the same approved matching manifest; review interrupted directories first:
& $projectPython -B run_post_training_evaluation.py --suite final --output-root "results\\post_training_evaluation\\v2_candidate"
```

The readiness audit does not regenerate the archived smoke or final reports.
Official V2 reports may be generated from authentic approved archived runs
after that evaluation, with incomplete/invalid/no-completion cases retained.
''')
    # Set dense to an empty list.
    dense=[]
    # Iterate over audit at 'presentations', binding each item to p.
    for p in audit['presentations']:
        # Set r to p at 'record'.
        # Set m to 'metrics' from r; use an empty dictionary if absent.
        r=p['record'];m=r.get('metrics',{})
        # Set spawned to the number of entries in r at 'spawned_vehicle_ids' when whether 'spawned_vehicle_ids'
        # from r; use None if absent has type list, otherwise 'total_vehicles_spawned' from m; use None if absent.
        spawned=len(r['spawned_vehicle_ids']) if isinstance(r.get('spawned_vehicle_ids'),list) else m.get('total_vehicles_spawned')
        # Set scheduled to 'presentation_vehicles_scheduled' from m; use None if absent.
        # Set completed to 'presentation_vehicles_completed' from m; use None if absent.
        scheduled=m.get('presentation_vehicles_scheduled');completed=m.get('presentation_vehicles_completed')
        # Append a list containing the text 'congested_four_approach', the text 'Qualitative historical
        # presentation', scheduled, spawned,... to dense.
        dense.append(['congested_four_approach','Qualitative historical presentation',scheduled,spawned,completed,
            # Include the rounded value of completed divided by scheduled multiplied by 100 when scheduled and
            # completed is a different object from None, otherwise None in this list.
            round(completed/scheduled*100,2) if scheduled and completed is not None else None,
            # Include 'maximum_simultaneously_moving_vehicles' from m; use None if absent in this list.
            m.get('maximum_simultaneous_active_vehicles'),m.get('maximum_simultaneously_moving_vehicles'),m.get('mappo_decision_epochs'),
            # Include 'presentation_semantic_selection_rule' from r; use 'execution_mode' from r; use None if
            # absent if absent in this list.
            m.get('collisions'),m.get('blocked_zone_violations'),r.get('presentation_semantic_selection_rule',r.get('execution_mode')),
            # Include the result of p['path'].replace(the text '\\', the text '/') in this list.
            r.get('run_status'),p['path'].replace('\\','/')])
    # Iterate over audit at 'families', binding each item to f.
    for f in audit['families']:
        # Run this branch when f at 'root' does not belong to a list containing the text
        # 'results/panel_validation/v1', the text 'results/panel_validation/v2'.
        # Skip the rest of this loop iteration and process the next item.
        if f['root'] not in ['results/panel_validation/v1','results/panel_validation/v2']:continue
        # Iterate over f at 'runs', binding each item to r.
        for r in f['runs']:
            # Run this branch when r at 'suite' differs from the text 'panel' or r at 'scenario_id' does not
            # belong to a list containing the text 'nominal_dense_continuous_16', the text
            # 'congested_four_approach'.
            # Skip the rest of this loop iteration and process the next item.
            if r['suite']!='panel' or r['scenario_id'] not in ['nominal_dense_continuous_16','congested_four_approach']:continue
            # Set m to r at 'metrics'.
            m=r['metrics']
            # Append a list containing r at 'scenario_id', the text 'Targeted scientific' plus
            # f['root'].rsplit('/', 1) at 1,... to dense.
            dense.append([r['scenario_id'],'Targeted scientific '+f['root'].rsplit('/',1)[1],m.get('total_vehicles_scheduled'),m.get('total_vehicles_spawned'),m.get('total_vehicles_completed'),
                # Include 'maximum_simultaneously_moving_vehicles' from m; use None if absent in this list.
                round(m['completion_rate']*100,2),m.get('maximum_simultaneous_active_vehicles'),m.get('maximum_simultaneously_moving_vehicles'),m.get('mappo_negotiation_events'),
                # Include r at 'classification' plus the text '/' plus a string built from 'termination_reason'
                # from m; use None if absent in this list.
                m.get('collision_count'),m.get('blocked_zone_violation_count'),'Seeded stochastic; ego-local',r['classification']+' / '+str(m.get('termination_reason')),r['path'].replace('\\','/')])
    # Call save with the supplied arguments.
    save('DENSE_TRAFFIC_EVIDENCE_SUMMARY.md','''# Dense traffic evidence — 16 October 2026

Historical presentation success, scientific targeted validation and the extended
final matrix are different evidence families. Every available historical
congested artifact found by the audit is listed; some are duplicate summaries
of the same episode and are not independent replications. N/A means the record
does not supply that metric. Older 16/16 successes do not guarantee current
behavior; the preserved later qualitative latest record is 0/16 and INCOMPLETE.
New short lifecycle checks are USER_STOPPED, not performance experiments.

'''+table(['Scenario','Purpose','Scheduled','Spawned','Completed','Completion %','Peak active','Peak moving','MAPPO epochs','Collisions','Blocked violations','Execution mode','Status','Evidence path'],dense)+'''

## Scientific interpretation

PV-04A nominal scientific evidence records 1/16 completion (6.25%), two MAPPO
invocations, two safety-fallback outcomes, zero collisions/blocked-zone violations
and a hard 180-second timeout. PV-04B critical records 0/16, zero MAPPO calls,
confirmed deadlock and zero observed safety violations. The V1 critical result
remains separately preserved. These are severe liveness limitations, not PASS.

Peak active/moving counts of 16 and queues of up to four per approach verify
traffic beyond four vehicles. Maximum encoded negotiation participation remains
four physical queue heads; native following does not mean every traffic vehicle
is a simultaneous MAPPO node. The congested schedule contains four vehicles
per approach and all twelve legal movement classes, verified from its existing
catalog and audit. No route, schedule, spacing or budget was changed here.

The existing dense/repair source traces document COMMUNICATED_PRECEDENCE_DISAGREEMENT
and held queue heads under incompatible local intention premises, while mandatory
claim conflicts remain outside MAPPO authorization. Nominal trace decisions
later show unresolved local precedence/zone obligations. This supports observed
safe holding and stalled discharge, not a proof that every underlying forecast
was correct. Generic MISSING_OR_STALE_LOCAL_COORDINATION labels alone do not
prove old messages. Consult PANEL_DENSE_V2_AUDIT.md and REPAIR_V2_AUDIT.md for the
timestamped analyses; no new causal claim is inferred merely from counts.

Zero observed collisions/violations is bounded safety evidence, not universal
safety or a liveness guarantee. No-completion trip statistics remain N/A;
unfinished waiting/exposure statistics are censored. Fairness is limited by
served-pair availability and incomplete discharge, not established by a small
approach-wait gap. V1 and V2, presentation argmax and scientific stochastic
sampling, and different reviewed runtime versions must not be pooled as one
performance study. The incomplete 34/165 V1 matrix establishes no universal
congestion or intersection-generalization claim.
''')
    # Set scale to an empty list.
    scale=[]
    # Iterate over audit at 'families', binding each item to f.
    for f in audit['families']:
        # Run this branch when the negation of the result of f['root'].startswith(the text
        # 'results/scalability_validation/v').
        # Skip the rest of this loop iteration and process the next item.
        if not f['root'].startswith('results/scalability_validation/v'):continue
        # Set scientific to a list of r for r in 'runs' from f; use an empty list if absent; retain entries
        # satisfying r at 'suite' equals the text 'scalability'.
        scientific=[r for r in f.get('runs',[]) if r['suite']=='scalability']
        # Iterate over 'runs' from f; use an empty list if absent, binding each item to r.
        for r in f.get('runs',[]):
            # Run this branch when r at 'suite' equals the text 'preflight'.
            # Append a list containing f at 'protocol_id', the number of entries in scientific, r['metrics'] at
            # 'total_vehicles_completed',... to scale.
            if r['suite']=='preflight':scale.append([f['protocol_id'],len(scientific),r['metrics']['total_vehicles_completed'],r['metrics']['total_vehicles_scheduled'],r['metrics'].get('mappo_inference_call_count'),r['metrics'].get('termination_reason'),r['wall_clock_seconds']])
    # Call save with the supplied arguments.
    save('SCALABILITY_STUDY_PLAN.md','''# Scalability study plan — not executed

Purpose: observe how the existing system changes as total scheduled traffic
increases, without claiming a statistically universal capacity threshold.
Both preserved seven-load studies have **0/7 scientific cases**; all scientific
rows remain NOT_RUN. Their separate plumbing preflights are not load-study data.

'''+table(['Family','Scientific cases','Preflight completed','Scheduled','MAPPO calls','Stop','Wall seconds'],scale)+'''

The existing V2 plan is the appropriate candidate for review: seven single
episodes at 4,8,12,16,24,32,40 vehicles, using exact prefixes of one deterministic
40-entry NESW round-robin stream, 0.4 seconds between entries and 1.6 seconds
per approach. Original legal movements and the fixed 180-second budget per
case stay unchanged. V1's identical initial departure times confounded load
interpretation; V2 staggered the opening but its preflight also deadlocked.
Do not tune spacing or movement order based on those outcomes.

Intersection, E5, intention models, traffic rules, geometry, vehicle physics,
speed mode 31, safety constraints, ego-local execution and <=4 queue heads
remain fixed. Followers use native SUMO car-following. Scientific inference
uses the existing masked stochastic sampler with one deterministic versioned
action seed across loads. No retraining or multi-seed search is proposed.

Record scheduled/spawned/completed counts separately, never-spawned demand,
actual departure delays, collision/blocked-zone/emergency-braking counts,
deadlock/timeout, unfinished spawned vehicles, safe holds, throughput,
average/p95/max incoming wait, per-approach mean/gap and served-pair FCFS
inversions where available. Record active/moving peaks, approach queue depths,
MAPPO calls/accepted/rejected/fallback outcomes, maximum participants, existing
hardware-dependent inference/execution timings and all integrity guard counters.
Unavailable trip metrics and no-call fallback rates remain N/A. Unfinished
exposure/wait is censored. Pending insertion alone is not negotiation failure.
NETWORK_CAPACITY_LIMIT requires the original frozen positive capacity evidence,
not just fewer spawned vehicles; otherwise retain explicit uncertain/backpressure
attribution. Preserve PASS/SAFE_DEGRADATION/UNSAFE_FAILURE/INVALID outcomes.

The existing conservative full-budget estimate is 146.18 minutes, not measured
seven-load runtime. Early deadlock stops might shorten it, larger-load costs
could increase it. Do not launch a large study without approval. Naming changed
live source hashes: the existing manifests must remain frozen. Reproduction
requires their exact archived source set, or a separately approved diagnostic
protocol/version, not editing the original manifest. A new diagnostic is not
directly comparable to the original V1 final evaluation, which used different
seeds, arrival spacing and inference. It must be labeled diagnostic and separate.

If viva time is limited, present verified historical 16-vehicle evidence and
the targeted 1/16 and 0/16 limitations, explicitly stating that broader
scalability remains future work. No threshold between unmeasured loads is known.
''')
    # Call save with the supplied arguments.
    save('FINAL_TEST_VERIFICATION.md','''# Final test verification — 16 October 2026

Environment: C:\\R26-DS-017\\venv\\Scripts\\python.exe, Python 3.13.1;
pytest 9.1.1; Torch 2.14.0; SUMO executable 1.26.0. Logs are newly generated
under results/final_readiness/20261016/, not reused prior test claims.

| Newly executed check | Result | Log |
|---|---|---|
| Root collection before correction | 699 collected; one archived snapshot error; exit 1 | root_collection_before.log |
| Root collection after minimal config | 926 collected, no errors (before new UI tests) | root_collection_after.log |
| Final root collection | 947 collected, no errors; 4.85 s | root_collection_final.log |
| Full active Component 2 | 848 passed, 2 existing strict xfails; 1012.22 s; no warnings | component2_full_tests.log |
| Full active showcase after fixes | 97 passed; 1.71 s; no warnings | showcase_tests_final_verified.log |

```powershell
Set-Location "C:\\Users\\Iresha Nethmini\\Documents\\R26-DS-017"
$projectPython = "C:\\R26-DS-017\\venv\\Scripts\\python.exe"
& $projectPython -B -m pytest --collect-only -q
& $projectPython -B -m pytest component_2_right_of_way_negotiation/tests -q -ra
& $projectPython -B -m pytest socialmind_drive_showcase/tests -q -ra
```

The root pytest.ini selects active Component 2/showcase suites and excludes
results/archive snapshots without deleting them. Module-scoped test CWD setup
makes Component 2's existing relative test assets work from the workspace root.
Explicit active test-directory invocation remains supported. Other components'
independent research tests are outside this task's root testpaths scope.

The two strict xfails are the original complete dense-discharge and zero-live-at-
completion assertions in test_ego_execution_and_dense_traffic.py. They were not
added, skipped or weakened here. Unmarked fixture safety/integrity assertions
still pass. Thus exit 0 is not a claim that dense liveness was fixed or that
the V2 acceptance gate passed. The full suite's SUMO fixture used a temporary
directory and original 360-second regression budget; no scientific evaluation
episode or old evidence was overwritten.

Earlier new-showcase attempts exposed an over-broad process-stop implementation,
a selector compatibility mismatch and a cleanup indentation error. Those were
fixed in presentation code; the original tests/assertions remain unchanged.
The intermediate failed logs are retained for audit, and the final 97-pass log
is identified explicitly. No failure was relabeled as success.

Two new short real qualitative launch probes (congested and default rolling)
were explicitly stopped after real frames at 2.12 simulated seconds. Both
returned USER_STOPPED/exit 0, refused duplicate launches, stopped gracefully,
and left no owned process running. They are not scientific performance evidence.
Six actual HTTP routes returned 200; the evaluation response contained 34/165
and SMOKE_NOT_FINAL. Full details are in qualitative_launch_checks.json,
http_checks.json and lifecycle_and_http_checks.log. A third short live qualitative
check invoked the registered shutdown method while traffic was running at
1.0 simulated seconds: graceful exit, zero remaining owned processes and
relaunch refused after shutdown (shutdown_check.json).

Real missing-checkpoint and absent-SUMO prerequisite guards also returned FAILED
before starting a process (startup_failure_checks.json). An earlier isolated
backend startup fault exposed a secondary Not connected finalizer error; its
log is retained. The UI now refuses these missing prerequisites before launch.
No scientific runtime was modified to suppress that backend failure; direct-CLI
fault cleanup remains a documented limitation requiring separate review.

No Browser connection was available, so visual layout/click rehearsal is not
claimed. Desktop pywebview 6.2.1 and owned-process psutil 7.2.2 were installed
from existing/new presentation requirements, without upgrading scientific
packages. pip check found no broken requirements and the Windows desktop
backend imported successfully without opening a window. Native window
interaction remains a manual viva rehearsal item.
''')
    # Call save with the supplied arguments.
    save('FINAL_VIVA_RUNBOOK.md',r'''# Final viva runbook — SOCIALMIND DRIVE

## Verified environment and startup

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017"
& "C:\R26-DS-017\venv\Scripts\Activate.ps1"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
& $projectPython --version
Get-Command sumo
sumo --version
& $projectPython -m pip check
# Install only missing declared dependencies if needed; do not retrain or upgrade models.
& $projectPython -m pip install -r socialmind_drive_showcase\requirements.txt
& $projectPython -m pip install -r component_2_right_of_way_negotiation\requirements.txt
& $projectPython -m pip install -r component_2_right_of_way_negotiation\requirements-training.txt

# Desktop, one resizable native window:
& $projectPython -B socialmind_drive_showcase\app.py
# Alternative browser/server-only mode:
& $projectPython -B socialmind_drive_showcase\app.py --server-only
# If port 8088 is occupied, close the old app or explicitly choose a free port:
& $projectPython -B socialmind_drive_showcase\app.py --server-only --port 8099
```

The existing environment is Python 3.13.1 with SUMO 1.26.0. Use the explicit
Python path if PowerShell activation is blocked; do not change global execution
policy just for this demo. The first install commands are recovery instructions,
not permission to change frozen scientific software/configuration indiscriminately.
Desktop uses pywebview; Stop/shutdown uses psutil for the owned process tree.

## Live demonstration

1. Open http://127.0.0.1:8088/component/right-of-way and its Live View. Use the
   chosen port if different. Navigation/layout/project names are unchanged.
2. Select **Congested Four-Approach Queues (16 vehicles)** while idle. The
   existing default rolling traffic presentation is also selectable.
3. Press **Run Scenario** once. It launches the real existing SUMO runtime with
   the selected scenario, E5, original vehicle parameters and original budget.
4. Wait for a fresh frame. LAUNCHING, RUNNING, STOPPING and FAILED are process
   states, not scientific classifications. Old frames are not a new launch.
5. Show simulation time, measured active/moving counts, N/E/S/W queues, current
   participants, peak traffic, MAPPO evidence, collisions and execution mode.
   N/A means unavailable, not an invented zero. The visual negotiation highlight
   is a display overlay; it never changes SUMO stepping or driving decisions.
6. Press **Stop** once; wait for idle. Cooperative stop is attempted first;
   only this launch's owned tree is terminated if grace expires. Do not kill
   every python.exe or sumo.exe process. Switch scenarios only while idle.
7. Close the app window or stop the server with Ctrl+C. Application shutdown
   requests cleanup of the owned simulation. Confirm the process stops before
   relaunching. Per-launch logs are in results/runtime_simulation/runtime/.

Standalone existing GUI demonstration (qualitative, not quantitative):

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
& $projectPython -B run_runtime_simulation.py --scenario congested_four_approach --gui
```

The scientific schedule is unchanged; 16 scheduled vehicles do not guarantee
16 simultaneously spawned or completed. The current congested runtime can
stall. Do not rerun repeatedly until a favorable demonstration is obtained.

## Read-only quantitative evidence

Open http://127.0.0.1:8088/component/right-of-way/evaluation. It distinguishes
34 checksum-verified archived V1 final records out of 165 from the saved
nine-episode SMOKE_NOT_FINAL comparison. Final outcomes are 10 PASS,
22 SAFE_DEGRADATION and 2 UNSAFE_FAILURE. No V2 final manifest is accepted.
This is an incomplete archive, not a completed 165-episode study.

Authentic saved files (do not regenerate or edit in place):

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
Start-Process "results\final_evaluation\latest\PANEL_EVALUATION_REPORT.html"
Start-Process "results\panel_validation\v2\latest\PANEL_VALIDATION_REPORT.html"
Get-Content "docs\final_readiness\DENSE_TRAFFIC_EVIDENCE_SUMMARY.md"
Get-Content "docs\final_readiness\FINAL_EVALUATION_PREFLIGHT.md"
```

The first saved HTML report is smoke evidence. The targeted report includes
the severe nominal/critical dense liveness failures. Broader scalability is
NOT_RUN. These results must remain visible even when showing an older successful
16-vehicle presentation. Saved qualitative success and current inference differ
by purpose/mode/runtime provenance and must not be pooled into a success claim.

## Defensible explanations

MAPPO supplies trained semantic KEEP/RELINQUISH and ACCEPT/REJECT actions only
when negotiation is authorized. German-rule precedence, protected obligations
and deterministic safety checks still govern legal/physical execution. A real
actor invocation is not automatically a successful negotiation or completed trip;
separate direct MAPPO, safety fallback, rule resolution and safe holding.

Total traffic can exceed four because followers wait under native car-following.
At most one physical queue head per incoming approach is currently negotiation
eligible; after rear clearance, the next follower is promoted. This is traffic
support beyond four vehicles, not validation of a >4-node MAPPO policy graph.

Safety and liveness are different. Zero observed collisions/blocked-zone
violations in a case does not establish efficient or fair discharge. PV-04A
completed 1/16; PV-04B 0/16. Unfinished wait/exposure is censored, no-completion
trip statistics are N/A, and a small observed wait gap is not proof of fairness.
One AV-only unsignalized intersection and ideal messages limit generalization.

## Failure contingency

If startup fails, read the on-page error and owned launch log; verify Python,
SUMO PATH, model files and dependencies. Do not replace the failure with a
success label or alter safety/physics. If frames become stale, show the warning,
request Stop and wait for cleanup. If the port is busy, use a new port rather
than terminating unrelated processes. For a missing model, restore the exact
frozen artifact from the full research archive; do not train a replacement.

During a viva failure, explicitly state what failed, then show authentic saved
reports and the dense comparison. The package is for demonstration; keep the
full research archives separately. Do not launch the long final/scalability
studies during the viva or without acceptance review and explicit approval.

## Rehearsal status

Full active tests and short real launch/stop/HTTP checks passed as documented
in FINAL_TEST_VERIFICATION.md. No connected Browser was available for visual
interaction checks. Rehearse desktop window opening/closing and page clicks on
the actual presentation machine before the viva; do not claim that was visually
verified in this session.
'''.replace(r'\"','"'))
    # Call save with the supplied arguments.
    save('PANEL_COMMENTS_RESOLUTION.md','''# Panel comments resolution

## Comment 1

> Need to have a good understanding about the background of the selected topic. Also need to plan how to demonstrate the implemented system. Need to address complex scenarios in PP2.

Concern: explain the research problem, contribution and credible demonstration
of complex interactions. Implemented: the existing perception/LDM, intention,
conflict, rule, claim-exchange, role-specific MAPPO and ego-local execution
pipeline; legal cycle, mixed-turn and queue scenarios; a read-only live viewer
and now a documented failure contingency. Evidence: Component 2 README,
runtime_simulation/scenario_catalog.json, selected_configuration.json,
REPAIR_V2_AUDIT.md, the targeted records and FINAL_VIVA_RUNBOOK.md.

Verification: full active Component 2 tests 848 pass with two pre-existing
liveness xfails; showcase 97 pass; real short launch/stop and six HTTP routes
verified. Visual desktop/page interaction still requires manual rehearsal.
Limitation: selected bounded scenarios do not prove universal intersection
generalization; the extended V2 study is not accepted or completed.
Viva explanation: "Our contribution combines learned semantic negotiation
with deterministic legal and safety checks. We demonstrate actual inference
and also disclose cases where safe holding prevents traffic discharge."

## Comment 2

> For the whole project fairness-time measurement is very important. Focus on narrowing down the scope of the component to selected complex intersections.

Concern: measure delay and fairness within a defensible operational scope.
Implemented: incoming-lane mean/p95/maximum waits, per-approach wait means/gap,
conflicting served-pair FCFS inversions, throughput and censored team travel
exposure in one selected unsignalized four-way AV-only SUMO intersection.
Evidence: post_training_evaluation/metrics.py, evaluation scope, targeted
PV-04A/PV-04B records and DENSE_TRAFFIC_EVIDENCE_SUMMARY.md.

Verification: metrics are archived and displayed read-only; no frontend
recalculation or fabricated unavailable trip statistics. Limitation: unfinished
waits are censored, served-pair inversions can be N/A, and partial/failed runs
do not establish broad fairness improvement or statistical superiority.
Viva explanation: "We narrowed the scope to one complex unsignalized four-way
intersection. We report delay by approach and censored waiting explicitly;
we do not interpret stalled traffic as successful fairness."

## Comment 3

> Simulated for 4 vehicles across junction. Better to go for a more congested scenario to test the system properly.

Concern: distinguish total traffic population from the negotiation graph limit.
Implemented: 16 scheduled vehicles, four per approach, all twelve legal
movement classes, queues, successive physical queue-head promotion and native
follower car-following. Evidence: authentic older 16/16 qualitative records,
the later incomplete qualitative record, and scientific nominal 1/16 and
critical 0/16 results, all retained in the dense comparison table.

Verification: archived counts/peaks/participants/safety read from actual files;
full dense regression independently confirms safety/integrity but still fails
the original discharge requirements under strict existing xfails. Maximum
simultaneous negotiators remains four. Limitation: no general congestion
success is established; 4..40 scalability scientific cases remain NOT_RUN.
Viva explanation: "We extended total traffic to sixteen vehicles while
retaining four current queue-head negotiators. Some older presentations fully
completed, but the targeted study exposes severe liveness limitations. Broader
scalability and robust decentralized premise reconciliation remain future work."

These comments are addressed by implemented and measured work with disclosed
limitations, not by declaring every experiment successful. The V2 acceptance
gate and explicit approval for the long study remain unresolved.
''')
    # Write the supplied text to (OUT / 'resource_estimates.json').
    (OUT/'resource_estimates.json').write_text(json.dumps(dict(maximum_simulated_seconds=maximum_budget,observed_max_population=observed_max_count,
        # Supply median_ratio_hours as low_hours.
        # Supply conservative_scaled_hours as high_hours.
        # Supply legacy_metadata_disk_bytes as disk_estimate.
        median_ratio_hours=low_hours,conservative_scaled_hours=high_hours,legacy_metadata_disk_bytes=disk_estimate,
        # Supply estimated_full_trace_disk_bytes as trace_disk_estimate.
        # Supply recommended_trace_reserve_bytes as 2 multiplied by trace_disk_estimate.
        estimated_full_trace_disk_bytes=trace_disk_estimate,recommended_trace_reserve_bytes=2*trace_disk_estimate,
        # Supply indent as 2.
        # Supply current_free_disk_bytes as audit at 'disk_free_bytes'.
        # Supply method_counts as rows.
        current_free_disk_bytes=audit['disk_free_bytes'],method_counts=rows),indent=2))
    # Display the text 'Created readiness reports from verified archived data.'.
    print('Created readiness reports from verified archived data.')

# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__=='__main__':main()
