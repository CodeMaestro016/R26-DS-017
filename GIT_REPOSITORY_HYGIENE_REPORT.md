# Git Repository Hygiene Report

## Scope and safety boundary

This audit covers the current SOCIALMIND DRIVE workspace and preserves the uncommitted Component 2 reorganization. It changes tracking policy and the Git index only. No local research artifact was deleted, no training or experiment was run, no commit or push was made, and Git history was not rewritten.

## Before-cleanup state

- Branch: `iresha`.
- Remote: `origin` at the public GitHub repository; no embedded credential was present in the reported URL.
- Branches inspected: local `iresha`, `main`, and the available `origin/*` collaborator branches.
- Index tracked files: 593.
- Tracked files matching ignore rules: 54.
- Visible untracked files: 53, mainly the new workspace documentation and complete showcase source/assets.
- The working tree already contained the large staged Component 2 relocation: 592 Git-detected renames plus authorized source/configuration/documentation changes. This work was preserved.
- `.gitattributes` was absent.

## Problems found

The old `.gitignore` contained malformed space-prefixed pseudo-rules and broad `*.json`, `*.csv`, `*.pt`, `*.onnx`, and `*.xml` ignores. These rules hid required scientific configurations, tables, checkpoints, ONNX models, SUMO XML, and the untracked final selected policy. The selected policy, selected configuration, candidate manifest, and protocol existed locally but were not indexed.

The index also contained a 396,320,542-byte regeneratable perception trace, progress snapshots, latest panel summaries, and duplicate/generated ZIP packaging.

## Complete classification

Every indexed file after cleanup is covered by the following mutually exclusive rules:

### A. KEEP_TRACKED — 418 files

All indexed files except the D/E/F exceptions below: Python source, tests, requirements, READMEs, project-authored documentation, SUMO configuration/network/routes, rule profiles, research inputs, scripts, canonical lightweight results, selected final artifacts, ONNX models, showcase source, and intentional application assets.

The extracted `results/final_mappo_selection_v2/` evidence is tracked instead of its ZIP packaging. This includes the selected policy/configuration, manifest, protocol, candidate checkpoints, validation records, held-out results, and canonical comparison tables. The canonical conference-paper evidence JSON is also tracked.

### B. UNTRACK_BUT_KEEP_LOCAL — 14 files

- `results/perception_ldm_evidence.jsonl` under Component 2.
- Four top-level Component 2 `results/*_progress.json` snapshots.
- `results/panel_demo/latest_panel_demo_summary.md` and `results/panel_demo/gui_smoke/latest_panel_demo_summary.md`.
- `archive/generated/panel_demo.zip` and `archive/legacy/generated/smoke (2).zip`.
- Final-selection `comparison.zip`, `held_out.zip`, `smoke.zip`, `training.zip`, and `validation.zip`.

All paths above remain on disk. The final-selection ZIPs were replaced in tracking by their existing extracted canonical contents.

### C. IGNORE_FOR_FUTURE

The exact B paths/patterns, runtime `latest_panel_demo.json`, final-selection `progress.json`, GUI research-demo output, liveness-fix runtime output, root/workspace showcase ZIPs, plus normal environments, caches, logs, temporary files, IDE files, OS files, and secret-file patterns.

### D. REVIEW_FOR_GIT_LFS_OR_EXTERNAL_STORAGE — 1 file

- `models/notebook/inD_intention_dataset_preparation.ipynb` (8.49 MiB).

It remains tracked because it is research provenance and is below 10 MiB. LFS is not presently justified.

### E. REVIEW_LICENSE_OR_PRIVACY — 271 files

- `docs/regulatory_sources/**`, including the official StVO PDF/XML and 257 page JPGs.
- Showcase team portraits, academic contact data, and the SLIIT logo.

The page images total only 707,234 bytes and are explicitly documented as a complete regulatory source bundle, so they were not removed. Public redistribution rights for third-party regulatory material and logos should be confirmed. Team names, university email addresses, supervisors, and portraits are `INTENTIONAL_PUBLIC_ACADEMIC_INFORMATION` and should be committed only with team agreement.

### F. UNCERTAIN_DO_NOT_CHANGE — 9 files

- `results/mappo_extended_resume/replication_*_state_*.pt`.

These intermediate checkpoints are used by tests and documented experiment reconstruction. They remain tracked; no automatic untracking was appropriate.

Classification total: 699 indexed files.

## Required artifacts repaired

The following were accidentally ignored and are now normally indexed without `git add -f`:

- `results/final_mappo_selection_v2/selected_policy.pt`
- `selected_configuration.json`, `candidate_manifest.json`, and `protocol.json`
- Extracted final-selection comparison, held-out, validation, smoke, and candidate-training artifacts
- `results/conference_paper_evidence.json`
- The new SUMO GUI settings XML and other legitimate newly added JSON/CSV/PT/XML files

