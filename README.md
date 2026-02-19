# NetTopoGen: Advanced Network Topology Generator and Simulator

[![Python](https://img.shields.io/badge/Python-3.7+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange.svg)](https://docs.python.org/3/library/tkinter.html)

NetTopoGen is a comprehensive network topology generator and simulation framework designed for educational, research, and network planning purposes. Built with Python and Tkinter, it provides an intuitive graphical interface for creating, visualizing, and analyzing network topologies with advanced routing algorithms, QoS metrics, and fault simulation capabilities.

## Features

### Topology Generation
- **Multiple Topology Types**: Hierarchical, Star, Ring, Mesh, Tree, and Intent-Based generation
- **Device Support**: PCs, Routers, Switches, Servers, Firewalls, ISPs, Access Points, Load Balancers
- **Manual Mode**: Interactive topology creation with drag-and-drop functionality
- **Configuration Import**: Load topologies from JSON and Cisco IOS configuration files

### Routing & Algorithms
- **Classic Algorithms**: Dijkstra, Bellman-Ford, A*, BFS
- **QoS-Aware Routing**: Composite cost function with adjustable weights for delay, bandwidth, and loss
- **Protocol Simulation**: RIP-like and OSPF-like routing protocols
- **Path Visualization**: Real-time path highlighting and cost calculation

### Quality of Service (QoS)
- **Dynamic QoS Weights**: Adjustable α (delay), β (bandwidth), γ (loss) parameters
- **Cost Function**: Cost = α·delay + β·(1/bandwidth) + γ·loss
- **Real-time Updates**: Instant path recalculation with QoS changes

### Traffic Simulation
- **Traffic Patterns**: Constant Bit Rate (CBR) and Bursty traffic models
- **Load Simulation**: Configurable traffic load factors
- **Packet Animation**: Visual packet flow with hop-by-hop animation
- **Performance Metrics**: Delay, loss, and throughput analysis

### Fault Simulation
- **Link Failures**: Break and restore network links
- **Node Failures**: Inject and clear node faults
- **Resilience Testing**: Analyze network behavior under failure conditions
- **Dynamic Routing**: Automatic path recalculation during faults

### Visualization & Export
- **Interactive Canvas**: Zoom, pan, and hover tooltips
- **Real-time Metrics**: Link utilization and queue visualization
- **Export Formats**: Packet Tracer packages, PDF reports, JSON configurations
- **Screenshot Support**: Save topology visualizations

## Diagrams

### Use Case Diagram

```mermaid
graph TD
    A[User] --> B[Generate Network Topology]
    A --> C[Configure QoS Parameters]
    A --> D[Run Routing Algorithms]
    A --> E[Simulate Traffic]
    A --> F[Visualize Network]
    A --> G[Inject Faults]
    A --> H[Export Results]
    A --> I[Load/Save Configurations]

    B --> J[Select Topology Type]
    B --> K[Set Device Counts]
    B --> L[Manual Creation]

    D --> M[Dijkstra]
    D --> N[A*]
    D --> O[Bellman-Ford]
    D --> P[BFS]
    D --> Q[QoS-Metric]
    D --> R[RIP-like]
    D --> S[OSPF-like]

    E --> T[CBR Traffic]
    E --> U[Bursty Traffic]

    G --> V[Link Failures]
    G --> W[Node Failures]

    H --> X[Packet Tracer]
    H --> Y[PDF Reports]
    H --> Z[JSON Configs]
```

### Class Diagram

```mermaid
classDiagram
    class NetworkSimulator {
        +__init__(root)
        +generate_network()
        +start_simulation_thread()
        +compute_route()
        +run_protocol()
        +inject_fault()
        +export_results()
        -_update_option_menus()
        -draw_topology()
    }

    class Topology {
        +graph: nx.Graph
        +nodes: Dict[str, Node]
        +links: Dict[Tuple[str,str], Link]
        +node_coordinates: Dict[str, Tuple[int,int]]
        +add_node(node: Node)
        +add_link(link: Link)
        +remove_node(node_id: str)
        +remove_link(node_a: str, node_b: str)
        +get_shortest_path(source: str, target: str)
        +is_connected(): bool
    }

    class Node {
        +node_id: str
        +node_type: str
        +coordinates: Optional[Tuple[int,int]]
        +interfaces: Dict[str, Any]
        +status: bool
    }

    class Link {
        +node_a: str
        +node_b: str
        +delay: float
        +bandwidth: float
        +loss: float
        +status: bool
        +is_inferred: bool
        +nodes: Tuple[str,str]
        +__hash__()
        +__eq__(other)
    }

    class RoutingEngine {
        +topology: Topology
        +qos_weights: Dict[str, float]
        +compute_route(algorithm: str, source: str, target: str)
        -_dijkstra(source: str, target: str)
        -_astar(source: str, target: str)
        -_bellman_ford(source: str, target: str)
        -_calculate_link_cost(link)
        -_heuristic(node_a: str, node_b: str)
    }

    class TrafficSimulator {
        +topology: Topology
        +generators: List[TrafficGenerator]
        +traffic_stats: Dict[str, Any]
        +add_generator(generator: TrafficGenerator)
        +create_cbr_traffic(source: str, dest: str, rate: float)
        +create_bursty_traffic(source: str, dest: str, ...)
        +simulate_step(current_time: float)
        +get_traffic_stats()
    }

    class NetworkVisualizer {
        +topology: Topology
        +canvas: tk.Canvas
        +node_positions: Dict[str, Tuple[int,int]]
        +draw_topology()
        +animate_packet(path, color, speed)
        +highlight_path(path, color)
        +update_node_status(node_id, status)
        -_draw_device_icon(node, pos, highlight)
        -_calculate_positions()
    }

    class TopologyGenerator {
        +generate_hierarchical(n_pcs, n_routers, ...)
        +generate_star(n_pcs, n_routers, ...)
        +generate_ring(n_pcs, n_routers, ...)
        +generate_mesh(n_pcs, n_routers, ...)
        +generate_tree(n_pcs, n_routers, ...)
        +generate_from_intent(intent: str, ...)
        +validate_topology(topology)
    }

    NetworkSimulator --> Topology : uses
    NetworkSimulator --> RoutingEngine : uses
    NetworkSimulator --> TrafficSimulator : uses
    NetworkSimulator --> NetworkVisualizer : uses
    NetworkSimulator --> TopologyGenerator : uses

    Topology --> Node : contains
    Topology --> Link : contains

    RoutingEngine --> Topology : operates on
    TrafficSimulator --> Topology : uses
    NetworkVisualizer --> Topology : visualizes
    TopologyGenerator --> Topology : creates
```

### Sequence Diagram

```mermaid
sequenceDiagram
    participant User
    participant NetworkSimulator
    participant TopologyGenerator
    participant Topology
    participant RoutingEngine
    participant NetworkVisualizer
    participant TrafficSimulator

    User->>NetworkSimulator: Launch Application
    NetworkSimulator->>NetworkSimulator: __init__(root)

    User->>NetworkSimulator: Configure Topology Parameters
    User->>NetworkSimulator: Click "Generate Network"
    NetworkSimulator->>TopologyGenerator: generate_hierarchical/star/ring/etc()
    TopologyGenerator->>Topology: add_node() & add_link()
    TopologyGenerator-->>NetworkSimulator: Return topology object

    NetworkSimulator->>NetworkVisualizer: draw_topology()
    NetworkVisualizer->>Topology: get_all_nodes() & get_all_links()
    NetworkVisualizer-->>NetworkSimulator: Display topology

    User->>NetworkSimulator: Select Source & Destination
    User->>NetworkSimulator: Choose Algorithm
    User->>NetworkSimulator: Click "Start Simulation"
    NetworkSimulator->>RoutingEngine: compute_route(algorithm, source, target)
    RoutingEngine->>Topology: get_link() for cost calculation
    RoutingEngine-->>NetworkSimulator: Return path & cost

    NetworkSimulator->>NetworkVisualizer: animate_packet(path)
    NetworkVisualizer-->>NetworkSimulator: Animation complete

    User->>NetworkSimulator: Configure Traffic Simulation
    NetworkSimulator->>TrafficSimulator: create_cbr_traffic() or create_bursty_traffic()
    TrafficSimulator->>TrafficSimulator: add_generator()

    User->>NetworkSimulator: Run Traffic Demo
    NetworkSimulator->>TrafficSimulator: simulate_step()
    TrafficSimulator-->>NetworkSimulator: Return simulation results

    NetworkSimulator->>NetworkVisualizer: update_node_status() & link utilization
    NetworkVisualizer-->>NetworkSimulator: Update display
```

### Collaboration Diagram

```mermaid
graph TD
    subgraph "User Interface Layer"
        UI[NetworkSimulator]
    end

    subgraph "Core Logic Layer"
        TG[TopologyGenerator]
        RE[RoutingEngine]
        TS[TrafficSimulator]
    end

    subgraph "Data Model Layer"
        TOP[Topology]
        NODE[Node]
        LINK[Link]
    end

    subgraph "Presentation Layer"
        NV[NetworkVisualizer]
    end

    UI --> TG
    UI --> RE
    UI --> TS
    UI --> NV

    TG --> TOP
    RE --> TOP
    TS --> TOP
    NV --> TOP

    TOP --> NODE
    TOP --> LINK

    UI -.->|configures| TOP
    TG -.->|creates| NODE
    TG -.->|creates| LINK
    RE -.->|reads| NODE
    RE -.->|reads| LINK
    TS -.->|uses| NODE
    TS -.->|uses| LINK
    NV -.->|displays| NODE
    NV -.->|displays| LINK
```

### State Diagram

```mermaid
stateDiagram-v2
    [*] --> Initialization
    Initialization --> Ready: Application Started

    Ready --> TopologyGeneration: Generate Network
    TopologyGeneration --> Ready: Topology Created

    Ready --> SimulationSetup: Configure Simulation
    SimulationSetup --> SimulationRunning: Start Simulation
    SimulationRunning --> SimulationPaused: Pause
    SimulationPaused --> SimulationRunning: Resume
    SimulationRunning --> Ready: Stop/Complete

    Ready --> FaultInjection: Inject Faults
    FaultInjection --> Ready: Faults Applied

    Ready --> QoSAdjustment: Adjust QoS Weights
    QoSAdjustment --> Ready: Weights Updated

    Ready --> ExportData: Export Results
    ExportData --> Ready: Export Complete

    Ready --> [*]: Exit Application

    note right of SimulationRunning
        Packet animation and
        real-time metrics updates
    end note

    note right of FaultInjection
        Link/node failures,
        automatic rerouting
    end note
```

### Data Flow Diagrams

#### Level 1 - System Flow

```mermaid
graph TD
    %% Entities
    User[User]

    %% Processes
    subgraph Processes
        UI[User Interface]
        TM[Topology Manager]
        RL[Routing Logic]
        FM[Fault Manager]
        Vis[Visualization]
    end

    %% Data Stores
    subgraph Data_Stores
        TC[(Topology Configuration)]
        RMS[(Runtime Memory State)]
    end

    %% Flows
    User --> UI
    UI --> TM
    TM --> RL
    RL --> Vis
    
    %% Interactions
    TM <--> TC
    RL <--> RMS
    FM --> TM
```

#### Level 2 - Internal Operations

```mermaid
graph LR
    IP[Intent Parsing] -->|structured request| TM[Topology Manager]
    RC[Routing Computation] -->|path generation| RL[Routing Logic]
    Vis[Visualization] -->|UI update| UI[User Interface]
    FI[Fault Injection] -->|topology modification| TM
```

## Installation

### Prerequisites
- Python 3.7 or higher
- Node.js and npm (for React frontend)
- Required packages: `tkinter`, `matplotlib`, `networkx`, `numpy`

### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MouryaSagar17/nettopogen.git
   cd nettopogen
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**:
   ```bash
   python src/main.py
   ```

### System Requirements
- **OS**: Windows 10/11, macOS, Linux
- **RAM**: 4GB minimum, 8GB recommended
- **Display**: 1280x720 minimum resolution

## Usage

### Getting Started

1. **Launch the Application**:
   ```bash
   python src/main.py
   ```

2. **Configure Topology**:
   - Select topology type from dropdown
   - Set number of devices (PCs, Routers, Switches, Servers)
   - Click "Generate Network"

3. **Run Simulations**:
   - Select source and destination nodes
   - Choose routing algorithm
   - Click "Start Simulation" to animate packet flow

### Key Interface Elements

#### Top Bar
- **Device Configuration**: Set counts for different device types
- **Topology Selection**: Choose from predefined or intent-based topologies
- **Actions**: Generate, load/save configurations

#### Control Panel (Right Side)
- **Simulation**: Configure and run packet simulations
- **Break Link**: Simulate link failures
- **Algorithm**: Select and compare routing algorithms
- **QoS Metrics**: Adjust quality of service parameters
- **Load**: Configure and run traffic simulations
- **Fail Node**: Inject node failures
- **Export**: Generate reports and export to external tools

#### Canvas (Main Area)
- **Interactive Visualization**: Drag nodes, hover for metrics
- **Zoom Controls**: Scale topology view
- **Manual Mode**: Add/remove devices and links

### Advanced Features

#### Intent-Based Generation
Enter natural language descriptions:
```
"small network with 3 PCs, 2 routers, and 1 switch"
```

#### QoS Optimization
Adjust weights to prioritize different metrics:
- **Delay-sensitive**: High α value
- **Bandwidth-sensitive**: High β value
- **Reliability-focused**: High γ value

#### Protocol Comparison
Compare RIP and OSPF behavior:
- RIP: Distance-vector, slow convergence
- OSPF: Link-state, fast convergence with QoS awareness

## Architecture

### Core Modules

```
src/
├── main.py              # Main GUI application
├── core.py              # Topology, Node, Link classes
├── topology_generation.py # Layout algorithms
├── routing_algorithms.py  # Path finding implementations
├── traffic_simulation.py  # Traffic modeling
├── evaluation_metrics.py  # Performance analysis
├── visualization.py      # Canvas rendering
├── protocols.py          # RIP/OSPF simulation
├── traffic_model.py      # CBR/Bursty generators
├── config.py             # QoS weight constants
├── simulation_config.py  # Configuration management
└── routing_engine.py     # Algorithm orchestration
```

### Class Hierarchy

- **Topology**: Main container for network elements
  - **Node**: Network devices with properties and interfaces
  - **Link**: Connections with QoS metrics
- **NetworkSimulator**: GUI application class
- **RoutingEngine**: Algorithm implementations
- **TrafficSimulator**: Load generation and analysis

### Design Patterns

- **Observer Pattern**: Real-time UI updates
- **Factory Pattern**: Topology generation
- **Strategy Pattern**: Routing algorithm selection
- **Decorator Pattern**: QoS metric composition

## Configuration

### Simulation Parameters

```python
# QoS Weights (config.py)
QOS_WEIGHTS = {
    'alpha': 1.0,  # Delay weight
    'beta': 1.0,   # Bandwidth weight
    'gamma': 1.0   # Loss weight
}
```

### Topology Limits

- **Maximum Nodes**: Limited by system memory
- **Supported Devices**: 10 device types
- **Link Metrics**: Configurable delay (1-50ms), bandwidth (10Mbps-10Gbps), loss (0-50%)

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Add tests** for new functionality
5. **Commit your changes**:
   ```bash
   git commit -am 'Add some feature'
   ```
6. **Push to the branch**:
   ```bash
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

### Development Guidelines

- Follow PEP 8 style guidelines
- Add docstrings to all functions and classes
- Write unit tests for new features
- Update documentation for API changes
- Test on multiple platforms (Windows, macOS, Linux)

### Testing

Run the test suite:
```bash
python -m pytest tests/
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with Python's Tkinter for cross-platform GUI
- NetworkX for graph algorithms and analysis
- Matplotlib for visualization and PDF export
- Inspired by network simulation tools like Packet Tracer and GNS3

## Support

For questions, issues, or contributions:

- **GitHub Issues**: [Report bugs and request features](https://github.com/MouryaSagar17/nettopogen/issues)
- **Documentation**: [Wiki](https://github.com/MouryaSagar17/nettopogen/wiki)
- **Email**: 23695a3707@mits.ac.in

---

**NetTopoGen** - Empowering network education and research through interactive simulation.
