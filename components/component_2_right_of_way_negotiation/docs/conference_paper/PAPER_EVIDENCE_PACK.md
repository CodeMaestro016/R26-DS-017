# Conference Paper Evidence Pack

## Scope and evidence rules

This pack is a read-only synthesis of artifacts already present in the repository. No model was trained, no SUMO scenario was run, and no result was recomputed. “Paper-safe” means that the stated, limited claim is directly supported by a cited artifact; it does not mean that the system is optimal, statistically significant, generally safe, legally compliant, or externally validated.

The final intention test metrics are stored in the saved outputs of `models/notebook/inD_intention_dataset_preparation.ipynb`. At audit time that notebook is **untracked by Git**. The deployed thresholds and model identities are corroborated by tracked deployment artifacts, but the notebook must be archived/committed or its tables exported before submission. Numeric confusion-matrix cells and raw prediction rows are not available as standalone artifacts.

## Table 1 — Intention recognition evidence

| Item | Primary (1.0 s lead) | Secondary (0.5 s lead) | Status / source |
|---|---:|---:|---|
| Test sequences | 58 | 58 | Current; notebook Cells 20–22B |
| Accuracy | 0.896552 | 0.931034 | Current deployed policy; notebook Cells 20–22B |
| Balanced accuracy | 0.891026 | 0.916667 | Current; notebook Cells 20–21 |
| Macro precision | 0.890370 | 0.934524 | Current; notebook Cells 20–21 |
| Macro recall | 0.891026 | 0.916667 | Current; notebook Cells 20–21 |
| Macro F1 | 0.889311 | 0.923765 | Current; notebook Cells 20–22B |
| Weighted F1 | 0.898253 | 0.930524 | Current; notebook Cells 20–21 |
| Log loss | 0.424631 | 0.245352 | Current; notebook Cells 20–21 |
| Final threshold | 0.4367631896 | 0.3872705111 | Current; `models/intention/robust_calibration_and_unknown_policy.json` |
| Test coverage | 1.000000 (58/58) | 1.000000 (58/58) | Current; notebook Cell 22B |
| Accepted-set accuracy | 0.896552 | 0.931034 | Current; notebook Cell 22B |
| Accepted-set macro F1 | 0.889311 | 0.923765 | Current; notebook Cell 22B |
| Unsafe accepted-error rate | 0.103448 (6/58) | 0.068966 (4/58) | Current; notebook Cell 22B |
| LEFT P/R/F1/support | .933333/.875000/.903226/16 | .875000/.875000/.875000/16 | Current; notebook Cells 20–21 |
| RIGHT P/R/F1/support | .777778/.875000/.823529/16 | 1.000000/.875000/.933333/16 | Current; notebook Cells 20–21 |
| STRAIGHT P/R/F1/support | .960000/.923077/.941176/26 | .928571/1.000000/.962963/26 | Current; notebook Cells 20–21 |
| Numeric confusion matrix | Not available | Not available | Embedded plots exist, but cells are not machine-readable; do not invent values |

The primary architecture was selected using validation data only: GRU, 32 hidden units, dropout 0.2, 3,939 parameters, best validation epoch 22. The secondary reused that architecture without a new architecture search and reached best validation epoch 44. Recordings 7–14/15–16/17 are the train/validation/test split. Both models accept a `[48,6]` feature window derived from a 50-sample x/y history at 25 Hz (nominal 2.0 s). Sources: `models/intention/deployment_manifest_onnx.json` and `models/intention/feature_specification.json`.

The superseded Cell-22 Youden-J thresholds were 0.937405 (primary) and 0.608585 (secondary), with test coverage 0.137931 and 0.931034. They are historical only; the robust Cell-22B policy explicitly supersedes them and did not use the test set for calibration (`models/intention/robust_calibration_and_unknown_policy.json`).

ONNX verification used 58 test sequences per model. Maximum probability differences were approximately 1.788×10⁻⁷ (primary) and 1.341×10⁻⁷ (secondary), with all recorded equivalence checks passing (`models/intention/onnx_export_verification.csv`, `models/intention/onnx_deployment_quality_checks.csv`).

