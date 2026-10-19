# Approved conditional-claim reconciliation: implementation and real verification

16 October 2026. Protocol: **CONDITIONAL_CLAIM_RECONCILIATION_V1**.
Execution revision: **EGO_ADMISSION_CCR_V1_NATIVE_RELEASE**.
This is a versioned scientific change explicitly approved in the user's
continuation task. It is separate from the earlier telemetry-only correction.

## Defect and correction

The original unknown-intention graph retained every feasible conflicting movement.
Rules evaluated its conflicting candidate subset, then emitted unconditional
mandatory pair edges. N straight considering hypothetical S left emitted S→N;
S right considering hypothetical N left emitted N→S. These mutually exclusive
premises became a mandatory disagreement, blocking MAPPO and ego coordination.
The original failures and their event/physical traces remain preserved.

`negotiation_learning/movement_declarations.py` adds an immutable sender-authored
message and a same-step authenticated transport abstraction, consistent with the
existing ideal precedence channel. Each sender reads only its own LDM navigation
manoeuvre and lane; ObservationManager already derives that own manoeuvre from
its own route. Receivers never read another vehicle's route or a global route map.

Messages identify sender, allowed manoeuvre, map path, lane, simulation timestamp,
protocol and epoch. The transport binds the payload to its authenticated author's
own generated message. Receivers reject wrong sender/payload, unsupported moves,
wrong path/manoeuvre, stale epochs, duplicates/contradictions, missing messages
and inconsistent locally represented lane context. Every step expires the old
message set. This assumes honest own-navigation state and authenticated ideal
same-step delivery; it is not a cryptographic implementation or Byzantine-safety
claim. Transmission corruption/forgery is tested, not a malicious navigation stack.

Each receiving ego reconciles its local uncertain graph independently. Original
prediction evidence/conditional candidate paths remain available for audit.
Only validated declared candidates feed current regulatory claims. A map-proven
nonconflicting declared pair produces no fictitious priority edge. A conflicting
declared pair still receives the unchanged adopted traffic rules; genuine
mandatory obligations remain protected by the existing execution shield.

The shared `_pipeline_step` accepts an optional protocol. Historical/training
callers that omit it retain their earlier branch; the active live runtime opts
into the approved version. Failed validation blocks current coordination and
inference. A previously valid authority cannot mask a newly blocked regulatory
state. Already admitted vehicles retain the existing clearance lock; missing
messages do not authorize a new entrant or force a vehicle to stop mid-zone.

No actor/critic class, observation tensor dimension, action interpretation,
agent ordering, reward, training data, checkpoint or physical parameter changed.
Regulatory input information and graph contents change, as explicitly approved;
compatibility with the old tensor interface does not prove unchanged performance.
Original E5 masked actor inference is retained, with presentation-only argmax.
Scientific evaluation requires separately reviewed versioning; old measurements
do not evaluate this new protocol.

## Additional verified execution bug

The first broad protocol regressions exposed a stopped-release admission defect.
At 23.80 s in the rule-resolved case, SUMO's preceding unconstrained speed was
zero. The old admission-lock boundary consequently remained zero even though
the junction had just cleared. SUMO accelerated 0.08 m/s in the next 0.04-second
step; the newly internal vehicle then received a hold, and the blocked-entry
invariant correctly raised. The failed run is preserved under
`reconciled_final_v1/rule_resolved_two/` (one violation; never PASS).

`DecentralizedEgoExecutionController.constrain` now includes
`current_speed + max_acceleration * simulation_step` in the next-speed bound
used to lock an already PERMITTED admission. It changes neither permission nor
acceleration: it accounts for the next physically possible SUMO action rather
than treating its preceding action report as a prediction. The original blocked
entry invariant, native braking, speed mode 31 and zone protections remain active.
A regression specifically covers a stopped vehicle whose native preceding
unconstrained speed is zero. Real rule-resolved and mixed cases then complete.

## Source and evidence organization

Production changes in this approved task:

- `negotiation_learning/movement_declarations.py`: new approved protocol.
- `negotiation_execution/replay.py`: optional sender publication, ego-local
  reconciliation and fail-closed snapshot integration; default historical branch
  remains optional/no-protocol.
- `runtime_simulation/runner.py`: enable the versioned live protocol, invalidate
  authority on newly blocked input, enforce local validation and record versions.
- `negotiation_execution/ego_controller.py`: physical next-step admission fix.

No new website design/code changes were required in this approved task. The
preceding telemetry correction remains in place. The runtime state is read by
the original shared website, in its existing sibling location.

