# File organization audit and proposed cleanup

Date: 16 October 2026. Status: **PROPOSED — awaiting approval.** No existing
file has been moved, deleted, overwritten or repackaged. No scientific or
website code has changed. This report will be supplemented with actual moves,
before/after measurements and verification results after approval.

## Current structure and provenance

```text
R26-DS-017/
  .git/                         shared version-control metadata
  .venv/                        existing workspace Python environment
  .pytest_cache/                generated workspace test cache
  .demo_probe_b7b08c60/          successful final-package extraction
  .presentation_probe_20261016/  superseded-package extraction
  .demo_probe_b7b08c60.zip       archive of that extracted probe
  .presentation_probe_20261016.zip
  deliverables/                 four different presentation ZIP builds
  deliverables.zip              exact nested copy of those four builds
  R26-DS-017.zip                 Component 2 + showcase snapshot only
  component_1/                  empty directory; preserve
  component_2_right_of_way_negotiation/
  component_3/                  empty directory; preserve
  component_4/                  empty directory; preserve
  socialmind_drive_showcase/
  .gitignore
  pytest.ini                    workspace-wide collection configuration
  README.md                     shared workspace documentation
```

The extraction folders were created by the prior presentation verification.
The audit establishes the ZIPs' contents and relationships, not who created
the later wrapper ZIPs. No additional generated root items were found beyond
those listed. Component-specific tools, readiness reports, receipts, test logs
and scientific evidence are already inside Component 2.

Root `.venv` contains 30,134 files / 909,077,861 bytes and its configuration
identifies Python 3.13.1. The previously verified working interpreter is
`C:\R26-DS-017\venv\Scripts\python.exe`, outside this checkout. Both environments
will be left untouched; no assumption that the root environment is usable is
needed for cleanup. Root `pytest.ini` and `.gitignore` remain in place.

## Verified archive and copy audit

Every entry in all eight ZIPs was read and SHA-256 recorded; all CRC checks
passed. Detailed per-entry hashes and complete root size inventory are retained
in `results/file_organization/20261016/pre_cleanup_audit.json` and comparisons
in `archive_comparisons.json`.

| Item | Files | Bytes | Finding |
|---|---:|---:|---|
| `.demo_probe_b7b08c60/` | 678 | 20,998,896 | No unique non-cache files; preserved in final ZIP |
| `.presentation_probe_20261016/` | 670 | 20,975,910 | No unique non-cache files; preserved in superseded ZIP |
| `.demo_probe_b7b08c60.zip` | 678 | 15,950,404 | Exact per-entry match to corresponding folder, with wrapper directory |
| `.presentation_probe_20261016.zip` | 670 | 15,952,841 | Exact per-entry match to corresponding folder, with wrapper directory |
| `deliverables.zip` | 4 | 62,096,129 | All four nested ZIPs exactly match root deliverables |
| `R26-DS-017.zip` | 3,763 | 112,884,928 | Every archived file matches canonical bytes; only Component 2 and showcase |
| Root `.pytest_cache/` | 5 | 134,882 | Disposable generated cache |

`R26-DS-017.zip` has 3,623 Component 2 files and 140 showcase files. It omits
root configuration, Git metadata, environments, deliverables and the empty
Component 1/3/4 directories. **It is not a complete group/workspace backup.**
Its small compressed size does not justify discarding the multi-gigabyte
canonical scientific results: its uncompressed contents total 2,490,338,809 bytes.

The three previous presentation builds are distinct artifacts, with different
SHA-256 values and historical document/code versions. Preserve them externally
as superseded builds; do not equate a CRC-valid ZIP with a working final package.

