import time
from collections import deque
import networkx as nx

class DispatchEngine:
    def __init__(self, city_graph, cab_manager):
        self.graph = city_graph.graph
        self.cab_manager = cab_manager

    def find_nearest_cabs_bfs(self, start_node, k=5):
        """
        Uses BFS to find the `k` nearest available cabs based on edge hops.
        Returns a list of cabs and metrics for benchmarking.
        """
        start_time = time.perf_counter()
        
        available_cabs = {cab.current_node: cab for cab in self.cab_manager.get_available_cabs()}
        
        if not available_cabs:
            return [], 0, time.perf_counter() - start_time
            
        visited = set()
        queue = deque([(start_node, 0)]) # (node, depth)
        visited.add(start_node)
        
        found_cabs = []
        nodes_traversed = 0
        
        while queue and len(found_cabs) < k:
            current_node, depth = queue.popleft()
            nodes_traversed += 1
            
            if current_node in available_cabs:
                found_cabs.append((available_cabs[current_node], depth))
                
            for neighbor in self.graph.neighbors(current_node):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, depth + 1))
                    
        end_time = time.perf_counter()
        return found_cabs, nodes_traversed, end_time - start_time

    def find_nearest_cabs_brute_force(self, start_node, k=5):
        """
        Calculates distance to ALL available cabs using Dijkstra to find the nearest.
        This is for benchmarking against BFS.
        """
        start_time = time.perf_counter()
        
        available_cabs = self.cab_manager.get_available_cabs()
        nodes_traversed = 0
        
        distances = []
        for cab in available_cabs:
            try:
                # Use shortest path length (Dijkstra)
                dist = nx.shortest_path_length(self.graph, start_node, cab.current_node, weight='distance')
                distances.append((cab, dist))
                nodes_traversed += len(self.graph.nodes) # approximation of dijkstra traversal per cab
            except nx.NetworkXNoPath:
                pass
                
        distances.sort(key=lambda x: x[1])
        
        end_time = time.perf_counter()
        return distances[:k], nodes_traversed, end_time - start_time

    def explore_pickup_routes_dfs(self, source, target, max_depth=5):
        """
        Uses DFS to find alternative paths.
        Returns a list of paths.
        """
        paths = []
        visited = set()
        
        def dfs(current, path, depth):
            if depth > max_depth:
                return
            if current == target:
                paths.append(list(path))
                return
                
            visited.add(current)
            for neighbor in self.graph.neighbors(current):
                if neighbor not in visited:
                    path.append(neighbor)
                    dfs(neighbor, path, depth + 1)
                    path.pop()
            visited.remove(current)
            
        dfs(source, [source], 0)
        return paths
