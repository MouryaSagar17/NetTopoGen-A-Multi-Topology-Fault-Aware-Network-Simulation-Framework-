"""
Traffic Simulation Module

This module handles traffic generation and simulation in the network.
"""

import random
import time
import os
import sys
from typing import List, Dict, Any, Optional, Tuple

# Add the parent directory to the Python path to import src modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core import Topology
from src.traffic_model import TrafficGenerator, CBRGenerator, BurstyGenerator

class TrafficSimulator:
    """
    Manages traffic generation and simulation.
    """

    def __init__(self, topology: Topology, random_seed: int = None):
        self.topology = topology
        if random_seed is not None:
            random.seed(random_seed)

        self.generators: List[TrafficGenerator] = []
        self.active_traffic = {}
        self.traffic_stats = {
            "packets_generated": 0,
            "packets_delivered": 0,
            "packets_dropped": 0,
            "total_delay": 0.0,
            "total_hops": 0
        }

    def add_generator(self, generator: TrafficGenerator):
        """
        Add a traffic generator to the simulation.

        Args:
            generator: TrafficGenerator instance
        """
        self.generators.append(generator)

    def create_cbr_traffic(self, source: str, destination: str, rate: float) -> CBRGenerator:
        """
        Create CBR (Constant Bit Rate) traffic generator.

        Args:
            source: Source node ID
            destination: Destination node ID
            rate: Packet rate (packets per second)

        Returns:
            CBRGenerator instance
        """
        generator = CBRGenerator(source, destination, rate)
        self.add_generator(generator)
        return generator

    def create_bursty_traffic(self, source: str, destination: str,
                            burst_rate: float, idle_rate: float,
                            burst_duration: float, idle_duration: float) -> BurstyGenerator:
        """
        Create bursty traffic generator.

        Args:
            source: Source node ID
            destination: Destination node ID
            burst_rate: Packet rate during burst
            idle_rate: Packet rate during idle periods
            burst_duration: Duration of burst periods
            idle_duration: Duration of idle periods

        Returns:
            BurstyGenerator instance
        """
        generator = BurstyGenerator(source, destination, burst_rate,
                                  idle_rate, burst_duration, idle_duration)
        self.add_generator(generator)
        return generator

    def generate_traffic(self, current_time: float) -> List[Any]:
        """
        Generate traffic packets from all generators at current time.

        Args:
            current_time: Current simulation time

        Returns:
            List of generated packets
        """
        all_packets = []
        for generator in self.generators:
            packets = generator.generate(current_time)
            all_packets.extend(packets)
            self.traffic_stats["packets_generated"] += len(packets)

        return all_packets

    def simulate_step(self, current_time: float, routing_table: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Simulate one step of traffic flow.

        Args:
            current_time: Current simulation time
            routing_table: Current routing table (optional)

        Returns:
            Dictionary with simulation results
        """
        # Generate new traffic
        new_packets = self.generate_traffic(current_time)

        # Process existing traffic (simplified - would need full discrete event simulation)
        results = {
            "time": current_time,
            "new_packets": len(new_packets),
            "active_flows": len(self.generators),
            "total_generated": self.traffic_stats["packets_generated"]
        }

        return results

    def get_traffic_stats(self) -> Dict[str, Any]:
        """
        Get current traffic statistics.

        Returns:
            Dictionary with traffic statistics
        """
        stats = self.traffic_stats.copy()
        stats["active_generators"] = len(self.generators)
        stats["packet_delivery_ratio"] = (
            stats["packets_delivered"] / stats["packets_generated"]
            if stats["packets_generated"] > 0 else 0
        )
        stats["average_delay"] = (
            stats["total_delay"] / stats["packets_delivered"]
            if stats["packets_delivered"] > 0 else 0
        )
        stats["average_hops"] = (
            stats["total_hops"] / stats["packets_delivered"]
            if stats["packets_delivered"] > 0 else 0
        )
        return stats

    def reset_stats(self):
        """Reset traffic statistics."""
        self.traffic_stats = {
            "packets_generated": 0,
            "packets_delivered": 0,
            "packets_dropped": 0,
            "total_delay": 0.0,
            "total_hops": 0
        }

    def clear_generators(self):
        """Remove all traffic generators."""
        self.generators.clear()
        self.reset_stats()

class TrafficPatternGenerator:
    """
    Generates various traffic patterns for simulation experiments.
    """

    def __init__(self, topology: Topology, random_seed: int = None):
        self.topology = topology
        if random_seed is not None:
            random.seed(random_seed)

    def generate_random_pairs(self, num_pairs: int) -> List[Tuple[str, str]]:
        """
        Generate random source-destination pairs.

        Args:
            num_pairs: Number of pairs to generate

        Returns:
            List of (source, destination) tuples
        """
        nodes = list(self.topology.graph.nodes())
        if len(nodes) < 2:
            return []

        pairs = []
        for _ in range(num_pairs):
            src, dst = random.sample(nodes, 2)
            pairs.append((src, dst))

        return pairs

    def generate_mesh_traffic(self, load_factor: float = 0.5) -> List[TrafficGenerator]:
        """
        Generate traffic for mesh topology (all-to-all communication).

        Args:
            load_factor: Factor controlling traffic intensity

        Returns:
            List of traffic generators
        """
        generators = []
        nodes = list(self.topology.graph.nodes())

        base_rate = 10 * load_factor  # Base packet rate

        for i, src in enumerate(nodes):
            for j, dst in enumerate(nodes):
                if i != j:
                    rate = base_rate / (len(nodes) - 1)  # Distribute load
                    generators.append(CBRGenerator(src, dst, rate))

        return generators

    def generate_hotspot_traffic(self, hotspot_node: str, load_factor: float = 0.8) -> List[TrafficGenerator]:
        """
        Generate traffic with a hotspot node.

        Args:
            hotspot_node: Node that receives high traffic
            load_factor: Traffic load factor

        Returns:
            List of traffic generators
        """
        generators = []
        nodes = [n for n in self.topology.graph.nodes() if n != hotspot_node]

        base_rate = 50 * load_factor

        for src in nodes:
            rate = base_rate / len(nodes)
            generators.append(CBRGenerator(src, hotspot_node, rate))

        return generators

    def generate_bursty_background_traffic(self, num_flows: int = 5,
                                         burst_rate: float = 100,
                                         idle_rate: float = 1,
                                         burst_duration: float = 1.0,
                                         idle_duration: float = 4.0) -> List[TrafficGenerator]:
        """
        Generate background bursty traffic.

        Args:
            num_flows: Number of background flows
            burst_rate: Packet rate during bursts
            idle_rate: Packet rate during idle periods
            burst_duration: Burst duration
            idle_duration: Idle duration

        Returns:
            List of BurstyGenerator instances
        """
        generators = []
        pairs = self.generate_random_pairs(num_flows)

        for src, dst in pairs:
            generators.append(BurstyGenerator(src, dst, burst_rate,
                                            idle_rate, burst_duration, idle_duration))

        return generators
