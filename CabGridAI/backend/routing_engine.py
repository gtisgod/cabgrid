import networkx as nx
import math

class RoutingEngine:
    def __init__(self, city_graph):
        self.graph = city_graph.graph

    def _calculate_travel_time(self, u, v, data):
        """Helper to calculate travel time based on distance, speed limit, and traffic."""
        # time in hours
        base_time = data['distance'] / data['speed_limit']
        # multiply by traffic factor (1.0 to 2.5)
        # convert to minutes for better readability
        return (base_time * data['traffic']) * 60

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
                edge_data = self.graph[u][v]
                total_distance += edge_data['distance']
                total_time += self._calculate_travel_time(u, v, edge_data)
                total_fuel += edge_data['fuel_cost']
                
            return {
                'path': path,
                'distance': round(total_distance, 2),
                'eta': round(total_time, 2),
                'fuel': round(total_fuel, 2)
            }
        except nx.NetworkXNoPath:
            return None

    def get_shortest_route(self, source, target):
        """Minimizes pure distance."""
        def weight(u, v, data):
            return data['distance']
        return self._dijkstra_path(source, target, weight)

    def get_fastest_route(self, source, target):
        """Minimizes travel time."""
        def weight(u, v, data):
            return self._calculate_travel_time(u, v, data)
        return self._dijkstra_path(source, target, weight)

    def get_eco_route(self, source, target):
        """Minimizes fuel cost."""
        def weight(u, v, data):
            return data['fuel_cost']
        return self._dijkstra_path(source, target, weight)

    def get_optimal_route(self, source, target):
        """Balances distance, time, and fuel."""
        def weight(u, v, data):
            time = self._calculate_travel_time(u, v, data)
            # Normalize and blend
            return (data['distance'] * 0.3) + (time * 0.5) + (data['fuel_cost'] * 0.2)
        return self._dijkstra_path(source, target, weight)

    def get_all_routes(self, source, target):
        return {
            'Shortest': self.get_shortest_route(source, target),
            'Fastest': self.get_fastest_route(source, target),
            'Eco': self.get_eco_route(source, target),
            'Optimal': self.get_optimal_route(source, target)
        }
