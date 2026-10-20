"""Step 5J.2B.4 live SUMO TraCI speed-authority validation."""

# Import math for use in this module.
import math

# Import traci for use in this module.
import traci

# Import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP, SUMO_CONFIG from config for the operations below.
from config import AV_TYPE_ID, SAFE_SUMO_SPEED_MODE, SIM_TIME_STEP, SUMO_CONFIG
# Import MapPathManager from conflict for the operations below.
from conflict import MapPathManager
# Import SUMOEnv from environment for the operations below.
from environment import SUMOEnv
# Import build_sumo_native_speed_constraint, comfortable_minimum_next_speed, continuous_kinematic_reference_cap,
# speed_mode_enforcement, sumo_euler_comfortable_brake_gap from negotiation_execution for the operations below.
from negotiation_execution import (build_sumo_native_speed_constraint,
    comfortable_minimum_next_speed, continuous_kinematic_reference_cap,
    speed_mode_enforcement, sumo_euler_comfortable_brake_gap)
# Import derive_existing_route_id from negotiation_scenarios.runner for the operations below.
from negotiation_scenarios.runner import derive_existing_route_id

# Set FORMER_SPEED to 6.327762945206484.
FORMER_SPEED = 6.327762945206484
# Set FORMER_DISTANCE to 4.410609013325224.
FORMER_DISTANCE = 4.410609013325224


