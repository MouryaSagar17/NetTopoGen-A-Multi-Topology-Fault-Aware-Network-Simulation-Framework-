"""
Simulation Configuration Module

This module provides configuration classes for network simulation experiments.
"""

from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
import json
import os


@dataclass
class QoSConfig:
    """
    Configuration for QoS (Quality of Service) parameters.
    """
    alpha: float = 1.0  # Weight for delay
    beta: float = 1.0   # Weight for bandwidth (inverse)
    gamma: float = 1.0  # Weight for packet loss

    def to_dict(self) -> Dict[str, float]:
        """Convert to dictionary."""
        return {
            "alpha": self.alpha,
            "beta": self.beta,
            "gamma": self.gamma
        }

    @classmethod
    def from_dict(cls, data: Dict[str, float]) -> 'QoSConfig':
        """Create from dictionary."""
        return cls(
            alpha=data.get("alpha", 1.0),
            beta=data.get("beta", 1.0),
            gamma=data.get("gamma", 1.0)
        )


@dataclass
class TrafficConfig:
    """
    Configuration for traffic generation.
    """
    traffic_type: str = "CBR"  # CBR, Bursty, Poisson
    load_factor: float = 0.5   # Traffic load (0.0 to 1.0)
    packet_size: int = 64      # bytes
    duration: float = 60.0     # seconds

    # CBR specific
    cbr_rate: float = 100.0    # packets per second

    # Bursty specific
    burst_rate: float = 500.0      # packets per second during burst
    idle_rate: float = 10.0        # packets per second during idle
    burst_duration: float = 1.0    # seconds
    idle_duration: float = 4.0     # seconds

    # Poisson specific
    poisson_rate: float = 100.0    # average packets per second

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "traffic_type": self.traffic_type,
            "load_factor": self.load_factor,
            "packet_size": self.packet_size,
            "duration": self.duration,
            "cbr_rate": self.cbr_rate,
            "burst_rate": self.burst_rate,
            "idle_rate": self.idle_rate,
            "burst_duration": self.burst_duration,
            "idle_duration": self.idle_duration,
            "poisson_rate": self.poisson_rate
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrafficConfig':
        """Create from dictionary."""
        return cls(
            traffic_type=data.get("traffic_type", "CBR"),
            load_factor=data.get("load_factor", 0.5),
            packet_size=data.get("packet_size", 64),
            duration=data.get("duration", 60.0),
            cbr_rate=data.get("cbr_rate", 100.0),
            burst_rate=data.get("burst_rate", 500.0),
            idle_rate=data.get("idle_rate", 10.0),
            burst_duration=data.get("burst_duration", 1.0),
            idle_duration=data.get("idle_duration", 4.0),
            poisson_rate=data.get("poisson_rate", 100.0)
        )


@dataclass
class TopologyConfig:
    """
    Configuration for network topology generation.
    """
    topology_type: str = "Hierarchical"  # Hierarchical, Star, Ring, Mesh, Tree
    num_end_devices: int = 4
    num_routers: int = 2
    num_switches: int = 2
    num_hubs: int = 0

    # Layout parameters
    canvas_width: int = 800
    canvas_height: int = 600

    # Link properties
    default_delay: float = 10.0      # ms
    default_bandwidth: float = 1e9   # 1 Gbps
    default_loss: float = 0.0        # packet loss probability

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "topology_type": self.topology_type,
            "num_end_devices": self.num_end_devices,
            "num_routers": self.num_routers,
            "num_switches": self.num_switches,
            "num_hubs": self.num_hubs,
            "canvas_width": self.canvas_width,
            "canvas_height": self.canvas_height,
            "default_delay": self.default_delay,
            "default_bandwidth": self.default_bandwidth,
            "default_loss": self.default_loss
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TopologyConfig':
        """Create from dictionary."""
        return cls(
            topology_type=data.get("topology_type", "Hierarchical"),
            num_end_devices=data.get("num_end_devices", 4),
            num_routers=data.get("num_routers", 2),
            num_switches=data.get("num_switches", 2),
            num_hubs=data.get("num_hubs", 0),
            canvas_width=data.get("canvas_width", 800),
            canvas_height=data.get("canvas_height", 600),
            default_delay=data.get("default_delay", 10.0),
            default_bandwidth=data.get("default_bandwidth", 1e9),
            default_loss=data.get("default_loss", 0.0)
        )


