# Initial research-readiness audit — 16 October 2026

This audit precedes presentation/test-configuration changes. No scientific
runtime, checkpoint, manifest, schedule, baseline, rule or result is changed.
Source: `results/final_readiness/20261016/initial_audit.json`.

## Evaluation status

The preserved `results/final_evaluation/manifest.json` is the checksum-valid
FINAL_EGO_LOCAL_EVALUATION_V1 protocol. It specifies 165 final episodes with
old demand seeds 101..1010 and presentation argmax inference. Exactly 34 final
episode records verify against result/provenance checksums, manifest identity
and demand hashes: 10 PASS, 22 SAFE_DEGRADATION and 2 UNSAFE_FAILURE; 131
matrix entries are missing. Nine separate smoke records verify: 5 PASS and
4 SAFE_DEGRADATION. Smoke is not part of the final 34/165 count.

The existing `latest/aggregate.json` describes those **nine smoke episodes**,
not the 34 recorded final episodes. It explicitly says SMOKE_NOT_FINAL.
Neither `results/final_evaluation/v2_candidate/` nor the preferred
`results/post_training_evaluation/v2_candidate/` contains a final manifest.
The current V2 evaluator proposes 165 episodes, fresh seeds 1103..11003 and
seeded stochastic masked sampling; it must not silently resume the V1 matrix.

`results/final_evaluation_development/` contains seven smoke records, none
passing this audit's full manifest/provenance verification. They remain
development evidence and are excluded from verified scientific totals.

## Acceptance and integrity

The saved repair receipt says ready_for_final_evaluation=false: three targeted
cases stall and complete-discharge assertions remain unmet. REPAIR_V2_AUDIT.md
explicitly prohibits V2 preparation/execution while acceptance is pending.
No subsequent accepted final manifest was found. Existing V1 sources differ
from renamed/current source paths. The executable is SUMO 1.26.0, matching
the recorded binary; Python TraCI/SUMO tools are 1.27.1. Neither source hashes nor the manifest may be rewritten
to bypass those differences. There is no currently approved safe long-suite
resume command. Review/acceptance and explicit user approval are required.

Selected E5 SHA-256 matches its frozen selection record:
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
The selected checkpoint is canonical replication 0, chosen under the bounded
E5/E10/E15 validation protocol. Selection is not a universal optimality claim.
The recorded held-out baseline failed one hard safety-validity gate, so a
complete safety-valid overall efficiency comparison is unavailable.

## Dense traffic and scalability

Authentic qualitative records include 16 scheduled/spawned/completed vehicles,
peak active/moving counts of 16, six MAPPO decision epochs and zero collisions
or blocked-zone violations. They describe older presentation runs, not guaranteed
current performance. The newer preserved latest qualitative congested record
is INCOMPLETE with 0/16 completed. Scientific targeted evidence includes PV-04A
1/16 and critical PV-04B 0/16, both SAFE_DEGRADATION; these failures remain visible.
The seven-load scalability V1 and V2 families each contain only one marked
preflight. Their scientific 4/8/12/16/24/32/40 results remain unexecuted.

## Environment and presentation findings

Existing environment: `C:\R26-DS-017\venv\Scripts\python.exe`, Python 3.13.1,
pytest 9.1.1, Torch 2.14.0, NiceGUI 3.16.0, NumPy 2.5.2, ONNX Runtime 1.29.0;
SUMO is on PATH. pywebview and psutil are missing in the initial environment.
Thus desktop mode and reliable owned-child fallback termination need attention.
No prerequisite is assumed installed merely because it appears in requirements.

Root pytest collection incorrectly enters historical source snapshots under
results, reproducing a missing archived debug_dashboard.html error after
collecting 699 tests. Archived tests must be excluded, not deleted. Active
Component 2 tests also assume their component working directory.

The existing launcher has an early-stop/startup race, does not stop its owned
run on application shutdown, and returns generic startup errors without a
saved per-launch log. The live page can show an old frame during a new launch,
label a failed process FINISHED and label incomplete discharge SCENARIO COMPLETE.
The selector omits the existing default rolling scenario. Layout and control
semantics will be preserved while addressing these presentation-only issues.

The evaluation reader searches preferred/V2-candidate roots but not the existing
V1 smoke aggregate. The page omits final expected/verified counts and uses the
preferred plot root even when displaying a fallback aggregate. Fixes must remain
read-only and label smoke, partial final archives and no-completion metrics clearly.

## Authorized verification boundary

Run new focused UI/evidence-reader tests and full active Component 2/showcase
test suites. Existing integration fixtures may exercise SUMO in temporary
test directories; this is not permission for the 165-episode study. Preserve
existing strict xfail markers and all assertions; report them explicitly.
Any new failures are reported, not skipped or repaired through algorithm changes.
Browser/server checks and a short explicitly stopped qualitative live check
may verify launch/stop behavior; they must not be presented as quantitative validation.

The pre-change inventory covers 2,334 historical files (2,441,563,403 bytes),
and a separate protected-source inventory covers runtime, rules, geometry,
models and evaluator/scalability code. Post-work hashes will verify preservation.
