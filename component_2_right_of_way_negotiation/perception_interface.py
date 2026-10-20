"""Deterministic, ASAM OSI-inspired object-level perception for SUMO.

The interface converts global simulator ground truth into an ego-specific
sensor view and then into current-frame local object detections. Positive ego
longitudinal is forward and positive lateral is left. SUMO navigation headings
are 0=north and 90 degrees=east.

SUMO ``position`` and ``lane_position`` use the center of the front bumper as
their vehicle reference. Geometric footprints derive the vehicle center from
that position and actual length. The virtual ego sensor origin remains the
project's SUMO reference point; no physical radar mounting offset is modelled.

``IDEAL_BASELINE`` applies only the 160 m reference limit (no FOV or
occlusion) to exact simulator values and is an unrealistic upper-performance
baseline. ``GEOMETRIC_SENSOR`` applies the fused 360-degree FOV and dynamic
vehicle-to-vehicle occlusion, retaining exact simulator values for visible
targets; it remains an object-level geometric abstraction. The provisional
``REALISTIC_OBJECT_SENSOR`` currently delegates to that same geometry: noise,
missed detections, and latency are not yet implemented.
Positive finite dimensions are mandatory for both geometric profiles.

Route and manoeuvre truth are deliberately excluded because they would leak
future information downstream. Static occluders may later be supplied to the
geometric layer; none are invented here.

``sensor_range`` is the selected reference sensor capability and
``sensor_fov_degrees`` is fused object-list coverage, not one radar's FOV. The
interface does not simulate separate radar returns; each reference radar has a
150-degree horizontal FOV. ASAM OSI inspires the ground-truth-to-sensor-view
structure but does not prescribe these numeric values.
"""

# Import copy for use in this module.
import copy
# Import math for use in this module.
import math

# Import numpy as np for use in this module.
import numpy as np

# Import DEFAULT_PERCEPTION_PROFILE, GEOMETRIC_SENSOR_PROFILE, PERCEPTION_PROFILES,
# REALISTIC_OBJECT_SENSOR_PROFILE, SENSOR_CONFIGURATION_SUMMARY, SENSOR_FOV_DEGREES, SENSOR_RANGE from config for
# the operations below.
from config import (
    DEFAULT_PERCEPTION_PROFILE,
    GEOMETRIC_SENSOR_PROFILE,
    PERCEPTION_PROFILES,
    REALISTIC_OBJECT_SENSOR_PROFILE,
    SENSOR_CONFIGURATION_SUMMARY,
    SENSOR_FOV_DEGREES,
    SENSOR_RANGE,
)