| Build filename under current `deliverables/` | Bytes | SHA-256 |
|---|---:|---|
| `SOCIALMIND_DRIVE_COMPONENT2_PRESENTATION_20261016.zip` | 15,813,573 | `30d74ac435fded7861631455a3f848d46fb00151f1297c634d312734e1e2dfc8` |
| `SOCIALMIND_DRIVE_COMPONENT2_PRESENTATION_20261016_FINAL.zip` | 15,814,537 | `483d6f87a1c7262152440ee98b0260381717ec4a53020093636b7bda7a48d905` |
| `SOCIALMIND_DRIVE_COMPONENT2_PRESENTATION_20261016_VERIFIED.zip` | 15,814,538 | `35d9e69c34ed95567f6580db882a56da4cbda1aa17125a6d3785d649ecf9a8df` |
| `SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip` | 15,823,421 | `b7b08c607428a9c00f105f8b66d0949333ff9ba4168f41f38eb10ae08016a311` |

Final VIVA contents retain 616 Component 2 files, 59 website files, root README,
pytest.ini and START_HERE.md. The prior successful independent import receipt
is retained in `results/final_readiness/20261016/package_import_probe.log` and
`final_verification.json`: imports succeeded, E5 hash matched, original 34/165
records and separate nine smoke records remained readable. The successful
probe matches the final package bytes. No new extraction/import check has yet
been run for this cleanup; it is scheduled after approval.

An additional partial extraction exists at
`results/final_readiness/20261016/package_import_probe/`: 202 files, 2,448,083
bytes, no unique non-cache files. This was a failed deep-path extraction probe.
**Keep it in the default plan** because it is under retained readiness evidence;
its optional removal requires explicit approval. Preserve all sibling receipts.

## Proposed structure and exact actions

```text
R26-DS-017/
  component_1/
  component_2_right_of_way_negotiation/
    [existing scientific packages, models, tests, archives, results unchanged]
    docs/final_readiness/FINAL_FILE_ORGANIZATION_REPORT.md
    results/file_organization/20261016/ [new cleanup receipts]
    tools/ [existing utilities and new audit utilities]
    deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip
  component_3/
  component_4/
  socialmind_drive_showcase/
  .git/
  .venv/
  .gitignore
  pytest.ini
  README.md
```

