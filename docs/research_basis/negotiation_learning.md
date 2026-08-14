# Step 5E negotiation-learning research basis

## Scope and semantic boundary

The precedence graph invariant is `yielding vehicle -> priority vehicle`.
An outgoing ego edge is a mandatory yield obligation. An incoming edge is a
distinct ego-owned precedence claim. Learning cannot remove an outgoing
regulatory obligation.

`KEEP_CLAIM` means ego does not voluntarily relinquish the one existing
incoming precedence claim identified by the candidate. It does not authorize
entry, acceleration, or any override of safety, reachability, or law.

`RELINQUISH_CLAIM` means ego proposes through the computational coordination
protocol to voluntarily relinquish the one existing incoming precedence claim
identified by the candidate. It is not braking, stopping, indefinite yielding,
or a grant of immediate safe entry.

The simulated V2V mechanism is not asserted to be legally equivalent to human
understanding or communication under German traffic law. Regulatory semantics
remain derived from the project's curated official StVO source.

Step 5E.1 supplies a deterministic two-message agreement formalization:
`RELINQUISH_CLAIM` creates a proposal and the correct counterparty supplies an
explicit `ACCEPT` or `REJECT` response naming that proposal. A proposal alone
never changes precedence. Under the immutable `IDEAL_SAME_STEP_V2V` snapshot,
an accepted response is evidence visible to every consumer, so a third network
acknowledgement would add no agreement fact and is not introduced.

The source of the response choice remains intentionally unresolved:
`RESPONSE_POLICY_SEMANTICS_REQUIRE_RESEARCH_DECISION`. Neither automatic
acceptance nor a learned response policy is implemented.

Step 5E.2 groups the frozen message set by exact deterministic `ProposalId`
`(timestamp, yielding vehicle, priority vehicle, sender, receiver)` and retains
the underlying claim key `(yielding vehicle, priority vehicle)`. Every group is
evaluated independently and collected in an immutable
`JointNegotiationProtocolSnapshot`. Thus simultaneous proposals for different
claims are independent, while contradictory `ACCEPT` and `REJECT` evidence for
the same proposal remains `PROTOCOL_DISAGREEMENT`. Mixed completed, pending,
rejected, blocked, and disputed outcomes coexist without a global score.

The response decision vocabulary is `ACCEPT_RELINQUISHMENT` and
`REJECT_RELINQUISHMENT`. These are negotiation semantics, never motion
commands. An untrained decentralized response-logit interface is available,
but cannot create a response. Whether proposal and response decisions share a
network, use separate heads, or use separate actors is
`REQUIRES_EXPERIMENTAL_SELECTION`.

## Step 5F role-aware masked MAPPO policy interface

Status: `IMPLEMENTED_UNTRAINED`.

`NegotiationDecisionRole` distinguishes `PROPOSER` from `RESPONDER` without
ordinal meaning. Proposer action order remains `KEEP_CLAIM`,
`RELINQUISH_CLAIM`; responder order remains `ACCEPT_RELINQUISHMENT`,
`REJECT_RELINQUISHMENT`. Every decision remains bound to one claim and, for a
response, one proposal.

The reusable masked categorical distribution accepts actor logits plus the
existing deterministic Boolean mask. Invalid logits are replaced by negative
infinity, not an arbitrary finite sentinel, before constructing PyTorch's
categorical distribution. An all-invalid mask raises
`NO_FEASIBLE_POLICY_ACTION`. The interface exposes semantic selection,
behavior-policy log probability, and raw entropy for future collection, but it
does not publish a protocol message or execute an action.

The immutable `NegotiationRolloutStep` stores deterministic event identity,
local observation provenance, role, claim/proposal identity, Boolean mask,
semantic action, behavior-policy log probability, and training-only critic
value at collection. It has no numeric reward, advantage, return, PPO ratio,
loss, or termination assumption. Reward status is
`NOT_IMPLEMENTED_STEP_5F`.