# Produce an independent deterministic perception frame for one ego AV.
# Instances expose the attributes and methods implemented in this class.
class PerceptionInterface:
    """Produce an independent deterministic perception frame for one ego AV."""

    # Set VALID_PROFILES to PERCEPTION_PROFILES.
    VALID_PROFILES = PERCEPTION_PROFILES
    # Set GEOMETRIC_PROFILES to an immutable set built from a set containing GEOMETRIC_SENSOR_PROFILE,
    # REALISTIC_OBJECT_SENSOR_PROFILE.
    GEOMETRIC_PROFILES = frozenset({
        # Include GEOMETRIC_SENSOR_PROFILE in this set.
        GEOMETRIC_SENSOR_PROFILE,
        # Include REALISTIC_OBJECT_SENSOR_PROFILE in this set.
        REALISTIC_OBJECT_SENSOR_PROFILE,
    })
    # Set _EPSILON to 1e-12.
    _EPSILON = 1e-12

    # Initialize the instance attributes and collaborators used by the operations below.
    # Input profile: the supplied profile.
    # Input sensor_range: the supplied sensor range.
    # Input sensor_fov_degrees: the supplied sensor fov degrees.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def __init__(self, profile=DEFAULT_PERCEPTION_PROFILE,
                 # Declare sensor_range as input parameter.
                 sensor_range=SENSOR_RANGE,
                 # Declare sensor_fov_degrees as input parameter.
                 sensor_fov_degrees=SENSOR_FOV_DEGREES):
        # Run this branch when profile does not belong to self.VALID_PROFILES.
        if profile not in self.VALID_PROFILES:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(f"Unsupported perception profile: {profile!r}")
        # Set self.profile to profile.
        self.profile = profile
        # Set self.sensor_range to the result of self._finite_number(sensor_range, the text 'sensor_range').
        self.sensor_range = self._finite_number(sensor_range, "sensor_range")
        # Set self.sensor_fov_degrees to the result of self._finite_number(sensor_fov_degrees, the text
        # 'sensor_fov_degrees').
        self.sensor_fov_degrees = self._finite_number(
            # Supply sensor_fov_degrees to self._finite_number.
            sensor_fov_degrees, "sensor_fov_degrees"
        )
        # Run this branch when self.sensor_range is less than 0.0.
        if self.sensor_range < 0.0:
            # Raise ValueError with the text 'sensor_range must be non-negative' to stop this execution path.
            raise ValueError("sensor_range must be non-negative")
        # Run this branch when the negation of 0.0 is less than self.sensor_fov_degrees; is at most 360.0.
        if not 0.0 < self.sensor_fov_degrees <= 360.0:
            # Raise ValueError with the text 'sensor_fov_degrees must be in (0, 360]' to stop this execution path.
            raise ValueError("sensor_fov_degrees must be in (0, 360]")
        # Set self.last_diagnostics_by_ego to an empty dictionary.
        self.last_diagnostics_by_ego = {}
        # Set self.last_summary_by_ego to an empty dictionary.
        self.last_summary_by_ego = {}
        # Deprecated compatibility alias for the most recently requested ego.
        # Set self.last_diagnostics to an empty list.
        self.last_diagnostics = []

    # Return ego localization plus current geometrically detected objects.
    # Input ego_vehicle_id: the supplied ego vehicle id.
    # Input ego_data: the supplied ego data.
    # Input all_vehicle_data: the supplied all vehicle data.
    # Input current_time: the supplied current time.
    # Output: observations.
    # Processing: iterate over the relevant records, then select branches using the stated conditions, then handle
    # the specified errors.
    def generate_observations(self, ego_vehicle_id, ego_data,
                              # Declare all_vehicle_data, current_time as input parameters.
                              all_vehicle_data, current_time):
        """Return ego localization plus current geometrically detected objects.

        ``all_vehicle_data[ego_vehicle_id]`` is the authoritative ego state.
        The separate ``ego_data`` parameter is retained temporarily for API
        compatibility and is validation-only; contradictory values raise
        ``ValueError``. Callers should plan to remove this redundant argument
        in a future breaking API revision.
        """
        # Set timestamp to the result of self._finite_number(current_time, the text 'current_time').
        timestamp = self._finite_number(current_time, "current_time")
        # Run this branch when timestamp is less than 0.0.
        if timestamp < 0.0:
            # Raise ValueError with the text 'current_time must be non-negative' to stop this execution path.
            raise ValueError("current_time must be non-negative")
        # Run this branch when ego_vehicle_id does not belong to all_vehicle_data.
        if ego_vehicle_id not in all_vehicle_data:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(
                # Supply formatted text built from the embedded values to ValueError.
                f"ego vehicle {ego_vehicle_id!r} is absent from all_vehicle_data"
            )

        # Set applies_geometry to the result of self._uses_geometric_visibility().
        applies_geometry = self._uses_geometric_visibility()
        # Set require_dimensions to applies_geometry.
        require_dimensions = applies_geometry
        # Set ego to the result of self._validate_vehicle_state(ego_vehicle_id, ego_data).
        ego = self._validate_vehicle_state(
            # Supply require_dimensions as require_dimensions.
            ego_vehicle_id, ego_data, require_dimensions=require_dimensions
        )
        # Set frame_ego to the result of self._validate_vehicle_state(ego_vehicle_id, all_vehicle_data at
        # ego_vehicle_id).
        frame_ego = self._validate_vehicle_state(
            # Supply ego_vehicle_id to self._validate_vehicle_state.
            ego_vehicle_id,
            # Supply all_vehicle_data at ego_vehicle_id to self._validate_vehicle_state.
            all_vehicle_data[ego_vehicle_id],
            # Supply require_dimensions as require_dimensions.
            require_dimensions=require_dimensions,
        )
        # Call self._validate_consistent_ego_state with the supplied arguments.
        self._validate_consistent_ego_state(ego_vehicle_id, ego, frame_ego)
        # Set ego to frame_ego.
        ego = frame_ego
        # Set observations to a dictionary of the supplied entries.
        observations = {
            # Store the result of self._make_ego_localization(ego_vehicle_id, ego, timestamp, self.profile) under
            # ego_vehicle_id.
            ego_vehicle_id: self._make_ego_localization(
                # Supply ego_vehicle_id to self._make_ego_localization.
                ego_vehicle_id, ego, timestamp, self.profile
            )
        }
        # Set diagnostics to an empty list.
        diagnostics = []
        # Set candidates to an empty list.
        candidates = []

        # Iterate over key/value pairs from all_vehicle_data, binding each item to (object_id, raw_state).
        for object_id, raw_state in all_vehicle_data.items():
            # Run this branch when object_id equals ego_vehicle_id.
            if object_id == ego_vehicle_id:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set diagnostic to the result of self._diagnostic_template(timestamp, ego_vehicle_id, object_id).
            diagnostic = self._diagnostic_template(
                # Supply ego_vehicle_id to self._diagnostic_template.
                timestamp, ego_vehicle_id, object_id
            )
            # Attempt the enclosed operations and route matching exceptions to the handlers below.
            try:
                # Set target to the result of self._validate_vehicle_state(object_id, raw_state).
                target = self._validate_vehicle_state(
                    # Supply require_dimensions as require_dimensions.
                    object_id, raw_state, require_dimensions=require_dimensions
                )
            # Handle (TypeError, ValueError) as error using the recovery steps below.
            except (TypeError, ValueError) as error:
                # Update diagnostic with the supplied entries.
                diagnostic.update(
                    # Supply result as the text 'REJECTED'.
                    # Supply reason as the text 'INVALID_TARGET_STATE'.
                    result="REJECTED", reason="INVALID_TARGET_STATE",
                    # Supply detail as a string built from error.
                    detail=str(error)
                )
                # Append diagnostic to diagnostics.
                diagnostics.append(diagnostic)
                # Skip the rest of this loop iteration and process the next item.
                continue

            # Set relative_position to the result of self._world_to_ego(target at 'position' minus ego at
            # 'position', ego at 'heading_radians').
            relative_position = self._world_to_ego(
                # Supply target at 'position' minus ego at 'position' to self._world_to_ego.
                target["position"] - ego["position"], ego["heading_radians"]
            )
            # Set range_m to a floating-point number built from the result of np.hypot(the unpacked values from
            # relative_position).
            range_m = float(np.hypot(*relative_position))
            # Set bearing to the result of math.atan2(relative_position at 1, relative_position at 0).
            bearing = math.atan2(relative_position[1], relative_position[0])
            # Update diagnostic with the supplied entries.
            diagnostic.update(range_m=range_m, bearing_radians=bearing)
            # Run this branch when range_m is greater than self.sensor_range.
            if range_m > self.sensor_range:
                # Update diagnostic with the supplied entries.
                diagnostic.update(result="REJECTED", reason="OUT_OF_RANGE")
                # Append diagnostic to diagnostics.
                diagnostics.append(diagnostic)
                # Skip the rest of this loop iteration and process the next item.
                continue

            # Set relative_velocity to the result of self._world_to_ego(the result of self._velocity_vector(target
            # at 'speed', target at 'heading_radians') minus the...).
            relative_velocity = self._world_to_ego(
                # Supply the result of self._velocity_vector(target at 'speed', target at 'heading_radians') minus
                # the result of self._velocity_vector(ego at 'speed', ego at 'heading_radians') to
                # self._world_to_ego.
                self._velocity_vector(target["speed"], target["heading_radians"])
                # Evaluate the result of self._velocity_vector(ego at 'speed', ego at 'heading_radians') as part
                # of the enclosing expression.
                - self._velocity_vector(ego["speed"], ego["heading_radians"]),
                # Supply ego at 'heading_radians' to self._world_to_ego.
                ego["heading_radians"],
            )
            # Set intervals to None.
            intervals = None
            # Set clipped_intervals to None.
            clipped_intervals = None
            # Set fov_fraction to 1.0.
            fov_fraction = 1.0
            # Run this branch when require_dimensions.
            if require_dimensions:
                # Set intervals to the result of self._calculate_angular_interval(the result of
                # self._calculate_bounding_box(target), ego).
                intervals = self._calculate_angular_interval(
                    # Supply the result of self._calculate_bounding_box(target) to
                    # self._calculate_angular_interval.
                    self._calculate_bounding_box(target), ego
                )
                # Set clipped_intervals to the result of self._intersect_intervals(intervals, the result of
                # self._fov_intervals()).
                clipped_intervals = self._intersect_intervals(
                    # Supply the result of self._fov_intervals() to self._intersect_intervals.
                    intervals, self._fov_intervals()
                )
                # Set fov_fraction to the result of self._interval_fraction(clipped_intervals, intervals).
                fov_fraction = self._interval_fraction(
                    # Supply clipped_intervals to self._interval_fraction.
                    clipped_intervals, intervals
                )
                # Run this branch when fov_fraction is at most self._EPSILON.
                if fov_fraction <= self._EPSILON:
                    # Update diagnostic with the supplied entries.
                    diagnostic.update(
                        # Supply result as the text 'REJECTED'.
                        # Supply reason as the text 'OUT_OF_FOV'.
                        result="REJECTED", reason="OUT_OF_FOV",
                        # Supply visible_fraction as 0.0.
                        # Supply fov_visible_fraction as 0.0.
                        visible_fraction=0.0, fov_visible_fraction=0.0,
                        # Supply occlusion_visible_fraction as None.
                        occlusion_visible_fraction=None,
                    )
                    # Append diagnostic to diagnostics.
                    diagnostics.append(diagnostic)
                    # Skip the rest of this loop iteration and process the next item.
                    continue

            # Append a dictionary containing object_id, state, relative_position, relative_velocity, range,
            # bearing, intervals,... to candidates.
            candidates.append({
                # Store object_id under 'object_id'.
                "object_id": object_id,
                # Store target under 'state'.
                "state": target,
                # Store relative_position under 'relative_position'.
                "relative_position": relative_position,
                # Store relative_velocity under 'relative_velocity'.
                "relative_velocity": relative_velocity,
                # Store range_m under 'range'.
                "range": range_m,
                # Store bearing under 'bearing'.
                "bearing": bearing,
                # Store intervals under 'intervals'.
                "intervals": intervals,
                # Store clipped_intervals under 'visible_intervals'.
                "visible_intervals": clipped_intervals,
                # Store fov_fraction under 'fov_visible_fraction'.
                "fov_visible_fraction": fov_fraction,
                # Store diagnostic under 'diagnostic'.
                "diagnostic": diagnostic,
                # Store self.profile under 'profile'.
                "profile": self.profile,
            })

        # Call candidates.sort with the supplied arguments.
        candidates.sort(key=lambda item: (item["range"], str(item["object_id"])))
        # Set covered to an empty list.
        covered = []
        # Set index to 0.
        index = 0
        # Repeat the following steps while index is less than the number of entries in candidates.
        while index < len(candidates):
            # Set group_end to index plus 1.
            group_end = index + 1
            # Repeat the following steps while group_end is less than the number of entries in candidates and the
            # absolute value of candidates[group_end]['range'] minus candidates[index]['range'] is at most
            # self._EPSILON.
            while (group_end < len(candidates)
                   # Evaluate the absolute value of candidates[group_end] at 'range' minus candidates[index] at
                   # 'range' is at most self._EPSILON as part of the enclosing expression.
                   and abs(candidates[group_end]["range"]
                           # Evaluate candidates[index] at 'range' as part of the enclosing expression.
                           - candidates[index]["range"]) <= self._EPSILON):
                # Update group_end to its current value plus 1.
                group_end += 1
            # Set group to candidates sliced by index:group_end.
            group = candidates[index:group_end]
            # Set group_intervals to an empty list.
            group_intervals = []
            # Iterate over group, binding each item to candidate.
            for candidate in group:
                # Set occlusion_fraction to 1.0.
                occlusion_fraction = 1.0
                # Set combined_fraction to 1.0.
                combined_fraction = 1.0
                # Run this branch when applies_geometry.
                if applies_geometry:
                    # Set occlusion_fraction to the result of self._calculate_visible_fraction(candidate at
                    # 'visible_intervals', covered).
                    occlusion_fraction = self._calculate_visible_fraction(
                        # Supply candidate at 'visible_intervals' to self._calculate_visible_fraction.
                        candidate["visible_intervals"], covered
                    )
                    # Set combined_fraction to the result of self._clamp_fraction(candidate at
                    # 'fov_visible_fraction' multiplied by occlusion_fraction).
                    combined_fraction = self._clamp_fraction(
                        # Supply candidate at 'fov_visible_fraction' multiplied by occlusion_fraction to
                        # self._clamp_fraction.
                        candidate["fov_visible_fraction"] * occlusion_fraction
                    )
                    # Extend group_intervals with candidate at 'visible_intervals'.
                    group_intervals.extend(candidate["visible_intervals"])

                # Set diagnostic to candidate at 'diagnostic'.
                diagnostic = candidate["diagnostic"]
                # Update diagnostic with the supplied entries.
                diagnostic.update(
                    # Supply fov_visible_fraction as candidate at 'fov_visible_fraction'.
                    fov_visible_fraction=candidate["fov_visible_fraction"],
                    # Supply occlusion_visible_fraction as occlusion_fraction.
                    occlusion_visible_fraction=occlusion_fraction,
                    # Supply visible_fraction as combined_fraction.
                    visible_fraction=combined_fraction,
                )
                # Run this branch when combined_fraction is at most self._EPSILON.
                if combined_fraction <= self._EPSILON:
                    # Update diagnostic with the supplied entries.
                    diagnostic.update(result="REJECTED", reason="FULLY_OCCLUDED")
                # Run this alternative branch when the preceding branch does not apply.
                else:
                    # Set reason to the text 'PARTIALLY_VISIBLE' when combined_fraction is less than 1.0 minus
                    # self._EPSILON, otherwise the text 'DETECTED'.
                    reason = (
                        "PARTIALLY_VISIBLE"
                        # Evaluate combined_fraction is less than 1.0 minus self._EPSILON as part of the enclosing
                        # expression.
                        if combined_fraction < 1.0 - self._EPSILON
                        # Supply the text 'DETECTED' to the enclosing expression.
                        else "DETECTED"
                    )
                    # Update diagnostic with the supplied entries.
                    diagnostic.update(result="DETECTED", reason=reason)
                    # Set observations[candidate['object_id']] to the result of
                    # self._make_object_detection(candidate, timestamp, candidate at 'fov_visible_fraction',
                    # occlusion_fraction, combined_fraction).
                    observations[candidate["object_id"]] = (
                        # Evaluate the result of self._make_object_detection(candidate, timestamp, candidate at
                        # 'fov_visible_fraction', occlusion_fraction, combined_fraction) as part of the enclosing
                        # expression.
                        self._make_object_detection(
                            # Supply candidate to self._make_object_detection.
                            candidate, timestamp,
                            # Supply candidate at 'fov_visible_fraction' to self._make_object_detection.
                            candidate["fov_visible_fraction"],
                            # Supply occlusion_fraction to self._make_object_detection.
                            occlusion_fraction, combined_fraction,
                        )
                    )
                # Append diagnostic to diagnostics.
                diagnostics.append(diagnostic)
            # Run this branch when applies_geometry.
            if applies_geometry:
                # Set covered to the result of self._merge_intervals(covered plus group_intervals).
                covered = self._merge_intervals(covered + group_intervals)
            # Set index to group_end.
            index = group_end

        # Call self._store_frame_metadata with the supplied arguments.
        self._store_frame_metadata(
            # Supply the number of entries in all_vehicle_data minus 1 to self._store_frame_metadata.
            ego_vehicle_id, timestamp, len(all_vehicle_data) - 1, diagnostics
        )
        # Return observations to the caller.
        return observations

    # Whether this profile uses the shared deterministic geometry layer.
    # Output: self.profile belongs to self.GEOMETRIC_PROFILES.
    def _uses_geometric_visibility(self):
        """Whether this profile uses the shared deterministic geometry layer."""
        # Return self.profile belongs to self.GEOMETRIC_PROFILES to the caller.
        return self.profile in self.GEOMETRIC_PROFILES

    # Return copies of the latest detailed diagnostics per requested ego.
    # Input ego_vehicle_id: the supplied ego vehicle id.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def get_last_diagnostics(self, ego_vehicle_id=None):
        """Return copies of the latest detailed diagnostics per requested ego."""
        # Run this branch when ego_vehicle_id is the same object as None.
        if ego_vehicle_id is None:
            # Return the result of copy.deepcopy(self.last_diagnostics_by_ego) to the caller.
            return copy.deepcopy(self.last_diagnostics_by_ego)
        # Return the result of copy.deepcopy(ego_vehicle_id from self.last_diagnostics_by_ego; use an empty list
        # if absent) to the caller.
        return copy.deepcopy(self.last_diagnostics_by_ego.get(ego_vehicle_id, []))

    # Return copies of the latest frame summaries per requested ego.
    # Input ego_vehicle_id: the supplied ego vehicle id.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def get_last_summary(self, ego_vehicle_id=None):
        """Return copies of the latest frame summaries per requested ego."""
        # Run this branch when ego_vehicle_id is the same object as None.
        if ego_vehicle_id is None:
            # Return the result of copy.deepcopy(self.last_summary_by_ego) to the caller.
            return copy.deepcopy(self.last_summary_by_ego)
        # Return the result of copy.deepcopy(ego_vehicle_id from self.last_summary_by_ego; use None if absent) to
        # the caller.
        return copy.deepcopy(self.last_summary_by_ego.get(ego_vehicle_id))

    # Discard retained latest-frame metadata for one departed ego.
    # Input ego_vehicle_id: the supplied ego vehicle id.
    # Output: no explicit value; normal completion returns None.
    def clear_ego_diagnostics(self, ego_vehicle_id):
        """Discard retained latest-frame metadata for one departed ego."""
        # Remove the requested entry from self.last_diagnostics_by_ego.
        self.last_diagnostics_by_ego.pop(ego_vehicle_id, None)
        # Remove the requested entry from self.last_summary_by_ego.
        self.last_summary_by_ego.pop(ego_vehicle_id, None)

    # Discard all retained frame metadata on simulation reset.
    # Output: no explicit value; normal completion returns None.
    def clear_diagnostics(self):
        """Discard all retained frame metadata on simulation reset."""
        # Clear the stored entries in self.last_diagnostics_by_ego.
        self.last_diagnostics_by_ego.clear()
        # Clear the stored entries in self.last_summary_by_ego.
        self.last_summary_by_ego.clear()
        # Set self.last_diagnostics to an empty list.
        self.last_diagnostics = []

    # Store frame metadata using the inputs and processing steps below.
    # Input ego_id: the identifier of the ego vehicle.
    # Input timestamp: the supplied timestamp.
    # Input candidate_count: the supplied candidate count.
    # Input diagnostics: the supplied diagnostics.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _store_frame_metadata(self, ego_id, timestamp, candidate_count,
                              # Declare diagnostics as input parameter.
                              diagnostics):
        # Set frame to the result of copy.deepcopy(diagnostics).
        frame = copy.deepcopy(diagnostics)
        # Set self.last_diagnostics_by_ego[ego_id] to frame.
        self.last_diagnostics_by_ego[ego_id] = frame
        # Set self.last_diagnostics to the result of copy.deepcopy(frame).
        self.last_diagnostics = copy.deepcopy(frame)
        # Set counts to a dictionary of reason mapped to 0 for reason in a tuple containing the text
        # 'INVALID_TARGET_STATE', the text 'OUT_OF_RANGE', the text 'OUT_OF_FOV', the text...
        counts = {reason: 0 for reason in (
            "INVALID_TARGET_STATE", "OUT_OF_RANGE", "OUT_OF_FOV",
            "FULLY_OCCLUDED", "PARTIALLY_VISIBLE"
        )}
        # Iterate over diagnostics, binding each item to item.
        for item in diagnostics:
            # Run this branch when item at 'reason' belongs to counts.
            if item["reason"] in counts:
                # Update counts[item['reason']] to its current value plus 1.
                counts[item["reason"]] += 1
        # Set self.last_summary_by_ego[ego_id] to a dictionary containing time_seconds, ego_id, profile,
        # candidate_targets, detected_targets, invalid_targets,...
        self.last_summary_by_ego[ego_id] = {
            # Store timestamp under 'time_seconds'.
            "time_seconds": timestamp,
            # Store ego_id under 'ego_id'.
            "ego_id": ego_id,
            # Store self.profile under 'profile'.
            "profile": self.profile,
            # Store candidate_count under 'candidate_targets'.
            "candidate_targets": candidate_count,
            # Store the sum of a lazy sequence of item at 'result' equals the text 'DETECTED' for item in
            # diagnostics under 'detected_targets'.
            "detected_targets": sum(
                # Evaluate item at 'result' equals the text 'DETECTED' as part of the enclosing expression.
                item["result"] == "DETECTED" for item in diagnostics
            ),
            # Store counts at 'INVALID_TARGET_STATE' under 'invalid_targets'.
            "invalid_targets": counts["INVALID_TARGET_STATE"],
            # Store counts at 'OUT_OF_RANGE' under 'out_of_range_targets'.
            "out_of_range_targets": counts["OUT_OF_RANGE"],
            # Store counts at 'OUT_OF_FOV' under 'out_of_fov_targets'.
            "out_of_fov_targets": counts["OUT_OF_FOV"],
            # Store counts at 'FULLY_OCCLUDED' under 'fully_occluded_targets'.
            "fully_occluded_targets": counts["FULLY_OCCLUDED"],
            # Store counts at 'PARTIALLY_VISIBLE' under 'partially_visible_targets'.
            "partially_visible_targets": counts["PARTIALLY_VISIBLE"],
            # Store the result of copy.deepcopy(SENSOR_CONFIGURATION_SUMMARY) under 'sensor_configuration'.
            "sensor_configuration": copy.deepcopy(SENSOR_CONFIGURATION_SUMMARY),
        }

    # Diagnostic template using the inputs and processing steps below.
    # Input timestamp: the supplied timestamp.
    # Input ego_id: the identifier of the ego vehicle.
    # Input target_id: the supplied target id.
    # Output: a dictionary containing time_seconds, ego_id, target_id, profile, result, reason, range_m,
    # bearing_radians,...
    def _diagnostic_template(self, timestamp, ego_id, target_id):
        # Return a dictionary containing time_seconds, ego_id, target_id, profile, result, reason, range_m,
        # bearing_radians,... to the caller.
        return {
            # Store timestamp under 'time_seconds'.
            # Store ego_id under 'ego_id'.
            "time_seconds": timestamp, "ego_id": ego_id,
            # Store target_id under 'target_id'.
            # Store self.profile under 'profile'.
            "target_id": target_id, "profile": self.profile,
            # Store None under 'result'.
            # Store None under 'reason'.
            # Store None under 'range_m'.
            "result": None, "reason": None, "range_m": None,
            # Store None under 'bearing_radians'.
            # Store None under 'fov_visible_fraction'.
            "bearing_radians": None, "fov_visible_fraction": None,
            # Store None under 'occlusion_visible_fraction'.
            # Store None under 'visible_fraction'.
            "occlusion_visible_fraction": None, "visible_fraction": None,
        }

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Finite number using the inputs and processing steps below.
    # Input value: the supplied value.
    # Input name: the supplied name.
    # Output: number.
    # Processing: select branches using the stated conditions, then handle the specified errors.
    def _finite_number(value, name):
        # Attempt the enclosed operations and route matching exceptions to the handlers below.
        try:
            # Set number to a floating-point number built from value.
            number = float(value)
        # Handle (TypeError, ValueError) as error using the recovery steps below.
        except (TypeError, ValueError) as error:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(f"{name} must be a finite number") from error
        # Run this branch when the negation of whether number contains finite numeric values.
        if not math.isfinite(number):
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(f"{name} must be a finite number")
        # Return number to the caller.
        return number

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Validate vehicle state using the inputs and processing steps below.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input state: the state read or updated by this operation.
    # Input require_dimensions: the supplied require dimensions.
    # Output: validated.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _validate_vehicle_state(cls, vehicle_id, state,
                                # Declare require_dimensions as input parameter.
                                require_dimensions=True):
        # Run this branch when the negation of whether state has type dict.
        if not isinstance(state, dict):
            # Raise TypeError with formatted text built from the embedded values to stop this execution path.
            raise TypeError(f"vehicle {vehicle_id!r} state must be a dictionary")
        # Iterate over a tuple containing the text 'position', the text 'speed', the text 'heading_radians',
        # binding each item to field.
        for field in ("position", "speed", "heading_radians"):
            # Run this branch when field does not belong to state.
            if field not in state:
                # Raise ValueError with formatted text built from the embedded values to stop this execution path.
                raise ValueError(
                    # Supply formatted text built from the embedded values to ValueError.
                    f"vehicle {vehicle_id!r} missing mandatory field {field!r}"
                )
        # Set position to the result of np.asarray(state at 'position').
        position = np.asarray(state["position"], dtype=float)
        # Set speed to the result of cls._finite_number(state at 'speed', the text 'speed').
        speed = cls._finite_number(state["speed"], "speed")
        # Set heading to the result of cls._finite_number(state at 'heading_radians', the text 'heading_radians').
        heading = cls._finite_number(state["heading_radians"], "heading_radians")
        # Run this branch when position.shape differs from a tuple containing 2 or the negation of the result of
        # np.all(whether position contains finite numeric values).
        if position.shape != (2,) or not np.all(np.isfinite(position)):
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(
                # Supply formatted text built from the embedded values to ValueError.
                f"vehicle {vehicle_id!r} position must contain two finite numbers"
            )
        # Run this branch when speed is less than 0.0.
        if speed < 0.0:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(f"vehicle {vehicle_id!r} speed must be non-negative")

        # Set dimensions to an empty dictionary.
        dimensions = {}
        # Iterate over a tuple containing the text 'length', the text 'width', binding each item to field.
        for field in ("length", "width"):
            # Run this branch when field does not belong to state.
            if field not in state:
                # Run this branch when require_dimensions.
                if require_dimensions:
                    # Raise ValueError with formatted text built from the embedded values to stop this execution
                    # path.
                    raise ValueError(
                        # Supply formatted text built from the embedded values to ValueError.
                        f"vehicle {vehicle_id!r} missing mandatory field {field!r}"
                    )
                # Set dimensions[field] to None.
                dimensions[field] = None
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Set value to the result of cls._finite_number(state at field, field).
            value = cls._finite_number(state[field], field)
            # Run this branch when value is at most 0.0.
            if value <= 0.0:
                # Raise ValueError with formatted text built from the embedded values to stop this execution path.
                raise ValueError(
                    # Supply formatted text built from the embedded values to ValueError.
                    f"vehicle {vehicle_id!r} {field} must be positive"
                )
            # Set dimensions[field] to value.
            dimensions[field] = value

        # Set validated to a dictionary built from state.
        validated = dict(state)
        # Update validated with the supplied entries.
        validated.update(position=position.copy(), speed=speed,
                         # Supply heading_radians as heading.
                         # Supply the unpacked keyword arguments as dimensions.
                         heading_radians=heading, **dimensions)
        # Return validated to the caller.
        return validated

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Reject contradictory duplicate ego inputs before geometry is used.
    # Input vehicle_id: the identifier of the vehicle being processed.
    # Input ego: the ego vehicle used in this calculation.
    # Input frame_ego: the supplied frame ego.
    # Output: no explicit value; normal completion returns None.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _validate_consistent_ego_state(cls, vehicle_id, ego, frame_ego):
        """Reject contradictory duplicate ego inputs before geometry is used."""
        # Set inconsistent to an empty list.
        inconsistent = []
        # Run this branch when the negation of the result of np.array_equal(ego at 'position', frame_ego at
        # 'position').
        if not np.array_equal(ego["position"], frame_ego["position"]):
            # Append the text 'position' to inconsistent.
            inconsistent.append("position")
        # Iterate over a tuple containing the text 'speed', the text 'heading_radians', the text 'length', the
        # text 'width', binding each item to field.
        for field in ("speed", "heading_radians", "length", "width"):
            # Run this branch when field from ego; use None if absent differs from field from frame_ego; use None
            # if absent.
            if ego.get(field) != frame_ego.get(field):
                # Append field to inconsistent.
                inconsistent.append(field)
        # Run this branch when inconsistent.
        if inconsistent:
            # Raise ValueError with formatted text built from the embedded values to stop this execution path.
            raise ValueError(
                # Supply formatted text built from the embedded values to ValueError.
                f"ego vehicle {vehicle_id!r} state is inconsistent between "
                f"ego_data and all_vehicle_data for fields: "
                # Evaluate {', '.join(inconsistent)} as part of the enclosing expression.
                f"{', '.join(inconsistent)}"
            )

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Velocity vector using the inputs and processing steps below.
    # Input speed: the supplied speed.
    # Input heading_radians: the supplied heading radians.
    # Output: the result of np.asarray(a list containing speed multiplied by the result of
    # math.sin(heading_radians), speed multiplied...).
    def _velocity_vector(speed, heading_radians):
        # Return the result of np.asarray(a list containing speed multiplied by the result of
        # math.sin(heading_radians), speed multiplied...) to the caller.
        return np.asarray([
            # Include speed multiplied by the result of math.sin(heading_radians) in this list.
            speed * math.sin(heading_radians),
            # Include speed multiplied by the result of math.cos(heading_radians) in this list.
            speed * math.cos(heading_radians),
        # Supply dtype as float.
        ], dtype=float)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # World to ego using the inputs and processing steps below.
    # Input vector: the supplied vector.
    # Input ego_heading_radians: the supplied ego heading radians.
    # Output: the result of np.asarray(a list containing the result of np.dot(vector, forward), the result of
    # np.dot(vector, left)).
    def _world_to_ego(vector, ego_heading_radians):
        # Set forward to the result of np.asarray(a list containing the result of math.sin(ego_heading_radians),
        # the result of...).
        forward = np.asarray([
            # Include the result of math.sin(ego_heading_radians) in this list.
            math.sin(ego_heading_radians), math.cos(ego_heading_radians)
        ])
        # Set left to the result of np.asarray(a list containing the negative of the result of
        # math.cos(ego_heading_radians), the result of...).
        left = np.asarray([
            # Include the negative of the result of math.cos(ego_heading_radians) in this list.
            -math.cos(ego_heading_radians), math.sin(ego_heading_radians)
        ])
        # Return the result of np.asarray(a list containing the result of np.dot(vector, forward), the result of
        # np.dot(vector, left)) to the caller.
        return np.asarray([
            # Include the result of np.dot(vector, forward) in this list.
            np.dot(vector, forward), np.dot(vector, left)
        # Supply dtype as float.
        ], dtype=float)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Return footprint corners from SUMO's front-bumper reference.
    # Input state: the state read or updated by this operation.
    # Output: the result of np.asarray(a list containing geometric_center plus longitudinal plus lateral,
    # geometric_center plus...).
    def _calculate_bounding_box(state):
        """Return footprint corners from SUMO's front-bumper reference.

        If p_f is the front-bumper position, L the actual vehicle length, and
        u the heading unit vector, the geometric center is
        p_c = p_f - (L / 2) u. The footprint is then constructed around p_c.
        """
        # Set heading to state at 'heading_radians'.
        heading = state["heading_radians"]
        # Set forward to the result of np.asarray(a list containing the result of math.sin(heading), the result of
        # math.cos(heading)).
        forward = np.asarray([math.sin(heading), math.cos(heading)])
        # Set left to the result of np.asarray(a list containing the negative of the result of math.cos(heading),
        # the result of math.sin(heading)).
        left = np.asarray([-math.cos(heading), math.sin(heading)])
        # Set longitudinal to 0.5 multiplied by state at 'length' multiplied by forward.
        longitudinal = 0.5 * state["length"] * forward
        # Set lateral to 0.5 multiplied by state at 'width' multiplied by left.
        lateral = 0.5 * state["width"] * left
        # Set front_bumper_position to the result of np.asarray(state at 'position').
        front_bumper_position = np.asarray(state["position"], dtype=float)
        # Set geometric_center to front_bumper_position minus longitudinal.
        geometric_center = front_bumper_position - longitudinal
        # Return the result of np.asarray(a list containing geometric_center plus longitudinal plus lateral,
        # geometric_center plus...) to the caller.
        return np.asarray([
            # Include geometric_center plus longitudinal plus lateral in this list.
            geometric_center + longitudinal + lateral,
            # Include geometric_center plus longitudinal minus lateral in this list.
            geometric_center + longitudinal - lateral,
            # Include geometric_center minus longitudinal minus lateral in this list.
            geometric_center - longitudinal - lateral,
            # Include geometric_center minus longitudinal plus lateral in this list.
            geometric_center - longitudinal + lateral,
        ])

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Calculate angular interval using the inputs and processing steps below.
    # Input world_corners: the supplied world corners.
    # Input ego: the ego vehicle used in this calculation.
    # Output: return the value selected by the matching return branch below.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _calculate_angular_interval(cls, world_corners, ego):
        # Set local to the result of np.asarray(a list of the result of cls._world_to_ego(corner minus
        # ego['position'], ego at...).
        local = np.asarray([
            # Evaluate the result of cls._world_to_ego(corner minus ego at 'position', ego at 'heading_radians')
            # as part of the enclosing expression.
            cls._world_to_ego(
                # Supply corner minus ego at 'position' to cls._world_to_ego.
                corner - ego["position"], ego["heading_radians"]
            # Evaluate world_corners as part of the enclosing expression.
            ) for corner in world_corners
        ])
        # If the sensor origin lies inside this convex box, it occupies every
        # bearing. Use the polygon edges rather than its axis-aligned bounds.
        # Set cross_products to an empty list.
        cross_products = []
        # Iterate over index/value pairs from local, binding each item to (index, corner).
        for index, corner in enumerate(local):
            # Set next_corner to local at (index + 1) % len(local).
            next_corner = local[(index + 1) % len(local)]
            # Set edge to next_corner minus corner.
            edge = next_corner - corner
            # Set to_origin to the negative of corner.
            to_origin = -corner
            # Append edge at 0 multiplied by to_origin at 1 minus edge at 1 multiplied by to_origin at 0 to
            # cross_products.
            cross_products.append(
                # Supply edge at 0 multiplied by to_origin at 1 minus edge at 1 multiplied by to_origin at 0 to
                # cross_products.append.
                edge[0] * to_origin[1] - edge[1] * to_origin[0]
            )
        # Run this branch when whether every item is true in a lazy sequence of value is at least -cls._EPSILON
        # for value in cross_products or whether every item is true in a lazy sequence of value is at most
        # cls._EPSILON for value in cross_products.
        if (all(value >= -cls._EPSILON for value in cross_products)
                # Evaluate whether every item is true in a lazy sequence of value is at most cls._EPSILON for
                # value in cross_products as part of the enclosing expression.
                or all(value <= cls._EPSILON for value in cross_products)):
            # Return a list containing a tuple containing the negative of math.pi, math.pi to the caller.
            return [(-math.pi, math.pi)]
        # Set angles to the result of np.mod(the result of np.arctan2(local at (:, 1), local at (:, 0)), 2.0
        # multiplied by math.pi).
        angles = np.mod(np.arctan2(local[:, 1], local[:, 0]), 2.0 * math.pi)
        # Call angles.sort with the supplied arguments.
        angles.sort()
        # Set circular to the result of np.concatenate(a tuple containing angles, a list containing angles[0] plus
        # 2.0 * math.pi).
        circular = np.concatenate((angles, [angles[0] + 2.0 * math.pi]))
        # Set gap_index to an integer built from the result of np.argmax(the result of np.diff(circular)).
        gap_index = int(np.argmax(np.diff(circular)))
        # Set start to circular at gap_index + 1.
        start = circular[gap_index + 1]
        # Set end to circular at gap_index plus 2.0 multiplied by math.pi.
        end = circular[gap_index] + 2.0 * math.pi
        # Set start to start plus math.pi modulo 2.0 multiplied by math.pi minus math.pi.
        start = ((start + math.pi) % (2.0 * math.pi)) - math.pi
        # Set span to a floating-point number built from end minus circular at gap_index + 1.
        span = float(end - circular[gap_index + 1])
        # Set finish to start plus span.
        finish = start + span
        # Run this branch when finish is at most math.pi plus cls._EPSILON.
        if finish <= math.pi + cls._EPSILON:
            # Return a list containing a tuple containing a floating-point number built from start, the minimum of
            # a floating-point number built... to the caller.
            return [(float(start), min(float(finish), math.pi))]
        # Return a list containing a tuple containing a floating-point number built from start, math.pi, a tuple
        # containing the negative of... to the caller.
        return [(float(start), math.pi),
                # Include a tuple containing the negative of math.pi, a floating-point number built from finish
                # minus 2.0 multiplied by math.pi in this list.
                (-math.pi, float(finish - 2.0 * math.pi))]

    # Fov intervals using the inputs and processing steps below.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _fov_intervals(self):
        # Run this branch when self.sensor_fov_degrees is at least 360.0 minus self._EPSILON.
        if self.sensor_fov_degrees >= 360.0 - self._EPSILON:
            # Return a list containing a tuple containing the negative of math.pi, math.pi to the caller.
            return [(-math.pi, math.pi)]
        # Set half to the result of math.radians(self.sensor_fov_degrees) divided by 2.0.
        half = math.radians(self.sensor_fov_degrees) / 2.0
        # Return a list containing a tuple containing the negative of half, half to the caller.
        return [(-half, half)]

    # Compatibility helper for testing a point bearing, not a vehicle box.
    # Input bearing: the supplied bearing.
    # Output: a Boolean built from the result of self._intersect_intervals(a list containing
    # (math.atan2(math.sin(bearing), math.cos(bearing)),) multiplied by 2, the...).
    def _is_inside_fov(self, bearing):
        """Compatibility helper for testing a point bearing, not a vehicle box."""
        # Return a Boolean built from the result of self._intersect_intervals(a list containing
        # (math.atan2(math.sin(bearing), math.cos(bearing)),) multiplied by 2, the...) to the caller.
        return bool(self._intersect_intervals(
            # Supply a list containing a tuple containing the result of math.atan2(math.sin(bearing),
            # math.cos(bearing)) multiplied by 2 to self._intersect_intervals.
            [(math.atan2(math.sin(bearing), math.cos(bearing)),) * 2],
            # Supply include_points as True.
            self._fov_intervals(), include_points=True,
        ))

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Intersect intervals using the inputs and processing steps below.
    # Input first: the supplied first.
    # Input second: the supplied second.
    # Input include_points: the supplied include points.
    # Output: the result of cls._merge_intervals(intersections).
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _intersect_intervals(cls, first, second, include_points=False):
        # Set intersections to an empty list.
        intersections = []
        # Iterate over first, binding each item to (first_start, first_end).
        for first_start, first_end in first:
            # Iterate over second, binding each item to (second_start, second_end).
            for second_start, second_end in second:
                # Set start to the maximum of first_start, second_start.
                start = max(first_start, second_start)
                # Set end to the minimum of first_end, second_end.
                end = min(first_end, second_end)
                # Run this branch when end is greater than start plus cls._EPSILON or include_points and end is at
                # least start minus cls._EPSILON.
                if end > start + cls._EPSILON or (
                    # Evaluate include_points and end is at least start minus cls._EPSILON as part of the
                    # enclosing expression.
                    include_points and end >= start - cls._EPSILON
                ):
                    # Append a tuple containing start, end to intersections.
                    intersections.append((start, end))
        # Return the result of cls._merge_intervals(intersections) to the caller.
        return cls._merge_intervals(intersections)

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Merge intervals using the inputs and processing steps below.
    # Input intervals: the supplied intervals.
    # Output: a list of a tuple containing a floating-point number built from start, a floating-point number built
    # from end for (start, end) in merged.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _merge_intervals(cls, intervals):
        # Set merged to an empty list.
        merged = []
        # Iterate over the sorted values from intervals, binding each item to (start, end).
        for start, end in sorted(intervals):
            # Run this branch when end is less than start.
            if end < start:
                # Skip the rest of this loop iteration and process the next item.
                continue
            # Run this branch when the negation of merged or start is greater than merged[-1] at 1 plus
            # cls._EPSILON.
            if not merged or start > merged[-1][1] + cls._EPSILON:
                # Append a list containing start, end to merged.
                merged.append([start, end])
            # Run this alternative branch when the preceding branch does not apply.
            else:
                # Set merged[-1][1] to the maximum of merged[-1] at 1, end.
                merged[-1][1] = max(merged[-1][1], end)
        # Return a list of a tuple containing a floating-point number built from start, a floating-point number
        # built from end for (start, end) in merged to the caller.
        return [(float(start), float(end)) for start, end in merged]

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Interval length using the inputs and processing steps below.
    # Input intervals: the supplied intervals.
    # Output: the sum of a lazy sequence of the maximum of 0.0, end minus start for (start, end) in the result of
    # cls._merge_intervals(intervals).
    def _interval_length(cls, intervals):
        # Return the sum of a lazy sequence of the maximum of 0.0, end minus start for (start, end) in the result
        # of cls._merge_intervals(intervals) to the caller.
        return sum(max(0.0, end - start) for start, end in
                   # Evaluate the result of cls._merge_intervals(intervals) as part of the enclosing expression.
                   cls._merge_intervals(intervals))

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Interval fraction using the inputs and processing steps below.
    # Input visible: the supplied visible.
    # Input total: the supplied total.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _interval_fraction(cls, visible, total):
        # Set denominator to the result of cls._interval_length(total).
        denominator = cls._interval_length(total)
        # Run this branch when denominator is at most cls._EPSILON.
        if denominator <= cls._EPSILON:
            # Return 1.0 to the caller.
            return 1.0
        # Return the result of cls._clamp_fraction(the result of cls._interval_length(visible) divided by
        # denominator) to the caller.
        return cls._clamp_fraction(cls._interval_length(visible) / denominator)

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Calculate visible fraction using the inputs and processing steps below.
    # Input intervals: the supplied intervals.
    # Input covered: the supplied covered.
    # Output: return the value selected by the matching return branch below.
    # Processing: select branches using the stated conditions.
    def _calculate_visible_fraction(cls, intervals, covered):
        # Set merged_intervals to the result of cls._merge_intervals(intervals).
        merged_intervals = cls._merge_intervals(intervals)
        # Set merged_covered to the result of cls._merge_intervals(covered).
        merged_covered = cls._merge_intervals(covered)
        # Set total to the result of cls._interval_length(merged_intervals).
        total = cls._interval_length(merged_intervals)
        # Run this branch when total is at most cls._EPSILON.
        if total <= cls._EPSILON:
            # Return 1.0 to the caller.
            return 1.0
        # Set hidden to the result of cls._interval_length(the result of
        # cls._intersect_intervals(merged_intervals, merged_covered)).
        hidden = cls._interval_length(
            # Supply the result of cls._intersect_intervals(merged_intervals, merged_covered) to
            # cls._interval_length.
            cls._intersect_intervals(merged_intervals, merged_covered)
        )
        # Return the result of cls._clamp_fraction(total minus hidden divided by total) to the caller.
        return cls._clamp_fraction((total - hidden) / total)

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Clamp fraction using the inputs and processing steps below.
    # Input value: the supplied value.
    # Output: the minimum of 1.0, the maximum of 0.0, a floating-point number built from value.
    def _clamp_fraction(value):
        # Return the minimum of 1.0, the maximum of 0.0, a floating-point number built from value to the caller.
        return min(1.0, max(0.0, float(value)))

    # Apply staticmethod as a decorator to configure the following definition.
    @staticmethod
    # Context fields using the inputs and processing steps below.
    # Input state: the state read or updated by this operation.
    # Output: a dictionary of key mapped to state at key for key in a tuple containing the text 'lane_id', the
    # text 'lane_position', the text 'lane_length', the text 'road_id', the text...; retain...
    def _context_fields(state):
        # Return a dictionary of key mapped to state at key for key in a tuple containing the text 'lane_id', the
        # text 'lane_position', the text 'lane_length', the text 'road_id', the text...; retain entries satisfying
        # key belongs to state to the caller.
        return {key: state[key] for key in (
            "lane_id", "lane_position", "lane_length", "road_id",
            "max_acceleration_mps2", "comfortable_deceleration_mps2",
            "emergency_deceleration_mps2", "max_speed_mps",
        # Evaluate key belongs to state as part of the enclosing expression.
        ) if key in state}

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Make ego localization using the inputs and processing steps below.
    # Input object_id: the supplied object id.
    # Input state: the state read or updated by this operation.
    # Input timestamp: the supplied timestamp.
    # Input profile: the supplied profile.
    # Output: result.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _make_ego_localization(cls, object_id, state, timestamp, profile):
        # Set velocity to the result of cls._velocity_vector(state at 'speed', state at 'heading_radians').
        velocity = cls._velocity_vector(state["speed"], state["heading_radians"])
        # Set result to a dictionary containing object_id, observation_type, position, measured_position_world,
        # speed,...
        result = {
            # Store object_id under 'object_id'.
            "object_id": object_id,
            "observation_type": "EGO_LOCALIZATION",
            # Store a tuple built from state at 'position' under 'position'.
            "position": tuple(state["position"]),
            # Store a tuple built from state at 'position' under 'measured_position_world'.
            "measured_position_world": tuple(state["position"]),
            # Store state at 'speed' under 'speed'.
            "speed": state["speed"],
            # Store state at 'heading_radians' under 'heading_radians'.
            "heading_radians": state["heading_radians"],
            # Store a tuple built from velocity under 'velocity_world'.
            "velocity_world": tuple(velocity),
            # Store a tuple containing 0.0, 0.0 under 'relative_position_ego'.
            "relative_position_ego": (0.0, 0.0),
            # Store a tuple containing 0.0, 0.0 under 'relative_velocity_ego'.
            "relative_velocity_ego": (0.0, 0.0),
            # Store 0.0 under 'range'.
            # Store 0.0 under 'distance'.
            # Store 0.0 under 'bearing_radians'.
            "range": 0.0, "distance": 0.0, "bearing_radians": 0.0,
            # Store timestamp under 'measurement_timestamp'.
            "measurement_timestamp": timestamp,
            # Store timestamp under 'available_timestamp'.
            # Store timestamp under 'timestamp'.
            "available_timestamp": timestamp, "timestamp": timestamp,
            "detection_status": "SELF_LOCALIZATION",
            # Store profile under 'perception_profile'.
            "perception_profile": profile,
            "localization_profile": "PERFECT_SUMO_LOCALIZATION",
        }
        # Iterate over a tuple containing the text 'length', the text 'width', binding each item to field.
        for field in ("length", "width"):
            # Run this branch when field from state; use None if absent is a different object from None.
            if state.get(field) is not None:
                # Set result[field] to state at field.
                result[field] = state[field]
        # Update result with the supplied entries.
        result.update(cls._context_fields(state))
        # Return result to the caller.
        return result

    # Apply classmethod as a decorator to configure the following definition.
    @classmethod
    # Make object detection using the inputs and processing steps below.
    # Input candidate: the supplied candidate.
    # Input timestamp: the supplied timestamp.
    # Input fov_fraction: the supplied fov fraction.
    # Input occlusion_fraction: the supplied occlusion fraction.
    # Input visible_fraction: the supplied visible fraction.
    # Output: result.
    # Processing: iterate over the relevant records, then select branches using the stated conditions.
    def _make_object_detection(cls, candidate, timestamp, fov_fraction,
                               # Declare occlusion_fraction, visible_fraction as input parameters.
                               occlusion_fraction, visible_fraction):
        # Set state to candidate at 'state'.
        state = candidate["state"]
        # Set velocity to the result of cls._velocity_vector(state at 'speed', state at 'heading_radians').
        velocity = cls._velocity_vector(state["speed"], state["heading_radians"])
        # Set result to a dictionary containing object_id, observation_type, position, measured_position_world,
        # speed,...
        result = {
            # Store candidate at 'object_id' under 'object_id'.
            "object_id": candidate["object_id"],
            "observation_type": "OBJECT_DETECTION",
            # Store a tuple built from state at 'position' under 'position'.
            "position": tuple(state["position"]),
            # Store a tuple built from state at 'position' under 'measured_position_world'.
            "measured_position_world": tuple(state["position"]),
            # Store state at 'speed' under 'speed'.
            "speed": state["speed"],
            # Store state at 'heading_radians' under 'heading_radians'.
            "heading_radians": state["heading_radians"],
            # Store a tuple built from velocity under 'velocity_world'.
            "velocity_world": tuple(velocity),
            # Store a tuple built from candidate at 'relative_position' under 'relative_position_ego'.
            "relative_position_ego": tuple(candidate["relative_position"]),
            # Store a tuple built from candidate at 'relative_velocity' under 'relative_velocity_ego'.
            "relative_velocity_ego": tuple(candidate["relative_velocity"]),
            # Store candidate at 'range' under 'range'.
            # Store candidate at 'range' under 'distance'.
            "range": candidate["range"], "distance": candidate["range"],
            # Store candidate at 'bearing' under 'bearing_radians'.
            "bearing_radians": candidate["bearing"],
            # Store the result of cls._clamp_fraction(fov_fraction) under 'fov_visible_fraction'.
            "fov_visible_fraction": cls._clamp_fraction(fov_fraction),
            # Store the result of cls._clamp_fraction(occlusion_fraction) under 'occlusion_visible_fraction'.
            "occlusion_visible_fraction": cls._clamp_fraction(
                # Supply occlusion_fraction to cls._clamp_fraction.
                occlusion_fraction
            ),
            # Store the result of cls._clamp_fraction(visible_fraction) under 'visible_fraction'.
            "visible_fraction": cls._clamp_fraction(visible_fraction),
            # Store timestamp under 'measurement_timestamp'.
            "measurement_timestamp": timestamp,
            # Store timestamp under 'available_timestamp'.
            # Store timestamp under 'timestamp'.
            "available_timestamp": timestamp, "timestamp": timestamp,
            "detection_status": "DETECTED",
            # Store candidate at 'profile' under 'perception_profile'.
            "perception_profile": candidate["profile"],
        }
        # Iterate over a tuple containing the text 'length', the text 'width', binding each item to field.
        for field in ("length", "width"):
            # Run this branch when field from state; use None if absent is a different object from None.
            if state.get(field) is not None:
                # Set result[field] to state at field.
                result[field] = state[field]
        # Update result with the supplied entries.
        result.update(cls._context_fields(state))
        # Return result to the caller.
        return result
