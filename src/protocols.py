"""
Protocols Module

This module implements routing protocols like RIP and OSPF.
"""

import time
import heapq
from typing import Dict, List, Tuple, Optional, Any, Set
from src.core import Topology
from src.config import RIP_UPDATE_INTERVAL, RIP_TIMEOUT, RIP_GARBAGE_COLLECTION, OSPF_UPDATE_INTERVAL, INITIAL_CONVERGENCE_TIME


class RIPRouter:
    """
    RIP (Routing Information Protocol) router implementation.
    """

    def __init__(self, router_id: str, topology: Topology):
        """
        Initialize RIP router.

        Args:
            router_id: Router identifier
            topology: Network topology
        """
        self.router_id = router_id
        self.topology = topology

        # RIP routing table: destination -> (next_hop, cost, timestamp)
        self.routing_table: Dict[str, Tuple[str, int, float]] = {}

        # Neighbor information
        self.neighbors: Set[str] = set()

        # Protocol parameters
        self.update_interval = RIP_UPDATE_INTERVAL
        self.timeout = RIP_TIMEOUT
        self.garbage_collection = RIP_GARBAGE_COLLECTION

        # Timestamps
        self.last_update = time.time()
        self.last_full_update = 0

        # Initialize routing table
        self._initialize_routing_table()

    def _initialize_routing_table(self):
        """Initialize routing table with directly connected networks."""
        # Add directly connected neighbors
        for neighbor in self.topology.get_neighbors(self.router_id):
            link = self.topology.get_link(self.router_id, neighbor)
            if link:
                # RIP cost is typically 1 for each hop
                cost = 1
                self.routing_table[neighbor.node_id] = (neighbor.node_id, cost, time.time())
                self.neighbors.add(neighbor.node_id)

        # Add self with cost 0
        self.routing_table[self.router_id] = (self.router_id, 0, time.time())

    def update_routing_table(self, neighbor_updates: Dict[str, Dict[str, int]]):
        """
        Update routing table based on neighbor advertisements.

        Args:
            neighbor_updates: Updates from neighbors (neighbor -> {dest: cost})
        """
        current_time = time.time()
        updated = False

        for neighbor, routes in neighbor_updates.items():
            if neighbor not in self.neighbors:
                continue

            for destination, advertised_cost in routes.items():
                # RIP split horizon: don't advertise routes back to sender
                if destination == self.router_id:
                    continue

                # Calculate new cost (advertised cost + 1)
                new_cost = advertised_cost + 1

                # Apply RIP infinity (16 is infinity in RIP)
                if new_cost >= 16:
                    new_cost = 16

                # Update if better route found or existing route timed out
                if (destination not in self.routing_table or
                    new_cost < self.routing_table[destination][1] or
                    current_time - self.routing_table[destination][2] > self.timeout):

                    if new_cost < 16:  # Don't install infinite routes
                        self.routing_table[destination] = (neighbor, new_cost, current_time)
                        updated = True

        # Clean up expired routes
        expired_routes = []
        for dest, (_, _, timestamp) in self.routing_table.items():
            if current_time - timestamp > self.garbage_collection:
                expired_routes.append(dest)

        for dest in expired_routes:
            if dest in self.routing_table:
                del self.routing_table[dest]
                updated = True

        if updated:
            self.last_update = current_time

    def get_routing_updates(self) -> Dict[str, Dict[str, int]]:
        """
        Generate routing updates to send to neighbors.

        Returns:
            Updates for each neighbor (neighbor -> {dest: cost})
        """
        updates = {}

        for neighbor in self.neighbors:
            neighbor_update = {}

            for dest, (next_hop, cost, _) in self.routing_table.items():
                # Split horizon with poisoned reverse
                if next_hop == neighbor:
                    neighbor_update[dest] = 16  # Poisoned reverse
                else:
                    neighbor_update[dest] = cost

            updates[neighbor] = neighbor_update

        return updates

    def get_route(self, destination: str) -> Optional[Tuple[str, int]]:
        """
        Get route to destination.

        Args:
            destination: Destination node

        Returns:
            Tuple of (next_hop, cost) or None
        """
        if destination in self.routing_table:
            next_hop, cost, timestamp = self.routing_table[destination]

            # Check if route is still valid
            if time.time() - timestamp <= self.timeout:
                return (next_hop, cost)

        return None

    def get_routing_table(self) -> Dict[str, Tuple[str, int, float]]:
        """
        Get current routing table.

        Returns:
            Routing table dictionary
        """
        return self.routing_table.copy()

    def should_send_update(self) -> bool:
        """
        Check if it's time to send a periodic update.

        Returns:
            True if update should be sent
        """
        return time.time() - self.last_full_update >= self.update_interval

    def mark_update_sent(self):
        """Mark that a full update has been sent."""
        self.last_full_update = time.time()

    def add_neighbor(self, neighbor_id: str):
        """
        Add a new neighbor.

        Args:
            neighbor_id: Neighbor router ID
        """
        self.neighbors.add(neighbor_id)

    def remove_neighbor(self, neighbor_id: str):
        """
        Remove a neighbor and update routes.

        Args:
            neighbor_id: Neighbor router ID
        """
        if neighbor_id in self.neighbors:
            self.neighbors.remove(neighbor_id)

            # Remove routes that used this neighbor as next hop
            routes_to_remove = []
            for dest, (next_hop, _, _) in self.routing_table.items():
                if next_hop == neighbor_id:
                    routes_to_remove.append(dest)

            for dest in routes_to_remove:
                del self.routing_table[dest]


