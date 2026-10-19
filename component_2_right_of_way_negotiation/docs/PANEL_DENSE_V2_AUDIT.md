# Dense evidence audit and reviewed V2 design

V1 is immutable evidence, not a result to erase. Its 59 files (including the
existing global latest reports) are inventoried in
`results/panel_validation_archives/v1/evidence_inventory.json`. Its measured
runtime, assets and unchanged E5 are copied to a separate archive with a
175-file SHA-256 inventory (including the GUI settings required for replay).
V2 writes only `results/targeted_validation/v2/`;
archived replays write only `results/targeted_validation/replays/v1/`.

## Exact PV-04 root cause

The recorded run is `20261008T171632326120Z_c654aaee`, under
`results/panel_validation/v1/runs/`. Its immutable result and source/decision
trace establish:

- 16 scheduled and spawned, zero completed, zero throughput and zero actor
  calls; SAFE_DEGRADATION, not PASS.
- First coordination event: 15.76 s, physical participants E01/N01/S01/W01;
  assembled participant graphs have at most four nodes. Followers are not
  admitted as extra negotiating nodes.
- North's own movement is STRAIGHT. Its candidate for South is LEFT, producing
  S01 → N01 under DE-STVO-9-3. South's own movement is RIGHT. Its candidate for
  North is LEFT, producing N01 → S01 under DE-STVO-9-4. These are conflicting
  target-intention premises; the reciprocal pair is not a valid grant of
  mutual mandatory priority for the actual movements.
- Each relevant conflict/regulatory source timestamp is 15.76 s, observation
  age zero, `source_snapshot_consistent=true`, current EGO_LOCAL_V2
  interpretation and profile DE_STVO_UNCONTROLLED_4WAY_V1. No stale source or
  incompatible profile explains this event. Adopted communicated claims bring
  the reciprocal N/S pair into all four local joint graphs.
- `JointLocalPrecedenceGraphAssembler.assemble` identifies a hard reciprocal
  pair; the local negotiation gate returns
  COMMUNICATED_PRECEDENCE_DISAGREEMENT. `runtime_simulation.runner` places this status
  in BLOCKED rather than NEGOTIABLE. No actor/proposer/responder action is
  requested. This is why MAPPO calls are zero, not a disconnected model.
- Execution epoch is ((PANEL_DEMO,), 15.76,
  CONTINUOUS_JOINT_NEGOTIATION_CONTEXT). Coordination is intentionally
  incomplete because the source authority is blocked. The controller's
  MISSING_OR_STALE_LOCAL_COORDINATION reason covers missing authorization here;
  that generic string alone does not prove stale V2V data.
- Heads stay HELD_BEFORE_ZONE; followers receive
  FOLLOWER_AWAITING_NEGOTIATED_ADMISSION. At the stop every vehicle is on an
  incoming lane at speed zero, four queued per approach. No conflict-zone
  commitment or clearance is preventing release: there was no admitted entry.
- Stable stationary held evidence begins at 48.84 s; the unchanged 15-s
  criterion confirms deadlock at 63.84 s. Zero collisions and zero blocked-zone
  violations are recorded, with valid decentralized runtime integrity.

The deterministic rule table correctly applies its conditional rules to the
candidate movements it receives. The audit does not establish a new table,
freshness, queue-head or clearance implementation bug that can be safely fixed
by changing a local condition. There are legitimate mandatory rules in the
graph, but the opposing beliefs do not prove both reciprocal obligations are
legitimate. This is an unresolved intention/claim-reconciliation liveness
limitation exposed by the conservative safety repair. The existing initial
N-straight/E-straight/S-right/W-left schedule reliably encounters that known
condition. It is preserved as the critical case, not called a malformed or
invalid experiment.

Sending these mandatory contradictions to MAPPO would weaken the required
safety gate. A future protocol for reconciling sender-owned rule premises may
be possible without changing KEEP/RELINQUISH meanings, but this evidence does
not establish that repair. No such algorithm change is made in this task.
The present evaluation changes preserve trained action semantics and require
no retraining. They do not claim to cure the underlying liveness defect.

## Review and fixed nominal design

Before editing, the audit and exact schedule were presented in chat. The user
approved: **“Approve the schedule and one run.”** That authorizes one PV-04A
measurement after checks, not a scenario search or automatic full-suite run.

| Approach | Vehicle 1 | Vehicle 2 | Vehicle 3 | Vehicle 4 | Departures (s) |
|---|---|---|---|---|---|
| North | LEFT | STRAIGHT | RIGHT | LEFT | 0, 1.5, 3, 4.5 |
| East | LEFT | RIGHT | STRAIGHT | LEFT | 0, 1.5, 3, 4.5 |
| South | LEFT | STRAIGHT | RIGHT | LEFT | 0, 1.5, 3, 4.5 |
| West | STRAIGHT | LEFT | RIGHT | STRAIGHT | 6, 7.5, 9, 10.5 |

Only legal movement, approach and scheduled departure are predefined. No
permissions, winners or actor outputs are scripted. The design has 16 vehicles,
four per approach, all 12 movements, short continuous headways and overlapping
conflicts. Three initial left turns supply a legitimate opportunity already
represented in the bounded scope; West is staggered to avoid deliberately
repeating the known initial N-straight/S-right contradiction. Later conflicts
may still stall. There is no guarantee of PASS or of MAPPO invocation; zero
calls must be explicitly reported as missing learned-negotiation evidence.