Fusion is conservative (`predictor.py:285`): accepted and agreeing stages yield `CONFIRMED_AGREEMENT`; accepted disagreement yields `UNKNOWN/HORIZON_DISAGREEMENT`; only-secondary acceptance yields `SECONDARY_RECOVERY`; primary-only acceptance yields `UNKNOWN/SECONDARY_UNCERTAIN`; both rejected yields `UNKNOWN/BOTH_UNCERTAIN`; missing stages also yield `UNKNOWN` with a missing-stage status. The saved offline status table contains 50 agreements and 8 disagreements. It contains no fused ground-truth score, therefore:

`FUSED_OFFLINE_TEST_METRIC_NOT_AVAILABLE`

## Table 2 — Perception, conflict, and traffic-rule evidence

| Layer | Verified evidence | Limitation / source |
|---|---|---|
| Perception configuration | Four 160 m, 150° reference corner radars; fused 360° coverage; minimum required range 118.34 m | Configuration evidence; `config.py`, `results/controlled_pilot_design.json` |
| Runtime perception | Default `GEOMETRIC_SENSOR`; world-to-ego transform, range/FOV, occlusion, partial visibility and dimensions are implemented | Object-level simulation abstraction, not a physical radar model; `perception_interface.py` and tests |
| Realistic sensor mode | Delegates geometric sensing | Noise, misses, and latency are not implemented; no perception-accuracy claim is supported |
| Conflict map | 12 legal movement paths; 30 physical conflict zones | `results/step_5j_3a_main_output.txt`; the catalogue CSV has 78 relationship rows, not 78 physical zones |
| Graph workload | 5,019 graphs; 27,063 spatial edges; 10,563 conservative unknown-intention edges; 14,835 prediction-unavailable edges | One coherent 200 s / 5,000-step run; `results/step_5j_3a_main_output.txt` |
| Filtering | 8,044 non-conflicting targets filtered; 31,013 non-conflicting candidate paths excluded | Same run/source |
| Temporal reasoning | 46,090 candidate-path evaluations; 1,717 nominal conflicts; 37,663 separations; 4,352 occupied-zone and 27,365 cleared-zone evaluations; 6,710 unresolved | Same run/source |
| Earliest-arrival / stopping | 92,180 earliest calculations; 10,674 finite stopped arrivals; 50,314 able-to-stop and 41,866 unable-to-stop evaluations | Same run/source |
| Traffic profile | `DE_STVO_UNCONTROLLED_4WAY_V1`; uncontrolled four-way, right-before-left, right-hand traffic; ODD check true | Simulation rule profile, not a legal-compliance certification |
| Regulatory reasoning | 27,063 assessments/pairs: §8 12,555; §9 10,457; §9(4) 2,953; mandatory yield 15,927; precedence 5,805; unresolved 3,997 | Regulatory-input unresolved = 0 and route-truth fields = 0; same run/source |

## Table 3 — Scenario catalogue and split design

| Item | Value | Source / interpretation |
|---|---:|---|
| Legal paths | 12 | `results/negotiation_scenario_catalogue.json` |
| Movement combinations enumerated | 243 | Same source |
| Regulatory-cycle candidates / specifications | 108 / 108 | Same source; SCC/cycles are derived by the traffic-rule precedence-graph builder, not hand-picked |
| Training / validation / held-out scenarios | 36 / 36 / 36 | `results/controlled_pilot_design.json` |
| Pairwise split overlap | 0 | Same source; frozen deterministic semantic partition |
| Used for parameter selection | No / Yes / No | Same source |
| Participant coverage | 2 vehicles: 6; 3: 44; 4: 58 | Audit of 108 stored signatures |
| Cyclic participant coverage | 2: 40; 3: 40; 4: 28 | Audit of stored signatures |
| Multi-factor capable | 3 of 108 | Stored signature flag; capability metadata, not executed ablation evidence |
| Proposer/responder/multi-action capable | 3 each of 108 | Stored signature flags |

## Table 4 — MAPPO/GNN architecture contract

