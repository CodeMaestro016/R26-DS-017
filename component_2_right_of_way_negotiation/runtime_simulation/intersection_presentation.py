"""Read-only presentation lifecycle, independent of admission and trip counts."""
import math

from config import SIM_TIME_STEP
from negotiation_execution.controller import sumo_euler_comfortable_brake_gap


class IntersectionPresentation:
    def __init__(self):
        self.run = None
        self.entry_stage = set()
        self.exited = set()

    def reset_for(self, run):
        if run != self.run:
            self.run = run
            self.entry_stage.clear()
            self.exited.clear()

    def classify(self, vehicle, physical, decision, geometry, *, pending=False):
        """Never write physical state or decisions; unknown geometry stays visible."""
        ego = vehicle['id']
        lane = (physical or {}).get('lane_id')
        lanes = geometry.get('presentation_lanes', {})
        kind = lanes.get(lane)
        distance = None
        envelope = None
        if kind == 'incoming':
            distance = max(0., float(physical['lane_length']) - float(physical['lane_position']))
            decel = physical.get('comfortable_deceleration_mps2')
            if decel and decel > 0:
                speed = float(physical['speed'])
                # Actual SUMO braking distance plus one step of travel and own
                # body length. Latching prevents a braking vehicle turning blue.
                envelope = sumo_euler_comfortable_brake_gap(speed, decel, SIM_TIME_STEP) + speed * SIM_TIME_STEP + float(physical['length'])
                if distance <= envelope:
                    self.entry_stage.add(ego)
        elif kind in {'internal', 'outgoing'}:
            self.entry_stage.add(ego)
        allowed = decision is not None and decision.permission == 'PERMITTED'
        held = decision is not None and decision.permission not in {'PERMITTED', 'NATIVE_FOLLOWING'}
        state = ('NEGOTIATING' if pending else 'READY' if allowed else
                 'BLOCKED' if held and ego in self.entry_stage else 'APPROACHING')
        rear_clear = bool(kind == 'outgoing' and
                          float(physical['lane_position']) > float(physical['length']))
        region = geometry.get('presentation_region')
        outside = False
        if region:
            angle = math.radians(vehicle['angle_degrees'])
            x, y = vehicle['front_bumper_x'], vehicle['front_bumper_y']
            rear = (x - math.sin(angle) * vehicle['length_m'],
                    y - math.cos(angle) * vehicle['length_m'])
            margin = vehicle['width_m'] / 2
            minx, miny, maxx, maxy = region
            # Whole body beyond the same boundary, not merely its front.
            outside = (max(x, rear[0]) + margin < minx or min(x, rear[0]) - margin > maxx or
                       max(y, rear[1]) + margin < miny or min(y, rear[1]) - margin > maxy)
        if rear_clear and outside:
            self.exited.add(ego)
        visible = ego not in self.exited
        # Before first arrival, only include bodies intersecting the fixed scene.
        if kind == 'incoming' and outside and ego not in self.entry_stage:
            visible = False
        return dict(display_state=state, execution_state=state if not pending else 'APPROACHING',
                    display_stage='ENTRY_CONTROL' if ego in self.entry_stage else 'ORDINARY_APPROACH',
                    presentation_visible=visible, intersection_rear_cleared=rear_clear,
                    presentation_exited=ego in self.exited,
                    entry_boundary_distance_m=distance, presentation_braking_envelope_m=envelope)