class OSPFRouter:
    """
    OSPF (Open Shortest Path First) router implementation.
    """

    def __init__(self, router_id: str, topology: Topology):
        """
        Initialize OSPF router.

        Args:
            router_id: Router identifier
            topology: Network topology
        """
        self.router_id = router_id
        self.topology = topology

        # OSPF routing table: destination -> (next_hop, cost, path)
        self.routing_table: Dict[str, Tuple[str, float, List[str]]] = {}

        # Link State Database (LSDB)
        self.lsdb: Dict[str, Dict[str, Any]] = {}

        # Neighbor information
        self.neighbors: Dict[str, Dict[str, Any]] = {}

        # Protocol parameters
        self.update_interval = OSPF_UPDATE_INTERVAL
        self.initial_convergence_time = INITIAL_CONVERGENCE_TIME

        # Timestamps
        self.last_update = time.time()
        self.convergence_time = 0

        # Initialize
        self._initialize_ospf()

    def _initialize_ospf(self):
        """Initialize OSPF structures."""
        # Add self to LSDB
        self.lsdb[self.router_id] = {
            "router_id": self.router_id,
            "links": [],
            "sequence_number": 1,
            "timestamp": time.time()
        }

        # Add directly connected links
        for neighbor in self.topology.get_neighbors(self.router_id):
            link = self.topology.get_link(self.router_id, neighbor)
            if link:
                self.lsdb[self.router_id]["links"].append({
                    "neighbor": neighbor.node_id,
                    "cost": self._calculate_link_cost(link),
                    "type": "p2p"  # Point-to-point
                })

        # Initialize neighbors
        for neighbor in self.topology.get_neighbors(self.router_id):
            self.neighbors[neighbor.node_id] = {
                "state": "init",
                "last_seen": time.time()
            }

    def _calculate_link_cost(self, link) -> float:
        """
        Calculate OSPF link cost.

        Args:
            link: Link object

        Returns:
            Link cost
        """
        # OSPF cost is typically based on bandwidth
        # Cost = 10^8 / bandwidth (in bps)
        if link.bandwidth > 0:
            return 100000000 / link.bandwidth
        else:
            return 1000  # Default high cost

    def run_spf(self):
        """
        Run Shortest Path First (SPF) algorithm to compute routes.

        Returns:
            True if routing table was updated
        """
        start_time = time.time()

        # Build graph from LSDB
        graph = self._build_topology_graph()

        # Run Dijkstra from self
        distances, previous = self._dijkstra(graph, self.router_id)

        # Update routing table
        updated = False
        for dest, distance in distances.items():
            if dest != self.router_id and distance < float('inf'):
                # Find next hop
                next_hop = self._get_next_hop(previous, dest)

                # Get path
                path = self._reconstruct_path(previous, dest)

                # Update routing table
                if (dest not in self.routing_table or
                    distance < self.routing_table[dest][1]):
                    self.routing_table[dest] = (next_hop, distance, path)
                    updated = True

        self.convergence_time = time.time() - start_time
        self.last_update = time.time()

        return updated

    def _build_topology_graph(self) -> Dict[str, Dict[str, float]]:
        """
        Build topology graph from LSDB.

        Returns:
            Graph as adjacency list with costs
        """
        graph = {}

        for router_id, lsa in self.lsdb.items():
            graph[router_id] = {}

            for link in lsa["links"]:
                neighbor = link["neighbor"]
                cost = link["cost"]
                graph[router_id][neighbor] = cost

        return graph

    def _dijkstra(self, graph: Dict[str, Dict[str, float]], source: str) -> Tuple[Dict[str, float], Dict[str, str]]:
        """
        Run Dijkstra's algorithm.

        Args:
            graph: Graph as adjacency list
            source: Source node

        Returns:
            Tuple of (distances, previous nodes)
        """
        distances = {node: float('inf') for node in graph}
        distances[source] = 0
        previous = {node: None for node in graph}

        pq = [(0, source)]

        while pq:
            current_distance, current = heapq.heappop(pq)

            if current_distance > distances[current]:
                continue

            for neighbor, weight in graph[current].items():
                distance = current_distance + weight

                if distance < distances[neighbor]:
                    distances[neighbor] = distance
                    previous[neighbor] = current
                    heapq.heappush(pq, (distance, neighbor))

        return distances, previous

    def _get_next_hop(self, previous: Dict[str, str], destination: str) -> str:
        """
        Get next hop to destination.

        Args:
            previous: Previous nodes from Dijkstra
            destination: Target destination

        Returns:
            Next hop node
        """
        current = destination
        while previous[current] is not None and previous[current] != self.router_id:
            current = previous[current]
        return current

    def _reconstruct_path(self, previous: Dict[str, str], destination: str) -> List[str]:
        """
        Reconstruct path from Dijkstra results.

        Args:
            previous: Previous nodes from Dijkstra
            destination: Target destination

        Returns:
            Path as list of nodes
        """
        path = []
        current = destination
        while current is not None:
            path.append(current)
            current = previous[current]
        path.reverse()
        return path

    def update_lsdb(self, neighbor_lsa: Dict[str, Any]):
        """
        Update Link State Database with neighbor's LSA.

        Args:
            neighbor_lsa: Link State Advertisement from neighbor

        Returns:
            True if LSDB was updated
        """
        router_id = neighbor_lsa["router_id"]
        sequence_number = neighbor_lsa["sequence_number"]

        # Check if we have newer information
        if (router_id in self.lsdb and
            self.lsdb[router_id]["sequence_number"] >= sequence_number):
            return False

        # Update LSDB
        self.lsdb[router_id] = neighbor_lsa.copy()
        self.lsdb[router_id]["timestamp"] = time.time()

        return True

    def get_lsa(self) -> Dict[str, Any]:
        """
        Get this router's Link State Advertisement.

        Returns:
            LSA dictionary
        """
        return self.lsdb[self.router_id].copy()

    def get_route(self, destination: str) -> Optional[Tuple[str, float, List[str]]]:
        """
        Get route to destination.

        Args:
            destination: Destination node

        Returns:
            Tuple of (next_hop, cost, path) or None
        """
        return self.routing_table.get(destination)

    def get_routing_table(self) -> Dict[str, Tuple[str, float, List[str]]]:
        """
        Get current routing table.

        Returns:
            Routing table dictionary
        """
        return self.routing_table.copy()

    def get_neighbors(self) -> Dict[str, Dict[str, Any]]:
        """
        Get neighbor information.

        Returns:
            Neighbor status dictionary
        """
        return self.neighbors.copy()

    def should_send_update(self) -> bool:
        """
        Check if it's time to send an update.

        Returns:
            True if update should be sent
        """
        return time.time() - self.last_update >= self.update_interval

    def get_convergence_time(self) -> float:
        """
        Get OSPF convergence time.

        Returns:
            Convergence time in seconds
        """
        return self.convergence_time

    def add_neighbor(self, neighbor_id: str):
        """
        Add a new neighbor.

        Args:
            neighbor_id: Neighbor router ID
        """
        if neighbor_id not in self.neighbors:
            self.neighbors[neighbor_id] = {
                "state": "init",
                "last_seen": time.time()
            }

    def remove_neighbor(self, neighbor_id: str):
        """
        Remove a neighbor.

        Args:
            neighbor_id: Neighbor router ID
        """
        if neighbor_id in self.neighbors:
            del self.neighbors[neighbor_id]

            # Remove from LSDB if present
            if neighbor_id in self.lsdb:
                del self.lsdb[neighbor_id]

            # Trigger SPF recalculation
            self.run_spf()


