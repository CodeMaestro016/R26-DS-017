"""SUMO/TraCI environment wrapper."""

# Import math for use in this module.
import math
# Import shutil for use in this module.
import shutil

# Import traci for use in this module.
import traci

# Import GUI_SETTINGS_FILE, SIM_TIME_STEP, SUMO_CONFIG, SUMO_NETWORK_FILE from config for the operations below.
from config import (GUI_SETTINGS_FILE, SIM_TIME_STEP, SUMO_CONFIG,
                    SUMO_NETWORK_FILE)
# Import SimulationLifecycleEvents from traffic_accounting for the operations below.
from traffic_accounting import SimulationLifecycleEvents


# Define SUMOEnv to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class SUMOEnv:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Input use_gui: the supplied use gui.
    # Input extra_options: the supplied extra options.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, use_gui=False, extra_options=()):
        # Set self.use_gui to use_gui.
        self.use_gui = use_gui
        # Set self.extra_options to a tuple built from extra_options.
        self.extra_options = tuple(extra_options)
        # Set self.step_count to 0.
        self.step_count = 0
        # Set self.current_time to 0.0.
        self.current_time = 0.0
        # Set self.lifecycle_events to the result of SimulationLifecycleEvents(0.0, an empty tuple, an empty
        # tuple).
        self.lifecycle_events = SimulationLifecycleEvents(0.0, (), ())

    # Start using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def start(self):
        # Set binary_name to the text 'sumo-gui' when self.use_gui, otherwise the text 'sumo'.
        binary_name = "sumo-gui" if self.use_gui else "sumo"
        # Set sumo_binary to the result of shutil.which(binary_name) or binary_name.
        sumo_binary = shutil.which(binary_name) or binary_name

        # Run this branch when the negation of whether SUMO_CONFIG is an existing file.
        if not SUMO_CONFIG.is_file():
            # Raise FileNotFoundError with formatted text built from the embedded values to stop this execution
            # path.
            raise FileNotFoundError(
                # Supply formatted text built from the embedded values to FileNotFoundError.
                f"Missing SUMO configuration: {SUMO_CONFIG}"
            )
        # Run this branch when the negation of whether SUMO_NETWORK_FILE is an existing file.
        if not SUMO_NETWORK_FILE.is_file():
            # Raise FileNotFoundError with formatted text built from the embedded values to stop this execution
            # path.
            raise FileNotFoundError(
                # Supply formatted text built from the embedded values to FileNotFoundError.
                f"Missing compiled network: {SUMO_NETWORK_FILE}. "
                "Run networks/build_network.bat before starting the "
                "simulation."
            )

        # Set base_command_options to a list containing the text '-c', a string built from SUMO_CONFIG, the text
        # '--step-length', a string built from...
        base_command_options = [
            "-c",
            # Include a string built from SUMO_CONFIG in this list.
            str(SUMO_CONFIG),
            "--step-length",
            # Include a string built from SIM_TIME_STEP in this list.
            str(SIM_TIME_STEP),
            "--no-step-log",
            "true",
            "--collision.action",
            "warn",
            "--duration-log.disable",
            "true",
        ]
        # Extend base_command_options with self.extra_options.
        base_command_options.extend(self.extra_options)
        # Set command_options to a list built from base_command_options.
        command_options = list(base_command_options)

        # Run this branch when self.use_gui.
        if self.use_gui:
            # Run this branch when the negation of whether GUI_SETTINGS_FILE is an existing file.
            if not GUI_SETTINGS_FILE.is_file():
                # Raise FileNotFoundError with formatted text built from the embedded values to stop this
                # execution path.
                raise FileNotFoundError(
                    # Supply formatted text built from the embedded values to FileNotFoundError.
                    f"Missing SUMO GUI settings: {GUI_SETTINGS_FILE}"
                )
            # Extend command_options with a list containing the text '--gui-settings-file', a string built from
            # GUI_SETTINGS_FILE.
            command_options.extend([
                "--gui-settings-file",
                # Include a string built from GUI_SETTINGS_FILE in this list.
                str(GUI_SETTINGS_FILE),
            ])

        # Display formatted text built from the embedded values.
        print(f"Starting SUMO with {SIM_TIME_STEP:.2f} s steps...")
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call traci.start with the supplied arguments.
            traci.start([sumo_binary, *command_options])
        # Handle traci.exceptions.FatalTraCIError as error using the recovery steps below.
        except traci.exceptions.FatalTraCIError as error:
            # Run this branch when the negation of self.use_gui.
            if not self.use_gui:
                # Raise RuntimeError with the text 'Headless SUMO closed before the TraCI connection was...' to
                # stop this execution path.
                raise RuntimeError(
                    "Headless SUMO closed before the TraCI connection was "
                    "established. Run `sumo -c intersection.sumocfg` to see "
                    "the underlying SUMO configuration error."
                # Evaluate error as part of the enclosing expression.
                ) from error

            # Some Windows graphics/desktop configurations allow sumo-gui to
            # launch but close it before TraCI completes its handshake. The
            # simulation itself does not depend on rendering, so retry the
            # identical command with the headless SUMO binary. This changes
            # only visualization; traffic, safety, and research logic remain
            # identical.
            # Set headless_binary to the result of shutil.which(the text 'sumo') or the text 'sumo'.
            headless_binary = shutil.which("sumo") or "sumo"
            # Display the text 'SUMO GUI closed during TraCI startup; retrying in headless mode.'.
            print(
                "SUMO GUI closed during TraCI startup; retrying in "
                "headless mode."
            )
            # Call traci.start with the supplied arguments.
            traci.start([headless_binary, *base_command_options])
        # Set self.current_time to a floating-point number built from the result of traci.simulation.getTime().
        self.current_time = float(traci.simulation.getTime())
        # Display the text 'SUMO started successfully.'.
        print("SUMO started successfully.")

    # Get vehicles using the inputs and processing steps below.
    # Output: states.
    # Processing: iterate over the relevant records, then handle the specified errors.
    def get_vehicles(self):
        # Set states to an empty dictionary.
        states = {}
        # Iterate over the identifiers reported by traci.vehicle.getIDList, binding each item to vehicle_id.
        for vehicle_id in traci.vehicle.getIDList():
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set angle_degrees to a floating-point number built from the result of
                # traci.vehicle.getAngle(vehicle_id).
                angle_degrees = float(traci.vehicle.getAngle(vehicle_id))
                # SUMO defines this world position at the center of the
                # vehicle's front bumper. Keep that canonical reference;
                # geometry consumers derive a vehicle center when required.
                # Set position to a tuple built from the SUMO position of vehicle vehicle_id.
                position = tuple(traci.vehicle.getPosition(vehicle_id))
                # Set speed to a floating-point number built from the SUMO speed of vehicle vehicle_id.
                speed = float(traci.vehicle.getSpeed(vehicle_id))
                # Set lane_id to the result of traci.vehicle.getLaneID(vehicle_id).
                lane_id = traci.vehicle.getLaneID(vehicle_id)
                # Longitudinal lane position uses the same front-bumper
                # reference, measured along the current SUMO lane.
                # Set lane_position to a floating-point number built from the result of
                # traci.vehicle.getLanePosition(vehicle_id).
                lane_position = float(
                    # Supply the result of traci.vehicle.getLanePosition(vehicle_id) to float.
                    traci.vehicle.getLanePosition(vehicle_id)
                )
                # Set lane_length to a floating-point number built from the result of
                # traci.lane.getLength(lane_id) when lane_id, otherwise 0.0.
                lane_length = (
                    # Evaluate a floating-point number built from the result of traci.lane.getLength(lane_id) when
                    # lane_id, otherwise 0.0 as part of the enclosing expression.
                    float(traci.lane.getLength(lane_id))
                    # Evaluate lane_id as part of the enclosing expression.
                    if lane_id
                    # Supply 0.0 to the enclosing expression.
                    else 0.0
                )
                # Set states[vehicle_id] to a dictionary containing position, speed, heading_radians, length,
                # width, pos, vel, accel,...
                states[vehicle_id] = {
                    # Canonical front-bumper state consumed by perception.
                    # Store position under 'position'.
                    "position": position,
                    # Store speed under 'speed'.
                    "speed": speed,
                    # Store the result of math.radians(angle_degrees) under 'heading_radians'.
                    "heading_radians": math.radians(angle_degrees),
                    # Store a floating-point number built from the result of traci.vehicle.getLength(vehicle_id)
                    # under 'length'.
                    "length": float(traci.vehicle.getLength(vehicle_id)),
                    # Store a floating-point number built from the result of traci.vehicle.getWidth(vehicle_id)
                    # under 'width'.
                    "width": float(traci.vehicle.getWidth(vehicle_id)),
                    # Temporary aliases retained for existing control/dashboard
                    # callers while they migrate to the canonical names.
                    # Store position under 'pos'.
                    "pos": position,
                    # Store speed under 'vel'.
                    "vel": speed,
                    # Store a floating-point number built from the result of
                    # traci.vehicle.getAcceleration(vehicle_id) under 'accel'.
                    "accel": float(
                        # Supply the result of traci.vehicle.getAcceleration(vehicle_id) to float.
                        traci.vehicle.getAcceleration(vehicle_id)
                    ),
                    # Runtime limits come from the active SUMO vehicle/type,
                    # not duplicated research constants.
                    # Store a floating-point number built from the result of traci.vehicle.getAccel(vehicle_id)
                    # under 'max_acceleration_mps2'.
                    "max_acceleration_mps2": float(
                        # Supply the result of traci.vehicle.getAccel(vehicle_id) to float.
                        traci.vehicle.getAccel(vehicle_id)
                    ),
                    # Store a floating-point number built from the result of traci.vehicle.getDecel(vehicle_id)
                    # under 'comfortable_deceleration_mps2'.
                    "comfortable_deceleration_mps2": float(
                        # Supply the result of traci.vehicle.getDecel(vehicle_id) to float.
                        traci.vehicle.getDecel(vehicle_id)
                    ),
                    # Store a floating-point number built from the result of
                    # traci.vehicle.getEmergencyDecel(vehicle_id) under 'emergency_deceleration_mps2'.
                    "emergency_deceleration_mps2": float(
                        # Supply the result of traci.vehicle.getEmergencyDecel(vehicle_id) to float.
                        traci.vehicle.getEmergencyDecel(vehicle_id)
                    ),
                    # Store a floating-point number built from the result of traci.vehicle.getMaxSpeed(vehicle_id)
                    # under 'max_speed_mps'.
                    "max_speed_mps": float(
                        # Supply the result of traci.vehicle.getMaxSpeed(vehicle_id) to float.
                        traci.vehicle.getMaxSpeed(vehicle_id)
                    ),
                    # Store angle_degrees under 'angle_degrees'.
                    "angle_degrees": angle_degrees,
                    # Store lane_id under 'lane_id'.
                    "lane_id": lane_id,
                    # Store lane_position under 'lane_position'.
                    "lane_position": lane_position,
                    # Store lane_length under 'lane_length'.
                    "lane_length": lane_length,
                    # Store the result of traci.vehicle.getRoadID(vehicle_id) under 'road_id'.
                    "road_id": traci.vehicle.getRoadID(vehicle_id),
                    # Evaluation-only truth. ObservationManager must not copy
                    # these fields into perception or operational LDM tracks.
                    # Store the result of traci.vehicle.getRouteID(vehicle_id) under 'route_id'.
                    "route_id": traci.vehicle.getRouteID(vehicle_id),
                    # Store an integer built from the result of traci.vehicle.getRouteIndex(vehicle_id) under
                    # 'route_index'.
                    "route_index": int(traci.vehicle.getRouteIndex(vehicle_id)),
                    # Store the result of traci.vehicle.getTypeID(vehicle_id) under 'type'.
                    "type": traci.vehicle.getTypeID(vehicle_id),
                }
            # Handle traci.TraCIException using the recovery steps below.
            except traci.TraCIException:
                # A vehicle can disappear between ID retrieval and state reads.
                # Skip the rest of this loop iteration and process the next item.
                continue
        # Return states to the caller.
        return states

    # Step using the inputs and processing steps below.
    # Output: the result of self.get_vehicles().
    def step(self):
        # Call traci.simulationStep with the supplied arguments.
        traci.simulationStep()
        # Update self.step_count to its current value plus 1.
        self.step_count += 1
        # Set self.current_time to a floating-point number built from the result of traci.simulation.getTime().
        self.current_time = float(traci.simulation.getTime())
        # Same-step authoritative lifecycle events are captured once directly
        # after simulationStep, before observations or downstream accounting.
        # Set self.lifecycle_events to the result of SimulationLifecycleEvents(self.current_time, a tuple built
        # from the result of traci.simulation.getDepartedIDList(), a...).
        self.lifecycle_events = SimulationLifecycleEvents(
            # Supply self.current_time to SimulationLifecycleEvents.
            self.current_time,
            # Supply a tuple built from the result of traci.simulation.getDepartedIDList() to
            # SimulationLifecycleEvents.
            tuple(traci.simulation.getDepartedIDList()),
            # Supply a tuple built from the result of traci.simulation.getArrivedIDList() to
            # SimulationLifecycleEvents.
            tuple(traci.simulation.getArrivedIDList()),
        )
        # Return the result of self.get_vehicles() to the caller.
        return self.get_vehicles()

    # Close using the inputs and processing steps below.
    # Output: no explicit value; normal completion returns None.
    # Processing: handle the specified errors.
    def close(self):
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Call traci.close with the supplied arguments.
            traci.close()
        # Handle traci.TraCIException using the recovery steps below.
        except traci.TraCIException:
            # Keep this block syntactically valid without performing an operation.
            pass
        # Display formatted text built from the embedded values.
        print(
            # Supply formatted text built from the embedded values to print.
            f"Simulation finished at {self.current_time:.2f} s "
            # Evaluate {self.step_count} as part of the enclosing expression.
            f"after {self.step_count} steps."
        )
