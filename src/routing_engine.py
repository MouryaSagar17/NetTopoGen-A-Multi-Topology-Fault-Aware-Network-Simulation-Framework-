"""
Routing Engine Module

This module provides a unified interface for different routing algorithms
and manages routing table computations.
"""

import time
from typing import Dict, List, Tuple, Optional, Any
from src.core import Topology
from src.routing_algorithms import RoutingEngine as RoutingAlgorithmEngine

class RoutingEngine:
    """
    Manages routing computations and protocol interactions.
    """

    def __init__(self, topology: Topology):
        self.topology = topology
        self.routing_tables = {}  # node_id -> routing_table
        self.last_update = time.time()

        # Initialize routing tables for all nodes
        for node_id in self.topology.graph.nodes():
            self.routing_tables[node_id] = {}

    def compute_all_routes(self, algorithm: str = "dijkstra",
                          qos_weights: Dict[str, float] = None) -> Dict[str, Dict[str, Any]]:
        """
        Compute routes for all node pairs using specified algorithm.

        Args:
            algorithm: Routing algorithm ("dijkstra", "astar", "bellman_ford", "rip")
            qos_weights: QoS weights for cost computation

        Returns:
            Dictionary mapping source nodes to their routing tables
        """
        routing_engine = RoutingAlgorithmEngine(self.topology, qos_weights)

        for source in self.topology.graph.nodes():
            routing_table = {}
            for destination in self.topology.graph.nodes():
                if source != destination:
                    path, cost = routing_engine.compute_route(algorithm, source, destination)
                    if path:
                        next_hop = path[1] if len(path) > 1 else destination
                        routing_table[destination] = {
                            "next_hop": next_hop,
                            "cost": cost,
                            "path": path
                        }
            self.routing_tables[source] = routing_table

        self.last_update = time.time()
        return self.routing_tables

    def get_route(self, source: str, destination: str) -> Optional[Dict[str, Any]]:
        """
        Get the route from source to destination.

        Args:
            source: Source node ID
            destination: Destination node ID

        Returns:
            Route information or None if no route exists
        """
        if source not in self.routing_tables:
            return None
        return self.routing_tables[source].get(destination)

    def update_topology(self, topology: Topology):
        """
        Update the topology and recompute routes if necessary.

        Args:
            topology: New topology
        """
        self.topology = topology
        # Reinitialize routing tables for new nodes
        current_nodes = set(self.topology.graph.nodes())
        existing_nodes = set(self.routing_tables.keys())

        # Remove routing tables for nodes that no longer exist
        for node in existing_nodes - current_nodes:
            del self.routing_tables[node]

        # Add routing tables for new nodes
        for node in current_nodes - existing_nodes:
            self.routing_tables[node] = {}

    def get_routing_table(self, node_id: str) -> Dict[str, Any]:
        """
        Get the complete routing table for a node.

        Args:
            node_id: Node ID

        Returns:
            Routing table dictionary
        """
        return self.routing_tables.get(node_id, {})

    def get_all_routing_tables(self) -> Dict[str, Dict[str, Any]]:
        """
        Get routing tables for all nodes.

        Returns:
            Dictionary of all routing tables
        """
        return self.routing_tables.copy()

    def invalidate_routes(self, affected_links: List[Tuple[str, str]]):
        """
        Invalidate routes that use affected links.

        Args:
            affected_links: List of (u, v) link tuples that are affected
        """
        affected_links_set = set(tuple(sorted(link)) for link in affected_links)

        for source, routing_table in self.routing_tables.items():
            routes_to_remove = []
            for dest, route_info in routing_table.items():
                path = route_info.get("path", [])
                # Check if any link in the path is affected
                path_affected = False
                for i in range(len(path) - 1):
                    link = tuple(sorted((path[i], path[i+1])))
                    if link in affected_links_set:
                        path_affected = True
                        break
                if path_affected:
                    routes_to_remove.append(dest)

            for dest in routes_to_remove:
                del routing_table[dest]

    def get_convergence_time(self) -> float:
        """
        Get the time since last routing update.

        Returns:
            Time in seconds since last update
        """
        return time.time() - self.last_update

    def export_routing_tables(self, filename: str):
        """
        Export routing tables to JSON file.

        Args:
            filename: Output filename
        """
        import json
        data = {
            "timestamp": time.time(),
            "routing_tables": self.routing_tables
        }
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)
