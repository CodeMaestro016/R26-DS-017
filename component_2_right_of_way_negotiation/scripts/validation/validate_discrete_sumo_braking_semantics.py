"""Step 5J.2B.4 live SUMO TraCI speed-authority validation."""

import math

import traci

from config import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP, SUMO_CONFIG
from conflict import MapPathManager
from environment import SUMOEnv
from negotiation_execution import (build_sumo_native_speed_constraint,
    comfortable_minimum_next_speed, continuous_kinematic_reference_cap,
    speed_mode_enforcement, sumo_euler_comfortable_brake_gap)
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
        traci.vehicle.setSpeedMode("BRAKE_AUDIT_AV", SAFE_SUMO_SPEED_MODE)
        environment.step()
        simulation_step = float(traci.simulation.getDeltaT())
        action_step = float(traci.vehicle.getActionStepLength("BRAKE_AUDIT_AV"))
        comfortable = float(traci.vehicle.getDecel("BRAKE_AUDIT_AV"))
        emergency = float(traci.vehicle.getEmergencyDecel("BRAKE_AUDIT_AV"))
        native_stop = float(traci.vehicle.getStopSpeed(
            "BRAKE_AUDIT_AV", FORMER_SPEED, FORMER_DISTANCE))
        native_unforced = float(
            traci.vehicle.getSpeedWithoutTraCI("BRAKE_AUDIT_AV"))
        speed_mode = int(traci.vehicle.getSpeedMode("BRAKE_AUDIT_AV"))
        enforcement = speed_mode_enforcement(speed_mode)
        assert speed_mode == SAFE_SUMO_SPEED_MODE
        assert all(enforcement.values())
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
            native_unforced, speed_mode)
        assert FORMER_SPEED > continuous
        assert gap <= FORMER_DISTANCE
        assert native_stop >= minimum
        assert record.comfortable_feasible is None
        assert record.precommand_python_feasibility_rejection is False
        traci.vehicle.setSpeed(
            "BRAKE_AUDIT_AV", record.requested_precedence_speed_mps)
        environment.step()
        actual_next_speed = float(traci.vehicle.getSpeed("BRAKE_AUDIT_AV"))
        actual_acceleration = float(
            traci.vehicle.getAcceleration("BRAKE_AUDIT_AV"))
        unchanged_mode = int(traci.vehicle.getSpeedMode("BRAKE_AUDIT_AV"))
        assert unchanged_mode == speed_mode
        assert math.isfinite(actual_next_speed) and actual_next_speed >= 0.0
        assert math.isfinite(actual_acceleration)
        assert actual_next_speed >= record.requested_precedence_speed_mps
        assert not traci.simulation.getCollidingVehiclesIDList()

        print("Step 5J.2B.4 SUMO Native Speed Authority\n")
        print("Runtime authority")
        print(f"  SUMO version: {tuple(traci.getVersion())}")
        print("  Integration method: SEMI_IMPLICIT_EULER")
        print(f"  Simulation step: {simulation_step}")
        print(f"  Action step: {action_step}")
        print(f"  Speed mode: {speed_mode}")
        print(f"  Safe-speed enforcement: {'PASS' if enforcement['safe_speed'] else 'FAIL'}")
        print(f"  Max-acceleration enforcement: {'PASS' if enforcement['max_acceleration'] else 'FAIL'}")
        print(f"  Max-deceleration enforcement: {'PASS' if enforcement['max_deceleration'] else 'FAIL'}")
        print(f"  Junction priority enforcement: {'PASS' if enforcement['junction_priority'] else 'FAIL'}\n")
        print("Dynamics")
        print("  Deceleration source: ACTUAL_SUMO_VEHICLE")
        print(f"  Comfortable deceleration: {comfortable}")
        print(f"  Emergency deceleration diagnostic: {emergency}")
        print("  Emergency deceleration used by controller: False\n")
        print("Former diagnostic state")
        print(f"  Speed: {FORMER_SPEED}")
        print(f"  Distance to entry: {FORMER_DISTANCE}")
        print(f"  Continuous reference cap: {continuous}")
        print("  Continuous reference says feasible: False")
        print(f"  Discrete Euler brake gap: {gap}")
        print(f"  SUMO-native stop speed: {native_stop}")
        print(f"  Comfortable minimum next speed: {minimum}")
        print(f"  Native speed without TraCI: {native_unforced}")
        print(f"  Requested precedence speed: {record.requested_precedence_speed_mps}")
        print("  Python comfortable-minimum live rejection: False\n")
        print("One-step live TraCI command")
        print(f"  Requested TraCI speed: {record.requested_precedence_speed_mps}")
        print(f"  Actual next SUMO speed: {actual_next_speed}")
        print(f"  Actual next acceleration: {actual_acceleration}")
        print("  Speed mode unchanged: PASS")
        print("  Native minNextSpeed protection active: PASS")
        print("  Runtime final speed authority: SUMO_PROCESS_TRACI_SPEED_CONTROL\n")
        print("Numerical integrity")
        print("  Arbitrary distance margin: 0")
        print("  Arbitrary time margin: 0")
        print("  Comparison tolerance: 0")
        print("  Project epsilon: 0")
        print("  Emergency-deceleration substitution: False")
    finally:
        environment.close()


if __name__ == "__main__": main()
