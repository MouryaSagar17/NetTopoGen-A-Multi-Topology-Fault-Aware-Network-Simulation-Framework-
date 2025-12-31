"""
Visualization Module

This module provides visualization capabilities for network simulations.
"""

import matplotlib.pyplot as plt # pyright: ignore[reportMissingModuleSource]
import matplotlib.animation as animation # pyright: ignore[reportMissingModuleSource]
import networkx as nx # pyright: ignore[reportMissingModuleSource]
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg # pyright: ignore[reportMissingModuleSource]
import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Tuple, Optional, Any, Set
import time
import threading
import queue
from collections import defaultdict
import json


class NetworkVisualizer:
    """
    Visualizes network topology and traffic.
    """

    def __init__(self, topology, canvas=None, tag_prefix="node"):
        """
        Initialize network visualizer.

        Args:
            topology: Network topology object
            canvas: Tkinter canvas for drawing (optional)
            tag_prefix: Prefix for device tags ("node" or "device")
        """
        self.topology = topology
        self.canvas = canvas
        self.tag_prefix = tag_prefix
        self.node_positions = {}
        self.node_colors = {}
        self.link_colors = {}
        self.traffic_paths = []
        self.animation_queue = queue.Queue()

        # Manual mode attributes
        self.manual_mode = False
        self.dragged_node = None
        self.link_items = {}  # link_key -> line_item_id
        self.link_label_items = {}  # link_key -> label_item_id
        self.last_mouse_pos = (0, 0) # Store last mouse position for dragging

        # Default colors
        self.node_colors = {
            "router": "lightblue",
            "switch": "lightgreen",
            "host": "lightcoral",
            "hub": "lightyellow",
            "server": "#E6E6FA",      # Lavender
            "firewall": "#FFA07A",    # LightSalmon
            "isp": "#D3D3D3",         # LightGray
            "ap": "#E0FFFF",          # LightCyan
            "load_balancer": "#FFB6C1" # LightPink
        }

        self.link_colors = {
            "active": "black",
            "broken": "red",
            "attacked": "purple"
        }

        # Calculate node positions if coordinates exist
        self._calculate_positions()

    def _calculate_positions(self):
        """Calculate node positions for visualization."""
        if not self.topology:
            return

        # Check if all nodes have coordinates
        all_have_coords = all(node.coordinates for node in self.topology.nodes.values())

        if all_have_coords:
            # Use existing coordinates
            for node_id, node in self.topology.nodes.items():
                self.node_positions[node_id] = node.coordinates
        else:
            # Generate circular layout for all nodes
            self._generate_circular_layout()

    def _generate_circular_layout(self):
        """Generate circular layout for nodes without coordinates."""
        nodes = list(self.topology.nodes.keys())
        n = len(nodes)
        if n == 0:
            return

        # Circular layout
        import math
        center_x, center_y = 400, 300
        radius = 150

        for i, node_id in enumerate(nodes):
            angle = 2 * math.pi * i / n
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.node_positions[node_id] = (x, y)

    def draw_topology(self, highlight_paths=None, failed_links=None, link_costs=None, optimal_path=None, optimal_color="green", node_queues=None, link_utilization=None, highlight_nodes=None):
        """
        Draw the network topology.

        Args:
            highlight_paths: List of paths to highlight
            failed_links: Set of failed link tuples
            link_costs: Dictionary of link costs
            optimal_path: The specific optimal path to highlight in green
            optimal_color: Color for the optimal path (default: green)
            node_queues: Dictionary of node queue levels (0.0 to 1.0)
            link_utilization: Dictionary of link utilization (0.0 to 1.0)
            highlight_nodes: Set of node IDs to highlight
        """
        if not self.canvas:
            return

        self.canvas.delete("all")
        self.link_items = {}
        self.link_label_items = {}

        # Draw links
        drawn_links = set()
        for node_a, node_b in self.topology.graph.edges():
            link_key = tuple(sorted((node_a, node_b)))
            if link_key in drawn_links:
                continue

            pos_a = self.node_positions.get(node_a)
            pos_b = self.node_positions.get(node_b)

            if not pos_a or not pos_b:
                continue

            # Get link properties
            link = self.topology.get_link(node_a, node_b)
            if link:
                delay = link.delay
                bandwidth = link.bandwidth / 1e6  # Convert to Mbps
                loss = link.loss * 100  # Convert to percentage
                is_broken = not link.status or (failed_links and link_key in failed_links)
                is_inferred = link.is_inferred
            else:
                delay, bandwidth, loss = 10.0, 1000.0, 0.0
                is_broken = failed_links and link_key in failed_links

            # Determine link color and style
            link_tag = f"link_{'_'.join(sorted(link_key))}"
            color = "gray80" # Default non-optimal (Thin gray)
            width = 1
            dash = None

            if is_broken:
                color = self.link_colors["broken"]
                dash = (5, 5)  # Dashed line
                width = 2
            else:
                # Congestion Visualization
                if link_utilization and link_key in link_utilization:
                    util = link_utilization[link_key]
                    if util > 0.8: color = "red"
                    elif util > 0.5: color = "orange"
                    elif util > 0.0: color = "green"

                # Check if link is in optimal path
                is_optimal = False
                if optimal_path:
                    for i in range(len(optimal_path) - 1):
                        if (optimal_path[i] == node_a and optimal_path[i+1] == node_b) or \
                           (optimal_path[i] == node_b and optimal_path[i+1] == node_a):
                            is_optimal = True
                            break

                is_highlighted = False
                if not is_optimal and highlight_paths:
                    for path in highlight_paths:
                        for i in range(len(path) - 1):
                            if (path[i] == node_a and path[i+1] == node_b) or \
                               (path[i] == node_b and path[i+1] == node_a):
                                is_highlighted = True
                                break

                if is_optimal:
                    # Glow effect (thick transparent-like line behind)
                    self.canvas.create_line(pos_a[0], pos_a[1], pos_b[0], pos_b[1],
                                          fill="#90EE90", width=8, tags=(link_tag, "glow"))
                    color = optimal_color
                    width = 4
                elif is_inferred:
                    dash = (4, 4)  # Dashed line for inferred access links
                    color = "gray60"
                    width = 1
                elif is_highlighted:
                    color = "red"
                    width = 1

            # Draw link line
            line_item = self.canvas.create_line(pos_a[0], pos_a[1], pos_b[0], pos_b[1],
                                              fill=color, width=width, dash=dash, tags=(link_tag,))
            self.link_items[link_key] = line_item

            # Draw link metrics at midpoint
            mid_x = (pos_a[0] + pos_b[0]) / 2
            mid_y = (pos_a[1] + pos_b[1]) / 2
            
            cost_str = ""
            if link_costs and link_key in link_costs:
                cost_str = f"\nCost: {link_costs[link_key]:.1f}"
            
            bw_str = f"{bandwidth:.0f}M" if bandwidth < 1000 else f"{bandwidth/1000:.1f}G"
            metrics_text = f"D:{delay:.0f}ms B:{bw_str} L:{loss:.1f}%{cost_str}"
            
            label_tag = f"link_label_{'_'.join(sorted(link_key))}"
            label_item = self.canvas.create_text(mid_x, mid_y, text=metrics_text,
                                               font=("Arial", 7), fill="blue", justify="center", tags=(label_tag,))
            self.link_label_items[link_key] = label_item

            drawn_links.add(link_key)

        # Draw nodes
        for node_id, pos in self.node_positions.items():
            node = self.topology.nodes.get(node_id)
            if not node:
                continue

            # Draw device icon based on type
            is_highlighted = highlight_nodes and node_id in highlight_nodes
            self._draw_device_icon(node, pos, highlight=is_highlighted)

            # Draw Queue Bar
            if node_queues and node_id in node_queues:
                q_level = node_queues[node_id]
                bar_x = pos[0] + 20
                bar_y = pos[1] - 15
                bar_h = 30
                bar_w = 6
                
                # Background
                self.canvas.create_rectangle(bar_x, bar_y, bar_x + bar_w, bar_y + bar_h, fill="white", outline="black")
                # Fill
                fill_h = bar_h * min(max(q_level, 0), 1)
                fill_color = "green" if q_level < 0.5 else "orange" if q_level < 0.8 else "red"
                self.canvas.create_rectangle(bar_x, bar_y + (bar_h - fill_h), bar_x + bar_w, bar_y + bar_h, fill=fill_color, outline="")

            # Node label near the icon
            device_tag = f"device_{node_id}"
            self.canvas.create_text(pos[0], pos[1] + 35, text=node_id,
                                  font=("Arial", 9, "bold"), tags=("device", device_tag, node_id))

    def _draw_device_icon(self, node, pos, highlight=False):
        """
        Draw a device icon based on node type.

        Args:
            node: Node object
            pos: (x, y) position tuple
            highlight: Whether to highlight the node
        """
        x, y = pos
        node_type = node.node_type
        device_tag = f"device_{node.node_id}"

        if highlight:
            # Draw glow effect
            glow_radius = 30
            self.canvas.create_oval(x-glow_radius, y-glow_radius, x+glow_radius, y+glow_radius,
                                  fill="yellow", outline="", stipple="gray50", tags=("device", device_tag, node.node_id, "glow"))

        if node_type == "router":
            # Router (blue, circular)
            self.canvas.create_oval(x-22, y-22, x+22, y+22,
                                  fill="#4da6ff", outline="black", width=2, tags=("device", device_tag, node.node_id))
            # Inner arrows symbol (simplified)
            self.canvas.create_oval(x-15, y-15, x+15, y+15,
                                  fill="lightblue", outline="black", width=1, tags=("device", device_tag, node.node_id))
            # Central dot
            self.canvas.create_oval(x-3, y-3, x+3, y+3,
                                  fill="black", tags=("device", device_tag, node.node_id))

        elif node_type == "switch":
            # Switch (green, rectangular)
            self.canvas.create_rectangle(x-25, y-15, x+25, y+15,
                                       fill="#90EE90", outline="black", width=2,
                                       tags=("device", device_tag, node.node_id))
            # Port dots
            for i in range(4):
                px = x - 18 + i * 12
                self.canvas.create_oval(px-2, y-8, px+2, y-4,
                                      fill="black", tags=("device", device_tag, node.node_id))
                self.canvas.create_oval(px-2, y+4, px+2, y+8,
                                      fill="black", tags=("device", device_tag, node.node_id))

        elif node_type == "host":
            # PC (gray)
            # Screen
            self.canvas.create_rectangle(x-15, y-18, x+15, y-4,
                                       fill="#e0e0e0", outline="black", width=2,
                                       tags=("device", device_tag, node.node_id))
            # Screen content (simple lines)
            self.canvas.create_line(x-10, y-14, x+10, y-14, fill="black", tags=("device", device_tag, node.node_id))
            self.canvas.create_line(x-10, y-10, x+10, y-10, fill="black", tags=("device", device_tag, node.node_id))
            # Base
            self.canvas.create_rectangle(x-10, y-4, x+10, y+6,
                                       fill="#a0a0a0", outline="black", width=1,
                                       tags=("device", device_tag, node.node_id))

        elif node_type == "hub":
            # Hub (orange)
            self.canvas.create_rectangle(x-22, y-12, x+22, y+12,
                                       fill="lightyellow", outline="black", width=2,
                                       tags=("device", device_tag, node.node_id))
            # Port indicators
            for i in range(4):
                angle = i * 90
                px = x + 14 * (1 if i % 2 == 0 else -1)
                py = y + 14 * (1 if i < 2 else -1)
                self.canvas.create_oval(px-2, py-2, px+2, py+2,
                                      fill="orange", tags=("device", device_tag, node.node_id))

        elif node_type == "server":
            # Server (Tower)
            self.canvas.create_rectangle(x-15, y-25, x+15, y+25,
                                       fill="#9370DB", outline="black", width=2,
                                       tags=("device", device_tag, node.node_id))
            # Rack lines
            for i in range(3):
                py = y - 15 + i * 15
                self.canvas.create_line(x-10, py, x+10, py, fill="black", tags=("device", device_tag, node.node_id))
            # LEDs
            self.canvas.create_oval(x-10, y-20, x-6, y-16, fill="green", tags=("device", device_tag, node.node_id))

        elif node_type == "firewall":
            # Firewall (Brick Wall)
            self.canvas.create_rectangle(x-20, y-15, x+20, y+15,
                                       fill="#CD5C5C", outline="black", width=2,
                                       tags=("device", device_tag, node.node_id))
            # Brick pattern
            self.canvas.create_line(x-20, y, x+20, y, fill="white", tags=("device", device_tag, node.node_id))
            self.canvas.create_line(x, y-15, x, y, fill="white", tags=("device", device_tag, node.node_id))
            self.canvas.create_line(x-10, y, x-10, y+15, fill="white", tags=("device", device_tag, node.node_id))
            self.canvas.create_line(x+10, y, x+10, y+15, fill="white", tags=("device", device_tag, node.node_id))

        elif node_type == "isp":
            # ISP (Cloud)
            self.canvas.create_oval(x-30, y-10, x+10, y+20, fill="#D3D3D3", outline="", tags=("device", device_tag, node.node_id))
            self.canvas.create_oval(x-10, y-20, x+30, y+10, fill="#D3D3D3", outline="", tags=("device", device_tag, node.node_id))
            self.canvas.create_oval(x-20, y-5, x+20, y+25, fill="#D3D3D3", outline="", tags=("device", device_tag, node.node_id))
            self.canvas.create_text(x, y, text="ISP", font=("Arial", 8, "bold"), tags=("device", device_tag, node.node_id))

        elif node_type == "ap":
            # Access Point
            self.canvas.create_rectangle(x-15, y-10, x+15, y+10,
                                       fill="#00CED1", outline="black", width=2,
                                       tags=("device", device_tag, node.node_id))
            # Antenna
            self.canvas.create_line(x, y-10, x, y-25, width=2, fill="black", tags=("device", device_tag, node.node_id))
            # Signal waves
            self.canvas.create_arc(x-10, y-30, x+10, y-10, start=45, extent=90, style="arc", outline="blue", tags=("device", device_tag, node.node_id))
            self.canvas.create_arc(x-20, y-40, x+20, y, start=45, extent=90, style="arc", outline="blue", tags=("device", device_tag, node.node_id))

        elif node_type == "load_balancer":
            # Load Balancer
            self.canvas.create_oval(x-20, y-20, x+20, y+20,
                                  fill="#FF69B4", outline="black", width=2,
                                  tags=("device", device_tag, node.node_id))
            # Arrows
            self.canvas.create_line(x-10, y, x+10, y-10, arrow=tk.LAST, tags=("device", device_tag, node.node_id))
            self.canvas.create_line(x-10, y, x+10, y+10, arrow=tk.LAST, tags=("device", device_tag, node.node_id))

        else:
            # Default rectangle for unknown types
            fill_color = self.node_colors.get(node_type, "gray")
            self.canvas.create_rectangle(x-20, y-15, x+20, y+15,
                                       fill=fill_color, outline="black", width=2,
                                       tags=("device", device_tag, node.node_id))

    def animate_packet(self, path, color="blue", speed=10.0):
        """
        Animate a packet moving along a path.

        Args:
            path: List of node IDs
            color: Packet color
            speed: Animation speed multiplier
        """
        if not self.canvas or len(path) < 2:
            return

        positions = []
        for node_id in path:
            pos = self.node_positions.get(node_id)
            if pos:
                positions.append(pos)

        if len(positions) < 2:
            return

        # Animation parameters
        steps_per_hop = 50
        delay = int(100 / speed)  # milliseconds - increased for visibility

        # Create packet at starting position
        start_x, start_y = positions[0]
        packet = self.canvas.create_oval(start_x-4, start_y-4, start_x+4, start_y+4, fill=color, outline="black")

        def animate_step(step=0):
            total_steps = (len(positions) - 1) * steps_per_hop
            if step >= total_steps:
                self.canvas.delete(packet)
                return

            hop_index = step // steps_per_hop
            start_pos = positions[hop_index]
            end_pos = positions[hop_index + 1]

            # Interpolate position
            t = (step % steps_per_hop) / steps_per_hop
            x = start_pos[0] + t * (end_pos[0] - start_pos[0])
            y = start_pos[1] + t * (end_pos[1] - start_pos[1])

            self.canvas.coords(packet, x-4, y-4, x+4, y+4)
            self.canvas.update_idletasks()
            self.canvas.update()

            self.canvas.after(delay, animate_step, step + 1)

        animate_step()

    def highlight_path(self, path, color="green"):
        """
        Highlight a path on the topology.

        Args:
            path: List of node IDs
            color: Highlight color
        """
        if not self.canvas or len(path) < 2:
            return

        for i in range(len(path) - 1):
            node_a, node_b = path[i], path[i+1]
            pos_a = self.node_positions.get(node_a)
            pos_b = self.node_positions.get(node_b)

            if pos_a and pos_b:
                self.canvas.create_line(pos_a[0], pos_a[1], pos_b[0], pos_b[1],
                                      fill=color, width=4, tags="highlight")

    def update_node_status(self, node_id, status):
        """
        Update the visual status of a node.

        Args:
            node_id: Node ID
            status: New status ("normal", "failed", "attacked")
        """
        if not self.canvas:
            return

        # Find node items
        node_items = self.canvas.find_withtag(node_id)
        if not node_items:
            return

        # Update color based on status
        if status == "failed":
            fill_color = "red"
        elif status == "attacked":
            fill_color = "purple"
        else:
            node = self.topology.nodes.get(node_id)
            fill_color = self.node_colors.get(node.node_type if node else "router", "gray")

        for item in node_items:
            self.canvas.itemconfig(item, fill=fill_color)

    def enable_manual_mode(self):
        """
        Enable manual mode for dragging devices.
        """
        if not self.canvas:
            return

        self.manual_mode = True
        # Bind mouse events for dragging
        self.canvas.bind("<Button-1>", self._on_mouse_press)
        self.canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_mouse_release)

    def disable_manual_mode(self):
        """
        Disable manual mode for dragging devices.
        """
        if not self.canvas:
            return

        self.manual_mode = False
        self.dragged_node = None
        # Unbind mouse events
        self.canvas.unbind("<Button-1>")
        self.canvas.unbind("<B1-Motion>")
        self.canvas.unbind("<ButtonRelease-1>")

    def _on_mouse_press(self, event):
        """
        Handle mouse press event to start dragging.

        Args:
            event: Tkinter event object
        """
        if not self.manual_mode:
            return

        # Find the node under the mouse cursor
        x, y = event.x, event.y
        overlapping_items = self.canvas.find_overlapping(x-5, y-5, x+5, y+5)

        for item in overlapping_items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("device_"):
                    node_id = tag.replace("device_", "")
                    if node_id in self.node_positions:
                        self.dragged_node = node_id
                        self.drag_start_pos = (x, y) # Keep this for initial node offset calculation
                        self.drag_start_node_pos = self.node_positions[node_id]
                        self.last_mouse_pos = (x, y) # Initialize last_mouse_pos
                        break
            if self.dragged_node:
                break

    def _on_mouse_drag(self, event):
        """
        Handle mouse drag event to move the device and its links.

        Args:
            event: Tkinter event object
        """
        if not self.manual_mode or not self.dragged_node:
            return

        x, y = event.x, event.y
        dx = x - self.last_mouse_pos[0]
        dy = y - self.last_mouse_pos[1]

        # Update node position in our internal tracking
        current_node_pos = self.node_positions[self.dragged_node]
        new_x = current_node_pos[0] + dx
        new_y = current_node_pos[1] + dy
        self.node_positions[self.dragged_node] = (new_x, new_y)

        # Move all canvas items associated with this node by the incremental change
        node_items = self.canvas.find_withtag(self.dragged_node)
        for item in node_items:
            self.canvas.move(item, dx, dy)

        # Update connected links
        self._update_connected_links(self.dragged_node)

        # Update last mouse position for the next drag event
        self.last_mouse_pos = (x, y)

        # Force canvas update for live link updates
        self.canvas.update_idletasks()

    def _on_mouse_release(self, event):
        """
        Handle mouse release event to stop dragging.

        Args:
            event: Tkinter event object
        """
        if not self.manual_mode:
            return

        self.dragged_node = None

    def update_node_position(self, node_id, new_pos):
        """
        Update the position of a node programmatically in manual mode.

        Args:
            node_id: Node ID to update
            new_pos: New (x, y) position tuple
        """
        if not self.manual_mode or not self.canvas:
            return

        old_pos = self.node_positions.get(node_id)
        if not old_pos:
            return

        # Update position in visualizer
        self.node_positions[node_id] = new_pos

        # Update topology coordinates
        if self.topology:
            self.topology.update_node_coordinates(node_id, new_pos)

        # Calculate movement delta
        dx = new_pos[0] - old_pos[0]
        dy = new_pos[1] - old_pos[1]

        # Move all canvas items associated with this node
        node_items = self.canvas.find_withtag(node_id)
        for item in node_items:
            self.canvas.move(item, dx, dy)

        # Update connected links
        self._update_connected_links(node_id)

    def _update_connected_links(self, node_id):
        """
        Update the positions of links connected to the given node.

        Args:
            node_id: Node ID whose links need updating
        """
        if not self.canvas:
            return

        # Find all links connected to this node
        connected_links = []
        for link_key in self.link_items.keys():
            if node_id in link_key:
                connected_links.append(link_key)

        # Update each connected link
        for link_key in connected_links:
            node_a, node_b = link_key
            pos_a = self.node_positions.get(node_a)
            pos_b = self.node_positions.get(node_b)

            if pos_a and pos_b:
                # Update link line
                line_item = self.link_items.get(link_key)
                if line_item:
                    self.canvas.coords(line_item, pos_a[0], pos_a[1], pos_b[0], pos_b[1])

    def export_topology_image(self, filename):
        """
        Export topology as image.

        Args:
            filename: Output filename
        """
        if not self.canvas:
            return

        # This would require additional libraries like PIL
        # For now, just save canvas content as postscript
        self.canvas.postscript(file=filename + ".ps")


