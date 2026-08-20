# Project Foundation

This chapter explains the current project at a high level. It deliberately avoids source-level details, formulas, PPO mathematics, and model-training internals.

## Research Problem

An autonomous vehicle (AV) must decide how to move without a human driver. At a signalized intersection, traffic lights normally decide which direction may move. This project studies a different case: an **unsignalized four-way intersection**, where there is no traffic light controlling the vehicles.

At this intersection, several AVs can arrive at nearly the same time. Each AV may intend to go straight, turn left, or turn right. Some of those movements can safely happen together, but others cross or merge into the same road space. The vehicles therefore need to know their **right-of-way**: who must wait and who has priority.

The practical problem is not merely detecting another vehicle. The system must determine:

- what each nearby vehicle is probably going to do;
- whether the intended paths physically conflict;
- whether the vehicles will reach the shared area at relevant times;
- what the traffic rules require;
- whether the rules already give a clear order; and
- when the remaining ambiguity needs coordinated negotiation.

### Small three-AV example

Suppose three AVs reach the intersection:

- AV1 approaches from the north and wants to turn left.
- AV2 approaches from the south and wants to go straight.
- AV3 approaches from the east and wants to turn right.

AV1's left turn may cross AV2's straight path. AV3's right turn may or may not overlap the same conflict area. The vehicles cannot all assume they should go first. They need a consistent crossing order that respects traffic rules and physical safety.

## Why the Problem Is Difficult

An AV cannot simply “see another vehicle and stop,” for several reasons.

### Each AV has a local view

Each vehicle builds its view from its own position and observations. AV1 may see AV2 clearly while AV3 is farther away or temporarily outside AV1's relevant local area. AV2 and AV3 can therefore hold different local information at the same instant.

### Vehicles can intend different movements

Seeing a vehicle does not reveal whether it will go straight, left, or right. Those choices produce different paths and different conflicts. The implemented system therefore estimates intention and associates vehicles with movement paths.

### Not every nearby vehicle creates a physical conflict

Two vehicles can be close to the intersection while following paths that never overlap. Conversely, two paths can cross even when the vehicles are approaching from directions that initially look separate. The system reasons about map-derived movement geometry and conflict zones.

### Timing matters

A shared conflict zone is dangerous only when vehicles could occupy it at overlapping times. Their positions, speeds, reachability, and estimated arrival times matter—not just their distance from one another.

### Traffic rules matter

The project uses a reviewed German StVO rule profile for the chosen intersection type. A vehicle must not learn its way around a mandatory legal obligation. The rules first establish claims such as “this vehicle must yield to that vehicle.”

### Rules can form a cycle or leave negotiable ambiguity

With several vehicles, local precedence claims can form a cycle: AV1 yields to AV2, AV2 yields to AV3, and AV3 yields to AV1. Everyone waiting forever is not useful. The project represents these relationships and allows negotiation only within the permitted action choices.

### The AVs decide independently

There is no single runtime controller choosing every vehicle's action from perfect global knowledge. Each actor uses its ego vehicle's local observation. The vehicles must still produce compatible decisions, so they exchange structured precedence claims and negotiation messages.

## Research Goal

### A. One very simple sentence

The goal is to help multiple autonomous vehicles agree on a safe, rule-respecting order for crossing a complex unsignalized intersection.

### B. Thirty-second supervisor explanation

This project builds a SUMO research prototype for several autonomous vehicles arriving at an unsignalized four-way intersection. Each vehicle forms an ego-local view, estimates nearby vehicles' intended movements, checks physical path conflicts and German traffic-rule precedence, and represents the situation as a negotiation graph. A trained MAPPO demonstration policy can make decentralized, hard-masked negotiation decisions. Those decisions are converted into physical precedence constraints and SUMO speed control. The prototype demonstrates that the complete path can execute, but it does not claim that the demonstration policy is statistically optimal.

### C. Formal thesis-style paragraph

The research goal is to design and demonstrate a multi-agent right-of-way coordination prototype for autonomous vehicles operating at an unsignalized four-way intersection under partial ego-local observations. The system integrates object-level perception, local dynamic maps, learned movement-intention inference, map-derived conflict and temporal reasoning, explicit regulatory precedence, graph-structured negotiation, and centralized-training/decentralized-execution MAPPO actors. Learned negotiation actions are constrained by hard semantic, regulatory, conflict-zone, and SUMO safety requirements before physical execution. The implemented demonstration is intended to establish end-to-end feasibility and traceable research evidence, rather than statistical optimality, convergence, or deployment readiness.

