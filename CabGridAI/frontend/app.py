import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time

from .visualization import MapVisualizer
from backend.routing_engine import RoutingEngine
from backend.dispatch_engine import DispatchEngine
from backend.pricing_engine import PricingEngine
from backend.benchmark import BenchmarkPanel

class CabGridApp:
    def __init__(self, root, city_graph, cab_manager, simulation):
        self.root = root
        self.root.title("CabGrid AI - Intelligent Cab Dispatch System")
        self.root.geometry("1400x900")
        self.root.configure(bg="#1a1a2e")
        
        # Styling
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure("TFrame", background="#1a1a2e")
        self.style.configure("Panel.TFrame", background="#16213e")
        self.style.configure("TLabel", background="#16213e", foreground="#e94560", font=("Segoe UI", 11))
        self.style.configure("Header.TLabel", font=("Segoe UI", 16, "bold"), foreground="#0f3460")
        self.style.configure("White.TLabel", foreground="white", font=("Segoe UI", 10))
        self.style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), background="#e94560", foreground="white")
        
        self.city_graph = city_graph
        self.cab_manager = cab_manager
        self.simulation = simulation
        
        self.routing_engine = RoutingEngine(self.city_graph)
        self.dispatch_engine = DispatchEngine(self.city_graph, self.cab_manager)
        self.pricing_engine = PricingEngine()
        
        self.current_routes = {}
        self.selected_route_key = None
        
        self._setup_ui()

        self.active_cab = None
        self.cab_ride_state_var = tk.StringVar(self.root)
        self.cab_process_state_var = tk.StringVar(self.root)
        self.cab_location_var = tk.StringVar(self.root)
        
        # Connect simulation callback (thread-safe UI update)
        self.simulation.start(update_callback=self._queue_map_update)
        
        # Initial draw
        self.visualizer.draw_map()

    def _setup_ui(self):
        # Main Layout
        self.left_panel = ttk.Frame(self.root, width=400, style="Panel.TFrame")
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)
        self.left_panel.pack_propagate(False)
        
        self.right_panel = ttk.Frame(self.root, style="TFrame")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # Title
        ttk.Label(self.left_panel, text="CabGrid AI", font=("Segoe UI", 24, "bold"), foreground="#e94560", background="#16213e").pack(pady=20)
        
        # Input Section
        input_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        input_frame.pack(fill="x", padx=20)
        
        locations = list(self.city_graph.locations.keys())
        
        ttk.Label(input_frame, text="Pickup Location:").grid(row=0, column=0, sticky="w", pady=5)
        self.pickup_var = tk.StringVar()
        self.pickup_cb = ttk.Combobox(input_frame, textvariable=self.pickup_var, values=locations, width=15)
        self.pickup_cb.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        if locations: self.pickup_cb.current(0)
        
        ttk.Label(input_frame, text="Destination:").grid(row=1, column=0, sticky="w", pady=5)
        self.dest_var = tk.StringVar()
        self.dest_cb = ttk.Combobox(input_frame, textvariable=self.dest_var, values=locations, width=15)
        self.dest_cb.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        if len(locations) > 1: self.dest_cb.current(1)
        
        ttk.Button(input_frame, text="Find Routes", style="Action.TButton", command=self._on_find_routes).grid(row=2, column=0, columnspan=2, pady=15, sticky="we")

        # Route Cards Section
        self.routes_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        self.routes_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Cabs Section
        self.cabs_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        self.cabs_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Visualization
        self.visualizer = MapVisualizer(self.right_panel, self.city_graph, self.cab_manager)

    def _on_find_routes(self):
        source_name = self.pickup_var.get()
        target_name = self.dest_var.get()
            
        if source_name == target_name:
            messagebox.showerror("Error", "Pickup and Destination cannot be the same.")
            return

        source = self.city_graph.location_nodes.get(source_name)
        target = self.city_graph.location_nodes.get(target_name)
        
        if source is None or target is None:
            messagebox.showerror("Error", "Invalid location selected.")
            return

        self.current_routes = self.routing_engine.get_all_routes(source, target)
        self._display_routes()

    def _display_routes(self):
        # Clear previous routes
        for widget in self.routes_frame.winfo_children():
            widget.destroy()
            
        ttk.Label(self.routes_frame, text="Select a Route:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
        
        for name, data in self.current_routes.items():
            if not data:
                continue
                
            frame = tk.Frame(self.routes_frame, bg="#0f3460", bd=1, relief="ridge", pady=5, padx=5)
            frame.pack(fill="x", pady=5)
            
            info = f"{name} Route\nDistance: {data['distance']} km | ETA: {data['eta']:.1f} min | Fuel: {data['fuel']} L"
            lbl = tk.Label(frame, text=info, bg="#0f3460", fg="white", font=("Segoe UI", 9), justify="left")
            lbl.pack(side="left", padx=5)
            
            btn = tk.Button(frame, text="Select", bg="#e94560", fg="white", command=lambda n=name, d=data: self._select_route(n, d))
            btn.pack(side="right", padx=5)

    def _select_route(self, route_name, route_data):
        self.selected_route_key = route_name
        self.visualizer.set_route(route_data['path'])
        
        # Trigger Cab Search (Benchmark BFS vs Brute Force)
        pickup_node = route_data['path'][0]
        
        bfs_cabs, bfs_nodes, bfs_time = self.dispatch_engine.find_nearest_cabs_bfs(pickup_node, k=3)
        bf_cabs, bf_nodes, bf_time = self.dispatch_engine.find_nearest_cabs_brute_force(pickup_node, k=3)
        
        # Log Benchmark
        BenchmarkPanel.print_dispatch_comparison(bfs_time, bfs_nodes, bf_time, bf_nodes)
        
        self._display_cabs(bfs_cabs, route_data)

    def _display_cabs(self, cabs_data, route_data):
        for widget in self.cabs_frame.winfo_children():
            widget.destroy()
            
        ttk.Label(self.cabs_frame, text="Nearby Available Cabs (BFS):", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
        
        surge = self.pricing_engine.calculate_surge(self.cab_manager)
        if surge > 1.0:
            tk.Label(self.cabs_frame, text=f"SURGE PRICING ACTIVE: {surge}x", fg="red", bg="#16213e", font=("Segoe UI", 10, "bold")).pack(anchor="w")
            BenchmarkPanel.log_surge(surge)

        if not cabs_data:
            ttk.Label(self.cabs_frame, text="No cabs available right now.", style="White.TLabel").pack(pady=10)
            return

        for cab, depth in cabs_data:
            fare = self.pricing_engine.estimate_fare(route_data['distance'], route_data['eta'], surge)
            
            frame = tk.Frame(self.cabs_frame, bg="#2c3e50", bd=1, relief="solid", pady=5, padx=5)
            frame.pack(fill="x", pady=5)
            
            info = f"{cab.cab_id} - {cab.cab_type}\nRating: {cab.rating}⭐ | Hops away: {depth}\nEst. Fare: ${fare}"
            tk.Label(frame, text=info, bg="#2c3e50", fg="white", font=("Segoe UI", 9), justify="left").pack(side="left")
            
            btn = tk.Button(frame, text="Book", bg="#27ae60", fg="white", command=lambda c=cab, r=route_data['path']: self._book_cab(c, r))
            btn.pack(side="right", padx=5)

    def _book_cab(self, cab, route_path):
        messagebox.showinfo("Cab Booked", f"Successfully booked {cab.cab_id}!\nWatch the live status below.")
        self.visualizer.set_route(route_path)
        
        for widget in self.cabs_frame.winfo_children():
            widget.destroy()
            
        self.active_cab = cab
        
        ttk.Label(self.cabs_frame, text="Current Trip Status", font=("Segoe UI", 14, "bold"), foreground="#e94560").pack(anchor="w", pady=(10, 5))
        
        status_container = tk.Frame(self.cabs_frame, bg="#0f3460", bd=0, pady=15, padx=15)
        status_container.pack(fill="x", pady=5)
        
        # Header: Cab ID and Type
        tk.Label(status_container, text=f"🚕 {cab.cab_id} • {cab.cab_type}", bg="#0f3460", fg="white", font=("Segoe UI", 13, "bold"), anchor="w").pack(fill="x", pady=(0, 10))
        
        # Status rows
        row1 = tk.Frame(status_container, bg="#0f3460")
        row1.pack(fill="x", pady=2)
        tk.Label(row1, textvariable=self.cab_ride_state_var, bg="#0f3460", fg="#f1c40f", font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left")
        
        row2 = tk.Frame(status_container, bg="#0f3460")
        row2.pack(fill="x", pady=2)
        tk.Label(row2, textvariable=self.cab_process_state_var, bg="#0f3460", fg="#3498db", font=("Segoe UI", 10), anchor="w").pack(side="left")
        
        row3 = tk.Frame(status_container, bg="#0f3460")
        row3.pack(fill="x", pady=(10, 0))
        tk.Label(row3, text="📍", bg="#0f3460", fg="#e94560", font=("Segoe UI", 12)).pack(side="left")
        tk.Label(row3, textvariable=self.cab_location_var, bg="#0f3460", fg="#2ecc71", font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", padx=5)

        self._update_status_ui()
        self.simulation.dispatch_cab(cab, route_path)
            
    def _queue_map_update(self):
        try:
            self.root.after(0, self.visualizer.draw_map)
            self.root.after(0, self._update_status_ui)
        except:
            pass

    def _update_status_ui(self):
        if getattr(self, 'active_cab', None):
            state = self.active_cab.state
            if state == "COMPLETED":
                self.cab_ride_state_var.set("COMPLETED ✅")
                self.cab_process_state_var.set("System: TERMINATED")
            else:
                self.cab_ride_state_var.set(f"Status: {state}")
                self.cab_process_state_var.set(f"System: {self.active_cab.process_state}")
                
            current_node = self.active_cab.current_node
            node_names = {v: k for k, v in self.city_graph.locations.items()}
            location_name = node_names.get(current_node, f"Intersection {current_node}")
            
            self.cab_location_var.set(location_name)
