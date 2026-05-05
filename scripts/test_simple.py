#!/usr/bin/env python3
"""
Simple test script to debug issue
"""

import os
import sys

# Configuration constants
SUMO_CONFIG = "unsignalized_intersection.sumocfg"
FOUR_VEHICLE_CONFIG = "four_vehicle_config.sumocfg"

def main():
    """Main function to test configuration."""
    # Check if configuration file exists
    if not os.path.exists(SUMO_CONFIG):
        print(f"Error: Configuration file '{SUMO_CONFIG}' not found!")
        sys.exit(1)
    
    # Check if four-vehicle config exists
    if not os.path.exists(FOUR_VEHICLE_CONFIG):
        print(f"Error: Four-vehicle configuration file '{FOUR_VEHICLE_CONFIG}' not found!")
        print("Using default configuration instead.")
        config_to_use = SUMO_CONFIG
    else:
        print(f"Using four-vehicle configuration: {FOUR_VEHICLE_CONFIG}")
        config_to_use = FOUR_VEHICLE_CONFIG
    
    print(f"Final config to use: {config_to_use}")

if __name__ == "__main__":
    main()