MAPPO/CTDE are research-supported by Yu et al. (2021); later old-policy log
probability and PPO-ratio concepts are methodologically motivated by Schulman
et al. (2017), arXiv:1707.06347, but no ratio or objective is implemented here.
State-dependent masking follows Huang and Ontañón (2020). Role-specific action
meanings are a project semantic requirement. Exact actor/critic architecture,
gamma, GAE lambda, PPO clipping, learning rate, entropy coefficient, and every
other optimization setting remain `REQUIRES_EXPERIMENTAL_SELECTION`; reward is
`NOT DESIGNED`.

A numerical hyperparameter used in MAPPO/PPO literature is an experimental
configuration unless a general theoretical requirement establishes that exact
value. Step 5F intentionally copies no paper-specific numerical setting.

## Step 5F.1 deterministic policy semantic encoding

Status: `COMPLETE_STEP_5F_1`.

The prior opaque `claim_or_proposal_representation` is now defined as the exact
counterparty node row followed by the exact directed claim-edge row from the
validated `EncodedGraphObservation`. Its availability mask uses the identical
column order, and the actor model input concatenates semantic values with the
mask converted to exact Boolean identity values. The schema is derived from
`NODE_NUMERIC_SCHEMA` and `EDGE_NUMERIC_SCHEMA`; no parallel feature vocabulary
or selected model dimension is introduced.

The exact directed lookup preserves `yielding -> priority`, selects the
counterparty by vehicle ID metadata, and rejects missing or ambiguous nodes and
edges. Vehicle, proposal, rule, source-section, and conflict-zone identifiers
remain provenance only. `REGULATORY_RULE_ID_FEATURE_STATUS` is
`NOT_INCLUDED_BASELINE_AVOIDS_REDUNDANT_ARBITRARY_VOCABULARY`.

`protocol_state_representation` is an exhaustive one-hot identity encoding of
the live `ProtocolState` enum with a parallel availability mask. Known states
have one active category and all columns available. A genuinely unavailable
proposer state is all-zero with all masks false; a responder without a known
state raises `RESPONDER_PROTOCOL_STATE_REQUIRED`. State column indices imply no
ordering, severity, progress, priority, confidence, or utility.

The base encoder is NumPy-only, immutable, stateless, and has no learned
parameters or normalization constants. Schema dimensions are
`DERIVED_SCHEMA_DIMENSIONS`, not architecture hyperparameters. Claim role is
not duplicated numerically because `NegotiationDecisionRole` is already an
explicit categorical input to the role-aware policy.

Classifications:

- Reuse of graph node/edge semantics: `PROJECT CONSISTENCY REQUIREMENT`.
- Exact directed claim lookup: `MATHEMATICAL / SEMANTIC REQUIREMENT`.
- Protocol one-hot representation: `NON-ORDINAL IDENTITY ENCODING`.
- Availability masks: `PROJECT PARTIAL-OBSERVABILITY REPRESENTATION`.
- IDs excluded from numeric inputs: `ANTI-LEAKAGE / NON-ORDINAL DESIGN`.
- Rule IDs retained only as provenance: `BASELINE SCOPE CHOICE`.

The exact 0/1 categorical and availability values are identities and Boolean
facts, not empirical behavioral constants. Step 5F.1 selects no actor, critic,
or GNN capacity and introduces no reward or PPO parameter.

Protocol states and transitions are categorical:

- `NO_PROPOSAL -> PROPOSAL_CREATED` only when a priority holder selects
  `RELINQUISH_CLAIM` for its valid incoming claim.
- `PROPOSAL_CREATED -> PROPOSAL_PENDING` when that valid proposal is present in
  the frozen protocol snapshot without a response.
- `PROPOSAL_PENDING -> AGREEMENT_ESTABLISHED` on one matching `ACCEPT`.
- `PROPOSAL_PENDING -> PROPOSAL_REJECTED` on one matching `REJECT`.
- Any authority-dependent nonterminal evidence becomes `PROTOCOL_BLOCKED` on
  source/profile/authority mismatch.
