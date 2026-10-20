"""Shadow-only map-aware conflict-zone temporal occupancy assessment.

Movement coordinate ``s=0`` is the end of the incoming lane. Front-bumper
progress is negative before the junction, projected onto the exact internal
movement centerline inside it, and continues as path length plus outgoing-lane
position. For zone interval [s_start, s_end] and vehicle length L:

    d_entry = max(0, s_start - s_vehicle)
    d_clear = max(0, s_end + L - s_vehicle)

Closed occupancy intervals overlap at boundary contact. No path-distance,
speed, temporal-safety threshold, or weighted score is used.
"""

# Import copy for use in this module.
import copy
# Import math for use in this module.
import math


# Evaluate spatial graph edges using ego-local state and static geometry.
# Instances expose the attributes and methods implemented in this class.
class ConflictZoneOccupancyAssessor:
    """Evaluate spatial graph edges using ego-local state and static geometry."""

    # Set NON_APPLICABLE to an immutable set built from a set containing the text
    # 'INCOMPATIBLE_WITH_OBSERVED_LANE', the text 'NO_APPLICABLE_ZONE'.
    NON_APPLICABLE = frozenset({
        "INCOMPATIBLE_WITH_OBSERVED_LANE", "NO_APPLICABLE_ZONE"
    })

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input path_manager: the supplied path manager.
    # Input zone_manager: the supplied zone manager.
    # Output: no explicit value; normal completion returns None.
    def __init__(self, path_manager, zone_manager):
        # Set self.path_manager to path_manager.
        self.path_manager = path_manager
        # Set self.zone_manager to zone_manager.
        self.zone_manager = zone_manager
        # Set self._results to an empty dictionary.
        self._results = {}
        # Set self._totals to the result of self._empty_totals().
        self._totals = self._empty_totals()
        # Set self._conflicting_pairs to an empty set.
        self._conflicting_pairs = set()

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Empty totals using the inputs and processing steps below.
    # Output: a dictionary containing spatial_edges_evaluated, candidate_path_zone_evaluations,
    # temporal_conflicts_observed,...
    def _empty_totals():
        # Return a dictionary containing spatial_edges_evaluated, candidate_path_zone_evaluations,
        # temporal_conflicts_observed,... to the caller.
        return {
            # Store 0 under 'spatial_edges_evaluated'.
            "spatial_edges_evaluated": 0,
            # Store 0 under 'candidate_path_zone_evaluations'.
            "candidate_path_zone_evaluations": 0,
            # Store 0 under 'temporal_conflicts_observed'.
            "temporal_conflicts_observed": 0,
            # Store 0 under 'spatial_only_temporal_separations'.
            "spatial_only_temporal_separations": 0,
            # Store 0 under 'currently_occupied_zone_evaluations'.
            "currently_occupied_zone_evaluations": 0,
            # Store 0 under 'cleared_zone_evaluations'.
            "cleared_zone_evaluations": 0,
            # Store 0 under 'unresolved_timing_evaluations'.
            "unresolved_timing_evaluations": 0,
            # Store 0 under 'unresolved_path_progress'.
            "unresolved_path_progress": 0,
            # Store 0 under 'unresolved_speed'.
            "unresolved_speed": 0,
            # Store 0 under 'unresolved_vehicle_state'.
            "unresolved_vehicle_state": 0,
            # Store 0 under 'incompatible_with_observed_lane'.
            "incompatible_with_observed_lane": 0,
            # Store 0 under 'no_applicable_zone'.
            "no_applicable_zone": 0,
            # Store 0 under 'unresolved_no_applicable_evaluation'.
            "unresolved_no_applicable_evaluation": 0,
            # Store 0 under 'candidate_paths_rejected_by_observed_lane'.
            "candidate_paths_rejected_by_observed_lane": 0,
            # Store 0 under 'nominal_timing_unavailable_due_to_zero_speed'.
            "nominal_timing_unavailable_due_to_zero_speed": 0,
            # Store 0 under 'earliest_reachability_calculations'.
            "earliest_reachability_calculations": 0,
            # Store 0 under 'stopped_vehicles_with_finite_earliest_arrival'.
            "stopped_vehicles_with_finite_earliest_arrival": 0,
            # Store 0 under 'vehicles_able_to_stop_before_zone'.
            "vehicles_able_to_stop_before_zone": 0,
            # Store 0 under 'vehicles_unable_to_stop_before_zone'.
            "vehicles_unable_to_stop_before_zone": 0,
            # Store 0 under 'physical_state_or_dynamics_unresolved'.
            "physical_state_or_dynamics_unresolved": 0,
            # Store 0 under 'non_conflicting_candidate_paths_excluded'.
            "non_conflicting_candidate_paths_excluded": 0,
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Compare two closed occupancy intervals; boundary contact counts as overlap and disjoint intervals yield a
    # separation.
    # Input first_entry: the supplied first entry.
    # Input first_clear: the supplied first clear.
    # Input second_entry: the supplied second entry.
    # Input second_clear: the supplied second clear.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def interval_relationship(first_entry, first_clear,
                              # Declare second_entry, second_clear as input parameters.
                              second_entry, second_clear):
        # Set overlap_start to the maximum of a floating-point number built from first_entry, a floating-point
        # number built from second_entry.
        overlap_start = max(float(first_entry), float(second_entry))
        # Set overlap_end to the minimum of a floating-point number built from first_clear, a floating-point
        # number built from second_clear.
        overlap_end = min(float(first_clear), float(second_clear))
        # Use an inclusive comparison because touching closed interval boundaries count as simultaneous occupancy.
        # Set overlaps to overlap_start is at most overlap_end.
        overlaps = overlap_start <= overlap_end
        # Run this branch when overlaps.
        if overlaps:
            # Return a tuple containing True, the maximum of 0.0, overlap_end minus overlap_start, 0.0 to the
            # caller.
            return True, max(0.0, overlap_end - overlap_start), 0.0
        # Return a tuple containing False, 0.0, the maximum of a floating-point number built from second_entry
        # minus a floating-point number... to the caller.
        return False, 0.0, max(
            # Supply a floating-point number built from second_entry minus a floating-point number built from
            # first_clear to max.
            float(second_entry) - float(first_clear),
            # Supply a floating-point number built from first_entry minus a floating-point number built from
            # second_clear to max.
            float(first_entry) - float(second_clear),
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Occupancy state using the inputs and processing steps below.
    # Input path_progress: the supplied path progress.
    # Input path_interval: the supplied path interval.
    # Input length: the supplied length.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def occupancy_state(path_progress, path_interval, length):
        # Set (start, end) to the result of map(float, path_interval).
        start, end = map(float, path_interval)
        # Set (progress, length) to a tuple containing a floating-point number built from path_progress, a
        # floating-point number built from length.
        progress, length = float(path_progress), float(length)
        # Run this branch when the negation of whether every item is true in a lazy sequence of whether value
        # contains finite numeric values for value in a tuple containing start, end, progress, length.
        if not all(math.isfinite(value) for value in (start, end, progress, length)):
            # Return a tuple containing None, the text 'UNRESOLVED_VEHICLE_STATE' to the caller.
            return None, "UNRESOLVED_VEHICLE_STATE"
        # Run this branch when length is at most 0.0 or end is less than start.
        if length <= 0.0 or end < start:
            # Return a tuple containing None, the text 'UNRESOLVED_VEHICLE_STATE' to the caller.
            return None, "UNRESOLVED_VEHICLE_STATE"
        # Run this branch when progress is less than start.
        if progress < start:
            # Return a tuple containing the text 'BEFORE_ZONE', None to the caller.
            return "BEFORE_ZONE", None
        # Run this branch when progress is less than end plus length.
        if progress < end + length:
            # Return a tuple containing the text 'CURRENTLY_OCCUPYING', None to the caller.
            return "CURRENTLY_OCCUPYING", None
        # Return a tuple containing the text 'CLEARED_ZONE', None to the caller.
        return "CLEARED_ZONE", None

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Timing from progress using the inputs and processing steps below.
    # Input progress: the supplied progress.
    # Input path_interval: the supplied path interval.
    # Input length: the supplied length.
    # Input speed: the supplied speed.
    # Input current_time: the supplied current time.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _timing_from_progress(progress, path_interval, length, speed,
                              # Declare current_time as input parameter.
                              current_time):
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set (progress, length, speed) to the result of map(float, a tuple containing progress, length,
            # speed).
            progress, length, speed = map(float, (progress, length, speed))
            # Set (start, end) to the result of map(float, path_interval).
            start, end = map(float, path_interval)
        # Handle (TypeError, ValueError) using the recovery steps below.
        except (TypeError, ValueError):
            # Return a tuple containing None, None, the text 'UNRESOLVED_VEHICLE_STATE' to the caller.
            return None, None, "UNRESOLVED_VEHICLE_STATE"
        # Set (state, state_error) to the result of ConflictZoneOccupancyAssessor.occupancy_state(progress, a
        # tuple containing start, end, length).
        state, state_error = ConflictZoneOccupancyAssessor.occupancy_state(
            # Supply a tuple containing start, end to ConflictZoneOccupancyAssessor.occupancy_state.
            progress, (start, end), length
        )
        # Run this branch when state_error.
        if state_error:
            # Return a tuple containing None, None, state_error to the caller.
            return None, None, state_error
        "First, the system calculates when the ego and target vehicles are expected to enter "
        "and fully clear the same conflict zone. These times form two occupancy intervals."
        " The code then compares the intervals using max(entry_times) and min(clear_times)."
        " If the calculated overlap start is earlier than or equal to the overlap end, "
        "both vehicles may occupy the conflict zone at the same time, "
        "so the result is TEMPORAL_CONFLICT. Otherwise, the paths still overlap spatially, "
        "but the vehicles are separated in time, so the result is SPATIAL_ONLY."
        # Clamp the remaining front-bumper distance to zero once the entry point has been reached.
        # Set distance_entry to the maximum of 0.0, start minus progress.
        distance_entry = max(0.0, start - progress)
        # Include vehicle length so the time interval ends only after the rear of the vehicle clears the zone.
        # Set distance_clear to the maximum of 0.0, end plus length minus progress.
        distance_clear = max(0.0, end + length - progress)
        # Set timing to a dictionary containing path_progress_m, distance_to_zone_entry_m,
        # distance_to_zone_clear_m, vehicle_length_m,...
        timing = {
            # Store progress under 'path_progress_m'.
            "path_progress_m": progress,
            # Store distance_entry under 'distance_to_zone_entry_m'.
            "distance_to_zone_entry_m": distance_entry,
            # Store distance_clear under 'distance_to_zone_clear_m'.
            "distance_to_zone_clear_m": distance_clear,
            # Store length under 'vehicle_length_m'.
            "vehicle_length_m": length,
            # Store speed under 'speed_mps'.
            "speed_mps": speed,
            # Store state under 'zone_occupancy_state'.
            "zone_occupancy_state": state,
        }
        # Run this branch when state equals the text 'CLEARED_ZONE'.
        if state == "CLEARED_ZONE":
            # Update timing with the supplied entries.
            timing.update({
                # Store 0.0 under 'time_to_entry_s'.
                # Store 0.0 under 'time_to_clear_s'.
                "time_to_entry_s": 0.0, "time_to_clear_s": 0.0,
                # Store a floating-point number built from current_time under 'predicted_entry_time_s'.
                "predicted_entry_time_s": float(current_time),
                # Store a floating-point number built from current_time under 'predicted_clear_time_s'.
                "predicted_clear_time_s": float(current_time),
            })
            # Return a tuple containing timing, state, None to the caller.
            return timing, state, None
        # Run this branch when the negation of whether speed contains finite numeric values or speed is at most
        # 0.0.
        if not math.isfinite(speed) or speed <= 0.0:
            # Run this branch when state equals the text 'CURRENTLY_OCCUPYING'.
            if state == "CURRENTLY_OCCUPYING":
                # Update timing with the supplied entries.
                timing.update({
                    # Store 0.0 under 'time_to_entry_s'.
                    "time_to_entry_s": 0.0,
                    # Store a floating-point number built from current_time under 'predicted_entry_time_s'.
                    "predicted_entry_time_s": float(current_time),
                })
            # Return a tuple containing timing, state, the text 'UNRESOLVED_SPEED' to the caller.
            return timing, state, "UNRESOLVED_SPEED"
        # Set time_entry to distance_entry divided by speed.
        time_entry = distance_entry / speed
        # Set time_clear to distance_clear divided by speed.
        time_clear = distance_clear / speed
        # Update timing with the supplied entries.
        timing.update({
            # Store time_entry under 'time_to_entry_s'.
            "time_to_entry_s": time_entry,
            # Store time_clear under 'time_to_clear_s'.
            "time_to_clear_s": time_clear,
            # Store a floating-point number built from current_time plus time_entry under
            # 'predicted_entry_time_s'.
            "predicted_entry_time_s": float(current_time) + time_entry,
            # Store a floating-point number built from current_time plus time_clear under
            # 'predicted_clear_time_s'.
            "predicted_clear_time_s": float(current_time) + time_clear,
        })
        # Return a tuple containing timing, state, None to the caller.
        return timing, state, None

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Earliest time under maximum acceleration and a maximum-speed cap.
    # Input distance: the supplied distance.
    # Input initial_speed: the supplied initial speed.
    # Input max_acceleration: the supplied max acceleration.
    # Input max_speed: the supplied max speed.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def earliest_reachable_time(distance, initial_speed, max_acceleration,
                                # Declare max_speed as input parameter.
                                max_speed):
        """Earliest time under maximum acceleration and a maximum-speed cap."""
        # Set distance to a floating-point number built from distance.
        distance = float(distance)
        # Set initial_speed to a floating-point number built from initial_speed.
        initial_speed = float(initial_speed)
        # Set max_acceleration to a floating-point number built from max_acceleration.
        max_acceleration = float(max_acceleration)
        # Set max_speed to a floating-point number built from max_speed.
        max_speed = float(max_speed)
        # Run this branch when the negation of whether every item is true in a lazy sequence of whether value
        # contains finite numeric values for value in a tuple containing distance, initial_speed,
        # max_acceleration, max_speed.
        if not all(math.isfinite(value) for value in (
                # Include max_acceleration in this tuple.
                distance, initial_speed, max_acceleration, max_speed)):
            # Raise ValueError with the text 'reachability inputs must be finite' to stop this execution path.
            raise ValueError("reachability inputs must be finite")
        # Run this branch when distance is less than 0.0 or initial_speed is less than 0.0.
        if distance < 0.0 or initial_speed < 0.0:
            # Raise ValueError with the text 'distance and initial speed must be non-negative' to stop this
            # execution path.
            raise ValueError("distance and initial speed must be non-negative")
        # Run this branch when distance equals 0.0.
        if distance == 0.0:
            # Return 0.0 to the caller.
            return 0.0
        # Run this branch when max_acceleration is at most 0.0 or max_speed is at most 0.0.
        if max_acceleration <= 0.0 or max_speed <= 0.0:
            # Raise ValueError with the text 'acceleration and maximum speed must be positive' to stop this
            # execution path.
            raise ValueError("acceleration and maximum speed must be positive")
        # Run this branch when initial_speed is at least max_speed.
        if initial_speed >= max_speed:
            # Return distance divided by initial_speed to the caller.
            return distance / initial_speed
        # Set acceleration_distance to max_speed raised to the power 2 minus initial_speed raised to the power 2
        # divided by 2.0 multiplied by max_acceleration.
        acceleration_distance = (
            # Evaluate max_speed raised to the power 2 minus initial_speed raised to the power 2 divided by 2.0
            # multiplied by max_acceleration as part of the enclosing expression.
            (max_speed ** 2 - initial_speed ** 2)
            # Evaluate 2.0 multiplied by max_acceleration as part of the enclosing expression.
            / (2.0 * max_acceleration)
        )
        # Run this branch when distance is at most acceleration_distance.
        if distance <= acceleration_distance:
            # Return the negative of initial_speed plus the square root of initial_speed ** 2 plus 2.0 *
            # max_acceleration * distance divided by max_acceleration to the caller.
            return (
                # Evaluate the negative of initial_speed plus the square root of initial_speed raised to the power
                # 2 plus 2.0 * max_acceleration multiplied by distance as part of the enclosing expression.
                -initial_speed + math.sqrt(
                    # Supply initial_speed raised to the power 2 plus 2.0 multiplied by max_acceleration
                    # multiplied by distance to math.sqrt.
                    initial_speed ** 2
                    # Evaluate 2.0 multiplied by max_acceleration multiplied by distance as part of the enclosing
                    # expression.
                    + 2.0 * max_acceleration * distance
                )
            # Evaluate max_acceleration as part of the enclosing expression.
            ) / max_acceleration
        # Set acceleration_time to max_speed minus initial_speed divided by max_acceleration.
        acceleration_time = (
            # Evaluate max_speed minus initial_speed divided by max_acceleration as part of the enclosing
            # expression.
            (max_speed - initial_speed) / max_acceleration
        )
        # Return acceleration_time plus distance minus acceleration_distance divided by max_speed to the caller.
        return (
            # Evaluate acceleration_time plus distance minus acceleration_distance divided by max_speed as part of
            # the enclosing expression.
            acceleration_time
            # Evaluate distance minus acceleration_distance divided by max_speed as part of the enclosing
            # expression.
            + (distance - acceleration_distance) / max_speed
        )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Stopping distance using the inputs and processing steps below.
    # Input speed: the supplied speed.
    # Input comfortable_deceleration: the supplied comfortable deceleration.
    # Output: speed raised to the power 2 divided by 2.0 multiplied by deceleration.
    # Processing: select branches using the stated conditions.
    def stopping_distance(speed, comfortable_deceleration):
        # Set speed to a floating-point number built from speed.
        speed = float(speed)
        # Set deceleration to a floating-point number built from comfortable_deceleration.
        deceleration = float(comfortable_deceleration)
        # Run this branch when the negation of whether speed contains finite numeric values or speed is less than
        # 0.0.
        if not math.isfinite(speed) or speed < 0.0:
            # Raise ValueError with the text 'speed must be finite and non-negative' to stop this execution path.
            raise ValueError("speed must be finite and non-negative")
        # Run this branch when the negation of whether deceleration contains finite numeric values or deceleration
        # is at most 0.0.
        if not math.isfinite(deceleration) or deceleration <= 0.0:
            # Raise ValueError with the text 'comfortable deceleration must be positive' to stop this execution
            # path.
            raise ValueError("comfortable deceleration must be positive")
        # Return speed raised to the power 2 divided by 2.0 multiplied by deceleration to the caller.
        return speed ** 2 / (2.0 * deceleration)

    # Add reachability fields using the inputs and processing steps below.
    # Input record: the supplied record.
    # Input prefix: the supplied prefix.
    # Input track: the supplied track.
    # Input timing: the supplied timing.
    # Input current_time: the supplied current time.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def _add_reachability_fields(self, record, prefix, track, timing,
                                 # Declare current_time as input parameter.
                                 current_time):
        # Set dynamics to a dictionary containing max_acceleration_mps2, comfortable_deceleration_mps2,
        # emergency_deceleration_mps2,...
        dynamics = {
            # Store 'max_acceleration_mps2' from track; use None if absent under 'max_acceleration_mps2'.
            "max_acceleration_mps2": track.get("max_acceleration_mps2"),
            # Store 'comfortable_deceleration_mps2' from track; use None if absent under
            # 'comfortable_deceleration_mps2'.
            "comfortable_deceleration_mps2": track.get(
                "comfortable_deceleration_mps2"
            ),
            # Store 'emergency_deceleration_mps2' from track; use None if absent under
            # 'emergency_deceleration_mps2'.
            "emergency_deceleration_mps2": track.get(
                "emergency_deceleration_mps2"
            ),
            # Store 'max_speed_mps' from track; use None if absent under 'max_speed_mps'.
            "max_speed_mps": track.get("max_speed_mps"),
        }
        # Iterate over key/value pairs from dynamics, binding each item to (name, value).
        for name, value in dynamics.items():
            # Set record[f'{prefix}_{name}'] to value.
            record[f"{prefix}_{name}"] = value
        # Run this branch when timing is the same object as None.
        if timing is None:
            # Set record[f'{prefix}_reachability_status'] to the text 'UNRESOLVED_DYNAMICS'.
            record[f"{prefix}_reachability_status"] = "UNRESOLVED_DYNAMICS"
            # Return the text 'UNRESOLVED_DYNAMICS' to the caller.
            return "UNRESOLVED_DYNAMICS"
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set speed to a floating-point number built from 'speed' from track; use None if absent.
            speed = float(track.get("speed"))
            # Set acceleration to a floating-point number built from dynamics at 'max_acceleration_mps2'.
            acceleration = float(dynamics["max_acceleration_mps2"])
            # Set deceleration to a floating-point number built from dynamics at 'comfortable_deceleration_mps2'.
            deceleration = float(dynamics["comfortable_deceleration_mps2"])
            # Set max_speed to a floating-point number built from dynamics at 'max_speed_mps'.
            max_speed = float(dynamics["max_speed_mps"])
            # Set earliest_entry to the result of self.earliest_reachable_time(timing at
            # 'distance_to_zone_entry_m', speed, acceleration, max_speed).
            earliest_entry = self.earliest_reachable_time(
                # Supply timing at 'distance_to_zone_entry_m' to self.earliest_reachable_time.
                timing["distance_to_zone_entry_m"], speed,
                # Supply acceleration to self.earliest_reachable_time.
                acceleration, max_speed,
            )
            # Set earliest_clear to the result of self.earliest_reachable_time(timing at
            # 'distance_to_zone_clear_m', speed, acceleration, max_speed).
            earliest_clear = self.earliest_reachable_time(
                # Supply timing at 'distance_to_zone_clear_m' to self.earliest_reachable_time.
                timing["distance_to_zone_clear_m"], speed,
                # Supply acceleration to self.earliest_reachable_time.
                acceleration, max_speed,
            )
            # Set stop_distance to the result of self.stopping_distance(speed, deceleration).
            stop_distance = self.stopping_distance(speed, deceleration)
        # Handle (TypeError, ValueError) using the recovery steps below.
        except (TypeError, ValueError):
            # Set record[f'{prefix}_reachability_status'] to the text 'UNRESOLVED_DYNAMICS'.
            record[f"{prefix}_reachability_status"] = "UNRESOLVED_DYNAMICS"
            # Return the text 'UNRESOLVED_DYNAMICS' to the caller.
            return "UNRESOLVED_DYNAMICS"
        # Set can_stop to stop_distance is at most timing at 'distance_to_zone_entry_m'.
        can_stop = stop_distance <= timing["distance_to_zone_entry_m"]
        # Set state to timing at 'zone_occupancy_state'.
        state = timing["zone_occupancy_state"]
        # Set upper_status to the text 'CLEARED_ZONE' when state equals the text 'CLEARED_ZONE', otherwise the
        # text 'CURRENTLY_OCCUPYING' when state equals the text 'CURRENTLY_OCCUPYING', otherwise the text
        # 'UNBOUNDED_CAN_STOP' when can_stop, otherwise the text 'CAN_NOT_STOP_BEFORE_ZONE'.
        upper_status = (
            # Evaluate the text 'CLEARED_ZONE' when state equals the text 'CLEARED_ZONE', otherwise the text
            # 'CURRENTLY_OCCUPYING' when state equals the text 'CURRENTLY_OCCUPYING', otherwise the text
            # 'UNBOUNDED_CAN_STOP' when can_stop, otherwise the text 'CAN_NOT_STOP_BEFORE_ZONE' as part of the
            # enclosing expression.
            "CLEARED_ZONE" if state == "CLEARED_ZONE"
            # Evaluate the text 'CURRENTLY_OCCUPYING' when state equals the text 'CURRENTLY_OCCUPYING', otherwise
            # the text 'UNBOUNDED_CAN_STOP' when can_stop, otherwise the text 'CAN_NOT_STOP_BEFORE_ZONE' as part
            # of the enclosing expression.
            else "CURRENTLY_OCCUPYING" if state == "CURRENTLY_OCCUPYING"
            # Evaluate the text 'UNBOUNDED_CAN_STOP' when can_stop, otherwise the text 'CAN_NOT_STOP_BEFORE_ZONE'
            # as part of the enclosing expression.
            else "UNBOUNDED_CAN_STOP" if can_stop
            # Supply the text 'CAN_NOT_STOP_BEFORE_ZONE' to the enclosing expression.
            else "CAN_NOT_STOP_BEFORE_ZONE"
        )
        # Update record with the supplied entries.
        record.update({
            # Store earliest_entry under f'{prefix}_earliest_reachable_entry_time_s'.
            f"{prefix}_earliest_reachable_entry_time_s": earliest_entry,
            # Store earliest_clear under f'{prefix}_earliest_reachable_clear_time_s'.
            f"{prefix}_earliest_reachable_clear_time_s": earliest_clear,
            # Store a floating-point number built from current_time plus earliest_entry under
            # f'{prefix}_earliest_predicted_entry_time_s'.
            f"{prefix}_earliest_predicted_entry_time_s": (
                # Evaluate a floating-point number built from current_time plus earliest_entry as part of the
                # enclosing expression.
                float(current_time) + earliest_entry
            ),
            # Store a floating-point number built from current_time plus earliest_clear under
            # f'{prefix}_earliest_predicted_clear_time_s'.
            f"{prefix}_earliest_predicted_clear_time_s": (
                # Evaluate a floating-point number built from current_time plus earliest_clear as part of the
                # enclosing expression.
                float(current_time) + earliest_clear
            ),
            # Store stop_distance under f'{prefix}_stopping_distance_m'.
            f"{prefix}_stopping_distance_m": stop_distance,
            # Store can_stop under f'{prefix}_can_stop_before_zone'.
            f"{prefix}_can_stop_before_zone": can_stop,
            # Store upper_status under f'{prefix}_entry_time_upper_bound_status'.
            f"{prefix}_entry_time_upper_bound_status": upper_status,
            # Store the text 'RESOLVED' under f'{prefix}_reachability_status'.
            f"{prefix}_reachability_status": "RESOLVED",
        })
        # Return the text 'RESOLVED' to the caller.
        return "RESOLVED"

    # Compatibility helper retained for focused tests of the original
    # pre-junction formulation. General assessment uses path progress above.
    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Incoming distance using the inputs and processing steps below.
    # Input track: the supplied track.
    # Input expected_lane_id: the supplied expected lane id.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _incoming_distance(track, expected_lane_id):
        # Run this branch when 'lane_id' from track; use None if absent differs from expected_lane_id.
        if track.get("lane_id") != expected_lane_id:
            # Return a tuple containing None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
            return None, "UNRESOLVED_PATH_PROGRESS"
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set (position, length) to a tuple containing a floating-point number built from track at
            # 'lane_position', a floating-point number built from track at...
            position, length = float(track["lane_position"]), float(track["lane_length"])
        # Handle (KeyError, TypeError, ValueError) using the recovery steps below.
        except (KeyError, TypeError, ValueError):
            # Return a tuple containing None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
            return None, "UNRESOLVED_PATH_PROGRESS"
        # Run this branch when the negation of whether position contains finite numeric values or the negation of
        # whether length contains finite numeric values.
        if not math.isfinite(position) or not math.isfinite(length):
            # Return a tuple containing None, the text 'UNRESOLVED_PATH_PROGRESS' to the caller.
            return None, "UNRESOLVED_PATH_PROGRESS"
        # Return a tuple containing the maximum of 0.0, length minus position, None to the caller.
        return max(0.0, length - position), None

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Kinematics using the inputs and processing steps below.
    # Input incoming_distance: the supplied incoming distance.
    # Input path_interval: the supplied path interval.
    # Input length: the supplied length.
    # Input speed: the supplied speed.
    # Input current_time: the supplied current time.
    # Output: a tuple containing timing, error.
    def _kinematics(incoming_distance, path_interval, length, speed, current_time):
        # Set (timing, _, error) to the result of ConflictZoneOccupancyAssessor._timing_from_progress(the negative
        # of a floating-point number built from incoming_distance, path_interval, length,...).
        timing, _, error = ConflictZoneOccupancyAssessor._timing_from_progress(
            # Supply the negative of a floating-point number built from incoming_distance to
            # ConflictZoneOccupancyAssessor._timing_from_progress.
            -float(incoming_distance), path_interval, length, speed, current_time
        )
        # Return a tuple containing timing, error to the caller.
        return timing, error

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Candidate path ids using the inputs and processing steps below.
    # Input edge: the supplied edge.
    # Output: yield the values produced by the yield statements below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _candidate_path_ids(edge):
        # Set candidates to 'spatially_conflicting_candidate_paths' from edge; use None if absent.
        candidates = edge.get("spatially_conflicting_candidate_paths")
        # Run this branch when candidates is the same object as None.
        if candidates is None:
            # Set candidates to 'target_candidate_paths' from edge; use an empty dictionary if absent.
            candidates = edge.get("target_candidate_paths", {})
        # Iterate over key/value pairs from candidates, binding each item to (manoeuvre, value).
        for manoeuvre, value in candidates.items():
            # Iterate over value when whether value has type a tuple containing tuple, list, otherwise a tuple
            # containing value, binding each item to path_id.
            for path_id in value if isinstance(value, (tuple, list)) else (value,):
                # Yield a tuple containing manoeuvre, path_id to the iterator consumer.
                yield manoeuvre, path_id

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Add timing fields using the inputs and processing steps below.
    # Input record: the supplied record.
    # Input prefix: the supplied prefix.
    # Input timing: the supplied timing.
    # Input source: the supplied source.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records.
    def _add_timing_fields(record, prefix, timing, source):
        # Set timing to timing or an empty dictionary.
        timing = timing or {}
        # Set record[f'{prefix}_path_progress_source'] to source.
        record[f"{prefix}_path_progress_source"] = source
        # Iterate over a tuple containing the text 'path_progress_m', the text 'zone_occupancy_state', the text
        # 'vehicle_length_m', the text..., binding each item to field.
        for field in (
            "path_progress_m", "zone_occupancy_state", "vehicle_length_m",
            "distance_to_zone_entry_m", "distance_to_zone_clear_m", "speed_mps",
            "time_to_entry_s", "time_to_clear_s", "predicted_entry_time_s",
            "predicted_clear_time_s",
        ):
            # Set record[f'{prefix}_{field}'] to field from timing; use None if absent.
            record[f"{prefix}_{field}"] = timing.get(field)
        # Set record[f'{prefix}_nominal_constant_speed_time_to_entry_s'] to 'time_to_entry_s' from timing; use
        # None if absent.
        record[f"{prefix}_nominal_constant_speed_time_to_entry_s"] = timing.get(
            "time_to_entry_s"
        )
        # Set record[f'{prefix}_nominal_constant_speed_time_to_clear_s'] to 'time_to_clear_s' from timing; use
        # None if absent.
        record[f"{prefix}_nominal_constant_speed_time_to_clear_s"] = timing.get(
            "time_to_clear_s"
        )
        # Set record[f'{prefix}_nominal_constant_speed_entry_time_s'] to 'predicted_entry_time_s' from timing; use
        # None if absent.
        record[f"{prefix}_nominal_constant_speed_entry_time_s"] = timing.get(
            "predicted_entry_time_s"
        )
        # Set record[f'{prefix}_nominal_constant_speed_clear_time_s'] to 'predicted_clear_time_s' from timing; use
        # None if absent.
        record[f"{prefix}_nominal_constant_speed_clear_time_s"] = timing.get(
            "predicted_clear_time_s"
        )

    # Base record using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input edge: the supplied edge.
    # Input target_id: the supplied target id.
    # Input manoeuvre: the supplied manoeuvre.
    # Input target_path_id: the supplied target path id.
    # Input current_time: the supplied current time.
    # Output: a dictionary containing ego_id, target_id, timestamp, ego_path_id, target_path_id,
    # target_manoeuvre,...
    def _base_record(self, ldm, edge, target_id, manoeuvre, target_path_id,
                     # Declare current_time as input parameter.
                     current_time):
        # Return a dictionary containing ego_id, target_id, timestamp, ego_path_id, target_path_id,
        # target_manoeuvre,... to the caller.
        return {
            # Store ldm.ego_id under 'ego_id'.
            # Store target_id under 'target_id'.
            "ego_id": ldm.ego_id, "target_id": target_id,
            # Store a floating-point number built from current_time under 'timestamp'.
            "timestamp": float(current_time),
            # Store edge at 'ego_path_id' under 'ego_path_id'.
            "ego_path_id": edge["ego_path_id"],
            # Store target_path_id under 'target_path_id'.
            "target_path_id": target_path_id,
            # Store manoeuvre under 'target_manoeuvre'.
            "target_manoeuvre": manoeuvre,
            # Store 'prediction_status' from edge; use None if absent under 'target_prediction_status'.
            "target_prediction_status": edge.get("prediction_status"),
            # Store 'observation_age_seconds' from edge; use None if absent under
            # 'target_observation_age_seconds'.
            "target_observation_age_seconds": edge.get("observation_age_seconds"),
            # Store 'lane_id' from ldm.tracks[ldm.ego_id]; use None if absent under 'ego_current_lane_id'.
            "ego_current_lane_id": ldm.tracks[ldm.ego_id].get("lane_id"),
            # Store 'lane_id' from ldm.tracks[target_id]; use None if absent under 'target_current_lane_id'.
            "target_current_lane_id": ldm.tracks[target_id].get("lane_id"),
        }

    # Evaluate path using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input edge: the supplied edge.
    # Input target_id: the supplied target id.
    # Input manoeuvre: the supplied manoeuvre.
    # Input target_path_id: the supplied target path id.
    # Input current_time: the supplied current time.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _evaluate_path(self, ldm, edge, target_id, manoeuvre, target_path_id,
                       # Declare current_time as input parameter.
                       current_time):
        # Set (ego, target) to a tuple containing ldm.tracks at ldm.ego_id, ldm.tracks at target_id.
        ego, target = ldm.tracks[ldm.ego_id], ldm.tracks[target_id]
        # Set ego_path_id to edge at 'ego_path_id'.
        ego_path_id = edge["ego_path_id"]
        # Set record to the result of self._base_record(ldm, edge, target_id, manoeuvre, target_path_id,
        # current_time).
        record = self._base_record(
            # Supply target_path_id to self._base_record.
            ldm, edge, target_id, manoeuvre, target_path_id, current_time
        )
        # Set (ego_progress, ego_source, ego_error) to the result of
        # self.path_manager.resolve_front_bumper_path_progress(ego, self.path_manager.paths at ego_path_id).
        ego_progress, ego_source, ego_error = (
            # Evaluate the result of self.path_manager.resolve_front_bumper_path_progress(ego,
            # self.path_manager.paths at ego_path_id) as part of the enclosing expression.
            self.path_manager.resolve_front_bumper_path_progress(
                # Supply self.path_manager.paths at ego_path_id to
                # self.path_manager.resolve_front_bumper_path_progress.
                ego, self.path_manager.paths[ego_path_id]
            )
        )
        # Set (target_progress, target_source, target_error) to the result of
        # self.path_manager.resolve_front_bumper_path_progress(target, self.path_manager.paths at target_path_id).
        target_progress, target_source, target_error = (
            # Evaluate the result of self.path_manager.resolve_front_bumper_path_progress(target,
            # self.path_manager.paths at target_path_id) as part of the enclosing expression.
            self.path_manager.resolve_front_bumper_path_progress(
                # Supply self.path_manager.paths at target_path_id to
                # self.path_manager.resolve_front_bumper_path_progress.
                target, self.path_manager.paths[target_path_id]
            )
        )
        # Update record with the supplied entries.
        record.update({
            # Store ego_progress under 'ego_path_progress_m'.
            "ego_path_progress_m": ego_progress,
            # Store target_progress under 'target_path_progress_m'.
            "target_path_progress_m": target_progress,
            # Store ego_source under 'ego_path_progress_source'.
            "ego_path_progress_source": ego_source,
            # Store target_source under 'target_path_progress_source'.
            "target_path_progress_source": target_source,
        })
        # Run this branch when ego_error or target_error.
        if ego_error or target_error:
            # Update record with the supplied entries.
            record.update({
                # Store None under 'temporal_overlap'.
                # Store None under 'overlap_duration_s'.
                "temporal_overlap": None, "overlap_duration_s": None,
                # Store None under 'temporal_separation_s'.
                "temporal_separation_s": None,
                # Store ego_error or target_error under 'status'.
                "status": ego_error or target_error,
            })
            # Return record to the caller.
            return record
        # Set zone to the result of self.zone_manager.zone_record(ego_path_id, 'width' from ego; use None if
        # absent, target_path_id, 'width' from target; use None...).
        zone = self.zone_manager.zone_record(
            # Supply 'width' from target; use None if absent to self.zone_manager.zone_record.
            ego_path_id, ego.get("width"), target_path_id, target.get("width")
        )
        # Run this branch when zone is the same object as None.
        if zone is None:
            # Set record['status'] to the text 'NO_APPLICABLE_ZONE'.
            record["status"] = "NO_APPLICABLE_ZONE"
            # Return record to the caller.
            return record
        # Update record with the supplied entries.
        record.update({
            # Store zone at 'zone_id' under 'conflict_zone_id'.
            "conflict_zone_id": zone["zone_id"],
            # Store zone at 'conflict_type' under 'conflict_type'.
            "conflict_type": zone["conflict_type"],
            # Store zone at 'first_path_distance_interval' under 'ego_zone_path_interval_m'.
            "ego_zone_path_interval_m": zone["first_path_distance_interval"],
            # Store zone at 'second_path_distance_interval' under 'target_zone_path_interval_m'.
            "target_zone_path_interval_m": zone["second_path_distance_interval"],
        })
        # Set (ego_timing, ego_state, ego_timing_error) to the result of self._timing_from_progress(ego_progress,
        # zone at 'first_path_distance_interval', 'length' from ego; use None if absent,...).
        ego_timing, ego_state, ego_timing_error = self._timing_from_progress(
            # Supply zone at 'first_path_distance_interval' to self._timing_from_progress.
            ego_progress, zone["first_path_distance_interval"],
            # Supply 'length' from ego; use None if absent to self._timing_from_progress.
            ego.get("length"), ego.get("speed"), current_time,
        )
        # Set (target_timing, target_state, target_timing_error) to the result of
        # self._timing_from_progress(target_progress, zone at 'second_path_distance_interval', 'length' from
        # target; use None if...).
        target_timing, target_state, target_timing_error = self._timing_from_progress(
            # Supply zone at 'second_path_distance_interval' to self._timing_from_progress.
            target_progress, zone["second_path_distance_interval"],
            # Supply 'length' from target; use None if absent to self._timing_from_progress.
            target.get("length"), target.get("speed"), current_time,
        )
        # Call self._add_timing_fields with the supplied arguments.
        self._add_timing_fields(record, "ego", ego_timing, ego_source)
        # Call self._add_timing_fields with the supplied arguments.
        self._add_timing_fields(record, "target", target_timing, target_source)
        # Set ego_reachability to the result of self._add_reachability_fields(record, the text 'ego', ego,
        # ego_timing, current_time).
        ego_reachability = self._add_reachability_fields(
            # Supply current_time to self._add_reachability_fields.
            record, "ego", ego, ego_timing, current_time
        )
        # Set target_reachability to the result of self._add_reachability_fields(record, the text 'target',
        # target, target_timing, current_time).
        target_reachability = self._add_reachability_fields(
            # Supply target_timing to self._add_reachability_fields.
            record, "target", target, target_timing, current_time
        )
        # Run this branch when the text 'CURRENTLY_OCCUPYING' belongs to a set containing ego_state, target_state.
        if "CURRENTLY_OCCUPYING" in {ego_state, target_state}:
            # Set reachability_interpretation to the text 'CURRENTLY_OCCUPYING'.
            reachability_interpretation = "CURRENTLY_OCCUPYING"
        # Run this branch when the text 'UNRESOLVED_DYNAMICS' belongs to a set containing ego_reachability,
        # target_reachability.
        elif "UNRESOLVED_DYNAMICS" in {
                # Include target_reachability in this set.
                ego_reachability, target_reachability}:
            # Set reachability_interpretation to the text 'UNRESOLVED_PHYSICAL_DYNAMICS'.
            reachability_interpretation = "UNRESOLVED_PHYSICAL_DYNAMICS"
        # Run this branch when 'ego_can_stop_before_zone' from record; use None if absent or
        # 'target_can_stop_before_zone' from record; use None if absent.
        elif (record.get("ego_can_stop_before_zone")
              # Evaluate 'target_can_stop_before_zone' from record; use None if absent as part of the enclosing
              # expression.
              or record.get("target_can_stop_before_zone")):
            # Set reachability_interpretation to the text 'UNCOMMITTED_CAN_STOP'.
            reachability_interpretation = "UNCOMMITTED_CAN_STOP"
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Set reachability_interpretation to the text 'POTENTIAL_CONFLICT_REACHABLE'.
            reachability_interpretation = "POTENTIAL_CONFLICT_REACHABLE"
        # Set record['reachability_interpretation'] to reachability_interpretation.
        record["reachability_interpretation"] = reachability_interpretation

        # Run this branch when the text 'CLEARED_ZONE' belongs to a set containing ego_state, target_state.
        if "CLEARED_ZONE" in {ego_state, target_state}:
            # Update record with the supplied entries.
            record.update({
                # Store False under 'temporal_overlap'.
                # Store 0.0 under 'overlap_duration_s'.
                "temporal_overlap": False, "overlap_duration_s": 0.0,
                # Store None under 'temporal_separation_s'.
                # Store the text 'CLEARED_ZONE' under 'status'.
                "temporal_separation_s": None, "status": "CLEARED_ZONE",
            })
            # Return record to the caller.
            return record
        # Run this branch when ego_state equals target_state; equals the text 'CURRENTLY_OCCUPYING'.
        if ego_state == target_state == "CURRENTLY_OCCUPYING":
            # Set clear_times to a list of 'predicted_clear_time_s' from item; use None if absent for item in a
            # tuple containing ego_timing or an empty dictionary, target_timing or an empty dictionary.
            clear_times = [
                # Evaluate 'predicted_clear_time_s' from item; use None if absent as part of the enclosing
                # expression.
                item.get("predicted_clear_time_s") for item in
                # Evaluate a tuple containing ego_timing or an empty dictionary, target_timing or an empty
                # dictionary as part of the enclosing expression.
                (ego_timing or {}, target_timing or {})
            ]
            # Set duration to the minimum of clear_times minus a floating-point number built from current_time
            # when whether every item is true in a lazy sequence of value is a different object from None for
            # value in clear_times, otherwise None.
            duration = (
                # Evaluate the minimum of clear_times minus a floating-point number built from current_time when
                # whether every item is true in a lazy sequence of value is a different object from None for value
                # in clear_times, otherwise None as part of the enclosing expression.
                min(clear_times) - float(current_time)
                # Evaluate whether every item is true in a lazy sequence of value is a different object from None
                # for value in clear_times as part of the enclosing expression.
                if all(value is not None for value in clear_times) else None
            )
            # Update record with the supplied entries.
            record.update({
                # Store True under 'temporal_overlap'.
                # Store duration under 'overlap_duration_s'.
                "temporal_overlap": True, "overlap_duration_s": duration,
                # Store 0.0 under 'temporal_separation_s'.
                # Store the text 'TEMPORAL_CONFLICT' under 'status'.
                "temporal_separation_s": 0.0, "status": "TEMPORAL_CONFLICT",
            })
            # Return record to the caller.
            return record
        # Run this branch when ego_timing_error or target_timing_error.
        if ego_timing_error or target_timing_error:
            # Update record with the supplied entries.
            record.update({
                # Store None under 'temporal_overlap'.
                # Store None under 'overlap_duration_s'.
                "temporal_overlap": None, "overlap_duration_s": None,
                # Store None under 'temporal_separation_s'.
                "temporal_separation_s": None,
                # Store ego_timing_error or target_timing_error under 'status'.
                "status": ego_timing_error or target_timing_error,
            })
            # Return record to the caller.
            return record
        # Set (overlap, duration, separation) to the result of self.interval_relationship(ego_timing at
        # 'predicted_entry_time_s', ego_timing at 'predicted_clear_time_s', target_timing at...).
        overlap, duration, separation = self.interval_relationship(
            # Supply ego_timing at 'predicted_entry_time_s' to self.interval_relationship.
            ego_timing["predicted_entry_time_s"],
            # Supply ego_timing at 'predicted_clear_time_s' to self.interval_relationship.
            ego_timing["predicted_clear_time_s"],
            # Supply target_timing at 'predicted_entry_time_s' to self.interval_relationship.
            target_timing["predicted_entry_time_s"],
            # Supply target_timing at 'predicted_clear_time_s' to self.interval_relationship.
            target_timing["predicted_clear_time_s"],
        )
        # Update record with the supplied entries.
        record.update({
            # Store overlap under 'temporal_overlap'.
            # Store duration under 'overlap_duration_s'.
            "temporal_overlap": overlap, "overlap_duration_s": duration,
            # Store separation under 'temporal_separation_s'.
            "temporal_separation_s": separation,
            # Store the text 'TEMPORAL_CONFLICT' when overlap, otherwise the text 'SPATIAL_ONLY' under 'status'.
            "status": "TEMPORAL_CONFLICT" if overlap else "SPATIAL_ONLY",
        })
        # Return record to the caller.
        return record

    # Count record using the inputs and processing steps below.
    # Input record: the supplied record.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _count_record(self, record):
        # Set status to record at 'status'.
        status = record["status"]
        # Run this branch when status equals the text 'INCOMPATIBLE_WITH_OBSERVED_LANE'.
        if status == "INCOMPATIBLE_WITH_OBSERVED_LANE":
            # Update self._totals['incompatible_with_observed_lane'] to its current value plus 1.
            self._totals["incompatible_with_observed_lane"] += 1
            # Update self._totals['candidate_paths_rejected_by_observed_lane'] to its current value plus 1.
            self._totals["candidate_paths_rejected_by_observed_lane"] += 1
            # Return no value to the caller.
            return
        # Run this branch when status equals the text 'NO_APPLICABLE_ZONE'.
        if status == "NO_APPLICABLE_ZONE":
            # Update self._totals['no_applicable_zone'] to its current value plus 1.
            self._totals["no_applicable_zone"] += 1
            # Return no value to the caller.
            return
        # Update self._totals['candidate_path_zone_evaluations'] to its current value plus 1.
        self._totals["candidate_path_zone_evaluations"] += 1
        # Set states to a set containing 'ego_zone_occupancy_state' from record; use None if absent,
        # 'target_zone_occupancy_state' from record; use...
        states = {
            # Include 'ego_zone_occupancy_state' from record; use None if absent in this set.
            record.get("ego_zone_occupancy_state"),
            # Include 'target_zone_occupancy_state' from record; use None if absent in this set.
            record.get("target_zone_occupancy_state"),
        }
        # Run this branch when the text 'CURRENTLY_OCCUPYING' belongs to states.
        if "CURRENTLY_OCCUPYING" in states:
            # Update self._totals['currently_occupied_zone_evaluations'] to its current value plus 1.
            self._totals["currently_occupied_zone_evaluations"] += 1
        # Run this branch when the text 'CLEARED_ZONE' belongs to states.
        if "CLEARED_ZONE" in states:
            # Update self._totals['cleared_zone_evaluations'] to its current value plus 1.
            self._totals["cleared_zone_evaluations"] += 1
        # Iterate over a tuple containing the text 'ego', the text 'target', binding each item to prefix.
        for prefix in ("ego", "target"):
            # Run this branch when f'{prefix}_reachability_status' from record; use None if absent equals the text
            # 'RESOLVED'.
            if record.get(f"{prefix}_reachability_status") == "RESOLVED":
                # Update self._totals['earliest_reachability_calculations'] to its current value plus 1.
                self._totals["earliest_reachability_calculations"] += 1
                # Run this branch when f'{prefix}_speed_mps' from record; use None if absent equals 0.0 and
                # f'{prefix}_earliest_reachable_entry_time_s' from record; use None if absent is a different
                # object from None.
                if (record.get(f"{prefix}_speed_mps") == 0.0
                        # Evaluate f'{prefix}_earliest_reachable_entry_time_s' from record; use None if absent is
                        # a different object from None as part of the enclosing expression.
                        and record.get(
                            # Supply formatted text built from the embedded values to record.get.
                            f"{prefix}_earliest_reachable_entry_time_s"
                        # Supply None to the enclosing expression.
                        ) is not None):
                    # Update self._totals['stopped_vehicles_with_finite_earliest_arrival'] to its current value
                    # plus 1.
                    self._totals[
                        "stopped_vehicles_with_finite_earliest_arrival"
                    # Supply 1 to the enclosing expression.
                    ] += 1
                # Run this branch when f'{prefix}_can_stop_before_zone' from record; use None if absent.
                if record.get(f"{prefix}_can_stop_before_zone"):
                    # Update self._totals['vehicles_able_to_stop_before_zone'] to its current value plus 1.
                    self._totals["vehicles_able_to_stop_before_zone"] += 1
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Update self._totals['vehicles_unable_to_stop_before_zone'] to its current value plus 1.
                    self._totals["vehicles_unable_to_stop_before_zone"] += 1
        # Run this branch when 'reachability_interpretation' from record; use None if absent equals the text
        # 'UNRESOLVED_PHYSICAL_DYNAMICS'.
        if record.get("reachability_interpretation") == (
                "UNRESOLVED_PHYSICAL_DYNAMICS"):
            # Update self._totals['physical_state_or_dynamics_unresolved'] to its current value plus 1.
            self._totals["physical_state_or_dynamics_unresolved"] += 1
        # Run this branch when status equals the text 'TEMPORAL_CONFLICT'.
        if status == "TEMPORAL_CONFLICT":
            # Update self._totals['temporal_conflicts_observed'] to its current value plus 1.
            self._totals["temporal_conflicts_observed"] += 1
        # Run this branch when status belongs to a set containing the text 'SPATIAL_ONLY', the text
        # 'CLEARED_ZONE'.
        elif status in {"SPATIAL_ONLY", "CLEARED_ZONE"}:
            # Update self._totals['spatial_only_temporal_separations'] to its current value plus 1.
            self._totals["spatial_only_temporal_separations"] += 1
        # Run this branch when the result of status.startswith(the text 'UNRESOLVED_').
        elif status.startswith("UNRESOLVED_"):
            # Update self._totals['unresolved_timing_evaluations'] to its current value plus 1.
            self._totals["unresolved_timing_evaluations"] += 1
            # Set key to the result of {'UNRESOLVED_PATH_PROGRESS': 'unresolved_path_progress',
            # 'UNRESOLVED_SPEED': 'unresolved_speed',...(status).
            key = {
                "UNRESOLVED_PATH_PROGRESS": "unresolved_path_progress",
                "UNRESOLVED_SPEED": "unresolved_speed",
                "UNRESOLVED_VEHICLE_STATE": "unresolved_vehicle_state",
            # Supply status to {'UNRESOLVED_PATH_PROGRESS': 'unresolved_path_progress', 'UNRESOLVED_SPEED':
            # 'unresolved_speed',...
            }.get(status)
            # Run this branch when key.
            if key:
                # Update self._totals[key] to its current value plus 1.
                self._totals[key] += 1
            # Run this branch when status equals the text 'UNRESOLVED_SPEED' and 'ego_speed_mps' from record; use
            # None if absent equals 0.0 or 'target_speed_mps' from record; use None if absent equals 0.0.
            if (status == "UNRESOLVED_SPEED"
                    # Evaluate 'ego_speed_mps' from record; use None if absent equals 0.0 or 'target_speed_mps'
                    # from record; use None if absent equals 0.0 as part of the enclosing expression.
                    and (record.get("ego_speed_mps") == 0.0
                         # Evaluate 'target_speed_mps' from record; use None if absent equals 0.0 as part of the
                         # enclosing expression.
                         or record.get("target_speed_mps") == 0.0)):
                # Update self._totals['nominal_timing_unavailable_due_to_zero_speed'] to its current value plus 1.
                self._totals[
                    "nominal_timing_unavailable_due_to_zero_speed"
                # Supply 1 to the enclosing expression.
                ] += 1

    # Assess ldm using the inputs and processing steps below.
    # Input ldm: the supplied ldm.
    # Input current_time: the supplied current time.
    # Output: the result of copy.deepcopy(result).
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def assess_ldm(self, ldm, current_time):
        # Set graph to ldm.current_conflict_graph or an empty dictionary.
        graph = ldm.current_conflict_graph or {}
        # Set edge_results to an empty list.
        edge_results = []
        # Iterate over 'edges' from graph; use an empty tuple if absent, binding each item to edge.
        for edge in graph.get("edges", ()):
            # Update self._totals['spatial_edges_evaluated'] to its current value plus 1.
            self._totals["spatial_edges_evaluated"] += 1
            # Update self._totals['non_conflicting_candidate_paths_excluded'] to its current value plus an integer
            # built from 'non_conflicting_candidate_path_count' from edge; use 0 if absent.
            self._totals["non_conflicting_candidate_paths_excluded"] += int(
                # Supply 'non_conflicting_candidate_path_count' from edge; use 0 if absent to int.
                edge.get("non_conflicting_candidate_path_count", 0)
            )
            # Set target_id to edge at 'target_track_id'.
            target_id = edge["target_track_id"]
            # Set records to an empty list.
            records = []
            # Run this branch when target_id belongs to ldm.tracks.
            if target_id in ldm.tracks:
                # Iterate over the result of self._candidate_path_ids(edge), binding each item to (manoeuvre,
                # path_id).
                for manoeuvre, path_id in self._candidate_path_ids(edge):
                    # Set record to the result of self._evaluate_path(ldm, edge, target_id, manoeuvre, path_id,
                    # current_time).
                    record = self._evaluate_path(
                        # Supply current_time to self._evaluate_path.
                        ldm, edge, target_id, manoeuvre, path_id, current_time
                    )
                    # Append record to records.
                    records.append(record)
                    # Call self._count_record with the supplied arguments.
                    self._count_record(record)
            # Set applicable to a list of record for record in records; retain entries satisfying record at
            # 'status' does not belong to self.NON_APPLICABLE.
            applicable = [
                # Evaluate records as part of the enclosing expression.
                record for record in records
                # Evaluate record at 'status' does not belong to self.NON_APPLICABLE as part of the enclosing
                # expression.
                if record["status"] not in self.NON_APPLICABLE
            ]
            # Set statuses to a set of record at 'status' for record in applicable.
            statuses = {record["status"] for record in applicable}
            # Run this branch when the text 'TEMPORAL_CONFLICT' belongs to statuses.
            if "TEMPORAL_CONFLICT" in statuses:
                # Set (possible, status) to a tuple containing True, the text 'TEMPORAL_CONFLICT'.
                possible, status = True, "TEMPORAL_CONFLICT"
                # Add a tuple containing ldm.ego_id, target_id to self._conflicting_pairs.
                self._conflicting_pairs.add((ldm.ego_id, target_id))
            # Run this branch when whether any item is true in a lazy sequence of the result of
            # value.startswith(the text 'UNRESOLVED_') for value in statuses.
            elif any(value.startswith("UNRESOLVED_") for value in statuses):
                # Set (possible, status) to a tuple containing None, the text 'UNRESOLVED_TIMING'.
                possible, status = None, "UNRESOLVED_TIMING"
            # Run this branch when applicable.
            elif applicable:
                # Set (possible, status) to a tuple containing False, the text 'SPATIAL_ONLY'.
                possible, status = False, "SPATIAL_ONLY"
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set (possible, status) to a tuple containing None, the text
                # 'UNRESOLVED_NO_APPLICABLE_EVALUATION'.
                possible, status = None, "UNRESOLVED_NO_APPLICABLE_EVALUATION"
                # Update self._totals['unresolved_no_applicable_evaluation'] to its current value plus 1.
                self._totals["unresolved_no_applicable_evaluation"] += 1
            # Append a dictionary containing ego_id, target_id, timestamp, temporal_conflict_possible, status,
            # evaluations to edge_results.
            edge_results.append({
                # Store ldm.ego_id under 'ego_id'.
                # Store target_id under 'target_id'.
                "ego_id": ldm.ego_id, "target_id": target_id,
                # Store a floating-point number built from current_time under 'timestamp'.
                "timestamp": float(current_time),
                # Store possible under 'temporal_conflict_possible'.
                "temporal_conflict_possible": possible,
                # Store status under 'status'.
                # Store a tuple built from records under 'evaluations'.
                "status": status, "evaluations": tuple(records),
            })
        # Set result to a dictionary containing ego_id, timestamp, edges.
        result = {
            # Store ldm.ego_id under 'ego_id'.
            # Store a floating-point number built from current_time under 'timestamp'.
            "ego_id": ldm.ego_id, "timestamp": float(current_time),
            # Store a tuple built from edge_results under 'edges'.
            "edges": tuple(edge_results),
        }
        # Set self._results[ldm.ego_id] to the result of copy.deepcopy(result).
        self._results[ldm.ego_id] = copy.deepcopy(result)
        # Return the result of copy.deepcopy(result) to the caller.
        return copy.deepcopy(result)

    # Get result using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Output: the result of copy.deepcopy(ego_id from self._results; use None if absent).
    def get_result(self, ego_id):
        # Return the result of copy.deepcopy(ego_id from self._results; use None if absent) to the caller.
        return copy.deepcopy(self._results.get(ego_id))

    # Validation summary using the inputs and processing steps below.
    # Output: result.
    def validation_summary(self):
        # Set result to a dictionary built from self._totals.
        result = dict(self._totals)
        # Set result['unique_ego_target_pairs_with_temporal_conflict'] to the number of entries in
        # self._conflicting_pairs.
        result["unique_ego_target_pairs_with_temporal_conflict"] = len(
            # Supply self._conflicting_pairs to len.
            self._conflicting_pairs
        )
        # Return result to the caller.
        return result

    # Reset using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def reset(self, ego_id=None):
        # Run this branch when ego_id is the same object as None.
        if ego_id is None:
            # Clear the stored entries in self._results.
            self._results.clear()
            # Set self._totals to the result of self._empty_totals().
            self._totals = self._empty_totals()
            # Clear the stored entries in self._conflicting_pairs.
            self._conflicting_pairs.clear()
        # Run this alternative branch when the preceding branch does not apply.
        else:
            # Remove the requested entry from self._results.
            self._results.pop(ego_id, None)