Existing tracked ONNX models, SUMO XML, traffic-rule JSON, and research-input JSON are no longer matched by broad ignore rules.

## Selected-policy verification

- Runtime resolution: `panel_demo/runner.py` uses `results/final_mappo_selection_v2/selected_policy.pt` relative to the Component 2 root.
- Size: 322,493 bytes.
- SHA-256: `2AB2029FDD66F96C3BA0ACF5E76487C96740161E898539F93C726228097EAF57`.
- Status: exists locally, indexed normally, and not ignored.

## Largest current files before cleanup

| Size | Path | Classification/recommendation |
|---:|---|---|
| 377.96 MiB | `results/perception_ldm_evidence.jsonl` | Generated visualization/LDM trace; untrack, preserve locally, ignore precisely |
| 8.49 MiB | intention preparation notebook | Keep as research provenance; review if it grows |
| 3.51 MiB | `mappo_behavior_rollout.json` | Canonical scientific evidence; keep |
| 2.30 MiB | final-selection `comparison.zip` | Package duplicate; untrack while extracted evidence is tracked |
| 2.22 MiB | final-selection `training.zip` | Package duplicate; untrack while extracted checkpoints are tracked |
| 1.55 MiB | `coupled_environment_profile.json` | Canonical profile; keep |
| 1.53 MiB | corresponding progress JSON | Generated progress; untrack but preserve locally |
| 1.41 MiB and below | intermediate MAPPO checkpoints | Keep pending case-by-case review |

Before cleanup, one current indexed file exceeded 10 MiB, 50 MiB, and 100 MiB.

## Largest current files after cleanup

| Size | Path | Recommendation |
|---:|---|---|
| 8.49 MiB | intention preparation notebook | Keep/review case-by-case |
| 3.51 MiB | `mappo_behavior_rollout.json` | Keep canonical evidence |
| 2.31 MiB | showcase `component_4.png` | Keep application asset |
| 2.31 MiB | showcase `component_2.png` | Keep application asset |
| 2.30 MiB | showcase `component_3.png` | Keep application asset |
| 2.05 MiB | showcase `component_1.jpg` | Keep application asset |
| 1.55 MiB | `coupled_environment_profile.json` | Keep canonical evidence |

No current indexed file now exceeds 10 MiB.

## Historical blobs and optional cleanup

Index-only removal does not remove prior objects. The 377.96 MiB perception JSONL blob remains in history (commits include `d8e0961` and `5aa79c2`), as do older copies of generated ZIPs. Other branches contain two Component 3 NumPy blobs around 11–12 MiB. The object database audit also reported two 11–13 MiB showcase ZIP blobs, although path-specific commit history did not identify them as committed on the current branch; they should be rechecked during any coordinated history cleanup.

`OPTIONAL_HISTORY_CLEANUP_REQUIRED`: the 377.96 MiB blob exceeds GitHub's ordinary 100 MiB per-file limit and materially inflates clones. A coordinated `git filter-repo` rewrite is recommended before public/shared distribution if the blob is not already accommodated remotely. This requires team agreement, backup, all collaborators re-cloning or carefully rebasing, and a force push. No rewrite was performed.

Git LFS was not introduced. No necessary current indexed artifact exceeds 10 MiB, so LFS migration is not currently warranted. Historical migration must not occur without team agreement and remote-LFS verification.

## Secret and privacy audit

No obvious secret filenames, private keys, credential JSON, service-account file, or common token/key signature was found in the worktree or tracked text scan. No secret-like historical filename was found. This is a best-effort static audit, not a credential guarantee.

Intentional public academic information exists in the showcase. Confirm consent before publishing. Third-party SLIIT branding and regulatory-source redistribution should receive a project-level license/provenance review; no legal conclusion is made here.

## Final Git policy result

- Broad scientific extension ignores removed.
- Tracked-but-ignored count: 0.
- Visible untracked count: 0.
- No current indexed file above 10 MiB.
- No commit, push, LFS migration, or history rewrite performed.

## Validation record

- Python compile/import check: passed.
- Combined Component 2 and showcase tests from the Component 2 root: 657 passed.
- Showcase application import and relocated Component 2 launcher path: passed.
- Missing runtime result behavior: returned the documented friendly unavailable state.
- Selected policy, both ONNX models, SUMO configuration, network, and route files: present and indexed.
- Selected policy SHA-256 remained `2AB2029FDD66F96C3BA0ACF5E76487C96740161E898539F93C726228097EAF57`.
- Final Git checks: 699 indexed files, 0 tracked-but-ignored files, 0 visible untracked files.

The final staged change summary is 120 additions, 14 index removals, 2 modifications, and 577 renames. The large count primarily reflects the already-requested Component 2 relocation and addition of the previously untracked showcase, not hygiene-driven source changes.
