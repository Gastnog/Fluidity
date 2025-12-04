# Step 1: Add modules for library and function access
import os
import sys
import csv

# Step 2: Path to SUMO (SUMO_HOME)
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Please declare environment variable 'SUMO_HOME'")

# Step 3: Add the Traci module for libraries and functions
import traci  # Information Network

# Step 4: Define Sumo configuration
Sumo_config = [
    'sumo-gui',
    '-c', 'Traci1.sumocfg',
    '--step-length', '0.1',
    '--delay', '1000',
    '--lateral-resolution', '0.1'
]

# Step 5: Connection between SUMO and Traci
traci.start(Sumo_config)

# Step 6: Define Variables
data_to_export = []

# Define CSV header for reuse
CSV_HEADER = [
    "t (s)",
    "acceleration (m/s^2)",
    "veh_id",
    "position_x (m)",
    "position_y (m)",
    "vitesse (m/s)"
]

# CSV header added to the data array
data_to_export.append(CSV_HEADER)


# Step 7: Define Functions
def update_data():
    global data_to_export

    current_time = traci.simulation.getTime()
    current_vehicle_ids = traci.vehicle.getIDList()

    # Iterate over each vehicle and collect data
    for veh_id in current_vehicle_ids:
        speed = traci.vehicle.getSpeed(veh_id)
        position = traci.vehicle.getPosition(veh_id)
        acceleration = traci.vehicle.getAcceleration(veh_id)

        # --- MODIFICATION: Display separated by commas (CSV-like) ---
        print(
            f"{current_time:.1f},{acceleration:.2f},{veh_id},{position[0]:.2f},{position[1]:.2f},{speed:.2f}"
        )
        # --- END MODIFICATION ---

        # Prepare the data row for the CSV (Order: T, a, ID, Pos X, Pos Y, Speed)
        data_row = [
            current_time,
            acceleration,
            veh_id,
            position[0],
            position[1],
            speed
        ]
        data_to_export.append(data_row)


# Step 8: Continue the simulation as long as there are vehicles (Natural Stop)

# --- MODIFICATION: Display the header in the console with commas ---
header_console = (
    "T (s),a (m/s²),vehID,Pos X (m),Pos Y (m),V (m/s)"
)
print("--- SIMULATION START (CSV-like Output) ---")
print(header_console)
# --- END MODIFICATION ---

while traci.simulation.getMinExpectedNumber() > 0:
    traci.simulationStep()  # Move simulation forward 1 step
    update_data()  # Call the function to update and store the data

print("\n✅ Simulation stopped: The network is empty (no more waiting or present vehicles).")

# Step 9: Close connection between SUMO and Traci
traci.close()

# Step 10: Create csv file

# Using a relative path for portability
csv_file_path = "simulation_data.csv"

# 2. Write the data to the file, with error handling
try:
    # The CSV file is already correctly formatted with commas thanks to writerows
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter=',')
        writer.writerows(data_to_export)

    print(f"\n✅ CSV FILE CREATED SUCCESSFULLY")
    print(f"Path: {os.path.abspath(csv_file_path)}")
    print(f"Total number of recorded data rows (including header): {len(data_to_export)}")

except PermissionError:
    print(f"\n❌ PERMISSION ERROR: Cannot write to file: {csv_file_path}")
    print("Check that the file is not open or run the script as an administrator.")
except Exception as e:
    print(f"\n❌ Unexpected error while writing the CSV file. Cause: {type(e).__name__}: {e}")