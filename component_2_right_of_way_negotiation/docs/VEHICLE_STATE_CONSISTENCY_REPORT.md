# Vehicle state, waiting and genuine MAPPO: diagnosis and correction

16 October 2026. Display contract: **VEHICLE_STATE_CONSISTENCY_V1**.
Scientific control remains CONDITIONAL_CLAIM_RECONCILIATION_V1 with
EGO_ADMISSION_CCR_V1_NATIVE_RELEASE. No further fallback method is implemented.

## Findings from synchronized real execution

Red represented lack of intersection-entry permission, not a zero-speed command.
The existing ego controller computes native SUMO stopping constraints for a
future boundary. A vehicle can therefore move while entry is held, provided its
front does not enter the protected region without permission. Current speed at
simulation time t and a new command applied for the next step are different
measurements; comparing them as simultaneous speed limits is incorrect.

Concrete reproduced examples:

| Case | Vehicle/time | Actual speed | Distance to entry | Current decision |
|---|---|---:|---:|---|
| Dense | E04 at 28.68 s | 8.39823 m/s | 37.35428 m | SAFE_HOLD; queue/admission gate |
| Four-way | S01 at 22.12 s | 0.84968 m/s | 0.16495 m | SAFE_HOLD; coordination not yet valid |

Both approach under native stopping constraints. Neither example establishes an
unauthorized crossing. The audit detects each actual junction-entry transition
before calculating the new step's decision and checks the preceding issued
permission. Every observed entry in all baseline, after and fault runs had valid
prior permission. Collision/blocked-entry counts are also zero in these runs.
This is finite execution evidence, not a universal safety proof or a claim about
every frame in an unavailable recording.

The source `FOLLOWER_AWAITING_NEGOTIATED_ADMISSION` also covers vehicles not yet
in the reasoning region; it is an entry gate, not evidence that a vehicle is
physically stopped or necessarily a trailing follower.

The first misleading state occurs before any crossing: the card describes a
moving entry-held vehicle as WAIT, without explaining its stopping distance.
There are independent confirmed display defects:

1. A recent-event wall-clock overlay replaced actual permission colors with
   NEGOTIATING after inference had already returned. Dense baseline: 104 affected
   sampled vehicle-frames; regulatory-cycle baseline: 69. No corresponding
   controller permission changed. These are samples, not independent episodes.
2. The inspector inferred NOT REQUIRED from absence of a local actor factor.
   A coordination recipient need not have a local selected factor, and a lack
   of factors does not establish regulatory resolution.
3. The inspector chose the first original regulatory edge as the waiting cause,
   rather than the current ego controller's actual blocking zones/peers.
   Original edges can differ from negotiated commitments and shield obligations.
4. Actor factors could survive authority invalidation and appear current even
   though they belonged to an earlier decision.
5. Run inference summaries counted a truncated twelve-event timeline rather
   than the actual runtime inference counter.
6. Forced final frames could reuse older positions/speeds. A forced live frame
   without supplied scientific state was also treated as a terminal frame.
7. Inspector polling ignored stale/unavailable data and could leave older cards
   displayed after a fetch failure.

## Precise visual and timestamp contract

| Color | Meaning | Physical speed implication |
|---|---|---|
| Blue | Approaching; no final entry decision represented | May move/follow |
| Yellow | Explicit backend inference-pending state | Does not grant entry |
| Green | Current ego permission is PERMITTED, including valid clearance lock | SUMO may still slow for native safety/following |
| Red | Entry is held by the ego controller | May approach/decelerate to the legal stopping boundary |

The live runtime performs inference synchronously. It normally publishes the
result after inference, not a sampled pending frame. A genuine recent decision
is therefore shown as a dated event, without fabricating a yellow negotiating
duration or overriding red/green body colors. Existing palette/layout remain.

Each vehicle exports its measured state timestamp, motion state, actual entry
permission/reason, current blocking peers/zones, stop distance, shield rejection,
fallback evidence and next-step speed request. MOVING, CREEPING and STOPPED are
separate from entry authorization. Red labels say ENTRY HELD / APPROACHING STOP
or ENTRY HELD / STOPPED. The existing stopped-speed threshold is used only to
describe creeping; no physics or control threshold changes.

Terminal frames use current physical readings, retain explicitly dated prior
permission evidence and label it LAST REPORTED. An ended receipt is expired,
not advertised as current. No final physical reading is silently replaced by
an older inspectable snapshot.

