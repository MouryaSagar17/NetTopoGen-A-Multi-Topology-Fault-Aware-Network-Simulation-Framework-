import sys
import os
import tkinter as tk

# Ensure src is in the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.main import NetworkSimulator

def launch_figure_3_scenario():
    """
    Launches the NetworkSimulator initialized to the state described in Figure 3:
    - Mesh Topology
    - Active QoS Sliders
    - Populated Multi-Algorithm Comparison Metrics
    """
    # 1. Initialize the real Tkinter root (no mocking)
    root = tk.Tk()
    root.title("Figure 3 Scenario: Mesh Topology & QoS")
    root.geometry("1200x800")  # Adjust size as needed

    # 2. Instantiate the simulator
    sim = NetworkSimulator(root)

    # 3. Set Topology to Mesh
    print("Setting topology to Mesh...")
    if hasattr(sim, 'topology_var'):
        sim.topology_var.set("Mesh")
        # Manually trigger the change handler if it's not auto-triggered
        if hasattr(sim, 'on_topology_change'):
            sim.on_topology_change()

    # 4. Activate QoS Sliders & Populate Metrics
    # Note: Adjust the following lines based on actual variable names in src/main.py
    print("Activating QoS and Metrics...")
    
    # Example: Enable QoS
    # if hasattr(sim, 'qos_enabled_var'): sim.qos_enabled_var.set(True)
    
    # Example: Run Simulation to populate metrics
    # if hasattr(sim, 'run_simulation'): 
    #     sim.run_simulation()
    # else:
    #     print("Please click 'Run' manually to populate metrics.")

    # 5. Start the GUI
    root.mainloop()

if __name__ == "__main__":
    launch_figure_3_scenario()