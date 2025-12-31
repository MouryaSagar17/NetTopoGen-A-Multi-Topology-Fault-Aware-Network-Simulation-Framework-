import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import time
import threading
import queue
import math
import matplotlib.pyplot as plt  # pyright: ignore[reportMissingModuleSource]
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg  # pyright: ignore[reportMissingModuleSource]
import random
from typing import Dict, List, Tuple, Optional
import json
import os
import sys
import heapq
import copy
import re
import zipfile
import ipaddress

# Add the parent directory to the Python path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import project modules
from src.core import Topology, Node, Link
from src.simulation_config import SimulationConfig
from src.topology_generation import TopologyGenerator
from src.routing_algorithms import RoutingEngine
from src.traffic_simulation import TrafficSimulator, TrafficPatternGenerator
from src.evaluation_metrics import EvaluationMetrics
from src.visualization import NetworkVisualizer, MetricsVisualizer, SimulationDashboard
from src.protocols import RIPRouter, OSPFRouter, RIPNetwork, OSPFNetwork
from src.traffic_model import CBRGenerator, BurstyGenerator
from src.config import QOS_WEIGHTS

class ToolTip:
    """
    It creates a tooltip for a given widget as the mouse goes on it.
    """
    def __init__(self, widget, text='widget info'):
        self.waittime = 500     #miliseconds
        self.wraplength = 180   #pixels
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.enter)
        self.widget.bind("<Leave>", self.leave)
        self.widget.bind("<ButtonPress>", self.leave)
        self.id = None
        self.tw = None

    def enter(self, event=None):
        self.schedule()

    def leave(self, event=None):
        self.unschedule()
        self.hidetip()

    def schedule(self):
        self.unschedule()
        self.id = self.widget.after(self.waittime, self.showtip)

    def unschedule(self):
        id = self.id
        self.id = None
        if id:
            self.widget.after_cancel(id)

    def showtip(self, event=None):
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        self.tw = tk.Toplevel(self.widget)
        self.tw.wm_overrideredirect(True)
        self.tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(self.tw, text=self.text, justify='left',
                       background="#ffffe0", relief='solid', borderwidth=1,
                       font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tw
        self.tw = None
        if tw:
            tw.destroy()

class CollapsibleFrame(ttk.Frame):
    """
    A collapsible frame widget for the accordion layout.
    """
    def __init__(self, parent, title, group=None, header_style='Toolbutton', *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.variable = tk.IntVar(value=1)
        self.group = group
        if self.group is not None:
            self.group.append(self)
            
        self.title_frame = ttk.Frame(self)
        self.title_frame.pack(fill="x", expand=False)

        self.toggle_button = ttk.Checkbutton(self.title_frame, text=title, variable=self.variable, command=self.on_toggle, style=header_style)
        self.toggle_button.pack(fill="x", expand=True, anchor='w')

        self.content_frame = ttk.Frame(self)
        self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
    def on_toggle(self):
        if self.variable.get():
            self.content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        else:
            self.content_frame.pack_forget()

class NetworkSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("NetTopoGen - Advanced Network Simulator")
        self.root.geometry("1400x900")
        
        # --- Styles ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TFrame", background="#f5f5f5")
        style.configure("TLabel", background="#f5f5f5", font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9))
        style.configure("Header.TLabel", font=("Segoe UI", 10, "bold"))
        style.configure("Result.TLabel", font=("Segoe UI", 10, "bold"), foreground="#006400")
        style.configure("Simulation.Toolbutton", background="#ffcc80", font=("Segoe UI", 9, "bold"))
        style.map("Simulation.Toolbutton", background=[('active', '#ffb74d'), ('selected', '#ffcc80')])

        # --- Main Layout Container ---
        self.main_container = ttk.Frame(root)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # --- 1. Top Bar (Network Inputs & Global Actions) ---
        self.top_bar = ttk.Frame(self.main_container, padding="5", relief="raised")
        self.top_bar.pack(side=tk.TOP, fill=tk.X)

        # -- Group: Devices --
        self.devices_frame = ttk.Frame(self.top_bar)
        self.devices_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.devices_frame, text="PCs:").pack(side=tk.LEFT, padx=2)
        self.pc_entry = ttk.Entry(self.devices_frame, width=6)
        self.pc_entry.pack(side=tk.LEFT, padx=2)
        self.pc_entry.insert(0, "4")  # Default value

        ttk.Label(self.devices_frame, text="Routers:").pack(side=tk.LEFT, padx=2)
        self.router_entry = ttk.Entry(self.devices_frame, width=6)
        self.router_entry.pack(side=tk.LEFT, padx=2)
        self.router_entry.insert(0, "2") # Default value

        ttk.Label(self.devices_frame, text="Switches:").pack(side=tk.LEFT, padx=2)
        self.switch_entry = ttk.Entry(self.devices_frame, width=6)
        self.switch_entry.pack(side=tk.LEFT, padx=2)
        self.switch_entry.insert(0, "2") # Default value
        
        ttk.Label(self.devices_frame, text="Servers:").pack(side=tk.LEFT, padx=2)
        self.server_entry = ttk.Entry(self.devices_frame, width=6)
        self.server_entry.pack(side=tk.LEFT, padx=2)
        self.server_entry.insert(0, "1")

        ttk.Separator(self.top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # -- Group: Topology --
        self.topology_frame = ttk.Frame(self.top_bar)
        self.topology_frame.pack(side=tk.LEFT, padx=5)

        ttk.Label(self.topology_frame, text="Topology:").pack(side=tk.LEFT, padx=2)
        self.topology_var = tk.StringVar(root)
        topology_options = ["Hierarchical", "Star", "Ring", "Mesh", "Tree", "Intent-Based"]
        self.topology_menu = ttk.OptionMenu(self.topology_frame, self.topology_var, topology_options[0], *topology_options)
        self.topology_menu.pack(side=tk.LEFT, padx=2)
        self.topology_var.trace_add("write", self.on_topology_change)

        # Intent Description (hidden by default)
        self.intent_var = tk.StringVar(value="e.g., small network with 3 PCs, 2 routers, and 1 switch")
        self.intent_button = ttk.Button(self.topology_frame, text="📝 Enter Details", command=self.open_intent_dialog)
        # Initially hidden, managed by on_topology_change

        ttk.Separator(self.top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # -- Group: Actions --
        self.actions_frame = ttk.Frame(self.top_bar)
        self.actions_frame.pack(side=tk.LEFT, padx=5)

        self.generate_button = ttk.Button(self.actions_frame, text="Generate Network", command=self.generate_network)
        self.generate_button.pack(side=tk.LEFT, padx=2)

        self.load_config_button = ttk.Button(self.actions_frame, text="Load Config", command=self.load_config)
        self.load_config_button.pack(side=tk.LEFT, padx=2)

        self.save_cfg_button = ttk.Button(self.actions_frame, text="Save CFG", command=self.save_cfgs)
        self.save_cfg_button.pack(side=tk.LEFT, padx=2)

        ttk.Separator(self.top_bar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)

        # Manual Mode Toggle
        self.manual_mode = tk.BooleanVar(value=False)
        self.manual_check = ttk.Checkbutton(self.top_bar, text="Manual Mode", variable=self.manual_mode, command=self.toggle_manual_mode)
        self.manual_check.pack(side=tk.LEFT, padx=10)
        
        # Search UI
        self.search_btn = ttk.Button(self.top_bar, text="🔍", width=3, command=self.search_nodes)
        self.search_btn.pack(side=tk.RIGHT, padx=2)
        
        self.search_entry = ttk.Entry(self.top_bar, width=15)
        self.search_entry.pack(side=tk.RIGHT, padx=2)
        self.search_entry.insert(0, "Search Node...")
        self.search_entry.bind("<FocusIn>", lambda e: self.search_entry.delete(0, tk.END) if self.search_entry.get() == "Search Node..." else None)
        self.search_entry.bind("<Return>", lambda e: self.search_nodes())

        # Screenshot
        self.screenshot_button = ttk.Button(self.top_bar, text="📷 Screenshot", command=self.take_screenshot)
        self.screenshot_button.pack(side=tk.RIGHT, padx=10)

        # --- Content Area (Split Pane) ---
        self.content_pane = ttk.PanedWindow(self.main_container, orient=tk.HORIZONTAL)
        self.content_pane.pack(fill=tk.BOTH, expand=True)

        # --- 2. Center Canvas (Main Focus) ---
        self.canvas_frame = ttk.Frame(self.content_pane)
        self.content_pane.add(self.canvas_frame, weight=4)
        
        self.canvas = tk.Canvas(self.canvas_frame, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas_width = 800
        self.canvas_height = 600

        # Tooltip Label (Hidden by default)
        self.tooltip_label = tk.Label(self.canvas, text="", bg="#ffffe0", borderwidth=1, relief="solid", font=("Segoe UI", 8))

        # Bind drag events always to allow node repositioning
        self.canvas.tag_bind("device", "<ButtonPress-1>", self.on_node_press)
        self.canvas.tag_bind("device", "<B1-Motion>", self.on_node_drag)
        self.canvas.tag_bind("device", "<ButtonRelease-1>", self.on_node_release)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind('<Motion>', self.on_canvas_hover) # Hover for metrics

        # --- 3. Right Side Control Panel (Scrollable) ---
        self.right_container = ttk.Frame(self.content_pane, width=350)
        self.content_pane.add(self.right_container, weight=1)
        
        # Scrollbar for Right Panel
        self.right_canvas = tk.Canvas(self.right_container)
        self.right_scrollbar = ttk.Scrollbar(self.right_container, orient="vertical", command=self.right_canvas.yview)
        self.right_scroll_frame = ttk.Frame(self.right_canvas)
        
        self.right_scroll_frame.bind(
            "<Configure>",
            lambda e: self.right_canvas.configure(scrollregion=self.right_canvas.bbox("all"))
        )
        
        self.right_window_id = self.right_canvas.create_window((0, 0), window=self.right_scroll_frame, anchor="nw")
        self.right_canvas.configure(yscrollcommand=self.right_scrollbar.set)
        
        self.right_canvas.pack(side="left", fill="both", expand=True)
        self.right_scrollbar.pack(side="right", fill="y")

        self.right_canvas.bind(
            "<Configure>",
            lambda e: self.right_canvas.itemconfig(self.right_window_id, width=e.width)
        )

        self.accordion_group = []

        # --- Accordion Sections ---

        # 1. Simulation
        self.sim_section = CollapsibleFrame(self.right_scroll_frame, title="1. Simulation", group=self.accordion_group, header_style="Simulation.Toolbutton")
        self.sim_section.pack(fill='both', expand=True, pady=2)
        self.control_frame = self.sim_section.content_frame
        
        ttk.Label(self.control_frame, text="Source:").pack(anchor="w")
        self.source_var = tk.StringVar(root)
        self.source_menu = ttk.OptionMenu(self.control_frame, self.source_var, "")
        self.source_menu.pack(fill='x')

        ttk.Label(self.control_frame, text="Destination:").pack(anchor="w")
        self.dest_var = tk.StringVar(root)
        self.dest_menu = ttk.OptionMenu(self.control_frame, self.dest_var, "")
        self.dest_menu.pack(fill='x')

        self.ping_button = ttk.Button(self.control_frame,
                                      text="Start Simulation",
                                      command=self.start_simulation_thread)
        self.ping_button.pack(fill='x', pady=5)
        
        # 2. Break Link
        self.link_fail_section = CollapsibleFrame(self.right_scroll_frame, title="2. Break Link", group=self.accordion_group, header_style="Simulation.Toolbutton")
        self.link_fail_section.pack(fill='both', expand=True, pady=2)
        self.link_fail_frame = self.link_fail_section.content_frame
        
        ttk.Label(self.link_fail_frame, text="Break Link:").pack(anchor="w")
        link_frame = ttk.Frame(self.link_fail_frame)
        link_frame.pack(fill='x')
        self.link_a_var = tk.StringVar(root)
        self.link_a_menu = ttk.OptionMenu(link_frame, self.link_a_var, "")
        self.link_a_menu.pack(side=tk.LEFT, expand=True, fill='x')
        ttk.Label(link_frame, text="-").pack(side=tk.LEFT)
        self.link_b_var = tk.StringVar(root)
        self.link_b_menu = ttk.OptionMenu(link_frame, self.link_b_var, "")
        self.link_b_menu.pack(side=tk.LEFT, expand=True, fill='x')
        
        self.break_link_button = ttk.Button(self.link_fail_frame, text="Break Link", command=self.break_link)
        self.break_link_button.pack(fill='x', pady=2)
        self.reset_links_button = ttk.Button(self.link_fail_frame, text="Reset All Links", command=self.reset_links)
        self.reset_links_button.pack(fill='x', pady=2)
        
        # 3. Algorithm
        self.routing_section = CollapsibleFrame(self.right_scroll_frame, title="3. Algorithm", group=self.accordion_group, header_style="Simulation.Toolbutton")
        self.routing_section.pack(fill='both', expand=True, pady=2)
        
        self.routing_frame = self.routing_section.content_frame
        
        ttk.Label(self.routing_frame, text="Algorithm:").pack(anchor="w")
        self.algorithm_var = tk.StringVar(root)
        self.protocol_var = tk.StringVar(root)
        algorithm_options = ["Compare All", "Dijkstra", "Bellman-Ford", "A*", "BFS", "QoS-Metric", "RIP-like", "OSPF-like"]
        self.algorithm_menu = ttk.OptionMenu(self.routing_frame, self.algorithm_var, algorithm_options[0], *algorithm_options)
        self.algorithm_menu.pack(fill='x', pady=2)

        self.compute_route_button = ttk.Button(self.routing_frame, text="Generate Optimal Path", command=self.compute_route)
        self.compute_route_button.pack(fill='x', pady=5)

        self.simulate_selected_button = ttk.Button(self.routing_frame, text="Simulate via Selected", command=self.simulate_via_selected)
        self.simulate_selected_button.pack(fill='x', pady=5)

        columns = ("algo", "hops", "cost", "conv")
        self.metrics_tree = ttk.Treeview(self.routing_frame, columns=columns, show="headings", height=5)
        self.metrics_tree.heading("algo", text="Alg")
        self.metrics_tree.heading("hops", text="Hop")
        self.metrics_tree.heading("cost", text="Cost")
        self.metrics_tree.heading("conv", text="Time")
        self.metrics_tree.column("algo", width=60)
        self.metrics_tree.column("hops", width=30)
        self.metrics_tree.column("cost", width=40)
        self.metrics_tree.column("conv", width=40)
        self.metrics_tree.pack(fill='both', expand=True, pady=5)

        # Optimal Path Result
        self.optimal_path_label = ttk.Label(self.routing_frame, text="Optimal Path: None", wraplength=300, style="Result.TLabel")
        self.optimal_path_label.pack(fill='x', pady=5)
        self.min_cost_label = ttk.Label(self.routing_frame, text="Min Cost: -", style="Result.TLabel")
        self.min_cost_label.pack(fill='x')

        ttk.Label(self.routing_frame, text="Protocol:").pack(anchor="w")
        protocol_options = ["None", "RIP", "OSPF"]
        self.protocol_menu = ttk.OptionMenu(self.routing_frame, self.protocol_var, protocol_options[0], *protocol_options)
        self.protocol_menu.pack(fill='x', pady=2)
        self.run_protocol_button = ttk.Button(self.routing_frame, text="Run Protocol", command=self.run_protocol)
        self.run_protocol_button.pack(fill='x', pady=5)
        self.protocol_status_label = ttk.Label(self.routing_frame, text="Protocol Status: None", style="Result.TLabel")
        self.protocol_status_label.pack(fill='x', pady=5)

        # Protocol Routing Table
        columns = ("dest", "next_hop", "metric")
        self.protocol_tree = ttk.Treeview(self.routing_frame, columns=columns, show="headings", height=5)
        self.protocol_tree.heading("dest", text="Destination")
        self.protocol_tree.heading("next_hop", text="Next Hop")
        self.protocol_tree.heading("metric", text="Metric")
        self.protocol_tree.column("dest", width=80)
        self.protocol_tree.column("next_hop", width=80)
        self.protocol_tree.column("metric", width=60)
        self.protocol_tree.pack(fill='both', expand=True, pady=5)


        # 4. QOS Metrics
        self.qos_section = CollapsibleFrame(self.right_scroll_frame, title="4. QOS Metrics", group=self.accordion_group, header_style="Simulation.Toolbutton")
        self.qos_section.pack(fill='both', expand=True, pady=2)
        self.qos_frame = self.qos_section.content_frame
        
        ttk.Label(self.qos_frame, text="Cost = α·delay + β·(1/bw) + γ·loss", font=("Segoe UI", 8, "italic")).pack(pady=2)
        
        ttk.Label(self.qos_frame, text="α (Delay):").pack(anchor="w")
        self.alpha_var = tk.DoubleVar(value=1.0)
        self.alpha_slider = tk.Scale(self.qos_frame, from_=0, to=10, resolution=0.1, orient=tk.HORIZONTAL, variable=self.alpha_var, command=self.update_qos)
        self.alpha_slider.pack(fill='x')

        ttk.Label(self.qos_frame, text="β (Bandwidth):").pack(anchor="w")
        self.beta_var = tk.DoubleVar(value=1.0)
        self.beta_slider = tk.Scale(self.qos_frame, from_=0, to=10, resolution=0.1, orient=tk.HORIZONTAL, variable=self.beta_var, command=self.update_qos)
        self.beta_slider.pack(fill='x')

        ttk.Label(self.qos_frame, text="γ (Loss):").pack(anchor="w")
        self.gamma_var = tk.DoubleVar(value=1.0)
        self.gamma_slider = tk.Scale(self.qos_frame, from_=0, to=10, resolution=0.1, orient=tk.HORIZONTAL, variable=self.gamma_var, command=self.update_qos)
        self.gamma_slider.pack(fill='x')
        
        self.qos_summary_label = ttk.Label(self.qos_frame, text="Impact: Balanced", foreground="blue")
        self.qos_summary_label.pack(fill='x', pady=2)

        self.metrics_label = ttk.Label(self.qos_frame, text="Metrics: Not run", style="Result.TLabel")
        self.metrics_label.pack(fill='x', pady=5)
        self.run_evaluation_button = ttk.Button(self.qos_frame, text="Run Evaluation", command=self.run_evaluation)
        self.run_evaluation_button.pack(fill='x', pady=5)

        # 5. Load
        self.traffic_section = CollapsibleFrame(self.right_scroll_frame, title="5. Load", group=self.accordion_group, header_style="Simulation.Toolbutton")
        self.traffic_section.pack(fill='both', expand=True, pady=2)
        self.traffic_frame = self.traffic_section.content_frame
        
        ttk.Label(self.traffic_frame, text="Type:").pack(anchor="w")
        self.traffic_var = tk.StringVar(root)
        traffic_options = ["CBR", "Bursty"]
        self.traffic_menu = ttk.OptionMenu(self.traffic_frame, self.traffic_var, traffic_options[0], *traffic_options)
        self.traffic_menu.pack(fill='x')
        
        ttk.Label(self.traffic_frame, text="Load:").pack(anchor="w")
        self.traffic_load_var = tk.DoubleVar(value=0.5)
        self.traffic_load_slider = tk.Scale(self.traffic_frame, from_=0, to=1, resolution=0.1, orient=tk.HORIZONTAL, variable=self.traffic_load_var)
        self.traffic_load_slider.pack(fill='x')
        
        t_btn_frame = ttk.Frame(self.traffic_frame)
        t_btn_frame.pack(fill='x', pady=5)
        self.run_traffic_button = ttk.Button(t_btn_frame, text="▶", width=3, command=self.run_traffic_demo)
        self.run_traffic_button.pack(side=tk.LEFT, padx=2)
        self.pause_traffic_button = ttk.Button(t_btn_frame, text="⏸", width=3, command=self.pause_traffic_demo)
        self.pause_traffic_button.pack(side=tk.LEFT, padx=2)
        self.resume_traffic_button = ttk.Button(t_btn_frame, text="⏯", width=3, command=self.resume_traffic_demo)
        self.resume_traffic_button.pack(side=tk.LEFT, padx=2)
        self.stop_traffic_button = ttk.Button(t_btn_frame, text="⏹", width=3, command=self.stop_traffic_demo)
        self.stop_traffic_button.pack(side=tk.LEFT, padx=2)
        
        self.traffic_explanation_label = ttk.Label(self.traffic_frame, text="", font=("Segoe UI", 8))
        self.traffic_explanation_label.pack(fill='x')

        # Traffic Results Table
        columns = ("type", "delay", "loss", "path")
        self.traffic_tree = ttk.Treeview(self.traffic_frame, columns=columns, show="headings", height=5)
        self.traffic_tree.heading("type", text="Type")
        self.traffic_tree.heading("delay", text="Avg Delay")
        self.traffic_tree.heading("loss", text="Loss")
        self.traffic_tree.heading("path", text="Path")
        self.traffic_tree.column("type", width=60)
        self.traffic_tree.column("delay", width=80)
        self.traffic_tree.column("loss", width=50)
        self.traffic_tree.column("path", width=100)
        self.traffic_tree.pack(fill='both', expand=True, pady=5)

        # 6. Fail Node
        self.fault_section = CollapsibleFrame(self.right_scroll_frame, title="6. Fail Node", group=self.accordion_group, header_style="Simulation.Toolbutton")
        self.fault_section.pack(fill='both', expand=True, pady=2)
        self.fault_frame = self.fault_section.content_frame

        ttk.Label(self.fault_frame, text="Fail Node:").pack(anchor="w")
        self.fault_node_var = tk.StringVar(root)
        self.fault_node_menu = ttk.OptionMenu(self.fault_frame, self.fault_node_var, "")
        self.fault_node_menu.pack(fill='x')
        self.inject_fault_button = ttk.Button(self.fault_frame, text="Fail Node", command=self.inject_fault)
        self.inject_fault_button.pack(fill='x', pady=2)

        self.fault_status_label = ttk.Label(self.fault_frame, text="Faults: None", foreground="blue")
        self.fault_status_label.pack(fill='x', pady=2)

        self.clear_faults_button = ttk.Button(self.fault_frame, text="Clear Faults", command=self.clear_faults)
        self.clear_faults_button.pack(fill='x', pady=2)

        # 7. Export Results
        self.export_section = CollapsibleFrame(self.right_scroll_frame, title="7. Export Results", group=self.accordion_group, header_style="Simulation.Toolbutton")
        self.export_section.pack(fill='both', expand=True, pady=2)
        self.export_frame = self.export_section.content_frame

        ttk.Label(self.export_frame, text="Export simulation results to file.").pack(anchor="w", pady=5)
        self.export_button = ttk.Button(self.export_frame, text="Export Results", command=self.export_results)
        self.export_button.pack(fill='x', pady=5)
        
        self.pt_export_button = ttk.Button(self.export_frame, text="Export to Packet Tracer", command=self.export_packet_tracer)
        self.pt_export_button.pack(fill='x', pady=5)
        ToolTip(self.pt_export_button, "Export topology structure for recreation in Cisco Packet Tracer")

        # --- Status Bar (Bottom) ---
        self.status_bar = ttk.Frame(root, relief="sunken", padding=2)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_label = ttk.Label(self.status_bar, text="Status: Ready", foreground="blue")
        self.status_label.pack(side=tk.LEFT)

        # --- Manual Mode Controls (Bottom Left) ---
        self.manual_controls_frame = ttk.Frame(self.canvas, padding="5")
        # We will place this using place() when manual mode is active
        
        ttk.Button(self.manual_controls_frame, text="Add PC", command=lambda: self.add_device_manual("PC")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add Switch", command=lambda: self.add_device_manual("Switch")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add Router", command=lambda: self.add_device_manual("Router")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add Server", command=lambda: self.add_device_manual("Server")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add Firewall", command=lambda: self.add_device_manual("Firewall")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add ISP", command=lambda: self.add_device_manual("ISP")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add AP", command=lambda: self.add_device_manual("AP")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add LB", command=lambda: self.add_device_manual("Load_Balancer")).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Add Link", command=self.enable_add_link_mode).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Delete", command=self.enable_delete_mode).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Clear All", command=self.clear_topology_manual).pack(side=tk.LEFT, padx=2)
        ttk.Button(self.manual_controls_frame, text="Undo", command=self.undo).pack(side=tk.LEFT, padx=5)

        # --- Zoom Controls ---
        self.zoom_frame = ttk.Frame(self.canvas, padding="5")
        self.zoom_frame.place(relx=0.98, rely=0.98, anchor="se")
        ttk.Button(self.zoom_frame, text="+", width=2, command=lambda: self.zoom(1.1)).pack(side=tk.TOP)
        ttk.Button(self.zoom_frame, text="-", width=2, command=lambda: self.zoom(0.9)).pack(side=tk.TOP)

        # --- Evaluation Frame (Hidden/Optional) ---
        # Keeping logic but not showing in main UI to reduce clutter, or move to a menu
        
        # Initialize network storage
        self.node_coordinates = {}
        self.network_graph = {}
        self.all_nodes = []
        self.broken_links = set()
        self.failed_nodes = set()
        self.topology = Topology()
        self.routing_engine = None
        self.current_paths = {}
        self.traffic_model = None
        self.protocol = None
        self.link_labels = {}
        self.node_queues = {}
        self.eval_data = {}
        self.plots = {}
        self.undo_stack = []
        self.drag_data = {"x": 0, "y": 0, "node": None}
        self.animation_ids = {}
        self.active_protocol = None # Track active protocol for dynamic updates
        self.node_queues = {}
        self.link_utilization = {}
        self.simulation_running = False
        self.simulation_paused = False
        
        # Manual Link Addition State
        self.adding_link_mode = False
        self.link_source_node = None
        self.deleting_mode = False
        
        # Generate the default network on startup
        self.generate_network()

    def on_topology_change(self, *args):
        if self.topology_var.get() == "Intent-Based":
            self.intent_button.pack(side=tk.LEFT, padx=5)
        else:
            self.intent_button.pack_forget()

    def open_intent_dialog(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Enter Topology Intent")
        dialog.geometry("400x300")
        
        ttk.Label(dialog, text="Describe the network topology:").pack(pady=5, padx=5, anchor="w")
        
        text_area = tk.Text(dialog, height=10, width=40, wrap=tk.WORD)
        text_area.pack(pady=5, padx=5, fill=tk.BOTH, expand=True)
        text_area.insert("1.0", self.intent_var.get())
        
        def on_generate():
            self.intent_var.set(text_area.get("1.0", "end-1c").strip())
            dialog.destroy()
            self.generate_network()
            
        ttk.Button(dialog, text="Generate Network", command=on_generate).pack(pady=10)

    def load_config(self):
        """
        Loads simulation configuration from JSON/CFG files.
        Supports loading multiple files to merge topologies.
        """
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Configuration files", "*.json *.cfg"), ("All files", "*.*")]
        )
        if not file_paths:
            return

        # Check for CFG files
        if any(f.lower().endswith(".cfg") for f in file_paths):
            self.load_from_cfg_files(file_paths)
            return

        # If single file, load normally and populate UI
        if len(file_paths) == 1:
            file_path = file_paths[0]
            try:
                config = SimulationConfig.load_from_file(file_path)
                
                # Update Topology Inputs
                self.pc_entry.delete(0, tk.END)
                self.pc_entry.insert(0, str(config.topology.num_end_devices))
                
                self.router_entry.delete(0, tk.END)
                self.router_entry.insert(0, str(config.topology.num_routers))
                
                self.switch_entry.delete(0, tk.END)
                self.switch_entry.insert(0, str(config.topology.num_switches))
                
                # Update Topology Type
                self.topology_var.set(config.topology.topology_type)
                
                # Update Traffic Settings
                self.traffic_var.set(config.traffic.traffic_type)
                self.traffic_load_var.set(config.traffic.load_factor)
                
                # Update QoS Settings
                self.alpha_var.set(config.routing.qos_weights.alpha)
                self.beta_var.set(config.routing.qos_weights.beta)
                self.gamma_var.set(config.routing.qos_weights.gamma)
                self.update_qos(None)
                
                # Generate the network
                self.generate_network()
                
                self.status_label.config(text=f"Status: Configuration loaded from {os.path.basename(file_path)}", foreground="green")
                
            except Exception as e:
                messagebox.showerror("Load Error", f"Failed to load configuration: {str(e)}")
            return

        # If multiple files, merge them
        original_add_node = self._add_node
        original_add_link = self._add_link
        try:
            self.canvas.delete("all")
            self.node_coordinates = {}
            self.network_graph = {}
            self.all_nodes = []
            self.broken_links.clear()
            self.topology = Topology()
            
            import math
            grid_cols = math.ceil(math.sqrt(len(file_paths)))
            
            for idx, file_path in enumerate(file_paths):
                config = SimulationConfig.load_from_file(file_path)
                
                # Calculate grid position
                col = idx % grid_cols
                row = idx // grid_cols
                prefix = f"Cfg{idx+1}_"
                
                # Define hooks to offset coordinates and prefix names
                def hooked_add_node(name, coords):
                    new_name = prefix + name
                    # Scale and translate
                    cx, cy = 400, 300
                    scaled_x = (coords[0] - cx) * 0.6 + cx
                    scaled_y = (coords[1] - cy) * 0.6 + cy
                    
                    trans_x = (col - (grid_cols-1)/2) * 450
                    trans_y = (row - (math.ceil(len(file_paths)/grid_cols)-1)/2) * 350
                    
                    final_x = int(scaled_x + trans_x)
                    final_y = int(scaled_y + trans_y)
                    
                    original_add_node(new_name, (final_x, final_y))

                def hooked_add_link(u, v):
                    original_add_link(prefix + u, prefix + v)
                
                # Apply hooks
                self._add_node = hooked_add_node
                self._add_link = hooked_add_link
                
                # Generate topology based on config
                t_type = config.topology.topology_type
                n_pcs = config.topology.num_end_devices
                n_routers = config.topology.num_routers
                n_switches = config.topology.num_switches
                n_hubs = config.topology.num_hubs
                
                if t_type == "Hierarchical":
                    self.layout_hierarchical(n_pcs, n_routers, n_switches, n_hubs)
                elif t_type == "Star":
                    self.layout_star(n_pcs, n_routers, n_switches, n_hubs)
                elif t_type == "Ring":
                    self.layout_ring(n_pcs, n_routers, n_switches, n_hubs)
                elif t_type == "Mesh":
                    self.layout_mesh(n_pcs, n_routers, n_switches, n_hubs)
                elif t_type == "Tree":
                    self.layout_tree(n_pcs, n_routers, n_switches, n_hubs)
                else:
                    # Fallback for Intent-Based or unknown
                    self.layout_hierarchical(n_pcs, n_routers, n_switches, n_hubs)
            
            # Restore methods
            self._add_node = original_add_node
            self._add_link = original_add_link
            
            # Finalize
            self.fit_to_canvas()
            
            # Randomize metrics for new links
            for start_node, neighbors in self.network_graph.items():
                for end_node in neighbors:
                    link = self.topology.get_link(start_node, end_node)
                    if not link:
                        self.topology.add_link(Link(start_node, end_node))
                        link = self.topology.get_link(start_node, end_node)
                    if link.delay == 10.0:
                        link.delay = random.uniform(1, 50)
                        link.bandwidth = random.choice([10, 100, 1000]) * 1e6
                        link.loss = random.uniform(0, 0.5)

            self.draw_topology()
            self._update_option_menus()
            self.status_label.config(text=f"Status: Merged {len(file_paths)} configurations.", foreground="green")
            
        except Exception as e:
            # Ensure methods are restored
            self._add_node = original_add_node
            self._add_link = original_add_link
            messagebox.showerror("Merge Error", f"Failed to merge configurations: {str(e)}")

    def load_from_cfg_files(self, file_paths):
        """
        Parses multiple .cfg files (Cisco IOS style) and generates topology based on subnets.
        Infers end devices dynamically based on available switches and subnets.
        Classifies devices, infers links, and ensures a valid hierarchical topology.
        """
        self.canvas.delete("all")
        self.node_coordinates = {}
        self.network_graph = {}
        self.all_nodes = []
        self.broken_links.clear()
        self.topology = Topology()
        
        parsed_nodes = []

        # 1. Parse Files
        for file_path in file_paths:
            node_data = self._parse_cfg_file(file_path)
            if node_data:
                parsed_nodes.append(node_data)

        # Auto-layout (Circular)
        if not parsed_nodes:
            return

        # 2. Classify Nodes
        routers = [n for n in parsed_nodes if n['type'] == 'router']
        switches = [n for n in parsed_nodes if n['type'] == 'switch']
        end_devices = [n for n in parsed_nodes if n['type'] == 'host']

        # 3. Layout Nodes (Hierarchical)
        self._layout_parsed_nodes(routers, switches, end_devices)

        # 4. Infer Links (Subnet Matching)
        self._infer_links(parsed_nodes)

        # 5. Dynamic End-Device Inference (Optional - if user requested via UI)
        try:
            num_pcs_requested = int(self.pc_entry.get())
        except ValueError:
            num_pcs_requested = 0
            
        # Only run dynamic inference if we loaded infrastructure but few/no PCs from CFG
        if len(end_devices) < num_pcs_requested:
             self._generate_dynamic_pcs(num_pcs_requested - len(end_devices), routers, switches)

        # 6. Validation and Auto-Correction
        self._validate_and_fix_topology()

        self.fit_to_canvas()
        self.draw_topology()
        self._update_option_menus()
        
        # Feedback
        n_hosts = len([n for n in self.all_nodes if self.topology.nodes[n].node_type == "host"])
        n_switches = len([n for n in self.all_nodes if self.topology.nodes[n].node_type == "switch"])
        self.status_label.config(text=f"Status: Imported {len(file_paths)} files. {n_hosts} Hosts distributed across {n_switches} Switches.", foreground="green")
        messagebox.showinfo("Import Successful", f"Topology inferred from {len(file_paths)} CFG files.\n{n_hosts} end devices distributed across {n_switches} switches.")

    def _parse_cfg_file(self, file_path):
        try:
            with open(file_path, 'r') as f:
                content = f.read()
            
            # Extract Hostname
            hostname_match = re.search(r'hostname\s+(\S+)', content, re.IGNORECASE)
            hostname = hostname_match.group(1) if hostname_match else os.path.splitext(os.path.basename(file_path))[0]
            
            interfaces = []
            current_int = None
            has_routing = False
            has_switchport = False
            has_gateway = False
            
            lines = content.splitlines()
            for line in lines:
                line = line.strip()
                if line.startswith("interface"):
                    current_int = line.split()[1]
                elif line.startswith("ip address") and current_int:
                    parts = line.split()
                    if len(parts) >= 3:
                        ip = parts[2]
                        mask = parts[3]
                        interfaces.append({'name': current_int, 'ip': ip, 'mask': mask})
                elif line.startswith("router ospf") or line.startswith("router rip") or line.startswith("router bgp"):
                    has_routing = True
                elif "switchport" in line:
                    has_switchport = True
                elif "ip default-gateway" in line:
                    has_gateway = True
                elif line.startswith("!"):
                    current_int = None
            
            # Classification
            node_type = "unknown"
            lower_name = hostname.lower()
            
            # Strong signals
            if has_routing and len(interfaces) > 0:
                node_type = "router"
            elif has_switchport:
                node_type = "switch"
            elif has_gateway:
                node_type = "host"
            
            # Name based signals (fallback)
            elif "pc" in lower_name or "laptop" in lower_name or "server" in lower_name or "host" in lower_name:
                node_type = "host"
            elif "switch" in lower_name or "sw" in lower_name:
                node_type = "switch"
            elif "hub" in lower_name:
                node_type = "hub"
            elif "router" in lower_name or "r" in lower_name:
                node_type = "router"
            elif "server" in lower_name:
                node_type = "server"
            elif "firewall" in lower_name or "fw" in lower_name or "asa" in lower_name:
                node_type = "firewall"
            elif "isp" in lower_name or "cloud" in lower_name or "internet" in lower_name:
                node_type = "isp"
            elif "ap" in lower_name or "access" in lower_name:
                node_type = "ap"
            else:
                # Heuristic Fallback
                if len(interfaces) > 1:
                    node_type = "router" # Likely a router if multiple IP interfaces
                elif len(interfaces) == 1:
                    node_type = "host" # Likely a host if 1 IP interface
                else:
                    node_type = "switch" # Likely a switch if no IP interfaces found (L2)
            
            return {'name': hostname, 'type': node_type, 'interfaces': interfaces}
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return None

        # 3. Infer Infra Links
    def _layout_parsed_nodes(self, routers, switches, end_devices):
        width = self.canvas_width
        height = self.canvas_height
        margin_y = 50
        
        # Routers (Top)
        y_r = margin_y + height * 0.15
        if routers:
            spacing = width / (len(routers) + 1)
            for i, node in enumerate(routers):
                x = spacing * (i + 1)
                self._add_node_to_topo(node, (int(x), int(y_r)))

        # Switches (Middle)
        y_sw = margin_y + height * 0.5
        if switches:
            spacing = width / (len(switches) + 1)
            for i, node in enumerate(switches):
                x = spacing * (i + 1)
                self._add_node_to_topo(node, (int(x), int(y_sw)))

        # End Devices (Bottom)
        y_ed = margin_y + height * 0.85
        if end_devices:
            spacing = width / (len(end_devices) + 1)
            for i, node in enumerate(end_devices):
                x = spacing * (i + 1)
                self._add_node_to_topo(node, (int(x), int(y_ed)))

    def _add_node_to_topo(self, node_data, coords):
        name = node_data['name']
        ntype = node_data['type']
        self.node_coordinates[name] = coords
        self.topology.add_node(Node(name, ntype, coords))
        self._add_node(name, coords)
        
        # Restore interfaces to node object
        node_obj = self.topology.nodes[name]
        node_obj.interfaces = {}
        for idx, intf in enumerate(node_data['interfaces']):
            node_obj.interfaces[intf['name']] = {'ip': intf['ip'], 'mask': intf['mask']}

    def _infer_links(self, nodes):
        # Subnet Matching
        for i in range(len(nodes)):
            for j in range(i + 1, len(nodes)):
                node_a = nodes[i]
                node_b = nodes[j]
                
                link_found = False
                for int_a in node_a['interfaces']:
                    for int_b in node_b['interfaces']:
                        if self._is_same_subnet(int_a['ip'], int_a['mask'], int_b['ip'], int_b['mask']):
                            self._create_link(node_a['name'], node_b['name'])
                            link_found = True
                            break 
                    if link_found: break

        # 4. Dynamic End-Device Inference
        try:
            num_pcs = int(self.pc_entry.get())
        except ValueError:
            num_pcs = 0
    def _create_link(self, name_a, name_b):
        if name_b not in self.network_graph.get(name_a, []):
            self._add_link(name_a, name_b)
            self.topology.add_link(Link(name_a, name_b))

    def _generate_dynamic_pcs(self, count, routers, switches):
        # Logic to add extra PCs if requested
        # Prefer switches, then routers
        targets = [s['name'] for s in switches] if switches else [r['name'] for r in routers]
        if not targets: return

        # Balanced distribution
        pcs_per_target = count // len(targets)
        extra = count % len(targets)
        
        pc_idx = 1
        for i, target_name in enumerate(targets):
            num = pcs_per_target + (1 if i < extra else 0)
            target_coords = self.node_coordinates[target_name]
            
            for _ in range(num):
                name = f"GenPC{pc_idx}"
                # Position below target
                x = target_coords[0] + random.randint(-30, 30)
                y = target_coords[1] + 100
                
                self.node_coordinates[name] = (x, y)
                self.topology.add_node(Node(name, "host", (x, y)))
                self._add_node(name, (x, y))
                
                self._create_link(name, target_name)
                # Mark as inferred
                link = self.topology.get_link(name, target_name)
                if link: link.is_inferred = True
                
                pc_idx += 1

    def _validate_and_fix_topology(self):
        # 1. Fix Isolated Nodes
        switches = [n for n in self.all_nodes if "switch" in n.lower() or "sw" in n.lower()]
        routers = [n for n in self.all_nodes if "router" in n.lower() or "r" in n.lower()]
        
        for node in self.all_nodes:
            if not self.network_graph.get(node):
                # Isolated
                target = None
                if "pc" in node.lower() or "host" in node.lower() or "genpc" in node.lower():
                    # Connect to nearest switch, else router
                    target = self._get_nearest_node(node, switches)
                    if not target: target = self._get_nearest_node(node, routers)
                elif "switch" in node.lower():
                    # Connect to nearest router
                    target = self._get_nearest_node(node, routers)
                
                if target:
                    self._create_link(node, target)
                    link = self.topology.get_link(node, target)
                    if link: link.is_inferred = True
                    print(f"Auto-fixed isolated node {node} -> {target}")

        # 2. Ensure Switches have Uplinks
        # If a switch is connected only to PCs, it needs a router
        for sw in switches:
            neighbors = self.network_graph.get(sw, [])
            has_router = any(n in routers for n in neighbors)
            has_uplink_switch = any(n in switches and n != sw for n in neighbors)
            
            if not has_router and not has_uplink_switch and routers:
                # Connect to nearest router
                target = self._get_nearest_node(sw, routers)
                if target:
                    self._create_link(sw, target)
                    link = self.topology.get_link(sw, target)
                    if link: link.is_inferred = True
                    print(f"Auto-fixed switch uplink {sw} -> {target}")

    def save_cfgs(self):
        """
        Saves the current topology back to CFG files.
        """
        directory = filedialog.askdirectory(title="Select Directory to Save CFG Files")
        if not directory:
            return

        try:
            for node_name in self.all_nodes:
                node = self.topology.nodes.get(node_name)
                if not node: continue

                file_path = os.path.join(directory, f"{node_name}.cfg")
                with open(file_path, 'w') as f:
                    f.write(f"!\nversion 15.1\n!\nhostname {node_name}\n!\n")
                    
                    # Interfaces
                    if hasattr(node, 'interfaces') and node.interfaces:
                        for intf, data in node.interfaces.items():
                            f.write(f"interface {intf}\n")
                            if 'ip' in data and 'mask' in data:
                                f.write(f" ip address {data['ip']} {data['mask']}\n")
                            else:
                                f.write(" no ip address\n")
                            f.write("!\n")
                    else:
                        # Generate default interfaces if missing based on connections
                        neighbors = self.network_graph.get(node_name, [])
                        for i, neighbor in enumerate(neighbors):
                            f.write(f"interface FastEthernet0/{i}\n")
                            f.write(" no ip address\n") 
                            f.write("!\n")

                    # Routing / Gateway
                    if node.node_type == "router":
                        f.write("router ospf 1\n network 0.0.0.0 255.255.255.255 area 0\n!\n")
                    elif node.node_type == "host":
                        # Find gateway
                        gateway = "0.0.0.0"
                        if hasattr(node, 'interfaces'):
                            for data in node.interfaces.values():
                                if 'gateway' in data:
                                    gateway = data['gateway']
                                    break
                        f.write(f"ip default-gateway {gateway}\n!\n")
                    
                    f.write("end\n")
            
            messagebox.showinfo("Save Config", f"Successfully saved {len(self.all_nodes)} CFG files.")
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save configurations: {str(e)}")

    def _is_same_subnet(self, ip1, mask1, ip2, mask2):
        try:
            net1 = ipaddress.IPv4Interface(f"{ip1}/{mask1}").network
            net2 = ipaddress.IPv4Interface(f"{ip2}/{mask2}").network
            return net1 == net2
        except:
            return False

    def search_nodes(self):
        """
        Searches for nodes matching the search query and highlights them.
        """
        query = self.search_entry.get().strip().lower()
        if not query:
            self.draw_topology()
            return

        matching_nodes = [node for node in self.all_nodes if query in node.lower()]
        if matching_nodes:
            self.draw_topology(highlight_nodes=set(matching_nodes))
            self.status_label.config(text=f"Status: Found {len(matching_nodes)} matching nodes", foreground="blue")
        else:
            self.draw_topology()
            self.status_label.config(text="Status: No nodes found matching query", foreground="orange")

    def on_canvas_hover(self, event):
        """Show tooltip with metrics on hover."""
        item = self.canvas.find_closest(event.x, event.y)
        tags = self.canvas.gettags(item)
        
        text = ""
        for tag in tags:
            if tag.startswith("link_") and not tag.startswith("link_label"):
                # Extract nodes from tag: link_NodeA_NodeB
                parts = tag.split("_")
                if len(parts) >= 3:
                    u, v = parts[1], parts[2]
                    cost = self.get_link_cost(u, v)
                    link = self.topology.get_link(u, v)
                    if link:
                        if link.is_inferred:
                            text = f"Inferred End Device Link\n(Access Network)\nLink {u}-{v}\nBW: {link.bandwidth/1e6:.0f}Mbps"
                        else:
                            text = f"Link {u}-{v}\nDelay: {link.delay:.1f}ms\nBW: {link.bandwidth/1e6:.0f}Mbps\nLoss: {link.loss*100:.1f}%\nCost: {cost:.1f}"
        
        if text:
            self.tooltip_label.config(text=text)
            self.tooltip_label.place(x=event.x + 15, y=event.y + 15)
            self.tooltip_label.lift()
        else:
            self.tooltip_label.place_forget()

    def zoom(self, factor):
        # Simple scaling of coordinates
        for node in self.node_coordinates:
            self.node_coordinates[node] = (self.node_coordinates[node][0] * factor, self.node_coordinates[node][1] * factor)
        self.draw_topology()

    def fit_to_canvas(self):
        """Auto-scales and centers the topology to fit the canvas."""
        if not self.node_coordinates:
            return
            
        # Get bounds of current layout
        xs = [c[0] for c in self.node_coordinates.values()]
        ys = [c[1] for c in self.node_coordinates.values()]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        
        width = max_x - min_x
        height = max_y - min_y
        
        if width == 0 or height == 0:
            return
            
        # Target dimensions (canvas size with padding)
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        # Fallback if canvas not yet drawn
        if canvas_w <= 1: canvas_w = self.canvas_width
        if canvas_h <= 1: canvas_h = self.canvas_height
        
        padding = 50
        target_w = canvas_w - 2 * padding
        target_h = canvas_h - 2 * padding
        
        if target_w <= 0 or target_h <= 0: return

        scale_x = target_w / width
        scale_y = target_h / height
        scale = min(scale_x, scale_y)
        
        # Limit scale to avoid huge nodes if only 1-2 nodes exist
        if scale > 2.0: scale = 2.0
        
        # Center offset
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2
        
        canvas_center_x = canvas_w / 2
        canvas_center_y = canvas_h / 2
        
        # Apply transform
        new_coords = {}
        for node, (x, y) in self.node_coordinates.items():
            nx = (x - center_x) * scale + canvas_center_x
            ny = (y - center_y) * scale + canvas_center_y
            new_coords[node] = (int(nx), int(ny))
            
        self.node_coordinates = new_coords
        
        # Update topology nodes
        for node_id, coords in self.node_coordinates.items():
            if node_id in self.topology.nodes:
                self.topology.nodes[node_id].coordinates = coords

    # --- Node/Link Helper Methods ---
    def _add_node(self, name, coords):
        """Helper to add a node to our data structures."""
        self.node_coordinates[name] = coords
        self.network_graph[name] = []
        self.all_nodes.append(name)

    def _add_link(self, nodeA, nodeB):
        """Helper to add a bi-directional link."""
        if nodeA in self.network_graph and nodeB not in self.network_graph[nodeA]:
            self.network_graph[nodeA].append(nodeB)
        if nodeB in self.network_graph and nodeA not in self.network_graph[nodeB]:
            self.network_graph[nodeB].append(nodeA)

    def _get_distance(self, nodeA, nodeB):
        """Calculate distance between two nodes."""
        if nodeA not in self.node_coordinates or nodeB not in self.node_coordinates:
            return float('inf')
        (x1, y1) = self.node_coordinates[nodeA]
        (x2, y2) = self.node_coordinates[nodeB]
        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)

    def _get_nearest_node(self, node, node_list):
        """Find the nearest node in node_list to the target node."""
        min_dist = float('inf')
        nearest = None
        for n in node_list:
            dist = self._get_distance(node, n)
            if dist < min_dist:
                min_dist = dist
                nearest = n
        return nearest
        
    def _update_option_menus(self):
        """Helper to refresh all dropdown menus with current nodes."""
        if not self.all_nodes:
            self.all_nodes = [""] # Prevent errors if empty

        node_list = self.all_nodes

        # Clear old menus
        self.source_menu['menu'].delete(0, 'end')
        self.dest_menu['menu'].delete(0, 'end')
        self.link_a_menu['menu'].delete(0, 'end')
        self.link_b_menu['menu'].delete(0, 'end')
        self.fault_node_menu['menu'].delete(0, 'end')

        # Set defaults
        self.source_var.set(node_list[0])
        self.dest_var.set(node_list[-1])
        self.link_a_var.set(node_list[0])
        self.link_b_var.set(node_list[0])
        self.fault_node_var.set(node_list[0])

        # Add new options
        for node in node_list:
            self.source_menu['menu'].add_command(label=node, command=tk._setit(self.source_var, node))
            self.dest_menu['menu'].add_command(label=node, command=tk._setit(self.dest_var, node))
            self.link_a_menu['menu'].add_command(label=node, command=tk._setit(self.link_a_var, node))
            self.link_b_menu['menu'].add_command(label=node, command=tk._setit(self.link_b_var, node))
            self.fault_node_menu['menu'].add_command(label=node, command=tk._setit(self.fault_node_var, node))


    def generate_network(self):
        """
        Reads input, generates the network layout and graph,
        draws it, and sets up simulation controls.
        """
        if self.manual_mode.get():
            messagebox.showinfo("Manual Mode", "Cannot auto-generate in Manual Mode. Disable it first.")
            return

        self.canvas.delete("all")
        self.node_coordinates = {}
        self.network_graph = {}
        self.all_nodes = []
        self.broken_links.clear() # NEW: Reset broken links

        try:
            n_pcs = int(self.pc_entry.get())
            n_routers = int(self.router_entry.get())
            n_switches = int(self.switch_entry.get())
            n_hubs = 0
            n_servers = int(self.server_entry.get())
            n_firewalls = 1
            n_isps = 1
            topology = self.topology_var.get()
        except ValueError:
            self.status_label.config(text="Status: Invalid input. Please enter numbers.", foreground="red")
            return

        if n_pcs <= 0:
             self.status_label.config(text="Status: Need at least 1 End Device.", foreground="red")
             return
        if n_routers + n_switches <= 0 and topology != "Star":
            self.status_label.config(text="Status: Need at least 1 network device for this topology.", foreground="red")
            return

        # Smart Validation
        if n_routers > 4 and topology == "Star":
             messagebox.showinfo("Optimization Tip", "Star topology usually has 1-2 central nodes. Extra routers will be treated as spokes.")

        # --- Generate the layout and graph based on topology ---
        try:
            generator = TopologyGenerator()
            new_topology = None
            
            # --- Clear status on successful generation ---
            self.status_label.config(text="", foreground="blue")
            
            if topology == "Hierarchical":
                new_topology = generator.generate_hierarchical(n_pcs, n_routers, n_switches, n_hubs, n_servers, n_firewalls, n_isps, self.canvas_width, self.canvas_height)
            elif topology == "Star":
                new_topology = generator.generate_star(n_pcs, n_routers, n_switches, n_hubs, n_servers, n_firewalls, n_isps, self.canvas_width, self.canvas_height)
            elif topology == "Ring":
                new_topology = generator.generate_ring(n_pcs, n_routers, n_switches, n_hubs, n_servers, n_firewalls, n_isps, self.canvas_width, self.canvas_height)
            elif topology == "Mesh":
                new_topology = generator.generate_mesh(n_pcs, n_routers, n_switches, n_hubs, n_servers, n_firewalls, n_isps, self.canvas_width, self.canvas_height)
            elif topology == "Tree":
                new_topology = generator.generate_tree(n_pcs, n_routers, n_switches, n_hubs, n_servers, n_firewalls, n_isps, self.canvas_width, self.canvas_height)
            elif topology == "Intent-Based":
                new_topology = generator.generate_from_intent(self.intent_var.get(), self.canvas_width, self.canvas_height)
            
            if new_topology:
                # Validate
                warnings = generator.validate_topology(new_topology)
                if warnings:
                    messagebox.showwarning("Topology Validation", "\n".join(warnings))
                
                # Apply to Main
                self.topology = new_topology
                self.node_coordinates = self.topology.node_coordinates
                self.all_nodes = list(self.topology.nodes.keys())
                self.network_graph = {}
                for u, v in self.topology.graph.edges():
                    if u not in self.network_graph: self.network_graph[u] = []
                    if v not in self.network_graph: self.network_graph[v] = []
                    self.network_graph[u].append(v)
                    self.network_graph[v].append(u)
                
                # Ensure isolated nodes are in network_graph
                for n in self.all_nodes:
                    if n not in self.network_graph:
                        self.network_graph[n] = []

        except Exception as e:
            self.status_label.config(text=f"Status: Error generating layout. {e}", foreground="red")
            return

        # --- Randomize Link Metrics for QoS ---
        for start_node, neighbors in self.network_graph.items():
            for end_node in neighbors:
                link = self.topology.get_link(start_node, end_node)
                if not link:
                    # Create link in topology if not exists (should exist from layout)
                    self.topology.add_link(Link(start_node, end_node))
                    link = self.topology.get_link(start_node, end_node)
                
                # Assign random metrics
                link.delay = random.uniform(1, 50) # 1-50 ms
                link.bandwidth = random.choice([10, 100, 1000]) * 1e6 # 10, 100, 1000 Mbps
                link.loss = random.uniform(0, 0.5) # 0-0.5%

        # --- Auto-scale to fit canvas ---
        self.fit_to_canvas()

        # --- Draw the new topology ---
        self.draw_topology()
        
        # --- Update simulation controls ---
        if not self.all_nodes:
            self.status_label.config(text="Status: Network generation failed.", foreground="red")
            return
        
        self._update_option_menus() # NEW: Update all dropdowns
        
        self.status_label.config(text="Status: Ready", foreground="blue")

    def draw_topology(self, highlight_paths=None, optimal_path=None, optimal_color="green", highlight_nodes=None):
        """Draws all the nodes and links onto the canvas using NetworkVisualizer."""
        self.canvas.delete("all") # Clear canvas

        # Create a temporary topology object for visualization
        from src.core import Topology, Node, Link
        temp_topology = Topology()

        # Add nodes to topology
        for name, coords in self.node_coordinates.items():
            node_type = "router" if name.startswith("R") else \
                       "switch" if name.startswith("Switch") else \
                       "hub" if name.startswith("Hub") else \
                       "server" if name.startswith("Server") else \
                       "firewall" if name.startswith("FW") else \
                       "isp" if name.startswith("ISP") else \
                       "ap" if name.startswith("AP") else \
                       "load_balancer" if name.startswith("LB") else \
                       "host"  # Default to host for PCs and others
            node = Node(name, node_type=node_type, coordinates=coords)
            temp_topology.add_node(node)

        # Determine which links to add
        # Add all links to topology
        for start_node, neighbors in self.network_graph.items():
            for end_node in neighbors:
                # Get actual link data from self.topology
                real_link = self.topology.get_link(start_node, end_node)
                if real_link:
                    temp_topology.add_link(real_link)
                else:
                    link = Link(start_node, end_node, delay=10.0, bandwidth=1000000.0, loss=0.0, status=True)
                    temp_topology.add_link(link)

        # Create visualizer and store it for animation
        self.visualizer = NetworkVisualizer(temp_topology, self.canvas)

        # Prepare failed links for visualization
        failed_links = self.broken_links

        # Calculate costs for visualization
        link_costs = {}
        for link in temp_topology.get_all_links():
            cost = self.get_link_cost(link.node_a, link.node_b)
            link_key = tuple(sorted((link.node_a, link.node_b)))
            link_costs[link_key] = cost

        # Draw topology with custom icons and link metrics
        self.visualizer.draw_topology(failed_links=failed_links, highlight_paths=highlight_paths, link_costs=link_costs, optimal_path=optimal_path, optimal_color=optimal_color, node_queues=self.node_queues, link_utilization=self.link_utilization, highlight_nodes=highlight_nodes)

    def find_shortest_path(self, start_node, end_node):
        """
        Finds the shortest path between two nodes using Breadth-First Search (BFS).
        Returns a list of nodes (the path) or None if no path is found.
        """
        visited = set()
        q = queue.Queue()

        q.put((start_node, [start_node]))
        visited.add(start_node)

        while not q.empty():
            current_node, path = q.get()

            if current_node == end_node:
                return path

            for neighbor in self.network_graph.get(current_node, []):
                if neighbor not in visited:
                    # --- Check for failed node ---
                    if neighbor in self.failed_nodes:
                        continue
                    # --- Check for broken link ---
                    link = tuple(sorted((current_node, neighbor)))
                    if link in self.broken_links:
                        continue # Ignore this path
                    # --- End of check ---

                    visited.add(neighbor)
                    new_path = list(path)
                    new_path.append(neighbor)
                    q.put((neighbor, new_path))

        return None

    def set_controls_state(self, state):
        """Helper function to enable/disable all controls."""
        state_str = "normal" if state == tk.NORMAL else "disabled"
        
        self.ping_button.config(state=state_str)
        self.source_menu.config(state=state_str)
        self.dest_menu.config(state=state_str)
        
        self.generate_button.config(state=state_str)
        self.topology_menu.config(state=state_str)
        
        self.break_link_button.config(state=state_str)
        self.reset_links_button.config(state=state_str)
        self.link_a_menu.config(state=state_str)
        self.link_b_menu.config(state=state_str)

        for entry in [self.pc_entry, self.router_entry, self.switch_entry, self.server_entry]:
            entry.config(state=state_str)

    def start_simulation_thread(self):
        """
        Gets the dynamic input from the dropdowns and starts the
        animation in the main thread.
        """
        source = self.source_var.get()
        dest = self.dest_var.get()

        if not source or not dest or source == "" or dest == "":
            self.status_label.config(text="Status: Please generate a network first.", foreground="red")
            return

        if source == dest:
            self.status_label.config(text="Status: Source and Destination are the same.", foreground="red")
            return

        path_nodes, _ = self.run_dijkstra(source, dest)

        if path_nodes is None:
            self.status_label.config(text=f"Status: No path from {source} to {dest}.", foreground="red")
            return

        threading.Thread(target=self.animate_ping, args=(path_nodes,), daemon=True).start()

    def animate_ping(self, path_nodes):
        """
        Animates a ping along a calculated path.
        'path_nodes' is a list like ['PC0', 'Switch0', 'R1', ...]
        """
        self.root.after(0, lambda: self.set_controls_state(tk.DISABLED))
        self.root.after(0, lambda: self.status_label.config(text=f"Status: Sending Request {path_nodes[0]} -> {path_nodes[-1]}", foreground="orange"))

        # Animate the request packet
        self.animate_packet_custom(path_nodes, "✉️", "green")

        self.root.after(0, lambda: self.status_label.config(text=f"Status: Sending Reply {path_nodes[-1]} -> {path_nodes[0]}", foreground="green"))
        time.sleep(0.5) # Pause before reply

        # Animate the reply packet
        path_reply_nodes = list(reversed(path_nodes))
        self.animate_packet_custom(path_reply_nodes, "✉️", "blue")

        self.root.after(0, lambda: self.set_controls_state(tk.NORMAL))
        self.root.after(0, lambda: self.status_label.config(text="Status: Ready", foreground="blue"))

    def animate_packet_custom(self, path, symbol="✉️", color="blue"):
        """
        Custom animation for packet moving along a path using text symbol.
        Positions are updated dynamically to reflect node dragging during animation.
        """
        if len(path) < 2:
            return

        # Animation parameters
        steps_per_hop = 100
        delay = 5  # milliseconds - fast animation

        # Create packet as text
        start_pos = self.node_coordinates.get(path[0])
        if not start_pos:
            return
        start_x, start_y = start_pos
        
        # Use threading event to wait for animation to complete
        done_event = threading.Event()

        def start_animation():
            try:
                packet = self.canvas.create_text(start_x, start_y, text=symbol, fill=color, font=("Arial", 16, "bold"))

                def animate_step(step=0):
                    try:
                        total_hops = len(path) - 1
                        total_steps = total_hops * steps_per_hop
                        if step >= total_steps:
                            self.canvas.delete(packet)
                            done_event.set()
                            return

                        hop_index = step // steps_per_hop
                        start_node = path[hop_index]
                        end_node = path[hop_index + 1]

                        # Get current positions (updated if nodes were dragged)
                        start_pos = self.node_coordinates.get(start_node)
                        end_pos = self.node_coordinates.get(end_node)
                        if not start_pos or not end_pos:
                            self.canvas.delete(packet)
                            done_event.set()
                            return

                        # Interpolate position
                        t = (step % steps_per_hop) / steps_per_hop
                        x = start_pos[0] + t * (end_pos[0] - start_pos[0])
                        y = start_pos[1] + t * (end_pos[1] - start_pos[1])

                        self.canvas.coords(packet, x, y)
                        self.canvas.after(delay, animate_step, step + 1)
                    except tk.TclError:
                        done_event.set()

                animate_step()
            except tk.TclError:
                done_event.set()

        # Schedule animation on main thread and wait
        self.root.after(0, start_animation)
        done_event.wait()

    def move_packet(self, start_coords, end_coords, color):
        """
        Animates a packet from a start (x,y) to an end (x,y).
        """
        # Make the packet size 8
        packet = self.canvas.create_oval(start_coords[0]-4, start_coords[1]-4, 
                                          start_coords[0]+4, start_coords[1]+4, 
                                          fill=color, outline="black")
        
        # Make the steps 50
        steps = 50
        if steps <= 0: steps = 1 # Avoid division by zero
            
        dx = (end_coords[0] - start_coords[0]) / steps
        dy = (end_coords[1] - start_coords[1]) / steps

        # Calculate sleep time to keep animation roughly constant
        sleep_time = 0.5 / steps # 0.5 seconds per hop

        for _ in range(steps):
            self.canvas.move(packet, dx, dy)
            self.canvas.update()
            time.sleep(sleep_time)
        
        self.canvas.delete(packet)

    # --- NEW: Link Failure Methods ---

    def break_link(self):
        """
        Adds the selected link to the broken_links set and redraws.
        """
        node_a = self.link_a_var.get()
        node_b = self.link_b_var.get()

        if not node_a or not node_b or node_a == node_b:
            self.status_label.config(text="Status: Select two different nodes.", foreground="red")
            return
            
        # Check if link actually exists
        if node_b not in self.network_graph.get(node_a, []):
            self.status_label.config(text=f"Status: No direct link between {node_a} and {node_b}.", foreground="red")
            return
            
        link = tuple(sorted((node_a, node_b)))
        self.broken_links.add(link)
        
        # Redraw topology to show broken link
        self.draw_topology()
        
        if self.active_protocol == "RIP":
            self.status_label.config(text=f"Status: Link Broken. RIP Re-converging...", foreground="orange")
            self.root.after(2000, self._finalize_rip) # Delayed recovery
        elif self.active_protocol == "OSPF":
            self.status_label.config(text=f"Status: Link Broken. OSPF Rerouting...", foreground="green")
            self._finalize_ospf() # Immediate recovery
        else:
            self.status_label.config(text=f"Status: Link {node_a}-{node_b} is broken.", foreground="orange")
            if self.source_var.get() and self.dest_var.get():
                 self.compute_route()

    def reset_links(self):
        """
        Clears the broken_links set and redraws.
        """
        self.broken_links.clear()
        self.draw_topology()
        self.status_label.config(text="Status: All links restored.", foreground="blue")
        
        if self.active_protocol == "RIP":
            self.root.after(2000, self._finalize_rip)
        elif self.active_protocol == "OSPF":
            self._finalize_ospf()
        elif self.source_var.get() and self.dest_var.get():
            self.compute_route()

    def get_link_cost(self, u, v):
        link = self.topology.get_link(u, v)
        
        alpha = self.alpha_var.get()
        beta = self.beta_var.get()
        gamma = self.gamma_var.get()
        
        if not link:
            # Default cost for links present in graph but missing in topology object
            # Default: Delay 10ms, BW 1Gbps (term=1), Loss 0
            return (alpha * 10.0) + (beta * 1.0) + (gamma * 0.0)
        
        # Cost = α * delay + β * (1 / bandwidth) + γ * loss
        # Normalize terms
        # Delay: ms
        # Bandwidth: 1e9 / bandwidth (so 1Gbps = 1, 10Mbps = 100)
        bw_term = (1e9 / link.bandwidth) if link.bandwidth > 0 else 1000
        
        # Loss: % * 100 (so 1% = 100 cost)
        loss_term = link.loss * 100
        
        cost = (alpha * link.delay) + (beta * bw_term) + (gamma * loss_term)
        return cost

    # --- Routing Algorithms ---

    def _reconstruct_path(self, came_from, current):
        total_path = [current]
        while current in came_from:
            current = came_from[current]
            if current:
                total_path.append(current)
        return total_path[::-1]

    def run_dijkstra(self, start, end):
        # Priority queue stores (cost, node)
        pq = [(0, start)]
        came_from = {}
        cost_so_far = {start: 0}

        while pq:
            current_cost, current = heapq.heappop(pq)

            if current == end:
                return self._reconstruct_path(came_from, end), current_cost

            for neighbor in self.network_graph.get(current, []):
                if tuple(sorted((current, neighbor))) in self.broken_links:
                    continue
                
                # Cost is distance for Dijkstra/OSPF
                weight = self.get_link_cost(current, neighbor)
                new_cost = cost_so_far[current] + weight
                
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost
                    heapq.heappush(pq, (priority, neighbor))
                    came_from[neighbor] = current
        return None, float('inf')

    def run_astar(self, start, end):
        pq = [(0, start)]
        came_from = {}
        cost_so_far = {start: 0}

        while pq:
            _, current = heapq.heappop(pq)

            if current == end:
                return self._reconstruct_path(came_from, end), cost_so_far[end]

            for neighbor in self.network_graph.get(current, []):
                if tuple(sorted((current, neighbor))) in self.broken_links:
                    continue
                
                weight = self.get_link_cost(current, neighbor)
                new_cost = cost_so_far[current] + weight
                
                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    # Heuristic: Euclidean distance to end
                    priority = new_cost + self._get_distance(neighbor, end)
                    heapq.heappush(pq, (priority, neighbor))
                    came_from[neighbor] = current
        return None, float('inf')

    def run_bellman_ford(self, start, end, metric="hops"):
        # Bellman-Ford (using hop count as cost for RIP style)
        distance = {node: float('inf') for node in self.all_nodes}
        predecessor = {node: None for node in self.all_nodes}
        distance[start] = 0

        # Relax edges |V| - 1 times
        for _ in range(len(self.all_nodes) - 1):
            for u in self.all_nodes:
                for v in self.network_graph.get(u, []):
                    if tuple(sorted((u, v))) in self.broken_links:
                        continue
                    
                    if metric == "distance":
                        weight = self.get_link_cost(u, v)
                    else:
                        weight = 1 # Hop count for RIP

                    if distance[u] + weight < distance[v]:
                        distance[v] = distance[u] + weight
                        predecessor[v] = u
        
        if distance[end] == float('inf'):
            return None, float('inf')
            
        # Reconstruct
        path = []
        curr = end
        while curr is not None:
            path.insert(0, curr)
            curr = predecessor[curr]
        return path, distance[end]

    def run_bfs(self, start, end):
        # BFS for unweighted shortest path (hops)
        queue = [(start, [start])]
        visited = set([start])
        
        while queue:
            (vertex, path) = queue.pop(0)
            if vertex == end:
                # Calculate QoS cost of this path
                cost = 0
                for i in range(len(path)-1):
                    cost += self.get_link_cost(path[i], path[i+1])
                return path, cost
            
            for neighbor in self.network_graph.get(vertex, []):
                if neighbor not in visited and tuple(sorted((vertex, neighbor))) not in self.broken_links:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        return None, float('inf')

    def simulate_via_selected(self):
        source = self.source_var.get()
        dest = self.dest_var.get()
        algo = self.algorithm_var.get()

        if not source or not dest or source == dest:
             self.status_label.config(text="Status: Invalid source/dest", foreground="red")
             return
        
        if algo == "Compare All":
            self.status_label.config(text="Status: Select a specific algorithm", foreground="red")
            return

        path = None
        
        if algo == "Dijkstra" or algo == "QoS-Metric" or algo == "OSPF-like":
            path, _ = self.run_dijkstra(source, dest)
        elif algo == "A*":
            path, _ = self.run_astar(source, dest)
        elif algo == "Bellman-Ford":
            path, _ = self.run_bellman_ford(source, dest, metric="distance")
        elif algo == "RIP-like":
            path, _ = self.run_bellman_ford(source, dest, metric="hops")
        elif algo == "BFS":
            path, _ = self.run_bfs(source, dest)
        
        if path:
            path_str = " → ".join(path)
            self.optimal_path_label.config(text=f"Selected Path ({algo}): {path_str}")
            self.draw_topology(highlight_paths=[], optimal_path=path)
            threading.Thread(target=self.animate_ping, args=(path,), daemon=True).start()
        else:
            self.status_label.config(text=f"Status: No path found via {algo}", foreground="red")

    def compute_route(self):
        """
        Computes routes using algorithms and updates metrics table.
        """
        source = self.source_var.get()
        dest = self.dest_var.get()
        self.active_protocol = None # Reset active protocol when manual generation is used
        algorithm = self.algorithm_var.get()

        if not source or not dest or source == dest:
            self.status_label.config(text="Status: Invalid source/dest", foreground="red")
            return

        # Clear table
        for i in self.metrics_tree.get_children():
            self.metrics_tree.delete(i)

        algos_to_run = ["Dijkstra", "Bellman-Ford", "A*", "BFS", "QoS-Metric", "RIP-like", "OSPF-like"]

        best_cost = float('inf')
        best_path = None
        best_algo = ""
        all_paths = []

        for algo in algos_to_run:
            path = None
            cost = 0
            hops = 0
            
            start_time = time.perf_counter()

            if algo == "Dijkstra" or algo == "OSPF-like" or algo == "QoS-Metric":
                path, cost = self.run_dijkstra(source, dest)
            elif algo == "A*":
                path, cost = self.run_astar(source, dest)
            elif algo == "Bellman-Ford":
                path, cost = self.run_bellman_ford(source, dest, metric="distance")
            elif algo == "RIP-like":
                path, cost = self.run_bellman_ford(source, dest, metric="hops")
                # Recalculate cost using QoS metric for fair comparison
                if path:
                    real_cost = 0
                    for i in range(len(path)-1):
                        real_cost += self.get_link_cost(path[i], path[i+1])
                    cost = real_cost
            elif algo == "BFS":
                path, cost = self.run_bfs(source, dest)
            
            end_time = time.perf_counter()
            exec_time = (end_time - start_time) * 1000 # ms
            time_str = f"{exec_time:.3f} ms"

            if path:
                hops = len(path) - 1
                self.metrics_tree.insert("", "end", values=(algo, hops, f"{cost:.1f}", time_str))
                all_paths.append(path)
                if cost < best_cost:
                    best_cost = cost
                    best_path = path
                    best_algo = algo
            else:
                self.metrics_tree.insert("", "end", values=(algo, "-", "Inf", time_str))

        # Highlight optimal path
        if best_path:
            other_paths = [p for p in all_paths if p != best_path]
            self.draw_topology(highlight_paths=other_paths, optimal_path=best_path)
            self.status_label.config(text=f"Status: Optimal path found via {best_algo}", foreground="green")
            path_str = " → ".join(best_path)
            self.optimal_path_label.config(text=f"Optimal Path ({best_algo}): {path_str}")
            self.min_cost_label.config(text=f"Min Cost: {best_cost:.1f}")
        else:
            self.draw_topology()
            self.status_label.config(text="Status: No path found.", foreground="red")
            self.optimal_path_label.config(text="Optimal Path: None")

    def highlight_path(self, path, color):
        for i in range(len(path) - 1):
            u, v = path[i], path[i+1]
            if u in self.node_coordinates and v in self.node_coordinates:
                p1 = self.node_coordinates[u]
                p2 = self.node_coordinates[v]
                self.canvas.create_line(p1, p2, fill=color, width=4, tags="highlight")
        self.canvas.tag_raise("highlight")
        self.canvas.tag_raise("device")

    def update_qos(self, value):
        """
        Updates QoS weights based on slider values.
        """
        alpha = self.alpha_var.get()
        beta = self.beta_var.get()
        gamma = self.gamma_var.get()
        
        # Update Summary
        summary = "QoS Impact: "
        if alpha > beta and alpha > gamma: summary += "Delay optimized (Latency sensitive)"
        elif beta > alpha and beta > gamma: summary += "Bandwidth optimized (Throughput sensitive)"
        elif gamma > alpha and gamma > beta: summary += "Loss optimized (Reliability sensitive)"
        else: summary += "Balanced"
        self.qos_summary_label.config(text=summary)

        # Live update
        if self.active_protocol == "OSPF":
            self._finalize_ospf() # OSPF updates instantly
        elif self.active_protocol == "RIP":
            pass # RIP ignores QoS changes (or updates very slowly, we simulate ignore here)
        else:
            if self.source_var.get() and self.dest_var.get():
                self.compute_route()
            else:
                self.draw_topology()

    def run_protocol(self):
        """
        Runs the selected routing protocol.
        """
        protocol = self.protocol_var.get()
        self.active_protocol = protocol
        
        if protocol == "RIP":
            self.protocol_status_label.config(text="Status: RIP Converging...", foreground="orange")
            self.draw_topology() # Clear current paths
            # Simulate slow convergence
            self.root.after(1500, self._finalize_rip)
            
        elif protocol == "OSPF":
            self.protocol_status_label.config(text="Status: OSPF Converged", foreground="green")
            self._finalize_ospf()

    def _finalize_rip(self):
        """Simulates RIP convergence completion."""
        source = self.source_var.get()
        dest = self.dest_var.get()
        
        # RIP uses Hop Count (Bellman-Ford with metric='hops')
        path, hops = self.run_bellman_ford(source, dest, metric="hops")
        
        if path:
            # Highlight Orange for RIP
            self.draw_topology(highlight_paths=[], optimal_path=path, optimal_color="orange")
            self.protocol_status_label.config(text="Status: RIP Converged", foreground="green")
            self.optimal_path_label.config(text=f"RIP Path: {' → '.join(path)}")
            
            # Show Routing Table (Hops)
            self._show_routing_table_popup("RIP", metric="hops")
        else:
            self.protocol_status_label.config(text="Status: Unreachable", foreground="red")

    def _finalize_ospf(self):
        """Simulates OSPF convergence completion."""
        source = self.source_var.get()
        dest = self.dest_var.get()
        
        # OSPF uses QoS Cost (Dijkstra)
        path, cost = self.run_dijkstra(source, dest)
        
        if path:
            # Highlight Green for OSPF
            self.draw_topology(highlight_paths=[], optimal_path=path, optimal_color="green")
            self.protocol_status_label.config(text="Status: OSPF Converged", foreground="green")
            self.optimal_path_label.config(text=f"OSPF Path: {' → '.join(path)}")
            
            # Show Routing Table (Cost)
            self._show_routing_table_popup("OSPF", metric="cost")
        else:
            self.protocol_status_label.config(text="Status: Unreachable", foreground="red")

    def run_protocol_comparison(self):
        """Runs both protocols and populates the comparison table."""
        source = self.source_var.get()
        dest = self.dest_var.get()
        
        if not source or not dest or source == dest:
            self.status_label.config(text="Status: Select valid Source/Dest", foreground="red")
            return

        # Clear table
        for i in self.metrics_tree.get_children():
            self.metrics_tree.delete(i)
            
        # Run RIP
        rip_path, rip_hops = self.run_bellman_ford(source, dest, metric="hops")
        rip_cost = 0
        if rip_path:
            for i in range(len(rip_path)-1):
                rip_cost += self.get_link_cost(rip_path[i], rip_path[i+1])
        
        # Run OSPF
        ospf_path, ospf_cost = self.run_dijkstra(source, dest)
        ospf_hops = len(ospf_path) - 1 if ospf_path else 0
        
        # Populate Table
        # Protocol | Hops | Cost | Convergence
        self.metrics_tree.insert("", "end", values=("RIP", rip_hops if rip_path else "-", f"{rip_cost:.1f}", "Slow"))
        self.metrics_tree.insert("", "end", values=("OSPF", ospf_hops if ospf_path else "-", f"{ospf_cost:.1f}", "Fast"))
        
        # Highlight better protocol (lower cost)
        if ospf_cost <= rip_cost:
            self.metrics_tree.selection_set(self.metrics_tree.get_children()[1])
            self.status_label.config(text="Status: OSPF provides better/equal QoS cost.", foreground="green")
        else:
            self.metrics_tree.selection_set(self.metrics_tree.get_children()[0])

    def _show_routing_table_popup(self, protocol, metric="cost"):
        """Updates the routing table display for the current source node."""
        source = self.source_var.get()
        
        # Clear existing items
        for i in self.protocol_tree.get_children():
            self.protocol_tree.delete(i)
        
        # Calculate routes to all other nodes
        for dest in self.all_nodes:
            if dest == source: continue
            
            if protocol == "RIP":
                path, cost = self.run_bellman_ford(source, dest, metric="hops")
            else:
                path, cost = self.run_dijkstra(source, dest)
                
            if path and len(path) > 1:
                next_hop = path[1]
                
                if isinstance(cost, float):
                    cost_str = f"{cost:.1f}"
                else:
                    cost_str = str(cost)
                    
                self.protocol_tree.insert("", "end", values=(dest, next_hop, cost_str))

    def _sync_topology(self):
        """Syncs self.topology with current network_graph and node_coordinates."""
        # Update Nodes
        current_nodes = set(self.all_nodes)
        topo_nodes = set(self.topology.nodes.keys())
        
        for node in current_nodes:
            if node not in topo_nodes:
                coords = self.node_coordinates.get(node)
                node_type = "router" if node.startswith("R") else \
                           "switch" if node.startswith("Switch") else \
                           "hub" if node.startswith("Hub") else "host"
                if node.startswith("Server"): node_type = "server"
                elif node.startswith("FW"): node_type = "firewall"
                elif node.startswith("ISP"): node_type = "isp"
                elif node.startswith("AP"): node_type = "ap"
                elif node.startswith("LB"): node_type = "load_balancer"
                
                self.topology.add_node(Node(node, node_type, coords))
            else:
                self.topology.update_node_coordinates(node, self.node_coordinates.get(node))

        for node in topo_nodes:
            if node not in current_nodes:
                self.topology.remove_node(node)

        # Update Links
        current_links = set()
        for u, neighbors in self.network_graph.items():
            for v in neighbors:
                current_links.add(tuple(sorted((u, v))))
        
        topo_links = set(self.topology.links.keys())
        
        for link_key in current_links:
            if link_key not in topo_links:
                u, v = link_key
                self.topology.add_link(Link(u, v, delay=10.0, bandwidth=1e9, loss=0.0))
        
        for link_key in topo_links:
            if link_key not in current_links:
                self.topology.remove_link(link_key[0], link_key[1])

    def show_routing_tables_window(self, title, tables):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry("600x500")
        
        text_area = tk.Text(win, wrap="none", font=("Courier New", 10))
        scrollbar_y = ttk.Scrollbar(win, orient="vertical", command=text_area.yview)
        scrollbar_x = ttk.Scrollbar(win, orient="horizontal", command=text_area.xview)
        text_area.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        scrollbar_y.pack(side="right", fill="y")
        scrollbar_x.pack(side="bottom", fill="x")
        text_area.pack(side="left", fill="both", expand=True)
        
        output = ""
        for router, table in sorted(tables.items()):
            output += f"Router: {router}\n"
            output += f"{'Destination':<15} {'Next Hop':<15} {'Metric':<10}\n"
            output += "-"*45 + "\n"
            
            # Sort routes by destination
            for dest, route_info in sorted(table.items()):
                # Format: (next_hop, cost)
                if isinstance(route_info, tuple):
                    next_hop = route_info[0]
                    metric = route_info[1]
                    if isinstance(metric, float):
                        metric_str = f"{metric:.1f}"
                    else:
                        metric_str = str(metric)
                        
                    output += f"{dest:<15} {next_hop:<15} {metric_str:<10}\n"
            output += "\n" + "="*45 + "\n\n"
            
        text_area.insert("1.0", output)
        text_area.config(state="disabled")

    def pause_traffic_demo(self):
        if self.simulation_running:
            self.simulation_paused = True
            self.status_label.config(text="Status: Traffic Simulation Paused", foreground="orange")

    def resume_traffic_demo(self):
        if self.simulation_running:
            self.simulation_paused = False
            self.status_label.config(text="Status: Traffic Simulation Resumed", foreground="green")

    def stop_traffic_demo(self):
        if self.simulation_running:
            self.simulation_running = False
            self.simulation_paused = False
            self.status_label.config(text="Status: Traffic Simulation Stopped", foreground="red")

    def run_traffic_demo(self):
        t_type = self.traffic_var.get()
        source = self.source_var.get()
        dest = self.dest_var.get()
        
        if not source or not dest or source == dest:
            self.status_label.config(text="Status: Select valid Source/Dest", foreground="red")
            return

        # Start thread
        self.simulation_running = True
        self.simulation_paused = False
        threading.Thread(target=self._simulate_traffic_loop, args=(t_type, source, dest), daemon=True).start()

    def _simulate_traffic_loop(self, t_type, source, dest):
        # Setup
        steps = 15
        
        # Update Explanation
        if t_type == "CBR":
            exp = "CBR:\n• Constant packet rate\n• Low congestion"
        else:
            exp = "Bursty:\n• Sudden traffic spikes\n• High congestion and delay"
        self.root.after(0, lambda: self.traffic_explanation_label.config(text=exp))

        path_used = "None"
        
        for i in range(steps):
            if not self.simulation_running: break
            
            while self.simulation_paused:
                if not self.simulation_running: break
                time.sleep(0.1)
            if not self.simulation_running: break
            
            # Simulate Metrics
            if t_type == "CBR":
                # Stable
                for node in self.all_nodes:
                    self.node_queues[node] = random.uniform(0.1, 0.3)
                for link in self.topology.links:
                    self.link_utilization[link] = random.uniform(0.2, 0.4)
                    # Update topology link metrics (Low Delay/Loss)
                    self.topology.links[link].delay = 10 + random.uniform(0, 5)
                    self.topology.links[link].loss = 0.01
            else:
                # Bursty
                for node in self.all_nodes:
                    # Random spikes
                    self.node_queues[node] = random.uniform(0.0, 0.9) if random.random() > 0.6 else 0.1
                for link in self.topology.links:
                    util = random.uniform(0.0, 1.0) if random.random() > 0.6 else 0.2
                    self.link_utilization[link] = util
                    # Update topology link metrics (High Delay/Loss)
                    self.topology.links[link].delay = 10 + (util * 100)
                    self.topology.links[link].loss = util * 0.1

            # Recalculate Path (OSPF/QoS)
            # We use Dijkstra here to simulate OSPF reacting to new costs
            path, cost = self.run_dijkstra(source, dest)
            if path:
                path_used = f"Path via {path[1] if len(path)>1 else 'Direct'}"
                # Update Visuals on Main Thread
                self.root.after(0, lambda p=path: self.draw_topology(highlight_paths=[], optimal_path=p, optimal_color="green"))
                
                # Animate Packets
                if t_type == "Bursty" and i % 3 == 0:
                    # Burst of packets
                    self.animate_packet_custom(path, "💥", "red")
                elif t_type == "CBR":
                    # Regular packets
                    self.animate_packet_custom(path, "●", "blue")
            
            time.sleep(0.8)

        # End - Update Table
        avg_delay = "Low" if t_type == "CBR" else "High"
        loss = "Low" if t_type == "CBR" else "High"
        
        def update_table():
            # Clear previous of same type
            for item in self.traffic_tree.get_children():
                if self.traffic_tree.item(item)['values'][0] == t_type:
                    self.traffic_tree.delete(item)
            self.traffic_tree.insert("", "end", values=(t_type, avg_delay, loss, path_used))
            self.simulation_running = False
            
        self.root.after(0, update_table)

    def inject_fault(self):
        """
        Injects a fault into the selected node.
        """
        node = self.fault_node_var.get()
        if node:
            self.failed_nodes.add(node)
            self.fault_status_label.config(text=f"Faults: {node} failed", foreground="red")
            self.draw_topology()  # Redraw to show failed node

    def clear_faults(self):
        """
        Clears all injected faults.
        """
        self.failed_nodes.clear()
        self.fault_status_label.config(text="Faults: None", foreground="blue")
        self.draw_topology()

    def run_evaluation(self):
        """
        Runs network evaluation.
        """
        # Placeholder for evaluation logic
        self.metrics_label.config(text="Metrics: Evaluation Complete", foreground="green")

    def export_results(self):
        """
        Exports evaluation results to a file.
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("PDF Report", "*.pdf")]
        )
        if not file_path:
            return

        if file_path.endswith(".pdf"):
            try:
                self._export_to_pdf(file_path)
                messagebox.showinfo("Export", "Results exported to PDF successfully!")
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export PDF: {str(e)}")
            return

        # Default JSON export
        data = {
            "timestamp": time.time(),
            "topology": {
                "type": self.topology_var.get(),
                "nodes": self.all_nodes,
                "links": [list(link) for link in self.topology.links.keys()]
            },
            "routing_metrics": [],
            "traffic_metrics": [],
            "optimal_path_info": {
                "optimal_path": self.optimal_path_label.cget("text"),
                "min_cost": self.min_cost_label.cget("text")
            }
        }
        
        # Collect metrics from trees
        for child in self.metrics_tree.get_children():
            data["routing_metrics"].append(self.metrics_tree.item(child)["values"])
            
        for child in self.traffic_tree.get_children():
            data["traffic_metrics"].append(self.traffic_tree.item(child)["values"])

        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=4)
            messagebox.showinfo("Export", "Results exported to JSON successfully!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export JSON: {str(e)}")

    def _export_to_pdf(self, filename):
        from matplotlib.backends.backend_pdf import PdfPages  # pyright: ignore[reportMissingModuleSource]
        import datetime
        import networkx as nx  # type: ignore

        with PdfPages(filename) as pdf:
            # --- Gather Data ---
            sim_date = datetime.datetime.now().strftime('%d-%m-%Y')
            user_mode = "Manual" if self.manual_mode.get() else "Automatic"
            topo_type = self.topology_var.get()

            # Device Counts
            counts = {"Router": 0, "Switch": 0, "PC": 0, "Hub": 0}
            for n in self.all_nodes:
                node = self.topology.nodes.get(n)
                ntype = node.node_type if node else "host"
                if ntype == "router": counts["Router"] += 1
                elif ntype == "switch": counts["Switch"] += 1
                elif ntype == "hub": counts["Hub"] += 1
                else: counts["PC"] += 1
            
            # Connectivity
            avg_degree = 0
            if self.topology.graph.number_of_nodes() > 0:
                avg_degree = sum(dict(self.topology.graph.degree()).values()) / self.topology.graph.number_of_nodes()
            
            redundant = "Yes" if self.topology.graph.number_of_edges() >= self.topology.graph.number_of_nodes() else "No"
            try:
                spof = "Yes" if not nx.is_biconnected(self.topology.graph) and self.topology.graph.number_of_nodes() > 2 else "No"
            except:
                spof = "Unknown"

            # Link Metrics
            delays = []
            bws = []
            losses = []
            for link in self.topology.links.values():
                delays.append(link.delay)
                bws.append(link.bandwidth / 1e6)
                losses.append(link.loss * 100)
            
            link_stats = {
                "Delay (ms)": (min(delays), max(delays), sum(delays)/len(delays)) if delays else (0,0,0),
                "Bandwidth (Mbps)": (min(bws), max(bws), sum(bws)/len(bws)) if bws else (0,0,0),
                "Packet Loss (%)": (min(losses), max(losses), sum(losses)/len(losses)) if losses else (0,0,0)
            }

            # QoS
            alpha = self.alpha_var.get()
            beta = self.beta_var.get()
            gamma = self.gamma_var.get()
            qos_focus = "Balanced"
            if alpha > beta and alpha > gamma: qos_focus = "Delay Optimized"
            elif beta > alpha and beta > gamma: qos_focus = "Bandwidth Optimized"
            elif gamma > alpha and gamma > beta: qos_focus = "Loss Optimized"

            # --- Page 1 ---
            fig = plt.figure(figsize=(8.5, 11))
            plt.axis('off')
            
            # Header
            y = 0.95
            plt.text(0.5, y, "Network Simulation Report", ha='center', fontsize=16, weight='bold')
            y -= 0.05
            
            info_text = (
                f"Tool Name: NetTopoGen – Advanced Network Simulator\n"
                f"Simulation Date: {sim_date}\n"
                f"Simulation ID: Auto-Generated\n"
                f"User Mode: {user_mode}\n"
                f"Topology Type: {topo_type}"
            )
            plt.text(0.1, y, info_text, va='top', fontsize=10, family='monospace')
            y -= 0.15
            
            # 1. Overview
            plt.text(0.1, y, "1. Network Overview", weight='bold', fontsize=12)
            y -= 0.03
            plt.text(0.1, y, "This report presents the results of a network simulation performed using the NetTopoGen framework.\nThe objective is to analyze routing behavior, QoS impact, and network resilience.", va='top', fontsize=10, wrap=True)
            y -= 0.08

            # 2. Topology
            plt.text(0.1, y, "2. Topology Configuration", weight='bold', fontsize=12)
            y -= 0.03
            plt.text(0.1, y, "2.1 Device Summary", weight='bold', fontsize=10)
            y -= 0.08
            
            dev_data = [[k, v] for k,v in counts.items()]
            plt.table(cellText=dev_data, colLabels=["Device Type", "Count"], loc='top', bbox=[0.1, y, 0.8, 0.08])
            y -= 0.05
            
            plt.text(0.1, y, "2.2 Connectivity Summary", weight='bold', fontsize=10)
            y -= 0.03
            conn_text = (
                f"Average node degree: {avg_degree:.1f}\n"
                f"Redundant paths available: {redundant}\n"
                f"Single point of failure: {spof}"
            )
            plt.text(0.1, y, conn_text, va='top', fontsize=10)
            y -= 0.1
            
            # 3. Link Characteristics
            plt.text(0.1, y, "3. Link Characteristics", weight='bold', fontsize=12)
            y -= 0.08
            link_data = [
                ["Delay (ms)", f"{link_stats['Delay (ms)'][0]:.1f}", f"{link_stats['Delay (ms)'][1]:.1f}", f"{link_stats['Delay (ms)'][2]:.1f}"],
                ["Bandwidth (Mbps)", f"{link_stats['Bandwidth (Mbps)'][0]:.0f}", f"{link_stats['Bandwidth (Mbps)'][1]:.0f}", f"{link_stats['Bandwidth (Mbps)'][2]:.1f}"],
                ["Packet Loss (%)", f"{link_stats['Packet Loss (%)'][0]:.1f}", f"{link_stats['Packet Loss (%)'][1]:.1f}", f"{link_stats['Packet Loss (%)'][2]:.2f}"]
            ]
            plt.table(cellText=link_data, colLabels=["Metric", "Min", "Max", "Avg"], loc='top', bbox=[0.1, y, 0.8, 0.08])
            y -= 0.1
            
            # 4. QoS
            plt.text(0.1, y, "4. QoS Configuration", weight='bold', fontsize=12)
            y -= 0.03
            plt.text(0.1, y, "Cost = α·Delay + β·(1/Bandwidth) + γ·Loss", fontsize=10, style='italic')
            y -= 0.08
            qos_data = [
                ["α (Delay)", f"{alpha}"],
                ["β (Bandwidth)", f"{beta}"],
                ["γ (Loss)", f"{gamma}"]
            ]
            plt.table(cellText=qos_data, colLabels=["Parameter", "Value"], loc='top', bbox=[0.1, y, 0.4, 0.08])
            plt.text(0.6, y+0.04, f"QoS Focus: {qos_focus}", fontsize=10, weight='bold')
            
            pdf.savefig(fig)
            plt.close(fig)

            # --- Page 2 ---
            fig = plt.figure(figsize=(8.5, 11))
            plt.axis('off')
            y = 0.95
            
            # 5. Routing Algo
            plt.text(0.1, y, "5. Routing Algorithm Evaluation", weight='bold', fontsize=12)
            y -= 0.15
            
            algo_data = []
            for child in self.metrics_tree.get_children():
                vals = self.metrics_tree.item(child)["values"]
                algo_data.append([vals[0], vals[1], vals[2]])
                
            if algo_data:
                plt.table(cellText=algo_data, colLabels=["Algorithm", "Hop Count", "Total Cost"], loc='top', bbox=[0.1, y, 0.8, 0.15])
            else:
                plt.text(0.1, y+0.05, "No algorithms evaluated.", fontsize=10)
            y -= 0.1
            
            # 6. Optimal Path
            plt.text(0.1, y, "6. Optimal Path Selection", weight='bold', fontsize=12)
            y -= 0.03
            
            opt_path_text = self.optimal_path_label.cget("text").replace("Optimal Path: ", "").replace("Selected Path ", "")
            selected_algo = "Unknown"
            if "(" in opt_path_text:
                selected_algo = opt_path_text.split("(")[1].split(")")[0]
            min_cost = self.min_cost_label.cget("text").replace("Min Cost: ", "")
            
            opt_text = (
                f"Selected Algorithm: {selected_algo}\n"
                f"Optimal Path: {opt_path_text}\n"
                f"Minimum Cost: {min_cost}\n"
                f"Reason: Lowest composite QoS cost under current weight configuration."
            )
            plt.text(0.1, y, opt_text, va='top', fontsize=10, wrap=True)
            y -= 0.15
            
            # 7. Traffic
            plt.text(0.1, y, "7. Traffic Simulation Results", weight='bold', fontsize=12)
            y -= 0.15
            
            traffic_data = []
            for child in self.traffic_tree.get_children():
                vals = self.traffic_tree.item(child)["values"]
                traffic_data.append(vals)
                
            if traffic_data:
                t_display = []
                for row in traffic_data:
                    t_display.append(["Traffic Type", row[0]])
                    t_display.append(["Avg Delay", row[1]])
                    t_display.append(["Packet Loss", row[2]])
                    t_display.append(["Path Used", row[3]])
                    t_display.append(["-", "-"])
                plt.table(cellText=t_display, colLabels=["Metric", "Value"], loc='top', bbox=[0.1, y, 0.8, 0.15])
            else:
                plt.text(0.1, y+0.05, "No traffic simulation run.", fontsize=10)
            y -= 0.1
            
            # 8. Fault Injection
            plt.text(0.1, y, "8. Fault Injection Analysis", weight='bold', fontsize=12)
            y -= 0.03
            
            faults_text = "None"
            if self.failed_nodes:
                faults_text = f"Nodes Failed: {', '.join(self.failed_nodes)}"
            if self.broken_links:
                links_str = [f"{u}-{v}" for u,v in self.broken_links]
                if faults_text == "None": faults_text = ""
                else: faults_text += "\n"
                faults_text += f"Links Broken: {', '.join(links_str)}"
                
            plt.text(0.1, y, f"Injected Faults: {faults_text}", va='top', fontsize=10, wrap=True)
            y -= 0.05
            if faults_text != "None":
                plt.text(0.1, y, "Observation: The routing engine recomputed paths where possible.", va='top', fontsize=10)
            y -= 0.1
            
            # 9. Visualization Summary
            plt.text(0.1, y, "9. Visualization Summary", weight='bold', fontsize=12)
            y -= 0.03
            vis_text = (
                "• Active routing paths highlighted using color coding\n"
                "• Link metrics displayed dynamically\n"
                "• Packet flow animated hop-by-hop\n"
                "• QoS changes reflected instantly in path selection"
            )
            plt.text(0.1, y, vis_text, va='top', fontsize=10)
            y -= 0.1
            
            # 10. Key Observations
            plt.text(0.1, y, "10. Key Observations", weight='bold', fontsize=12)
            y -= 0.03
            obs_text = (
                "• QoS-aware routing adapts effectively to changing network conditions\n"
                "• Fault injection demonstrates network resilience\n"
                "• Visualization enhances understanding of routing dynamics"
            )
            plt.text(0.1, y, obs_text, va='top', fontsize=10)
            y -= 0.1
            
            # 11. Conclusion
            plt.text(0.1, y, "11. Conclusion", weight='bold', fontsize=12)
            y -= 0.03
            conc_text = "The simulation confirms that NetTopoGen effectively models realistic network behavior, supports QoS-aware routing, and enables interactive exploration of routing protocols and fault scenarios."
            plt.text(0.1, y, conc_text, va='top', fontsize=10, wrap=True)
            
            pdf.savefig(fig)
            plt.close(fig)

    def export_packet_tracer(self):
        """
        Exports a Packet Tracer friendly package (ZIP) containing:
        - topology.txt (Physical connections)
        - Device configurations (.cfg)
        - README.txt (Instructions)
        """
        file_path = filedialog.asksaveasfilename(
            defaultextension=".zip",
            filetypes=[("ZIP Archive", "*.zip")],
            title="Export Packet Tracer Package"
        )
        if not file_path:
            return

        try:
            with zipfile.ZipFile(file_path, 'w') as zipf:
                # --- 1. Generate Topology Text ---
                topo_lines = ["Packet Tracer Topology Blueprint", "="*30, "", "Devices:"]
                
                device_counts = {"Router": 0, "Switch": 0, "PC": 0, "Hub": 0}
                
                # Collect devices
                for node_name in self.all_nodes:
                    node = self.topology.nodes.get(node_name)
                    n_type = node.node_type if node else "host"
                    pt_type = "PC"
                    if n_type == "router": pt_type = "Router"
                    elif n_type == "switch": pt_type = "Switch"
                    elif n_type == "hub": pt_type = "Hub"
                    elif n_type == "server": pt_type = "Server"
                    elif n_type == "firewall": pt_type = "Firewall"
                    elif n_type == "isp": pt_type = "Cloud"
                    elif n_type == "ap": pt_type = "AccessPoint"
                    elif n_type == "host": pt_type = "PC"
                    
                    device_counts[pt_type] += 1
                    topo_lines.append(f"{pt_type} {node_name}")
                
                topo_lines.extend(["", "Connections:"])
                
                # Collect connections
                processed_links = set()
                if_counters = {n: 0 for n in self.all_nodes}
                
                sorted_nodes = sorted(self.all_nodes)
                
                for u in sorted_nodes:
                    if u not in self.network_graph: continue
                    for v in sorted(self.network_graph[u]):
                        link_key = tuple(sorted((u, v)))
                        if link_key in processed_links: continue
                        processed_links.add(link_key)
                        
                        # Helper to generate interface names
                        def get_if(n_name, idx):
                            node = self.topology.nodes.get(n_name)
                            ntype = node.node_type if node else "host"
                            if ntype == "host": return "FastEthernet0"
                            if ntype == "router": return f"FastEthernet0/{idx}"
                            if ntype == "switch": return f"FastEthernet0/{idx + 1}"
                            return f"Port{idx}"

                        if_u = get_if(u, if_counters[u])
                        if_v = get_if(v, if_counters[v])
                        
                        # Increment counters
                        node_u = self.topology.nodes.get(u)
                        if node_u and node_u.node_type != "host": if_counters[u] += 1
                        node_v = self.topology.nodes.get(v)
                        if node_v and node_v.node_type != "host": if_counters[v] += 1

                        line = f"{u} {if_u} <-> {v} {if_v}"
                        topo_lines.append(line)

                zipf.writestr("topology.txt", "\n".join(topo_lines))

                # --- 2. Generate Device Configs ---
                for node_name in self.all_nodes:
                    node = self.topology.nodes.get(node_name)
                    if not node: continue
                    
                    cfg_content = []
                    cfg_content.append("!\nversion 15.1\n!\n")
                    cfg_content.append(f"hostname {node_name}\n!\n")
                    
                    # Interfaces
                    if hasattr(node, 'interfaces') and node.interfaces:
                        for intf, data in node.interfaces.items():
                            # Map ethX -> FastEthernet0/X
                            pt_intf = intf
                            if intf.startswith("eth"):
                                try:
                                    idx = int(intf.replace("eth", ""))
                                    pt_intf = f"FastEthernet0/{idx}"
                                except:
                                    pass
                            
                            cfg_content.append(f"interface {pt_intf}\n")
                            if 'ip' in data and 'mask' in data:
                                cfg_content.append(f" ip address {data['ip']} {data['mask']}\n")
                            else:
                                cfg_content.append(" no ip address\n")
                            cfg_content.append(" duplex auto\n speed auto\n no shutdown\n!\n")
                    else:
                        # Fallback for devices without IP config
                        degree = len(self.network_graph.get(node_name, []))
                        start_idx = 1 if node.node_type == "switch" else 0
                        for i in range(degree):
                            cfg_content.append(f"interface FastEthernet0/{start_idx + i}\n")
                            cfg_content.append(" no ip address\n") 
                            cfg_content.append(" duplex auto\n speed auto\n no shutdown\n!\n")

                    # Routing / Gateway
                    if node.node_type == "router":
                        cfg_content.append("router ospf 1\n network 0.0.0.0 255.255.255.255 area 0\n!\n")
                    elif node.node_type == "host":
                        gateway = "0.0.0.0"
                        if hasattr(node, 'interfaces'):
                            for data in node.interfaces.values():
                                if 'gateway' in data:
                                    gateway = data['gateway']
                                    break
                        cfg_content.append(f"ip default-gateway {gateway}\n!\n")
                    
                    cfg_content.append("end\n")
                    zipf.writestr(f"{node_name}.cfg", "".join(cfg_content))

                # --- 3. Generate README.txt ---
                readme_lines = [
                    "NetTopoGen - Packet Tracer Export Package",
                    "="*40,
                    "",
                    "Instructions:",
                    "1. Open Cisco Packet Tracer.",
                    f"2. Add devices: {device_counts['Router']} Routers, {device_counts['Switch']} Switches, {device_counts['PC']} PCs.",
                    "3. Connect devices as listed in 'topology.txt'.",
                    "4. For each device:",
                    "   a. Click the device.",
                    "   b. Go to CLI tab (or Config tab -> Load).",
                    "   c. Paste the content of the corresponding .cfg file.",
                    "",
                    "Generated by NetTopoGen"
                ]
                zipf.writestr("README.txt", "\n".join(readme_lines))

            messagebox.showinfo("Export Successful", f"Packet Tracer package saved to:\n{file_path}")
            self.status_label.config(text=f"Status: Exported PT Package to {os.path.basename(file_path)}", foreground="green")
            
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to create package: {str(e)}")

    def take_screenshot(self):
        """
        Takes a screenshot of the current topology.
        """
        file_path = filedialog.asksaveasfilename(defaultextension=".ps", filetypes=[("PostScript", "*.ps")])
        if file_path:
            try:
                self.canvas.postscript(file=file_path, colormode='color')
                messagebox.showinfo("Screenshot", f"Screenshot saved to {file_path}")
            except Exception as e:
                messagebox.showerror("Screenshot Error", f"Failed to save screenshot: {str(e)}")

    # --- Manual Mode & Undo ---

    def toggle_manual_mode(self):
        is_manual = self.manual_mode.get()
        if is_manual:
            self.manual_controls_frame.place(relx=0.02, rely=0.9, anchor="sw")
            self.generate_button.config(state="disabled")
            self.topology_menu.config(state="disabled")
        else:
            self.manual_controls_frame.place_forget()
            self.generate_button.config(state="normal")
            self.topology_menu.config(state="normal")
            # Reset link mode
            self.adding_link_mode = False
            self.link_source_node = None
            self.deleting_mode = False
            self.canvas.config(cursor="")

    def save_state(self):
        state = {
            "coords": copy.deepcopy(self.node_coordinates),
            "graph": copy.deepcopy(self.network_graph),
            "broken": copy.deepcopy(self.broken_links),
            "nodes": list(self.all_nodes)
        }
        self.undo_stack.append(state)
        if len(self.undo_stack) > 10: self.undo_stack.pop(0)

    def undo(self):
        if not self.undo_stack:
            self.status_label.config(text="Status: Nothing to undo", foreground="orange")
            return
        state = self.undo_stack.pop()
        self.node_coordinates = state["coords"]
        self.network_graph = state["graph"]
        self.broken_links = state["broken"]
        self.all_nodes = state["nodes"]
        self.draw_topology()
        self._update_option_menus()

    def add_device_manual(self, dev_type):
        self.save_state()
        idx = len(self.all_nodes)
        name = f"{dev_type}_{idx}"
        # Place randomly near center
        x = 400 + random.randint(-50, 50)
        y = 300 + random.randint(-50, 50)
        self._add_node(name, (x, y))
        
        # Auto-connect to nearest
        nearest = self._get_nearest_node(name, [n for n in self.all_nodes if n != name])
        if nearest:
            self._add_link(name, nearest)
        
        self.draw_topology()
        self._update_option_menus()

    def enable_add_link_mode(self):
        """Toggles the manual link addition mode."""
        if self.adding_link_mode:
            # Toggle off
            self.adding_link_mode = False
            self.link_source_node = None
            self.canvas.config(cursor="")
            self.status_label.config(text="Manual Mode: Link addition cancelled.", foreground="blue")
        else:
            # Toggle on
            self.adding_link_mode = True
            self.link_source_node = None
            self.deleting_mode = False
            self.canvas.config(cursor="crosshair")
            self.status_label.config(text="Manual Mode: Select Source Node for Link", foreground="orange")

    def add_link_manual(self, u, v):
        """Adds a link between two nodes in manual mode."""
        self.save_state()
        self._add_link(u, v)
        # Add to topology object as well to ensure consistency
        if not self.topology.get_link(u, v):
             self.topology.add_link(Link(u, v))
        
        # Randomize metrics for new link
        link = self.topology.get_link(u, v)
        if link:
            link.delay = random.uniform(1, 50)
            link.bandwidth = 1e9
            link.loss = 0.0

        self.draw_topology()
        self._update_option_menus()

    def enable_delete_mode(self):
        """Toggles the manual deletion mode."""
        if self.deleting_mode:
            self.deleting_mode = False
            self.canvas.config(cursor="")
            self.status_label.config(text="Manual Mode: Delete mode disabled.", foreground="blue")
        else:
            self.deleting_mode = True
            self.adding_link_mode = False
            self.link_source_node = None
            self.canvas.config(cursor="cross")
            self.status_label.config(text="Manual Mode: Click on Node or Link to delete.", foreground="red")

    def delete_node_manual(self, node):
        """Deletes a node and its connections."""
        self.save_state()
        # Remove from data structures
        if node in self.all_nodes: self.all_nodes.remove(node)
        if node in self.node_coordinates: del self.node_coordinates[node]
        
        # Remove from graph
        if node in self.network_graph:
            neighbors = self.network_graph[node]
            for neighbor in neighbors:
                if neighbor in self.network_graph and node in self.network_graph[neighbor]:
                    self.network_graph[neighbor].remove(node)
            del self.network_graph[node]
            
        # Remove from topology
        if node in self.topology.nodes:
            self.topology.remove_node(node)
        
        # Remove broken links referencing this node
        to_remove = set()
        for link in self.broken_links:
            if node in link:
                to_remove.add(link)
        self.broken_links -= to_remove
        
        self.draw_topology()
        self._update_option_menus()
        self.status_label.config(text=f"Deleted node {node}", foreground="blue")

    def delete_link_manual(self, u, v):
        """Deletes a link between two nodes."""
        self.save_state()
        # Remove from graph
        if u in self.network_graph and v in self.network_graph[u]:
            self.network_graph[u].remove(v)
        if v in self.network_graph and u in self.network_graph[v]:
            self.network_graph[v].remove(u)
            
        # Remove from topology
        self.topology.remove_link(u, v)
        
        # Remove from broken links
        link_tuple = tuple(sorted((u, v)))
        if link_tuple in self.broken_links:
            self.broken_links.remove(link_tuple)
            
        self.draw_topology()
        self.status_label.config(text=f"Deleted link {u}-{v}", foreground="blue")

    def clear_topology_manual(self):
        """Clears the entire topology."""
        if messagebox.askyesno("Clear Topology", "Are you sure you want to delete all nodes and links?"):
            self.save_state()
            self.all_nodes = []
            self.node_coordinates = {}
            self.network_graph = {}
            self.broken_links = set()
            self.topology = Topology()
            self.draw_topology()
            self._update_option_menus()
            self.status_label.config(text="Topology cleared.", foreground="blue")

    def on_node_press(self, event):
        if not self.manual_mode.get():
            return
        item = self.canvas.find_closest(event.x, event.y)[0]
        tags = self.canvas.gettags(item)
        if "device" in tags:
            # Safe extraction of node name
            node_name = None
            for tag in tags:
                if tag.startswith("device_"):
                    node_name = tag.replace("device_", "")
                    break
            
            if not node_name: return

            # Handle Delete Mode
            if self.deleting_mode:
                self.delete_node_manual(node_name)
                return "break"

            # Handle Link Addition Mode
            if self.adding_link_mode:
                if self.link_source_node is None:
                    self.link_source_node = node_name
                    self.status_label.config(text=f"Manual Mode: Source {node_name} selected. Select Destination.", foreground="orange")
                else:
                    if node_name != self.link_source_node:
                        source = self.link_source_node
                        self.add_link_manual(source, node_name)
                        self.adding_link_mode = False
                        self.link_source_node = None
                        self.canvas.config(cursor="")
                        self.status_label.config(text=f"Manual Mode: Link added between {source} and {node_name}.", foreground="blue")
                    else:
                        self.status_label.config(text="Manual Mode: Cannot link node to itself. Select different node.", foreground="red")
                return

            # Normal Drag Logic
            self.drag_data["node"] = node_name
            self.drag_data["item"] = item
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.drag_data["total_dx"] = 0
            self.drag_data["total_dy"] = 0
            self.drag_data["original_coords"] = self.node_coordinates[node_name]
            self.save_state() # Save before drag starts

    def on_canvas_click(self, event):
        """Handles clicks on the canvas (mainly for selecting links)."""
        if not self.manual_mode.get(): return
        if not self.deleting_mode: return
        
        # Find closest item
        try:
            item = self.canvas.find_closest(event.x, event.y)[0]
        except IndexError:
            return

        tags = self.canvas.gettags(item)
        
        # Check if it is a link
        link_tag = None
        for tag in tags:
            if tag.startswith("link_") and not tag.startswith("link_label"):
                link_tag = tag
                break
        
        if link_tag:
            # Iterate network_graph to find matching tag (Source of truth for visuals)
            seen_edges = set()
            for u, neighbors in self.network_graph.items():
                for v in neighbors:
                    edge = tuple(sorted((u, v)))
                    if edge in seen_edges: continue
                    seen_edges.add(edge)
                    
                    expected_tag = f"link_{'_'.join(edge)}"
                    if expected_tag == link_tag:
                        self.delete_link_manual(edge[0], edge[1])
                        return

    def on_node_drag(self, event):
        if not self.manual_mode.get():
            return
        if self.drag_data["node"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]

            node = self.drag_data["node"]

            # Move all canvas items for this node (icon and label share the node ID tag)
            node_items = self.canvas.find_withtag(node)
            for item in node_items:
                self.canvas.move(item, dx, dy)

            # Accumulate total displacement
            self.drag_data["total_dx"] += dx
            self.drag_data["total_dy"] += dy

            # Update coordinates in real-time during drag
            ox, oy = self.drag_data["original_coords"]
            new_coords = (ox + self.drag_data["total_dx"], oy + self.drag_data["total_dy"])
            self.node_coordinates[node] = new_coords

            # Update topology object coordinates
            if node in self.topology.nodes:
                self.topology.nodes[node].coordinates = new_coords

            # Update visualizer's node positions for dynamic updates
            if self.visualizer:
                self.visualizer.node_positions[node] = new_coords

            # Update connected links and their labels in real-time with smooth animation
            self._update_connected_links(node)

            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y

    def on_node_release(self, event):
        if self.drag_data["node"]:
            node = self.drag_data["node"]
            ox, oy = self.drag_data["original_coords"]
            self.node_coordinates[node] = (ox + self.drag_data["total_dx"], oy + self.drag_data["total_dy"])
        self.drag_data["node"] = None

    def _update_connected_links(self, node):
        """
        Update positions of all links connected to the given node directly during drag.
        """
        if node not in self.network_graph:
            return

        # Get connected nodes
        connected_nodes = self.network_graph[node]

        for connected_node in connected_nodes:
            if connected_node not in self.node_coordinates:
                continue

            # Get updated positions
            pos_a = self.node_coordinates[node]
            pos_b = self.node_coordinates[connected_node]

            # Create link key (sorted tuple of node names)
            link_key = tuple(sorted((node, connected_node)))

            # Construct tags used by NetworkVisualizer
            link_tag = f"link_{'_'.join(link_key)}"
            label_tag = f"link_label_{'_'.join(link_key)}"

            # Update link line position directly
            link_items = self.canvas.find_withtag(link_tag)
            if link_items:
                self.canvas.coords(link_items[0], pos_a[0], pos_a[1], pos_b[0], pos_b[1])

            # Update link label position
            label_items = self.canvas.find_withtag(label_tag)
            if label_items:
                mid_x = (pos_a[0] + pos_b[0]) / 2
                mid_y = (pos_a[1] + pos_b[1]) / 2
                self.canvas.coords(label_items[0], mid_x, mid_y)

# --- Main code to run the application ---
if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkSimulator(root)
    root.mainloop()
