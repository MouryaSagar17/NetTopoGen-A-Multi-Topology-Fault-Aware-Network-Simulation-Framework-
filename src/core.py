"""
Core Module

This module contains the fundamental classes for network topology representation.
"""

from typing import Dict, List, Set, Optional, Any, Tuple
import networkx as nx # pyright: ignore[reportMissingModuleSource]
from dataclasses import dataclass, field


@dataclass
class Link:
    """
    Represents a network link between two nodes.
    """
    node_a: str
    node_b: str
    delay: float = 10.0  # ms
    bandwidth: float = 1e9  # 1 Gbps
    loss: float = 0.0  # packet loss probability
    status: bool = True  # True if link is operational
    is_inferred: bool = False  # True if link was inferred (e.g. access link)

    @property
    def nodes(self) -> Tuple[str, str]:
        """Returns the two nodes connected by this link."""
        return (self.node_a, self.node_b)

    def __hash__(self):
        """Make Link hashable for use in sets."""
        return hash((self.node_a, self.node_b, self.delay, self.bandwidth, self.loss))

    def __eq__(self, other):
        """Check equality based on nodes and properties."""
        if not isinstance(other, Link):
            return False
        return (self.node_a == other.node_a and self.node_b == other.node_b and
                self.delay == other.delay and self.bandwidth == other.bandwidth and
                self.loss == other.loss)


@dataclass
class Node:
    """
    Represents a network node (router, switch, host, etc.).
    """
    node_id: str
    node_type: str = "router"  # router, switch, host, hub
    coordinates: Optional[Tuple[int, int]] = None
    interfaces: Dict[str, Any] = field(default_factory=dict)
    status: bool = True  # True if node is operational

    def __post_init__(self):
        """Initialize node properties based on type."""
        if self.node_type == "router":
            self.interfaces = {"eth0": {"ip": "192.168.1.1", "mask": "255.255.255.0"}}
        elif self.node_type == "switch":
            self.interfaces = {"port1": {}, "port2": {}}
        elif self.node_type == "host":
            self.interfaces = {"eth0": {"ip": "192.168.1.100", "mask": "255.255.255.0"}}
        elif self.node_type == "hub":
            self.interfaces = {"port1": {}, "port2": {}, "port3": {}, "port4": {}}
        elif self.node_type == "server":
            self.interfaces = {"eth0": {"ip": "192.168.1.200", "mask": "255.255.255.0"}}
        elif self.node_type == "firewall":
            self.interfaces = {"eth0": {}, "eth1": {}}
        elif self.node_type == "isp":
            self.interfaces = {"eth0": {"ip": "8.8.8.8", "mask": "255.255.255.255"}}
        elif self.node_type == "ap":
            self.interfaces = {"eth0": {}, "wlan0": {}}
        elif self.node_type == "load_balancer":
            self.interfaces = {"eth0": {}, "eth1": {}, "eth2": {}}


