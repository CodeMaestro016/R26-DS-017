# Final readiness summary — 16 October 2026

**READY WITH LIMITATIONS for an honest qualitative viva demonstration and
read-only evidence review. NOT READY to claim a completed final quantitative
study.** No long final/scalability suite was authorized or launched.

## Files and evidence inspected

Component 2 and showcase READMEs; POST_TRAINING_EVALUATION_SCOPE.md and GUIDE;
REPAIR_V2_AUDIT.md and COMMANDS; the saved repair validation receipt;
all current final/targeted/scalability manifests and result/provenance records;
the saved aggregate and reports; selected_configuration.json, selection report,
progress and model-selection comparison records; congested presentation
records; scenario catalog, queue-head selection, runtime/evaluator/integrity,
metric/aggregation/resume implementation; active tests/configuration; showcase
app/config, launcher, live reader/view, evaluation reader/page, history reader
and presentation controls. The initial audit and hash inventories identify
every inspected archived episode and its verification status.

## Confirmed issues and changes

- Added workspace pytest.ini and Component 2 tests/conftest.py: normal root
  collection now selects only active Component 2/showcase tests and retains
  component-relative test asset resolution. Historical tests were not deleted.
- Updated showcase services/component_launcher.py: owned run tokens/logs,
  stop-during-startup handling, generation-aware grace cleanup, explicit
  missing-SUMO/E5/psutil errors and application shutdown cleanup. Only owned
  processes are targeted; no broad process-image termination is introduced.
- Updated services/live_state_reader.py and pages/component2_live_view.py:
  reject old/malformed/nonfinite frames, distinguish startup/failure/stale
  state, show N/A for missing metrics, avoid calling incomplete discharge
  complete, and provide the existing default rolling scenario as an option.
  Existing scenario definitions, layout and navigation are preserved.
- Updated app.py: registers owned launcher shutdown, checks desktop dependency,
  invalid/busy ports, and serves only current-launch live snapshots.
- Updated services/evaluation_reader.py and pages/component2_evaluation.py:
  read the authentic existing smoke aggregate, independently verify archived
  final episode metadata/counts, separate 34/165 final records from nine smoke
  episodes, show incomplete warnings/N/A, preserve raw groups and figures, and
  use the actual artifact plot directory. Scientific statistics are not
  recomputed or modified by the frontend.
- Added tests/test_final_readiness.py and declared psutil in showcase requirements.
  Installed missing presentation dependencies pywebview 6.2.1 and psutil 7.2.2;
  scientific Python package versions are unchanged. Added read-only audit,
  lifecycle, packaging and verification utilities under Component 2 tools/.
- Clarified active evaluation-scope/guide and README documentation; created
  all requested readiness/preflight/dense/scalability/test/package/viva/comment
  documents. No scientific runtime/evaluator source, manifest or result was edited.

## Newly executed verification

- Root collection: 947 active tests, zero collection errors, 4.85 seconds.
- Full Component 2: 848 passed, two existing strict liveness xfails,
  1012.22 seconds. Full showcase: 97 passed, 1.71 seconds. No warnings in
  either final full-suite log; existing assertions/xfail markers were preserved.
- Two real short qualitative launch/stop checks and one active shutdown
  check: actual telemetry, duplicate launch refusal, graceful cleanup,
  no remaining owned process. These are USER_STOPPED presentation plumbing
  checks, not scientific performance episodes.
- Six actual HTTP routes returned 200; evaluation delivered both 34/165 and
  SMOKE_NOT_FINAL. Prerequisite faults refuse startup before process creation.
  pip check passes; Windows desktop backend imports. No connected Browser
  was available, so visual/native-window interaction still needs rehearsal.
- All 2,334 inventoried original result/archive files and 151 protected
  scientific source/model/configuration assets match their pre-task SHA-256.
  Selected E5 bytes/tensor content and intention assets are unchanged. E5 hash:
  `2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.

## Genuine research status and presentation-safe evidence

V1 final archive: **34/165**, 131 missing; 10 PASS, 22 SAFE_DEGRADATION,
2 UNSAFE_FAILURE, zero recorded INVALID among verified final records. Nine
smoke episodes are separate. The current V2 final protocol has no accepted
manifest and no final episodes. Seven-load scalability scientific rows are
NOT_RUN; only marked preflights exist. Do not present incomplete results as
a completed study or broader scalability evidence.

Present the bounded research architecture/selection, genuine older qualitative
16/16 success and later incomplete presentation, together with scientific
PV-04A 1/16 and PV-04B 0/16 failures. Safety and liveness are distinct;
zero observed collisions is not successful/generalizable discharge. Waiting
and exposure can be censored; no-completion trip statistics remain N/A.

An isolated missing-SUMO backend fault exposed a secondary Not connected
finalizer error. Its log is preserved; UI prerequisite guards now prevent
that missing-binary launch. Direct-CLI fault cleanup was not changed because
scientific runtime edits require separate review. Other components' remote
GPU services and manual desktop/page interaction were not asserted verified.

## Package and next approval boundary

Use only `deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip` as the
final presentation bundle. It is 15,823,421 bytes (about 15.1 MiB), SHA-256
`b7b08c607428a9c00f105f8b66d0949333ff9ba4168f41f38eb10ae08016a311`.
It passed ZIP byte checks and fresh-extraction import/model/scenario/evidence
checks, including the genuine 34/165 and nine-smoke counts. Preliminary package
drafts are not the hand-in artifact. Extract to a short Windows folder, such
as C:\SOCIALMIND_DRIVE, to avoid legacy path-length limits. Keep full research
archives separately; the minimal bundle cannot reproduce historical per-step
replay or continue frozen experiments without their archived source/traces.

The final verification receipt is
`results/final_readiness/20261016/final_verification.json`.
See FINAL_VIVA_RUNBOOK.md for startup/16-vehicle demonstration instructions;
FINAL_TEST_VERIFICATION.md for exact newly executed commands/logs;
DENSE_TRAFFIC_EVIDENCE_SUMMARY.md and PANEL_COMMENTS_RESOLUTION.md for defensible
presentation claims; FINAL_PACKAGE_AUDIT.md for the package inventory.

**Approval is still required for the long final suite.** The saved V2 acceptance
gate remains false, and trace-storage planning (~143 GiB, ~286 GiB with a 2x
reserve) exceeds roughly 38 GiB available. Review/resolution of acceptance,
storage and any proposed scientific behavior change must precede preparation
and explicit approval of the long run. No manifest mismatch is bypassed.
FINAL_EVALUATION_PREFLIGHT.md contains exact current/missing counts and clearly
conditional future commands; they are not permission to execute the suite.
