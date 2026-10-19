# Panel comments resolution

## Comment 1

> Need to have a good understanding about the background of the selected topic. Also need to plan how to demonstrate the implemented system. Need to address complex scenarios in PP2.

Concern: explain the research problem, contribution and credible demonstration
of complex interactions. Implemented: the existing perception/LDM, intention,
conflict, rule, claim-exchange, role-specific MAPPO and ego-local execution
pipeline; legal cycle, mixed-turn and queue scenarios; a read-only live viewer
and now a documented failure contingency. Evidence: Component 2 README,
runtime_simulation/scenario_catalog.json, selected_configuration.json,
REPAIR_V2_AUDIT.md, the targeted records and FINAL_VIVA_RUNBOOK.md.

Verification: full active Component 2 tests 848 pass with two pre-existing
liveness xfails; showcase 97 pass; real short launch/stop and six HTTP routes
verified. Visual desktop/page interaction still requires manual rehearsal.
Limitation: selected bounded scenarios do not prove universal intersection
generalization; the extended V2 study is not accepted or completed.
Viva explanation: "Our contribution combines learned semantic negotiation
with deterministic legal and safety checks. We demonstrate actual inference
and also disclose cases where safe holding prevents traffic discharge."

## Comment 2

> For the whole project fairness-time measurement is very important. Focus on narrowing down the scope of the component to selected complex intersections.

Concern: measure delay and fairness within a defensible operational scope.
Implemented: incoming-lane mean/p95/maximum waits, per-approach wait means/gap,
conflicting served-pair FCFS inversions, throughput and censored team travel
exposure in one selected unsignalized four-way AV-only SUMO intersection.
Evidence: post_training_evaluation/metrics.py, evaluation scope, targeted
PV-04A/PV-04B records and DENSE_TRAFFIC_EVIDENCE_SUMMARY.md.

Verification: metrics are archived and displayed read-only; no frontend
recalculation or fabricated unavailable trip statistics. Limitation: unfinished
waits are censored, served-pair inversions can be N/A, and partial/failed runs
do not establish broad fairness improvement or statistical superiority.
Viva explanation: "We narrowed the scope to one complex unsignalized four-way
intersection. We report delay by approach and censored waiting explicitly;
we do not interpret stalled traffic as successful fairness."

## Comment 3

> Simulated for 4 vehicles across junction. Better to go for a more congested scenario to test the system properly.

Concern: distinguish total traffic population from the negotiation graph limit.
Implemented: 16 scheduled vehicles, four per approach, all twelve legal
movement classes, queues, successive physical queue-head promotion and native
follower car-following. Evidence: authentic older 16/16 qualitative records,
the later incomplete qualitative record, and scientific nominal 1/16 and
critical 0/16 results, all retained in the dense comparison table.

Verification: archived counts/peaks/participants/safety read from actual files;
full dense regression independently confirms safety/integrity but still fails
the original discharge requirements under strict existing xfails. Maximum
simultaneous negotiators remains four. Limitation: no general congestion
success is established; 4..40 scalability scientific cases remain NOT_RUN.
Viva explanation: "We extended total traffic to sixteen vehicles while
retaining four current queue-head negotiators. Some older presentations fully
completed, but the targeted study exposes severe liveness limitations. Broader
scalability and robust decentralized premise reconciliation remain future work."

These comments are addressed by implemented and measured work with disclosed
limitations, not by declaring every experiment successful. The V2 acceptance
gate and explicit approval for the long study remain unresolved.
