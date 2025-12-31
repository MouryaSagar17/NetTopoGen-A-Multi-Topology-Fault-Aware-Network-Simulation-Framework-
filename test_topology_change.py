import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Mock tkinter to avoid GUI
import tkinter as tk
tk.Tk = lambda: None  # Mock Tk to prevent window creation

from src.main import NetworkSimulator

def test_on_topology_change():
    # Create a mock root
    root = tk.Tk()

    # Instantiate the simulator
    sim = NetworkSimulator(root)

    # Test 1: Change to Intent-Based, should show intent fields
    print("Test 1: Changing to Intent-Based")
    sim.topology_var.set("Intent-Based")
    # Check if intent_label is packed (visible)
    # Since we can't check packing directly, we'll add prints in the method

    # Test 2: Change to Hierarchical, should hide intent fields
    print("Test 2: Changing to Hierarchical")
    sim.topology_var.set("Hierarchical")

    print("Tests completed. Check prints for method calls.")

if __name__ == "__main__":
    test_on_topology_change()