class MetricsVisualizer:
    """
    Visualizes performance metrics and statistics.
    """

    def __init__(self, root=None):
        """
        Initialize metrics visualizer.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.figure = None
        self.canvas = None
        self.plots = {}

    def create_metrics_dashboard(self, parent):
        """
        Create metrics dashboard in parent widget.

        Args:
            parent: Parent tkinter widget
        """
        self.figure = plt.Figure(figsize=(8, 6))
        self.canvas = FigureCanvasTkAgg(self.figure, master=parent)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def plot_throughput_over_time(self, time_data, throughput_data):
        """
        Plot throughput over time.

        Args:
            time_data: Time points
            throughput_data: Throughput values
        """
        if not self.figure:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.plot(time_data, throughput_data, 'b-', linewidth=2)
        ax.set_title('Network Throughput Over Time')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Throughput (packets/s)')
        ax.grid(True)
        self.canvas.draw()

    def plot_delay_distribution(self, delays):
        """
        Plot delay distribution histogram.

        Args:
            delays: List of delay values
        """
        if not self.figure:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.hist(delays, bins=50, alpha=0.7, color='green', edgecolor='black')
        ax.set_title('Packet Delay Distribution')
        ax.set_xlabel('Delay (s)')
        ax.set_ylabel('Frequency')
        ax.grid(True)
        self.canvas.draw()

    def plot_link_utilization(self, link_data):
        """
        Plot link utilization bar chart.

        Args:
            link_data: Dictionary of link utilization values
        """
        if not self.figure:
            return

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        links = list(link_data.keys())
        utilizations = list(link_data.values())

        bars = ax.bar(range(len(links)), utilizations, color='orange', alpha=0.7)
        ax.set_title('Link Utilization')
        ax.set_xlabel('Links')
        ax.set_ylabel('Utilization (%)')
        ax.set_xticks(range(len(links)))
        ax.set_xticklabels([f'{a}-{b}' for a, b in links], rotation=45)
        ax.grid(True, axis='y')

        # Add value labels on bars
        for bar, util in zip(bars, utilizations):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                   f'{util:.1%}', ha='center', va='bottom')

        self.figure.tight_layout()
        self.canvas.draw()

    def plot_comparison_chart(self, algorithms, metrics):
        """
        Plot algorithm comparison chart.

        Args:
            algorithms: List of algorithm names
            metrics: Dictionary of metric values per algorithm
        """
        if not self.figure:
            return

        self.figure.clear()

        # Create subplots for different metrics
        metric_names = list(metrics.keys())
        n_metrics = len(metric_names)

        for i, metric_name in enumerate(metric_names):
            ax = self.figure.add_subplot(1, n_metrics, i+1)

            values = [metrics[metric_name].get(alg, 0) for alg in algorithms]
            bars = ax.bar(range(len(algorithms)), values, color='skyblue', alpha=0.7)

            ax.set_title(f'{metric_name}')
            ax.set_xticks(range(len(algorithms)))
            ax.set_xticklabels(algorithms, rotation=45)
            ax.grid(True, axis='y')

            # Add value labels
            for bar, value in zip(bars, values):
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(values)*0.01,
                       f'{value:.2f}', ha='center', va='bottom')

        self.figure.tight_layout()
        self.canvas.draw()

    def export_plot(self, filename):
        """
        Export current plot to file.

        Args:
            filename: Output filename
        """
        if self.figure:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')


class SimulationDashboard:
    """
    Comprehensive simulation dashboard with real-time updates.
    """

    def __init__(self, root):
        """
        Initialize simulation dashboard.

        Args:
            root: Tkinter root window
        """
        self.root = root
        self.root.title("Network Simulation Dashboard")
        self.root.geometry("1400x900")

        # Create main frames
        self.topology_frame = ttk.Frame(root, padding="5")
        self.topology_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.metrics_frame = ttk.Frame(root, padding="5")
        self.metrics_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Topology canvas
        self.canvas = tk.Canvas(self.topology_frame, width=800, height=600, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Metrics display
        self.metrics_text = tk.Text(self.metrics_frame, height=20, width=50)
        self.metrics_text.pack(fill=tk.BOTH, expand=True)

        # Control buttons
        self.control_frame = ttk.Frame(root, padding="5")
        self.control_frame.pack(fill=tk.X)

        ttk.Button(self.control_frame, text="Start Simulation",
                  command=self.start_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="Stop Simulation",
                  command=self.stop_simulation).pack(side=tk.LEFT, padx=5)
        ttk.Button(self.control_frame, text="Export Results",
                  command=self.export_results).pack(side=tk.LEFT, padx=5)

        # Status bar
        self.status_var = tk.StringVar(value="Ready")
        self.status_bar = ttk.Label(root, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)

        # Initialize components
        self.visualizer = None
        self.metrics_visualizer = MetricsVisualizer()
        self.metrics_visualizer.create_metrics_dashboard(self.metrics_frame)

        self.simulation_running = False
        self.simulation_thread = None

    def set_topology(self, topology):
        """
        Set the network topology for visualization.

        Args:
            topology: Network topology object
        """
        self.visualizer = NetworkVisualizer(topology, self.canvas)
        self.visualizer.draw_topology()

    def update_metrics(self, metrics_data):
        """
        Update metrics display.

        Args:
            metrics_data: Dictionary of current metrics
        """
        self.metrics_text.delete(1.0, tk.END)

        text = "Current Metrics:\n\n"
        for key, value in metrics_data.items():
            if isinstance(value, float):
                text += f"{key}: {value:.3f}\n"
            else:
                text += f"{key}: {value}\n"

        self.metrics_text.insert(tk.END, text)

    def start_simulation(self):
        """Start the simulation."""
        if not self.simulation_running:
            self.simulation_running = True
            self.status_var.set("Simulation Running...")
            self.simulation_thread = threading.Thread(target=self._run_simulation, daemon=True)
            self.simulation_thread.start()

    def stop_simulation(self):
        """Stop the simulation."""
        self.simulation_running = False
        self.status_var.set("Simulation Stopped")

    def _run_simulation(self):
        """Run simulation loop (placeholder)."""
        # This would be implemented with actual simulation logic
        while self.simulation_running:
            time.sleep(1)
            # Update metrics periodically
            self.update_metrics({
                "throughput": 95.5,
                "packet_loss": 0.02,
                "average_delay": 0.15,
                "simulation_time": time.time()
            })

    def export_results(self):
        """Export simulation results."""
        # Placeholder for export functionality
        self.status_var.set("Results exported")

    def animate_traffic(self, path, packet_type="data"):
        """
        Animate traffic on the topology.

        Args:
            path: Traffic path
            packet_type: Type of packet ("data", "control", etc.)
        """
        if self.visualizer:
            color = "blue" if packet_type == "data" else "red"
            self.visualizer.animate_packet(path, color)
