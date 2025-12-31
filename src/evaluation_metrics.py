"""
Evaluation Metrics Module

This module provides functions to calculate various network performance metrics.
"""

import statistics
import time
from typing import Dict, List, Tuple, Optional, Any, Set
from collections import defaultdict


def calculate_throughput(packets_delivered: int, time_interval: float) -> float:
    """
    Calculate network throughput.

    Args:
        packets_delivered: Number of packets delivered
        time_interval: Time interval in seconds

    Returns:
        Throughput in packets per second
    """
    if time_interval <= 0:
        return 0.0
    return packets_delivered / time_interval


def calculate_packet_loss_rate(packets_sent: int, packets_delivered: int) -> float:
    """
    Calculate packet loss rate.

    Args:
        packets_sent: Total packets sent
        packets_delivered: Packets successfully delivered

    Returns:
        Packet loss rate (0.0 to 1.0)
    """
    if packets_sent == 0:
        return 0.0
    return (packets_sent - packets_delivered) / packets_sent


def calculate_average_delay(packet_delays: List[float]) -> float:
    """
    Calculate average packet delay.

    Args:
        packet_delays: List of packet delay times

    Returns:
        Average delay in seconds
    """
    if not packet_delays:
        return 0.0
    return statistics.mean(packet_delays)


def calculate_delay_jitter(packet_delays: List[float]) -> float:
    """
    Calculate delay jitter (variation in delay).

    Args:
        packet_delays: List of packet delay times

    Returns:
        Jitter value (standard deviation of delays)
    """
    if len(packet_delays) < 2:
        return 0.0
    return statistics.stdev(packet_delays)


def calculate_link_utilization(link_traffic: Dict[Tuple[str, str], float],
                             link_capacities: Dict[Tuple[str, str], float]) -> Dict[Tuple[str, str], float]:
    """
    Calculate link utilization percentages.

    Args:
        link_traffic: Traffic on each link (bits per second)
        link_capacities: Link capacities (bits per second)

    Returns:
        Dictionary of utilization percentages (0.0 to 1.0)
    """
    utilization = {}
    for link, traffic in link_traffic.items():
        capacity = link_capacities.get(link, 1.0)  # Default capacity of 1 bps
        if capacity > 0:
            utilization[link] = min(traffic / capacity, 1.0)  # Cap at 100%
        else:
            utilization[link] = 1.0  # Fully utilized if capacity is 0
    return utilization


def calculate_network_efficiency(actual_throughput: float, max_possible_throughput: float) -> float:
    """
    Calculate network efficiency.

    Args:
        actual_throughput: Actual network throughput
        max_possible_throughput: Maximum possible throughput

    Returns:
        Efficiency ratio (0.0 to 1.0)
    """
    if max_possible_throughput <= 0:
        return 0.0
    return min(actual_throughput / max_possible_throughput, 1.0)


def calculate_routing_convergence_time(routing_updates: List[float]) -> float:
    """
    Calculate routing convergence time.

    Args:
        routing_updates: List of routing update timestamps

    Returns:
        Convergence time in seconds
    """
    if len(routing_updates) < 2:
        return 0.0
    return max(routing_updates) - min(routing_updates)


def calculate_path_stability(path_changes: List[int], time_intervals: List[float]) -> float:
    """
    Calculate path stability (lower values indicate more stable paths).

    Args:
        path_changes: Number of path changes in each time interval
        time_intervals: Duration of each time interval

    Returns:
        Average path changes per second
    """
    if not time_intervals or sum(time_intervals) == 0:
        return 0.0

    total_changes = sum(path_changes)
    total_time = sum(time_intervals)
    return total_changes / total_time


def calculate_load_balancing_index(link_utilizations: List[float]) -> float:
    """
    Calculate load balancing index (1.0 = perfect balance).

    Args:
        link_utilizations: List of link utilization values

    Returns:
        Load balancing index (0.0 to 1.0)
    """
    if not link_utilizations:
        return 1.0

    mean_util = statistics.mean(link_utilizations)
    if mean_util == 0:
        return 1.0

    # Coefficient of variation
    try:
        cv = statistics.stdev(link_utilizations) / mean_util
        # Convert to index where 1.0 is perfect balance
        return 1.0 / (1.0 + cv)
    except statistics.StatisticsError:
        return 1.0


def calculate_network_resilience(failures_handled: int, total_failures: int) -> float:
    """
    Calculate network resilience.

    Args:
        failures_handled: Number of failures successfully handled
        total_failures: Total number of failures

    Returns:
        Resilience ratio (0.0 to 1.0)
    """
    if total_failures == 0:
        return 1.0
    return failures_handled / total_failures


def calculate_scalability_metric(computation_times: List[float], network_sizes: List[int]) -> float:
    """
    Calculate scalability metric (computation time per node squared).

    Args:
        computation_times: List of computation times
        network_sizes: Corresponding network sizes (number of nodes)

    Returns:
        Average scalability metric
    """
    if not computation_times or not network_sizes or len(computation_times) != len(network_sizes):
        return 0.0

    metrics = []
    for time_val, size in zip(computation_times, network_sizes):
        if size > 0:
            metrics.append(time_val / (size ** 2))

    return statistics.mean(metrics) if metrics else 0.0