# Main using the inputs and processing steps below.
# Output: no explicit value; normal completion returns None.
# Processing: handle the specified errors.
def main():
    # Require the text 'step-method.ballistic' does not belong to the text read from SUMO_CONFIG; otherwise raise
    # AssertionError.
    assert "step-method.ballistic" not in SUMO_CONFIG.read_text(encoding="utf-8")
    # Set (paths, environment) to a tuple containing the result of MapPathManager(), the result of SUMOEnv().
    paths, environment = MapPathManager(), SUMOEnv(use_gui=False)
    # Attempt the enclosed operations and route matching exceptions to the handlers below.
    try:
        # Call environment.start with the supplied arguments.
        environment.start()
        # Require the text '--step-method.ballistic' does not belong to
        # __import__('negotiation_execution.replay',...; otherwise raise AssertionError.
        assert "--step-method.ballistic" not in __import__(
            # Supply fromlist as a list containing the text 'PhysicalBranchReplayRunner'.
            "negotiation_execution.replay", fromlist=[
                # Supply the text 'PhysicalBranchReplayRunner' to the enclosing expression.
                "PhysicalBranchReplayRunner"]).PhysicalBranchReplayRunner.COMMAND_ARGUMENTS
        # Set path_id to the next item from the result of iter(paths.paths).
        path_id = next(iter(paths.paths))
        # Set route_id to the result of derive_existing_route_id(paths, path_id).
        route_id = derive_existing_route_id(paths, path_id)
        # Add the text 'BRAKE_AUDIT_AV' to traci.vehicle.
        traci.vehicle.add("BRAKE_AUDIT_AV", route_id, AV_TYPE_ID,
                          # Supply departSpeed as the text 'max'.
                          # Supply departLane as the text 'free'.
                          # Supply departPos as the text 'base'.
                          departSpeed="max", departLane="free", departPos="base")
        # Set the SUMO speed-control mode using traci.vehicle.setSpeedMode.
        traci.vehicle.setSpeedMode("BRAKE_AUDIT_AV", SAFE_SUMO_SPEED_MODE)
        # Advance environment using its configured step operation.
        environment.step()
        # Set simulation_step to a floating-point number built from the result of traci.simulation.getDeltaT().
        simulation_step = float(traci.simulation.getDeltaT())
        # Set action_step to a floating-point number built from the result of
        # traci.vehicle.getActionStepLength(the text 'BRAKE_AUDIT_AV').
        action_step = float(traci.vehicle.getActionStepLength("BRAKE_AUDIT_AV"))
        # Set comfortable to a floating-point number built from the result of traci.vehicle.getDecel(the text
        # 'BRAKE_AUDIT_AV').
        comfortable = float(traci.vehicle.getDecel("BRAKE_AUDIT_AV"))
        # Set emergency to a floating-point number built from the result of traci.vehicle.getEmergencyDecel(the
        # text 'BRAKE_AUDIT_AV').
        emergency = float(traci.vehicle.getEmergencyDecel("BRAKE_AUDIT_AV"))
        # Set native_stop to a floating-point number built from the result of traci.vehicle.getStopSpeed(the text
        # 'BRAKE_AUDIT_AV', FORMER_SPEED, FORMER_DISTANCE).
        native_stop = float(traci.vehicle.getStopSpeed(
            # Supply FORMER_DISTANCE to traci.vehicle.getStopSpeed.
            "BRAKE_AUDIT_AV", FORMER_SPEED, FORMER_DISTANCE))
        # Set native_unforced to a floating-point number built from the result of
        # traci.vehicle.getSpeedWithoutTraCI(the text 'BRAKE_AUDIT_AV').
        native_unforced = float(
            # Supply the result of traci.vehicle.getSpeedWithoutTraCI(the text 'BRAKE_AUDIT_AV') to float.
            traci.vehicle.getSpeedWithoutTraCI("BRAKE_AUDIT_AV"))
        # Set speed_mode to an integer built from the result of traci.vehicle.getSpeedMode(the text
        # 'BRAKE_AUDIT_AV').
        speed_mode = int(traci.vehicle.getSpeedMode("BRAKE_AUDIT_AV"))
        # Set enforcement to the result of speed_mode_enforcement(speed_mode).
        enforcement = speed_mode_enforcement(speed_mode)
        # Require speed_mode equals SAFE_SUMO_SPEED_MODE; otherwise raise AssertionError.
        assert speed_mode == SAFE_SUMO_SPEED_MODE
        # Require whether every item is true in values from enforcement; otherwise raise AssertionError.
        assert all(enforcement.values())
        # Require simulation_step equals SIM_TIME_STEP; otherwise raise AssertionError.
        assert simulation_step == SIM_TIME_STEP
        # Set continuous to the result of continuous_kinematic_reference_cap(FORMER_DISTANCE, comfortable).
        continuous = continuous_kinematic_reference_cap(
            # Supply FORMER_DISTANCE to continuous_kinematic_reference_cap.
            FORMER_DISTANCE, comfortable)
        # Set gap to the result of sumo_euler_comfortable_brake_gap(FORMER_SPEED, comfortable, simulation_step).
        gap = sumo_euler_comfortable_brake_gap(
            # Supply simulation_step to sumo_euler_comfortable_brake_gap.
            FORMER_SPEED, comfortable, simulation_step)
        # Set minimum to the result of comfortable_minimum_next_speed(FORMER_SPEED, comfortable, simulation_step).
        minimum = comfortable_minimum_next_speed(
            # Supply simulation_step to comfortable_minimum_next_speed.
            FORMER_SPEED, comfortable, simulation_step)
        # Set record to the result of build_sumo_native_speed_constraint(the text 'BRAKE_AUDIT_AV', the text
        # 'CZ_016', FORMER_DISTANCE, comfortable, FORMER_SPEED,...).
        record = build_sumo_native_speed_constraint(
            # Supply FORMER_DISTANCE to build_sumo_native_speed_constraint.
            "BRAKE_AUDIT_AV", "CZ_016", FORMER_DISTANCE, comfortable,
            # Supply simulation_step to build_sumo_native_speed_constraint.
            FORMER_SPEED, simulation_step, action_step, native_stop,
            # Supply native_unforced to build_sumo_native_speed_constraint.
            native_unforced, speed_mode)
        # Require FORMER_SPEED is greater than continuous; otherwise raise AssertionError.
        assert FORMER_SPEED > continuous
        # Require gap is at most FORMER_DISTANCE; otherwise raise AssertionError.
        assert gap <= FORMER_DISTANCE
        # Require native_stop is at least minimum; otherwise raise AssertionError.
        assert native_stop >= minimum
        # Require record.comfortable_feasible is the same object as None; otherwise raise AssertionError.
        assert record.comfortable_feasible is None
        # Require record.precommand_python_feasibility_rejection is the same object as False; otherwise raise
        # AssertionError.
        assert record.precommand_python_feasibility_rejection is False
        # Request the specified SUMO speed using traci.vehicle.setSpeed.
        traci.vehicle.setSpeed(
            # Supply record.requested_precedence_speed_mps to traci.vehicle.setSpeed.
            "BRAKE_AUDIT_AV", record.requested_precedence_speed_mps)
        # Advance environment using its configured step operation.
        environment.step()
        # Set actual_next_speed to a floating-point number built from the SUMO speed of vehicle the text
        # 'BRAKE_AUDIT_AV'.
        actual_next_speed = float(traci.vehicle.getSpeed("BRAKE_AUDIT_AV"))
        # Set actual_acceleration to a floating-point number built from the result of
        # traci.vehicle.getAcceleration(the text 'BRAKE_AUDIT_AV').
        actual_acceleration = float(
            # Supply the result of traci.vehicle.getAcceleration(the text 'BRAKE_AUDIT_AV') to float.
            traci.vehicle.getAcceleration("BRAKE_AUDIT_AV"))
        # Set unchanged_mode to an integer built from the result of traci.vehicle.getSpeedMode(the text
        # 'BRAKE_AUDIT_AV').
        unchanged_mode = int(traci.vehicle.getSpeedMode("BRAKE_AUDIT_AV"))
        # Require unchanged_mode equals speed_mode; otherwise raise AssertionError.
        assert unchanged_mode == speed_mode
        # Require whether actual_next_speed contains finite numeric values and actual_next_speed is at least 0.0;
        # otherwise raise AssertionError.
        assert math.isfinite(actual_next_speed) and actual_next_speed >= 0.0
        # Require whether actual_acceleration contains finite numeric values; otherwise raise AssertionError.
        assert math.isfinite(actual_acceleration)
        # Require actual_next_speed is at least record.requested_precedence_speed_mps; otherwise raise
        # AssertionError.
        assert actual_next_speed >= record.requested_precedence_speed_mps
        # Require the negation of the result of traci.simulation.getCollidingVehiclesIDList(); otherwise raise
        # AssertionError.
        assert not traci.simulation.getCollidingVehiclesIDList()

        # Display the text 'Step 5J.2B.4 SUMO Native Speed Authority'.
        print("Step 5J.2B.4 SUMO Native Speed Authority\n")
        # Display the text 'Runtime authority'.
        print("Runtime authority")
        # Display formatted text built from the embedded values.
        print(f"  SUMO version: {tuple(traci.getVersion())}")
        # Display the text 'Integration method: SEMI_IMPLICIT_EULER'.
        print("  Integration method: SEMI_IMPLICIT_EULER")
        # Display formatted text built from the embedded values.
        print(f"  Simulation step: {simulation_step}")
        # Display formatted text built from the embedded values.
        print(f"  Action step: {action_step}")
        # Display formatted text built from the embedded values.
        print(f"  Speed mode: {speed_mode}")
        # Display formatted text built from the embedded values.
        print(f"  Safe-speed enforcement: {'PASS' if enforcement['safe_speed'] else 'FAIL'}")
        # Display formatted text built from the embedded values.
        print(f"  Max-acceleration enforcement: {'PASS' if enforcement['max_acceleration'] else 'FAIL'}")
        # Display formatted text built from the embedded values.
        print(f"  Max-deceleration enforcement: {'PASS' if enforcement['max_deceleration'] else 'FAIL'}")
        # Display formatted text built from the embedded values.
        print(f"  Junction priority enforcement: {'PASS' if enforcement['junction_priority'] else 'FAIL'}\n")
        # Display the text 'Dynamics'.
        print("Dynamics")
        # Display the text 'Deceleration source: ACTUAL_SUMO_VEHICLE'.
        print("  Deceleration source: ACTUAL_SUMO_VEHICLE")
        # Display formatted text built from the embedded values.
        print(f"  Comfortable deceleration: {comfortable}")
        # Display formatted text built from the embedded values.
        print(f"  Emergency deceleration diagnostic: {emergency}")
        # Display the text 'Emergency deceleration used by controller: False'.
        print("  Emergency deceleration used by controller: False\n")
        # Display the text 'Former diagnostic state'.
        print("Former diagnostic state")
        # Display formatted text built from the embedded values.
        print(f"  Speed: {FORMER_SPEED}")
        # Display formatted text built from the embedded values.
        print(f"  Distance to entry: {FORMER_DISTANCE}")
        # Display formatted text built from the embedded values.
        print(f"  Continuous reference cap: {continuous}")
        # Display the text 'Continuous reference says feasible: False'.
        print("  Continuous reference says feasible: False")
        # Display formatted text built from the embedded values.
        print(f"  Discrete Euler brake gap: {gap}")
        # Display formatted text built from the embedded values.
        print(f"  SUMO-native stop speed: {native_stop}")
        # Display formatted text built from the embedded values.
        print(f"  Comfortable minimum next speed: {minimum}")
        # Display formatted text built from the embedded values.
        print(f"  Native speed without TraCI: {native_unforced}")
        # Display formatted text built from the embedded values.
        print(f"  Requested precedence speed: {record.requested_precedence_speed_mps}")
        # Display the text 'Python comfortable-minimum live rejection: False'.
        print("  Python comfortable-minimum live rejection: False\n")
        # Display the text 'One-step live TraCI command'.
        print("One-step live TraCI command")
        # Display formatted text built from the embedded values.
        print(f"  Requested TraCI speed: {record.requested_precedence_speed_mps}")
        # Display formatted text built from the embedded values.
        print(f"  Actual next SUMO speed: {actual_next_speed}")
        # Display formatted text built from the embedded values.
        print(f"  Actual next acceleration: {actual_acceleration}")
        # Display the text 'Speed mode unchanged: PASS'.
        print("  Speed mode unchanged: PASS")
        # Display the text 'Native minNextSpeed protection active: PASS'.
        print("  Native minNextSpeed protection active: PASS")
        # Display the text 'Runtime final speed authority: SUMO_PROCESS_TRACI_SPEED_CONTROL'.
        print("  Runtime final speed authority: SUMO_PROCESS_TRACI_SPEED_CONTROL\n")
        # Display the text 'Numerical integrity'.
        print("Numerical integrity")
        # Display the text 'Arbitrary distance margin: 0'.
        print("  Arbitrary distance margin: 0")
        # Display the text 'Arbitrary time margin: 0'.
        print("  Arbitrary time margin: 0")
        # Display the text 'Comparison tolerance: 0'.
        print("  Comparison tolerance: 0")
        # Display the text 'Project epsilon: 0'.
        print("  Project epsilon: 0")
        # Display the text 'Emergency-deceleration substitution: False'.
        print("  Emergency-deceleration substitution: False")
    # Run these cleanup steps whether the preceding operations succeed or raise an exception.
    finally:
        # Call environment.close with the supplied arguments.
        environment.close()


# Run this branch when __name__ equals the text '__main__'.
# Call main with the supplied arguments.
if __name__ == "__main__": main()
