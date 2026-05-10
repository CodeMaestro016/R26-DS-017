"""
Local Awareness Module for V2V SUMO Demo
Calculates local awareness from SUMO live vehicles for decision making.
"""

import math
import traci
from typing import Dict, List, Optional, Tuple


class LocalAwareness:
    """Local awareness calculator for SUMO vehicles."""
    
    def __init__(self, intersection_center: Tuple[float, float] = (0.0, 0.0)):
        """
        Initialize local awareness calculator.
        
        Args:
            intersection_center: (x, y) coordinates of intersection center
        """
        self.intersection_center = intersection_center
        self.interaction_radius = 50.0  # meters
        self.threshold_distance = 35.0   # meters
        self.decision_distance = 20.0    # meters
        self.min_speed_for_eta = 0.1     # m/s
        self.conflict_eta_gap = 1.5      # seconds
    
    def estimate_intersection_center(self) -> Tuple[float, float]:
        """
        Estimate intersection center from network or use fixed center.
        For this demo, we'll use a fixed center for the unsignalized intersection.
        
        Returns:
            (x, y) coordinates of intersection center
        """
        # For the standard unsignalized intersection network
        return (0.0, 0.0)  # Center of the intersection from network file
    
    def get_vehicle_state(self, vehicle_id: str) -> Dict:
        """
        Get basic vehicle state from SUMO.
        
        Args:
            vehicle_id: Vehicle identifier
            
        Returns:
            Dictionary with vehicle state information
        """
        try:
            x, y = traci.vehicle.getPosition(vehicle_id)
            speed = traci.vehicle.getSpeed(vehicle_id)
            angle = traci.vehicle.getAngle(vehicle_id)
            acceleration = traci.vehicle.getAcceleration(vehicle_id)
            
            # Convert angle to radians and calculate heading components
            angle_rad = math.radians(angle)
            heading_sin = math.sin(angle_rad)
            heading_cos = math.cos(angle_rad)
            
            # Calculate signed acceleration (positive = forward, negative = braking)
            signed_acceleration = acceleration if speed > 0.1 else acceleration
            
            return {
                'x': x,
                'y': y,
                'speed': speed,
                'angle': angle,
                'heading_sin': heading_sin,
                'heading_cos': heading_cos,
                'acceleration': acceleration,
                'signed_acceleration': signed_acceleration
            }
        except Exception as e:
            print(f"[AWARENESS] Error getting state for {vehicle_id}: {e}")
            return {
                'x': 0.0, 'y': 0.0, 'speed': 0.0, 'angle': 0.0,
                'heading_sin': 0.0, 'heading_cos': 1.0,
                'acceleration': 0.0, 'signed_acceleration': 0.0
            }
    
    def get_side_from_position(self, x: float, y: float, center_x: float, center_y: float) -> str:
        """
        Determine which side of intersection vehicle is on based on position.
        
        Args:
            x, y: Vehicle position
            center_x, center_y: Intersection center position
            
        Returns:
            Side name: 'NORTH', 'SOUTH', 'EAST', 'WEST', or 'UNKNOWN'
        """
        dx = x - center_x
        dy = y - center_y
        
        # Determine primary direction
        if abs(dx) > abs(dy):
            # East-West dominant
            return 'EAST' if dx > 0 else 'WEST'
        else:
            # North-South dominant
            return 'NORTH' if dy > 0 else 'SOUTH'
    
    def get_right_side_approach(self, approach: str) -> str:
        """
        Get the approach that is to the right of given approach.
        
        Args:
            approach: Current approach ('NORTH', 'SOUTH', 'EAST', 'WEST')
            
        Returns:
            Right-side approach name
        """
        right_side_map = {
            'NORTH': 'EAST',
            'EAST': 'SOUTH',
            'SOUTH': 'WEST',
            'WEST': 'NORTH'
        }
        return right_side_map.get(approach, 'UNKNOWN')
    
    def approximate_path_conflict(self, ego_state: Dict, other_state: Dict) -> bool:
        """
        Approximate if two vehicle paths conflict based on approach/exit.
        
        Args:
            ego_state: Ego vehicle state with approach/exit
            other_state: Other vehicle state with approach/exit
            
        Returns:
            True if paths likely conflict
        """
        ego_approach = ego_state.get('approach', 'UNKNOWN')
        ego_exit = ego_state.get('exit', 'UNKNOWN')
        other_approach = other_state.get('approach', 'UNKNOWN')
        other_exit = other_state.get('exit', 'UNKNOWN')
        
        # Same approach - likely conflict
        if ego_approach == other_approach:
            return True
        
        # Opposite approaches going straight - no conflict
        opposite_pairs = [('NORTH', 'SOUTH'), ('EAST', 'WEST')]
        if (ego_approach, other_approach) in opposite_pairs or (other_approach, ego_approach) in opposite_pairs:
            if ego_exit == other_approach and other_exit == ego_approach:
                return False  # Both going straight through
        
        # Adjacent approaches - likely conflict
        adjacent_pairs = [
            ('NORTH', 'EAST'), ('NORTH', 'WEST'),
            ('SOUTH', 'EAST'), ('SOUTH', 'WEST'),
            ('EAST', 'NORTH'), ('EAST', 'SOUTH'),
            ('WEST', 'NORTH'), ('WEST', 'SOUTH')
        ]
        if (ego_approach, other_approach) in adjacent_pairs or (other_approach, ego_approach) in adjacent_pairs:
            return True
        
        return False
    
    def calculate_distance_to_intersection(self, x: float, y: float, center_x: float, center_y: float) -> float:
        """
        Calculate distance from vehicle to intersection center.
        
        Args:
            x, y: Vehicle position
            center_x, center_y: Intersection center position
            
        Returns:
            Distance in meters
        """
        return math.sqrt((x - center_x)**2 + (y - center_y)**2)
    
    def calculate_eta(self, distance: float, speed: float) -> float:
        """
        Calculate estimated time to arrival at intersection.
        
        Args:
            distance: Distance to intersection (meters)
            speed: Current speed (m/s)
            
        Returns:
            ETA in seconds
        """
        effective_speed = max(speed, self.min_speed_for_eta)
        return distance / effective_speed
    
    def determine_zone(self, distance: float) -> str:
        """
        Determine vehicle zone based on distance to intersection.
        
        Args:
            distance: Distance to intersection (meters)
            
        Returns:
            Zone: 'DECISION', 'THRESHOLD', or 'OUTSIDE'
        """
        if distance <= self.decision_distance:
            return 'DECISION'
        elif distance <= self.threshold_distance:
            return 'THRESHOLD'
        else:
            return 'OUTSIDE'
    
    def estimate_maneuver(self, vehicle_id: str, approach: str, exit_direction: str = None) -> Tuple[str, str]:
        """
        Estimate vehicle maneuver based on route information.
        
        Args:
            vehicle_id: Vehicle identifier
            approach: Current approach direction
            exit_direction: Exit direction if known
            
        Returns:
            Tuple of (maneuver, confidence)
        """
        try:
            # Get vehicle route
            route = traci.vehicle.getRoute(vehicle_id)
            if len(route) < 2:
                return 'UNKNOWN', 'LOW'
            
            # Simple heuristic based on current and next edge
            current_edge = traci.vehicle.getRoadID(vehicle_id)
            
            # For this demo, use simple approach-based estimation
            # In a real implementation, you'd analyze the actual route
            if exit_direction:
                if exit_direction == approach:
                    return 'STRAIGHT', 'MEDIUM'
                elif self._is_left_turn(approach, exit_direction):
                    return 'LEFT_TURN', 'MEDIUM'
                elif self._is_right_turn(approach, exit_direction):
                    return 'RIGHT_TURN', 'MEDIUM'
            
            return 'UNKNOWN', 'LOW'
        except Exception:
            return 'UNKNOWN', 'LOW'
    
    def _is_left_turn(self, approach: str, exit: str) -> bool:
        """Check if this is a left turn."""
        left_turns = {
            ('NORTH', 'WEST'), ('WEST', 'SOUTH'),
            ('SOUTH', 'EAST'), ('EAST', 'NORTH')
        }
        return (approach, exit) in left_turns
    
    def _is_right_turn(self, approach: str, exit: str) -> bool:
        """Check if this is a right turn."""
        right_turns = {
            ('NORTH', 'EAST'), ('EAST', 'SOUTH'),
            ('SOUTH', 'WEST'), ('WEST', 'NORTH')
        }
        return (approach, exit) in right_turns
    
    def build_local_awareness(self, ego_id: str, all_vehicle_ids: List[str]) -> Dict:
        """
        Build comprehensive local awareness for ego vehicle.
        
        Args:
            ego_id: Ego vehicle identifier
            all_vehicle_ids: List of all active vehicle IDs
            
        Returns:
            Dictionary with local awareness information
        """
        # Get intersection center
        center_x, center_y = self.estimate_intersection_center()
        
        # Get ego vehicle state
        ego_state = self.get_vehicle_state(ego_id)
        ego_x, ego_y = ego_state['x'], ego_state['y']
        
        # Calculate ego distance and ETA
        ego_distance = self.calculate_distance_to_intersection(ego_x, ego_y, center_x, center_y)
        ego_eta = self.calculate_eta(ego_distance, ego_state['speed'])
        ego_zone = self.determine_zone(ego_distance)
        
        # Determine ego approach and estimate maneuver
        ego_approach = self.get_side_from_position(ego_x, ego_y, center_x, center_y)
        ego_maneuver, ego_maneuver_confidence = self.estimate_maneuver(ego_id, ego_approach)
        
        # Initialize awareness values
        awareness = {
            'context_vehicle_count': 0,
            'nearest_vehicle_id': None,
            'nearest_vehicle_distance': 100.0,
            'nearest_vehicle_rel_speed': 0.0,
            'min_eta_gap': 100.0,
            'conflict_count': 0,
            'min_conflict_eta': 100.0,
            'right_side_vehicle_present': 0,
            'right_side_vehicle_eta': 100.0,
            'right_side_vehicle_distance': 100.0,
            'ego_distance_to_intersection': ego_distance,
            'ego_eta': ego_eta,
            'ego_zone': ego_zone,
            'ego_approach': ego_approach,
            'ego_exit': 'UNKNOWN',  # Would need route analysis for accurate exit
            'ego_maneuver': ego_maneuver,
            'ego_maneuver_confidence': ego_maneuver_confidence,
            'ego_dx_to_center': center_x - ego_x,
            'ego_dy_to_center': center_y - ego_y
        }
        
        # Get right-side approach for ego
        right_side_approach = self.get_right_side_approach(ego_approach)
        
        # Analyze other vehicles
        nearest_distance = float('inf')
        conflicts = []
        
        for other_id in all_vehicle_ids:
            if other_id == ego_id:
                continue
            
            other_state = self.get_vehicle_state(other_id)
            other_x, other_y = other_state['x'], other_state['y']
            
            # Calculate distance to ego
            distance_to_ego = math.sqrt((other_x - ego_x)**2 + (other_y - ego_y)**2)
            
            # Check if within interaction radius
            if distance_to_ego > self.interaction_radius:
                continue
            
            # Update context vehicle count
            awareness['context_vehicle_count'] += 1
            
            # Update nearest vehicle
            if distance_to_ego < nearest_distance:
                nearest_distance = distance_to_ego
                awareness['nearest_vehicle_id'] = other_id
                awareness['nearest_vehicle_distance'] = distance_to_ego
                awareness['nearest_vehicle_rel_speed'] = other_state['speed'] - ego_state['speed']
            
            # Calculate other vehicle distance and ETA
            other_distance = self.calculate_distance_to_intersection(other_x, other_y, center_x, center_y)
            other_eta = self.calculate_eta(other_distance, other_state['speed'])
            
            # Calculate ETA gap
            eta_gap = abs(ego_eta - other_eta)
            awareness['min_eta_gap'] = min(awareness['min_eta_gap'], eta_gap)
            
            # Determine other vehicle approach
            other_approach = self.get_side_from_position(other_x, other_y, center_x, center_y)
            
            # Check for right-side vehicle
            if other_approach == right_side_approach and other_distance <= self.threshold_distance:
                awareness['right_side_vehicle_present'] = 1
                awareness['right_side_vehicle_eta'] = min(awareness['right_side_vehicle_eta'], other_eta)
                awareness['right_side_vehicle_distance'] = min(awareness['right_side_vehicle_distance'], other_distance)
            
            # Check for conflict
            if eta_gap <= self.conflict_eta_gap:
                # Approximate path conflict
                ego_full_state = {'approach': ego_approach, 'exit': awareness['ego_exit']}
                other_full_state = {'approach': other_approach, 'exit': 'UNKNOWN'}
                
                if self.approximate_path_conflict(ego_full_state, other_full_state):
                    conflicts.append({'vehicle_id': other_id, 'eta': other_eta, 'distance': other_distance})
                    awareness['min_conflict_eta'] = min(awareness['min_conflict_eta'], other_eta)
        
        # Update conflict count
        awareness['conflict_count'] = len(conflicts)
        
        return awareness


# Factory function for easy instantiation
def create_local_awareness() -> LocalAwareness:
    """Create LocalAwareness instance with default settings."""
    return LocalAwareness()
