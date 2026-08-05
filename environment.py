"""SUMO/TraCI environment wrapper."""

import math
import shutil

import traci

from config import SIM_TIME_STEP, SUMO_CONFIG, SUMO_NETWORK_FILE


class SUMOEnv:
    def __init__(self, use_gui=False):
        self.use_gui = use_gui
        self.step_count = 0
        self.current_time = 0.0

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

        command = [
            sumo_binary,
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
        traci.start(command)
        self.current_time = float(traci.simulation.getTime())
        print("SUMO started successfully.")

    def get_vehicles(self):
        states = {}
        for vehicle_id in traci.vehicle.getIDList():
            try:
                angle_degrees = float(traci.vehicle.getAngle(vehicle_id))
                position = tuple(traci.vehicle.getPosition(vehicle_id))
                speed = float(traci.vehicle.getSpeed(vehicle_id))
                lane_id = traci.vehicle.getLaneID(vehicle_id)
                lane_position = float(
                    traci.vehicle.getLanePosition(vehicle_id)
                )
                lane_length = (
                    float(traci.lane.getLength(lane_id))
                    if lane_id
                    else 0.0
                )
                states[vehicle_id] = {
                    # Canonical current-state contract consumed by perception.
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
