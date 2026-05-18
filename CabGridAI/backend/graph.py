import networkx as nx
import random
import json
import os
import math

class CityGraph:
    def __init__(self, cols=12, rows=8):
        self.graph = nx.Graph()
        self.cols = cols
        self.rows = rows
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "data", "city_graph.json")
        self.image_width = 800
        self.image_height = 600
        
        # We will manually map predefined locations to nodes later
        self.locations = {
            "MG Road": 40,
            "Cubbon Park": 42,
            "Lalbagh": 85,
            "UB City": 55,
            "Brigade Road": 46,
            "Indiranagar": 10,
            "Koramangala": 89,
            "Majestic (KSR)": 36,
            "Vidhana Soudha": 38
        }
        self.location_nodes = self.locations

    def generate_city(self):
        """Generates a grid-based city graph that overlays on our background image."""
        self.graph = nx.grid_2d_graph(self.cols, self.rows)

        # Relabel nodes from (x, y) to integer IDs
        mapping = {node: i for i, node in enumerate(self.graph.nodes())}
        pos_mapping = {mapping[node]: node for node in self.graph.nodes()}
        
        self.graph = nx.relabel_nodes(self.graph, mapping)
        
        # Add (x, y) coordinates mapped to pixel space (approx 800x600)
        margin_x = 50
        margin_y = 50
        step_x = (self.image_width - 2 * margin_x) / (self.cols - 1)
        step_y = (self.image_height - 2 * margin_y) / (self.rows - 1)
        
        for node in self.graph.nodes():
            grid_x, grid_y = pos_mapping[node]
            pixel_x = margin_x + grid_x * step_x
            pixel_y = margin_y + grid_y * step_y
            # Jitter slightly for organic look
            pixel_x += random.uniform(-15, 15)
            pixel_y += random.uniform(-15, 15)
            self.graph.nodes[node]['pos'] = (pixel_x, pixel_y)

        # Randomly remove some edges to create a more realistic map
        edges_to_remove = random.sample(list(self.graph.edges()), k=int(len(self.graph.edges()) * 0.2))
        self.graph.remove_edges_from(edges_to_remove)

        # Ensure our landmark nodes aren't isolated
        isolated = list(nx.isolates(self.graph))
        for iso in isolated:
            if iso not in self.locations.values():
                self.graph.remove_node(iso)
            else:
                # reconnect it
                neighbors = [n for n in self.graph.nodes() if n != iso]
                closest = min(neighbors, key=lambda n: math.dist(self.graph.nodes[iso]['pos'], self.graph.nodes[n]['pos']))
                self.graph.add_edge(iso, closest)

        # Assign attributes
        for u, v in self.graph.edges():
            pos_u = self.graph.nodes[u]['pos']
            pos_v = self.graph.nodes[v]['pos']
            # Pixel distance
            dist = math.dist(pos_u, pos_v)
            dist_km = round(dist / 100.0, 2) # Arbitrary scale
            
            traffic = random.choice([1.0, 1.2, 1.5, 2.0, 2.5])
            speed_limit = random.choice([30, 45, 60])
            fuel_cost = round(dist_km * random.uniform(0.5, 1.5), 2)

            self.graph[u][v].update({
                'distance': dist_km,
                'traffic': traffic,
                'speed_limit': speed_limit,
                'fuel_cost': fuel_cost
            })

    def save_graph(self):
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        data = nx.node_link_data(self.graph)
        with open(self.data_path, 'w') as f:
            json.dump(data, f, indent=4)

    def load_graph(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r') as f:
                data = json.load(f)
            self.graph = nx.node_link_graph(data)
            for node in self.graph.nodes():
                pos = self.graph.nodes[node]['pos']
                if isinstance(pos, list):
                    self.graph.nodes[node]['pos'] = tuple(pos)
        else:
            self.generate_city()
            self.save_graph()
            
    def get_nodes(self):
        return list(self.graph.nodes())
    
    def get_edges(self):
        return self.graph.edges(data=True)

    def get_pos(self):
        return nx.get_node_attributes(self.graph, 'pos')