## High-Level Architecture

There are two related executable architectures. The normal simulation is a shadow-validation path; the research demo is the learned negotiation and physical-execution path.

### End-to-end research demonstration path

| Stage name | Simple purpose | Input | Output |
|---|---|---|---|
| SUMO simulation | Provides the intersection and moving vehicles | Network, routes, scenario schedule, simulation settings | Current vehicle and simulation state |
| Ego-local perception | Converts simulator state into what one ego AV is allowed to observe | Vehicle states and ego identity | Filtered ego-relative object observations |
| Local Dynamic Map (LDM) | Maintains each AV's local tracks and recent motion history | Ego-local observations over time | Per-AV local world model |
| Intention prediction | Estimates likely movement intention from recent motion | Local vehicle history and ONNX GRU models | Primary, secondary, and fused intention estimates or UNKNOWN |
| Movement and conflict reasoning | Relates vehicles to map paths and shared conflict zones | LDM, predicted intentions, compiled SUMO map | Local conflict relationships and temporal occupancy evidence |
| Traffic-rule reasoning | Establishes mandatory regulatory precedence | Local conflict evidence and StVO rule profile | Per-ego yield/priority assessments |
| Local precedence claims | Expresses who should yield to whom | Regulatory assessment and local graph | Directed precedence claims |
| Ideal same-step claim exchange | Shares only structured current-step claims | Each AV's published local claims | Frozen message set visible to receivers |
| Joint local precedence graph | Gives each AV a locally reconstructed negotiation context | Ego graph and received claims | Ego-owned joint graph snapshot |
| Tensor/GNN representation | Converts the graph into neural input and embeddings | Encoded local graph | Node, edge, graph, and subject representations |
| MAPPO proposer/responder actors | Select learned negotiation actions from local information | Ego-local representations and hard action masks | Keep/relinquish and accept/reject decisions |
| Negotiation protocol | Applies compatible proposals and responses to precedence | Learned masked decisions and claim identities | Effective coordination/precedence graph |
| Physical execution mapping and planner | Turns abstract precedence into executable vehicle obligations | Effective graph, movement paths, conflict zones | Per-vehicle execution plan and speed constraints |
| SUMO control | Enforces the plan while retaining SUMO-native safety behavior | Planned speed caps/releases | Physical vehicle motion |
| Evaluation and evidence | Checks outcomes and implementation boundaries | Decisions, control records, vehicle outcomes | Collisions, completions, travel time, violations, and audit evidence |

### Normal `main.py` path

The first stages also run in `main.py`, but the newer learned stack is **shadow-only** there. `main.py` builds local conflict, temporal, traffic-rule, precedence, message, and encoded graph information for observation and validation. It does not use a trained GNN/MAPPO policy to control vehicles. A legacy rule-based negotiation manager produces `ASSERT`, `YIELD`, or `MAINTAIN`, and those actions are translated into TraCI speed commands.

Therefore, the simple diagram must be stated carefully:

```text
main.py:
SUMO -> perception/LDM -> ONNX intention + conflict/rules/graphs [shadow]
     -> legacy rule-based negotiation -> SUMO speed control -> evaluation

run_research_demo.py:
SUMO -> perception/LDM -> intention -> conflict/rules/precedence
     -> local graph/GNN representation -> trained MAPPO actors
     -> hard-masked protocol outcome -> physical planner
     -> SUMO speed control -> demonstration evidence
```

## Rule-Based vs Learned Components

“Neural” does not automatically mean “learned in this project.” A component is called learned here only when the executed parameters came from training.

