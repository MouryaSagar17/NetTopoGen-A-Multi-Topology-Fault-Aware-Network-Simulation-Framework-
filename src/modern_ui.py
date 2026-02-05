import tkinter as tk
from tkinter import ttk
import random
import datetime

# --- ADVANCED NOC THEME ---
COLORS = {
    "bg_dark": "#0B0E14",        # Deep workspace black
    "panel_bg": "#161B22",       # Side panel gray
    "accent": "#58A6FF",         # Electric blue
    "success": "#238636",        # Router green
    "error": "#DA3633",          # Link failure red
    "text_main": "#C9D1D9",      # Light silver
    "text_dim": "#8B949E",       # Muted gray
    "card_bg": "rgba(22, 27, 34, 0.8)", # Glassmorphism effect
    "grid": "#1F242C"
}

class AdvancedNetworkUI:
    def __init__(self, root):
        self.root = root
        self.root.title("NetTopoGen Pro - Real Time Simulator")
        self.root.geometry("1400x900")
        self.root.configure(bg=COLORS["bg_dark"])

        self.setup_styles()
        self.setup_layout()
        self.draw_workspace_grid()
        self.render_sample_topology()
        self.create_floating_property_card()
        self.create_hud()
        self.log_event("System initialized ready.", "INFO")

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Base Colors
        style.configure("TFrame", background=COLORS["panel_bg"])
        style.configure("TLabel", background=COLORS["panel_bg"], foreground=COLORS["text_main"], font=("Segoe UI", 9))
        style.configure("TButton", font=("Segoe UI", 9))
        
        # Notebook Styles
        style.configure("TNotebook", background=COLORS["panel_bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=COLORS["bg_dark"], foreground=COLORS["text_dim"], padding=[12, 8], font=("Segoe UI", 9))
        style.map("TNotebook.Tab", background=[("selected", COLORS["panel_bg"])], foreground=[("selected", COLORS["accent"])])

        # 1. Visual Hierarchy & Button Priority
        # Primary Actions
        style.configure("Primary.TButton", background=COLORS["accent"], foreground="white", font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Primary.TButton", background=[("active", "#4090E0")])
        
        # Secondary Actions
        style.configure("Secondary.TButton", background="#21262D", foreground=COLORS["text_main"], borderwidth=1, relief="flat")
        style.map("Secondary.TButton", background=[("active", "#30363D")])
        
        # Muted/Advanced
        style.configure("Muted.TButton", background=COLORS["panel_bg"], foreground=COLORS["text_dim"], borderwidth=0)
        style.map("Muted.TButton", foreground=[("active", COLORS["text_main"])])

    def setup_layout(self):
        # Top Global Menu
        self.top_bar = tk.Frame(self.root, bg=COLORS["panel_bg"], height=40)
        self.top_bar.pack(side=tk.TOP, fill=tk.X)
        
        tk.Label(self.top_bar, text="NetTopoGen Pro", fg=COLORS["accent"], 
                 bg=COLORS["panel_bg"], font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=20)

        # Right Sidebar - Analytics & Metrics
        self.sidebar = tk.Frame(self.root, bg=COLORS["panel_bg"], width=350)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)
        
        # 9. Status Bar -> Event Log (Bottom)
        self.bottom_panel = tk.Frame(self.root, bg=COLORS["panel_bg"], height=150)
        self.bottom_panel.pack(side=tk.BOTTOM, fill=tk.X)
        self.bottom_panel.pack_propagate(False)
        
        tk.Label(self.bottom_panel, text="EVENT LOG", fg=COLORS["text_dim"], bg=COLORS["panel_bg"], 
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=2)
        
        self.event_log = tk.Text(self.bottom_panel, bg=COLORS["bg_dark"], fg=COLORS["text_main"], 
                                 font=("Consolas", 9), relief="flat", height=8)
        self.event_log.pack(fill="both", expand=True, padx=5, pady=5)

        # Main Canvas Area
        self.canvas = tk.Canvas(self.root, bg=COLORS["bg_dark"], highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.setup_sidebar_content()

    def setup_sidebar_content(self):
        # 2. Replace Long Right Accordion With Research Tabs
        self.notebook = ttk.Notebook(self.sidebar)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # Tab 1: Simulation
        self.tab_sim = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_sim, text="Simulation")
        
        ttk.Label(self.tab_sim, text="CONTROLS", font=("Segoe UI", 8, "bold"), foreground=COLORS["text_dim"]).pack(anchor="w", pady=(15,5))
        ttk.Button(self.tab_sim, text="Generate Network", style="Primary.TButton").pack(fill="x", pady=5)
        ttk.Button(self.tab_sim, text="Start Simulation", style="Primary.TButton").pack(fill="x", pady=5)
        
        ttk.Label(self.tab_sim, text="MODES", font=("Segoe UI", 8, "bold"), foreground=COLORS["text_dim"]).pack(anchor="w", pady=(20,5))
        ttk.Button(self.tab_sim, text="Manual Mode", style="Muted.TButton").pack(fill="x", pady=2)
        ttk.Button(self.tab_sim, text="Intent-Based", style="Muted.TButton", command=self.show_intent_panel).pack(fill="x", pady=2)

        # Tab 2: Routing & Protocols
        self.tab_routing = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_routing, text="Routing")
        
        ttk.Button(self.tab_routing, text="Generate Optimal Path", style="Primary.TButton").pack(fill="x", pady=10)
        ttk.Button(self.tab_routing, text="Run OSPF", style="Secondary.TButton", command=lambda: self.run_protocol("OSPF")).pack(fill="x", pady=2)
        ttk.Button(self.tab_routing, text="Run RIP", style="Secondary.TButton", command=lambda: self.run_protocol("RIP")).pack(fill="x", pady=2)
        
        # 5. Protocol Convergence Timeline Placeholder
        self.timeline_frame = tk.Frame(self.tab_routing, bg=COLORS["bg_dark"], height=100)
        self.timeline_frame.pack(fill="x", pady=20)
        tk.Label(self.timeline_frame, text="Convergence Timeline (Idle)", fg=COLORS["text_dim"], bg=COLORS["bg_dark"]).pack(pady=40)

        # Tab 3: QoS & Traffic
        self.tab_qos = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_qos, text="QoS")
        
        ttk.Label(self.tab_qos, text="TRAFFIC LOAD", font=("Segoe UI", 8, "bold"), foreground=COLORS["text_dim"]).pack(anchor="w", pady=(15,5))
        scale = ttk.Scale(self.tab_qos, from_=0, to=100, orient="horizontal")
        scale.pack(fill="x", pady=10)

        # Tab 4: Faults & Export
        self.tab_export = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_export, text="Export")
        
        ttk.Label(self.tab_export, text="DATA MANAGEMENT", font=("Segoe UI", 8, "bold"), foreground=COLORS["text_dim"]).pack(anchor="w", pady=(15,5))
        ttk.Button(self.tab_export, text="Load Config", style="Secondary.TButton").pack(fill="x", pady=2)
        ttk.Button(self.tab_export, text="Save CFG", style="Secondary.TButton").pack(fill="x", pady=2)
        
        ttk.Label(self.tab_export, text="RESEARCH EXPORT", font=("Segoe UI", 8, "bold"), foreground=COLORS["text_dim"]).pack(anchor="w", pady=(20,5))
        ttk.Button(self.tab_export, text="Export Results (CSV)", style="Secondary.TButton").pack(fill="x", pady=2)
        ttk.Button(self.tab_export, text="Experiment Summary", style="Secondary.TButton").pack(fill="x", pady=2)
        ttk.Button(self.tab_export, text="Export to Packet Tracer", style="Muted.TButton").pack(fill="x", pady=10)

    def create_hud(self):
        # 3. Real-Time Metrics Overlay (Canvas HUD)
        self.hud_frame = tk.Frame(self.canvas, bg="#1F242C", bd=1, relief="solid")
        self.hud_frame.place(x=20, y=20, width=200, height=140)
        
        tk.Label(self.hud_frame, text="LIVE METRICS", fg=COLORS["accent"], bg="#1F242C", font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=10, pady=5)
        
        self.metrics_labels = {}
        metrics = ["End-to-End Delay", "Packet Loss", "Throughput", "Active Path Cost"]
        for m in metrics:
            row = tk.Frame(self.hud_frame, bg="#1F242C")
            row.pack(fill="x", padx=10, pady=2)
            tk.Label(row, text=m, fg=COLORS["text_dim"], bg="#1F242C", font=("Segoe UI", 8)).pack(side="left")
            val = tk.Label(row, text="--", fg="white", bg="#1F242C", font=("Segoe UI", 8, "bold"))
            val.pack(side="right")
            self.metrics_labels[m] = val
            
        # Simulate update
        self.metrics_labels["End-to-End Delay"].config(text="12ms")
        self.metrics_labels["Packet Loss"].config(text="0.0%")
        self.metrics_labels["Throughput"].config(text="1.2 Gbps")
        self.metrics_labels["Active Path Cost"].config(text="10")

    def draw_workspace_grid(self):
        for i in range(0, 2000, 50):
            self.canvas.create_line(i, 0, i, 2000, fill=COLORS["grid"], width=1)
            self.canvas.create_line(0, i, 2000, i, fill=COLORS["grid"], width=1)

    def render_sample_topology(self):
        # Draw Links first (so they stay behind nodes)
        # 4. Semantic Link Coloring
        self.create_smart_link(400, 200, 250, 400, bandwidth=1000, utilization=0.4, loss=0.0)
        self.create_smart_link(400, 200, 550, 400, bandwidth=1000, utilization=0.1, loss=0.0)
        self.create_smart_link(250, 400, 250, 650, bandwidth=100, utilization=0.9, loss=0.05) # Congested
        
        # Draw Modern Nodes
        self.create_node(400, 200, "Core_Router_01", "router")
        self.create_node(250, 400, "Dist_Switch_A", "switch")
        self.create_node(550, 400, "Dist_Switch_B", "switch")
        self.create_node(250, 650, "End_Point_PC1", "pc")

    def create_node(self, x, y, name, n_type):
        # Outer Ring
        self.canvas.create_oval(x-25, y-25, x+25, y+25, outline=COLORS["accent"], width=2)
        # Inner Fill
        color = COLORS["success"] if n_type == "router" else COLORS["accent"]
        self.canvas.create_oval(x-18, y-18, x+18, y+18, fill=COLORS["panel_bg"], outline=color, width=2)
        # Type Icon (Simplified)
        icon_text = "R" if n_type == "router" else "S" if n_type == "switch" else "PC"
        self.canvas.create_text(x, y, text=icon_text, fill="white", font=("Segoe UI", 10, "bold"))
        # Label
        self.canvas.create_text(x, y+40, text=name, fill=COLORS["text_main"], font=("Segoe UI", 8))

    def create_smart_link(self, x1, y1, x2, y2, bandwidth=100, utilization=0.0, loss=0.0):
        # 4. Semantic Link Coloring Logic
        if loss > 0.1: # Failed or high loss
            color = COLORS["error"]
            dash = (5, 5)
        elif utilization > 0.8: # Congestion
            color = "#D29922" # Yellow/Orange
            dash = None
        else:
            color = COLORS["success"]
            dash = None
            
        width = 2 + (bandwidth / 500) # Thickness based on bandwidth
        
        # Glow Effect (Shadow line)
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width+2, stipple="gray50")
        # Main Line
        self.canvas.create_line(x1, y1, x2, y2, fill=color, width=width, dash=dash)

    def create_floating_property_card(self):
        """Creates the floating dark-mode card seen in your reference image."""
        card = tk.Frame(self.canvas, bg=COLORS["panel_bg"], bd=1, highlightthickness=1, highlightbackground=COLORS["accent"])
        card.place(x=700, y=150, width=280, height=220)

        tk.Label(card, text="Router R0 Properties", bg=COLORS["panel_bg"], fg="white", 
                 font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        options = ["Static Routing", "OSPF Protocol", "RIP Protocol", "BGP Protocol"]
        for opt in options:
            btn = tk.Button(card, text=opt, bg="#21262D", fg=COLORS["text_main"], 
                            relief="flat", activebackground=COLORS["accent"], anchor="w", padx=10)
            btn.pack(fill="x", padx=10, pady=2)

        tk.Button(card, text="RUN SIMULATION", bg=COLORS["accent"], fg="white", 
                  font=("Segoe UI", 9, "bold"), relief="flat").pack(fill="x", padx=10, pady=10)

    def log_event(self, message, level="INFO"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        tag = "info" if level == "INFO" else "warn" if level == "WARN" else "error"
        
        self.event_log.tag_config("info", foreground=COLORS["text_main"])
        self.event_log.tag_config("warn", foreground="#D29922")
        self.event_log.tag_config("error", foreground=COLORS["error"])
        
        self.event_log.insert(tk.END, f"[{timestamp}] [{level}] {message}\n", tag)
        self.event_log.see(tk.END)

    def run_protocol(self, protocol):
        self.log_event(f"Starting {protocol} convergence...", "INFO")
        # 5. Protocol Convergence Timeline (Visual update)
        for widget in self.timeline_frame.winfo_children():
            widget.destroy()
            
        steps = [("0s", "Update sent"), ("1s", "Route invalidated"), ("2s", "New path selected"), ("3s", "Converged")]
        for t, desc in steps:
            f = tk.Frame(self.timeline_frame, bg=COLORS["bg_dark"])
            f.pack(fill="x", padx=10, pady=2)
            tk.Label(f, text=t, fg=COLORS["accent"], bg=COLORS["bg_dark"], width=4).pack(side="left")
            tk.Label(f, text=desc, fg=COLORS["text_dim"], bg=COLORS["bg_dark"]).pack(side="left")
        
        self.log_event(f"{protocol} converged successfully.", "INFO")

    def show_intent_panel(self):
        # 6. Intent-Based Topology Explainability Panel
        win = tk.Toplevel(self.root)
        win.title("Intent Analysis")
        win.geometry("300x250")
        win.configure(bg=COLORS["panel_bg"])
        
        tk.Label(win, text="INTENT ANALYSIS", fg=COLORS["accent"], bg=COLORS["panel_bg"], font=("Segoe UI", 10, "bold")).pack(pady=10)
        
        details = [("Inferred Type", "Star Topology"), ("Confidence", "High (98%)"), ("Security", "Firewall Detected"), ("Nodes", "3 Switches, 12 PCs")]
        for k, v in details:
            f = tk.Frame(win, bg=COLORS["panel_bg"])
            f.pack(fill="x", padx=20, pady=2)
            tk.Label(f, text=k, fg=COLORS["text_dim"], bg=COLORS["panel_bg"]).pack(side="left")
            tk.Label(f, text=v, fg="white", bg=COLORS["panel_bg"]).pack(side="right")

if __name__ == "__main__":
    root = tk.Tk()
    app = AdvancedNetworkUI(root)
    root.mainloop()