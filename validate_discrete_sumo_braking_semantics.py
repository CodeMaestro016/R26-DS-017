"""Step 5J.2B.3 live SUMO discrete-braking semantics validation."""

import math

import traci

from config import AV_TYPE_ID, SIM_TIME_STEP, SUMO_CONFIG
from conflict import MapPathManager
from environment import SUMOEnv
from negotiation_execution import (build_sumo_native_speed_constraint,
    comfortable_minimum_next_speed, continuous_kinematic_reference_cap,
    sumo_euler_comfortable_brake_gap)
from negotiation_scenarios.runner import derive_existing_route_id

FORMER_SPEED = 6.327762945206484
FORMER_DISTANCE = 4.410609013325224


def main():
    assert "step-method.ballistic" not in SUMO_CONFIG.read_text(encoding="utf-8")
    paths, environment = MapPathManager(), SUMOEnv(use_gui=False)
    try:
        environment.start()
        assert "--step-method.ballistic" not in __import__(
            "negotiation_execution.replay", fromlist=[
                "PhysicalBranchReplayRunner"]).PhysicalBranchReplayRunner.COMMAND_ARGUMENTS
        path_id = next(iter(paths.paths))
        route_id = derive_existing_route_id(paths, path_id)
        traci.vehicle.add("BRAKE_AUDIT_AV", route_id, AV_TYPE_ID,
                          departSpeed="max", departLane="free", departPos="base")
        environment.step()
        simulation_step = float(traci.simulation.getDeltaT())
        action_step = float(traci.vehicle.getActionStepLength("BRAKE_AUDIT_AV"))
        comfortable = float(traci.vehicle.getDecel("BRAKE_AUDIT_AV"))
        emergency = float(traci.vehicle.getEmergencyDecel("BRAKE_AUDIT_AV"))
        native_stop = float(traci.vehicle.getStopSpeed(
            "BRAKE_AUDIT_AV", FORMER_SPEED, FORMER_DISTANCE))
        native_unforced = float(
            traci.vehicle.getSpeedWithoutTraCI("BRAKE_AUDIT_AV"))
        assert simulation_step == SIM_TIME_STEP
        continuous = continuous_kinematic_reference_cap(
            FORMER_DISTANCE, comfortable)
        gap = sumo_euler_comfortable_brake_gap(
            FORMER_SPEED, comfortable, simulation_step)
        minimum = comfortable_minimum_next_speed(
            FORMER_SPEED, comfortable, simulation_step)
        record = build_sumo_native_speed_constraint(
            "BRAKE_AUDIT_AV", "CZ_016", FORMER_DISTANCE, comfortable,
            FORMER_SPEED, simulation_step, action_step, native_stop,
            native_unforced)
        assert FORMER_SPEED > continuous
        assert gap <= FORMER_DISTANCE
        assert native_stop >= minimum
        assert record.comfortable_feasible

        print("Step 5J.2B.3 SUMO Discrete Braking Validation\n")
        print("SUMO semantics")
        print(f"  SUMO version: {tuple(traci.getVersion())}")
        print("  Integration method: SEMI_IMPLICIT_EULER")
        print(f"  Simulation step: {simulation_step}")
        print(f"  Action step: {action_step}")
        print("  New controller timestep: False\n")
        print("Dynamics")
        print("  Deceleration source: ACTUAL_SUMO_VEHICLE")
        print(f"  Comfortable deceleration: {comfortable}")
        print(f"  Emergency deceleration diagnostic: {emergency}")
        print("  Emergency deceleration used by controller: False\n")
        print("Former failure")
        print(f"  Speed: {FORMER_SPEED}")
        print(f"  Distance to entry: {FORMER_DISTANCE}")
        print(f"  Continuous reference cap: {continuous}")
        print("  Continuous reference says feasible: False")
        print(f"  Discrete Euler brake gap: {gap}")
        print(f"  SUMO-native stop speed: {native_stop}")
        print(f"  Comfortable minimum next speed: {minimum}")
        print(f"  Native speed without TraCI: {native_unforced}")
        print(f"  Requested precedence speed: {record.requested_precedence_speed_mps}")
        print("  SUMO discrete comfortable feasibility: PASS\n")
        print("Numerical integrity")
        print("  Arbitrary distance margin: 0")
        print("  Arbitrary time margin: 0")
        print("  Comparison tolerance: 0")
        print("  Emergency-deceleration substitution: False")
    finally:
        environment.close()


if __name__ == "__main__": main()
