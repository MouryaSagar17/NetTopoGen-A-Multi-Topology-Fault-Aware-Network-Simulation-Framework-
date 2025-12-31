"""
Routing Algorithms Module

This module implements various routing algorithms for network path computation.
"""

import heapq
import time
from typing import Dict, List, Tuple, Optional, Any, Set
from src.core import Topology
from src.config import QOS_WEIGHTS


class RoutingEngine:
    """
    Unified interface for different routing algorithms.
    """

    def __init__(self, topology: Topology, qos_weights: Optional[Dict[str, float]] = None):
        """
        Initialize routing engine.

        Args:
            topology: Network topology
            qos_weights: QoS weights for cost computation
        """
        self.topology = topology
        self.qos_weights = qos_weights or QOS_WEIGHTS.copy()

    def compute_route(self, algorithm: str, source: str, target: str) -> Tuple[Optional[List[str]], float]:
        """
        Compute route using specified algorithm.

        Args:
            algorithm: Algorithm name ("dijkstra", "astar", "bellman_ford", "rip")
            source: Source node ID
            target: Target node ID

        Returns:
            Tuple of (path, cost) or (None, inf) if no path
        """
        if algorithm.lower() == "dijkstra":
            return self._dijkstra(source, target)
        elif algorithm.lower() == "astar":
            return self._astar(source, target)
        elif algorithm.lower() == "bellman_ford":
            return self._bellman_ford(source, target)
        elif algorithm.lower() == "rip":
            return self._bellman_ford(source, target)  # RIP uses distance vector
        else:
            raise ValueError(f"Unknown algorithm: {algorithm}")

    def _dijkstra(self, source: str, target: str) -> Tuple[Optional[List[str]], float]:
        """
        Dijkstra's algorithm for shortest path.

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            Tuple of (path, cost)
        """
        # Priority queue: (cost, node)
        pq = [(0, source)]
        came_from = {source: None}
        cost_so_far = {source: 0}

        while pq:
            current_cost, current = heapq.heappop(pq)

            if current == target:
                break

            for neighbor in self.topology.graph.neighbors(current):
                link = self.topology.get_link(current, neighbor)
                if not link or not link.status:
                    continue

                # Calculate edge cost using QoS weights
                edge_cost = self._calculate_link_cost(link)
                new_cost = cost_so_far[current] + edge_cost

                if neighbor not in cost_so_far or new_cost < cost_so_far[neighbor]:
                    cost_so_far[neighbor] = new_cost
                    priority = new_cost
                    heapq.heappush(pq, (priority, neighbor))
                    came_from[neighbor] = current

        if target not in came_from:
            return None, float('inf')

        # Reconstruct path
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()

        return path, cost_so_far[target]

    def _astar(self, source: str, target: str) -> Tuple[Optional[List[str]], float]:
        """
        A* algorithm with Euclidean distance heuristic.

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            Tuple of (path, cost)
        """
        pq = [(0, source)]  # (f_score, node)
        came_from = {source: None}
        g_score = {source: 0}  # Cost from start to node
        f_score = {source: self._heuristic(source, target)}

        while pq:
            _, current = heapq.heappop(pq)

            if current == target:
                break

            for neighbor in self.topology.graph.neighbors(current):
                link = self.topology.get_link(current, neighbor)
                if not link or not link.status:
                    continue

                edge_cost = self._calculate_link_cost(link)
                tentative_g_score = g_score[current] + edge_cost

                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f_score[neighbor] = tentative_g_score + self._heuristic(neighbor, target)
                    heapq.heappush(pq, (f_score[neighbor], neighbor))

        if target not in came_from:
            return None, float('inf')

        # Reconstruct path
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = came_from[current]
        path.reverse()

        return path, g_score[target]

    def _bellman_ford(self, source: str, target: str) -> Tuple[Optional[List[str]], float]:
        """
        Bellman-Ford algorithm (handles negative edges, but we don't have them).

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            Tuple of (path, cost)
        """
        nodes = list(self.topology.graph.nodes())
        if source not in nodes or target not in nodes:
            return None, float('inf')

        # Initialize distances
        distance = {node: float('inf') for node in nodes}
        predecessor = {node: None for node in nodes}
        distance[source] = 0

        # Relax edges |V| - 1 times
        for _ in range(len(nodes) - 1):
            for u, v in self.topology.graph.edges():
                link = self.topology.get_link(u, v)
                if not link or not link.status:
                    continue

                edge_cost = self._calculate_link_cost(link)
                if distance[u] + edge_cost < distance[v]:
                    distance[v] = distance[u] + edge_cost
                    predecessor[v] = u

        # Check for negative cycles (shouldn't happen in our case)
        for u, v in self.topology.graph.edges():
            link = self.topology.get_link(u, v)
            if link and link.status:
                edge_cost = self._calculate_link_cost(link)
                if distance[u] + edge_cost < distance[v]:
                    return None, float('inf')  # Negative cycle

        if distance[target] == float('inf'):
            return None, float('inf')

        # Reconstruct path
        path = []
        current = target
        while current is not None:
            path.append(current)
            current = predecessor[current]
        path.reverse()

        return path, distance[target]

    def _calculate_link_cost(self, link) -> float:
        """
        Calculate link cost based on QoS weights.

        Args:
            link: Link object

        Returns:
            Cost value
        """
        # Cost = α·delay + β·(1/bandwidth) + γ·loss
        alpha = self.qos_weights.get("alpha", 1.0)
        beta = self.qos_weights.get("beta", 1.0)
        gamma = self.qos_weights.get("gamma", 1.0)

        delay_cost = alpha * (link.delay / 1000.0)  # Convert ms to seconds
        bandwidth_cost = beta * (1.0 / link.bandwidth) if link.bandwidth > 0 else float('inf')
        loss_cost = gamma * link.loss

        return delay_cost + bandwidth_cost + loss_cost

    def _heuristic(self, node_a: str, node_b: str) -> float:
        """
        Euclidean distance heuristic for A*.

        Args:
            node_a: First node ID
            node_b: Second node ID

        Returns:
            Heuristic distance
        """
        coords_a = self.topology.get_node_coordinates(node_a)
        coords_b = self.topology.get_node_coordinates(node_b)

        if not coords_a or not coords_b:
            return 0.0  # No heuristic information

        dx = coords_a[0] - coords_b[0]
        dy = coords_a[1] - coords_b[1]
        return (dx**2 + dy**2)**0.5

    def compute_all_pairs_shortest_paths(self, algorithm: str = "dijkstra") -> Dict[Tuple[str, str], Tuple[List[str], float]]:
        """
        Compute shortest paths between all pairs of nodes.

        Args:
            algorithm: Algorithm to use

        Returns:
            Dictionary mapping (source, target) to (path, cost)
        """
        nodes = list(self.topology.graph.nodes())
        all_pairs = {}

        for source in nodes:
            for target in nodes:
                if source != target:
                    path, cost = self.compute_route(algorithm, source, target)
                    all_pairs[(source, target)] = (path, cost)

        return all_pairs

    def get_network_diameter(self, algorithm: str = "dijkstra") -> Tuple[int, float]:
        """
        Calculate network diameter (longest shortest path).

        Args:
            algorithm: Algorithm to use

        Returns:
            Tuple of (diameter_hops, diameter_cost)
        """
        all_pairs = self.compute_all_pairs_shortest_paths(algorithm)

        max_hops = 0
        max_cost = 0.0

        for (source, target), (path, cost) in all_pairs.items():
            if path:
                hops = len(path) - 1
                max_hops = max(max_hops, hops)
                max_cost = max(max_cost, cost)

        return max_hops, max_cost

    def get_average_path_length(self, algorithm: str = "dijkstra") -> Tuple[float, float]:
        """
        Calculate average path length in hops and cost.

        Args:
            algorithm: Algorithm to use

        Returns:
            Tuple of (avg_hops, avg_cost)
        """
        all_pairs = self.compute_all_pairs_shortest_paths(algorithm)

        total_hops = 0
        total_cost = 0.0
        count = 0

        for (source, target), (path, cost) in all_pairs.items():
            if path:
                hops = len(path) - 1
                total_hops += hops
                total_cost += cost
                count += 1

        if count == 0:
            return 0.0, 0.0

        return total_hops / count, total_cost / count

    def find_critical_links(self, algorithm: str = "dijkstra") -> List[Tuple[str, str]]:
        """
        Find links that, if removed, would disconnect the network or significantly increase diameter.

        Args:
            algorithm: Algorithm to use

        Returns:
            List of critical link tuples
        """
        original_diameter = self.get_network_diameter(algorithm)[1]
        critical_links = []

        for link in self.topology.get_all_links():
            # Temporarily disable link
            original_status = link.status
            link.status = False

            try:
                new_diameter = self.get_network_diameter(algorithm)[1]
                if new_diameter > original_diameter * 1.5:  # Significant increase
                    critical_links.append((link.node_a, link.node_b))
            finally:
                # Restore link status
                link.status = original_status

        return critical_links

    def compare_algorithms(self, source: str, target: str) -> Dict[str, Dict[str, Any]]:
        """
        Compare different routing algorithms for a specific route.

        Args:
            source: Source node ID
            target: Target node ID

        Returns:
            Dictionary with algorithm comparison results
        """
        algorithms = ["dijkstra", "astar", "bellman_ford"]
        results = {}

        for algorithm in algorithms:
            start_time = time.time()
            path, cost = self.compute_route(algorithm, source, target)
            end_time = time.time()

            results[algorithm] = {
                "path": path,
                "cost": cost,
                "hops": len(path) - 1 if path else 0,
                "computation_time": end_time - start_time,
                "found_path": path is not None
            }

        return results
