# Component 2 naming migration

This is a source/import, command, path and presentation-label refactor only.
No policy, rules, action meanings, schedules, metrics, classifications or
recorded scientific values are changed. No scientific experiment is launched
and no historical report is regenerated. The 165-episode study is not claimed
to be completed by this migration.

## Renamed active paths

| Previous path | Preferred path |
|---|---|
| panel_demo/ | runtime_simulation/ |
| panel_validation/ | targeted_validation/ |
| final_evaluation/ | post_training_evaluation/ |
| run_panel_demo.py | run_runtime_simulation.py |
| run_panel_validation.py | run_targeted_validation.py |
| run_final_evaluation.py | run_post_training_evaluation.py |
| tests/test_panel_demo.py | tests/test_runtime_simulation.py |
| tests/test_panel_validation.py | tests/test_targeted_validation.py |
| tests/test_final_evaluation.py | tests/test_post_training_evaluation.py |
| docs/PANEL_VALIDATION_GUIDE.md | docs/TARGETED_VALIDATION_GUIDE.md |
| docs/FINAL_EVALUATION_GUIDE.md | docs/POST_TRAINING_EVALUATION_GUIDE.md |
| docs/FINAL_EVALUATION_SCOPE.md | docs/POST_TRAINING_EVALUATION_SCOPE.md |
| showcase pages/component2_panel_validation.py | pages/component2_targeted_validation.py |
| showcase services/panel_validation_reader.py | services/targeted_validation_reader.py |
| showcase tests/test_panel_validation_reader.py | tests/test_targeted_validation_reader.py |

Package moves include their existing implementation files. Tracked paths were
moved with `git mv`; untracked paths used filesystem moves. Thin aliases now
occupy the old package/CLI locations; they contain no duplicate algorithms.

Future outputs use `results/runtime_simulation/`,
`results/targeted_validation/`, and `results/post_training_evaluation/`.
Future generated reports use TARGETED_VALIDATION_REPORT.html/.md and
POST_TRAINING_EVALUATION_REPORT.html/.md. All historical directories and report
filenames remain exactly where originally recorded. Active scalability command
names and its result-family paths remain unchanged.

## Audit and research preservation

The pre-edit occurrence audit classified every matched term by path/line into
active source/import, test, documentation, showcase/UI, generated current-path
reference, or historical evidence/archive. Counts were A=97, B=123, C=160,
D=20, E=1 and F=4,779. Details are in
`results/naming_migration/occurrences.csv` and `occurrence_counts.json`.
The immutable-file SHA-256 inventory covers 1,683 files under existing results,
including recorded runs, hashes, reports, diagnostics, snapshots and replay
evidence. Those files were not renamed, edited, moved, regenerated or re-hashed
in place. Verification computes hashes separately without updating originals.

A 293-file pre-migration runtime/assets copy was added under
`results/naming_migration/pre_migration_runtime/`, separate from every existing
archive. Its inventory preserves the exact original source spelling and bytes.
`migration_files.json` lists every moved path and initial active-text edit.
Additional compatibility changes are covered by the migration's tests and
post-migration verification receipt.

E5 remains at its existing research checkpoint path; its SHA-256 is
`2ab2029fdd66f96c3ba0acf5e76487c96740161e898539f93c726228097eaf57`.
Tests compare all checkpoint tensors with the saved original and verify byte
identity of traffic rules, execution/learning/training sources and network
inputs. AST comparisons verify runtime decisions, queue-head selection,
inference, metrics, classifications and scenario generation after the declared
name substitutions. No model training or scientific runtime is executed.

## Compatibility

`naming_compat.py` aliases old packages and submodules to the same canonical
module objects. This keeps old imports and serialized Python references valid,
without loading a second operational implementation. Old CLI scripts delegate
to their preferred replacement. `run_panel_demo` remains a callable alias of
`run_runtime_simulation` at the package and runner levels. The old showcase
reader/page paths delegate to renamed functions. Reader schemas and historical
protocol identifiers remain unchanged so saved scientific evidence still parses.

