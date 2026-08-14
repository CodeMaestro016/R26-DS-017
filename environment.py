"""SUMO/TraCI environment wrapper."""

import math
import shutil

import traci

from config import SIM_TIME_STEP, SUMO_CONFIG, SUMO_NETWORK_FILE
from traffic_accounting import SimulationLifecycleEvents


class SUMOEnv:
    def __init__(self, use_gui=False):
        self.use_gui = use_gui
        self.step_count = 0
        self.current_time = 0.0
        self.lifecycle_events = SimulationLifecycleEvents(0.0, (), ())

    def start(self):
        binary_name = "sumo-gui" if self.use_gui else "sumo"
        sumo_binary = shutil.which(binary_name) or binary_name

        if not SUMO_CONFIG.is_file():
            raise FileNotFoundError(
                f"Missing SUMO configuration: {SUMO_CONFIG}"
            )
        if not SUMO_NETWORK_FILE.is_file():
            raise FileNotFoundError(
                f"Missing compiled network: {SUMO_NETWORK_FILE}. "
                "Run networks/build_network.bat before starting the "
                "simulation."
            )

        command_options = [
            "-c",
            str(SUMO_CONFIG),
            "--step-length",
            str(SIM_TIME_STEP),
            "--no-step-log",
            "true",
            "--collision.action",
            "warn",
            "--duration-log.disable",
            "true",
        ]

        print(f"Starting SUMO with {SIM_TIME_STEP:.2f} s steps...")
        try:
            traci.start([sumo_binary, *command_options])
        except traci.exceptions.FatalTraCIError as error:
            if not self.use_gui:
                raise RuntimeError(
                    "Headless SUMO closed before the TraCI connection was "
                    "established. Run `sumo -c intersection.sumocfg` to see "
                    "the underlying SUMO configuration error."
                ) from error

            # Some Windows graphics/desktop configurations allow sumo-gui to
            # launch but close it before TraCI completes its handshake. The
            # simulation itself does not depend on rendering, so retry the
            # identical command with the headless SUMO binary. This changes
            # only visualization; traffic, safety, and research logic remain
            # identical.
            headless_binary = shutil.which("sumo") or "sumo"
            print(
                "SUMO GUI closed during TraCI startup; retrying in "
                "headless mode."
            )
            traci.start([headless_binary, *command_options])
        self.current_time = float(traci.simulation.getTime())
        print("SUMO started successfully.")

    def get_vehicles(self):
        states = {}
        for vehicle_id in traci.vehicle.getIDList():
            try:
                angle_degrees = float(traci.vehicle.getAngle(vehicle_id))
                # SUMO defines this world position at the center of the
                # vehicle's front bumper. Keep that canonical reference;
                # geometry consumers derive a vehicle center when required.
                position = tuple(traci.vehicle.getPosition(vehicle_id))
                speed = float(traci.vehicle.getSpeed(vehicle_id))
                lane_id = traci.vehicle.getLaneID(vehicle_id)
                # Longitudinal lane position uses the same front-bumper
                # reference, measured along the current SUMO lane.
                lane_position = float(
                    traci.vehicle.getLanePosition(vehicle_id)
                )
                lane_length = (
                    float(traci.lane.getLength(lane_id))
                    if lane_id
                    else 0.0
                )
                states[vehicle_id] = {
                    # Canonical front-bumper state consumed by perception.
                    "position": position,
                    "speed": speed,
                    "heading_radians": math.radians(angle_degrees),
                    "length": float(traci.vehicle.getLength(vehicle_id)),
                    "width": float(traci.vehicle.getWidth(vehicle_id)),
                    # Temporary aliases retained for existing control/dashboard
                    # callers while they migrate to the canonical names.
                    "pos": position,
                    "vel": speed,
                    "accel": float(
                        traci.vehicle.getAcceleration(vehicle_id)
                    ),
                    # Runtime limits come from the active SUMO vehicle/type,
                    # not duplicated research constants.
                    "max_acceleration_mps2": float(
                        traci.vehicle.getAccel(vehicle_id)
                    ),
                    "comfortable_deceleration_mps2": float(
                        traci.vehicle.getDecel(vehicle_id)
                    ),
                    "emergency_deceleration_mps2": float(
                        traci.vehicle.getEmergencyDecel(vehicle_id)
                    ),
                    "max_speed_mps": float(
                        traci.vehicle.getMaxSpeed(vehicle_id)
                    ),
                    "angle_degrees": angle_degrees,
                    "lane_id": lane_id,
                    "lane_position": lane_position,
                    "lane_length": lane_length,
                    "road_id": traci.vehicle.getRoadID(vehicle_id),
                    # Evaluation-only truth. ObservationManager must not copy
                    # these fields into perception or operational LDM tracks.
                    "route_id": traci.vehicle.getRouteID(vehicle_id),
                    "route_index": int(traci.vehicle.getRouteIndex(vehicle_id)),
                    "type": traci.vehicle.getTypeID(vehicle_id),
                }
            except traci.TraCIException:
                # A vehicle can disappear between ID retrieval and state reads.
                continue
        return states

    def step(self):
        traci.simulationStep()
        self.step_count += 1
        self.current_time = float(traci.simulation.getTime())
        # Same-step authoritative lifecycle events are captured once directly
        # after simulationStep, before observations or downstream accounting.
        self.lifecycle_events = SimulationLifecycleEvents(
            self.current_time,
            tuple(traci.simulation.getDepartedIDList()),
            tuple(traci.simulation.getArrivedIDList()),
        )
        return self.get_vehicles()

    def close(self):
        try:
            traci.close()
        except traci.TraCIException:
            pass
        print(
            f"Simulation finished at {self.current_time:.2f} s "
            f"after {self.step_count} steps."
        )
