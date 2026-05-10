"""
V2V Action Decision Module
Combines model prediction with local awareness for final action decisions.
"""

from typing import Dict


class V2VActionDecision:
    """Decision maker that combines LSTM predictions with local awareness."""
    
    def __init__(self):
        """Initialize the action decision module."""
        pass
    
    def decide_final_action(self, model_prediction: str, confidence: float, awareness: Dict) -> Dict:
        """
        Decide final action based on model prediction and local awareness.
        
        Args:
            model_prediction: Model prediction ("GO", "NEUTRAL", "YIELD")
            confidence: Model confidence score (0-1)
            awareness: Local awareness information
            
        Returns:
            Dictionary with final action decision:
            {
                "final_action": "GO/YIELD/WAIT/RISK",
                "reason": short explanation string,
                "acceleration": float
            }
        """
        # Extract key awareness values
        conflict_count = awareness.get('conflict_count', 0)
        min_eta_gap = awareness.get('min_eta_gap', 100.0)
        right_side_vehicle_present = awareness.get('right_side_vehicle_present', 0)
        ego_distance_to_intersection = awareness.get('ego_distance_to_intersection', 100.0)
        ego_speed = awareness.get('ego_speed', 0.0)
        
        # Decision logic with safety overrides
        
        # High-risk conflict override
        if conflict_count > 0 and min_eta_gap <= 1.0:
            final_action = "YIELD"
            reason = "high_risk_conflict"
            acceleration = -1.5
        
        # Right-side vehicle override in decision zone
        elif right_side_vehicle_present == 1 and ego_distance_to_intersection <= 20:
            final_action = "WAIT"
            reason = "right_side_vehicle_decision_zone"
            acceleration = -2.0 if ego_speed > 1.0 else 0.0
        
        # Normal decision based on model prediction
        else:
            if model_prediction == "GO":
                final_action = "GO"
                reason = "model_go_no_high_risk"
                acceleration = 1.0
            elif model_prediction == "YIELD":
                final_action = "YIELD"
                reason = "model_yield"
                acceleration = -1.5
            elif model_prediction == "NEUTRAL":
                final_action = "WAIT"
                reason = "model_neutral"
                acceleration = -2.0 if ego_speed > 1.0 else 0.0
            else:
                # Unknown prediction - conservative approach
                final_action = "WAIT"
                reason = "unknown_model_prediction"
                acceleration = -2.0 if ego_speed > 1.0 else 0.0
        
        # Additional safety checks
        if ego_distance_to_intersection < 5.0 and ego_speed > 8.0:
            # Too fast approaching intersection
            final_action = "RISK"
            reason = "excessive_speed_approach"
            acceleration = -3.0
        
        return {
            "final_action": final_action,
            "reason": reason,
            "acceleration": acceleration
        }
    
    def get_action_color(self, action: str) -> str:
        """
        Get color code for vehicle based on action.
        
        Args:
            action: Final action string
            
        Returns:
            Color string for SUMO vehicle visualization
        """
        color_map = {
            "GO": "green",
            "YIELD": "orange", 
            "WAIT": "blue",
            "RISK": "red",
            "NEUTRAL": "gray",
            "UNKNOWN": "gray"
        }
        return color_map.get(action, "gray")
    
    def format_decision_log(self, vehicle_id: str, model_prediction: str, confidence: float,
                           awareness: Dict, decision: Dict) -> str:
        """
        Format decision information for logging.
        
        Args:
            vehicle_id: Vehicle identifier
            model_prediction: Model prediction
            confidence: Model confidence
            awareness: Local awareness data
            decision: Final decision
            
        Returns:
            Formatted log string
        """
        nearest_vehicle_id = awareness.get('nearest_vehicle_id', 'None')
        conflict_count = awareness.get('conflict_count', 0)
        min_eta_gap = awareness.get('min_eta_gap', 0.0)
        right_side_vehicle_present = awareness.get('right_side_vehicle_present', 0)
        final_action = decision.get('final_action', 'UNKNOWN')
        reason = decision.get('reason', 'unknown')
        
        return (f"veh={vehicle_id} | nearest={nearest_vehicle_id} | "
                f"model={model_prediction}({confidence:.2f}) | "
                f"conflict={conflict_count} | eta_gap={min_eta_gap:.2f} | "
                f"right_side={right_side_vehicle_present} | "
                f"action={final_action} | reason={reason}")


# Factory function for easy instantiation
def create_v2v_action_decision() -> V2VActionDecision:
    """Create V2VActionDecision instance with default settings."""
    return V2VActionDecision()