class RIPNetwork:
    """
    RIP network simulation with multiple routers.
    """

    def __init__(self, topology: Topology):
        """
        Initialize RIP network.

        Args:
            topology: Network topology
        """
        self.topology = topology
        self.routers: Dict[str, RIPRouter] = {}

        # Initialize routers for all router-type nodes
        for node_id, node in topology.nodes.items():
            if node.node_type == "router":
                self.routers[node_id] = RIPRouter(node_id, topology)

    def run_protocol(self, max_iterations: int = 50):
        """
        Run RIP protocol until convergence or max iterations.

        Args:
            max_iterations: Maximum number of iterations
        """
        for iteration in range(max_iterations):
            updated = False

            # Collect updates from all routers
            all_updates = {}
            for router_id, router in self.routers.items():
                all_updates[router_id] = router.get_routing_updates()

            # Send updates to neighbors
            for router_id, router in self.routers.items():
                neighbor_updates = {}

                for neighbor_id in router.neighbors:
                    if neighbor_id in all_updates:
                        neighbor_updates[neighbor_id] = all_updates[neighbor_id][router_id]

                if router.update_routing_table(neighbor_updates):
                    updated = True

            # Mark updates as sent
            for router in self.routers.values():
                router.mark_update_sent()

            # Check for convergence
            if not updated:
                break

    def get_routing_tables(self) -> Dict[str, Dict[str, Tuple[str, int, float]]]:
        """
        Get routing tables from all routers.

        Returns:
            Dictionary of routing tables
        """
        return {router_id: router.get_routing_table()
                for router_id, router in self.routers.items()}


