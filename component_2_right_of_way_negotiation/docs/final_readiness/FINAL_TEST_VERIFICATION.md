# Final test verification — 16 October 2026

Environment: C:\R26-DS-017\venv\Scripts\python.exe, Python 3.13.1;
pytest 9.1.1; Torch 2.14.0; SUMO executable 1.26.0. Logs are newly generated
under results/final_readiness/20261016/, not reused prior test claims.

| Newly executed check | Result | Log |
|---|---|---|
| Root collection before correction | 699 collected; one archived snapshot error; exit 1 | root_collection_before.log |
| Root collection after minimal config | 926 collected, no errors (before new UI tests) | root_collection_after.log |
| Final root collection | 947 collected, no errors; 4.85 s | root_collection_final.log |
| Full active Component 2 | 848 passed, 2 existing strict xfails; 1012.22 s; no warnings | component2_full_tests.log |
| Full active showcase after fixes | 97 passed; 1.71 s; no warnings | showcase_tests_final_verified.log |

```powershell
Set-Location "C:\Users\Iresha Nethmini\Documents\R26-DS-017"
$projectPython = "C:\R26-DS-017\venv\Scripts\python.exe"
& $projectPython -B -m pytest --collect-only -q
& $projectPython -B -m pytest component_2_right_of_way_negotiation/tests -q -ra
& $projectPython -B -m pytest socialmind_drive_showcase/tests -q -ra
```

The root pytest.ini selects active Component 2/showcase suites and excludes
results/archive snapshots without deleting them. Module-scoped test CWD setup
makes Component 2's existing relative test assets work from the workspace root.
Explicit active test-directory invocation remains supported. Other components'
independent research tests are outside this task's root testpaths scope.

The two strict xfails are the original complete dense-discharge and zero-live-at-
completion assertions in test_ego_execution_and_dense_traffic.py. They were not
added, skipped or weakened here. Unmarked fixture safety/integrity assertions
still pass. Thus exit 0 is not a claim that dense liveness was fixed or that
the V2 acceptance gate passed. The full suite's SUMO fixture used a temporary
directory and original 360-second regression budget; no scientific evaluation
episode or old evidence was overwritten.

Earlier new-showcase attempts exposed an over-broad process-stop implementation,
a selector compatibility mismatch and a cleanup indentation error. Those were
fixed in presentation code; the original tests/assertions remain unchanged.
The intermediate failed logs are retained for audit, and the final 97-pass log
is identified explicitly. No failure was relabeled as success.

Two new short real qualitative launch probes (congested and default rolling)
were explicitly stopped after real frames at 2.12 simulated seconds. Both
returned USER_STOPPED/exit 0, refused duplicate launches, stopped gracefully,
and left no owned process running. They are not scientific performance evidence.
Six actual HTTP routes returned 200; the evaluation response contained 34/165
and SMOKE_NOT_FINAL. Full details are in qualitative_launch_checks.json,
http_checks.json and lifecycle_and_http_checks.log. A third short live qualitative
check invoked the registered shutdown method while traffic was running at
1.0 simulated seconds: graceful exit, zero remaining owned processes and
relaunch refused after shutdown (shutdown_check.json).

Real missing-checkpoint and absent-SUMO prerequisite guards also returned FAILED
before starting a process (startup_failure_checks.json). An earlier isolated
backend startup fault exposed a secondary Not connected finalizer error; its
log is retained. The UI now refuses these missing prerequisites before launch.
No scientific runtime was modified to suppress that backend failure; direct-CLI
fault cleanup remains a documented limitation requiring separate review.

No Browser connection was available, so visual layout/click rehearsal is not
claimed. Desktop pywebview 6.2.1 and owned-process psutil 7.2.2 were installed
from existing/new presentation requirements, without upgrading scientific
packages. pip check found no broken requirements and the Windows desktop
backend imported successfully without opening a window. Native window
interaction remains a manual viva rehearsal item.
