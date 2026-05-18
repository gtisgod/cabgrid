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
        
        # Active trips state management
        self.active_trips = {} # cab_id -> dict
        self.trip_status_widgets = {} # cab_id -> dict of widgets
        
        self._setup_ui()
        
        # Connect simulation callback (thread-safe UI update)
        self.simulation.start(update_callback=self._queue_map_update)
        
        # Initial draw
        self.visualizer.draw_map()
        
        self.show_dashboard()

    def _setup_ui(self):
        # Main Layout
        self.left_panel = ttk.Frame(self.root, width=450, style="Panel.TFrame")
        self.left_panel.pack(side="left", fill="y", padx=10, pady=10)
        self.left_panel.pack_propagate(False)
        
        self.right_panel = ttk.Frame(self.root, style="TFrame")
        self.right_panel.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        # System Logs (Global at bottom of left panel)
        self.logs_frame = ttk.LabelFrame(self.left_panel, text="System Logs", style="Panel.TFrame")
        self.logs_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        self.log_text = tk.Text(self.logs_frame, height=8, bg="#0f3460", fg="#00ffcc", font=("Consolas", 9), state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True, padx=5, pady=5)
        BenchmarkPanel.set_ui_callback(self._append_log)
        
        # Visualization
        self.visualizer = MapVisualizer(self.right_panel, self.city_graph, self.cab_manager)
        
        # View Frames (Stacked)
        self.dashboard_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        self.booking_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        self.livetrips_frame = ttk.Frame(self.left_panel, style="Panel.TFrame")
        
        self._build_dashboard()
        self._build_booking()
        self._build_livetrips()

    def _build_dashboard(self):
        ttk.Label(self.dashboard_frame, text="CabGrid AI", font=("Segoe UI", 30, "bold"), foreground="#e94560", background="#16213e").pack(pady=(40, 5))
        ttk.Label(self.dashboard_frame, text="Intelligent Dispatch Platform", style="White.TLabel").pack()
        
        stats_frame = tk.Frame(self.dashboard_frame, bg="#0f3460", pady=20)
        stats_frame.pack(fill="x", padx=20, pady=30)
        
        self.stat_total = tk.StringVar(value="Total Fleet: 0")
        self.stat_avail = tk.StringVar(value="Available Cabs: 0")
        
        tk.Label(stats_frame, textvariable=self.stat_total, bg="#0f3460", fg="#3498db", font=("Segoe UI", 14, "bold")).pack(pady=5)
        tk.Label(stats_frame, textvariable=self.stat_avail, bg="#0f3460", fg="#2ecc71", font=("Segoe UI", 14, "bold")).pack(pady=5)
        
        ttk.Button(self.dashboard_frame, text="Book a Ride", style="Action.TButton", command=self.show_booking).pack(pady=20, ipadx=20, ipady=10)

    def _build_booking(self):
        ttk.Label(self.booking_frame, text="Book a Ride", font=("Segoe UI", 24, "bold"), foreground="#e94560", background="#16213e").pack(pady=15)
        
        input_frame = ttk.Frame(self.booking_frame, style="Panel.TFrame")
        input_frame.pack(fill="x", padx=10)
        
        locations = list(self.city_graph.locations.keys())
        
        ttk.Label(input_frame, text="Pickup:").grid(row=0, column=0, sticky="w", pady=5)
        self.pickup_var = tk.StringVar()
        self.pickup_cb = ttk.Combobox(input_frame, textvariable=self.pickup_var, values=locations, width=15)
        self.pickup_cb.grid(row=0, column=1, sticky="w", pady=5, padx=10)
        if locations: self.pickup_cb.current(0)
        
        ttk.Label(input_frame, text="Dropoff:").grid(row=1, column=0, sticky="w", pady=5)
        self.dest_var = tk.StringVar()
        self.dest_cb = ttk.Combobox(input_frame, textvariable=self.dest_var, values=locations, width=15)
        self.dest_cb.grid(row=1, column=1, sticky="w", pady=5, padx=10)
        if len(locations) > 1: self.dest_cb.current(1)
        
        btn_frame = ttk.Frame(input_frame, style="Panel.TFrame")
        btn_frame.grid(row=2, column=0, columnspan=2, pady=15)
        ttk.Button(btn_frame, text="< Dashboard", command=self.show_dashboard).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Find Routes", style="Action.TButton", command=self._on_find_routes).pack(side="left", padx=5)
        
        self.routes_frame = ttk.Frame(self.booking_frame, style="Panel.TFrame")
        self.routes_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.cabs_frame = ttk.Frame(self.booking_frame, style="Panel.TFrame")
        self.cabs_frame.pack(fill="both", expand=True, padx=10, pady=5)

    def _build_livetrips(self):
        ttk.Label(self.livetrips_frame, text="Live Trips", font=("Segoe UI", 24, "bold"), foreground="#e94560", background="#16213e").pack(pady=15)
        
        btn_frame = ttk.Frame(self.livetrips_frame, style="Panel.TFrame")
        btn_frame.pack(fill="x", pady=10)
        ttk.Button(btn_frame, text="< Home", command=self.show_dashboard).pack(side="left", padx=10)
        ttk.Button(btn_frame, text="+ Book Another", style="Action.TButton", command=self.show_booking).pack(side="right", padx=10)
        
        self.trips_container = tk.Canvas(self.livetrips_frame, bg="#16213e", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.livetrips_frame, orient="vertical", command=self.trips_container.yview)
        self.trips_scrollable_frame = ttk.Frame(self.trips_container, style="Panel.TFrame")
        
        self.trips_scrollable_frame.bind(
            "<Configure>",
            lambda e: self.trips_container.configure(
                scrollregion=self.trips_container.bbox("all")
            )
        )
        
        self.trips_container.create_window((0, 0), window=self.trips_scrollable_frame, anchor="nw", width=420)
        self.trips_container.configure(yscrollcommand=scrollbar.set)
        
        self.trips_container.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    # --- Flow Management ---
    
    def _hide_all_views(self):
        self.dashboard_frame.pack_forget()
        self.booking_frame.pack_forget()
        self.livetrips_frame.pack_forget()

    def show_dashboard(self):
        self._hide_all_views()
        self.dashboard_frame.pack(fill="both", expand=True, side="top")
        self._update_stats()
        self.visualizer.clear_preview_route()
        
    def show_booking(self):
        self._hide_all_views()
        self.booking_frame.pack(fill="both", expand=True, side="top")
        
    def show_live_trips(self):
        self._hide_all_views()
        self.livetrips_frame.pack(fill="both", expand=True, side="top")
        self.visualizer.clear_preview_route()
        self._rebuild_trips_ui()

    # --- Logic ---

    def _update_stats(self):
        all_cabs = self.cab_manager.get_all_cabs()
        avail = len([c for c in all_cabs if c.state == "IDLE"])
        self.stat_total.set(f"Total Fleet: {len(all_cabs)}")
        self.stat_avail.set(f"Available Cabs: {avail}")

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
        for widget in self.routes_frame.winfo_children():
            widget.destroy()
            
        ttk.Label(self.routes_frame, text="Select a Route:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
        
        for name, data in self.current_routes.items():
            if not data:
                continue
                
            frame = tk.Frame(self.routes_frame, bg="#0f3460", bd=1, relief="ridge", pady=5, padx=5)
            frame.pack(fill="x", pady=2)
            
            info = f"{name} Route\nDist: {data['distance']} km | ETA: {data['eta']:.1f} m"
            lbl = tk.Label(frame, text=info, bg="#0f3460", fg="white", font=("Segoe UI", 9), justify="left")
            lbl.pack(side="left", padx=5)
            
            btn = tk.Button(frame, text="Select", bg="#e94560", fg="white", command=lambda n=name, d=data: self._select_route(n, d))
            btn.pack(side="right", padx=5)

    def _select_route(self, route_name, route_data):
        self.selected_route_key = route_name
        pickup_node = route_data['path'][0]
        destination_node = route_data['path'][-1]
        
        self.visualizer.set_preview_route(route_data['path'], pickup_node, destination_node)
        
        bfs_cabs, bfs_nodes, bfs_time = self.dispatch_engine.find_nearest_cabs_bfs(pickup_node, k=3)
        bf_cabs, bf_nodes, bf_time = self.dispatch_engine.find_nearest_cabs_brute_force(pickup_node, k=3)
        
        BenchmarkPanel.print_dispatch_comparison(bfs_time, bfs_nodes, bf_time, bf_nodes)
        self._display_cabs(bfs_cabs, route_data)

    def _display_cabs(self, cabs_data, route_data):
        for widget in self.cabs_frame.winfo_children():
            widget.destroy()
            
        ttk.Label(self.cabs_frame, text="Nearby Available Cabs:", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=5)
        
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
            frame.pack(fill="x", pady=2)
            
            info = f"{cab.cab_id} - {cab.cab_type}\nRating: {cab.rating}⭐ | ETA to pickup: {depth} hops\nFare: ${fare}"
            tk.Label(frame, text=info, bg="#2c3e50", fg="white", font=("Segoe UI", 9), justify="left").pack(side="left")
            
            btn = tk.Button(frame, text="Book", bg="#27ae60", fg="white", command=lambda c=cab, r=route_data['path']: self._book_cab(c, r))
            btn.pack(side="right", padx=5)

    def _book_cab(self, cab, route_path):
        pickup_node = route_path[0]
        destination_node = route_path[-1]
        
        if cab.current_node != pickup_node:
            route_to_pickup = self.routing_engine.get_fastest_route(cab.current_node, pickup_node)
            if route_to_pickup and route_to_pickup['path']:
                full_route = route_to_pickup['path'][:-1] + route_path
            else:
                full_route = route_path
        else:
            full_route = route_path
            
        self.active_trips[cab.cab_id] = {
            'cab': cab,
            'pickup': pickup_node,
            'dest': destination_node,
            'pickup_done': False,
            'full_route': full_route
        }
        
        self.visualizer.set_active_route(cab.cab_id, full_route, pickup_node, destination_node)
        self.simulation.dispatch_cab(cab, full_route)
        
        # Clear booking selection state
        for widget in self.cabs_frame.winfo_children(): widget.destroy()
        for widget in self.routes_frame.winfo_children(): widget.destroy()
            
        messagebox.showinfo("Cab Booked", f"Successfully booked {cab.cab_id}!\nTracking in Live Trips.")
        self.show_live_trips()

    def _rebuild_trips_ui(self):
        for widget in self.trips_scrollable_frame.winfo_children():
            widget.destroy()
            
        self.trip_status_widgets = {}
        
        if not self.active_trips:
            tk.Label(self.trips_scrollable_frame, text="No active trips.", bg="#16213e", fg="gray", font=("Segoe UI", 12)).pack(pady=20)
            return
            
        for cab_id, data in self.active_trips.items():
            cab = data['cab']
            
            card = tk.Frame(self.trips_scrollable_frame, bg="#0f3460", bd=1, relief="ridge", pady=10, padx=10)
            card.pack(fill="x", pady=5, padx=5)
            
            tk.Label(card, text=f"🚕 {cab.cab_id} • {cab.cab_type}", bg="#0f3460", fg="white", font=("Segoe UI", 12, "bold"), anchor="w").pack(fill="x")
            
            state_lbl = tk.Label(card, text="Status: ...", bg="#0f3460", fg="#f1c40f", font=("Segoe UI", 10, "bold"), anchor="w")
            state_lbl.pack(fill="x", pady=2)
            
            loc_lbl = tk.Label(card, text="Location: ...", bg="#0f3460", fg="#2ecc71", font=("Segoe UI", 10), anchor="w")
            loc_lbl.pack(fill="x")
            
            self.trip_status_widgets[cab_id] = {'state_lbl': state_lbl, 'loc_lbl': loc_lbl}
            
        self._update_status_ui()

    def _queue_map_update(self):
        try:
            self.root.after(0, self.visualizer.draw_map)
            self.root.after(0, self._update_status_ui)
        except:
            pass

    def _update_status_ui(self):
        if self.dashboard_frame.winfo_ismapped():
            self._update_stats()
            
        if not self.livetrips_frame.winfo_ismapped():
            return
            
        completed_cabs = []
        node_names = {v: k for k, v in self.city_graph.locations.items()}
            
        for cab_id, data in self.active_trips.items():
            cab = data['cab']
            pickup_node = data['pickup']
            widgets = self.trip_status_widgets.get(cab_id)
            
            if not widgets:
                continue
                
            state = cab.state
            current_node = cab.current_node
            loc_name = node_names.get(current_node, f"Node {current_node}")
            
            widgets['loc_lbl'].config(text=f"Location: {loc_name}")
            
            if state == "COMPLETED" or state == "IDLE":
                widgets['state_lbl'].config(text="COMPLETED ✅", fg="#2ecc71")
                completed_cabs.append(cab_id)
            else:
                if not data['pickup_done']:
                    if current_node == pickup_node:
                        data['pickup_done'] = True
                        widgets['state_lbl'].config(text="PICKUP DONE ✅", fg="#2ecc71")
                    else:
                        widgets['state_lbl'].config(text="Heading to Pickup...", fg="#f1c40f")
                else:
                    if current_node == data['dest']:
                        widgets['state_lbl'].config(text="ARRIVED ✅", fg="#2ecc71")
                    else:
                        widgets['state_lbl'].config(text="Heading to Destination 🚕", fg="#3498db")
                        
        for cab_id in completed_cabs:
            if cab_id in self.active_trips and self.active_trips[cab_id]['cab'].state == "IDLE":
                if cab_id in self.visualizer.active_routes:
                    self.visualizer.remove_active_route(cab_id)

    def _append_log(self, msg):
        def _update():
            self.log_text.config(state="normal")
            self.log_text.insert("end", msg + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        try:
            self.root.after(0, _update)
        except:
            pass