- A disappeared or timestamp-inconsistent claim becomes
  `SOURCE_CLAIM_INVALID`.
- Conflicting responses or proposals become `PROTOCOL_DISAGREEMENT`; no vote,
  order rule, score, or vehicle-ID priority resolves them.

The original regulatory graph is immutable audit evidence. A
`NegotiatedPrecedenceOverlay` records the proposal, response, agreement,
participants, sources, and `CLAIM_VOLUNTARILY_RELINQUISHED_BY_AGREEMENT`.
A separate effective coordination graph omits only a claim with a completed
agreement. Agreement is not physical safety or crossing authorization.

## Research-supported choices versus unselected parameters

| Item | Basis | Status |
|---|---|---|
| MAPPO and centralized value function with decentralized policies | Yu et al. (2021) | RESEARCH-SUPPORTED METHOD |
| Centralized training and local actor execution | Lowe et al. (2017) | RESEARCH-SUPPORTED METHOD |
| State-dependent invalid-action masking | Huang and Ontañón (2020) | THEORETICALLY SUPPORTED METHOD |
| Permutation-invariant SUM over agent representations | Zaheer et al. (2017) | RESEARCH-SUPPORTED METHOD |
| Cooperative MARL at mixed-traffic unsignalized intersections | Zhuang et al. (2023) | DOMAIN EVIDENCE ONLY |
| Learned right-of-way relinquishment behavior | Yan et al. (2021) | DOMAIN EVIDENCE ONLY; NOT LEGAL EQUIVALENCE |
| StVO precedence and explicit-understanding basis | Curated official StVO source | OFFICIAL_REGULATORY_REQUIREMENT |
| Two-message proposal/response state machine | Project digital agreement model | ENGINEERING_FORMALIZATION |
| Exact claim/proposal identity matching | Logical agreement consistency | MATHEMATICAL_REQUIREMENT |
| Ideal same-step immutable message snapshot | Isolates protocol semantics from networking | EXPERIMENTAL_BASELINE_ASSUMPTION |
| No timeout/retry/range/loss parameters | Step 5E.1 scope avoids unsupported values | SCOPE CHOICE |
| Future ACCEPT/REJECT decision policy | No established deterministic rule | REQUIRES_FUTURE_EXPERIMENT |
| Per-claim ProposalId grouping | Independent semantic claims must remain distinguishable | MATHEMATICAL / SEMANTIC REQUIREMENT |
| Learned ACCEPT/REJECT interface | Multi-agent negotiation research design | RESEARCH DESIGN CHOICE |
| Response network sharing, heads, layers, activation, and dimensions | No project ablation yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Shared actor parameters for homogeneous AVs | Homogeneous-agent option | ARCHITECTURE_CHOICE_REQUIRES_ABLATION |
| SUM versus MEAN aggregation | Baseline SUM; comparison untested | ARCHITECTURE_CHOICE_REQUIRES_ABLATION |
| PPO clip epsilon | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Discount factor gamma | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| GAE lambda | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Learning rate | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Entropy coefficient | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Value-loss coefficient | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Gradient clipping | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Actor/critic hidden dimensions and layers | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Activation and dropout | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Batch size, rollout length, and training epochs | No project experiment yet | REQUIRES_EXPERIMENTAL_SELECTION |
| Reward terms and weights | Reward design is out of scope | REQUIRES_EXPERIMENTAL_SELECTION |

No PPO optimization field above is configured in Step 5E; each has operational
status `NOT_CONFIGURED_STEP_5E`.

> A parameter value reported in a research paper is an experimental
> configuration for that paper's environment unless the source establishes a
> generally applicable theoretical or physical requirement. Such values are
> not copied automatically into this project.

## Input and CTDE contracts

