import networkx as nx
import osmnx as ox
import random
import os

class CityGraph:
    def __init__(self):
        self.graph = None
        self.data_path = os.path.join(os.path.dirname(__file__), "..", "data", "bangalore_graph.graphml")
        self.locations = {
            "MG Road": (12.9716, 77.5946),
            "Cubbon Park": (12.9764, 77.5929),
            "Lalbagh": (12.9507, 77.5848),
            "UB City": (12.9719, 77.5961),
            "Brigade Road": (12.9738, 77.6067),
            "Indiranagar": (12.9784, 77.6408),
            "Koramangala": (12.9279, 77.6271),
            "Majestic (KSR)": (12.9781, 77.5695),
            "Vidhana Soudha": (12.9796, 77.5906)
        }
        self.location_nodes = {}

    def generate_city(self):
        """Downloads Bangalore map around a center point (MG Road)"""
        center_point = self.locations["MG Road"]
        # Download a 3.5km radius to keep it fast but expansive enough
        print("Downloading Bangalore map from OpenStreetMap (this may take a minute)...")
        # Ensure we use drive network
        self.graph = ox.graph_from_point(center_point, dist=3500, network_type='drive')
        
        # Convert to undirected graph for easier bidirectional routing for cabs
        self.graph = ox.convert.to_undirected(self.graph)

        self._assign_custom_attributes()
        
    def _assign_custom_attributes(self):
        # Assign attributes to edges
        # We must use G.edges since it's an undirected graph which is essentially a MultiGraph in OSMnx context sometimes,
        # but utils_graph.get_undirected returns a standard Graph or MultiGraph depending on parallel edges.
        # OSMnx graphs are MultiDiGraphs by default, and get_undirected returns a MultiGraph.
        for u, v, k, data in self.graph.edges(keys=True, data=True):
            # 'length' is in meters, provided by OSMnx
            length = data.get('length', 100) 
            # Make sure length is numerical, sometimes lists can sneak in if simplified
            if isinstance(length, list): length = length[0]
            try:
                dist_km = float(length) / 1000.0
            except:
                dist_km = 0.1
            
            # Traffic multiplier: 1.0 (low), 1.5 (medium), 2.5 (heavy)
            traffic = random.choice([1.0, 1.2, 1.5, 2.0, 2.5])
            
            # Speed limit in km/h - infer from OSM or fallback
            speed_limit = 40
            if 'maxspeed' in data:
                ms = data['maxspeed']
                if isinstance(ms, list): ms = ms[0]
                try: speed_limit = int(ms)
                except: pass
                
            # Fuel cost (simplified metric)
            fuel_cost = round(dist_km * random.uniform(0.5, 1.5), 2)

            self.graph[u][v][k].update({
                'distance': round(dist_km, 3),
                'traffic': traffic,
                'speed_limit': speed_limit,
                'fuel_cost': fuel_cost
            })
            
    def map_locations_to_nodes(self):
        """Find nearest graph node for each predefined location"""
        print("Mapping predefined locations to graph nodes...")
        for name, (lat, lng) in self.locations.items():
            # osmnx expects (G, X, Y) where X is longitude and Y is latitude
            node = ox.nearest_nodes(self.graph, X=lng, Y=lat)
            self.location_nodes[name] = node

    def save_graph(self):
        """Saves the graph to a GraphML file."""
        os.makedirs(os.path.dirname(self.data_path), exist_ok=True)
        ox.save_graphml(self.graph, filepath=self.data_path)

    def load_graph(self):
        """Loads the graph from a file if it exists, else generates a new one."""
        if os.path.exists(self.data_path):
            print("Loading cached Bangalore map...")
            self.graph = ox.load_graphml(self.data_path)
            # Ensure we re-assign custom attributes because GraphML serialization
            # might not perfectly preserve all our custom float types (and traffic should be random each run)
            self._assign_custom_attributes()
        else:
            self.generate_city()
            self.save_graph()
            
        self.map_locations_to_nodes()
            
    def get_nodes(self):
        return list(self.graph.nodes())
    
    def get_edges(self):
        return self.graph.edges(data=True)

    def get_pos(self):
        # Extract x, y attributes from nodes (OSMnx stores them as 'x' and 'y')
        return {node: (float(data['x']), float(data['y'])) for node, data in self.graph.nodes(data=True)}