| Component | Rule-based / mathematical / learned | Purpose |
|---|---|---|
| Perception filtering | Rule-based/geometric | Produces ego-relative observations under the configured sensor profile |
| Local Dynamic Map | Rule-based state management | Maintains local tracks, confidence, history, and current reasoning snapshots |
| Intention GRUs | Learned | Predict movement intention using pretrained ONNX GRU parameters |
| Map-path construction | Mathematical/geometric | Derives movement paths from the compiled SUMO network |
| Conflict geometry | Mathematical/geometric | Finds crossing/merging paths and conflict zones |
| Temporal occupancy/reachability | Mathematical/kinematic | Checks whether vehicles can occupy relevant zones at overlapping times |
| German traffic rules | Rule-based/regulatory | Creates mandatory precedence and yield assessments |
| Local and joint precedence graphs | Rule-based/graph construction | Represents directed claims and combines ego-local communicated context |
| Claim/protocol semantic encoding | Deterministic/mathematical | Converts negotiation meaning into stable numerical representations |
| Hard action masks | Rule-based safety/semantic constraints | Prevents invalid or disallowed negotiation actions |
| GNN encoder in the final demo | Neural but fixed, not learned by the demonstrated training tranche | Produces graph embeddings; its parameters are reconstructed and kept fixed |
| MAPPO proposer actor | Learned | Chooses whether to keep or propose relinquishing an eligible claim |
| MAPPO responder actor | Learned | Chooses whether to accept or reject a relinquishment proposal |
| Centralized critic | Learned during training; not used in demo execution | Estimates centralized value for training updates only |
| Negotiation protocol | Rule-based/deterministic | Matches proposals and responses and constructs the effective graph |
| Physical execution mapper | Rule-based/semantic | Separates physical obligations from nonphysical coordination relationships |
| Conflict-zone execution planner | Rule-based/geometric | Builds an executable crossing plan from precedence and zone state |
| SUMO speed constraints and safety gates | Rule-based/physical | Applies safe speed caps or releases through TraCI |
| Legacy `NegotiationManager` in `main.py` | Rule-based | Supplies the normal simulation's actual control-facing decisions |

## Decentralized Architecture

In this project, **decentralized execution** means that each AV's learned actor makes its decision from that AV's local runtime information—not from a perfect global table of all vehicles.

- AV1 owns AV1's LDM and actor observation.
- AV2 owns AV2's LDM and actor observation.
- AV3 owns AV3's LDM and actor observation.

AV1's LDM is not automatically identical to AV2's LDM. They observe from different locations, can have different relevant neighbors, and build ego-relative graphs. They exchange structured precedence claims, but that exchange does not merge every vehicle's raw world state into one omniscient runtime controller.

### Centralized training

During training, extra joint information can be used by a **centralized critic** to judge the shared situation and calculate training signals. The critic helps update the actors. Centralized training is allowed to see information that an individual runtime actor does not receive.

### Decentralized execution

After training, each proposer or responder actor selects an action from its ego-local representation and hard action mask. The final research demo deliberately removes the centralized critic from the runtime policy bundle. Its recorded runtime critic-call count is zero, and actor input records report zero route-truth leakage.

This is commonly summarized as **centralized training, decentralized execution (CTDE)**.

## main.py vs run_research_demo.py

### `python main.py`

This starts the configured 200-second SUMO simulation, normally with the GUI. It spawns the configured validation traffic, updates per-vehicle observations and LDMs, runs the trained ONNX intention predictor, builds conflict/occupancy/regulatory/precedence information, exchanges claims, encodes graphs, records evaluation data, and displays or reports diagnostics.

However, these newer intention-aware regulatory and graph/MARL components remain shadow-only in this path. They do not issue learned control actions. The control-facing path is the legacy rule-based `NegotiationManager`, which chooses `ASSERT`, `YIELD`, or `MAINTAIN`; `apply_action` converts that choice into a SUMO speed command. The executable explicitly reports zero learned policy actions.

### `python run_research_demo.py`

This runs a fixed three-scenario, headless SUMO research demonstration. It creates or verifies the demonstration policy from the preselected replication-0/state-2 checkpoint, loads trained proposer and responder actor parameters, and selects scenarios from the frozen training manifest using a deterministic structural rule rather than performance.

For each scenario, it builds ego-local graph observations, uses the trained actors with hard action masks, resolves the negotiation protocol, maps the result to physical obligations, plans conflict-zone execution, and applies SUMO speed control. It records detailed demonstration evidence and verifies that policy hashes remain unchanged. It performs no training, optimizer step, backward pass, PPO update, or parameter update. The centralized critic is absent at runtime.

### Learned MAPPO actions enabled?

| Command | Learned MAPPO actions? | Actual vehicle-control source |
|---|---|---|
| `python main.py` | No | Legacy rule-based negotiation manager |
| `python run_research_demo.py` | Yes | Trained decentralized proposer/responder actors, constrained and translated by deterministic safety/execution components |