class Topology:
    """
    Represents a network topology using NetworkX graph.
    """

    def __init__(self):
        self.graph = nx.Graph()
        self.nodes: Dict[str, Node] = {}
        self.links: Dict[Tuple[str, str], Link] = {}
        self.node_coordinates: Dict[str, Tuple[int, int]] = {}

    def add_node(self, node: Node):
        """
        Add a node to the topology.

        Args:
            node: Node object to add
        """
        self.graph.add_node(node.node_id)
        self.nodes[node.node_id] = node
        if node.coordinates:
            self.node_coordinates[node.node_id] = node.coordinates

    def add_link(self, link: Link):
        """
        Add a link between two nodes.

        Args:
            link: Link object to add
        """
        self.graph.add_edge(link.node_a, link.node_b)
        link_key = tuple(sorted((link.node_a, link.node_b)))
        self.links[link_key] = link

    def remove_node(self, node_id: str):
        """
        Remove a node and all its links from the topology.

        Args:
            node_id: ID of node to remove
        """
        if node_id in self.nodes:
            # Remove all links connected to this node
            links_to_remove = []
            for link_key, link in self.links.items():
                if node_id in link_key:
                    links_to_remove.append(link_key)

            for link_key in links_to_remove:
                del self.links[link_key]

            # Remove from graph and nodes dict
            self.graph.remove_node(node_id)
            del self.nodes[node_id]
            if node_id in self.node_coordinates:
                del self.node_coordinates[node_id]

    def remove_link(self, node_a: str, node_b: str):
        """
        Remove a link between two nodes.

        Args:
            node_a: First node ID
            node_b: Second node ID
        """
        link_key = tuple(sorted((node_a, node_b)))
        if link_key in self.links:
            self.graph.remove_edge(node_a, node_b)
            del self.links[link_key]

    def get_node(self, node_id: str) -> Optional[Node]:
        """
        Get a node by ID.

        Args:
            node_id: Node ID

        Returns:
            Node object or None if not found
        """
        return self.nodes.get(node_id)

    def get_link(self, node_a: str, node_b: str) -> Optional[Link]:
        """
        Get a link between two nodes.

        Args:
            node_a: First node ID
            node_b: Second node ID

        Returns:
            Link object or None if not found
        """
        link_key = tuple(sorted((node_a, node_b)))
        return self.links.get(link_key)

    def get_neighbors(self, node_id: str) -> List[Node]:
        """
        Get all neighbor nodes of a given node.

        Args:
            node_id: Node ID

        Returns:
            List of neighbor Node objects
        """
        if node_id not in self.graph:
            return []

        neighbors = []
        for neighbor_id in self.graph.neighbors(node_id):
            neighbor = self.nodes.get(neighbor_id)
            if neighbor:
                neighbors.append(neighbor)

        return neighbors

    def get_all_nodes(self) -> List[Node]:
        """
        Get all nodes in the topology.

        Returns:
            List of all Node objects
        """
        return list(self.nodes.values())

    def get_all_links(self) -> List[Link]:
        """
        Get all links in the topology.

        Returns:
            List of all Link objects
        """
        return list(self.links.values())

    def is_connected(self) -> bool:
        """
        Check if the topology is connected.

        Returns:
            True if topology is connected, False otherwise
        """
        return nx.is_connected(self.graph) if self.graph.nodes() else False

    def get_shortest_path(self, source: str, target: str) -> Optional[List[str]]:
        """
        Get the shortest path between two nodes.

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            List of node IDs in the path, or None if no path exists
        """
        try:
            return nx.shortest_path(self.graph, source, target)
        except nx.NetworkXNoPath:
            return None

    def get_path_length(self, path: List[str]) -> float:
        """
        Calculate the total length/cost of a path.

        Args:
            path: List of node IDs

        Returns:
            Total path cost (sum of link delays)
        """
        if len(path) < 2:
            return 0.0

        total_cost = 0.0
        for i in range(len(path) - 1):
            link = self.get_link(path[i], path[i+1])
            if link:
                total_cost += link.delay

        return total_cost

    def update_node_coordinates(self, node_id: str, coordinates: Tuple[int, int]):
        """
        Update the coordinates of a node.

        Args:
            node_id: Node ID
            coordinates: New (x, y) coordinates
        """
        if node_id in self.nodes:
            self.nodes[node_id].coordinates = coordinates
            self.node_coordinates[node_id] = coordinates

    def get_node_coordinates(self, node_id: str) -> Optional[Tuple[int, int]]:
        """
        Get the coordinates of a node.

        Args:
            node_id: Node ID

        Returns:
            (x, y) coordinates or None if not set
        """
        return self.node_coordinates.get(node_id)

    def export_to_graphml(self, filename: str):
        """
        Export topology to GraphML format.

        Args:
            filename: Output filename
        """
        # Add node attributes
        for node_id, node in self.nodes.items():
            self.graph.nodes[node_id]['type'] = node.node_type
            if node.coordinates:
                self.graph.nodes[node_id]['x'] = node.coordinates[0]
                self.graph.nodes[node_id]['y'] = node.coordinates[1]

        # Add edge attributes
        for (u, v), link in self.links.items():
            if self.graph.has_edge(u, v):
                self.graph.edges[u, v]['delay'] = link.delay
                self.graph.edges[u, v]['bandwidth'] = link.bandwidth
                self.graph.edges[u, v]['loss'] = link.loss
                self.graph.edges[u, v]['status'] = link.status

        nx.write_graphml(self.graph, filename)

    def import_from_graphml(self, filename: str):
        """
        Import topology from GraphML format.

        Args:
            filename: Input filename
        """
        self.graph = nx.read_graphml(filename)

        # Reconstruct nodes and links from graph
        self.nodes = {}
        self.links = {}
        self.node_coordinates = {}

        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get('type', 'router')
            coordinates = None
            if 'x' in node_data and 'y' in node_data:
                coordinates = (int(node_data['x']), int(node_data['y']))

            node = Node(node_id=node_id, node_type=node_type, coordinates=coordinates)
            self.nodes[node_id] = node
            if coordinates:
                self.node_coordinates[node_id] = coordinates

        for u, v, edge_data in self.graph.edges(data=True):
            link = Link(
                node_a=u,
                node_b=v,
                delay=float(edge_data.get('delay', 10.0)),
                bandwidth=float(edge_data.get('bandwidth', 1e9)),
                loss=float(edge_data.get('loss', 0.0)),
                status=bool(edge_data.get('status', True))
            )
            link_key = tuple(sorted((u, v)))
            self.links[link_key] = link

    def __str__(self) -> str:
        """String representation of the topology."""
        return f"Topology with {len(self.nodes)} nodes and {len(self.links)} links"

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"Topology(nodes={list(self.nodes.keys())}, links={list(self.links.keys())})"
