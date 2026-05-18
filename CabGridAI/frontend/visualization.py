import matplotlib.pyplot as plt
import networkx as nx
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from backend.cab_manager import CabState

class MapVisualizer:
    def __init__(self, parent_frame, city_graph, cab_manager):
        self.graph = city_graph.graph
        self.pos = city_graph.get_pos()
        self.cab_manager = cab_manager
        self.city_graph = city_graph # Ref to access locations
        
        # Setup Figure
        self.fig = Figure(figsize=(8, 6), facecolor='#111111')
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor('#111111')
        self.fig.subplots_adjust(left=0.01, right=0.99, bottom=0.01, top=0.99)
        
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
        
        # Draw background roads (dark gray/blue)
        # OSMnx graphs are dense, use thin lines
        nx.draw_networkx_edges(
            self.graph, self.pos, ax=self.ax,
            edge_color='#2c3e50', width=0.5, alpha=0.3
        )
        
        # Draw traffic on edges
        heavy_traffic = [(u, v) for u, v, k, d in self.graph.edges(keys=True, data=True) if d.get('traffic', 1) >= 2.0]
        med_traffic = [(u, v) for u, v, k, d in self.graph.edges(keys=True, data=True) if 1.5 <= d.get('traffic', 1) < 2.0]
        
        nx.draw_networkx_edges(self.graph, self.pos, ax=self.ax, edgelist=med_traffic, edge_color='#f39c12', width=1.0, alpha=0.5)
        nx.draw_networkx_edges(self.graph, self.pos, ax=self.ax, edgelist=heavy_traffic, edge_color='#e74c3c', width=1.5, alpha=0.6)

        # Draw selected route
        if self.selected_route:
            route_edges = list(zip(self.selected_route, self.selected_route[1:]))
            nx.draw_networkx_edges(
                self.graph, self.pos, ax=self.ax, edgelist=route_edges,
                edge_color='#00ffcc', width=4, alpha=1.0
            )

        # Draw Pre-defined Landmarks
        landmark_nodes = list(self.city_graph.location_nodes.values())
        nx.draw_networkx_nodes(self.graph, self.pos, nodelist=landmark_nodes, ax=self.ax, node_size=60, node_color='#e74c3c')
        
        # Draw Labels for Landmarks
        labels = {node: name for name, node in self.city_graph.location_nodes.items()}
        nx.draw_networkx_labels(
            self.graph, self.pos, labels=labels, ax=self.ax,
            font_size=10, font_color='#ffffff', font_weight='bold', verticalalignment='bottom'
        )

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
                
            x = cab.current_x if cab.current_x is not None else self.pos[cab.current_node][0]
            y = cab.current_y if cab.current_y is not None else self.pos[cab.current_node][1]
            
            self.ax.plot(x, y, marker='s', color=color, markersize=8, markeredgecolor='white')
            # Don't clutter UI with cab IDs if they are far away, just the colored marker
            # self.ax.text(x, y + 0.0005, cab.cab_id[-3:], color='white', fontsize=7, ha='center')

        self.ax.set_xticks([])
        self.ax.set_yticks([])
        self.ax.set_facecolor('#111111')
        
        # Proper scaling for lat/lon maps
        self.ax.set_aspect('equal')
        
        self.canvas.draw()
