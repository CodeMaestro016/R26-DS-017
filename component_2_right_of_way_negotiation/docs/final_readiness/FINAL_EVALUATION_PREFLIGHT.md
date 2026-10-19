# Final evaluation preflight — 16 October 2026

**BLOCKED; no long-suite approval or execution.** This document is not an
official completed-evaluation report.

## Protocol and exact counts

Archived V1: FINAL_EGO_LOCAL_EVALUATION_V1, manifest
`061324320e90e8a6387f9913ea6ce9cec4df86a819ab6cedc3304a51955eddf0` at `results/final_evaluation/manifest.json`.
Manifest, result, provenance and demand checksums verify for 34 final records;
**34/165 recorded final episodes; 131 missing**. Recorded episodes are not
equivalent to successful discharge. Nine separate smoke episodes (5 PASS,
4 SAFE_DEGRADATION) are excluded from that count. The saved latest aggregate
describes smoke, not the final archive.

| Method | Expected | Verified final | Missing | PASS | SAFE_DEGRADATION | UNSAFE_FAILURE | INVALID |
|---|---|---|---|---|---|---|---|
| PROPOSED_MAPPO | 55 | 12 | 43 | 4 | 6 | 2 | 0 |
| RULE_PLUS_FCFS | 55 | 11 | 44 | 5 | 6 | 0 | 0 |
| RULES_ONLY | 55 | 11 | 44 | 1 | 10 | 0 | 0 |


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
Using the observed V1 median wall/sim ratio gives roughly 10.0 hours
for all budgets. A conservative observed maximum ratio scaled by
32/8 for the largest population gives 100.2 hours.
These are planning extrapolations, not reliable bounds: larger populations,
machine load and early stops can change cost substantially. They are not
permission to start the study.

Largest observed final episode directory: 0.05 MiB.
The legacy V1 metadata-only extrapolation is 0.03 GiB,
but **must not be used as V2's required disk reserve**, because V1 did not save
the same per-step traces. Using the maximum observed traced bytes per scheduled
vehicle-second from `results\panel_validation\v2\runs\20261009T063931819195Z_dee74d22` (17.56 MiB,
38.08 simulated seconds, 4 scheduled vehicles),
the full planned 1,269,180 scheduled vehicle-seconds project
about **142.85 GiB of trace/evidence storage**. A 2x
planning reserve is **285.69 GiB**, excluding the
environment, extra diagnostics and duplicated archives. This linear exposure
projection can still underestimate richer interactions and is not a bound.
Available disk at audit: 37.98 GiB, below both
the traced-storage projection and the planning reserve. **Storage planning is
an additional blocker**: review/add capacity before approval. Retain full traces;
do not remove evidence merely to make a run fit.

## Commands and approval boundary

**There is currently no approved runnable long-suite resume command.**
The following are conditional future commands only, after documented acceptance,
source review and explicit user approval. They were not executed:

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017\component_2_right_of_way_negotiation"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
# ONLY after the V2 acceptance/preparation gate is resolved and approved:
& $projectPython -B run_post_training_evaluation.py --prepare --output-root "results\post_training_evaluation\v2_candidate"
# ONLY after separate explicit approval of the long suite:
& $projectPython -B run_post_training_evaluation.py --suite final --output-root "results\post_training_evaluation\v2_candidate"
# Resume only the same approved matching manifest; review interrupted directories first:
& $projectPython -B run_post_training_evaluation.py --suite final --output-root "results\post_training_evaluation\v2_candidate"
```

The readiness audit does not regenerate the archived smoke or final reports.
Official V2 reports may be generated from authentic approved archived runs
after that evaluation, with incomplete/invalid/no-completion cases retained.