Proposed external backup destination:
`C:\Users\Iresha Nethmini\Documents\R26-DS-017_BACKUPS\cleanup_20261016\`.
This is outside the writable workspace and requires filesystem approval when
the backup is created. No external directory has been created yet.

Execute only after approval, in this order:

1. Create a full pre-cleanup workspace backup outside the active project,
   including hidden files, Git metadata, environments, root archives, all
   component data and empty directories. Record a complete path/size/SHA-256
   manifest; verify all copied/archive entries against source. Check available
   disk space first. Abort cleanup if the backup cannot be fully verified.
2. Move the existing final VIVA ZIP into Component 2 `deliverables/`, preserving
   its filename and bytes; verify the destination SHA-256 before removing source.
3. Preserve the three superseded builds under the external backup's
   `superseded_presentation_builds/`; preserve `R26-DS-017.zip` under
   `historical_archives/`. Verify each destination byte-for-byte. They also remain
   in the full pre-cleanup backup.
4. Remove only the two proven redundant root probe folders, their two wrapper
   ZIPs, and `deliverables.zip`, after the backup and preserved builds are checked.
   Remove the now-empty root `deliverables/` directory.
5. Remove only root `.pytest_cache`, after checking no tests are running.
   Keep all other caches in this plan; do not clean scientific archive interiors.
6. Apply the minimal path updates below, then run the post-cleanup checks.

No scientific data are unique to the two root probes. Historical package
documents that differ from current source remain preserved in superseded builds
and the full backup. No research failure, diagnostic trace, manifest, source,
model, SUMO file, scenario, test assertion or website content will be changed.

## Reference audit and proposed updates

The source/config/document search found no application or test dependency on
either extracted root probe. Existing verification tooling can recreate a probe,
so it must be updated to prevent new root clutter.

| File | Minimal proposed update |
|---|---|
| `tools/build_presentation_package.py` | Set DEST under Component 2 `deliverables/`; preserve the exact runtime/model/evidence selection and ZIP internal layout. Exclude ZIP/backup files from workspace source-size calculations as well as existing probe/output exclusions. Keep exclusive ZIP creation. |
| `tools/verify_final_readiness.py` | Use an isolated short temporary extraction outside the project; resolve relocated package using an explicit current-location fallback. Preserve original dated receipts; avoid overwriting them for cleanup verification. |
| `docs/final_readiness/FINAL_PACKAGE_AUDIT.md` | Correct the outer ZIP location only; retain recorded scientific findings and historical sizes. |
| `docs/final_readiness/FINAL_READINESS_SUMMARY.md` | Correct the final ZIP location only. |

The dated `package_manifest.json` and `final_verification.json` contain the old
absolute package path as historical provenance. Preserve their original bytes;
write a separate relocation receipt with old/new paths and identical SHA-256.
Do not rewrite documents inside the already verified ZIP. Do not run the package
builder merely to update its destination: that would create a new package.

## Storage accounting and move risks

Measured logical file bytes at audit start: **4,927,875,131** (includes Git,
root `.venv`, archives and probes). This is file content size, not filesystem
allocated size. Newly written audit/report files are not included in that baseline.

| Planned effect | Exact bytes |
|---|---:|
| Remove redundant copies and root cache | 136,109,062 |
| Relocate superseded builds + historical ZIP outside workspace | 160,327,576 |
| Move final ZIP within workspace | 0 reduction |
| Total active workspace reduction | **296,436,638** |
| Projected remaining baseline content | **4,631,438,493** |

The reduction is about 282.70 MiB. External backups increase storage usage;
moving to a sibling on the same drive does not free drive space. A full backup
means net drive usage increases, even though the active checkout is cleaner.
Actual after sizes must include new reports/receipts and any recreated cache.
Optional partial-probe removal would save another 2,448,083 bytes, excluded above.

Risks: Windows deep-path extraction can fail; use a short isolated extraction
path. External backup creation needs permission and sufficient capacity. Old
absolute paths in preserved dated receipts become historical references; the
relocation receipt and updated reader fallback will make the current location
explicit. Existing staged/unstaged user work must be copied and preserved;
Git HEAD alone is not a backup of this workspace. Destination collisions must
fail closed rather than overwrite files.

## Verification and execution record

Completed for this proposal: root/hidden directory inventory, all eight ZIP CRC
checks, per-entry SHA-256 comparisons, probe uniqueness checks, archive/canonical
comparisons and source/document reference search. No Python/pytest process was
listed during the audit. No scientific simulation or evaluation was run.

After approval: root and Component 2 imports; workspace pytest collection; focused
existing path/compatibility/launcher/evaluation tests; showcase imports; unchanged
E5 and deployed intention asset hashes; SUMO network/scenario and website asset
resolution; read-only evaluation readers; final ZIP CRC/SHA; fresh isolated final
package import check; source scan for removed-path dependencies; short local
website HTTP startup check if feasible. Do not execute training or long suites.
Record missing dependencies or paths without speculative scientific changes.

Previous readiness results (not rerun here): 848 Component 2 tests passed with
two existing strict xfails; 97 showcase tests passed; 947 workspace tests
collected. Six HTTP routes returned 200 in the retained previous startup receipt.
These are historical verification results, not post-cleanup results.

Moved files: **none yet**. Removed files: **none yet**. Retained backups:
existing archives remain untouched; a verified full-workspace backup is still
required before cleanup. Updated existing paths: **none yet**.

Current final package: root `deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip`.
Proposed final package:
`component_2_right_of_way_negotiation/deliverables/SOCIALMIND_DRIVE_COMPONENT2_VIVA_20261016.zip`.
Website startup after cleanup: pending approval/execution. Unresolved: approval,
external-backup filesystem access/capacity, and all post-cleanup checks.