| Component | Verified contract | Source |
|---|---|---|
| Graph encoder | 8-D node features, 9-D edge features, hidden size 64, 3 message-passing layers, ReLU | `results/mappo_architecture_contract.json`; tensor schemas in `negotiation_learning/tensor_encoding/schemas.py` |
| Encoder state | Deterministically initialized and frozen | Mechanical reference configuration; not demonstrated optimal |
| Proposer | 162-D concatenated input → one linear two-logit head | Actions: `KEEP_CLAIM`, `RELINQUISH_CLAIM` |
| Responder | 180-D concatenated input → one linear two-logit head | Actions: `ACCEPT_RELINQUISHMENT`, `REJECT_RELINQUISHMENT` |
| Critic | Deep-Sets sum → 64-D representation → scalar value head | Training-only centralized critic |
| Parameter sharing | Shared representation with role-specific policy heads | Same contract |
| Hard action masks | Boolean invalid-action masks prevent impossible/protocol-disallowed choices | Demonstrated enabled; no no-mask ablation exists |
| CTDE runtime boundary | Critic used for training; final demo critic calls = 0 | `results/final_research_prototype_demo.json` |

The contract itself records `project_selected=false`, `final_selection_eligible=false`, and `training_performed=false`; later evidence uses this architecture, but no artifact establishes architectural optimality.

## Table 5 — Extended MAPPO training evidence

| Quantity | Replication 0 | Replication 1 | Replication 2 | Cross-replication source |
|---|---:|---:|---:|---|
| C0 team travel time (vehicle-s) | 19,035.08 | 14,027.04 | 18,130.24 | `results/mappo_extended_learning_curve_evidence.json` |
| C1 team travel time (vehicle-s) | 19,464.16 | 11,334.80 | 17,817.12 | Same source |
| C2 team travel time (vehicle-s) | 18,847.00 | 11,763.36 | 16,929.56 | Same source |
| C0→C2 delta (vehicle-s) | −188.08 | −2,263.68 | −1,200.68 | Mean −1,217.48; sample variance 1,077,240.52; sample SD 1,037.902 |
| Update cycles | 2 | 2 | 2 | 6 total cycles; 5 PPO epochs/cycle = 30 optimizer epochs |

The tranche contains 3 replications, 9 policy states, 324 training-scenario executions, and 1,620,000 SUMO steps. C0/C1/C2 means were 17,064.12 / 16,205.36 / 15,846.64 vehicle-s; sample variances were 7,122,575.0512 / 18,469,951.2256 / 13,424,025.7072 and sample SDs 2,668.815 / 4,297.668 / 3,663.881. Recorded collisions, blocked vehicles, and native safety interventions were all zero within this tranche. Validation executions, held-out executions, and candidate comparisons were all zero. Update 3 was not performed; no final replication count or training budget was selected. The artifact explicitly does **not** establish convergence, significance, or optimality.

## Table 6 — Final frozen demo evidence

| Item | Verified value | Source / boundary |
|---|---:|---|
| Demonstration policy | `RESEARCH_PROTOTYPE_DEMONSTRATION_POLICY_V1` | `results/final_research_prototype_demo.json` |
| Source checkpoint | Replication 0, terminal state 2 (`results/mappo_extended_resume/replication_0_state_2.pt`) | First canonical replication terminal state; not performance/statistically selected |
| Scenarios / completed | 3 / 3 | Structurally selected, not performance-selected |
| Aggregate team travel time | 1,544.20 s | Three-scenario demonstration total |
| Proposer / responder / total actions | 16 / 6 / 22 | 3 batches, 2 cycles |
| Physical executable outcomes | 1 | Nonphysical edges: 4 |
| Collisions / blocked / native safety interventions | 0 / 0 / 0 | Only these three demo scenarios |
| Runtime critic calls / route-truth fields | 0 / 0 | Ego-local observations and hard masks recorded true |
| Training or optimizer operations | 0 | No backward, PPO, parameter-update, new-training, validation, or held-out operation during demo |

Per scenario: regulatory-cycle negotiation completed 2 outcomes with 490.76 s and 8/3 proposer/responder actions; multi-factor multi-action negotiation completed 0 outcomes with 600.00 s and 4/0 actions; coordination-to-nonphysical interpretation completed 1 outcome with 453.44 s and 4/3 actions. Policy and checkpoint hashes were unchanged. These results demonstrate execution, not general performance.

## Table 7 — Baseline and ablation audit

`PAPER_READY_MATCHED_BASELINE_COMPARISON =`

`NOT_AVAILABLE`