The decentralized actor receives ego and counterparty IDs as metadata, current
ego and local-graph MPNN embeddings, a claim representation, an exact Boolean
claim-action mask, and provenance identifying the ego LDM, current same-step
V2V graph, current MPNN encoding, and current deterministic regulatory
evidence. IDs are never numeric features.

The centralized critic is `TRAINING_ONLY` and
`NOT_AVAILABLE_TO_DEPLOYED_ACTOR`. Its input is a variable-size set of
per-agent representations produced by legitimate agent pipelines. It receives
no SUMO route truth, future route, ground-truth intention, future collision
label, or evaluation-only field. Exact SUM across the agent axis supplies the
Deep Sets baseline; there are no identity slots or maximum participant count.

Production dimensions remain explicit constructor inputs. Validation values
are `TEST_ONLY_NON_OPERATIONAL_VALUE`, not final policy choices. Parameter
sharing is compatible with homogeneous AVs but requires ablation.

## Primary sources

1. Chao Yu et al., “The Surprising Effectiveness of PPO in Cooperative,
   Multi-Agent Games” (2021), arXiv:2103.01955. MAPPO and centralized-value /
   decentralized-policy framing. <https://arxiv.org/abs/2103.01955>
2. Ryan Lowe et al., “Multi-Agent Actor-Critic for Mixed
   Cooperative-Competitive Environments” (NeurIPS 2017). Centralized critic
   training with local policy execution.
   <https://proceedings.neurips.cc/paper/2017/hash/68a9750337a418a86fe06c1991a1d64c-Abstract.html>
3. Shengyi Huang and Santiago Ontañón, “A Closer Look at Invalid Action Masking
   in Policy Gradient Algorithms” (2020), arXiv:2006.14171. State-dependent
   invalid-action masking. <https://arxiv.org/abs/2006.14171>
4. Manzil Zaheer et al., “Deep Sets” (NeurIPS 2017), arXiv:1703.06114.
   Permutation-invariant set functions and SUM aggregation.
   <https://papers.nips.cc/paper/2017/hash/f22e4747da1aa27e363d86d40ff442fe-Abstract.html>
5. Huanbiao Zhuang et al., “Cooperative Decision-Making for Mixed Traffic at an
   Unsignalized Intersection Based on Multi-Agent Reinforcement Learning”
   (Applied Sciences 2023), DOI:10.3390/app13085018. Domain evidence only; no
   numerical or reward settings copied. <https://doi.org/10.3390/app13085018>
6. Shengchao Yan et al., “Courteous Behavior of Automated Vehicles at
   Unsignalized Intersections via Reinforcement Learning” (2021),
   arXiv:2106.06369. Relinquishment as learned coordination evidence, not
   German legal equivalence. <https://arxiv.org/abs/2106.06369>

The German StVO supplies the project's regulatory basis for precedence and
voluntary relinquishment with explicit understanding. The exact digital
proposal/response schema is an engineering research abstraction, not a legally
mandated V2V message format. Ideal same-step communication intentionally
isolates negotiation logic from communication-network performance.

## Step 5G event and transition semantics

Decisions are emitted on categorical semantic changes, not every simulator
step. A claim lifecycle is identified by its authoritative source-snapshot
identity; no elapsed-time threshold is used. `KEEP_CLAIM` resolves immediately
because `CLAIM_RETAINED` is its complete semantic consequence. Leaving it open
would require an undefined waiting boundary. Relinquishment transitions remain
open until the exact proposal receives a deterministic protocol outcome.

Raw immutable NumPy graph tensors—not only detached embeddings—are retained for
replay. Actor reconstruction remains local; centralized participant snapshots
are training-only. Exact elapsed time is `resolution_timestamp -
decision_timestamp`, including valid zero-duration same-step outcomes.

Formal Dec-POMDP proof: not claimed. Formal SMDP proof: not claimed.
Event-driven variable-duration timing is supported for future semi-Markov
formulation. Reward and bootstrap semantics remain undefined at Step 5G.