@dataclass
class RoutingConfig:
    """
    Configuration for routing algorithms.
    """
    algorithm: str = "dijkstra"  # dijkstra, astar, bellman_ford, rip
    qos_weights: QoSConfig = field(default_factory=QoSConfig)
    convergence_timeout: float = 30.0  # seconds
    update_interval: float = 10.0      # seconds for dynamic protocols

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "algorithm": self.algorithm,
            "qos_weights": self.qos_weights.to_dict(),
            "convergence_timeout": self.convergence_timeout,
            "update_interval": self.update_interval
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RoutingConfig':
        """Create from dictionary."""
        return cls(
            algorithm=data.get("algorithm", "dijkstra"),
            qos_weights=QoSConfig.from_dict(data.get("qos_weights", {})),
            convergence_timeout=data.get("convergence_timeout", 30.0),
            update_interval=data.get("update_interval", 10.0)
        )


@dataclass
class FailureConfig:
    """
    Configuration for failure simulation.
    """
    enable_link_failures: bool = False
    enable_node_failures: bool = False
    failure_probability: float = 0.01  # probability per time step
    mean_failure_duration: float = 60.0  # seconds
    recovery_probability: float = 0.1   # probability per time step

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enable_link_failures": self.enable_link_failures,
            "enable_node_failures": self.enable_node_failures,
            "failure_probability": self.failure_probability,
            "mean_failure_duration": self.mean_failure_duration,
            "recovery_probability": self.recovery_probability
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FailureConfig':
        """Create from dictionary."""
        return cls(
            enable_link_failures=data.get("enable_link_failures", False),
            enable_node_failures=data.get("enable_node_failures", False),
            failure_probability=data.get("failure_probability", 0.01),
            mean_failure_duration=data.get("mean_failure_duration", 60.0),
            recovery_probability=data.get("recovery_probability", 0.1)
        )


@dataclass
class AttackConfig:
    """
    Configuration for attack simulation.
    """
    enable_attacks: bool = False
    attack_types: List[str] = field(default_factory=lambda: ["link_flooding"])
    attack_probability: float = 0.005  # probability per time step
    mean_attack_duration: float = 30.0  # seconds
    attack_intensity: float = 0.5       # attack strength (0.0 to 1.0)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enable_attacks": self.enable_attacks,
            "attack_types": self.attack_types,
            "attack_probability": self.attack_probability,
            "mean_attack_duration": self.mean_attack_duration,
            "attack_intensity": self.attack_intensity
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AttackConfig':
        """Create from dictionary."""
        return cls(
            enable_attacks=data.get("enable_attacks", False),
            attack_types=data.get("attack_types", ["link_flooding"]),
            attack_probability=data.get("attack_probability", 0.005),
            mean_attack_duration=data.get("mean_attack_duration", 30.0),
            attack_intensity=data.get("attack_intensity", 0.5)
        )