Frozen manifests intentionally retain old source keys and hashes; renamed
live code is not declared identical to them. `historical_replay.py` validates
original result/provenance/artifact hashes and action seed, finds exact archived
source bytes, constructs only the original manifest-listed source set, and
launches an isolated worker using original imports. Replay outputs go to a new
preferred-name replay directory, never into original evidence. Missing exact
sources cause a clear refusal rather than a substituted implementation. The
preferred PV-03 replay automatically finds its preserved record when no new
targeted manifest exists. Exact old roots and run IDs remain selectable.

The existing archived diagnostic worker retains its original script filename.
The original V1 worker in targeted_validation/v1_replay.py deliberately retains
legacy imports because it runs archived code. Its future replay output path
uses the preferred family. No replay was actually launched for this migration;
tests check routing and original source sets without stepping SUMO.

Preservation tests resolve original active source paths to the pre-migration
archive for their exact old-byte assertions. Separate tests independently check
the current implementation's operational equivalence and unchanged rules and
weights; archive-based assertions are not used to conceal a logic change.

Showcase readers prefer new output paths and fall back to preserved historical
summaries. They do not recalculate, rewrite or reclassify scientific values.
Stable schema names such as panel_summary.json, TARGETED_PANEL_VALIDATION,
PANEL_AV vehicle IDs, and stored protocol identifiers remain intentional; changing
them could alter evidence interpretation or seed derivation. They are not
user-facing implementation labels. Old words also intentionally remain in
compatibility mappings, archived-worker imports and historical path references.

Existing scalability manifests remain frozen and may reject the renamed live
checkout for new execution, as they should. Use their original archived source
set when reproducing them; do not re-freeze or overwrite an old manifest merely
to accept renamed source hashes. Their recorded values/reports are unchanged.

## Preferred commands

Run from Component 2 with the project's existing environment:

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"

& $projectPython -B run_runtime_simulation.py --scenario congested_four_approach --gui
& $projectPython -B run_targeted_validation.py --report-only
& $projectPython -B run_targeted_validation.py --replay PV-03 --gui
& $projectPython -B run_post_training_evaluation.py --suite smoke
```

These are usage commands, not simulations executed during the migration.
The smoke command still requires an explicitly prepared matching manifest in
its new output family; naming does not bypass experimental preparation rules.
The targeted report-only command can display preserved measurements in a new
preferred-name report without touching the original historical report. No new
scientific result is implied. Do not regenerate old reports in place.

## Verification — 10 October 2026

Final selection: **285 passed in 57.19 seconds**, without warnings. It includes
the renamed runtime/targeted/post-training unit tests, scalability V1/V2
contracts, runtime safety tests, showcase tests and new naming/compatibility
tests. Import and CLI checks cover all three preferred entry points and all
three legacy CLI aliases. Historical replay tests reconstruct original source
sets in isolated interpreters and mock the actual replay launch.

```powershell
& $projectPython -B -m pytest tests/test_naming_migration.py tests/test_runtime_simulation.py tests/test_targeted_validation.py tests/test_post_training_evaluation.py tests/test_panel_dense_v2.py tests/test_runtime_v2_safety.py tests/test_scalability_validation.py tests/test_scalability_validation_v2.py ../socialmind_drive_showcase/tests -q
```

The full Component 2 regression suite was not launched because it includes
long SUMO integration episodes and training tests unrelated to this rename.
No scientific SUMO episode, preflight, replay, training run or 165-episode
evaluation was executed. No recorded scientific value, historical report,
manifest, provenance or stored checksum was regenerated. All 1,683 historical
files and all 293 copied pre-migration runtime/assets are checked separately
against their original SHA-256 inventories. E5 bytes and all checkpoint tensors
match the preserved original. The active-source whitespace check passes with
existing CRLF line endings accepted; historical files are not normalized.

The machine-readable receipt is
`results/naming_migration/post_migration_verification.json`.
