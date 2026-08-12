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

The two-action vocabulary is insufficient to complete a binding multi-agent
coordination protocol: it does not represent counterparty receipt,
acknowledgement, or acceptance of a relinquishment proposal. Step 5E therefore
records `ACTION_PROTOCOL_INCOMPLETE`. The actor produces preferences only; no
action is sampled, made authoritative, transmitted, or executed. A later
protocol-design checkpoint must define the missing agreement state.

## Research-supported choices versus unselected parameters

| Item | Basis | Status |
|---|---|---|
| MAPPO and centralized value function with decentralized policies | Yu et al. (2021) | RESEARCH-SUPPORTED METHOD |
| Centralized training and local actor execution | Lowe et al. (2017) | RESEARCH-SUPPORTED METHOD |
| State-dependent invalid-action masking | Huang and Ontañón (2020) | THEORETICALLY SUPPORTED METHOD |
| Permutation-invariant SUM over agent representations | Zaheer et al. (2017) | RESEARCH-SUPPORTED METHOD |
| Cooperative MARL at mixed-traffic unsignalized intersections | Zhuang et al. (2023) | DOMAIN EVIDENCE ONLY |
| Learned right-of-way relinquishment behavior | Yan et al. (2021) | DOMAIN EVIDENCE ONLY; NOT LEGAL EQUIVALENCE |
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