## Implemented changes

- `runtime_simulation/vehicle_display_contract.py`: pure display explanations
  separating motion, permission, command timing and MAPPO receipt lifetime.
- `runtime_simulation/browser_state.py`: synchronized returned ego decisions;
  current receipt membership/timestamps; clear obsolete factors; explicit local
  action counts; shield/fallback execution status; cumulative real counters;
  accurate terminal physics/dating. Changing displayed event age does not create
  another process-trace inference event.
- `runtime_simulation/runner.py`: pass already-calculated decisions and current
  authority metadata to publication, and withhold obsolete display factors.
  Its entire control AST is unchanged after excluding these display arguments.
- `socialmind_drive_showcase/pages/component2_live_view.py`: recent-event metadata
  no longer changes permission colors; actual event participants/run identity
  define the highlight; legend/banner explain entry permission and event history.
- `socialmind_drive_showcase/pages/component2_inspector.py`: display actual
  blockers, execution reasons, motion and current/expired receipt state. Missing
  actor factors no longer imply NOT REQUIRED. Stale/unavailable cards are cleared.

No scientific controller, rule, conflict geometry, reconciliation message,
checkpoint, reward, scenario demand or vehicle parameter changed in this task.
The existing native-speed release branch remains intact. No timeout or hidden
first-come-first-served release was added.

Tests updated only where the previous display contract expected the now-proven
incorrect yellow override. Atomic-publish support for an explicit real pending
state remains. New tests cover moving red vehicles, factor absence, expired
actions, terminal timestamps/physics and non-truncated counters. The naming
guard verifies exact scientific-control AST equivalence for the display-only
publish arguments; all other approved scientific source hashes remain strict.

## Waiting causes and actual release commands

No unnecessary physical waiting caused by an obsolete peer or retained GO speed
cap was established in these reproductions. Every sampled PERMITTED decision
has no active precedence speed constraint. A logging wrapper forwarded actual
TraCI calls unchanged and recorded 989 speed requests in the rule-resolved case,
including two native releases (`setSpeed(-1)`). The final regulatory-cycle check
recorded 2,408 requests and five native releases. Both cases completed safely.

Long dense waits are recorded individually in `verification.json`. The four
remaining heads wait for active peers, not completed vehicles:

- E02 waits for W03 under a mandatory turning obligation.
- N02 waits for E02 and S02 under current fallback/mandatory obligations.
- S02 waits for E02 under the existing fallback.
- W03 waits for N02 and S02 under the existing fallback.

Seven followers remain behind those heads under their entry gates. At the end
of each measured extended wait, named blocking peers are still present. No
vehicle crossing in view does not imply that these dependencies have cleared.
The minimum cycle E02→W03→N02→S02→E02 was established in the preceding approved
protocol investigation. Removing it requires the separately proposed
mandatory-aware fallback, beyond a state-reporting correction. That approval
remains pending. The current task does not silently implement that methodology.

Thus the corrected defects are inaccurate waiting explanations/states, not a
claimed physical waiting-time reduction. Matched before/after waiting and
throughput metrics remain exactly identical.

## Genuine MAPPO verification and results

Global MAPPO OBSERVED IN THIS RUN is historical. Per-vehicle NOT REQUIRED,
ELIGIBLE, BLOCKED, DECISION APPLIED and DECISION EXPIRED describe its local
current assessment/receipt. A blocked vehicle can legitimately have received a
MAPPO outcome: physical permission may still be held by its shield or peers.
The payload/card explicitly distinguish SAFETY FALLBACK, SHIELD REJECTION,
ENTRY HELD and LOCAL EXECUTION. DECISION APPLIED is not a claim of direct policy
success or automatic GO. No sampled synchronous inference is fabricated as
ongoing negotiation.

The original four-way schedule is not four right turns: N right, E right,
S straight and W right. Its validated conflict relations are rule-resolved;
4/4 completed with zero MAPPO calls. The separate regulatory-cycle case invokes
the unchanged E5 actors once and completes 4/4. Original actor masks, selected
indices and participant identities were verified in saved inference records;
current receipt metadata is sent to the original independent ego controllers.

See [the measured table](VEHICLE_STATE_CONSISTENCY_RESULTS.md) for all thirteen
after/fault scenarios, waits, throughput, safety and color counts. Summary:

