# Final Research Prototype Demonstration

Project: Multi-Agent Negotiation for Right-of-Way in Complex Intersections

Architecture demonstrated: decentralized execution using a CTDE-trained MAPPO policy.

Each AV acts from ego-local observations. Intention predictions support conflict reasoning, traffic rules establish mandatory precedence, and MAPPO resolves negotiable ambiguity or cycles. Learned actions remain subordinate to hard regulatory, conflict-zone, and SUMO safety gates. The resulting agreement is mapped to physical vehicle control.

The centralized critic was not part of runtime decentralized control. HELD_OUT remained untouched.

The demonstration policy is an existing trained checkpoint selected by a deterministic provenance rule for demonstration only. It is not claimed to be the statistically optimal or final selected MAPPO model.

## Demonstrated scenarios

- REGULATORY_CYCLE_NEGOTIATION: `['NEGOTIATION_SCENARIO_V1', 'intersection.net.xml:9316', 'REGULATORY_CYCLE', ['E_IN_0_LEFT', 'N_IN_0_RIGHT', 'S_IN_0_LEFT', 'W_IN_0_RIGHT'], 'ISOLATED_LDM_IN_APPROACH_ZONE_STEP_ALIGNMENT', 'AV', 'DE_STVO_UNCONTROLLED_4WAY_V1']` — 11 learned decisions, 2 completed vehicles, 0 collisions.
- MULTI_FACTOR_MULTI_ACTION_NEGOTIATION: `['NEGOTIATION_SCENARIO_V1', 'intersection.net.xml:9316', 'REGULATORY_CYCLE', ['E_IN_0_LEFT', 'N_IN_0_LEFT', 'S_IN_0_LEFT'], 'ISOLATED_LDM_IN_APPROACH_ZONE_STEP_ALIGNMENT', 'AV', 'DE_STVO_UNCONTROLLED_4WAY_V1']` — 4 learned decisions, 0 completed vehicles, 0 collisions.
- COORDINATION_TO_NONPHYSICAL_EXECUTION_INTERPRETATION: `['NEGOTIATION_SCENARIO_V1', 'intersection.net.xml:9316', 'REGULATORY_CYCLE', ['E_IN_0_LEFT', 'N_IN_0_LEFT', 'S_IN_0_RIGHT'], 'ISOLATED_LDM_IN_APPROACH_ZONE_STEP_ALIGNMENT', 'AV', 'DE_STVO_UNCONTROLLED_4WAY_V1']` — 7 learned decisions, 1 completed vehicles, 0 collisions.

## Boundary

This validates end-to-end implementation, not model optimality. Exhaustive hyperparameter selection remains future work under explicit project resource and statistical protocols.