class EvaluationMetrics:
    """
    Comprehensive network evaluation metrics calculator.
    """

    def __init__(self):
        """Initialize evaluation metrics calculator."""
        self.metrics_history = defaultdict(list)
        self.start_time = time.time()

    def update_metrics(self, simulation_data: Dict[str, Any]):
        """
        Update metrics with new simulation data.

        Args:
            simulation_data: Dictionary containing simulation statistics
        """
        current_time = time.time() - self.start_time

        # Basic metrics
        throughput = calculate_throughput(
            simulation_data.get("packets_delivered", 0),
            simulation_data.get("time_interval", 1.0)
        )

        packet_loss_rate = calculate_packet_loss_rate(
            simulation_data.get("packets_sent", 0),
            simulation_data.get("packets_delivered", 0)
        )

        packet_delays = simulation_data.get("packet_delays", [])
        avg_delay = calculate_average_delay(packet_delays)
        jitter = calculate_delay_jitter(packet_delays)

        # Store metrics
        self.metrics_history["throughput"].append((current_time, throughput))
        self.metrics_history["packet_loss_rate"].append((current_time, packet_loss_rate))
        self.metrics_history["average_delay"].append((current_time, avg_delay))
        self.metrics_history["jitter"].append((current_time, jitter))

        # Link utilization
        link_traffic = simulation_data.get("link_traffic", {})
        link_capacities = simulation_data.get("link_capacities", {})
        link_utilization = calculate_link_utilization(link_traffic, link_capacities)

        for link, util in link_utilization.items():
            self.metrics_history[f"link_util_{link}"].append((current_time, util))

    def get_current_metrics(self) -> Dict[str, float]:
        """
        Get current values of all metrics.

        Returns:
            Dictionary of current metric values
        """
        metrics = {}

        for metric_name, history in self.metrics_history.items():
            if history:
                metrics[metric_name] = history[-1][1]  # Latest value

        return metrics

    def get_metric_history(self, metric_name: str) -> List[Tuple[float, float]]:
        """
        Get historical values for a specific metric.

        Args:
            metric_name: Name of the metric

        Returns:
            List of (time, value) tuples
        """
        return self.metrics_history.get(metric_name, [])

    def calculate_overall_performance_score(self) -> float:
        """
        Calculate an overall performance score (0.0 to 1.0).

        Returns:
            Performance score
        """
        current_metrics = self.get_current_metrics()

        # Weights for different metrics
        weights = {
            "throughput": 0.3,
            "packet_loss_rate": 0.3,
            "average_delay": 0.2,
            "jitter": 0.2
        }

        score = 0.0
        total_weight = 0.0

        for metric, weight in weights.items():
            if metric in current_metrics:
                value = current_metrics[metric]

                # Normalize based on metric type
                if metric == "packet_loss_rate":
                    # Lower is better, invert
                    normalized_value = max(0.0, 1.0 - value * 10)  # Assume 10% loss is very bad
                elif metric in ["average_delay", "jitter"]:
                    # Lower is better, assume 1 second is very bad
                    normalized_value = max(0.0, 1.0 - value)
                else:
                    # Higher is better, use as-is (assuming normalized 0-1)
                    normalized_value = min(value, 1.0)

                score += normalized_value * weight
                total_weight += weight

        return score / total_weight if total_weight > 0 else 0.0

    def generate_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.

        Returns:
            Dictionary containing performance analysis
        """
        current_metrics = self.get_current_metrics()

        report = {
            "timestamp": time.time(),
            "metrics": current_metrics,
            "performance_score": self.calculate_overall_performance_score(),
            "summary": {}
        }

        # Generate summary
        throughput = current_metrics.get("throughput", 0)
        packet_loss = current_metrics.get("packet_loss_rate", 0)
        avg_delay = current_metrics.get("average_delay", 0)
        jitter = current_metrics.get("jitter", 0)

        report["summary"] = {
            "throughput": f"{throughput:.2f} packets/s",
            "packet_loss_rate": f"{packet_loss:.3%}",
            "average_delay": f"{avg_delay:.3f} seconds",
            "delay_jitter": f"{jitter:.3f} seconds",
            "performance_score": f"{report['performance_score']:.3f}/1.0"
        }

        # Performance assessment
        if report["performance_score"] >= 0.8:
            assessment = "Excellent"
        elif report["performance_score"] >= 0.6:
            assessment = "Good"
        elif report["performance_score"] >= 0.4:
            assessment = "Fair"
        else:
            assessment = "Poor"

        report["assessment"] = assessment

        return report

    def compare_scenarios(self, scenario_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare performance across different scenarios.

        Args:
            scenario_results: List of scenario result dictionaries

        Returns:
            Comparison analysis
        """
        if not scenario_results:
            return {}

        comparison = {
            "num_scenarios": len(scenario_results),
            "best_scenario": None,
            "worst_scenario": None,
            "average_performance": 0.0,
            "metric_averages": {}
        }

        best_score = -1
        worst_score = 2

        # Calculate averages and find best/worst
        for i, result in enumerate(scenario_results):
            score = result.get("performance_score", 0)

            if score > best_score:
                best_score = score
                comparison["best_scenario"] = i

            if score < worst_score:
                worst_score = score
                comparison["worst_scenario"] = i

            comparison["average_performance"] += score

            # Accumulate metric values
            for metric, value in result.get("metrics", {}).items():
                if metric not in comparison["metric_averages"]:
                    comparison["metric_averages"][metric] = []
                comparison["metric_averages"][metric].append(value)

        comparison["average_performance"] /= len(scenario_results)

        # Calculate metric averages
        for metric in comparison["metric_averages"]:
            values = comparison["metric_averages"][metric]
            comparison["metric_averages"][metric] = statistics.mean(values) if values else 0.0

        return comparison

    def export_metrics_to_file(self, filename: str):
        """
        Export metrics history to JSON file.

        Args:
            filename: Output filename
        """
        data = {
            "export_time": time.time(),
            "metrics_history": dict(self.metrics_history),
            "current_metrics": self.get_current_metrics(),
            "performance_report": self.generate_performance_report()
        }

        import json
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2, default=str)

    def reset(self):
        """Reset all metrics and history."""
        self.metrics_history.clear()
        self.start_time = time.time()
