"""Read-only presentation lifecycle, independent of admission and trip counts."""
# Import math for use in this module.
import math

# Import SIM_TIME_STEP from config for the operations below.
from config import SIM_TIME_STEP
# Import sumo_euler_comfortable_brake_gap from negotiation_execution.controller for the operations below.
from negotiation_execution.controller import sumo_euler_comfortable_brake_gap


# Define IntersectionPresentation to group the state and operations declared below.
# Instances expose the attributes and methods implemented in this class.
class IntersectionPresentation:
    # Initialize the instance attributes and collaborators used by the operations below.
    # Output: no explicit value; normal completion returns None.
    def __init__(self):
        # Set self.run to None.
        self.run = None
        # Set self.entry_stage to an empty set.
        self.entry_stage = set()
        # Set self.exited to an empty set.
        self.exited = set()

    # Reset for using the inputs and processing steps below.
    # Input run: the supplied run.
    # Output: no explicit value; normal completion returns None.
    # Processing: select branches using the stated conditions.
    def reset_for(self, run):
        # Run this branch when run differs from self.run.
        if run != self.run:
            # Set self.run to run.
            self.run = run
            # Clear the stored entries in self.entry_stage.
            self.entry_stage.clear()
            # Clear the stored entries in self.exited.
            self.exited.clear()

    # Never write physical state or decisions; unknown geometry stays visible.
    # Input vehicle: the supplied vehicle.
    # Input physical: the supplied physical.
    # Input decision: the supplied decision.
    # Input geometry: the supplied geometry.
    # Input pending: the supplied pending.
    # Output: a dictionary built from the supplied values.
    # Processing: select branches using the stated conditions.
    def classify(self, vehicle, physical, decision, geometry, *, pending=False):
        """Never write physical state or decisions; unknown geometry stays visible."""
        # Set ego to vehicle at 'id'.
        ego = vehicle['id']
        # Set lane to 'lane_id' from (physical or {}); use None if absent.
        lane = (physical or {}).get('lane_id')
        # Set lanes to 'presentation_lanes' from geometry; use an empty dictionary if absent.
        lanes = geometry.get('presentation_lanes', {})
        # Set kind to lane from lanes; use None if absent.
        kind = lanes.get(lane)
        # Set distance to None.
        distance = None
        # Set envelope to None.
        envelope = None
        # Run this branch when kind equals the text 'incoming'.
        if kind == 'incoming':
            # Set distance to the maximum of 0.0, a floating-point number built from physical at 'lane_length'
            # minus a floating-point number...
            distance = max(0., float(physical['lane_length']) - float(physical['lane_position']))
            # Set decel to 'comfortable_deceleration_mps2' from physical; use None if absent.
            decel = physical.get('comfortable_deceleration_mps2')
            # Run this branch when decel and decel is greater than 0.
            if decel and decel > 0:
                # Set speed to a floating-point number built from physical at 'speed'.
                speed = float(physical['speed'])
                # Actual SUMO braking distance plus one step of travel and own
                # body length. Latching prevents a braking vehicle turning blue.
                # Set envelope to the result of sumo_euler_comfortable_brake_gap(speed, decel, SIM_TIME_STEP) plus
                # speed multiplied by SIM_TIME_STEP plus a floating-point number built from physical at 'length'.
                envelope = sumo_euler_comfortable_brake_gap(speed, decel, SIM_TIME_STEP) + speed * SIM_TIME_STEP + float(physical['length'])
                # Run this branch when distance is at most envelope.
                if distance <= envelope:
                    # Add ego to self.entry_stage.
                    self.entry_stage.add(ego)
        # Run this branch when kind belongs to a set containing the text 'internal', the text 'outgoing'.
        elif kind in {'internal', 'outgoing'}:
            # Add ego to self.entry_stage.
            self.entry_stage.add(ego)
        # Set allowed to decision is a different object from None and decision.permission equals the text
        # 'PERMITTED'.
        allowed = decision is not None and decision.permission == 'PERMITTED'
        # Set held to decision is a different object from None and decision.permission does not belong to a set
        # containing the text 'PERMITTED', the text 'NATIVE_FOLLOWING'.
        held = decision is not None and decision.permission not in {'PERMITTED', 'NATIVE_FOLLOWING'}
        # Set state to the text 'NEGOTIATING' when pending, otherwise the text 'READY' when allowed, otherwise the
        # text 'BLOCKED' when held and ego in self.entry_stage, otherwise the text 'APPROACHING'.
        state = ('NEGOTIATING' if pending else 'READY' if allowed else
                 # Evaluate the text 'BLOCKED' when held and ego belongs to self.entry_stage, otherwise the text
                 # 'APPROACHING' as part of the enclosing expression.
                 'BLOCKED' if held and ego in self.entry_stage else 'APPROACHING')
        # Set rear_clear to a Boolean built from kind equals the text 'outgoing' and a floating-point number built
        # from physical['lane_position'] is greater than a floating-point number built from physical['length'].
        rear_clear = bool(kind == 'outgoing' and
                          # Evaluate a floating-point number built from physical at 'lane_position' is greater
                          # than a floating-point number built from physical at 'length' as part of the enclosing
                          # expression.
                          float(physical['lane_position']) > float(physical['length']))
        # Set region to 'presentation_region' from geometry; use None if absent.
        region = geometry.get('presentation_region')
        # Set outside to False.
        outside = False
        # Run this branch when region.
        if region:
            # Set angle to the result of math.radians(vehicle at 'angle_degrees').
            angle = math.radians(vehicle['angle_degrees'])
            # Set (x, y) to a tuple containing vehicle at 'front_bumper_x', vehicle at 'front_bumper_y'.
            x, y = vehicle['front_bumper_x'], vehicle['front_bumper_y']
            # Set rear to a tuple containing x minus the result of math.sin(angle) multiplied by vehicle at
            # 'length_m', y minus the result of...
            rear = (x - math.sin(angle) * vehicle['length_m'],
                    # Include y minus the result of math.cos(angle) multiplied by vehicle at 'length_m' in this
                    # tuple.
                    y - math.cos(angle) * vehicle['length_m'])
            # Set margin to vehicle at 'width_m' divided by 2.
            margin = vehicle['width_m'] / 2
            # Set (minx, miny, maxx, maxy) to region.
            minx, miny, maxx, maxy = region
            # Whole body beyond the same boundary, not merely its front.
            # Set outside to the maximum of x, rear[0] plus margin is less than minx or the minimum of x, rear[0]
            # minus margin is greater than maxx or the maximum of y, rear[1] plus margin is less than miny or the
            # minimum of y, rear[1] minus margin is greater than maxy.
            outside = (max(x, rear[0]) + margin < minx or min(x, rear[0]) - margin > maxx or
                       # Evaluate the maximum of y, rear at 1 plus margin is less than miny as part of the
                       # enclosing expression.
                       max(y, rear[1]) + margin < miny or min(y, rear[1]) - margin > maxy)
        # Run this branch when rear_clear and outside.
        if rear_clear and outside:
            # Add ego to self.exited.
            self.exited.add(ego)
        # Set visible to ego does not belong to self.exited.
        visible = ego not in self.exited
        # Before first arrival, only include bodies intersecting the fixed scene.
        # Run this branch when kind equals the text 'incoming' and outside and ego does not belong to
        # self.entry_stage.
        if kind == 'incoming' and outside and ego not in self.entry_stage:
            # Set visible to False.
            visible = False
        # Return a dictionary built from the supplied values to the caller.
        return dict(display_state=state, execution_state=state if not pending else 'APPROACHING',
                    # Supply display_stage as the text 'ENTRY_CONTROL' when ego belongs to self.entry_stage,
                    # otherwise the text 'ORDINARY_APPROACH'.
                    display_stage='ENTRY_CONTROL' if ego in self.entry_stage else 'ORDINARY_APPROACH',
                    # Supply presentation_visible as visible.
                    # Supply intersection_rear_cleared as rear_clear.
                    presentation_visible=visible, intersection_rear_cleared=rear_clear,
                    # Supply presentation_exited as ego belongs to self.exited.
                    presentation_exited=ego in self.exited,
                    # Supply entry_boundary_distance_m as distance.
                    # Supply presentation_braking_envelope_m as envelope.
                    entry_boundary_distance_m=distance, presentation_braking_envelope_m=envelope)
