# V1 audit and V2 repair candidate

The stopped V1 is diagnostic evidence. Its manifest, run records, reports and
warnings remain in `results/post_training_evaluation/`. A pre-edit runtime copy is in
`results/repair_diagnostics/v1_code_snapshot/`; the pre-edit file inventory is
`results/repair_diagnostics/v1_evidence_inventory.json`.

## Findings reported before editing

| V1 case | Exact trigger | MAPPO calls | Safety |
|---|---|---|---|
| multiple_left_turns | At 15.76 s, N↔S reciprocal precedence was classified COMMUNICATED_PRECEDENCE_DISAGREEMENT. The old §9 interpretation made opposite left turns mutually yield and collapsed uncertain turn candidates into mandatory obligations. | 0 | 0 collisions, 0 blocked-zone violations; 0/3 completed |
| four_way_simultaneous | At 15.76 s, E↔W reciprocal precedence blocked inference. A right-turning ego was made to yield unconditionally to an oncoming LEFT candidate. | 0 | 0 collisions, 0 violations; 0/4 completed |
| normal 404 | Both inferred epochs removed every precedence edge. E02 entered an internal lane under NATIVE_FOLLOWING, was promoted already inside at 36.84 s, then received a zero-distance SAFE_HOLD. At 36.88 s the blocked-entry invariant raised. | 2 | 0 collisions, 1 violation; aborted 0/8 |
| normal 606 | Earlier inferred epochs removed every edge. W02 received a new hold at 29.16 s too late to stop under native braking. At 29.48 s it had only 0.02765 m remaining at 5.156 m/s; at 29.52 s it entered the internal lane at 4.976 m/s and the invariant raised. | 2 | 0 collisions, 1 violation; aborted 0/8 |

V1 did not archive full per-step ego inputs, V2V claims or occupancy traces.
Those details were reconstructed through instrumented in-memory repetitions;
they are not presented as original saved traces. Saved result records and
event histories establish the classifications, edges and invocation counts.
SUMO emergency-braking warnings were secondary; no route/network defect was
demonstrated. The failures combine rule interpretation, claim reconciliation,
missing pair-order validation, follower admission and commitment timing.

Relevant files: `traffic_rules/rule_engine.py`,
`negotiation_learning/joint_graph_assembler.py`, `runtime_simulation/runner.py`, and
`negotiation_execution/ego_controller.py`. The inference-mode defect was in
`post_training_evaluation/runner.py`.