| Requested comparison | Status | What exists / what is missing |
|---|---|---|
| Learned policy vs legacy/rule baseline | NOT AVAILABLE | Legacy/rule logic exists, but no matched scenarios, seeds, budget, and metrics comparison exists |
| Without GNN | NOT EXECUTED | No stored result |
| Different GNN depth | PLANNED, NOT EXECUTED | Candidate depths 1/2/3 declared; candidate comparisons = 0 |
| Frozen vs trainable GNN | PLANNED, NOT EXECUTED | Frozen mode implemented; no matched comparison |
| Without hard masks | NOT EXECUTED | Masks implemented/enabled; no matched unsafe/no-mask run |
| Without traffic rules | NOT EXECUTED | Rule engine implemented; no matched removal run |
| Without intention prediction | NOT EXECUTED | Intention stack implemented; no matched removal run |
| Other registered choices | PLANNED, NOT EXECUTED | Policy factor aggregation, capacity, sharing, PPO optimization, advantage normalization |

No value from `main.py` or another unmatched run should be presented as a baseline improvement. A paper-ready baseline requires a frozen matched protocol (same scenario IDs, seeds, ODD, stopping rules, compute budget, and metrics), then execution of both policies.

## Table 8 — Figure and raw-data availability

| Candidate figure | Current availability | Paper action |
|---|---|---|
| Intention confusion matrices | Embedded PNG outputs in untracked notebook; numeric cells unavailable | Export figures and raw confusion matrices from the preserved evaluation, without rerunning |
| Accuracy/F1 and coverage/accuracy plots | Embedded notebook outputs | Export with explicit primary/secondary and current/superseded labels |
| MAPPO learning curve | Raw C0/C1/C2 values in extended-evidence JSON; no standalone figure | Plot all three replications and mean; avoid convergence/significance language |
| Architecture diagram | No standalone media artifact found | Draw from the architecture contract and label frozen encoder/CTDE boundaries |
| Scenario/conflict graph | Raw path/zone CSVs and scenario JSON exist; no standalone figure | Render 12 paths and 30 physical zones; do not depict 78 relationship rows as zones |
| SUMO demo visual | Metrics/summary JSON exists; no screenshot/video artifact found | Capture only if a future authorized run or preserved recording is available |

## Claim audit

### Supported with precise scope

- A rule-aware, multi-agent negotiation research prototype was implemented and executed in SUMO.
- Two deployed GRU intention models achieved the Table-1 metrics on 58 stored test sequences each; cite the untracked-notebook provenance caveat.
- The final three-scenario demonstration used ego-local observations, hard masks, no route truth, and no runtime critic calls.
- Zero collisions and zero blocked vehicles were recorded in the 324 training executions and the three final demo scenarios. This is a bounded observation, not a general safety claim.
- Traffic-rule and spatiotemporal conflict reasoning were exercised with the counts in Table 2.
- Mean team travel time decreased from C0 to C2 in the three-replication evidence tranche; this descriptive result is not a significance, convergence, or baseline-improvement result.

### Not currently supported

- “Optimal,” “state of the art,” “converged,” or “statistically significant.”
- “Outperforms the baseline” or “improves over rule-based control.”
- Generalization to held-out scenarios: held-out executions are zero.
- Universal safety, collision avoidance guarantees, production readiness, real-radar performance, or legal compliance.
- A fused offline accuracy/F1 value, perception accuracy, or numeric confusion matrices.
- Causal contribution claims for the GNN, masks, traffic rules, intention prediction, or any other component.

### Requires new experiments or preserved exports

- Matched baseline evaluation, registered ablations, held-out evaluation, more replications, uncertainty intervals/significance tests, and substantially broader safety stress testing.
- A labeled fused-prediction evaluation and a physical/noisy perception evaluation.
- Export of intention raw predictions/confusion matrices and durable version control of the notebook evidence.

## Recommended paper wording

“We present and demonstrate a rule-aware multi-agent negotiation research prototype for a simulated uncontrolled intersection. In a three-replication training-evidence tranche, mean aggregate team travel time decreased descriptively from 17,064.12 to 15,846.64 vehicle-seconds between C0 and C2 (mean paired change −1,217.48 vehicle-seconds); the experiment was not designed to establish statistical significance, convergence, held-out generalization, or improvement over a matched baseline. The frozen three-scenario demonstration completed without recorded collisions or blocked vehicles and used decentralized ego-local policy inputs without runtime critic access.”