@dataclass
class SimulationConfig:
    """
    Main configuration class for network simulations.
    """
    name: str = "default_simulation"
    description: str = ""

    # Sub-configurations
    topology: TopologyConfig = field(default_factory=TopologyConfig)
    routing: RoutingConfig = field(default_factory=RoutingConfig)
    traffic: TrafficConfig = field(default_factory=TrafficConfig)
    failure: FailureConfig = field(default_factory=FailureConfig)
    attack: AttackConfig = field(default_factory=AttackConfig)

    # General simulation parameters
    duration: float = 60.0      # simulation duration in seconds
    time_step: float = 0.1      # simulation time step
    random_seed: Optional[int] = None
    output_dir: str = "output"
    log_level: str = "INFO"

    # Visualization
    enable_visualization: bool = True
    animation_speed: float = 1.0  # multiplier for animation speed

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "topology": self.topology.to_dict(),
            "routing": self.routing.to_dict(),
            "traffic": self.traffic.to_dict(),
            "failure": self.failure.to_dict(),
            "attack": self.attack.to_dict(),
            "duration": self.duration,
            "time_step": self.time_step,
            "random_seed": self.random_seed,
            "output_dir": self.output_dir,
            "log_level": self.log_level,
            "enable_visualization": self.enable_visualization,
            "animation_speed": self.animation_speed
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SimulationConfig':
        """Create configuration from dictionary."""
        return cls(
            name=data.get("name", "default_simulation"),
            description=data.get("description", ""),
            topology=TopologyConfig.from_dict(data.get("topology", {})),
            routing=RoutingConfig.from_dict(data.get("routing", {})),
            traffic=TrafficConfig.from_dict(data.get("traffic", {})),
            failure=FailureConfig.from_dict(data.get("failure", {})),
            attack=AttackConfig.from_dict(data.get("attack", {})),
            duration=data.get("duration", 60.0),
            time_step=data.get("time_step", 0.1),
            random_seed=data.get("random_seed"),
            output_dir=data.get("output_dir", "output"),
            log_level=data.get("log_level", "INFO"),
            enable_visualization=data.get("enable_visualization", True),
            animation_speed=data.get("animation_speed", 1.0)
        )

    def save_to_file(self, filename: str):
        """
        Save configuration to JSON file.

        Args:
            filename: Output filename
        """
        data = self.to_dict()
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

    @classmethod
    def load_from_file(cls, filename: str) -> 'SimulationConfig':
        """
        Load configuration from JSON file.

        Args:
            filename: Input filename

        Returns:
            SimulationConfig instance
        """
        with open(filename, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def create_default(cls) -> 'SimulationConfig':
        """Create a default simulation configuration."""
        return cls()

    @classmethod
    def create_mesh_experiment(cls) -> 'SimulationConfig':
        """Create configuration for mesh topology experiment."""
        config = cls(name="mesh_experiment")
        config.topology = TopologyConfig(
            topology_type="Mesh",
            num_end_devices=8,
            num_routers=4,
            num_switches=2
        )
        config.routing.algorithm = "dijkstra"
        config.traffic.load_factor = 0.7
        return config

    @classmethod
    def create_failure_experiment(cls) -> 'SimulationConfig':
        """Create configuration for failure resilience experiment."""
        config = cls(name="failure_experiment")
        config.failure.enable_link_failures = True
        config.failure.enable_node_failures = True
        config.failure.failure_probability = 0.02
        config.duration = 120.0
        return config

    @classmethod
    def create_attack_experiment(cls) -> 'SimulationConfig':
        """Create configuration for attack simulation experiment."""
        config = cls(name="attack_experiment")
        config.attack.enable_attacks = True
        config.attack.attack_types = ["link_flooding", "blackhole"]
        config.attack.attack_probability = 0.01
        config.duration = 90.0
        return config

    def validate(self) -> List[str]:
        """
        Validate the configuration for consistency.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate topology
        if self.topology.num_end_devices < 0:
            errors.append("Number of end devices must be non-negative")
        if self.topology.num_routers < 0:
            errors.append("Number of routers must be non-negative")
        if self.topology.num_switches < 0:
            errors.append("Number of switches must be non-negative")
        if self.topology.num_hubs < 0:
            errors.append("Number of hubs must be non-negative")

        # Validate QoS weights
        if self.routing.qos_weights.alpha < 0:
            errors.append("QoS alpha weight must be non-negative")
        if self.routing.qos_weights.beta < 0:
            errors.append("QoS beta weight must be non-negative")
        if self.routing.qos_weights.gamma < 0:
            errors.append("QoS gamma weight must be non-negative")

        # Validate traffic
        if self.traffic.load_factor < 0 or self.traffic.load_factor > 1:
            errors.append("Traffic load factor must be between 0 and 1")
        if self.traffic.duration <= 0:
            errors.append("Simulation duration must be positive")

        # Validate probabilities
        if not (0 <= self.failure.failure_probability <= 1):
            errors.append("Failure probability must be between 0 and 1")
        if not (0 <= self.failure.recovery_probability <= 1):
            errors.append("Recovery probability must be between 0 and 1")
        if not (0 <= self.attack.attack_probability <= 1):
            errors.append("Attack probability must be between 0 and 1")
        if not (0 <= self.attack.attack_intensity <= 1):
            errors.append("Attack intensity must be between 0 and 1")

        return errors

    def __str__(self) -> str:
        """String representation of the configuration."""
        return f"SimulationConfig(name='{self.name}', topology='{self.topology.topology_type}', duration={self.duration}s)"
