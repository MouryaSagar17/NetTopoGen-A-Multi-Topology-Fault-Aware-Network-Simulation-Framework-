# NetTopoGen UI/UX Refactor Plan

## Phase 1: Theme and Styles
- [x] Import COLORS from modern_ui.py
- [ ] Update ttk.Style configuration with dark theme
- [ ] Apply dark background to root and main containers
- [ ] Update label, button, and frame styles

## Phase 2: Tabbed Interface
- [ ] Replace accordion with ttk.Notebook in right panel
- [ ] Create 4 tabs: "Simulation", "Routing & Protocols", "QoS & Traffic", "Faults & Export"
- [ ] Redistribute accordion content to appropriate tabs:
  - Simulation tab: source/dest selection, ping button, manual mode toggle
  - Routing & Protocols tab: algorithm selection, compute route, protocol run, metrics tree, routing table
  - QoS & Traffic tab: QoS sliders, traffic controls, traffic results table
  - Faults & Export tab: break link, fail node, export functions

## Phase 3: Canvas Overlays
- [ ] Add floating real-time metrics overlay (HUD) on canvas
- [ ] Integrate metrics updates with simulation

## Phase 4: Bottom Panel
- [ ] Replace status bar with scrolling event log
- [ ] Add log_event method for system messages

## Phase 5: Advanced Panels
- [ ] Add protocol convergence timeline panel in Routing tab
- [ ] Add intent-based topology explainable preview panel

## Phase 6: Visualization Updates
- [ ] Update visualization.py for semantic link coloring (colors, thickness, dashed for failures)
- [ ] Ensure compatibility with existing metrics

## Phase 7: Testing and Validation
- [ ] Test all UI functionality
- [ ] Verify simulation behavior unchanged
- [ ] Adjust layouts as needed