- Four-way: 4/4, zero MAPPO; regulatory cycle: 4/4, one MAPPO.
- Rule-resolved/two-vehicle: 2/2, zero MAPPO.
- Multiple left turns: 3/3, three MAPPO; mixed: 4/4, zero MAPPO.
- Rolling: 12/12, one MAPPO.
- Dense: 16 spawned, 5 completed, five MAPPO calls; SAFE_DEGRADATION.
- Five declaration faults and stale commitments: safe holds, no completed trips
  or unauthorized entry; these are not completion PASS results.

All cases have zero recorded collisions, blocked-zone violations and observed
unauthorized entries. The final eligible receipt/command verification independently
completed 4/4 with one MAPPO call and zero permission-color mismatches.
The existing safety fallback is reported explicitly; inference calls alone do
not establish direct learned-policy success or robust performance.

Four matched cases use identical before/after horizons: dense 70 s and up to
90 s for four-way/regulatory-cycle/rule-resolved, ending early only on complete
discharge. Waiting, throughput and full original negotiation events match
exactly. Dense 70-second censored metrics must not be compared directly with the
previous 360-second run. This is diagnostic evidence, not a frozen evaluation.

## Tests, website and integrity

Final complete focused suite: **210 passed in 29.42 s**. Additional final
showcase checks after the stale-card guard also pass; logs are retained under
`results/vehicle_state_consistency/20261016/`. No completion/safety assertion was
relaxed, and no long dense fixture/full scientific matrix was rerun for these
display-only changes. Earlier failed contract tests and the two new edge-case
failures remain logged; their fixes were verified rather than suppressing tests.

Actual same-launcher start/stop/relaunch, duplicate refusal, fresh scenario
frames and six HTTP routes passed. Browser discovery returned no connected
browser. Interactive clicks/screenshots are unavailable; this report does not
claim a visual browser rehearsal. The synchronized audit invokes the same
server-side display-state model used by the road/cards and records real positions.

All 2,334 historical evidence files remain SHA-256 identical. E5 remains
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`;
intention assets and scientific controller/protocol sources are unchanged from
the approved revision. Source snapshots and new receipts stay inside Component 2.
No root probe, duplicate project, package rebuild or unrelated cleanup occurred.
One diagnostic helper initially used a relative output path across different
working directories; its newly created probe outputs were relocated to the
intended evidence folder with all SHA-256 values verified, and its path is now
resolved absolutely. Existing research files were not moved.

## Commands and final classifications

From the workspace root:

```powershell
& 'C:\R26-DS-017\venv\Scripts\python.exe' -B socialmind_drive_showcase/app.py --server-only
```

Open `http://127.0.0.1:8088/component/right-of-way/live`. Use Regulatory Cycle
to demonstrate real MAPPO; Four-Way Simultaneous is a rule-resolved example.
Dense remains an explained partial case, not 16/16 success.

Audit commands (choose a fresh version when rerunning; evidence refuses overwrite):

```powershell
$projectPython = 'C:\R26-DS-017\venv\Scripts\python.exe'
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_vehicle_states.py --scenario congested_four_approach --duration 70 --version after_v1
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_vehicle_states.py --scenario four_way_simultaneous --duration 90 --version after_v1
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_vehicle_states.py --scenario regulatory_cycle --duration 90 --version final_receipt_v1 --command-trace
& $projectPython -B component_2_right_of_way_negotiation/tools/diagnose_vehicle_states.py --scenario rule_resolved_two --duration 45 --version after_faults_v1 --fault stale_commitment
& $projectPython -B component_2_right_of_way_negotiation/tools/report_vehicle_states.py
```

| Area | Classification | Scope |
|---|---|---|
| Vehicle state correctness | PASS | Measured permissions, colors, motion and dated evidence agree |
| Waiting-time behavior | PARTIAL | No obsolete GO cap proved; genuine dense dependency cycle remains |
| Genuine MAPPO inference | PASS | Eligible E5 calls/actions verified; no direct-policy robustness claim |
| Decentralized execution | PASS | Unchanged independent ego control, zero critic/global-control calls |
| Safety verification | PARTIAL | Zero observed violations/unauthorized entries in finite tests |
| Website accuracy | PARTIAL | Corrected contract/API/HTTP verified; interactive browser unavailable |
