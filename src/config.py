"""
Configuration Module

This module contains global configuration constants for the network simulation.
"""

# QoS weights for multi-metric cost function: Cost = α·delay + β·(1/bandwidth) + γ·loss
QOS_WEIGHTS = {
    "alpha": 1.0,  # Weight for delay
    "beta": 1.0,   # Weight for bandwidth (inverse)
    "gamma": 1.0   # Weight for packet loss
}

# OSPF Configuration
OSPF_UPDATE_INTERVAL = 10.0  # seconds
INITIAL_CONVERGENCE_TIME = 5.0  # seconds

# RIP Configuration
RIP_UPDATE_INTERVAL = 30.0  # seconds
RIP_TIMEOUT = 180.0  # seconds
RIP_GARBAGE_COLLECTION = 120.0  # seconds

# Simulation Configuration
DEFAULT_SIMULATION_DURATION = 60.0  # seconds
DEFAULT_TIME_STEP = 0.1  # seconds

# Traffic Configuration
DEFAULT_CBR_RATE = 100  # packets per second
DEFAULT_BURST_RATE = 500  # packets per second during burst
DEFAULT_IDLE_RATE = 10  # packets per second during idle
DEFAULT_BURST_DURATION = 1.0  # seconds
DEFAULT_IDLE_DURATION = 4.0  # seconds

# Network Configuration
DEFAULT_LINK_DELAY = 10  # ms
DEFAULT_LINK_BANDWIDTH = 1e9  # 1 Gbps
DEFAULT_LINK_LOSS = 0.0  # packet loss probability
DEFAULT_LINK_JITTER = 0.0  # delay variation

# GUI Configuration
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600
NODE_RADIUS = 20
LINK_WIDTH = 2

# Colors
NODE_COLORS = {
    "router": "blue",
    "switch": "green",
    "host": "red",
    "hub": "orange",
    "server": "#8A2BE2",      # BlueViolet
    "firewall": "#A52A2A",    # Brown
    "isp": "#808080",         # Gray
    "ap": "#00CED1",          # DarkTurquoise
    "load_balancer": "#FF1493" # DeepPink
}

LINK_COLORS = {
    "active": "black",
    "broken": "red",
    "attacked": "purple"
}

# Logging Configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Output Configuration
OUTPUT_DIR = "output"
SAMPLE_OUTPUT_DIR = "sample_output"

# Random Seed for Reproducibility
DEFAULT_RANDOM_SEED = 42
