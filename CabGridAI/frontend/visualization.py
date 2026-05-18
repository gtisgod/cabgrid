import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from PIL import Image
import os
from backend.cab_manager import CabState

class MapVisualizer:
    def __init__(self, parent_frame, city_graph, cab_manager):
        self.graph = city_graph.graph
        self.pos = city_graph.get_pos()
        self.cab_manager = cab_manager
        self.city_graph = city_graph
        
        # Load Background Image
        img_path = os.path.join(os.path.dirname(__file__), '..', 'assets', 'city_map_bg.png')
        self.bg_img = None
        if os.path.exists(img_path):
            self.bg_img = Image.open(img_path)
        
        # Setup Figure
        self.fig = Figure(figsize=(8, 6), facecolor='#111111')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#111111')
        self.fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
        
        # Setup Canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent_frame)
        self.canvas_widget = self.canvas.get_tk_widget()
        self.canvas_widget.pack(fill="both", expand=True)
        
        self.selected_route = []

    def set_route(self, route_path):
        self.selected_route = route_path
        self.draw_map()

    def draw_map(self):
        self.ax.clear()
        
        # Draw Background Image
        if self.bg_img is not None:
            self.ax.imshow(self.bg_img, extent=[0, 800, 600, 0])
        
        # Draw background roads (subtle overlay)
        nx.draw_networkx_edges(
            self.graph, self.pos, ax=self.ax,
            edge_color='#2c3e50', width=2.0, alpha=0.4
        )
        
        # Draw traffic on edges
        heavy_traffic = [(u, v) for u, v, d in self.graph.edges(data=True) if d['traffic'] >= 2.0]
        med_traffic = [(u, v) for u, v, d in self.graph.edges(data=True) if 1.5 <= d['traffic'] < 2.0]
        
        nx.draw_networkx_edges(self.graph, self.pos, ax=self.ax, edgelist=med_traffic, edge_color='#f39c12', width=2, alpha=0.5)
        nx.draw_networkx_edges(self.graph, self.pos, ax=self.ax, edgelist=heavy_traffic, edge_color='#e74c3c', width=3, alpha=0.6)

        # Draw selected route
        if self.selected_route:
            route_edges = list(zip(self.selected_route, self.selected_route[1:]))
            nx.draw_networkx_edges(
                self.graph, self.pos, ax=self.ax, edgelist=route_edges,
                edge_color='#00ffcc', width=5, alpha=0.9
            )

        # Draw Landmark Nodes
        landmark_nodes = list(self.city_graph.location_nodes.values())
        # Filter out if node was removed randomly
        landmark_nodes = [n for n in landmark_nodes if n in self.pos]
        
        nx.draw_networkx_nodes(self.graph, self.pos, nodelist=landmark_nodes, ax=self.ax, node_size=100, node_color='#e74c3c')
        
        # Draw Labels for Landmarks
        labels = {node: name for name, node in self.city_graph.locations.items()}
        
        # Text annotations
        for node, label in labels.items():
            if node in self.pos:
                x, y = self.pos[node]
                self.ax.text(x, y - 15, label, color='white', fontsize=10, fontweight='bold', ha='center',
                            bbox=dict(facecolor='#16213e', alpha=0.7, edgecolor='none', pad=2))

        # Draw Cabs
        for cab in self.cab_manager.get_all_cabs():
            if cab.state == CabState.IDLE:
                color = '#2ecc71' # Green
            elif cab.state == CabState.DISPATCHED:
                color = '#f1c40f' # Yellow
            elif cab.state == CabState.EN_ROUTE:
                color = '#3498db' # Blue
            else:
                color = '#9b59b6' # Purple
                
            # Fallback for cab movement
            if cab.current_node in self.pos:
                x = cab.current_x if cab.current_x is not None else self.pos[cab.current_node][0]
                y = cab.current_y if cab.current_y is not None else self.pos[cab.current_node][1]
                
                self.ax.plot(x, y, marker='s', color=color, markersize=10, markeredgecolor='white', markeredgewidth=1.5)
                
                # Show cab status text on map (hide for IDLE to reduce clutter, or show briefly)
                if cab.state != CabState.IDLE:
                    self.ax.text(x, y - 20, f"{cab.cab_id} - {cab.state}", color=color, fontsize=8, fontweight='bold', ha='center',
                                bbox=dict(facecolor='#111111', alpha=0.8, edgecolor='none', pad=1))

        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_xlim(0, 800)
        self.ax.set_ylim(600, 0) # Inverted for typical image coordinates
        self.ax.set_facecolor('#111111')
        
        self.canvas.draw()
