#!/usr/bin/env python3
"""
Test script to verify SUMO project setup and dependencies
"""

import os
import sys

def test_project_structure():
    """Test if all required files and directories exist"""
    print("=== Testing Project Structure ===")
    
    required_dirs = ['networks', 'routes', 'scripts', 'outputs']
    required_files = [
        'networks/unsignalized_intersection.net.xml',
        'routes/two_vehicle_routes.rou.xml',
        'scripts/run_fcfs_baseline.py',
        'unsignalized_intersection.sumocfg'
    ]
    
    # Test directories
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ Directory exists: {dir_name}/")
        else:
            print(f"✗ Directory missing: {dir_name}/")
    
    # Test files
    for file_name in required_files:
        if os.path.exists(file_name):
            print(f"✓ File exists: {file_name}")
        else:
            print(f"✗ File missing: {file_name}")

def test_python_imports():
    """Test if required Python modules can be imported"""
    print("\n=== Testing Python Imports ===")
    
    try:
        import traci
        print("✓ traci module imported successfully")
    except ImportError:
        print("✗ traci module not found")
        print("  Please install SUMO and ensure traci is in your Python path")
        return False
    
    return True

def test_sumo_installation():
    """Test if SUMO is available in system PATH"""
    print("\n=== Testing SUMO Installation ===")
    
    import subprocess
    
    try:
        # Try to run sumo --version
        result = subprocess.run(['sumo', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ SUMO is available in PATH")
            print(f"  Version: {result.stdout.strip()}")
        else:
            print("✗ SUMO not found in PATH")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ SUMO not found in PATH")
        print("  Please add SUMO installation directory to system PATH")
        return False
    
    try:
        # Try to run sumo-gui --version
        result = subprocess.run(['sumo-gui', '--version'], 
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✓ SUMO-GUI is available in PATH")
        else:
            print("✗ SUMO-GUI not found in PATH")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("✗ SUMO-GUI not found in PATH")
    
    return True

def main():
    """Run all tests"""
    print("SUMO Project Setup Test")
    print("=" * 40)
    
    # Test project structure
    test_project_structure()
    
    # Test Python imports
    traci_ok = test_python_imports()
    
    # Test SUMO installation
    sumo_ok = test_sumo_installation()
    
    print("\n=== Test Summary ===")
    if traci_ok and sumo_ok:
        print("✓ All tests passed! Project is ready to run.")
        print("\nTo start the simulation, run:")
        print("python scripts/run_fcfs_baseline.py")
    else:
        print("✗ Some tests failed. Please fix the issues above.")
        print("\nTroubleshooting tips:")
        print("1. Install SUMO from https://sumo.dlr.de/wiki/Downloads")
        print("2. Add SUMO to your system PATH")
        print("3. Ensure traci module is available in Python")

if __name__ == "__main__":
    main()
