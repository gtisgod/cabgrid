import networkx as nx
import math

class RoutingEngine:
    def __init__(self, city_graph):
        self.graph = city_graph.graph

    def _calculate_travel_time(self, u, v, data):
        """Helper to calculate travel time based on distance, speed limit, and traffic."""
        dist = data.get('distance', 0.1)
        speed = data.get('speed_limit', 40)
        traffic = data.get('traffic', 1.0)
        
        base_time = dist / speed
        return (base_time * traffic) * 60

    def _dijkstra_path(self, source, target, weight_func):
        """Runs NetworkX Dijkstra with a custom weight function."""
        try:
            path = nx.dijkstra_path(self.graph, source, target, weight=weight_func)
            
            # Calculate total metrics for the path
            total_distance = 0
            total_time = 0
            total_fuel = 0
            
            for i in range(len(path) - 1):
                u = path[i]
                v = path[i+1]
                
                # Handle MultiGraph (dictionary of parallel edges)
                edge_dict = self.graph[u][v]
                # Find the parallel edge that minimizes the specific weight_func
                best_data = None
                best_weight = float('inf')
                
                for key, data in edge_dict.items():
                    w = weight_func(u, v, data)
                    if w < best_weight:
                        best_weight = w
                        best_data = data
                
                if best_data:
                    total_distance += best_data.get('distance', 0)
                    total_time += self._calculate_travel_time(u, v, best_data)
                    total_fuel += best_data.get('fuel_cost', 0)
                
            return {
                'path': path,
                'distance': round(total_distance, 2),
                'eta': round(total_time, 2),
                'fuel': round(total_fuel, 2)
            }
        except nx.NetworkXNoPath:
            return None

    def get_shortest_route(self, source, target):
        def weight(u, v, data): return data.get('distance', 0.1)
        return self._dijkstra_path(source, target, weight)

    def get_fastest_route(self, source, target):
        def weight(u, v, data): return self._calculate_travel_time(u, v, data)
        return self._dijkstra_path(source, target, weight)

    def get_eco_route(self, source, target):
        def weight(u, v, data): return data.get('fuel_cost', 1.0)
        return self._dijkstra_path(source, target, weight)

    def get_optimal_route(self, source, target):
        def weight(u, v, data):
            time = self._calculate_travel_time(u, v, data)
            return (data.get('distance', 0.1) * 0.3) + (time * 0.5) + (data.get('fuel_cost', 1.0) * 0.2)
        return self._dijkstra_path(source, target, weight)

    def get_all_routes(self, source, target):
        return {
            'Shortest': self.get_shortest_route(source, target),
            'Fastest': self.get_fastest_route(source, target),
            'Eco': self.get_eco_route(source, target),
            'Optimal': self.get_optimal_route(source, target)
        }
