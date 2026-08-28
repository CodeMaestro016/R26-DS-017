# Final MAPPO Selection Report

## Research question

Which eligible configuration among predefined E5/E10/E15 gives the lowest mean validation total team travel time?

## Controlled design

Only PPO update epochs varied. Learning rate, clip, architecture, GNN mode, masks, environment, manifests and H=2 remained fixed.

## Validation results

- E5: mean replication-total TTT 15817.906666666666; ELIGIBLE
- E10: mean replication-total TTT 16579.066666666666; ELIGIBLE
- E15: mean replication-total TTT 16942.56; ELIGIBLE

## Selected configuration

E5 — validation-selected among the predefined tested candidates.

## Held-out and baseline

The deterministic no-negotiation baseline failed the predefined hard safety-validity gate in 1 held-out scenario(s). Therefore a full safety-valid overall efficiency comparison is not available. The selected MAPPO configuration remained eligible under the recorded held-out hard safety gates.

## Limitations

N=3 and H=2 are bounded project-resource choices. This is not an exhaustive search and does not establish global optimality.