class OSPFNetwork:
    """
    OSPF network simulation with multiple routers.
    """

    def __init__(self, topology: Topology):
        """
        Initialize OSPF network.

        Args:
            topology: Network topology
        """
        self.topology = topology
        self.routers: Dict[str, OSPFRouter] = {}

        # Initialize routers for all router-type nodes
        for node_id, node in topology.nodes.items():
            if node.node_type == "router":
                self.routers[node_id] = OSPFRouter(node_id, topology)

    def run_protocol(self, max_iterations: int = 10):
        """
        Run OSPF protocol until convergence.

        Args:
            max_iterations: Maximum number of iterations
        """
        # Flood LSAs
        for iteration in range(max_iterations):
            updated = False

            # Collect LSAs from all routers
            lsas = {}
            for router_id, router in self.routers.items():
                lsas[router_id] = router.get_lsa()

            # Flood LSAs to all routers
            for router_id, router in self.routers.items():
                for sender_id, lsa in lsas.items():
                    if sender_id != router_id:
                        if router.update_lsdb(lsa):
                            updated = True

            # Run SPF on all routers
            for router in self.routers.values():
                router.run_spf()

            # Check for convergence
            if not updated:
                break

    def get_routing_tables(self) -> Dict[str, Dict[str, Tuple[str, float, List[str]]]]:
        """
        Get routing tables from all routers.

        Returns:
            Dictionary of routing tables
        """
        return {router_id: router.get_routing_table()
                for router_id, router in self.routers.items()}

    def get_convergence_times(self) -> Dict[str, float]:
        """
        Get convergence times for all routers.

        Returns:
            Dictionary of convergence times
        """
        return {router_id: router.get_convergence_time()
                for router_id, router in self.routers.items()}
