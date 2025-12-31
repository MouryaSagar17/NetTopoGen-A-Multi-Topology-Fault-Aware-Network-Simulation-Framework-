"""
Topology Generation Module

This module provides various algorithms for generating network topologies.
"""

import random
import math
import re
from typing import List, Tuple, Dict, Optional, Any
from src.core import Topology, Node, Link


class TopologyGenerator:
    """
    Generates various network topologies.
    """

    def __init__(self, random_seed: Optional[int] = None):
        """
        Initialize the topology generator.

        Args:
            random_seed: Random seed for reproducible generation
        """
        if random_seed is not None:
            random.seed(random_seed)

    def _assign_ip_addresses(self, topology: Topology):
        """
        Assign IP addresses and gateways to nodes based on connectivity.
        """
        subnet_idx = 1
        
        # Find routers
        routers = [n for n in topology.nodes.values() if n.node_type == "router"]
        if not routers:
            # If no routers, assign a flat subnet to everyone
            subnet = f"192.168.{subnet_idx}"
            host_idx = 1
            for node in topology.nodes.values():
                if node.node_type == "host":
                    node.interfaces = {"eth0": {"ip": f"{subnet}.{host_idx}", "mask": "255.255.255.0", "gateway": ""}}
                    host_idx += 1
            return

        # Assign subnets to router interfaces
        visited_switches = set()
        
        for router in routers:
            neighbors = topology.get_neighbors(router.node_id)
            for neighbor in neighbors:
                if neighbor.node_type in ["switch", "hub"] and neighbor.node_id not in visited_switches:
                    # New subnet for this switch segment
                    subnet = f"192.168.{subnet_idx}"
                    subnet_idx += 1
                    
                    # Router Interface
                    router_ip = f"{subnet}.1"
                    if "eth" not in router.interfaces: router.interfaces = {}
                    intf_name = f"eth{len(router.interfaces)}"
                    router.interfaces[intf_name] = {"ip": router_ip, "mask": "255.255.255.0"}
                    
                    # BFS/DFS to find all downstream hosts from this switch
                    queue = [neighbor]
                    visited_switches.add(neighbor.node_id)
                    host_idx = 2
                    
                    segment_visited = {neighbor.node_id}
                    
                    while queue:
                        curr = queue.pop(0)
                        curr_neighbors = topology.get_neighbors(curr.node_id)
                        
                        for n in curr_neighbors:
                            if n.node_id in segment_visited: continue
                            if n.node_type == "router": continue # Don't cross routers
                            
                            segment_visited.add(n.node_id)
                            
                            if n.node_type == "host":
                                n.interfaces = {"eth0": {"ip": f"{subnet}.{host_idx}", "mask": "255.255.255.0", "gateway": router_ip}}
                                host_idx += 1
                            elif n.node_type in ["switch", "hub"]:
                                visited_switches.add(n.node_id)
                                queue.append(n)

    def validate_topology(self, topology: Topology) -> List[str]:
        """
        Validate the generated topology.
        Returns a list of warnings/errors.
        """
        warnings = []
        if not topology.nodes:
            return ["Empty topology"]

        # Check connectivity (Graph should be connected)
        if not topology.is_connected():
            warnings.append("Topology is not fully connected (isolated islands exist).")

        # Check isolated nodes
        for node_id in topology.nodes:
            if not topology.get_neighbors(node_id):
                warnings.append(f"Node {node_id} is isolated.")

        # Check Switches without uplinks (to routers)
        routers = [n.node_id for n in topology.nodes.values() if n.node_type == "router"]
        if routers:
            for node in topology.nodes.values():
                if node.node_type == "switch":
                    has_path = False
                    for r in routers:
                        if topology.get_shortest_path(node.node_id, r):
                            has_path = True
                            break
                    if not has_path:
                        warnings.append(f"Switch {node.node_id} has no path to a router.")

        return warnings

    def generate_hierarchical(self, num_pcs: int, num_routers: int,
                            num_switches: int, num_hubs: int,
                            num_servers: int, num_firewalls: int, num_isps: int,
                            canvas_width: int = 800, canvas_height: int = 600) -> Topology:
        """
        Generate a hierarchical topology with redundant router backbone.

        Args:
            num_pcs: Number of end devices (PCs)
            num_routers: Number of routers
            num_switches: Number of switches
            num_hubs: Number of hubs
            num_servers: Number of servers
            num_firewalls: Number of firewalls
            num_isps: Number of ISPs
            canvas_width: Canvas width for layout
            canvas_height: Canvas height for layout

        Returns:
            Generated topology
        """
        topology = Topology()
        
        # Layout parameters
        margin_x = 50
        margin_y = 50
        usable_width = canvas_width - 2 * margin_x
        
        # 1. ISP (External)
        isps = []
        if num_isps > 0:
            for i in range(num_isps):
                name = f"ISP{i+1}" if num_isps > 1 else "ISP"
                x = int(canvas_width * (i + 1) / (num_isps + 1))
                y = int(margin_y)
                node = Node(name, "isp", (x, y))
                topology.add_node(node)
                isps.append(name)

        # 2. Firewalls
        fws = []
        if num_firewalls > 0:
            for i in range(num_firewalls):
                name = f"FW{i+1}" if num_firewalls > 1 else "FW1"
                x = int(canvas_width * (i + 1) / (num_firewalls + 1))
                y = int(margin_y + 60)
                node = Node(name, "firewall", (x, y))
                topology.add_node(node)
                fws.append(name)
                
                if isps:
                    topology.add_link(Link(name, isps[i % len(isps)], delay=5.0, bandwidth=1e9))

        # 3. Core Layer: Routers
        routers = []
        if num_routers > 0:
            y_pos = margin_y + canvas_height * 0.2
            spacing = usable_width / (num_routers + 1)
            for i in range(num_routers):
                name = f"R{i}"
                x_pos = margin_x + spacing * (i + 1)
                router = Node(name, "router", (int(x_pos), int(y_pos)))
                topology.add_node(router)
                routers.append(name)

                # Connect Edge Routers to FW or ISP
                uplink_targets = fws if fws else isps
                if uplink_targets:
                    if i == 0:
                        topology.add_link(Link(name, uplink_targets[0], delay=2.0, bandwidth=1e9))
                    elif i == num_routers - 1 and len(uplink_targets) > 1:
                        topology.add_link(Link(name, uplink_targets[-1], delay=2.0, bandwidth=1e9))
                
                # Connect to previous router (Linear backbone)
                if i > 0:
                    topology.add_link(Link(name, routers[i-1]))
            
            # Close ring if > 2 routers
            if num_routers > 2:
                topology.add_link(Link(routers[0], routers[-1]))
        
        # 4. Distribution Layer: Switches
        switches = []
        if num_switches > 0:
            y_pos = margin_y + canvas_height * 0.5
            spacing = usable_width / (num_switches + 1)
            for i in range(num_switches):
                name = f"Switch{i}"
                x_pos = margin_x + spacing * (i + 1)
                switch = Node(name, "switch", (int(x_pos), int(y_pos)))
                topology.add_node(switch)
                switches.append(name)
                
                # Uplink to Router (Round Robin)
                if routers:
                    uplink_router = routers[i % len(routers)]
                    topology.add_link(Link(name, uplink_router))

        # 5. Servers
        if num_servers > 0:
            targets = switches if switches else routers
            if targets:
                for i in range(num_servers):
                    name = f"Server{i+1}"
                    x = int(canvas_width - margin_x - 50)
                    y = int(margin_y + canvas_height * 0.5 + (i * 40))
                    node = Node(name, "server", (x, y))
                    topology.add_node(node)
                    topology.add_link(Link(name, targets[i % len(targets)]))
        
        # 6. End Devices: PCs
        # Access devices are Switches
        access_devices = switches
        # If no access devices, use routers
        if not access_devices:
            access_devices = routers
            
        if num_pcs > 0:
            y_pos = margin_y + canvas_height * 0.85
            spacing = usable_width / (num_pcs + 1)
            for i in range(num_pcs):
                name = f"PC{i}"
                x_pos = margin_x + spacing * (i + 1)
                node = Node(name, "host", (int(x_pos), int(y_pos)))
                topology.add_node(node)
                
                # Connect to Access Device (Round Robin)
                if access_devices:
                    uplink = access_devices[i % len(access_devices)]
                    topology.add_link(Link(name, uplink))
        
        self._assign_ip_addresses(topology)
        return topology

    def generate_star(self, num_pcs: int, num_routers: int,
                     num_switches: int, num_hubs: int,
                     num_servers: int, num_firewalls: int, num_isps: int,
                     canvas_width: int = 800, canvas_height: int = 600) -> Topology:
        """
        Generate a star topology with redundant center if possible.

        Args:
            num_pcs: Number of end devices (PCs)
            num_routers: Number of routers
            num_switches: Number of switches
            num_hubs: Number of hubs
            num_servers: Number of servers
            num_firewalls: Number of firewalls
            num_isps: Number of ISPs
            canvas_width: Canvas width for layout
            canvas_height: Canvas height for layout

        Returns:
            Generated topology
        """
        topology = Topology()
        center_x = canvas_width // 2
        center_y = canvas_height // 2

        # 1. ISP & Firewall (External)
        margin_y = 50
        isps = []
        if num_isps > 0:
            for i in range(num_isps):
                name = f"ISP{i+1}" if num_isps > 1 else "ISP"
                x = int(canvas_width * (i + 1) / (num_isps + 1))
                y = int(margin_y)
                topology.add_node(Node(name, "isp", (x, y)))
                isps.append(name)

        fws = []
        if num_firewalls > 0:
            for i in range(num_firewalls):
                name = f"FW{i+1}" if num_firewalls > 1 else "FW1"
                x = int(canvas_width * (i + 1) / (num_firewalls + 1))
                y = int(margin_y + 60)
                topology.add_node(Node(name, "firewall", (x, y)))
                fws.append(name)
                if isps: topology.add_link(Link(name, isps[i % len(isps)], delay=5.0, bandwidth=1e9))

        # Determine center nodes
        center_nodes_ids = []
        other_devices = []

        # Add PCs to other_devices
        for i in range(num_pcs):
            other_devices.append(f"PC{i}")
        for i in range(num_servers):
            other_devices.append(f"Server{i}")

        # Try to find two central nodes
        if num_routers >= 1:
            center_nodes_ids = ["R0"]
            if num_routers >= 2: center_nodes_ids.append("R1")
            
            for i in range(len(center_nodes_ids), num_routers):
                other_devices.append(f"R{i}")
            for i in range(num_switches):
                other_devices.append(f"Switch{i}")
        elif num_switches >= 1:
            center_nodes_ids = ["Switch0"]
            if num_switches >= 2: center_nodes_ids.append("Switch1")
            
            for i in range(2, num_switches):
                other_devices.append(f"Switch{i}")
        else:
            # Fallback if only PCs
            center_nodes_ids = ["Switch0"]

        # Place center nodes
        if len(center_nodes_ids) == 1:
            name = center_nodes_ids[0]
            ntype = "router" if "R" in name else "switch" if "Switch" in name else "hub"
            center_node = Node(name, ntype,
                             (center_x, center_y))
            topology.add_node(center_node)
            
            # Connect FW to Center
            if fws:
                topology.add_link(Link(name, fws[0]))
        else:
            name1 = center_nodes_ids[0]
            ntype1 = "router" if "R" in name1 else "switch" if "Switch" in name1 else "hub"
            center_node1 = Node(name1, ntype1,
                              (center_x - 50, center_y))
            
            name2 = center_nodes_ids[1]
            ntype2 = "router" if "R" in name2 else "switch" if "Switch" in name2 else "hub"
            center_node2 = Node(name2, ntype2,
                              (center_x + 50, center_y))
            
            topology.add_node(center_node1)
            topology.add_node(center_node2)

            # Link centers (Redundancy)
            link = Link(center_nodes_ids[0], center_nodes_ids[1])
            topology.add_link(link)
            
            # Connect FW to Center(s)
            if fws:
                topology.add_link(Link(name1, fws[0]))
                if len(fws) > 1: topology.add_link(Link(name2, fws[1]))

        # Place spoke devices
        n_spokes = len(other_devices)
        if n_spokes > 0:
            radius = min(250, center_y - 50)
            angle_step = (2 * math.pi) / n_spokes

            for i, name in enumerate(other_devices):
                angle = angle_step * i
                x = int(center_x + radius * math.cos(angle))
                y = int(center_y + radius * math.sin(angle))

                # Determine node type
                if name.startswith("PC"):
                    node_type = "host"
                elif name.startswith("R"):
                    node_type = "router"
                elif name.startswith("Switch"):
                    node_type = "switch"
                elif name.startswith("Server"):
                    node_type = "server"
                else:
                    node_type = "hub"

                node = Node(name, node_type, (x, y))
                topology.add_node(node)

                # Connect to center(s) - Load Balance
                center = center_nodes_ids[i % len(center_nodes_ids)]
                link = Link(name, center)
                topology.add_link(link)

        self._assign_ip_addresses(topology)
        return topology

    def generate_ring(self, num_pcs: int, num_routers: int,
                     num_switches: int, num_hubs: int,
                     num_servers: int, num_firewalls: int, num_isps: int,
                     canvas_width: int = 800, canvas_height: int = 600) -> Topology:
        """
        Generate a ring topology.

        Args:
            num_pcs: Number of end devices (PCs)
            num_routers: Number of routers
            num_switches: Number of switches
            num_hubs: Number of hubs
            num_servers: Number of servers
            num_firewalls: Number of firewalls
            num_isps: Number of ISPs
            canvas_width: Canvas width for layout
            canvas_height: Canvas height for layout

        Returns:
            Generated topology
        """
        topology = Topology()
        center_x = canvas_width // 2
        center_y = canvas_height // 2

        # 1. ISP & Firewall (External)
        margin_y = 50
        isps = []
        if num_isps > 0:
            for i in range(num_isps):
                name = f"ISP{i+1}" if num_isps > 1 else "ISP"
                x = int(canvas_width * (i + 1) / (num_isps + 1))
                y = int(margin_y)
                topology.add_node(Node(name, "isp", (x, y)))
                isps.append(name)

        fws = []
        if num_firewalls > 0:
            for i in range(num_firewalls):
                name = f"FW{i+1}" if num_firewalls > 1 else "FW1"
                x = int(canvas_width * (i + 1) / (num_firewalls + 1))
                y = int(margin_y + 60)
                topology.add_node(Node(name, "firewall", (x, y)))
                fws.append(name)
                if isps: topology.add_link(Link(name, isps[i % len(isps)], delay=5.0, bandwidth=1e9))

        # Create ring devices
        ring_devices = []
        for i in range(num_routers):
            ring_devices.append(f"R{i}")
        for i in range(num_switches):
            ring_devices.append(f"Switch{i}")

        if not ring_devices:
            raise ValueError("Ring topology requires at least 1 Router or Switch.")

        n_ring = len(ring_devices)
        radius = 150
        angle_step = (2 * math.pi) / n_ring

        # Place ring devices
        for i, name in enumerate(ring_devices):
            angle = angle_step * i
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))

            node_type = "router" if name.startswith("R") else "switch"
            node = Node(name, node_type, (x, y))
            topology.add_node(node)

            # Connect to previous
            if i > 0:
                link = Link(name, ring_devices[i-1])
                topology.add_link(link)

        # Connect last to first
        if n_ring > 1:
            link = Link(ring_devices[n_ring-1], ring_devices[0])
            topology.add_link(link)
            
        # Connect FW to Ring (e.g., R0)
        if fws and ring_devices:
            topology.add_link(Link(ring_devices[0], fws[0]))

        # Place other devices
        other_devices = []
        for i in range(num_pcs):
            other_devices.append(f"PC{i}")
        for i in range(num_servers):
            other_devices.append(f"Server{i}")

        if not other_devices:
            return topology

        n_other = len(other_devices)
        radius_outer = 250
        angle_step_outer = (2 * math.pi) / n_other

        for i, name in enumerate(other_devices):
            angle = angle_step_outer * i
            x = int(center_x + radius_outer * math.cos(angle))
            y = int(center_y + radius_outer * math.sin(angle))

            node_type = "hub" if name.startswith("Hub") else "server" if name.startswith("Server") else "host"
            node = Node(name, node_type, (x, y))
            topology.add_node(node)

            # Connect to nearest ring device
            nearest_ring = self._find_nearest_node(topology, name, ring_devices)
            if nearest_ring:
                link = Link(name, nearest_ring)
                topology.add_link(link)

        self._assign_ip_addresses(topology)
        return topology

    def generate_mesh(self, num_pcs: int, num_routers: int,
                     num_switches: int, num_hubs: int,
                     num_servers: int, num_firewalls: int, num_isps: int,
                     canvas_width: int = 800, canvas_height: int = 600) -> Topology:
        """
        Generate a full mesh topology.

        Args:
            num_pcs: Number of end devices (PCs)
            num_routers: Number of routers
            num_switches: Number of switches
            num_hubs: Number of hubs
            num_servers: Number of servers
            num_firewalls: Number of firewalls
            num_isps: Number of ISPs
            canvas_width: Canvas width for layout
            canvas_height: Canvas height for layout

        Returns:
            Generated topology
        """
        topology = Topology()
        center_x = canvas_width // 2
        center_y = canvas_height // 2

        # 1. ISP & Firewall (External)
        margin_y = 50
        isps = []
        if num_isps > 0:
            for i in range(num_isps):
                name = f"ISP{i+1}" if num_isps > 1 else "ISP"
                x = int(canvas_width * (i + 1) / (num_isps + 1))
                y = int(margin_y)
                topology.add_node(Node(name, "isp", (x, y)))
                isps.append(name)

        fws = []
        if num_firewalls > 0:
            for i in range(num_firewalls):
                name = f"FW{i+1}" if num_firewalls > 1 else "FW1"
                x = int(canvas_width * (i + 1) / (num_firewalls + 1))
                y = int(margin_y + 60)
                topology.add_node(Node(name, "firewall", (x, y)))
                fws.append(name)
                if isps: topology.add_link(Link(name, isps[i % len(isps)], delay=5.0, bandwidth=1e9))

        if num_routers < 2:
            raise ValueError("Mesh topology requires at least 2 Routers.")

        routers = []
        n_ring = num_routers
        radius = 150
        angle_step = (2 * math.pi) / n_ring

        # Place routers in a circle and connect all pairs
        for i in range(num_routers):
            name = f"R{i}"
            angle = angle_step * i
            x = int(center_x + radius * math.cos(angle))
            y = int(center_y + radius * math.sin(angle))

            router = Node(name, "router", (x, y))
            topology.add_node(router)
            routers.append(name)

            # Connect to all previous routers
            for j in range(i):
                link = Link(name, routers[j])
                topology.add_link(link)
        
        # Connect FW to Mesh (e.g., R0)
        if fws and routers:
            topology.add_link(Link(routers[0], fws[0]))

        # Place switches and hubs
        lan_devices = []
        for i in range(num_switches):
            lan_devices.append(f"Switch{i}")

        if not lan_devices and num_pcs > 0:
            lan_devices = routers  # Connect PCs directly to routers

        n_lan = len(lan_devices)
        if n_lan > 0:
            radius_lan = 250
            angle_step_lan = (2 * math.pi) / n_lan

            for i, name in enumerate(lan_devices):
                if name in [r.node_id for r in topology.get_all_nodes()]:
                    continue  # Already a router

                angle = angle_step_lan * i
                x = int(center_x + radius_lan * math.cos(angle))
                y = int(center_y + radius_lan * math.sin(angle))

                node_type = "switch" if name.startswith("Switch") else "hub"
                node = Node(name, node_type, (x, y))
                topology.add_node(node)

                # Connect to a router
                router = routers[i % num_routers]
                link = Link(name, router)
                topology.add_link(link)

        # Place PCs
        if num_pcs > 0 and n_lan > 0:
            radius_pc = 350
            angle_step_pc = (2 * math.pi) / num_pcs

            for i in range(num_pcs):
                name = f"PC{i}"
                angle = angle_step_pc * i
                x = int(center_x + radius_pc * math.cos(angle))
                y = int(center_y + radius_pc * math.sin(angle))

                pc = Node(name, "host", (x, y))
                topology.add_node(pc)

                # Connect to a LAN device
                lan_device = lan_devices[i % n_lan]
                link = Link(name, lan_device)
                topology.add_link(link)
        
        # Place Servers (connected to routers for mesh)
        if num_servers > 0:
            for i in range(num_servers):
                name = f"Server{i}"
                x = int(center_x + 300 * math.cos(i)) # Random-ish placement
                y = int(center_y + 300 * math.sin(i))
                node = Node(name, "server", (x, y))
                topology.add_node(node)
                topology.add_link(Link(name, routers[i % len(routers)]))

        self._assign_ip_addresses(topology)
        return topology

    def generate_tree(self, num_pcs: int, num_routers: int,
                     num_switches: int, num_hubs: int,
                     num_servers: int, num_firewalls: int, num_isps: int,
                     canvas_width: int = 800, canvas_height: int = 600) -> Topology:
        """
        Generate a tree topology.

        Args:
            num_pcs: Number of end devices (PCs)
            num_routers: Number of routers
            num_switches: Number of switches
            num_hubs: Number of hubs
            num_servers: Number of servers
            num_firewalls: Number of firewalls
            num_isps: Number of ISPs
            canvas_width: Canvas width for layout
            canvas_height: Canvas height for layout

        Returns:
            Generated topology
        """
        topology = Topology()
        center_x = canvas_width // 2

        if num_routers < 1:
            raise ValueError("Tree topology requires at least 1 Router.")

        # 1. ISP & Firewall (External)
        margin_y = 30
        isps = []
        if num_isps > 0:
            for i in range(num_isps):
                name = f"ISP{i+1}" if num_isps > 1 else "ISP"
                x = int(canvas_width * (i + 1) / (num_isps + 1))
                y = int(margin_y)
                topology.add_node(Node(name, "isp", (x, y)))
                isps.append(name)

        fws = []
        if num_firewalls > 0:
            for i in range(num_firewalls):
                name = f"FW{i+1}" if num_firewalls > 1 else "FW1"
                x = int(canvas_width * (i + 1) / (num_firewalls + 1))
                y = int(margin_y + 60)
                topology.add_node(Node(name, "firewall", (x, y)))
                fws.append(name)
                if isps: topology.add_link(Link(name, isps[i % len(isps)], delay=5.0, bandwidth=1e9))

        # Root router
        root_router = Node("R0", "router", (center_x, 150))
        topology.add_node(root_router)
        routers = ["R0"]
        router_levels = [0]
        
        if fws: topology.add_link(Link("R0", fws[0]))

        # Add more routers in levels
        y_offset = 150
        for i in range(1, num_routers):
            name = f"R{i}"
            level = int(math.log2(i + 1))
            y = 150 + level * 100

            # Calculate horizontal position
            level_start = 2 ** level - 1
            level_count = min(2 ** level, num_routers - level_start)
            index_in_level = i - level_start
            spacing = 500 / (2 ** level) if level > 0 else 0
            x = center_x + (index_in_level - (level_count - 1) / 2) * spacing

            router = Node(name, "router", (x, y))
            topology.add_node(router)
            routers.append(name)
            router_levels.append(level)

            # Connect to parent
            parent = routers[(i - 1) // 2]
            link = Link(name, parent)
            topology.add_link(link)

        # Add switches and hubs as branches
        leaf_routers = [r for i, r in enumerate(routers) if (i * 2 + 1) >= num_routers and (i * 2 + 2) >= num_routers]
        if not leaf_routers:
            leaf_routers = routers

        lan_devices = []
        switch_index = 0
        hub_index = 0

        # Distribute switches
        switches_per_leaf = num_switches // len(leaf_routers) if leaf_routers else 0
        extra_switches = num_switches % len(leaf_routers) if leaf_routers else 0

        for i, leaf in enumerate(leaf_routers):
            num_switches_here = switches_per_leaf + (1 if i < extra_switches else 0)
            leaf_coords = topology.get_node_coordinates(leaf)
            if not leaf_coords:
                continue

            for j in range(num_switches_here):
                name = f"Switch{switch_index}"
                x = leaf_coords[0] + (j - (num_switches_here - 1) / 2) * 120
                y = leaf_coords[1] + 100

                switch = Node(name, "switch", (x, y))
                topology.add_node(switch)
                lan_devices.append(name)

                link = Link(name, leaf)
                topology.add_link(link)
                switch_index += 1

        # Add PCs at the bottom
        pc_y = 500
        for i in range(num_pcs):
            name = f"PC{i}"
            pc_spacing = (canvas_width - 100) / max(1, num_pcs - 1) if num_pcs > 1 else 0
            x = 50 + i * pc_spacing

            pc = Node(name, "host", (x, pc_y))
            topology.add_node(pc)

            # Connect to nearest LAN device or leaf router
            if lan_devices:
                nearest = self._find_nearest_node(topology, name, lan_devices)
            else:
                nearest = self._find_nearest_node(topology, name, leaf_routers)

            if nearest:
                link = Link(name, nearest)
                topology.add_link(link)
        
        # Place Servers (connected to root or leaf routers)
        if num_servers > 0:
            for i in range(num_servers):
                name = f"Server{i}"
                x = 50 + i * 60
                y = 50 # Top
                node = Node(name, "server", (x, y))
                topology.add_node(node)
                topology.add_link(Link(name, routers[0]))

        self._assign_ip_addresses(topology)
        return topology

    def generate_random(self, num_nodes: int, num_links: int,
                       canvas_width: int = 800, canvas_height: int = 600) -> Topology:
        """
        Generate a random topology.

        Args:
            num_nodes: Number of nodes
            num_links: Number of links
            canvas_width: Canvas width for layout
            canvas_height: Canvas height for layout

        Returns:
            Generated topology
        """
        topology = Topology()

        # Create nodes
        for i in range(num_nodes):
            node_type = random.choice(["router", "switch", "host"])
            node_type = random.choice(["router", "switch", "host", "server", "ap"])
            name = f"{node_type.capitalize()}{i}"
            x = random.randint(50, canvas_width - 50)
            y = random.randint(50, canvas_height - 50)

            node = Node(name, node_type, (x, y))
            topology.add_node(node)

        # Create random links
        nodes = [n.node_id for n in topology.get_all_nodes()]
        links_created = 0
        max_attempts = num_links * 3

        for _ in range(max_attempts):
            if links_created >= num_links:
                break

            node_a, node_b = random.sample(nodes, 2)
            link_key = tuple(sorted((node_a, node_b)))

            # Check if link already exists
            if not topology.get_link(node_a, node_b):
                link = Link(node_a, node_b)
                topology.add_link(link)
                links_created += 1

        return topology

    def generate_from_intent(self, intent_description: str,
                           canvas_width: int = 800, canvas_height: int = 600) -> Topology:
        """
        Generate a network topology based on natural language intent description.

        Args:
            intent_description: Natural language description of desired network topology
            canvas_width: Canvas width for layout
            canvas_height: Canvas height for layout

        Returns:
            Generated topology based on intent
        """
        # Parse the intent description to extract network requirements
        parsed_intent = self._parse_intent_description(intent_description)

        # Determine topology type based on intent
        topology_type = self._determine_topology_type(parsed_intent, intent_description)

        # Common arguments for all generators
        args = (
            parsed_intent.get("pcs", 0),
            parsed_intent.get("routers", 0),
            parsed_intent.get("switches", 0),
            parsed_intent.get("hubs", 0),
            parsed_intent.get("servers", 0),
            parsed_intent.get("firewalls", 0),
            parsed_intent.get("isps", 0),
            canvas_width, canvas_height
        )

        # Generate topology using appropriate method
        if topology_type == "star":
            return self.generate_star(*args)
        elif topology_type == "ring":
            return self.generate_ring(*args)
        elif topology_type == "mesh":
            return self.generate_mesh(*args)
        elif topology_type == "tree":
            return self.generate_tree(*args)
        else:  # Default to hierarchical
            return self.generate_hierarchical(*args)

    def _parse_intent_description(self, description: str) -> Dict[str, int]:
        """
        Parse natural language description to extract network device counts.

        Args:
            description: Natural language description

        Returns:
            Dictionary with device counts
        """
        description = description.lower()
        parsed = {
            "pcs": 0,
            "routers": 0,
            "switches": 0,
            "hubs": 0,
            "servers": 0,
            "firewalls": 1,
            "isps": 1
        }

        patterns = {
            "pcs": r'(\d+|a|an)\s*(?:pc|computer|host|end\s*device)s?\b',
            "routers": r'(\d+|a|an)\s*router',
            "switches": r'(\d+|a|an)\s*switch',
            "servers": r'(\d+|a|an)\s*server',
            "firewalls": r'(\d+|a|an)\s*firewall',
            "isps": r'(\d+|a|an)\s*isp',
            "hubs": r'(\d+|a|an)\s*hub',
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, description)
            if match:
                val = match.group(1)
                if val in ['a', 'an']:
                    parsed[key] = 1
                else:
                    parsed[key] = int(val)

        # Fallback defaults if nothing detected
        if sum(parsed.values()) == 0:
             parsed["pcs"] = 4
             parsed["routers"] = 1
             parsed["switches"] = 1

        return parsed

    def _determine_topology_type(self, parsed_intent: Dict[str, int], description: str = "") -> str:
        """
        Determine the most appropriate topology type based on parsed intent.

        Args:
            parsed_intent: Parsed device counts and requirements
            description: Original intent description for keyword analysis

        Returns:
            Topology type string
        """
        description = description.lower()
        
        # Explicit keywords
        if "ring" in description: return "ring"
        if "mesh" in description: return "mesh"
        if "star" in description: return "star"
        if "tree" in description: return "tree"
        if "hierarchical" in description: return "hierarchical"

        # Contextual keywords
        if "redundant" in description or "backup" in description or "fault tolerance" in description:
            if parsed_intent["routers"] >= 3:
                return "mesh"
            return "hierarchical"

        if "secure" in description:
            return "hierarchical"

        # Simple heuristic-based topology selection
        total_devices = parsed_intent["routers"] + parsed_intent["switches"] + parsed_intent["hubs"]

        # Star topology: Good for central management, single point of failure
        if parsed_intent["routers"] <= 2 and parsed_intent["switches"] >= 1:
            return "star"

        # Ring topology: Good for redundancy, equal path lengths
        if parsed_intent["routers"] >= 3 and parsed_intent["switches"] == 0:
            return "ring"

        # Mesh topology: Maximum redundancy, complex
        if parsed_intent["routers"] >= 4 and total_devices >= 6:
            return "mesh"

        # Tree topology: Hierarchical, scalable
        if parsed_intent["routers"] >= 2 and parsed_intent["switches"] >= 2:
            return "tree"

        # Default to hierarchical for most cases
        return "hierarchical"

    def _find_nearest_node(self, topology: Topology, target_node: str, candidate_nodes: List[str]) -> Optional[str]:
        """
        Find the nearest node in candidate_nodes to target_node.

        Args:
            topology: Network topology
            target_node: Target node ID
            candidate_nodes: List of candidate node IDs

        Returns:
            Nearest node ID or None
        """
        target_coords = topology.get_node_coordinates(target_node)
        if not target_coords:
            return None

        min_distance = float('inf')
        nearest = None

        for candidate in candidate_nodes:
            candidate_coords = topology.get_node_coordinates(candidate)
            if candidate_coords:
                distance = math.sqrt(
                    (target_coords[0] - candidate_coords[0]) ** 2 +
                    (target_coords[1] - candidate_coords[1]) ** 2
                )
                if distance < min_distance:
                    min_distance = distance
                    nearest = candidate

        return nearest