New protocol/unit regressions: `tests/test_movement_declarations.py`. Naming-only
historical checks in `tests/test_naming_migration.py` now compare the recorded
naming-period source for the three deliberately revised files while also hashing
the new approved source version. Original AST/byte equivalence assertions remain;
they no longer incorrectly demand that an approved later scientific algorithm
be identical to the naming-only historical algorithm. Existing safety/discharge
assertions and strict expected-failure markers are retained.

The full regression run exposed an additional test-fixture applicability issue:
its old incomplete-run guard required zero completed trips and only communicated
disagreement events. That is the historical failure, not the approved protocol's
new five-trip residual failure. The guard now branches on the recorded protocol:
the legacy zero-trip assertions remain for legacy runs; the revised case requires
at least the five independently measured completed trips, exact remaining/live
count consistency, unique completed IDs, genuine MAPPO and a regulatory-cycle
event. All safety/weight/critic/global-control guards remain unmarked and strict.
The original 16/16 and zero-live assertions are unchanged and still strict xfails.

Source bytes/identities: `results/live_deadlock_investigation/20261016/approved_source_versions/`.
All run evidence stays beneath the same investigation root:

- `baseline/`: original unreconciled failures and successes.
- `telemetry_v1/`: earlier display-only comparisons.
- `reconciled_v1/`: initial protocol runs, including an interim dense run.
- `reconciled_final_v1/`: broad interim runs, including the discovered release failures.
- `reconciled_release_fix_v1/`: final corrected execution runs.
- `reconciled_faults_v1/` and `reconciled_final_faults_v1/`: separate fault injections.
- `showcase_approved_v1/`: actual launcher/live-state/HTTP receipts.

Each diagnostic records real physical samples, changed local permissions,
commitments, sender metadata, masks/actions, policy hashes, source hashes,
completion/lifecycle events and measured metrics. No historical failure was
overwritten, relabeled or merged into a final study. No root probe or ZIP was made.

## Real scenario results

Final numeric tables, integrity counts and full-suite outcome are recorded in
`APPROVED_RECONCILIATION_VERIFICATION.md` and the corresponding JSON receipt.
The rule-resolved, four-way, regulatory-cycle, multiple-left-turn, mixed,
rolling and combined-yield cases all completed in the final separate runs.
Four-way: 4/4, no unnecessary MAPPO. Regulatory cycle: 4/4 with one genuine MAPPO
invocation. Rolling: 12/12 with one invocation. Dense traffic makes progressive
discharge and genuine inferences, then encounters the residual cycle below.
No universal safety or improved statistical robustness is claimed.

Fault-injection tests deliberately alter the sender S channel (missing, stale,
invalid manoeuvre, incorrect authored payload, contradictory duplicate). These
are corrupted-channel cases, not changed route demand. All four vehicles remain
uncompleted under the tested failures; no MAPPO invocation or unsafe release
occurs. SAFE_DEGRADATION is the correct outcome, not a completion PASS.

## Residual dense limitation and additional design boundary

After initial discharge, a valid later wave contains E02 left, N02 left,
S02 straight and W03 straight. At 43.60 s the original E5 actors relinquish
the represented claims and responders accept them, leaving an empty effective
graph. The shield correctly retains mandatory E02→W03 and N02→S02 turning
obligations. Existing pair fallback uses published arrival times/ID ties for
otherwise unordered eligible physical pairs. That creates:

```text
E02 → W03  mandatory turning obligation
W03 → N02  existing arrival-order fallback
N02 → S02  mandatory turning obligation
S02 → E02  existing arrival-order fallback
```

All arrows mean "yields to". W03 arrives later (3.04 s); the other second-wave
vehicles arrive at 1.56 s, with the existing ID tie convention. Both endpoints
derive the recorded fallback orders. These are actual declared physical
interactions, not the former hypothetical conditional-claim disagreement.
The safety controller consequently has no safe release under the current
commitments. Reconciliation has corrected the approved defect but cannot, alone,
make these inconsistent fallback orders acyclic. Re-running deterministic argmax
or adding a timeout does not supply a valid resolution.