The §9 interpretation is checked against the [official StVO §9](https://www.gesetze-im-internet.de/stvo_2013/__9.html).
Opposite left turns do not create an unconditional reciprocal yield rule;
left turns yield to oncoming right turns, with physical geometry checked
separately. All other scope limitations remain explicit in the protocol.

## Repair behavior

The operational panel/evaluation path opts into corrected V2 rule interpretation
and stricter source reconciliation. Historical training/replay constructors
retain their original default behavior. Missing/stale source timestamps,
profiles, unsupported rules, absent physical evidence and invalid source ages
do not become negotiable disagreements. Valid mutual voluntary §11(3) claims
are distinguished from mandatory reciprocal claims. Mixed turn candidates
remain uncertain, rather than becoming unconditional mandatory yields.

The ego controller receives its own state, current endpoint commitments and
fresh sender-owned physical messages. Every relevant physical pair must be
ordered, cleared or nonconflicting. An unordered pair is rejected as
UNORDERED_PHYSICAL_CONFLICT. Only a valid MAPPO receipt for a legally eligible
pair permits deterministic fallback. Each endpoint uses the same published
incoming-lane arrival times, with an eight-ULP same-instant tolerance
`8 * ulp(max(1, abs(a), abs(b)))` and lexicographic vehicle-ID ties. This
tolerance handles floating representation; it is not a traffic time window.
Baseline outcomes cannot activate MAPPO fallback.

Mandatory §9 commitments survive execution even if MAPPO removes their claim;
such removal is recorded as rejection. Sender-owned movement metadata also
allows each execution endpoint to independently protect an actual oncoming
turning obligation. This metadata is not an actor input. The fallback does not
override protected turning obligations. Existing §8 claim relinquishment uses
the original explicitly accepted §11 waiver protocol; it does not invent a
new permission to disregard a rule.

Followers receive an ego-owned incoming-lane entry gate before promotion.
Returned admissible permission becomes committed when remaining entry distance
is no greater than SUMO's semi-implicit Euler comfortable braking gap plus
`speed * native_action_step_length`. Only then is admission locked through
rear clearance. A previously blocked entry still raises an invariant failure;
it is never retrospectively authorized. All ego speed caps still use native
SUMO stop speed and speed mode 31. Teleport is disabled in panel and evaluator.

No centralized graph computes runtime execution permissions. Global graphs
remain diagnostics and protocol bookkeeping. Actor graphs remain at most four
queue heads, while followers and clearing vehicles remain supported traffic.

## Frozen policy and inference

KEEP_CLAIM retains the incoming priority claim. Explicitly accepted
RELINQUISH_CLAIM removes that edge; rejected relinquishment retains it.
No edge is reversed by changing those trained actions. Protocol transition
code, actor weights and critic/training code were not changed. This repair
does not require E5 retraining; it changes runtime validation and its input
interpretation, so V1 and V2 measurements must remain separate.

The original `FinalSelectionInferenceProvider` inherits stochastic masked
sampling. V1 scientific evaluation incorrectly used presentation argmax.
`ScientificEvaluationProvider` restores the original sampling method with a
predeclared per-case action seed. Panel argmax remains presentation only.
Action seeds derive from SHA256 of protocol/scenario/demand seed/method and
are stored separately from demand seeds and checked during replay.

Selected E5 SHA-256:
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.

## Evidence and review boundary

The initial four regressions use `results/post_training_evaluation/v2_candidate/diagnostics/`;
the revised four use `results/post_training_evaluation/v2_candidate/diagnostics_followup/`.
`diagnostic_identity.json` captures code hashes, versions and budgets; it is
not a frozen final manifest. Per-run records include physical/ego/source traces,
warnings, outcomes, action seeds, integrity checks and artifact hashes.
Reports distinguish MAPPO_DIRECT, MAPPO_WITH_SAFETY_FALLBACK, RULE_RESOLVED,
and SAFE_HOLD. Fallback rate counts MAPPO epochs requiring eligible pair
fallback divided by MAPPO epochs, including rejections in the denominator.

Fresh proposed final demand seeds are 1103, 2207, 3301, 4409, 5501, 6607,
7703, 8807, 9901, 11003. These are not used to debug the repairs. Functional
failure cases are explicitly marked previously inspected regressions.
No V2 final manifest is prepared automatically. Running a suite requires a
previously prepared manifest; V1 roots are protected against V2 writes.

See the targeted report and commands document for actual validation outcomes.
Any residual safe stall is SAFE_DEGRADATION, not PASS. Existing complete
discharge assertions are retained. Acceptance remains pending when those fail.

## Measured repair outcome

The revised diagnostics used controller `EGO_ADMISSION_V2`, shield
`PAIR_ORDER_V2_1`, and the original seeded stochastic masked actor sampler.
They used only the previously inspected cases and fixed original budgets.

| Case | Budget (s) | Completed | Classification | Collisions | Blocked-zone violations | MAPPO events | Accepted | Rejected | Fallback | Maximum wait (s) | Timeout/deadlock |
|---|---|---|---|---|---|---|---|---|---|---|---|
| multiple_left_turns | 180 | 3/3 | PASS | 0 | 0 | 1 | 0 | 1 | 1 | 8.04 | No / No |
| four_way_simultaneous | 180 | 0/4 | SAFE_DEGRADATION | 0 | 0 | 0 | 0 | 0 | 0 | 157.84 | Yes / Yes |
| normal, seed 404 | 240 | 0/8 | SAFE_DEGRADATION | 0 | 0 | 0 | 0 | 0 | 0 | 217.84 | Yes / Yes |
| normal, seed 606 | 240 | 0/8 | SAFE_DEGRADATION | 0 | 0 | 0 | 0 | 0 | 0 | 217.84 | Yes / Yes |

The left-turn event is `MAPPO_WITH_SAFETY_FALLBACK`, not a direct MAPPO
success. Its action seed and KEEP choices match the first diagnostic attempt.
Initially the physically conflicting N/S pair had no original precedence
edge, so no fallback certificate existed. The revision admits only explicit
valid `UNRESOLVED_DUE_TO_TARGET_MANOEUVRE` candidate-conflict relations into
pair fallback eligibility, while excluding protected mandatory turning pairs.
Both egos compute the same queue-arrival order. The stopped-vehicle admission
boundary also includes SUMO's native uncapped release speed; a vehicle cannot
cross the entry line in the next step before receiving its admission lock.

Residual liveness failure is established in the new source traces, rather
than inferred from aggregate counts. At 15.76 s, the four-way and seed-404
cases have reciprocal E/W and N/S claims. Seed 606 has reciprocal N/S claims.
The first event remains `COMMUNICATED_PRECEDENCE_DISAGREEMENT` / `SAFE_HOLD`,
so no actor inference or fallback occurs in these three cases. Timestamps are
current and the adopted profile is consistent; incompatible target-intention
premises remain the issue. For example, in the four-way case E and W actually
follow their own RIGHT movements, but each local rule assessment predicts the
opposite vehicle LEFT and claims priority under 9(4). N is RIGHT and S is
STRAIGHT; N predicts S LEFT, while S predicts N LEFT, producing opposing
9(4)/9(3) claims. These route measurements explain the failure retrospectively;
they are not supplied as another ego's private actor observation or used by a
central controller to pick a winner.

Allowing these conflicting mandatory claims into MAPPO would weaken the
specified safety boundary. A further repair needs a validated decentralized
rule-premise reconciliation protocol that can distinguish an incorrect peer
prediction from a binding obligation. This candidate does not claim to solve
that remaining issue. Do not prepare or run final V2 while acceptance is pending.

Across the four revised episodes all integrity checks passed: zero training,
backward, optimizer, parameter-update, centralized-critic and global-execution
calls; ego-local execution true; global graph control false; frozen measured
sources and E5 state dictionaries unchanged. Fallback frequency is 1/1 MAPPO
events (100%); the other three cases never invoked MAPPO. An average of their
zero-event episode rates would misleadingly show 25%, so the panel report
now displays an event-weighted ratio and N/A when no events exist.

Focused checks: 81 passed in 10.53 s. Showcase checks: 74 passed in 2.03 s.
Full Component 2 suite: **734 passed, 2 failed in 704.27 s**. The actual log is
`results/repair_diagnostics/component2_full_tests.log`. Both failures are
existing assertions in `tests/test_ego_execution_and_dense_traffic.py`:
`test_real_congested_run_has_safe_dense_traffic_and_complete_discharge` returned
INCOMPLETE rather than COMPLETED; `test_live_state_exports_measured_counts_and_execution_flags`
observed 16 live vehicles rather than zero. These assertions remain unchanged.
**The all-existing-tests-pass requirement is not met.** This candidate requires
further liveness repair before acceptance, manifest preparation or Post-Training Evaluation.
The dense fixture's saved state is preserved as
`results/repair_diagnostics/dense_integration_live_state.json`: 16 scheduled,
16 spawned, 0 completed, 16 still active, zero collisions, zero blocked-zone
violations, maximum four negotiating participants and zero critic calls.

Both diagnostic iterations and their source snapshots are preserved. Replay
selects the matching archived source and verifies its complete inventory before
launching. The final reporting-only change occurred after the revised batch;
it does not relabel its recorded runtime identity or replace any run evidence.
The first iteration's runtime header incorrectly printed the fixed presentation
argmax label. Its individual POLICY_FACTOR records, saved action seeds and
archived provider show seeded stochastic sampling (including KEEP choices
below 0.22 probability when RELINQUISH exceeds 0.78). The revised logger prints
the provider's actual selection rule. The erroneous original header is retained
as evidence and is not used to infer how those actions were selected.

## Repair file inventory

Paths below are relative to Component 2 unless prefixed with the showcase
directory. Existing unrelated workspace edits are preserved.

- `traffic_rules/rule_engine.py`
- `negotiation_learning/message_models.py`
- `negotiation_learning/precedence_graph.py`
- `negotiation_learning/joint_graph_assembler.py`
- `negotiation_execution/ego_controller.py`
- `runtime_simulation/runner.py`
- `post_training_evaluation/models.py`
- `post_training_evaluation/scenarios.py`
- `post_training_evaluation/inference.py` (new)
- `post_training_evaluation/runner.py`
- `post_training_evaluation/metrics.py`
- `post_training_evaluation/aggregation.py`
- `post_training_evaluation/reporting.py`
- `post_training_evaluation/replay.py`
- `post_training_evaluation/diagnostics.py` (new)
- `run_post_training_evaluation.py`
- `tests/test_runtime_v2_safety.py` (new)
- `tests/test_v2v_joint_graph.py`
- `tests/test_traffic_rules.py`
- `tests/test_post_training_evaluation.py`
- `docs/POST_TRAINING_EVALUATION_GUIDE.md`
- `docs/REPAIR_V2_AUDIT.md` (new)
- `docs/REPAIR_V2_COMMANDS.md` (new)
- `results/repair_diagnostics/verify_repair_evidence.py` (new evidence verifier)
- `socialmind_drive_showcase/services/evaluation_reader.py`
- `socialmind_drive_showcase/pages/component2_evaluation.py`

Generated evidence is confined to `results/repair_diagnostics/` and
`results/post_training_evaluation/v2_candidate/diagnostics*/`. The selected checkpoint
and inventoried V1 evidence files are unchanged.
