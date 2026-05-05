# SUMO Unsignalized Intersection Simulation

This project implements a simple SUMO (Simulation of Urban Mobility) simulation for autonomous vehicle right-of-way negotiation at unsignalized intersections using a First-Come-First-Serve (FCFS) baseline algorithm.

## Project Structure

```
Research-SUMO/
├── networks/
│   └── unsignalized_intersection.net.xml    # Intersection network definition
├── routes/
│   └── two_vehicle_routes.rou.xml           # Vehicle routes and types
├── scripts/
│   └── run_fcfs_baseline.py                 # Python TraCI control script
├── outputs/                                 # Simulation output files
├── unsignalized_intersection.sumocfg        # SUMO configuration file
└── README.md                                # This file
```

## Scenario Description

The simulation creates a simple four-way unsignalized intersection with:

- **Vehicle A**: Starts from West, travels East (priority/assertive vehicle)
- **Vehicle B**: Starts from South, travels North (yielding vehicle)
- Both vehicles arrive near the intersection at similar times
- FCFS algorithm determines which vehicle gets priority

## Features

### Intersection Design
- Four-way unsignalized intersection (no traffic lights)
- One lane per direction
- Speed limit: 13.9 m/s (~50 km/h)
- 50m road segments connecting to the intersection

### FCFS Control Algorithm
- **Control Zone**: 15m radius from intersection center
- **Priority Logic**: First vehicle to enter control zone gets priority
- **Speed Control**:
  - Priority vehicle: Normal speed (13.9 m/s)
  - Yielding vehicle: Reduced speed (2.0 m/s, or 0.5 m/s when very close)

### Python TraCI Script Features
- Real-time vehicle tracking and speed control
- Distance-based intersection detection
- Priority assignment based on arrival time
- Comprehensive status output and logging
- Error handling and graceful shutdown

## Prerequisites

### 1. Install SUMO
Download and install SUMO from the official website:
- **Windows**: https://sumo.dlr.de/wiki/Downloads
- **Recommended version**: SUMO 1.16.0 or later

### 2. Python Requirements
Install required Python packages:
```bash
pip install traci
```

Note: `traci` is included with SUMO installation. If the import fails, add SUMO's Python tools to your Python path.

### 3. Environment Setup (if needed)
Add SUMO to your system PATH:
- Windows: Add SUMO installation directory to System PATH
- The `traci` module is usually located at: `SUMO_INSTALL_DIR/tools/`

## Running the Simulation

### Method 1: Run with Python Control Script (Recommended)

1. Open a terminal/command prompt
2. Navigate to the project directory:
   ```bash
   cd Research-SUMO
   ```
3. Run the Python control script:
   ```bash
   python scripts/run_fcfs_baseline.py
   ```

The script will:
- Start SUMO-GUI automatically
- Load the network and routes
- Apply FCFS control logic
- Display real-time status information
- Save output files to the `outputs/` directory

### Method 2: Run SUMO-GUI Directly

1. Open a terminal/command prompt
2. Navigate to the project directory:
   ```bash
   cd Research-SUMO
   ```
3. Start SUMO-GUI with the configuration file:
   ```bash
   sumo-gui -c unsignalized_intersection.sumocfg
   ```

This will run the simulation without the Python FCFS control (vehicles use default SUMO behavior).

### Method 3: Run Headless (No GUI)

For automated testing or batch runs:

1. Modify the Python script:
   - Change `SUMO_BINARY = "sumo-gui"` to `SUMO_BINARY = "sumo"`
2. Run the script as in Method 1

OR run directly:
```bash
sumo -c unsignalized_intersection.sumocfg
```

## Expected Output

When running with the Python control script, you should see output like:

```
=== Starting FCFS Baseline Simulation ===
Intersection: Unsignalized four-way intersection
Control Logic: First-Come-First-Serve (FCFS)
Control Zone Radius: 15.0m
Priority Vehicle Speed: 13.9m/s
Yielding Vehicle Speed: 2.0m/s

Starting SUMO: sumo-gui -c unsignalized_intersection.sumocfg --remote-port 8813
TraCI connection established successfully!

=== Simulation Time: 1.0s ===
  vehicle_A: speed=13.9m/s, distance=35.2m
  vehicle_B: speed=13.9m/s, distance=33.8m

=== Simulation Time: 2.0s ===
  vehicle_A: speed=13.9m/s, distance=21.3m [PRIORITY]
  vehicle_B: speed=13.9m, distance=19.9m [YIELDING]
  Priority: vehicle_A
  Yielding: vehicle_B
  [FCFS] vehicle_A gets priority (arrived at 2.0s)
  [FCFS] vehicle_B must yield (arrived at 2.0s)

=== Simulation Complete ===
All vehicles have completed their routes.
```

## Output Files

The simulation generates output files in the `outputs/` directory:

- `simulation_output.xml`: Detailed simulation data
- `tripinfo_output.xml`: Trip summary information for each vehicle

## Customization

### Modifying Vehicle Behavior
Edit `routes/two_vehicle_routes.rou.xml`:
- Change departure times to test different scenarios
- Adjust vehicle types and parameters
- Add more vehicles or routes

### Adjusting Control Parameters
Edit `scripts/run_fcfs_baseline.py`:
- `CONTROL_ZONE_RADIUS`: Distance from intersection to trigger control
- `PRIORITY_VEHICLE_SPEED`: Speed for priority vehicles
- `YIELDING_VEHICLE_SPEED`: Speed for yielding vehicles
- `STOP_SPEED`: Near-stop speed for vehicles very close to intersection

### Modifying Intersection Design
Edit `networks/unsignalized_intersection.net.xml`:
- Change road lengths and speeds
- Add more lanes or complex intersections
- Modify junction types and connections

## Troubleshooting

### Common Issues

1. **"traci module not found"**
   - Ensure SUMO is properly installed
   - Add SUMO's tools directory to Python path
   - Install SUMO's Python tools: `pip install sumo`

2. **"Configuration file not found"**
   - Ensure you're running the script from the project root directory
   - Check that `unsignalized_intersection.sumocfg` exists

3. **SUMO doesn't start**
   - Verify SUMO installation and PATH configuration
   - Try running SUMO manually first to test installation

4. **Vehicles don't move**
   - Check network file for connection errors
   - Verify route file matches network edge IDs
   - Ensure vehicle types have appropriate parameters

### Debug Mode
To enable debug output, modify the script to print additional information:
```python
# Add to print_simulation_status() function
print(f"  Debug: Vehicles in zone: {len(vehicles_in_zone)}")
print(f"  Debug: Priority vehicle: {priority_vehicle}")
```

## Next Steps for Research

This baseline simulation provides a foundation for more advanced research:

1. **Enhanced Algorithms**: Implement more sophisticated right-of-way negotiation
2. **Multiple Vehicles**: Test with more complex traffic scenarios
3. **Performance Metrics**: Add detailed data collection and analysis
4. **Machine Learning**: Use this simulation as a training environment
5. **Validation**: Compare with real-world intersection data

## References

- SUMO Documentation: https://sumo.dlr.de/wiki/
- TraCI API: https://sumo.dlr.de/wiki/TraCI
- SUMO Tutorials: https://sumo.dlr.de/wiki/Tutorials

## License

This project is for research purposes. Feel free to modify and use for academic research on autonomous vehicle intersection negotiation.