Further proposal, **not implemented**: a separately versioned, decentralized
mandatory-aware fallback ordering. Each ego would retain all mandatory pair
obligations and reconcile fallback orders only among legally incomparable peers,
using authenticated endpoint evidence. A genuine mandatory cycle must still
safe-hold. This would change safety-fallback semantics beyond conditional-claim
reconciliation, requiring an additional impact assessment and approval.
It must remain labeled MAPPO_WITH_SAFETY_FALLBACK, not direct policy success;
no central execution graph or hidden scripted substitute is acceptable.
Such fallback could activate only after a verified eligible MAPPO outcome and
accepted waiver evidence. All mandatory and non-waived commitments must remain
constraints. Rule-only execution, missing messages, unsupported claims and a
timeout must not authorize fallback. Deterministic arrival/ID ordering would
apply only among otherwise legally incomparable participants; a mandatory or
retained-commitment cycle still has no release certificate.

Needed before that extension: formal ordering/endpoint-consistency cases, missing
chain evidence tests, mandatory-cycle safe-holds, preserved action semantics,
mixed obligatory/voluntary cycle regressions, exact dense replay and all original
scenario/safety tests. New formal comparisons would be required; the old frozen
evaluation records remain evidence of their original systems only.

## Website and startup

The actual shared launcher completes the four-way case, relaunches dense traffic,
receives real positions/speeds/completions and genuine MAPPO counters, then stops
only its owned process tree. Unique launch IDs/freshness checks prevent stale
frames; duplicate launch is refused. HTTP verification covers six real routes.
Browser discovery returned no connected browser; interactive clicks/screenshots
are unavailable and are not claimed as verified. No fabricated animations exist.

From the workspace root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only
```

Open `http://127.0.0.1:8088/component/right-of-way/live`. The Regulatory Cycle
scenario is a verified real MAPPO example; the original four-way scenario is
rule-resolved after correct declarations. Rolling traffic now completes.
The dense case remains a documented partial/safe-degradation demonstration,
not a verified 16/16 success. The previous presentation ZIP is unchanged and
does not contain this correction; use the active repository for these runs.

## Reproduction commands and verification record

Executed from the workspace root, using distinct output versions (existing
diagnostic directories intentionally refuse overwrite):

```powershell
$projectPython = 'C:\R26-DS-017\venv\Scripts\python.exe'
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario rule_resolved_two --duration 90 --version reconciled_release_fix_v1
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario congested_four_approach --duration 360 --version reconciled_release_fix_v1
foreach ($scenarioId in @('four_way_simultaneous','regulatory_cycle','multiple_left_turns','mixed_manoeuvres','default_panel','yield_negotiation_demo')) {
    & $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario $scenarioId --duration 220 --version reconciled_release_fix_v1
    if ($LASTEXITCODE -ne 0) { break }
}
foreach ($faultMode in @('missing','stale','invalid','incorrect','contradictory')) {
    & $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_live_deadlock.py --scenario four_way_simultaneous --duration 45 --version reconciled_final_faults_v1 --fault $faultMode
    if ($LASTEXITCODE -ne 0) { break }
}
& $projectPython -B component_2_right_of_way_negotiation/tools/probe_reconciled_showcase.py
& $projectPython -B -m pytest component_2_right_of_way_negotiation/tests socialmind_drive_showcase/tests -q -p no:cacheprovider
# After correcting the version-specific incomplete-run fixture expectation:
& $projectPython -B -m pytest component_2_right_of_way_negotiation/tests/test_ego_execution_and_dense_traffic.py -q -p no:cacheprovider
& $projectPython -B component_2_right_of_way_negotiation/tools/report_approved_reconciliation.py
```

The initial full run had 965 passed and four setup errors at the obsolete
zero-trip fixture assumption. The affected real module recheck had 18 passed
and two existing strict xfails. Combined final coverage is 967 passed/two strict
xfails; this is not represented as a second entire full-suite run. The report
helper initially could not parse PowerShell UTF-16 redirected logs; it was
corrected to recognize their BOM. That helper failure and successful final log
are both retained; no result was changed to pass it.

Final integrity verification covers 13 final scenario/fault runs, selected
action masks and identities, exact recorded production sources, unchanged E5/
intention assets and all 2,334 historical evidence files. Four protected source
paths differ from the original readiness inventory across the telemetry and
approved-protocol tasks; the other 147 protected assets remain byte-identical.

Status: approved reconciliation implemented and verified; four-way and rolling
demonstrations PASS in these runs; dense demonstration SAFE_DEGRADATION (5/16);
no universal safety/robustness claim; real launcher/live-state/HTTP checks PASS,
interactive visual verification UNAVAILABLE. Additional fallback redesign
requires separate approval. No scientific matrix, selected-policy retraining,
historical report rewrite, unrelated cleanup or package rebuild was performed.