PV-04A has a predeclared 180-s maximum. PV-04B preserves the original critical
schedule and its V1 record without changing any value or rerunning it in this
task. Both remain visible. The V2 design has seven cases/seven traffic episodes
(PV-02 has two methods; PV-06 has controlled checks) and a maximum total budget
of 750 simulated seconds. Only PV-04A is run in this task.

## Existing two dense integration failures

The original 734-pass/2-fail record remains unchanged. Both failed assertions
require complete discharge of the same critical 16-vehicle demand: COMPLETED
rather than INCOMPLETE, and zero live vehicles rather than 16. They reflect a
real unresolved liveness limitation, not obsolete evidence that liveness is
irrelevant. The new validation wrapper did not introduce this behavior.

Their original assertion bodies are retained as **strict expected failures**
with the documented cause. This does not mean liveness is fixed. A recovered
result produces strict XPASS and requires review/removal of the marker.
Markers accept only AssertionError from those unmet discharge requirements.
The shared fixture validates exact spawn counts, unchanged tensors/policy,
decentralized execution, zero unsafe/critic/training operations, <=4 actors,
congestion/moving coverage and live-state equality. A changed incomplete
failure mode is rejected. Fixture assertion breaches are converted to
RuntimeError so the expected-failure markers cannot conceal them. Separate
unmarked safety and live-consistency tests also exercise the same fixture.

The full regression suite is not rerun here: it would execute another dense
traffic episode, contrary to this task's instruction to run only PV-04A once.
Focused tests verify the guarded test contracts. The production suite now has
explicit known-liveness expectations, but a full green run is not claimed.

## Evidence presentation and files

The V2 report labels inherited rows PANEL_VALIDATION_V1 (preserved historical
record). They retain their original run IDs, metric values, action seeds,
classifications and manifest hashes. Future V2 reruns appear alongside V1,
never as silent replacements. Successful capability evidence contains actual
PASS records; failed capability cases remain in limitation evidence. MAPPO
fallback labeling is per event: PV-03's first event is fallback-resolved, while
its later direct event remains MAPPO_DIRECT. No whole-episode pure-MAPPO claim
is made from that mixed event history.

Nominal and critical dense fairness panels show observed/censored waiting,
TTT, throughput, service-order inversions, active/moving counts, queues,
negotiation calls/results/fallback and guard evidence. SUMO emergency-braking
log warnings are reported separately from measured braking episodes; missing
historical warning counts remain N/A rather than invented zeros. Per-event
and per-version provenance remain explicit. This is targeted simulation-based
validation in SUMO; inD supports intention-model provenance only.

Modified files: `targeted_validation/cases.py`, `models.py`, `runner.py`,
`metrics.py`, `reporting.py`; `run_targeted_validation.py`;
`tests/test_targeted_validation.py`, `tests/test_ego_execution_and_dense_traffic.py`;
`socialmind_drive_showcase/services/targeted_validation_reader.py`,
`socialmind_drive_showcase/pages/component2_targeted_validation.py`.
Created files: `targeted_validation/v1_replay.py`, `tests/test_panel_dense_v2.py`,
this audit and `docs/PANEL_DENSE_V2_COMMANDS.md`. Generated inventories,
archived runtime/model copies and receipts are separate from immutable V1.
No operational controller, rule, negotiation, physics or E5 file is modified.

## Approved one-run outcome

The approved PV-04A measurement was executed exactly once, run
`20261008T175551068657Z_095c9470`, against frozen manifest
`9bee17559fd5f49ee1d912e8c003c00f5800d7b34a99278f61d48cc4f042ec74`.
All 16 vehicles spawned; 1 completed (6.25%) and 15 remained at the
180-second hard budget. Classification is SAFE_DEGRADATION, with timeout and
observed deadlock. This does not demonstrate successful dense discharge.

There were two authorized MAPPO events, both safety-fallback outcomes:
zero accepted outcomes, two shield-rejected outcomes, fallback rate 1.0,
zero rule-resolved events and one renegotiation. Maximum active and moving
vehicles were both 16; maximum queue depth was four on each approach,
with at most four physical queue heads participating. The final heads were
held by unresolved local precedence obligations. The exact stationarity
criterion did not trigger early termination; the recorded termination is
HARD_TIME_BUDGET, not DEADLOCK_CONFIRMED. No criterion or demand was changed
after observing this failure, and no second trial was performed.

Collisions, blocked-zone violations, native emergency-braking events and
SUMO emergency-braking warnings were all zero. Censored team travel time was
2697.32 vehicle-seconds; completed-vehicle mean travel time was 57.32 seconds
(one completion). Mean/p95/maximum observed waiting was
141.87/157.84/157.84 seconds. Throughput was 0.3333 vehicles/minute.
Approach mean waits E/N/S/W were 150.95/116.59/153.74/146.20 seconds,
with a 37.15-second gap. FCFS inversion rate is unavailable: zero eligible
served pairs. These censored statistics cannot establish congestion fairness.

The generated V2 report shows both this failed nominal case and original
PV-04B (0/16, zero MAPPO calls), explicitly labeling inherited V1 evidence.
The new execution did not rerun other panel cases or the 165-episode study.
Focused checks passed: 39 tests in 11.94 seconds. The full production
regression suite was not rerun; its two documented strict expected liveness
failures retain their original assertions and separate safety/fixture guards.

Post-run SHA-256 checks found no changes in 59 original panel evidence files,
337 original final-evaluation evidence files or 175 archived runtime/assets.
Training, backward calls, optimizer steps, parameter updates, centralized
critic calls and global execution calls were zero. Execution remained
decentralized; the policy hash before and after was
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
Machine-readable measurements and verification are in
`results/targeted_validation/v2/post_run_verification.json`.
