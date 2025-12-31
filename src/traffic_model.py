"""
Traffic Model Module

This module defines traffic generators for network simulation.
"""

import random
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class Packet:
    """
    Represents a network packet.
    """
    source: str
    destination: str
    size: int = 64  # bytes
    timestamp: float = 0.0
    packet_id: int = 0


class TrafficGenerator:
    """
    Base class for traffic generators.
    """

    def __init__(self, source: str, destination: str):
        self.source = source
        self.destination = destination
        self.packets_sent = 0

    def generate(self, current_time: float) -> List[Packet]:
        """
        Generate packets at the current time.

        Args:
            current_time: Current simulation time

        Returns:
            List of generated packets
        """
        raise NotImplementedError("Subclasses must implement generate()")


class CBRGenerator(TrafficGenerator):
    """
    Constant Bit Rate (CBR) traffic generator.
    """

    def __init__(self, source: str, destination: str, rate: float):
        """
        Initialize CBR generator.

        Args:
            source: Source node ID
            destination: Destination node ID
            rate: Packet rate (packets per second)
        """
        super().__init__(source, destination)
        self.rate = rate
        self.interval = 1.0 / rate if rate > 0 else float('inf')
        self.last_packet_time = 0.0

    def generate(self, current_time: float) -> List[Packet]:
        """
        Generate CBR packets.

        Args:
            current_time: Current simulation time

        Returns:
            List of generated packets
        """
        packets = []

        # Generate packets at regular intervals
        while current_time - self.last_packet_time >= self.interval:
            self.last_packet_time += self.interval
            packet = Packet(
                source=self.source,
                destination=self.destination,
                timestamp=self.last_packet_time,
                packet_id=self.packets_sent
            )
            packets.append(packet)
            self.packets_sent += 1

        return packets


class BurstyGenerator(TrafficGenerator):
    """
    Bursty traffic generator with alternating burst and idle periods.
    """

    def __init__(self, source: str, destination: str,
                 burst_rate: float, idle_rate: float,
                 burst_duration: float, idle_duration: float):
        """
        Initialize bursty generator.

        Args:
            source: Source node ID
            destination: Destination node ID
            burst_rate: Packet rate during burst periods
            idle_rate: Packet rate during idle periods
            burst_duration: Duration of burst periods
            idle_duration: Duration of idle periods
        """
        super().__init__(source, destination)
        self.burst_rate = burst_rate
        self.idle_rate = idle_rate
        self.burst_duration = burst_duration
        self.idle_duration = idle_duration

        self.burst_interval = 1.0 / burst_rate if burst_rate > 0 else float('inf')
        self.idle_interval = 1.0 / idle_rate if idle_rate > 0 else float('inf')

        self.cycle_duration = burst_duration + idle_duration
        self.last_packet_time = 0.0

    def generate(self, current_time: float) -> List[Packet]:
        """
        Generate bursty packets.

        Args:
            current_time: Current simulation time

        Returns:
            List of generated packets
        """
        packets = []

        # Calculate current position in burst/idle cycle
        cycle_time = current_time % self.cycle_duration
        in_burst = cycle_time < self.burst_duration

        # Determine packet rate based on current phase
        if in_burst:
            interval = self.burst_interval
        else:
            interval = self.idle_interval

        # Generate packets at appropriate intervals
        while current_time - self.last_packet_time >= interval:
            self.last_packet_time += interval

            # Recalculate phase for the packet time
            packet_cycle_time = self.last_packet_time % self.cycle_duration
            packet_in_burst = packet_cycle_time < self.burst_duration

            if packet_in_burst:
                packet = Packet(
                    source=self.source,
                    destination=self.destination,
                    timestamp=self.last_packet_time,
                    packet_id=self.packets_sent
                )
                packets.append(packet)
                self.packets_sent += 1

        return packets


class PoissonGenerator(TrafficGenerator):
    """
    Poisson traffic generator.
    """

    def __init__(self, source: str, destination: str, rate: float, random_seed: int = None):
        """
        Initialize Poisson generator.

        Args:
            source: Source node ID
            destination: Destination node ID
            rate: Average packet rate (packets per second)
            random_seed: Random seed for reproducibility
        """
        super().__init__(source, destination)
        self.rate = rate
        if random_seed is not None:
            random.seed(random_seed)
        self.last_packet_time = 0.0

    def generate(self, current_time: float) -> List[Packet]:
        """
        Generate Poisson packets.

        Args:
            current_time: Current simulation time

        Returns:
            List of generated packets
        """
        packets = []

        # Generate packets using Poisson process
        while True:
            # Exponential inter-arrival time
            if self.rate > 0:
                inter_arrival = random.expovariate(self.rate)
            else:
                break

            packet_time = self.last_packet_time + inter_arrival

            if packet_time > current_time:
                break

            packet = Packet(
                source=self.source,
                destination=self.destination,
                timestamp=packet_time,
                packet_id=self.packets_sent
            )
            packets.append(packet)
            self.packets_sent += 1
            self.last_packet_time = packet_time

        return packets