## Example Three-AV Story

Three autonomous cars approach the four-way intersection at nearly the same time.

Each car first observes the scene from its own position. AV1 builds one local picture, AV2 builds another, and AV3 builds a third. Their pictures overlap, but they are not assumed to be identical.

The cars keep short motion histories for the vehicles they observe. The intention predictor uses those histories to estimate whether each nearby car is likely to go straight, left, or right. If the evidence is insufficient, it can remain conservative and report that the intention is unknown.

The system places the likely movements on the intersection map. It checks which paths cross or merge and whether the cars could reach the same conflict areas at relevant times. Cars with unrelated paths do not need to be ordered merely because they are nearby.

Next, each car applies the traffic-rule profile to its local conflict situation. This produces directed claims such as “AV1 must yield to AV2.” The cars exchange these structured claims for the current step. Each car then reconstructs a joint local precedence graph from its own information and the messages it received.

If the rules already provide a clear and physically safe order, that order is preserved. If eligible claims form a negotiable ambiguity or cycle, the trained decentralized actors choose among the allowed actions. A vehicle may keep a claim, propose relinquishing it, accept a valid proposal, or reject it. Hard masks prevent actions that are invalid for that claim or role.

The deterministic protocol combines compatible choices into an effective order. The physical mapper and planner then translate that abstract order into conflict-zone obligations and speed constraints. One car is released when safe, another is capped or held, and SUMO's native safety behavior remains active.

The vehicles cross according to that plan. Finally, the system records whether vehicles completed their routes, whether any collision or blocked-zone violation occurred, how much travel time accumulated, which learned decisions were made, and whether the policy remained unchanged.

## What the Research Demonstrates

The current evidence supports the following careful claims:

- A complete research prototype has been implemented and executed in SUMO.
- Ego-local perception and LDMs feed intention, conflict, regulatory, and negotiation representations.
- The normal simulation can run the ONNX intention models and the newer graph/regulatory stack in shadow mode while retaining legacy rule-based control.
- A separate final research demo executes trained decentralized MAPPO proposer/responder decisions in three structurally selected scenarios.
- Learned demo actions are subject to hard masks and deterministic regulatory, conflict-zone, physical-execution, and SUMO safety mechanisms.
- The centralized critic is not used for runtime demo decisions.
- The final recorded demo contains 22 learned decisions across three scenarios, with zero recorded collisions and zero blocked-zone violations.
- The selected demo policy is traceable to a protected checkpoint, is used without further training, and remains hash-stable during the demo.
- The implementation demonstrates end-to-end feasibility and research-prototype integration.

## What the Research Does Not Claim

The project must **not** claim that:

- the demonstrated MAPPO policy is statistically optimal;
- training has converged;
- exhaustive hyperparameter selection has been completed;
- the checkpoint is the final performance-selected model;
- three demonstration scenarios prove general safety or broad generalization;
- zero collisions in this limited demo prove that collisions are impossible;
- the normal `main.py` simulation is controlled by MAPPO;
- the centralized critic participates in decentralized runtime decisions;
- each AV has perfect global information;
- learned negotiation can override mandatory traffic rules or safety gates;
- the simulator prototype is ready for deployment on real public roads; or
- the implementation constitutes a formal proof of a Dec-POMDP, SMDP, legal compliance, or system-wide safety.

The correct headline is:

> **A trained, decentralized MAPPO negotiation policy has been demonstrated as part of an end-to-end SUMO research prototype, but it has not been established as a statistically optimal or deployment-ready policy.**

## Self-Test Questions

1. Why is seeing another vehicle not enough to decide who should cross first?
2. What does “right-of-way” mean in this project?
3. Why can AV1's LDM differ from AV2's LDM at the same time?
4. What is the difference between a nearby vehicle and a physically conflicting vehicle?
5. What role does the intention predictor play before conflict reasoning?
6. Why are traffic rules applied before learned negotiation choices?
7. What is the difference between centralized training and decentralized execution?
8. Which component controls vehicles when you run `python main.py`?
9. Which learned components select negotiation actions in `python run_research_demo.py`?
10. Why can the project claim an end-to-end research demonstration but not a statistically optimal MAPPO policy?
